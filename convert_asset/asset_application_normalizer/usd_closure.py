"""Static USD dependency closure for AAN-03."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import posixpath
import re
import shutil
import sys
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
RESOLUTION_STATES = ("mirrored", "pruned", "waived", "blocked")
MISSING_DEPENDENCY_REQUIRED_RESOLUTION = (
    "Find and package the missing local dependency, prove task-scope prune/waiver safety, "
    "or keep this source blocked."
)
REMOTE_DEPENDENCY_REQUIRED_RESOLUTION = (
    "Mirror the remote URI into the package with provenance, prove task-scope prune/explicit "
    "allowance, or keep this source blocked."
)


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
    resolution: str | None = None
    required_resolution: str | None = None
    resolution_source: str | None = None

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
        if self.resolution:
            record["resolution"] = self.resolution
        if self.required_resolution:
            record["required_resolution"] = self.required_resolution
        if self.resolution_source:
            record["resolution_source"] = self.resolution_source
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

    dependencies = _resolve_missing_dependencies_from_mirrors(root, dependencies)
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
        can_compose=not remote,
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


def _resolve_missing_dependencies_from_mirrors(
    root: Path,
    dependencies: list[AssetDependency],
) -> list[AssetDependency]:
    resolved = []
    for dep in dependencies:
        if dep.resolved_path and dep.resolved_path.exists():
            resolved.append(dep)
            continue
        mirror = _find_local_mirror(root, dep)
        if mirror is None:
            resolved.append(dep)
        else:
            resolved.append(
                replace(
                    dep,
                    resolved_path=mirror.resolve(),
                    status="mirrored",
                    resolution="mirrored",
                    resolution_source="local_mirror_search",
                )
            )
    return resolved


def _find_local_mirror(root: Path, dep: AssetDependency) -> Path | None:
    if _is_remote_uri(dep.raw_asset_path) or dep.kind == "usd":
        return None

    raw_path = Path(dep.raw_asset_path.split("?", 1)[0])
    if not raw_path.name:
        return None

    for search_root in _local_mirror_search_roots(root, dep.source_layer):
        direct_candidates = [search_root / raw_path, search_root / raw_path.name]
        for candidate in direct_candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        if _is_small_mirror_root(search_root):
            for candidate in search_root.rglob(raw_path.name):
                if candidate.is_file():
                    return candidate
    return None


def _local_mirror_search_roots(root: Path, layer_path: Path) -> list[Path]:
    roots: list[Path] = []
    for base in [layer_path.parent, root.parent, *layer_path.parents, *root.parents]:
        roots.extend(
            [
                base,
                base / "SubUSDs" / "materials",
                base / "SubUSDs" / "textures",
                base / "Materials",
                base / "materials",
                base / "textures",
                base / "miscs" / "mdl",
                base / "assets" / "miscs" / "mdl",
            ]
        )

    roots.extend(
        [
            Path("/isaac-sim/kit/mdl/core/Base"),
            Path("/isaac-sim/kit/mdl/core/mdl"),
            Path("/isaac-sim/kit/mdl/core"),
        ]
    )
    for entry in sys.path:
        site_root = Path(entry) / "omni" / "mdl" / "core"
        roots.extend([site_root / "Base", site_root / "mdl", site_root])

    return _existing_unique_paths(roots)


def _existing_unique_paths(paths: list[Path]) -> list[Path]:
    unique = []
    seen: set[Path] = set()
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.exists() or not resolved.is_dir():
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def _is_small_mirror_root(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return bool(parts & {"mdl", "materials", "textures", "base"})


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

    stage = None
    if can_compose:
        try:
            from pxr import Usd  # type: ignore

            stage = Usd.Stage.Open(str(root))
        except Exception:
            stage = None

    records = []
    for prim in required_prims:
        if stage:
            exists = bool(stage.GetPrimAtPath(prim).IsValid())
            records.append(
                {"path": prim, "exists": exists, "status": "pass" if exists else "blocked"}
            )
            continue

        authored = _root_layer_has_prim_spec(root, prim)
        if authored is True:
            records.append({"path": prim, "exists": True, "status": "pass"})
        elif can_compose:
            records.append({"path": prim, "exists": False, "status": "blocked"})
        else:
            records.append({"path": prim, "exists": False, "status": "not_run"})
    return records


def _root_layer_has_prim_spec(root: Path, prim_path: str) -> bool | None:
    try:
        from pxr import Sdf  # type: ignore
    except Exception:
        return None

    layer = Sdf.Layer.FindOrOpen(str(root))
    if not layer:
        return None
    try:
        return bool(layer.GetPrimAtPath(Sdf.Path(prim_path)))
    except Exception:
        return None


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
        if layer_deps and _read_text(layer) is None and not _can_export_usd_layer_to_text(layer):
            result.append(
                {
                    "layer": str(layer),
                    "reason": (
                        "Layer has asset dependencies but cannot be text-rewritten or "
                        "Sdf-exported by AAN-03."
                    ),
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
                resolution=dep.resolution,
                required_resolution=dep.required_resolution,
                resolution_source=dep.resolution_source,
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
        text = _export_usd_layer_to_string(source)
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


def _can_export_usd_layer_to_text(path: Path) -> bool:
    return _export_usd_layer_to_string(path) is not None


def _export_usd_layer_to_string(path: Path) -> str | None:
    try:
        from pxr import Sdf  # type: ignore
    except Exception:
        return None
    try:
        layer = Sdf.Layer.OpenAsAnonymous(str(path))
        if not layer:
            return None
        return layer.ExportToString()
    except Exception:
        return None


def _build_blockers(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = []
    if inventory["remote"]:
        blockers.append(
            {
                "blocker_id": "aan03_block_remote_uri",
                "severity": "blocking",
                "summary": "USD dependency closure found unauthorized remote URI dependencies.",
                "count": len(inventory["remote"]),
                "required_resolution": REMOTE_DEPENDENCY_REQUIRED_RESOLUTION,
            }
        )
    if inventory["missing"]:
        blockers.append(
            {
                "blocker_id": "aan03_block_missing_dependency",
                "severity": "blocking",
                "summary": "USD dependency closure found missing local dependencies.",
                "count": len(inventory["missing"]),
                "required_resolution": MISSING_DEPENDENCY_REQUIRED_RESOLUTION,
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
    resolution_records = _resolution_records(inventory)
    missing_material_refs = _missing_raw_paths_by_kind(inventory["missing"], "mdl")
    missing_textures = _missing_raw_paths_by_kind(inventory["missing"], "texture")
    dependency_closure = {
        "root_layer": str(inventory["root_layer"]),
        "scanned_layers": [str(path) for path in inventory["scanned_layers"]],
        "local_files": _unique_local_records(dependencies),
        "missing": [
            _blocked_dependency_record(
                dep,
                required_resolution=MISSING_DEPENDENCY_REQUIRED_RESOLUTION,
                resolution_source="aan03r_missing_dependency_policy",
            )
            for dep in inventory["missing"]
        ],
        "missing_material_refs": missing_material_refs,
        "missing_textures": missing_textures,
        "remote_uri": [
            _blocked_dependency_record(
                dep,
                required_resolution=REMOTE_DEPENDENCY_REQUIRED_RESOLUTION,
                resolution_source="aan03r_remote_uri_policy",
            )
            for dep in inventory["remote"]
        ],
        "unauthorized_remote_uri": [
            _blocked_dependency_record(
                dep,
                required_resolution=REMOTE_DEPENDENCY_REQUIRED_RESOLUTION,
                resolution_source="aan03r_remote_uri_policy",
            )
            for dep in inventory["remote"]
        ],
        "unrewritable_layers": inventory["unrewritable_layers"],
        "resolution_records": resolution_records,
        "resolution_summary": _resolution_summary(resolution_records),
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
            "missing_material_ref": len(missing_material_refs),
            "missing_texture": len(missing_textures),
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


def _missing_raw_paths_by_kind(
    dependencies: list[AssetDependency],
    kind: str,
) -> list[str]:
    result = []
    seen: set[str] = set()
    for dep in dependencies:
        if dep.kind != kind or dep.raw_asset_path in seen:
            continue
        seen.add(dep.raw_asset_path)
        result.append(dep.raw_asset_path)
    return result


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


def _blocked_dependency_record(
    dep: AssetDependency,
    *,
    required_resolution: str,
    resolution_source: str,
) -> dict[str, Any]:
    record = dep.to_manifest_record()
    record["status"] = "blocked"
    record["resolution"] = "blocked"
    record["required_resolution"] = required_resolution
    record["resolution_source"] = resolution_source
    record["claim_impact"] = (
        "This source cannot claim package-local USD dependency closure until the gap is "
        "mirrored, safely pruned, explicitly waived, or remains blocked."
    )
    return record


def _resolution_records(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for dep in inventory["dependencies"]:
        if dep.resolution != "mirrored" or not dep.package_path:
            continue
        record = dep.to_manifest_record()
        record["claim_impact"] = (
            "AAN found a local mirror for this dependency and wrote it into the package."
        )
        records.append(record)

    records.extend(
        _blocked_dependency_record(
            dep,
            required_resolution=MISSING_DEPENDENCY_REQUIRED_RESOLUTION,
            resolution_source="aan03r_missing_dependency_policy",
        )
        for dep in inventory["missing"]
    )
    records.extend(
        _blocked_dependency_record(
            dep,
            required_resolution=REMOTE_DEPENDENCY_REQUIRED_RESOLUTION,
            resolution_source="aan03r_remote_uri_policy",
        )
        for dep in inventory["remote"]
    )
    return _unique_resolution_records(records)


def _resolution_summary(records: list[dict[str, Any]]) -> dict[str, int]:
    summary = {state: 0 for state in RESOLUTION_STATES}
    for record in records:
        resolution = record.get("resolution")
        if resolution in summary:
            summary[resolution] += 1
    return summary


def _unique_resolution_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for record in records:
        key = (
            str(record.get("source_layer", "")),
            str(record.get("raw_asset_path", "")),
            str(record.get("resolved_path", "")),
            str(record.get("package_path", "")),
            str(record.get("resolution", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique
