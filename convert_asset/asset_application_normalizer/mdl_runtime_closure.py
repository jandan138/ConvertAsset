"""AAN-11 static MDL runtime dependency closure."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
import shutil
import sys
from typing import Any

from .evidence_manifest import sha256_file
from .model import MILESTONE_AAN11


_IMPORT_RE = re.compile(
    r"^\s*import\s+(?P<module>(?:\.?::)?[A-Za-z_][\w]*(?:::[A-Za-z_][\w]*)*)",
    re.MULTILINE,
)
_USING_RE = re.compile(
    r"^\s*using\s+(?P<module>(?:\.?::)?[A-Za-z_][\w]*(?:::[A-Za-z_][\w]*)*)\s+import\b",
    re.MULTILINE,
)
_TEXTURE_RE = re.compile(r"\btexture_2d\s*\(\s*\"(?P<path>[^\"]+)\"")
_MISSING_MODULE_RE = re.compile(r"could not find module\s+(?P<module>[.:\w]+)", re.IGNORECASE)
NATIVE_MDL_MODULES = {"anno", "base", "df", "math", "state", "tex"}
DEFAULT_RUNTIME_MDL_ROOTS = (
    Path("/isaac-sim/kit/mdl/core/mdl"),
    Path("/isaac-sim/kit/mdl/core/Base"),
    Path("/isaac-sim/kit/mdl/core"),
)
VIEW_EVIDENCE_KEYS = {
    "view_id",
    "camera_pose",
    "target_prim",
    "render_hash",
    "mean_rgb",
    "foreground_rgb",
    "non_background_ratio",
    "bbox_ratio",
}


@dataclass(frozen=True)
class MdlRuntimeDependencies:
    mdl_path: Path
    imported_modules: list[str] = field(default_factory=list)
    texture_literals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MaterialRuntimeClosureResult:
    overall_status: str
    return_code: int
    material_runtime_closure: dict[str, Any]
    static_material_runtime_report: dict[str, Any]
    stage_gate: dict[str, Any]
    blocked_reasons: list[dict[str, Any]]


MATERIAL_RUNTIME_NOT_RUN_REPORT = {
    "status": "not_run",
    "root_mdl_count": 0,
    "imported_module_count": 0,
    "mdl_texture_asset_count": 0,
    "blocked_dependency_count": 0,
}


def build_not_run_material_runtime_closure(reason: str) -> MaterialRuntimeClosureResult:
    closure = {
        "status": "not_run",
        "claim_level": "not_claimed",
        "full_material_parity_claimed": False,
        "root_mdl_assets": [],
        "imported_mdl_modules": [],
        "mdl_texture_assets": [],
        "native_runtime_modules": [],
        "mirror_actions": [],
        "rewrite_actions": [],
        "runtime_compiler": {"status": "not_run"},
        "view_evidence": [],
        "reason": reason,
    }
    return MaterialRuntimeClosureResult(
        overall_status="blocked",
        return_code=0,
        material_runtime_closure=closure,
        static_material_runtime_report={**MATERIAL_RUNTIME_NOT_RUN_REPORT, "reason": reason},
        stage_gate={
            "check_id": MILESTONE_AAN11,
            "stage": "material_runtime_closure",
            "status": "not_run",
            "summary": reason,
        },
        blocked_reasons=[],
    )


def parse_mdl_runtime_dependencies(path: Path) -> MdlRuntimeDependencies:
    text = _strip_line_comments(path.read_text(encoding="utf-8", errors="ignore"))
    modules: list[str] = []
    matches = [*_IMPORT_RE.finditer(text), *_USING_RE.finditer(text)]
    for match in sorted(matches, key=lambda item: item.start()):
        module = _normalize_module_reference(match.group("module"))
        if module and module not in modules:
            modules.append(module)

    textures: list[str] = []
    for match in _TEXTURE_RE.finditer(text):
        value = match.group("path").strip()
        if value and value not in textures:
            textures.append(value)

    return MdlRuntimeDependencies(path, modules, textures)


def classify_mdl_module(module: str) -> str:
    root = _module_root(module)
    if root in NATIVE_MDL_MODULES:
        return "native_runtime_module"
    return "required_helper_module"


def discover_mdl_roots(package_root: Path, material_closure: list[dict]) -> list[Path]:
    """Return MDL roots reachable from admitted material bindings.

    A package may retain source mirrors for provenance, but AAN-11 must not
    turn an unrelated scene material into a target-runtime requirement.  When
    AAN-04 has material records, start only from their referenced source MDLs
    and follow package-local helper imports.  The directory-wide fallback is
    retained for direct/legacy callers that do not provide a material closure.
    """
    roots: set[Path] = set()
    for material in material_closure:
        for asset in material.get("source_mdl_assets", []):
            package_path = asset.get("package_path")
            if not package_path:
                continue
            candidate = package_root / str(package_path)
            if candidate.exists() and candidate.suffix.lower() == ".mdl":
                roots.add(candidate)

    if material_closure:
        queue = list(roots)
        while queue:
            root = queue.pop(0)
            for module in parse_mdl_runtime_dependencies(root).imported_modules:
                if classify_mdl_module(module) == "native_runtime_module":
                    continue
                helper = package_root / "deps" / "mdl" / _module_package_file(module)
                if helper.exists() and helper.suffix.lower() == ".mdl" and helper not in roots:
                    roots.add(helper)
                    queue.append(helper)
        return sorted(roots, key=lambda item: item.relative_to(package_root).as_posix())

    mdl_dir = package_root / "deps" / "mdl"
    if mdl_dir.exists():
        roots.update(path for path in mdl_dir.rglob("*.mdl") if path.is_file())

    return sorted(roots, key=lambda item: item.relative_to(package_root).as_posix())


def build_material_runtime_closure(
    package_root: Path,
    material_closure: list[dict],
    required_prims: list[str] | None = None,
    runtime_mdl_roots: list[Path] | None = None,
) -> MaterialRuntimeClosureResult:
    approved_runtime_roots = _existing_runtime_mdl_roots(runtime_mdl_roots)
    mirror_actions = _mirror_mdl_runtime_dependencies(
        package_root,
        material_closure,
        runtime_mdl_roots=approved_runtime_roots,
    )
    roots = discover_mdl_roots(package_root, material_closure)
    module_records: list[dict[str, Any]] = []
    texture_records: list[dict[str, Any]] = []

    for root in roots:
        deps = parse_mdl_runtime_dependencies(root)
        root_rel = root.relative_to(package_root).as_posix()
        for module in deps.imported_modules:
            module_records.append(
                _module_record(package_root, root_rel, module, approved_runtime_roots)
            )
        for texture in deps.texture_literals:
            texture_records.append(_texture_record(package_root, root, root_rel, texture))

    unresolved = [
        record
        for record in [*module_records, *texture_records]
        if record.get("resolution") == "blocked"
    ]
    status = "blocked" if unresolved else "pass"
    return_code = 5 if unresolved else 0
    closure = {
        "status": status,
        "claim_level": (
            "required_surface_runtime_dependency_closure" if status == "pass" else "not_claimed"
        ),
        "full_material_parity_claimed": False,
        "root_mdl_assets": [path.relative_to(package_root).as_posix() for path in roots],
        "imported_mdl_modules": module_records,
        "mdl_texture_assets": texture_records,
        "native_runtime_modules": [
            record
            for record in module_records
            if record.get("resolution") == "native_runtime_module"
        ],
        "mirror_actions": mirror_actions,
        "binding_scope": build_binding_scope_report(
            material_closure,
            required_prims or [],
            package_root=package_root,
        ),
        "rewrite_actions": [],
        "runtime_compiler": {"status": "not_run"},
        "view_evidence": [],
    }
    summary = (
        "AAN-11 material runtime dependency closure passed."
        if status == "pass"
        else "AAN-11 material runtime dependency closure found blocking gaps."
    )
    blockers: list[dict[str, Any]] = []
    if unresolved:
        blockers.append(
            {
                "blocker_id": "aan11_block_required_mdl_runtime_dependency",
                "severity": "blocking",
                "summary": (
                    "One or more required MDL runtime helper modules or textures are unresolved."
                ),
                "count": len(unresolved),
                "required_resolution": (
                    "Mirror the helper MDL/texture into the package, classify it as native "
                    "runtime module, or attach a scoped waiver."
                ),
            }
        )

    return MaterialRuntimeClosureResult(
        overall_status=status,
        return_code=return_code,
        material_runtime_closure=closure,
        static_material_runtime_report={
            "status": status,
            "root_mdl_count": len(roots),
            "imported_module_count": len(module_records),
            "mdl_texture_asset_count": len(texture_records),
            "blocked_dependency_count": len(unresolved),
        },
        stage_gate={
            "check_id": MILESTONE_AAN11,
            "stage": "material_runtime_closure",
            "status": status,
            "summary": summary,
        },
        blocked_reasons=blockers,
    )


def parse_material_runtime_log(text: str) -> dict[str, Any]:
    counters = {
        "stderr_bytes": len(text.encode("utf-8")),
        "error_count": 0,
        "warning_count": 0,
        "mdlc_count": 0,
        "usd_mdl_count": 0,
        "omni_hydra_count": 0,
        "rtx_mdltranslator_count": 0,
        "failed_shader_node_count": 0,
        "missing_texture_count": 0,
    }
    missing_modules: list[str] = []
    exemplars: list[dict[str, str]] = []
    for line in text.splitlines():
        lower = line.lower()
        if "[error]" in lower:
            counters["error_count"] += 1
        if "[warning]" in lower:
            counters["warning_count"] += 1
        if "mdlc" in lower:
            counters["mdlc_count"] += 1
        if "usd_mdl" in lower:
            counters["usd_mdl_count"] += 1
        if "omni.hydra" in lower:
            counters["omni_hydra_count"] += 1
        if "rtx.mdltranslator" in lower:
            counters["rtx_mdltranslator_count"] += 1
        if "failed to create mdl shade node" in lower:
            counters["failed_shader_node_count"] += 1
        if "missing texture" in lower or "could not find texture" in lower:
            counters["missing_texture_count"] += 1

        module_match = _MISSING_MODULE_RE.search(line)
        if module_match:
            module = _module_root(module_match.group("module").lstrip("."))
            if module and module not in missing_modules:
                missing_modules.append(module)

        if _is_material_runtime_log_exemplar(lower) and len(exemplars) < 5:
            exemplars.append(
                {
                    "line_hash": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                    "message": line,
                }
            )

    blocked = bool(
        counters["mdlc_count"]
        or counters["failed_shader_node_count"]
        or counters["missing_texture_count"]
        or missing_modules
    )
    return {
        "status": "blocked" if blocked else "pass",
        "counters": counters,
        "missing_modules": missing_modules,
        "exemplars": exemplars,
    }


def merge_runtime_compiler_report(
    closure: dict[str, Any],
    compiler_report: dict[str, Any],
) -> dict[str, Any]:
    merged = {**closure, "runtime_compiler": compiler_report}
    if compiler_report.get("status") == "blocked":
        merged["status"] = "blocked"
        merged["claim_level"] = "not_claimed"
    return merged


def runtime_compiler_report_from_evidence(
    package_root: Path,
    runtime_evidence: dict[str, Any],
) -> dict[str, Any]:
    log_text_parts = []
    for key in ("stdout_path", "stderr_path"):
        raw_path = runtime_evidence.get(key)
        if not raw_path:
            continue
        path = _runtime_log_path(package_root, str(raw_path))
        if not path.exists():
            continue
        log_text_parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    if not log_text_parts:
        return {
            "status": "not_run",
            "reason": "AAN-06 runtime evidence did not expose readable stdout/stderr logs.",
        }
    return parse_material_runtime_log("\n".join(log_text_parts))


def merge_runtime_compiler_result(
    result: MaterialRuntimeClosureResult,
    compiler_report: dict[str, Any],
) -> MaterialRuntimeClosureResult:
    closure = merge_runtime_compiler_report(result.material_runtime_closure, compiler_report)
    if compiler_report.get("status") != "blocked":
        return MaterialRuntimeClosureResult(
            overall_status=result.overall_status,
            return_code=result.return_code,
            material_runtime_closure=closure,
            static_material_runtime_report={
                **result.static_material_runtime_report,
                "runtime_compiler_status": compiler_report.get("status", "unknown"),
            },
            stage_gate=result.stage_gate,
            blocked_reasons=result.blocked_reasons,
        )

    blocked_reasons = [
        *result.blocked_reasons,
        {
            "blocker_id": "aan11_block_runtime_material_compiler",
            "severity": "blocking",
            "summary": "AAN-06 runtime logs contain required material compiler errors.",
            "required_resolution": (
                "Close the MDL helper/texture/runtime dependency gap and rerun AAN-11/AAN-06."
            ),
        },
    ]
    return MaterialRuntimeClosureResult(
        overall_status="blocked",
        return_code=5,
        material_runtime_closure=closure,
        static_material_runtime_report={
            **result.static_material_runtime_report,
            "status": "blocked",
            "runtime_compiler_status": "blocked",
        },
        stage_gate={
            **result.stage_gate,
            "status": "blocked",
            "summary": "AAN-11 runtime material compiler evidence found blocking errors.",
        },
        blocked_reasons=blocked_reasons,
    )


def merge_material_view_evidence_result(
    result: MaterialRuntimeClosureResult,
    records: list[dict[str, Any]],
) -> MaterialRuntimeClosureResult:
    closure = {
        **result.material_runtime_closure,
        "view_evidence": build_material_view_evidence(records),
    }
    return MaterialRuntimeClosureResult(
        overall_status=result.overall_status,
        return_code=result.return_code,
        material_runtime_closure=closure,
        static_material_runtime_report=result.static_material_runtime_report,
        stage_gate=result.stage_gate,
        blocked_reasons=result.blocked_reasons,
    )


def build_binding_scope_report(
    material_closure: list[dict[str, Any]],
    required_prims: list[str],
    *,
    package_root: Path | None = None,
    root_usd: Path | None = None,
) -> dict[str, Any]:
    effective = _effective_binding_scope_report(
        required_prims,
        root_usd=root_usd or (package_root / "asset.usd" if package_root else None),
    )
    if effective is not None:
        return effective

    required_materials: list[dict[str, str]] = []
    matched: set[str] = set()
    for material in material_closure:
        scope = material.get("binding_scope")
        material_prim = material.get("material_prim")
        if not scope or not material_prim:
            continue
        for required in required_prims:
            if scope == required:
                matched.add(required)
                required_materials.append(
                    {
                        "required_prim": required,
                        "material_prim": material_prim,
                        "binding_source": "material_closure.binding_scope",
                    }
                )
    unknown = [prim for prim in required_prims if prim not in matched]
    return {
        "status": "static_hint" if required_materials else "unknown",
        "required_materials": required_materials,
        "unknown_required_prims": unknown,
        "non_render_required_prims": [],
    }


def _effective_binding_scope_report(
    required_prims: list[str],
    *,
    root_usd: Path | None,
) -> dict[str, Any] | None:
    if not required_prims or root_usd is None or not root_usd.exists():
        return None
    try:
        from pxr import Usd, UsdShade  # type: ignore
    except Exception:
        return None

    try:
        stage = Usd.Stage.Open(str(root_usd))
    except Exception:
        return None
    if stage is None:
        return None

    required_materials: list[dict[str, str]] = []
    unknown: list[str] = []
    non_render: list[str] = []
    for required in required_prims:
        prim = stage.GetPrimAtPath(required)
        if not prim or not prim.IsValid():
            unknown.append(required)
            continue
        records = _effective_binding_records_for_required(required, prim, UsdShade)
        if not records:
            if not _has_render_mesh_scope(prim):
                non_render.append(required)
                continue
            unknown.append(required)
            continue
        required_materials.extend(records)

    if not required_materials and unknown:
        return {
            "status": "unknown",
            "required_materials": [],
            "unknown_required_prims": unknown,
            "non_render_required_prims": non_render,
        }
    return {
        "status": "effective_binding" if required_materials else "no_required_render_mesh",
        "required_materials": required_materials,
        "unknown_required_prims": unknown,
        "non_render_required_prims": non_render,
    }


def _effective_binding_records_for_required(
    required: str,
    prim: Any,
    usd_shade: Any,
) -> list[dict[str, str]]:
    own_record = _effective_binding_record(required, prim, usd_shade)
    if own_record is not None:
        return [own_record]

    records = []
    for render_prim in _iter_render_mesh_prims(prim):
        record = _effective_binding_record(required, render_prim, usd_shade)
        if record is None:
            continue
        record["render_prim"] = render_prim.GetPath().pathString
        records.append(record)
    return records


def _effective_binding_record(
    required: str,
    prim: Any,
    usd_shade: Any,
) -> dict[str, str] | None:
    bound = usd_shade.MaterialBindingAPI(prim).ComputeBoundMaterial()
    material, relationship = _bound_material_and_relationship(bound)
    if material is None or not material.GetPrim().IsValid():
        return None

    binding_prim = prim.GetPath().pathString
    material_prim = material.GetPrim().GetPath().pathString
    bound_at_prim = _binding_relationship_prim_path(relationship) or _authored_binding_prim_path(prim)
    return {
        "required_prim": required,
        "material_prim": material_prim,
        "binding_source": "UsdShade.MaterialBindingAPI.ComputeBoundMaterial",
        "binding_strength": "direct" if bound_at_prim == binding_prim else "inherited_or_weaker",
        "bound_at_prim": bound_at_prim or binding_prim,
    }


def _iter_render_mesh_prims(prim: Any) -> list[Any]:
    meshes = []
    stack = list(prim.GetChildren())
    while stack:
        child = stack.pop(0)
        if child.GetTypeName() == "Mesh":
            meshes.append(child)
        stack.extend(child.GetChildren())
    return meshes


def _has_render_mesh_scope(prim: Any) -> bool:
    return prim.GetTypeName() == "Mesh" or bool(_iter_render_mesh_prims(prim))


def _bound_material_and_relationship(bound: Any) -> tuple[Any | None, Any | None]:
    if isinstance(bound, tuple):
        material = bound[0] if len(bound) > 0 else None
        relationship = bound[1] if len(bound) > 1 else None
        return material, relationship
    return bound, None


def _binding_relationship_prim_path(relationship: Any | None) -> str | None:
    if relationship is None:
        return None
    try:
        prim = relationship.GetPrim()
    except Exception:
        return None
    if prim and prim.IsValid():
        return prim.GetPath().pathString
    return None


def _authored_binding_prim_path(prim: Any) -> str | None:
    current = prim
    while current and current.IsValid():
        relationship = current.GetRelationship("material:binding")
        if relationship and relationship.HasAuthoredTargets():
            return current.GetPath().pathString
        current = current.GetParent()
    return None


def build_material_view_evidence(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for record in records:
        missing = sorted(VIEW_EVIDENCE_KEYS.difference(record))
        if missing:
            raise ValueError(f"material view evidence missing keys: {', '.join(missing)}")
        normalized.append(dict(record))
    return normalized


def _mirror_mdl_runtime_dependencies(
    package_root: Path,
    material_closure: list[dict[str, Any]],
    *,
    runtime_mdl_roots: list[Path],
) -> list[dict[str, Any]]:
    source_by_package = _source_mdl_paths_by_package(material_closure)
    if not source_by_package:
        return []

    actions: list[dict[str, Any]] = []
    queue = sorted(source_by_package)
    visited: set[str] = set()
    while queue:
        root_rel = queue.pop(0)
        if root_rel in visited:
            continue
        visited.add(root_rel)
        package_mdl = package_root / root_rel
        source_mdl = source_by_package.get(root_rel)
        if source_mdl is None or not package_mdl.exists() or not source_mdl.exists():
            continue

        deps = parse_mdl_runtime_dependencies(package_mdl)
        for module in deps.imported_modules:
            package_path, source_path, action = _mirror_helper_module(
                package_root,
                package_mdl,
                source_mdl,
                module,
                runtime_mdl_roots=runtime_mdl_roots,
            )
            if source_path is not None and package_path not in source_by_package:
                source_by_package[package_path] = source_path
                queue.append(package_path)
            if action is not None:
                actions.append(action)
        for texture in deps.texture_literals:
            action = _mirror_mdl_texture(package_root, package_mdl, source_mdl, texture)
            if action is not None:
                actions.append(action)
    return actions


def _source_mdl_paths_by_package(
    material_closure: list[dict[str, Any]],
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for material in material_closure:
        for asset in material.get("source_mdl_assets", []):
            package_path = asset.get("package_path")
            resolved_path = asset.get("resolved_path")
            if not package_path or not resolved_path:
                continue
            source = Path(str(resolved_path))
            if source.exists() and source.is_file():
                paths[str(package_path)] = source
    return paths


def _mirror_helper_module(
    package_root: Path,
    owner_package_mdl: Path,
    owner_source_mdl: Path,
    module: str,
    *,
    runtime_mdl_roots: list[Path],
) -> tuple[str, Path | None, dict[str, Any] | None]:
    package_rel = (Path("deps") / "mdl" / _module_package_file(module)).as_posix()
    package_candidate = package_root / package_rel
    source_candidate = (owner_source_mdl.parent / _module_package_file(module)).resolve()
    if classify_mdl_module(module) == "native_runtime_module":
        return package_rel, None, None
    if package_candidate.exists():
        return package_rel, source_candidate if source_candidate.exists() else None, None
    if not source_candidate.exists() or not source_candidate.is_file():
        runtime = _runtime_module_resolution(module, runtime_mdl_roots)
        if runtime is None:
            return package_rel, None, None
        runtime_module, runtime_root, runtime_path = runtime
        _copy_package_file(runtime_path, package_candidate)
        return package_rel, runtime_path, {
            "action_id": "aan11_mirror_runtime_compatible_helper_mdl",
            "module": module,
            "runtime_module": runtime_module,
            "owner_mdl": owner_package_mdl.relative_to(package_root).as_posix(),
            "source_path": str(runtime_path),
            "runtime_root": str(runtime_root),
            "package_path": package_rel,
            "package_sha256": sha256_file(package_candidate),
            "resolution_source": "target_runtime_module_mirror",
        }

    _copy_package_file(source_candidate, package_candidate)
    return package_rel, source_candidate, {
        "action_id": "aan11_mirror_helper_mdl",
        "module": module,
        "owner_mdl": owner_package_mdl.relative_to(package_root).as_posix(),
        "source_path": str(source_candidate),
        "package_path": package_rel,
        "package_sha256": sha256_file(package_candidate),
    }


def _mirror_mdl_texture(
    package_root: Path,
    owner_package_mdl: Path,
    owner_source_mdl: Path,
    raw_texture: str,
) -> dict[str, Any] | None:
    package_candidate = (owner_package_mdl.parent / raw_texture).resolve()
    try:
        package_rel = package_candidate.relative_to(package_root.resolve()).as_posix()
    except ValueError:
        return None
    if package_candidate.exists():
        return None

    source_candidate = (owner_source_mdl.parent / raw_texture).resolve()
    if source_candidate.exists() and source_candidate.is_file():
        _copy_package_file(source_candidate, package_candidate)
        return {
            "action_id": "aan11_mirror_mdl_texture",
            "raw_asset_path": raw_texture,
            "owner_mdl": owner_package_mdl.relative_to(package_root).as_posix(),
            "source_path": str(source_candidate),
            "package_path": package_rel,
            "package_sha256": sha256_file(package_candidate),
        }

    # Some localized USD packages contain the byte-identical texture next to a
    # second copy of the MDL, while the first copy retains a stale relative
    # literal.  Do not guess among alternatives: only an exactly one package
    # local basename match is a deterministic closure repair.
    alias = _unique_package_local_texture_alias(package_root, package_candidate.name)
    if alias is None:
        return None
    _copy_package_file(alias, package_candidate)
    return {
        "action_id": "aan11_mirror_unique_package_texture_alias",
        "raw_asset_path": raw_texture,
        "owner_mdl": owner_package_mdl.relative_to(package_root).as_posix(),
        "source_path": str(alias),
        "package_path": package_rel,
        "package_sha256": sha256_file(package_candidate),
        "resolution_source": "unique_package_local_basename",
    }


def _unique_package_local_texture_alias(package_root: Path, basename: str) -> Path | None:
    if not basename:
        return None
    candidates = sorted(
        (
            path.resolve()
            for path in package_root.rglob(basename)
            if path.is_file()
        ),
        key=str,
    )
    return candidates[0] if len(candidates) == 1 else None


def _copy_package_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _module_record(
    package_root: Path,
    root_mdl: str,
    module: str,
    runtime_mdl_roots: list[Path],
) -> dict[str, Any]:
    classification = classify_mdl_module(module)
    record: dict[str, Any] = {
        "root_mdl": root_mdl,
        "module": module,
        "classification": classification,
    }
    if classification == "native_runtime_module":
        record["resolution"] = "native_runtime_module"
        return record

    candidate = package_root / "deps" / "mdl" / _module_package_file(module)
    if candidate.exists():
        record.update(
            {
                "resolution": "mirrored",
                "package_path": candidate.relative_to(package_root).as_posix(),
                "package_sha256": sha256_file(candidate),
            }
        )
        return record

    runtime = _runtime_module_resolution(module, runtime_mdl_roots)
    if runtime is not None:
        runtime_module, runtime_root, runtime_path = runtime
        record.update(
            {
                "classification": "approved_runtime_module",
                "resolution": "native_runtime_module",
                "runtime_module": runtime_module,
                "runtime_root": str(runtime_root),
                "runtime_path": str(runtime_path),
                "runtime_sha256": sha256_file(runtime_path),
            }
        )
        return record

    record.update(
        {
            "resolution": "blocked",
            "failure_mode": "missing_helper_module",
            "required_resolution": (
                "Mirror the helper MDL into deps/mdl or classify it as a native runtime module."
            ),
        }
    )
    return record


def _existing_runtime_mdl_roots(runtime_mdl_roots: list[Path] | None) -> list[Path]:
    roots = list(runtime_mdl_roots) if runtime_mdl_roots is not None else []
    if runtime_mdl_roots is None:
        for entry in sys.path:
            site = Path(entry)
            roots.extend(
                [
                    site / "omni" / "mdl" / "core" / "mdl",
                    site / "omni" / "mdl" / "core" / "Base",
                    site / "omni" / "mdl" / "core",
                ]
            )
        roots.extend(DEFAULT_RUNTIME_MDL_ROOTS)
    existing: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.exists() or not resolved.is_dir():
            continue
        seen.add(resolved)
        existing.append(resolved)
    return existing


def _runtime_module_resolution(
    module: str,
    runtime_mdl_roots: list[Path],
) -> tuple[str, Path, Path] | None:
    for runtime_module in _runtime_module_candidates(module):
        module_file = _module_package_file(runtime_module)
        for root in runtime_mdl_roots:
            candidate = root / module_file
            if candidate.exists() and candidate.is_file():
                return runtime_module, root, candidate
    return None


def _runtime_module_candidates(module: str) -> list[str]:
    parts = [part for part in _normalize_module_reference(module).split("::") if part]
    candidates = []
    while parts:
        candidate = "::".join(parts)
        candidates.append(candidate)
        parts = parts[:-1]
    return candidates


def _texture_record(
    package_root: Path,
    owner_mdl: Path,
    root_mdl: str,
    raw_texture: str,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "root_mdl": root_mdl,
        "raw_asset_path": raw_texture,
    }
    candidate = (owner_mdl.parent / raw_texture).resolve()
    package_root_resolved = package_root.resolve()
    try:
        package_path = candidate.relative_to(package_root_resolved).as_posix()
    except ValueError:
        record.update(
            {
                "resolution": "blocked",
                "failure_mode": "package_escape",
                "required_resolution": "Mirror the MDL texture into the package.",
            }
        )
        return record

    record["package_path"] = package_path
    if candidate.exists():
        record.update(
            {
                "resolution": "mirrored",
                "package_sha256": sha256_file(candidate),
            }
        )
        return record

    record.update(
        {
            "resolution": "blocked",
            "failure_mode": "missing_texture",
            "required_resolution": "Mirror the MDL texture into the package.",
        }
    )
    return record


def _strip_line_comments(text: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


def _module_root(raw: str) -> str:
    module = _normalize_module_reference(raw)
    if not module:
        return ""
    return module.split("::", 1)[0]


def _normalize_module_reference(raw: str) -> str:
    module = raw.lstrip(".").strip(":")
    if not module:
        return ""
    parts = [part for part in module.split("::") if part and part != "*"]
    if len(parts) == 2 and parts[0] == parts[1]:
        return parts[0]
    return "::".join(parts)


def _module_package_file(module: str) -> Path:
    return Path(*module.split("::")).with_suffix(".mdl")


def _runtime_log_path(package_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return package_root / path


def _is_material_runtime_log_exemplar(line_lower: str) -> bool:
    needles = (
        "[error]",
        "mdlc",
        "usd_mdl",
        "failed to create mdl shade node",
        "missing texture",
        "could not find texture",
        "could not find module",
    )
    return any(needle in line_lower for needle in needles)
