#!/usr/bin/env python3
"""Plan the exact GRScenes split-level material dependency closure.

The previous reference closure planner identifies the selected scene directories
and selected model roots, but it intentionally stops before copying the shared
`home_scenes/Materials` tree. This planner scans only the selected model USDs,
recovers the concrete material files they reference, and emits a small auditable
plan. It does not copy, hardlink, convert, render, or mutate assets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, NamedTuple


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_REFERENCE_PLAN = (
    PROJECT_ROOT
    / "paper"
    / "shared"
    / "evidence"
    / "raw"
    / "grscene_vlm_grounding"
    / "reference_closure_plan.json"
)
DEFAULT_OUTPUT = DEFAULT_REFERENCE_PLAN.with_name("material_dependency_closure_plan.json")

ASSET_REF_RE = re.compile(r"@([^@\r\n]+)@")
TEXT_ASSET_EXTENSIONS = {".mdl", ".mtlx", ".sdf", ".usd", ".usda"}
MAX_TEXT_SCAN_BYTES = 32 * 1024 * 1024


class DependencyScan(NamedTuple):
    backend: str
    root_asset: Path
    layer_count: int
    resolved_asset_paths: tuple[Path, ...]
    unresolved_asset_paths: tuple[Path, ...]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "unknown"


def _resolve_maybe_missing(path: Path) -> Path:
    return path.resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        _resolve_maybe_missing(path).relative_to(_resolve_maybe_missing(parent))
    except ValueError:
        return False
    return True


def _lexical_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.absolute().relative_to(parent.absolute())
    except ValueError:
        return False
    return True


def _relative_to(path: Path, parent: Path) -> str:
    return _resolve_maybe_missing(path).relative_to(_resolve_maybe_missing(parent)).as_posix()


def _planned_destination(src: Path, *, source_root: Path, scratch_root: Path) -> Path:
    if not _is_relative_to(src, source_root):
        raise ValueError(f"planned material src must be inside source_root: {src}")
    return _resolve_maybe_missing(scratch_root / _resolve_maybe_missing(src).relative_to(source_root))


def _validate_roots(source_root: Path, scratch_root: Path) -> None:
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")


def _asset_ref_to_path(asset_ref: str, *, base_dir: Path) -> Path | None:
    text = asset_ref.strip()
    if not text or "://" in text or text.startswith("anon:"):
        return None
    path = Path(text)
    if path.is_absolute():
        return _resolve_maybe_missing(path)
    return _resolve_maybe_missing(base_dir / path)


def _asset_refs_from_text_file(path: Path) -> list[str]:
    try:
        if path.stat().st_size > MAX_TEXT_SCAN_BYTES:
            return []
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return sorted({match.strip() for match in ASSET_REF_RE.findall(text) if match.strip()})


def _looks_like_text_asset(path: Path) -> bool:
    return path.suffix.lower() in TEXT_ASSET_EXTENSIONS


def _scan_text_dependencies(root_asset: Path) -> DependencyScan:
    resolved: set[Path] = set()
    unresolved: set[Path] = set()
    visited: set[Path] = set()
    queue = [_resolve_maybe_missing(root_asset)]

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for asset_ref in _asset_refs_from_text_file(current):
            candidate = _asset_ref_to_path(asset_ref, base_dir=current.parent)
            if candidate is None:
                continue
            if candidate.exists():
                resolved_candidate = _resolve_maybe_missing(candidate)
                resolved.add(resolved_candidate)
                if _looks_like_text_asset(resolved_candidate):
                    queue.append(resolved_candidate)
            else:
                unresolved.add(candidate)

    return DependencyScan(
        backend="text",
        root_asset=_resolve_maybe_missing(root_asset),
        layer_count=len(visited),
        resolved_asset_paths=tuple(sorted(resolved)),
        unresolved_asset_paths=tuple(sorted(unresolved)),
    )


def _path_from_pxr_asset(value: Any) -> Path | None:
    resolved_path = getattr(value, "resolvedPath", None)
    if resolved_path:
        return _resolve_maybe_missing(Path(str(resolved_path)))
    asset_path = getattr(value, "path", None)
    if asset_path:
        return _resolve_maybe_missing(Path(str(asset_path)))
    text = str(value).strip()
    if not text:
        return None
    return _resolve_maybe_missing(Path(text))


def _pxr_unresolved_to_path(value: Any, *, base_dir: Path) -> Path | None:
    text = str(value).strip()
    if not text or "://" in text or text.startswith("anon:"):
        return None
    path = Path(text)
    if path.is_absolute():
        return _resolve_maybe_missing(path)
    return _resolve_maybe_missing(base_dir / path)


def _scan_pxr_dependencies(root_asset: Path) -> DependencyScan:
    # Keep pxr lazy so normal unit tests can import this module without Isaac.
    from pxr import UsdUtils  # type: ignore

    resolved_root_asset = _resolve_maybe_missing(root_asset)
    layers, assets, unresolved = UsdUtils.ComputeAllDependencies(str(resolved_root_asset))
    resolved_paths = {
        path
        for asset in assets
        for path in [_path_from_pxr_asset(asset)]
        if path is not None
    }
    unresolved_paths = {
        path
        for asset_path in unresolved
        for path in [_pxr_unresolved_to_path(asset_path, base_dir=resolved_root_asset.parent)]
        if path is not None
    }
    return DependencyScan(
        backend="pxr",
        root_asset=resolved_root_asset,
        layer_count=len(layers),
        resolved_asset_paths=tuple(sorted(resolved_paths)),
        unresolved_asset_paths=tuple(sorted(unresolved_paths)),
    )


def _scan_dependencies(root_asset: Path, backend: str) -> DependencyScan:
    if backend == "text":
        return _scan_text_dependencies(root_asset)
    if backend == "pxr":
        return _scan_pxr_dependencies(root_asset)
    if backend == "auto":
        try:
            return _scan_pxr_dependencies(root_asset)
        except Exception:
            return _scan_text_dependencies(root_asset)
    raise ValueError(f"unsupported dependency backend: {backend}")


def _material_tail(path: Path, *, model_root: Path, split_materials_root: Path) -> Path | None:
    resolved = _resolve_maybe_missing(path)
    split_resolved = _resolve_maybe_missing(split_materials_root)
    try:
        tail = resolved.relative_to(split_resolved)
        return tail if tail.parts else None
    except ValueError:
        pass

    model_materials = model_root / "Materials"
    if _lexical_is_relative_to(path, model_materials):
        tail = path.absolute().relative_to(model_materials.absolute())
        return tail if tail.parts else None

    return None


def _candidate_from_material_tail(path: Path, *, model_root: Path, split_materials_root: Path) -> Path | None:
    tail = _material_tail(path, model_root=model_root, split_materials_root=split_materials_root)
    if tail is None:
        return None
    return _resolve_maybe_missing(split_materials_root / tail)


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _material_record(
    *,
    computed_path: Path,
    source_path: Path,
    source_root: Path,
    scratch_root: Path,
    source_type: str,
) -> dict[str, Any]:
    if not _is_relative_to(source_path, source_root):
        raise ValueError(f"material dependency must resolve inside source_root: {source_path}")
    dst = _planned_destination(source_path, source_root=source_root, scratch_root=scratch_root)
    return {
        "computed_asset_path": str(_resolve_maybe_missing(computed_path)),
        "source_path": str(_resolve_maybe_missing(source_path)),
        "dst": str(dst),
        "source_relative_path": _relative_to(source_path, source_root),
        "scratch_relative_path": _relative_to(dst, scratch_root),
        "source_type": source_type,
        "size_bytes": _file_size(source_path),
    }


def _missing_material_record(
    *,
    computed_path: Path,
    recovered_source_path: Path,
    source_root: Path,
    source_type: str,
) -> dict[str, Any]:
    return {
        "computed_asset_path": str(_resolve_maybe_missing(computed_path)),
        "recovered_source_path": str(_resolve_maybe_missing(recovered_source_path)),
        "recovered_source_relative_path": _relative_to(recovered_source_path, source_root)
        if _is_relative_to(recovered_source_path, source_root)
        else None,
        "source_type": source_type,
    }


def _add_dependency_candidate(
    candidate: Path,
    *,
    model_root: Path,
    split_materials_root: Path,
    source_root: Path,
    scratch_root: Path,
    source_type: str,
    required: dict[str, dict[str, Any]],
    missing: dict[str, dict[str, Any]],
    unresolved_non_material: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    recovered = _candidate_from_material_tail(
        candidate,
        model_root=model_root,
        split_materials_root=split_materials_root,
    )
    source_path: Path | None = None
    if candidate.exists():
        source_path = _resolve_maybe_missing(candidate)
    elif recovered is not None and recovered.exists():
        source_path = recovered

    if source_path is not None:
        if not source_path.is_file():
            missing.setdefault(
                str(_resolve_maybe_missing(source_path)),
                _missing_material_record(
                    computed_path=candidate,
                    recovered_source_path=source_path,
                    source_root=source_root,
                    source_type="material_dependency_is_not_file",
                ),
            )
            return None
        if not _is_relative_to(source_path, split_materials_root):
            unresolved_non_material.setdefault(
                str(_resolve_maybe_missing(candidate)),
                {
                    "computed_asset_path": str(_resolve_maybe_missing(candidate)),
                    "reason": "resolved_material_realpath_outside_split_materials",
                    "source_type": source_type,
                },
            )
            return None
        if _candidate_from_material_tail(
            source_path,
            model_root=model_root,
            split_materials_root=split_materials_root,
        ) is None:
            if _is_relative_to(source_path, model_root):
                return None
            unresolved_non_material.setdefault(
                str(_resolve_maybe_missing(candidate)),
                {
                    "computed_asset_path": str(_resolve_maybe_missing(candidate)),
                    "reason": "resolved_dependency_is_not_under_materials",
                    "source_type": source_type,
                },
            )
            return None
        record = _material_record(
            computed_path=candidate,
            source_path=source_path,
            source_root=source_root,
            scratch_root=scratch_root,
            source_type=source_type,
        )
        existing = required.setdefault(record["source_path"], record)
        return existing

    if recovered is not None:
        record = _missing_material_record(
            computed_path=candidate,
            recovered_source_path=recovered,
            source_root=source_root,
            source_type=source_type,
        )
        missing.setdefault(str(_resolve_maybe_missing(recovered)), record)
        return None

    unresolved_non_material.setdefault(
        str(_resolve_maybe_missing(candidate)),
        {
            "computed_asset_path": str(_resolve_maybe_missing(candidate)),
            "reason": "unresolved_dependency_has_no_material_tail",
            "source_type": source_type,
        },
    )
    return None


def _expand_text_material_dependencies(
    *,
    model_root: Path,
    split_materials_root: Path,
    source_root: Path,
    scratch_root: Path,
    required: dict[str, dict[str, Any]],
    missing: dict[str, dict[str, Any]],
    unresolved_non_material: dict[str, dict[str, Any]],
) -> None:
    visited: set[str] = set()
    queue = [Path(source_path) for source_path in sorted(required)]
    while queue:
        current = _resolve_maybe_missing(queue.pop(0))
        current_key = str(current)
        if current_key in visited:
            continue
        visited.add(current_key)
        if not _looks_like_text_asset(current):
            continue
        for asset_ref in _asset_refs_from_text_file(current):
            candidate = _asset_ref_to_path(asset_ref, base_dir=current.parent)
            if candidate is None:
                continue
            before = set(required)
            record = _add_dependency_candidate(
                candidate,
                model_root=model_root,
                split_materials_root=split_materials_root,
                source_root=source_root,
                scratch_root=scratch_root,
                source_type="expanded_from_material_text_reference",
                required=required,
                missing=missing,
                unresolved_non_material=unresolved_non_material,
            )
            if record is None:
                continue
            source_path = record["source_path"]
            if source_path not in before:
                queue.append(Path(source_path))


def _model_root_for_action(action: dict[str, Any]) -> Path:
    return _resolve_maybe_missing(Path(str(action["src"])))


def _root_asset_for_action(action: dict[str, Any], *, model_root: Path) -> Path:
    targets = action.get("targets") or []
    for target in targets:
        resolved_model_path = str(target.get("resolved_model_path") or "").strip()
        if resolved_model_path:
            return _resolve_maybe_missing(Path(resolved_model_path))
    return _resolve_maybe_missing(model_root / "instance.usd")


def _materials_entry_repair_action(
    *,
    action: dict[str, Any],
    model_root: Path,
    split_materials_root: Path,
    source_root: Path,
    scratch_root: Path,
) -> dict[str, Any] | None:
    entry = action.get("materials_entry") or {}
    entry_type = str(entry.get("type") or "unknown")
    if entry_type not in {"pointer_file", "missing"}:
        return None

    scratch_model_root = _planned_destination(model_root, source_root=source_root, scratch_root=scratch_root)
    scratch_split_materials_root = _planned_destination(
        split_materials_root,
        source_root=source_root,
        scratch_root=scratch_root,
    )
    target_text = os.path.relpath(scratch_split_materials_root, start=scratch_model_root)
    return {
        "kind": "model_materials_entry_repair",
        "mode": "replace_pointer_file_with_relative_symlink"
        if entry_type == "pointer_file"
        else "create_relative_symlink",
        "dst": str(scratch_model_root / "Materials"),
        "target_text": target_text,
        "model_root": str(model_root),
        "scratch_model_root": str(scratch_model_root),
        "scratch_split_materials_root": str(scratch_split_materials_root),
        "source_entry_type": entry_type,
        "reason": "model_materials_entry_must_resolve_to_split_materials_in_scratch",
    }


def _entry_warnings(action: dict[str, Any], *, repair_action: dict[str, Any] | None) -> set[str]:
    warnings = {str(warning) for warning in action.get("warnings", []) if str(warning)}
    entry = action.get("materials_entry") or {}
    entry_type = str(entry.get("type") or "unknown")
    target_scope = str(entry.get("target_scope") or "")

    if entry_type == "symlink" and target_scope != "inside_model_root":
        warnings.add("materials_symlink_escapes_selected_root")
        warnings.add("model_root_only_materialization_unsafe")
        warnings.add("unresolved_split_level_material_closure")
    elif entry_type == "pointer_file":
        warnings.add("materials_pointer_file_not_usd_resolvable")
        warnings.add("model_root_only_materialization_unsafe")
        warnings.add("unresolved_split_level_material_closure")
    elif entry_type == "missing":
        warnings.add("materials_entry_missing_requires_usd_dependency_scan")
        warnings.add("model_root_only_materialization_unsafe")
        warnings.add("unresolved_split_level_material_closure")

    if repair_action is not None:
        warnings.add("scratch_materials_entry_repair_required")
    return warnings


def _model_dependency_plan(
    action: dict[str, Any],
    *,
    source_root: Path,
    scratch_root: Path,
    dependency_backend: str,
) -> dict[str, Any]:
    model_root = _model_root_for_action(action)
    if not _is_relative_to(model_root, source_root):
        raise ValueError(f"model action src must be inside source_root: {model_root}")

    action_dst = _resolve_maybe_missing(Path(str(action["dst"])))
    if not _is_relative_to(action_dst, scratch_root):
        raise ValueError(f"model action dst must be inside scratch_root: {action_dst}")

    split_root = _resolve_maybe_missing(Path(str(action["split_root"])))
    if not _is_relative_to(split_root, source_root):
        raise ValueError(f"model split_root must be inside source_root: {split_root}")
    split_materials_root = _resolve_maybe_missing(split_root / "Materials")
    if not _is_relative_to(split_materials_root, source_root):
        raise ValueError(f"split Materials root must be inside source_root: {split_materials_root}")

    root_asset = _root_asset_for_action(action, model_root=model_root)
    if not _is_relative_to(root_asset, model_root):
        raise ValueError(f"resolved_model_path must be inside model action src: {root_asset}")

    repair_action = _materials_entry_repair_action(
        action=action,
        model_root=model_root,
        split_materials_root=split_materials_root,
        source_root=source_root,
        scratch_root=scratch_root,
    )
    scan = _scan_dependencies(root_asset, dependency_backend)
    required: dict[str, dict[str, Any]] = {}
    missing: dict[str, dict[str, Any]] = {}
    unresolved_non_material: dict[str, dict[str, Any]] = {}

    for path in scan.resolved_asset_paths:
        _add_dependency_candidate(
            path,
            model_root=model_root,
            split_materials_root=split_materials_root,
            source_root=source_root,
            scratch_root=scratch_root,
            source_type="resolved_dependency",
            required=required,
            missing=missing,
            unresolved_non_material=unresolved_non_material,
        )

    for path in scan.unresolved_asset_paths:
        _add_dependency_candidate(
            path,
            model_root=model_root,
            split_materials_root=split_materials_root,
            source_root=source_root,
            scratch_root=scratch_root,
            source_type="recovered_from_unresolved_material_path",
            required=required,
            missing=missing,
            unresolved_non_material=unresolved_non_material,
        )

    _expand_text_material_dependencies(
        model_root=model_root,
        split_materials_root=split_materials_root,
        source_root=source_root,
        scratch_root=scratch_root,
        required=required,
        missing=missing,
        unresolved_non_material=unresolved_non_material,
    )

    warnings = _entry_warnings(action, repair_action=repair_action)
    if scan.unresolved_asset_paths:
        warnings.add("usd_dependency_unresolved")
    if missing:
        warnings.add("missing_material_dependency_after_split_recovery")
    if unresolved_non_material:
        warnings.add("unresolved_non_material_dependency")
        for item in unresolved_non_material.values():
            reason = str(item.get("reason") or "")
            if reason:
                warnings.add(reason)
    if not split_materials_root.exists():
        warnings.add("split_materials_root_missing")
    if missing or unresolved_non_material:
        coverage_status = "incomplete"
    elif repair_action is not None:
        coverage_status = "material_files_resolved_entry_repair_required"
    else:
        coverage_status = "complete"

    return {
        "model_root": str(model_root),
        "root_asset": str(root_asset),
        "split_root": str(split_root),
        "split_materials_root": str(split_materials_root),
        "materials_entry": action.get("materials_entry", {}),
        "target_count": len(action.get("targets") or []),
        "targets": action.get("targets") or [],
        "dependency_scan": {
            "backend": scan.backend,
            "layer_count": scan.layer_count,
            "resolved_asset_count": len(scan.resolved_asset_paths),
            "unresolved_asset_count": len(scan.unresolved_asset_paths),
        },
        "required_material_assets": sorted(required.values(), key=lambda item: item["source_path"]),
        "missing_material_assets": sorted(missing.values(), key=lambda item: item["recovered_source_path"]),
        "unresolved_non_material_assets": sorted(
            unresolved_non_material.values(), key=lambda item: item["computed_asset_path"]
        ),
        "materials_entry_repair_action": repair_action,
        "required_material_asset_count": len(required),
        "missing_material_asset_count": len(missing),
        "unresolved_non_material_asset_count": len(unresolved_non_material),
        "warnings": sorted(warnings),
        "coverage_status": coverage_status,
    }


def _warning_counts(models: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for model in models:
        for warning in model.get("warnings", []):
            counts[warning] = counts.get(warning, 0) + 1
    return counts


def _material_actions_from_models(
    models: list[dict[str, Any]], *, source_root: Path, scratch_root: Path
) -> list[dict[str, Any]]:
    by_source: dict[str, dict[str, Any]] = {}
    for model in models:
        for asset in model.get("required_material_assets", []):
            source_path = str(asset["source_path"])
            entry = by_source.setdefault(
                source_path,
                {
                    "kind": "material_asset_file",
                    "src": source_path,
                    "dst": asset["dst"],
                    "copy_mode": "hardlink",
                    "source_relative_path": asset["source_relative_path"],
                    "scratch_relative_path": asset["scratch_relative_path"],
                    "size_bytes": asset["size_bytes"],
                    "referenced_by_model_roots": [],
                    "source_types": [],
                },
            )
            entry["referenced_by_model_roots"].append(model["model_root"])
            entry["source_types"].append(asset["source_type"])

    actions = []
    for entry in by_source.values():
        entry["referenced_by_model_roots"] = sorted(set(entry["referenced_by_model_roots"]))
        entry["referenced_by_model_root_count"] = len(entry["referenced_by_model_roots"])
        entry["source_types"] = sorted(set(entry["source_types"]))
        src = Path(str(entry["src"]))
        dst = Path(str(entry["dst"]))
        if not _is_relative_to(src, source_root):
            raise ValueError(f"material action src must be inside source_root: {src}")
        if not _is_relative_to(dst, scratch_root):
            raise ValueError(f"material action dst must be inside scratch_root: {dst}")
        actions.append(entry)
    return sorted(actions, key=lambda item: item["src"])


def _materials_entry_repair_actions_from_models(models: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = [
        model["materials_entry_repair_action"]
        for model in models
        if model.get("materials_entry_repair_action") is not None
    ]
    return sorted(actions, key=lambda item: item["dst"])


def _unique_missing_materials(models: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for model in models:
        for item in model.get("missing_material_assets", []):
            out.setdefault(str(item["recovered_source_path"]), item)
    return sorted(out.values(), key=lambda item: item["recovered_source_path"])


def _unique_unresolved_non_materials(models: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for model in models:
        for item in model.get("unresolved_non_material_assets", []):
            out.setdefault(str(item["computed_asset_path"]), item)
    return sorted(out.values(), key=lambda item: item["computed_asset_path"])


def build_material_dependency_closure_plan(
    reference_plan: dict[str, Any],
    *,
    dependency_backend: str = "pxr",
    limit_models: int | None = None,
) -> dict[str, Any]:
    source_root = _resolve_maybe_missing(Path(str(reference_plan["source_root"])))
    scratch_root = _resolve_maybe_missing(Path(str(reference_plan["scratch_root"])))
    _validate_roots(source_root, scratch_root)

    model_actions = [
        action for action in reference_plan.get("actions", []) if action.get("kind") == "target_model_root"
    ]
    model_actions = sorted(model_actions, key=lambda item: str(item.get("src")))
    if limit_models is not None:
        if limit_models < 0:
            raise ValueError("limit_models must be non-negative")
        model_actions = model_actions[:limit_models]

    models = [
        _model_dependency_plan(
            action,
            source_root=source_root,
            scratch_root=scratch_root,
            dependency_backend=dependency_backend,
        )
        for action in model_actions
    ]
    material_file_actions = _material_actions_from_models(models, source_root=source_root, scratch_root=scratch_root)
    materials_entry_repair_actions = _materials_entry_repair_actions_from_models(models)
    missing_materials = _unique_missing_materials(models)
    unresolved_non_materials = _unique_unresolved_non_materials(models)
    warning_counts = _warning_counts(models)
    scan_resolved_asset_count = sum(int(model["dependency_scan"]["resolved_asset_count"]) for model in models)
    scan_unresolved_asset_count = sum(int(model["dependency_scan"]["unresolved_asset_count"]) for model in models)
    recovered_from_unresolved_paths = {
        str(asset["source_path"])
        for model in models
        for asset in model.get("required_material_assets", [])
        if asset.get("source_type") == "recovered_from_unresolved_material_path"
    }
    safe_to_materialize = not missing_materials and not unresolved_non_materials
    ready_for_nomdl_after_material_file_actions = safe_to_materialize and not materials_entry_repair_actions
    material_closure_status = (
        "requires_missing_dependency_resolution"
        if not safe_to_materialize
        else "selected_material_dependencies_resolved_with_entry_repairs_required"
        if materials_entry_repair_actions
        else "selected_material_dependencies_resolved"
    )

    return {
        "schema_version": 1,
        "status": "planned_material_dependency_closure",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_material_dependency_closure.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generator_git_commit": _git_commit(),
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "reference_plan_status": reference_plan.get("status"),
        "summary": {
            "dependency_backend": dependency_backend,
            "model_root_count": len(models),
            "model_dependency_scan_resolved_asset_count": scan_resolved_asset_count,
            "model_dependency_scan_unresolved_asset_count": scan_unresolved_asset_count,
            "recovered_from_unresolved_material_asset_count": len(recovered_from_unresolved_paths),
            "required_material_asset_count": len(material_file_actions),
            "required_material_total_size_bytes": sum(int(action.get("size_bytes", 0)) for action in material_file_actions),
            "missing_material_asset_count": len(missing_materials),
            "unresolved_non_material_asset_count": len(unresolved_non_materials),
            "material_file_action_count": len(material_file_actions),
            "materials_entry_repair_action_count": len(materials_entry_repair_actions),
            "warning_counts": warning_counts,
            "copy_mode": "hardlink",
            "planner_only": True,
            "safe_to_materialize_selected_materials": safe_to_materialize,
            "requires_materials_entry_repair_before_nomdl": bool(materials_entry_repair_actions),
            "ready_for_nomdl_after_material_file_actions": ready_for_nomdl_after_material_file_actions,
            "material_closure_status": material_closure_status,
        },
        "models": models,
        "material_file_actions": material_file_actions,
        "materials_entry_repair_actions": materials_entry_repair_actions,
        "missing_material_assets": missing_materials,
        "unresolved_non_material_assets": unresolved_non_materials,
        "notes": [
            "This is a planner-only artifact; it does not copy, hardlink, convert, render, or mutate assets.",
            "Material file actions enumerate only concrete files needed by selected model USD dependencies.",
            "Do not mirror the full split-level Materials tree unless a later planner proves the subset is insufficient.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-plan", type=Path, default=DEFAULT_REFERENCE_PLAN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dependency-backend", choices=("pxr", "text", "auto"), default="pxr")
    parser.add_argument("--limit-models", type=int, default=None)
    args = parser.parse_args()

    reference_plan = _load_json(args.reference_plan)
    plan = build_material_dependency_closure_plan(
        reference_plan,
        dependency_backend=args.dependency_backend,
        limit_models=args.limit_models,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} with {plan['summary']['model_root_count']} model roots, "
        f"{plan['summary']['required_material_asset_count']} material files, "
        f"{plan['summary']['missing_material_asset_count']} missing material dependencies"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
