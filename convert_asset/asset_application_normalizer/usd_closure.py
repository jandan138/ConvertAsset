"""Static USD dependency closure for AAN-03."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from pathlib import Path
import posixpath
import re
import shutil
import sys
from typing import Any

from .model import MILESTONE_AAN03, NormalizeAssetRequest
from .package_layout import TargetPackageLayout
from .stage_metrics import read_stage_metrics


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
REFERENCE_MATERIAL_SCOPE_NAME = "__aan_materials"
SOURCE_MATERIAL_PRIM_CUSTOM_DATA_KEY = "aan:sourceMaterialPrim"
REFERENCE_RENDER_PRIM_TYPES = {"BasisCurves", "GeomSubset", "Mesh", "Points"}


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

    scope_extraction = _write_package(layout, inventory, request)
    inventory["scope_extraction"] = scope_extraction
    if scope_extraction.get("status") == "blocked":
        return _result(
            "blocked",
            5,
            layout,
            inventory,
            [
                {
                    "blocker_id": "aan03_block_scope_extraction",
                    "severity": "blocking",
                    "summary": "AAN-03 could not create the declared role-scoped package USD.",
                    "detail": scope_extraction.get("reason"),
                    "required_resolution": (
                        "Use a declared source scope that composes successfully with all "
                        "bound materials, or fix the package-local source closure."
                    ),
                }
            ],
            gate_status="blocked",
        )
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


def _write_package(
    layout: TargetPackageLayout,
    inventory: dict[str, Any],
    request: NormalizeAssetRequest,
) -> dict[str, Any]:
    layout.root.mkdir(parents=True, exist_ok=True)
    # Recompilation owns the complete runtime tree.  Keeping files generated by
    # an earlier source/runtime profile can silently combine incompatible USD
    # or MDL layers, so rebuild those roots while retaining evidence outside
    # the runtime closure.
    for owned_root in ("deps", "interaction", "overlays", "physics", "task"):
        candidate = layout.root / owned_root
        if candidate.exists():
            shutil.rmtree(candidate)
    dependencies: list[AssetDependency] = inventory["dependencies"]
    deps_by_layer: dict[Path, list[AssetDependency]] = {}
    for dep in dependencies:
        deps_by_layer.setdefault(dep.source_layer.resolve(), []).append(dep)

    root = inventory["root_layer"].resolve()
    # The package entrypoint is deliberately a ConvertAsset-owned strong overlay.
    # It allows later role normalization to author scoped changes without mutating
    # the copied source layer or the upstream LabUtopia input.
    _copy_usd_with_rewrites(
        root,
        layout.source_root_usd,
        "deps/usd/source_root.usd",
        deps_by_layer.get(root, []),
    )

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

    scope_extraction = _build_role_scoped_source(layout, request)
    package_sublayer = scope_extraction.get("package_path")
    if not isinstance(package_sublayer, str):
        package_sublayer = "deps/usd/source_root.usd"
    package_sublayers = [package_sublayer]
    # A dynamic profile is a package-owned, stronger sublayer.  It starts
    # empty; AAN-05 only fills it after its source binding and exact rigid-body
    # coverage checks pass.  This keeps the upstream LabUtopia USD immutable.
    if request.asset_role == "dynamic":
        layout.physics_overlay_usd.parent.mkdir(parents=True, exist_ok=True)
        layout.physics_overlay_usd.write_text("#usda 1.0\n", encoding="utf-8")
        package_sublayers.insert(0, "overlays/physics_profile.usda")
        if request.interaction_profile is not None:
            layout.interaction_overlay_usd.write_text(
                "#usda 1.0\n", encoding="utf-8"
            )
            # The mass-only physics profile remains strongest.  Interaction
            # topology is nevertheless composed above the immutable source and
            # is authored earlier in the pipeline, so profile resolution sees
            # the normalized rigid root.
            package_sublayers.insert(1, "overlays/interaction.usda")
    source_metrics = read_stage_metrics(layout.source_root_usd)
    layout.root_usd.write_text(
        _entry_overlay_text(
            inventory.get("default_prim"),
            package_sublayers,
            stage_metrics=source_metrics,
        ),
        encoding="utf-8",
    )
    if (
        request.interaction_profile is not None
        and scope_extraction.get("status") == "pass"
    ):
        qualification = _qualify_entry_reference_materials(
            layout.root_usd,
            request.effective_asset_scope_prims[0],
        )
        scope_extraction["entry_reference_qualification"] = qualification
        if qualification["status"] != "pass":
            scope_extraction["status"] = "blocked"
            scope_extraction["reason"] = (
                "Interaction asset_entry_prim material reference closure failed: "
                + "; ".join(qualification["errors"])
            )
    return scope_extraction


def _entry_overlay_text(
    default_prim: str | None,
    package_sublayers: str | list[str],
    *,
    stage_metrics: dict[str, Any] | None = None,
) -> str:
    """Build the owned entry layer without changing the source's SI frame."""
    if isinstance(package_sublayers, str):
        package_sublayers = [package_sublayers]
    lines = ["#usda 1.0", "("]
    if default_prim:
        lines.append(f'    defaultPrim = "{default_prim}"')
    if stage_metrics:
        # These are stage metadata, not formatting hints.  Omitting them from
        # the strongest layer silently changes the physics interpretation to
        # USD's defaults (0.01 m/unit and Y-up) even when numeric geometry has
        # not moved.
        lines.extend(
            [
                f"    metersPerUnit = {_usda_number(stage_metrics.get('meters_per_unit'))}",
                f"    kilogramsPerUnit = {_usda_number(stage_metrics.get('kilograms_per_unit'))}",
                f'    upAxis = "{stage_metrics.get("up_axis")}"',
                f"    timeCodesPerSecond = {_usda_number(stage_metrics.get('time_codes_per_second'))}",
                f"    framesPerSecond = {_usda_number(stage_metrics.get('frames_per_second'))}",
                f"    startTimeCode = {_usda_number(stage_metrics.get('start_time_code'))}",
                f"    endTimeCode = {_usda_number(stage_metrics.get('end_time_code'))}",
            ]
        )
    lines.extend(
        [
            "    subLayers = [",
            *[f"        @{package_sublayer}@," for package_sublayer in package_sublayers],
            "    ]",
            ")",
            "",
        ]
    )
    return "\n".join(lines)


