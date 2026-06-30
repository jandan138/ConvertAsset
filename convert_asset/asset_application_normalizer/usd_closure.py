"""Static USD dependency closure for AAN-03."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import posixpath
import re
import shutil
from typing import Any

from .model import MILESTONE_AAN03, NormalizeAssetRequest
from .package_layout import TargetPackageLayout


USD_DEP_EXTENSIONS = {".usd", ".usda", ".usdc", ".usdz"}
MDL_EXTENSIONS = {".mdl", ".mdle"}
TEXTURE_EXTENSIONS = {
    ".bmp",
    ".dds",
    ".exr",
    ".hdr",
    ".jpeg",
    ".jpg",
    ".png",
    ".tga",
    ".tif",
    ".tiff",
    ".tx",
}
REMOTE_URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
ASSET_TOKEN_RE = re.compile(r"@([^@\r\n]+)@")


@dataclass(frozen=True)
class AssetDependency:
    kind: str
    arc_kind: str
    raw_asset_path: str
    source_layer: Path
    holder: str | None = None
    prim_path: str | None = None
    resolved_path: Path | None = None
    package_path: str | None = None
    status: str = "pending"

    def to_manifest_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "kind": self.kind,
            "arc_kind": self.arc_kind,
            "raw_asset_path": self.raw_asset_path,
            "source_layer": str(self.source_layer),
            "status": self.status,
        }
        if self.holder:
            record["holder"] = self.holder
        if self.prim_path:
            record["prim_path"] = self.prim_path
        if self.resolved_path:
            record["resolved_path"] = str(self.resolved_path)
        if self.package_path:
            record["package_path"] = self.package_path
        return record


@dataclass(frozen=True)
class UsdClosureResult:
    overall_status: str
    return_code: int
    root_usd_package_path: str
    dependency_closure: dict[str, Any]
    static_usd_report: dict[str, Any]
    stage_gates: list[dict[str, Any]]
    blocked_reasons: list[dict[str, Any]] = field(default_factory=list)


def build_usd_closure_package(request: NormalizeAssetRequest) -> UsdClosureResult:
    layout = TargetPackageLayout(request.out_dir)
    inventory = _collect_inventory(request)
    blockers = _build_blockers(inventory)

    if blockers:
        return _result(
            "blocked",
            5,
            layout,
            inventory,
            blockers,
            gate_status="blocked",
        )

    _write_package(layout, inventory)
    return _result("pass", 0, layout, inventory, [], gate_status="pass")


def _collect_inventory(request: NormalizeAssetRequest) -> dict[str, Any]:
    root = request.source_usd.resolve()
    dependencies: list[AssetDependency] = []
    scanned_layers: list[Path] = []
    queue = [root]
    seen_layers: set[Path] = set()

    while queue:
        layer_path = queue.pop(0).resolve()
        if layer_path in seen_layers:
            continue
        seen_layers.add(layer_path)
        scanned_layers.append(layer_path)

        layer_deps = _scan_layer_dependencies(layer_path)
        dependencies.extend(layer_deps)
        for dep in layer_deps:
            if dep.kind == "usd" and dep.resolved_path and dep.resolved_path.exists():
                dep_path = dep.resolved_path.resolve()
                if dep_path not in seen_layers and dep_path not in queue:
                    queue.append(dep_path)

    remote = [dep for dep in dependencies if _is_remote_uri(dep.raw_asset_path)]
    missing = [
        dep
        for dep in dependencies
        if (not _is_remote_uri(dep.raw_asset_path))
        and dep.resolved_path is not None
        and not dep.resolved_path.exists()
    ]
    required_prims = _required_prim_records(
        root,
        request.required_prims,
        can_compose=not remote and not missing,
    )
    unrewritable = _unrewritable_layers(scanned_layers, dependencies)

    if not remote and not missing and not unrewritable:
        dependencies = _assign_package_paths(root, dependencies)

    return {
        "root_layer": root,
        "scanned_layers": scanned_layers,
        "dependencies": dependencies,
        "remote": remote,
        "missing": missing,
        "required_prims": required_prims,
        "unrewritable_layers": unrewritable,
        "default_prim": _default_prim(root),
    }


def _scan_layer_dependencies(layer_path: Path) -> list[AssetDependency]:
    deps: list[AssetDependency] = []
    seen: set[tuple[str, str]] = set()

    for dep in _scan_sdf_layer_dependencies(layer_path):
        key = (dep.raw_asset_path, dep.arc_kind)
        if key not in seen:
            seen.add(key)
            deps.append(dep)

    text = _read_text(layer_path)
    if text:
        for raw in ASSET_TOKEN_RE.findall(text):
            raw = raw.strip()
            if not raw:
                continue
            key = (raw, "asset_token")
            if key in seen:
                continue
            seen.add(key)
            deps.append(_dependency_from_raw(layer_path, raw, "asset_token"))

    return deps


def _scan_sdf_layer_dependencies(layer_path: Path) -> list[AssetDependency]:
    try:
        from pxr import Sdf  # type: ignore
    except Exception:
        return []

    layer = Sdf.Layer.FindOrOpen(str(layer_path))
    if not layer:
        return []

    deps: list[AssetDependency] = []
    for sublayer in layer.subLayerPaths:
        if sublayer:
            deps.append(_dependency_from_raw(layer_path, sublayer, "sublayer"))

    for prim_spec in _iter_prim_specs(layer.rootPrims):
        prim_path = getattr(getattr(prim_spec, "path", None), "pathString", None)
        deps.extend(_listop_dependencies(layer_path, prim_spec, "reference", prim_path))
        deps.extend(_listop_dependencies(layer_path, prim_spec, "payload", prim_path))
        deps.extend(_clip_dependencies(layer_path, prim_spec, prim_path))
        deps.extend(_property_asset_dependencies(layer_path, prim_spec, prim_path))
    return deps


def _iter_prim_specs(root_prims: Any):
    if root_prims is None:
        return
    if not isinstance(root_prims, (list, tuple)) and hasattr(root_prims, "path"):
        root_prims = [root_prims]
    for prim_spec in root_prims:
        yield prim_spec
        for child in getattr(prim_spec, "nameChildren", []) or []:
            yield from _iter_prim_specs([child])
        variant_sets = getattr(prim_spec, "variantSets", None)
        if variant_sets:
            for variant_set in variant_sets:
                for variant in getattr(variant_set, "variants", []) or []:
                    yield from _iter_prim_specs(getattr(variant, "primSpec", None))


def _listop_dependencies(
    layer_path: Path,
    prim_spec: Any,
    arc_kind: str,
    prim_path: str | None,
) -> list[AssetDependency]:
    list_name = "referenceList" if arc_kind == "reference" else "payloadList"
    list_op = getattr(prim_spec, list_name, None)
    if not list_op:
        return []
    deps = []
    effective_arc_kind = arc_kind
    if prim_path and "{" in prim_path:
        effective_arc_kind = f"variant_{arc_kind}"
    for attr in ("explicitItems", "addedItems", "prependedItems", "appendedItems"):
        for item in getattr(list_op, attr, []) or []:
            raw = getattr(item, "assetPath", None)
            if raw:
                deps.append(
                    _dependency_from_raw(
                        layer_path,
                        raw,
                        effective_arc_kind,
                        holder=str(getattr(getattr(prim_spec, "path", None), "pathString", "")),
                        prim_path=prim_path,
                    )
                )
    return deps


def _clip_dependencies(
    layer_path: Path,
    prim_spec: Any,
    prim_path: str | None,
) -> list[AssetDependency]:
    try:
        clips = prim_spec.GetInfo("clips")
    except Exception:
        clips = None
    if not isinstance(clips, dict):
        return []

    deps = []
    for arc_kind, raw in _iter_clip_asset_paths(clips):
        deps.append(_dependency_from_raw(layer_path, raw, arc_kind, prim_path=prim_path))
    return deps


def _iter_clip_asset_paths(clips: dict[str, Any]):
    for key, value in clips.items():
        if key in {"assetPaths", "clipAssetPaths"}:
            for raw in _coerce_asset_path_values(value):
                yield "clip_asset", raw
        elif key == "manifestAssetPath":
            for raw in _coerce_asset_path_values(value):
                yield "clip_manifest", raw
        elif isinstance(value, dict):
            yield from _iter_clip_asset_paths(value)


def _coerce_asset_path_values(value: Any) -> list[str]:
    if value is None:
        return []
    raw = getattr(value, "path", None)
    if raw:
        return [raw]
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)) or value.__class__.__name__.endswith("AssetPathArray"):
        paths = []
        for item in value:
            paths.extend(_coerce_asset_path_values(item))
        return paths
    return []


def _property_asset_dependencies(
    layer_path: Path,
    prim_spec: Any,
    prim_path: str | None,
) -> list[AssetDependency]:
    try:
        from pxr import Sdf  # type: ignore
    except Exception:
        return []

    deps = []
    for prop in getattr(prim_spec, "properties", []) or []:
        try:
            value = prop.default
        except Exception:
            continue
        for raw in _asset_paths_from_value(value, Sdf):
            deps.append(_dependency_from_raw(layer_path, raw, "asset_property", prim_path=prim_path))
    return deps


def _asset_paths_from_value(value: Any, sdf_module: Any) -> list[str]:
    asset_path_type = getattr(sdf_module, "AssetPath", None)
    if asset_path_type and isinstance(value, asset_path_type):
        return [value.path] if value.path else []
    if isinstance(value, (list, tuple)):
        paths = []
        for item in value:
            paths.extend(_asset_paths_from_value(item, sdf_module))
        return paths
    return []


def _dependency_from_raw(
    layer_path: Path,
    raw: str,
    arc_kind: str,
    *,
    holder: str | None = None,
    prim_path: str | None = None,
) -> AssetDependency:
    resolved = None if _is_remote_uri(raw) else _resolve_local_asset(layer_path, raw)
    return AssetDependency(
        kind=_classify_asset(raw),
        arc_kind=arc_kind,
        raw_asset_path=raw,
        source_layer=layer_path.resolve(),
        holder=holder,
        prim_path=prim_path,
        resolved_path=resolved,
    )


def _classify_asset(raw: str) -> str:
    ext = Path(raw.split("?", 1)[0]).suffix.lower()
    if ext in USD_DEP_EXTENSIONS:
        return "usd"
    if ext in MDL_EXTENSIONS:
        return "mdl"
    if ext in TEXTURE_EXTENSIONS:
        return "texture"
    return "asset"


def _is_remote_uri(raw: str) -> bool:
    return bool(REMOTE_URI_RE.match(raw))


def _resolve_local_asset(layer_path: Path, raw: str) -> Path:
    raw_path = Path(raw)
    if raw_path.is_absolute():
        return raw_path.resolve()
    return (layer_path.parent / raw_path).resolve()


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError:
        return None


def _default_prim(root: Path) -> str | None:
    try:
        from pxr import Sdf  # type: ignore
    except Exception:
        return None
    layer = Sdf.Layer.FindOrOpen(str(root))
    if not layer:
        return None
    return str(layer.defaultPrim) if layer.defaultPrim else None


def _required_prim_records(
    root: Path,
    required_prims: list[str],
    *,
    can_compose: bool,
) -> list[dict[str, Any]]:
    if not required_prims:
        return []
    if not can_compose:
        return [
            {"path": prim, "exists": False, "status": "not_run"}
            for prim in required_prims
        ]
    try:
        from pxr import Usd  # type: ignore
    except Exception:
        return [
            {"path": prim, "exists": False, "status": "blocked"}
            for prim in required_prims
        ]

    stage = Usd.Stage.Open(str(root))
    records = []
    for prim in required_prims:
        exists = bool(stage and stage.GetPrimAtPath(prim).IsValid())
        records.append({"path": prim, "exists": exists, "status": "pass" if exists else "blocked"})
    return records


def _unrewritable_layers(
    scanned_layers: list[Path],
    dependencies: list[AssetDependency],
) -> list[dict[str, Any]]:
    result = []
    deps_by_layer: dict[Path, list[AssetDependency]] = {}
    for dep in dependencies:
        deps_by_layer.setdefault(dep.source_layer.resolve(), []).append(dep)
    for layer in scanned_layers:
        layer_deps = deps_by_layer.get(layer.resolve(), [])
        if layer_deps and _read_text(layer) is None:
            result.append(
                {
                    "layer": str(layer),
                    "reason": "Layer has asset dependencies but cannot be text-rewritten in AAN-03.",
                }
            )
    return result


def _assign_package_paths(
    root: Path,
    dependencies: list[AssetDependency],
) -> list[AssetDependency]:
    used: set[str] = {"asset.usd"}
    resolved_to_package: dict[Path, str] = {}
    assigned = []
    for dep in dependencies:
        if not dep.resolved_path:
            assigned.append(dep)
            continue
        resolved = dep.resolved_path.resolve()
        if resolved == root.resolve():
            package_path = "asset.usd"
        else:
            package_path = resolved_to_package.get(resolved)
            if package_path is None:
                package_path = _package_path_for_dependency(dep, used)
                resolved_to_package[resolved] = package_path
        assigned.append(
            AssetDependency(
                kind=dep.kind,
                arc_kind=dep.arc_kind,
                raw_asset_path=dep.raw_asset_path,
                source_layer=dep.source_layer,
                holder=dep.holder,
                prim_path=dep.prim_path,
                resolved_path=dep.resolved_path,
                package_path=package_path,
                status="packaged",
            )
        )
    return assigned


def _package_path_for_dependency(dep: AssetDependency, used: set[str]) -> str:
    assert dep.resolved_path is not None
    folder = {
        "usd": "deps/usd",
        "mdl": "deps/mdl",
        "texture": "deps/textures",
    }.get(dep.kind, "deps/assets")
    name = dep.resolved_path.name
    candidate = f"{folder}/{name}"
    if candidate in used:
        stem = dep.resolved_path.stem
        suffix = dep.resolved_path.suffix
        digest = _path_digest(dep.resolved_path)
        candidate = f"{folder}/{stem}-{digest}{suffix}"
    used.add(candidate)
    return candidate


def _path_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]


def _write_package(layout: TargetPackageLayout, inventory: dict[str, Any]) -> None:
    layout.root.mkdir(parents=True, exist_ok=True)
    dependencies: list[AssetDependency] = inventory["dependencies"]
    deps_by_layer: dict[Path, list[AssetDependency]] = {}
    for dep in dependencies:
        deps_by_layer.setdefault(dep.source_layer.resolve(), []).append(dep)

    root = inventory["root_layer"].resolve()
    _copy_usd_with_rewrites(root, layout.root_usd, "asset.usd", deps_by_layer.get(root, []))

    copied: set[Path] = {root}
    for dep in sorted(dependencies, key=lambda item: item.package_path or ""):
        if not dep.resolved_path or not dep.package_path:
            continue
        source = dep.resolved_path.resolve()
        if source in copied:
            continue
        copied.add(source)
        target = layout.root / dep.package_path
        if dep.kind == "usd":
            _copy_usd_with_rewrites(source, target, dep.package_path, deps_by_layer.get(source, []))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def _copy_usd_with_rewrites(
    source: Path,
    target: Path,
    target_package_path: str,
    dependencies: list[AssetDependency],
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    text = _read_text(source)
    if text is None:
        shutil.copy2(source, target)
        return

    target_dir = posixpath.dirname(target_package_path)
    target_dir = target_dir if target_dir else "."
    for dep in dependencies:
        if not dep.package_path:
            continue
        rel = posixpath.relpath(dep.package_path, start=target_dir)
        text = text.replace(f"@{dep.raw_asset_path}@", f"@{rel}@")
    target.write_text(text, encoding="utf-8")


def _build_blockers(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = []
    if inventory["remote"]:
        blockers.append(
            {
                "blocker_id": "aan03_block_remote_uri",
                "severity": "blocking",
                "summary": "USD dependency closure found unauthorized remote URI dependencies.",
                "count": len(inventory["remote"]),
                "required_resolution": "Mirror the remote asset locally or add an explicit waiver policy.",
            }
        )
    if inventory["missing"]:
        blockers.append(
            {
                "blocker_id": "aan03_block_missing_dependency",
                "severity": "blocking",
                "summary": "USD dependency closure found missing local dependencies.",
                "count": len(inventory["missing"]),
                "required_resolution": "Provide the missing files or update the source USD references.",
            }
        )
    missing_required = [
        item for item in inventory["required_prims"] if item["status"] == "blocked"
    ]
    if missing_required:
        blockers.append(
            {
                "blocker_id": "aan03_block_required_prim_missing",
                "severity": "blocking",
                "summary": "One or more required prim paths are absent in the composed source stage.",
                "count": len(missing_required),
                "required_resolution": "Fix the task contract or source USD prim layout.",
            }
        )
    if inventory["unrewritable_layers"]:
        blockers.append(
            {
                "blocker_id": "aan03_block_unrewritable_usd_dependency",
                "severity": "blocking",
                "summary": "A USD layer with dependencies cannot be safely rewritten by the AAN-03 text path.",
                "count": len(inventory["unrewritable_layers"]),
                "required_resolution": "Use a USDA source or add an Sdf-level rewrite backend for this layer.",
            }
        )
    return blockers


def _result(
    overall_status: str,
    return_code: int,
    layout: TargetPackageLayout,
    inventory: dict[str, Any],
    blockers: list[dict[str, Any]],
    *,
    gate_status: str,
) -> UsdClosureResult:
    dependencies: list[AssetDependency] = inventory["dependencies"]
    dependency_closure = {
        "root_layer": str(inventory["root_layer"]),
        "scanned_layers": [str(path) for path in inventory["scanned_layers"]],
        "local_files": _unique_local_records(dependencies),
        "missing": [dep.to_manifest_record() for dep in inventory["missing"]],
        "remote_uri": [dep.to_manifest_record() for dep in inventory["remote"]],
        "unauthorized_remote_uri": [dep.to_manifest_record() for dep in inventory["remote"]],
        "unrewritable_layers": inventory["unrewritable_layers"],
    }
    static_usd_report = {
        "root_layer": {
            "source_path": str(inventory["root_layer"]),
            "package_path": "asset.usd" if overall_status == "pass" else None,
            "default_prim": inventory["default_prim"],
        },
        "required_prims": inventory["required_prims"],
        "dependency_counts": {
            "total": len(dependencies),
            "usd": sum(1 for dep in dependencies if dep.kind == "usd"),
            "mdl": sum(1 for dep in dependencies if dep.kind == "mdl"),
            "texture": sum(1 for dep in dependencies if dep.kind == "texture"),
            "remote": len(inventory["remote"]),
            "missing": len(inventory["missing"]),
        },
    }
    stage_gates = [
        {
            "check_id": MILESTONE_AAN03,
            "stage": "usd_closure",
            "status": gate_status,
            "summary": (
                "USD dependency closure produced a package-local USD tree."
                if gate_status == "pass"
                else "USD dependency closure found blocking dependency gaps."
            ),
        }
    ]
    return UsdClosureResult(
        overall_status=overall_status,
        return_code=return_code,
        root_usd_package_path="asset.usd",
        dependency_closure=dependency_closure,
        static_usd_report=static_usd_report,
        stage_gates=stage_gates,
        blocked_reasons=blockers,
    )


def _unique_local_records(dependencies: list[AssetDependency]) -> list[dict[str, Any]]:
    records = []
    seen: set[tuple[str, str]] = set()
    for dep in dependencies:
        if not dep.package_path or not dep.resolved_path:
            continue
        key = (str(dep.resolved_path), dep.package_path)
        if key in seen:
            continue
        seen.add(key)
        records.append(dep.to_manifest_record())
    return records