def _usda_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "1"
    if not math.isfinite(number):
        return "1"
    return format(number, ".17g")


def _build_role_scoped_source(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
) -> dict[str, Any]:
    """Create a standalone role-scoped scene from scope and bound materials.

    Both dynamic and visual-static packages must avoid inheriting an unrelated
    laboratory scene.  Copying selected composed prim subtrees into a
    package-local USDA keeps transforms, joints, collision data, and material
    bindings at their original absolute paths while preventing unrelated source
    materials from entering the target runtime.
    """
    dynamic_profiled = request.asset_role == "dynamic" and (
        request.physics_profile is not None or request.interaction_profile is not None
    )
    if request.asset_role != "visual_static" and not dynamic_profiled:
        return {
            "status": "not_applicable",
            "reason": (
                "Role-scoped USD extraction is required for visual_static and source-bound "
                "dynamic-profile packages only."
            ),
            "scope_prims": list(request.effective_asset_scope_prims),
            "retained_material_prims": [],
            "package_path": "deps/usd/source_root.usd",
        }

    try:
        from pxr import Sdf, Usd, UsdGeom, UsdShade  # type: ignore
    except Exception as exc:
        return {
            "status": "blocked",
            "reason": f"USD scope extraction requires pxr modules: {exc}",
            "scope_prims": list(request.effective_asset_scope_prims),
            "retained_material_prims": [],
        }

    try:
        source_stage = Usd.Stage.Open(str(layout.source_root_usd))
    except Exception as exc:
        source_stage = None
        open_error = str(exc)
    else:
        open_error = None
    if source_stage is None:
        return {
            "status": "blocked",
            "reason": f"Could not compose package-local source root: {open_error or layout.source_root_usd}",
            "scope_prims": list(request.effective_asset_scope_prims),
            "retained_material_prims": [],
        }

    scope_prims = list(request.effective_asset_scope_prims)
    missing = [
        path
        for path in scope_prims
        if not source_stage.GetPrimAtPath(path).IsValid()
    ]
    if missing:
        return {
            "status": "blocked",
            "reason": f"Declared scope prims are absent from the package-local source: {missing}",
            "scope_prims": scope_prims,
            "retained_material_prims": [],
        }

    material_paths = _scope_bound_material_paths(source_stage, scope_prims, Usd, UsdShade)
    subtree_paths = _minimal_subtree_paths([*scope_prims, *material_paths])
    try:
        # Flatten a population-masked composed snapshot rather than the full
        # scene.  This keeps the output package independent from unrelated
        # source materials (which may not be compatible with the target Kit)
        # while still resolving future sublayers/references in the declared
        # visual scope.
        population_mask = Usd.StagePopulationMask()
        for path in subtree_paths:
            population_mask.Add(Sdf.Path(path))
        masked_stage = Usd.Stage.OpenMasked(
            str(layout.source_root_usd),
            population_mask,
            Usd.Stage.LoadAll,
        )
        if masked_stage is None:
            raise RuntimeError("Could not compose the population-masked source stage")
        flattened = masked_stage.Flatten()
        scoped = Sdf.Layer.CreateAnonymous("aan_role_scope.usda")
        _copy_layer_timing_metadata(flattened, scoped)
        for root_spec in flattened.rootPrims:
            if not Sdf.CopySpec(
                flattened,
                root_spec.path,
                scoped,
                root_spec.path,
            ):
                raise RuntimeError(f"Sdf.CopySpec returned false for {root_spec.path}")
        reference_scope_material_relocations: list[dict[str, str]] = []
        material_output_paths = list(material_paths)
        if request.interaction_profile is not None:
            scoped_stage_for_relocation = Usd.Stage.Open(scoped)
            if scoped_stage_for_relocation is None:
                raise RuntimeError("Scoped USDA could not be opened for material relocation")
            reference_scope_material_relocations = (
                _relocate_reference_scope_materials(
                    scoped_stage_for_relocation,
                    scope_prims[0],
                    material_paths,
                    Usd,
                    Sdf,
                )
            )
            relocated_by_source = {
                item["source_material_prim"]: item["package_material_prim"]
                for item in reference_scope_material_relocations
            }
            material_output_paths = [
                relocated_by_source.get(path, path) for path in material_paths
            ]

        layout.scoped_source_usd.parent.mkdir(parents=True, exist_ok=True)
        if not scoped.Export(str(layout.scoped_source_usd)):
            raise RuntimeError(f"Could not export scoped USDA: {layout.scoped_source_usd}")
        snapshot_rewrite = rewrite_scoped_snapshot_asset_paths(
            layout.root,
            layout.scoped_source_usd,
        )
        if snapshot_rewrite["status"] != "pass":
            raise RuntimeError(str(snapshot_rewrite["reason"]))

        scoped_stage = Usd.Stage.Open(str(layout.scoped_source_usd))
        if scoped_stage is None:
            raise RuntimeError("Scoped USDA could not be reopened")
        UsdGeom.SetStageMetersPerUnit(
            scoped_stage,
            UsdGeom.GetStageMetersPerUnit(source_stage),
        )
        UsdGeom.SetStageUpAxis(scoped_stage, UsdGeom.GetStageUpAxis(source_stage))
        try:
            from pxr import UsdPhysics  # type: ignore

            UsdPhysics.SetStageKilogramsPerUnit(
                scoped_stage,
                UsdPhysics.GetStageKilogramsPerUnit(source_stage),
            )
        except Exception:
            # The entry layer still owns a strict frame-parity gate.  Older
            # pxr builds that lack this metadata helper will be blocked there
            # rather than silently accepted.
            pass
        scoped_stage.GetRootLayer().Save()
        missing_after_export = [
            path for path in [*scope_prims, *material_output_paths]
            if not scoped_stage.GetPrimAtPath(path).IsValid()
        ]
        if missing_after_export:
            raise RuntimeError(
                "Scoped USDA lost required visual/material prims: "
                f"{missing_after_export}"
            )
    except Exception as exc:
        return {
            "status": "blocked",
            "reason": str(exc),
            "scope_prims": scope_prims,
            "retained_material_prims": material_paths,
        }

    result = {
        "status": "pass",
        "strategy": "population_masked_composed_snapshot",
        "source_root_package_path": "deps/usd/source_root.usd",
        "package_path": "deps/usd/scoped_source.usda",
        "scope_prims": scope_prims,
        "retained_subtree_prims": subtree_paths,
        "retained_material_prims": material_paths,
        "snapshot_asset_path_rewrite": snapshot_rewrite,
        "preserved_stage_metadata": {
            "meters_per_unit": float(UsdGeom.GetStageMetersPerUnit(source_stage)),
            "up_axis": str(UsdGeom.GetStageUpAxis(source_stage)),
            "kilograms_per_unit": (
                float(UsdPhysics.GetStageKilogramsPerUnit(source_stage))
                if "UsdPhysics" in locals()
                else None
            ),
            "time_codes_per_second": float(source_stage.GetTimeCodesPerSecond()),
            "frames_per_second": float(source_stage.GetFramesPerSecond()),
        },
    }
    if request.interaction_profile is not None:
        result["reference_scope_material_relocations"] = (
            reference_scope_material_relocations
        )
    return result


def rewrite_scoped_snapshot_asset_paths(package_root: Path, snapshot_path: Path) -> dict[str, Any]:
    """Rewrite flattened package-internal asset paths to snapshot-relative form.

    `Usd.Stage.Flatten()` resolves authored asset paths.  A snapshot exported
    from a package-local stage can therefore contain absolute temporary output
    paths even though all of its assets are already inside the package.  Those
    paths are not portable package evidence, so rewrite only paths proved to be
    descendants of ``package_root`` and fail closed for anything external.
    """
    text = _read_text(snapshot_path)
    if text is None:
        return {
            "status": "blocked",
            "reason": f"Scoped snapshot is not UTF-8 USDA: {snapshot_path}",
            "rewrite_count": 0,
            "external_asset_paths": [],
        }
    package = package_root.resolve()
    try:
        snapshot_rel = snapshot_path.resolve().relative_to(package).as_posix()
    except ValueError:
        return {
            "status": "blocked",
            "reason": f"Scoped snapshot is outside package root: {snapshot_path}",
            "rewrite_count": 0,
            "external_asset_paths": [],
        }
    snapshot_dir = posixpath.dirname(snapshot_rel) or "."
    external_asset_paths: list[str] = []
    rewrite_actions: list[dict[str, str]] = []

    def replace(match: re.Match[str]) -> str:
        raw = match.group(1).strip()
        if not raw or _is_remote_uri(raw):
            if raw:
                external_asset_paths.append(raw)
            return match.group(0)
        candidate = Path(raw)
        if not candidate.is_absolute():
            return match.group(0)
        try:
            package_rel = candidate.resolve().relative_to(package).as_posix()
        except (OSError, ValueError):
            external_asset_paths.append(raw)
            return match.group(0)
        rewritten = posixpath.relpath(package_rel, start=snapshot_dir)
        rewrite_actions.append(
            {
                "raw_asset_path": raw,
                "package_relative_asset_path": rewritten,
            }
        )
        return f"@{rewritten}@"

    rewritten_text = ASSET_TOKEN_RE.sub(replace, text)
    if external_asset_paths:
        return {
            "status": "blocked",
            "reason": "Scoped snapshot retains an external or remote asset path.",
            "rewrite_count": len(rewrite_actions),
            "rewrite_actions": rewrite_actions,
            "external_asset_paths": sorted(set(external_asset_paths)),
        }
    if rewritten_text != text:
        snapshot_path.write_text(rewritten_text, encoding="utf-8")
    return {
        "status": "pass",
        "rewrite_count": len(rewrite_actions),
        "rewrite_actions": rewrite_actions,
        "external_asset_paths": [],
    }


def _scope_bound_material_paths(
    stage: Any,
    scope_prims: list[str],
    usd_module: Any,
    usd_shade: Any,
) -> list[str]:
    material_paths: set[str] = set()
    for path in scope_prims:
        root = stage.GetPrimAtPath(path)
        for prim in usd_module.PrimRange(root):
            binding = usd_shade.MaterialBindingAPI(prim)
            try:
                material, _relationship = binding.ComputeBoundMaterial()
            except Exception:
                material = None
            if material and material.GetPrim().IsValid():
                material_paths.add(material.GetPath().pathString)
            for relationship in prim.GetRelationships():
                if not relationship.GetName().startswith("material:binding"):
                    continue
                for target in relationship.GetTargets():
                    target_prim = stage.GetPrimAtPath(target)
                    if target_prim and target_prim.IsValid():
                        material_paths.add(target.pathString)
    return sorted(material_paths)


def _relocate_reference_scope_materials(
    scoped_stage: Any,
    asset_entry_prim: str,
    material_paths: list[str],
    usd_module: Any,
    sdf_module: Any,
) -> list[dict[str, str]]:
    """Move bound sibling materials below an interaction asset's entry prim.

    A consumer references ``asset.usd@<asset_entry_prim>`` rather than the
    package's whole ``/World``.  USD therefore drops relationship targets to
    sibling material scopes.  NamespaceEditor keeps the material network and
    fixes binding/connection back-pointers while moving the package-owned
    flattened snapshot; the immutable source layer is never edited.
    """
    entry_path = sdf_module.Path(asset_entry_prim)
    external_paths = [
        sdf_module.Path(path)
        for path in material_paths
        if not sdf_module.Path(path).HasPrefix(entry_path)
    ]
    if not external_paths:
        return []

    material_scope_path = entry_path.AppendChild(REFERENCE_MATERIAL_SCOPE_NAME)
    if scoped_stage.GetPrimAtPath(material_scope_path).IsValid():
        raise RuntimeError(
            f"reserved reference material scope already exists: {material_scope_path}"
        )

    destinations: dict[str, Any] = {}
    for source_path in external_paths:
        source_prim = scoped_stage.GetPrimAtPath(source_path)
        if not source_prim.IsValid() or source_prim.GetTypeName() != "Material":
            raise RuntimeError(
                f"bound material prim is absent or not a Material: {source_path}"
            )
        if source_prim.GetCustomDataByKey(
            SOURCE_MATERIAL_PRIM_CUSTOM_DATA_KEY
        ) is not None:
            raise RuntimeError(
                "source material already uses reserved AAN provenance key: "
                f"{source_path}"
            )
        destination = material_scope_path.AppendChild(source_prim.GetName())
        destination_key = destination.pathString
        if destination_key in destinations:
            raise RuntimeError(
                "reference material destination name collision: "
                f"{destinations[destination_key]} and {source_path} -> {destination}"
            )
        destinations[destination_key] = source_path

    for index, source_path in enumerate(external_paths):
        for other_path in external_paths[index + 1 :]:
            if source_path.HasPrefix(other_path) or other_path.HasPrefix(source_path):
                raise RuntimeError(
                    "nested bound material roots cannot be relocated independently: "
                    f"{source_path}, {other_path}"
                )

    scoped_stage.DefinePrim(material_scope_path, "Scope")
    relocations: list[dict[str, str]] = []
    for source_path in sorted(external_paths, key=lambda path: path.pathString):
        destination = material_scope_path.AppendChild(
            scoped_stage.GetPrimAtPath(source_path).GetName()
        )
        # NamespaceEditor keeps one pending move.  Apply each material with a
        # fresh editor so a multi-material asset cannot silently keep all but
        # the last binding outside the entry reference scope.
        editor = usd_module.NamespaceEditor(scoped_stage)
        if not editor.MovePrimAtPath(source_path, destination):
            raise RuntimeError(
                f"could not schedule material relocation: {source_path} -> {destination}"
            )
        if not editor.CanApplyEdits():
            raise RuntimeError(
                f"could not apply material relocation: {source_path} -> {destination}"
            )
        if not editor.ApplyEdits():
            raise RuntimeError(
                f"material relocation failed: {source_path} -> {destination}"
            )
        relocated = scoped_stage.GetPrimAtPath(destination)
        if not relocated.IsValid() or relocated.GetTypeName() != "Material":
            raise RuntimeError(f"relocated material is missing: {destination}")
        relocated.SetCustomDataByKey(
            SOURCE_MATERIAL_PRIM_CUSTOM_DATA_KEY,
            source_path.pathString,
        )
        relocations.append(
            {
                "source_material_prim": source_path.pathString,
                "package_material_prim": destination.pathString,
                "method": "Usd.NamespaceEditor.MovePrimAtPath",
            }
        )
    return relocations


def _qualify_entry_reference_materials(
    root_usd: Path,
    asset_entry_prim: str,
) -> dict[str, Any]:
    """Prove effective material bindings survive an entry-prim reference."""
    try:
        from pxr import Sdf, Usd, UsdShade  # type: ignore
    except Exception as exc:
        return {
            "status": "blocked",
            "asset_entry_prim": asset_entry_prim,
            "probe_paths": [],
            "qualified_bindings": [],
            "errors": [f"entry reference qualification requires pxr modules: {exc}"],
        }

    errors: list[str] = []
    qualified_bindings: list[dict[str, str]] = []
    try:
        direct_stage = Usd.Stage.Open(str(root_usd))
    except Exception as exc:
        direct_stage = None
        errors.append(f"could not open package entry USD: {exc}")
    entry_path = Sdf.Path(asset_entry_prim)
    entry_prim = direct_stage.GetPrimAtPath(entry_path) if direct_stage else None
    if not entry_prim or not entry_prim.IsValid():
        errors.append(f"asset entry prim is missing: {asset_entry_prim}")

    if entry_prim and entry_prim.IsValid():
        seen: set[tuple[str, str, str]] = set()
        for prim in Usd.PrimRange(entry_prim):
            if prim.GetTypeName() not in REFERENCE_RENDER_PRIM_TYPES:
                continue
            binding_api = UsdShade.MaterialBindingAPI(prim)
            for purpose in (
                UsdShade.Tokens.allPurpose,
                UsdShade.Tokens.preview,
                UsdShade.Tokens.full,
            ):
                try:
                    material, relationship = binding_api.ComputeBoundMaterial(
                        materialPurpose=purpose
                    )
                except Exception as exc:
                    errors.append(
                        f"could not compute {purpose} material at {prim.GetPath()}: {exc}"
                    )
                    continue
                if not material or not material.GetPrim().IsValid():
                    continue
                material_path = material.GetPath()
                key = (
                    prim.GetPath().pathString,
                    str(purpose),
                    material_path.pathString,
                )
                if key in seen:
                    continue
                seen.add(key)
                if not material_path.HasPrefix(entry_path):
                    errors.append(
                        f"effective material remains outside asset_entry_prim: "
                        f"{prim.GetPath()} -> {material_path}"
                    )
                relationship_name = (
                    relationship.GetName() if relationship is not None else ""
                )
                if "collection" in relationship_name:
                    errors.append(
                        f"collection material binding is not reference-qualified: "
                        f"{relationship.GetPath()}"
                    )
                if relationship is not None:
                    for target in relationship.GetTargets():
                        if not target.GetPrimPath().HasPrefix(entry_path):
                            errors.append(
                                "material binding target remains outside asset_entry_prim: "
                                f"{relationship.GetPath()} -> {target}"
                            )
                errors.extend(
                    _material_network_reference_errors(
                        direct_stage,
                        material.GetPrim(),
                        Usd,
                    )
                )
                qualified_bindings.append(
                    {
                        "render_prim": prim.GetPath().pathString,
                        "purpose": str(purpose),
                        "material_prim": material_path.pathString,
                    }
                )

    probe_paths = ["/__aan_nested/reference_probe"]
    if direct_stage is not None and not errors:
        for probe_raw in probe_paths:
            probe_path = Sdf.Path(probe_raw)
            probe_stage = Usd.Stage.CreateInMemory()
            probe = probe_stage.DefinePrim(probe_path, "Xform")
            if not probe.GetReferences().AddReference(
                str(root_usd.resolve()),
                asset_entry_prim,
            ):
                errors.append(f"could not author entry reference at {probe_path}")
                continue
            for binding in qualified_bindings:
                source_render_path = Sdf.Path(binding["render_prim"])
                relative_render_path = source_render_path.MakeRelativePath(entry_path)
                probe_render_path = probe_path.AppendPath(relative_render_path)
                probe_render = probe_stage.GetPrimAtPath(probe_render_path)
                if not probe_render.IsValid():
                    errors.append(
                        f"referenced render prim is missing: {probe_render_path}"
                    )
                    continue
                material, relationship = UsdShade.MaterialBindingAPI(
                    probe_render
                ).ComputeBoundMaterial(materialPurpose=binding["purpose"])
                if not material or not material.GetPrim().IsValid():
                    errors.append(
                        f"referenced effective material is missing: "
                        f"{probe_render_path} ({binding['purpose']})"
                    )
                    continue
                expected_material = Sdf.Path(binding["material_prim"]).ReplacePrefix(
                    entry_path,
                    probe_path,
                )
                if material.GetPath() != expected_material:
                    errors.append(
                        f"referenced material path mismatch: {material.GetPath()} != "
                        f"{expected_material}"
                    )
                if relationship is not None:
                    for target in relationship.GetTargets():
                        if not target.GetPrimPath().HasPrefix(probe_path):
                            errors.append(
                                "referenced material target escapes probe scope: "
                                f"{relationship.GetPath()} -> {target}"
                            )
                errors.extend(
                    _material_network_reference_errors(
                        probe_stage,
                        material.GetPrim(),
                        Usd,
                    )
                )

    return {
        "status": "pass" if not errors else "blocked",
        "asset_entry_prim": asset_entry_prim,
        "probe_paths": probe_paths,
        "qualified_bindings": sorted(
            qualified_bindings,
            key=lambda item: (
                item["render_prim"],
                item["purpose"],
                item["material_prim"],
            ),
        ),
        "errors": sorted(set(errors)),
    }


def _material_network_reference_errors(
    stage: Any,
    material_prim: Any,
    usd_module: Any,
) -> list[str]:
    """Reject shader connections that would escape an entry reference."""
    errors: list[str] = []
    material_path = material_prim.GetPath()
    for prim in usd_module.PrimRange(material_prim):
        for attribute in prim.GetAttributes():
            for target in attribute.GetConnections():
                target_prim_path = target.GetPrimPath()
                target_prim = stage.GetPrimAtPath(target_prim_path)
                if not target_prim.IsValid():
                    errors.append(
                        f"material connection target is invalid: {attribute.GetPath()} -> {target}"
                    )
                elif not target_prim_path.HasPrefix(material_path):
                    errors.append(
                        "material connection target is outside the material subtree: "
                        f"{attribute.GetPath()} -> {target}"
                    )
    return errors


def _minimal_subtree_paths(paths: list[str]) -> list[str]:
    retained: list[str] = []
    for path in sorted(set(paths), key=lambda item: (item.count("/"), item)):
        if any(path == parent or path.startswith(parent.rstrip("/") + "/") for parent in retained):
            continue
        retained.append(path)
    return retained


def _copy_layer_timing_metadata(source_layer: Any, target_layer: Any) -> None:
    target_layer.defaultPrim = source_layer.defaultPrim
    target_layer.startTimeCode = source_layer.startTimeCode
    target_layer.endTimeCode = source_layer.endTimeCode
    target_layer.framesPerSecond = source_layer.framesPerSecond
    target_layer.timeCodesPerSecond = source_layer.timeCodesPerSecond


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
    dependency_closure = {
        "root_layer": str(inventory["root_layer"]),
        "scope_extraction": inventory.get(
            "scope_extraction",
            {
                "status": "not_run",
                "reason": "AAN-03 package writing did not run.",
                "scope_prims": [],
                "retained_material_prims": [],
            },
        ),
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
        "scope_extraction": inventory.get(
            "scope_extraction",
            {
                "status": "not_run",
                "reason": "AAN-03 package writing did not run.",
                "scope_prims": [],
                "retained_material_prims": [],
            },
        ),
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
