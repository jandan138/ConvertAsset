#!/usr/bin/env python3
"""Plan the GRScenes target/reference closure for the ACL VLM pilot.

This script is intentionally pure Python. It does not import pxr, open USD
stages, copy assets, run no-MDL, or mutate source/scratch datasets. It turns
resolved target prim records into a small, auditable filesystem closure plan so
the next materializer can avoid mirroring whole split-level GRScenes resources.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_SOURCE_MANIFEST = (
    PROJECT_ROOT
    / "paper"
    / "shared"
    / "evidence"
    / "raw"
    / "grscene_vlm_grounding"
    / "source_manifest.json"
)
DEFAULT_TARGET_MANIFEST = DEFAULT_SOURCE_MANIFEST.with_name("target_manifest.json")
DEFAULT_OUTPUT = DEFAULT_SOURCE_MANIFEST.with_name("reference_closure_plan.json")


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


def _relative_to(path: Path, parent: Path) -> str:
    return _resolve_maybe_missing(path).relative_to(_resolve_maybe_missing(parent)).as_posix()


def _lexical_relative_to(path: Path, parent: Path) -> str:
    return path.absolute().relative_to(parent.absolute()).as_posix()


def _dataset_roots(source_manifest: dict[str, Any]) -> tuple[Path, Path]:
    roles = source_manifest.get("dataset_roles") or {}
    benchmark = roles.get("benchmark_source_dataset") or {}
    intervention = roles.get("intervention_outputs") or {}
    source_root_text = str(benchmark.get("local_root") or "").strip()
    scratch_root_text = str(intervention.get("scratch_root") or "").strip()
    if not source_root_text or not scratch_root_text:
        raise ValueError("source_manifest must define benchmark source_root and intervention scratch_root")
    return Path(source_root_text).resolve(), Path(scratch_root_text).resolve()


def _validate_roots(source_root: Path, scratch_root: Path) -> None:
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")


def _scene_lookup(source_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scenes = source_manifest.get("scenes") or []
    return {str(scene.get("source_scene_id")): scene for scene in scenes if scene.get("source_scene_id")}


def _resolved_records(target_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        record
        for record in target_manifest.get("episode_records", [])
        if str(record.get("mapping_status", "")).startswith("resolved_")
        and record.get("target_prim_path")
        and record.get("resolved_model_path")
    ]


def _target_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(record.get("source_scene_id")),
        str(record.get("object_instance_id")),
        str(record.get("target_prim_path")),
    )


def _model_root_for_path(model_path: Path) -> Path:
    resolved = _resolve_maybe_missing(model_path)
    if resolved.exists() and resolved.is_dir():
        return resolved
    return resolved.parent


def _split_root_for_model(source_root: Path, scene_split: str) -> Path:
    if not scene_split:
        raise ValueError("target record must include source_scene_split for material closure planning")
    return (source_root / "scenes" / "GRScenes-100" / scene_split).resolve()


def _path_scope(path: Path | None, *, model_root: Path, split_root: Path) -> str:
    if path is None:
        return "missing"
    if _is_relative_to(path, model_root):
        return "inside_model_root"
    if _is_relative_to(path, split_root):
        return "inside_split_root_outside_model_root"
    return "outside_split_root"


def _read_pointer_text(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    if not text or "\n" in text:
        return None
    return text


def _classify_materials_entry(model_root: Path, *, split_root: Path) -> dict[str, Any]:
    materials_path = model_root / "Materials"
    entry: dict[str, Any] = {
        "path": str(materials_path),
        "relative_path": materials_path.relative_to(model_root).as_posix(),
        "type": "missing",
        "target_text": None,
        "resolved_path": None,
        "target_exists": False,
        "target_scope": "missing",
    }
    resolved_path: Path | None = None
    target_text: str | None = None
    if materials_path.is_symlink():
        target_text = os.readlink(materials_path)
        resolved_path = _source_symlink_target(materials_path)
        entry["type"] = "symlink"
    elif materials_path.is_dir():
        resolved_path = materials_path.resolve()
        entry["type"] = "dir"
    elif materials_path.is_file():
        target_text = _read_pointer_text(materials_path)
        if target_text:
            resolved_path = _resolve_maybe_missing(materials_path.parent / target_text)
            entry["type"] = "pointer_file"
        else:
            resolved_path = materials_path.resolve()
            entry["type"] = "file"
    else:
        candidate = split_root / "Materials"
        if candidate.exists():
            resolved_path = candidate.resolve()

    entry["target_text"] = target_text
    entry["resolved_path"] = str(resolved_path) if resolved_path is not None else None
    entry["target_exists"] = bool(resolved_path is not None and resolved_path.exists())
    entry["target_scope"] = _path_scope(resolved_path, model_root=model_root, split_root=split_root)
    return entry


def _planned_external_resource(
    *,
    resource_name: str,
    src: Path | None,
    source_root: Path,
    scratch_root: Path,
    reason: str,
) -> dict[str, Any] | None:
    if src is None or not _is_relative_to(src, source_root):
        return None
    dst = _planned_destination(src, source_root=source_root, scratch_root=scratch_root)
    return {
        "resource_name": resource_name,
        "src": str(src),
        "dst": str(dst),
        "source_relative_path": _relative_to(src, source_root),
        "scratch_relative_path": _relative_to(dst, scratch_root),
        "reason": reason,
    }


def _materials_risk(
    *,
    model_root: Path,
    split_root: Path,
    source_root: Path,
    scratch_root: Path,
) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    entry = _classify_materials_entry(model_root, split_root=split_root)
    warnings: list[str] = []
    required_roots: list[dict[str, Any]] = []
    target_path = Path(str(entry["resolved_path"])) if entry.get("resolved_path") else None
    target_scope = str(entry.get("target_scope"))
    entry_type = str(entry.get("type"))

    if entry_type == "symlink" and target_scope != "inside_model_root":
        warnings.append("materials_symlink_escapes_selected_root")
    if entry_type == "pointer_file":
        warnings.append("materials_pointer_file_not_usd_resolvable")
    if entry_type == "missing":
        warnings.append("materials_entry_missing_requires_usd_dependency_scan")
    if target_scope == "inside_split_root_outside_model_root" or entry_type in {"pointer_file", "missing"}:
        warnings.append("unresolved_split_level_material_closure")
        required = _planned_external_resource(
            resource_name="Materials",
            src=target_path,
            source_root=source_root,
            scratch_root=scratch_root,
            reason="model_materials_entry_points_outside_selected_model_root",
        )
        if required:
            required_roots.append(required)
    if warnings:
        warnings.insert(0, "model_root_only_materialization_unsafe")
    return entry, sorted(set(warnings)), required_roots


def _validate_duplicate_target_metadata(items: list[dict[str, Any]]) -> None:
    if len(items) <= 1:
        return
    first = items[0]
    for item in items[1:]:
        for field_name in ("resolved_model_path", "reference_asset_path", "object_category"):
            if item.get(field_name) != first.get(field_name):
                raise ValueError(f"inconsistent duplicate target metadata: {field_name} differs")


def _validate_target_manifest_provenance(target_manifest: dict[str, Any], *, source_root: Path) -> None:
    roles = target_manifest.get("dataset_roles") or {}
    benchmark = roles.get("benchmark_source_dataset") or {}
    target_source_root_text = str(benchmark.get("local_root") or "").strip()
    if target_source_root_text and Path(target_source_root_text).resolve() != source_root:
        raise ValueError("target_manifest benchmark source root must match source_manifest")

    for record in target_manifest.get("episode_records", []) or []:
        record_source_root_text = str(record.get("source_dataset_root") or "").strip()
        if record_source_root_text and Path(record_source_root_text).resolve() != source_root:
            raise ValueError("target record source_dataset_root must match source_root")


def _group_unique_targets(records: Iterable[dict[str, Any]], *, limit_targets: int | None = None) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(_target_key(record), []).append(record)

    targets: list[dict[str, Any]] = []
    for key, items in grouped.items():
        items = sorted(items, key=lambda item: str(item.get("stable_episode_id", "")))
        _validate_duplicate_target_metadata(items)
        first = items[0]
        targets.append(
            {
                "source_scene_id": key[0],
                "source_scene_split": first.get("source_scene_split"),
                "object_instance_id": key[1],
                "target_prim_path": key[2],
                "object_category": first.get("object_category"),
                "reference_asset_path": first.get("reference_asset_path"),
                "resolved_model_path": first.get("resolved_model_path"),
                "linked_episode_ids": [str(item.get("stable_episode_id")) for item in items],
                "linked_episode_count": len(items),
            }
        )

    targets.sort(key=lambda item: (item["source_scene_id"], item["object_instance_id"], item["target_prim_path"]))
    if limit_targets is not None:
        if limit_targets < 0:
            raise ValueError("limit_targets must be non-negative")
        targets = targets[:limit_targets]
    return targets


def _tree_counts(root: Path) -> dict[str, int]:
    counts = {"file_count": 0, "dir_count": 0, "symlink_count": 0}
    if not root.exists():
        return counts
    for path in root.rglob("*"):
        if path.is_symlink():
            counts["symlink_count"] += 1
        elif path.is_dir():
            counts["dir_count"] += 1
        elif path.is_file():
            counts["file_count"] += 1
    return counts


def _merge_counts(items: Iterable[dict[str, int]]) -> dict[str, int]:
    out = {"file_count": 0, "dir_count": 0, "symlink_count": 0}
    for item in items:
        for key in out:
            out[key] += int(item.get(key, 0))
    return out


def _source_usd_variant(value: Any) -> str:
    variant = str(value or "start_result_raw.usd").strip()
    path = Path(variant)
    if not variant or path.is_absolute() or path.name != variant or variant in {".", ".."}:
        raise ValueError("source_usd_variant must be a relative file name")
    return variant


def _no_mdl_command(scratch_input_usd: Path) -> str:
    return f"./scripts/isaac_python.sh ./main.py no-mdl {scratch_input_usd}"


def _planned_destination(src: Path, *, source_root: Path, scratch_root: Path) -> Path:
    if not _is_relative_to(src, source_root):
        raise ValueError(f"planned src must be inside source_root: {src}")
    return _resolve_maybe_missing(scratch_root / _resolve_maybe_missing(src).relative_to(source_root))


def _action_covers(path: Path, actions: list[dict[str, Any]]) -> bool:
    return any(_is_relative_to(path, Path(str(action["dst"]))) for action in actions)


def _projected_symlink_target(link_path: Path, *, source_copy_root: Path, destination_copy_root: Path) -> Path:
    target_text = os.readlink(link_path)
    target_path = Path(target_text)
    if target_path.is_absolute():
        return _resolve_maybe_missing(target_path)
    destination_link = destination_copy_root / link_path.relative_to(source_copy_root)
    return _resolve_maybe_missing(destination_link.parent / target_path)


def _source_symlink_target(link_path: Path) -> Path:
    target_path = Path(os.readlink(link_path))
    if target_path.is_absolute():
        return _resolve_maybe_missing(target_path)
    return _resolve_maybe_missing(link_path.parent / target_path)


def _symlink_gap_record(
    link_path: Path,
    *,
    source_root: Path,
    scratch_root: Path,
    source_copy_root: Path,
    destination_copy_root: Path,
    actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    projected_target = _projected_symlink_target(
        link_path,
        source_copy_root=source_copy_root,
        destination_copy_root=destination_copy_root,
    )
    covered = _action_covers(projected_target, actions)
    if covered:
        return None
    source_target = _source_symlink_target(link_path)
    inside_scratch = _is_relative_to(projected_target, scratch_root)
    return {
        "link_path": str(link_path),
        "link_relative_path": _lexical_relative_to(link_path, source_root),
        "link_target_text": os.readlink(link_path),
        "source_target": str(source_target),
        "source_target_relative_path": _relative_to(source_target, source_root) if _is_relative_to(source_target, source_root) else None,
        "projected_target": str(projected_target),
        "projected_target_relative_path": _relative_to(projected_target, scratch_root) if inside_scratch else None,
        "target_inside_scratch_root": inside_scratch,
        "target_covered_by_planned_actions": False,
    }


def _uncovered_symlink_targets(
    actions: list[dict[str, Any]], *, source_root: Path, scratch_root: Path
) -> list[dict[str, Any]]:
    gaps: dict[tuple[str, str], dict[str, Any]] = {}
    for action in actions:
        src = Path(str(action["src"]))
        dst = Path(str(action["dst"]))
        if not src.exists() or not src.is_dir():
            continue
        for path in src.rglob("*"):
            if not path.is_symlink():
                continue
            gap = _symlink_gap_record(
                path,
                source_root=source_root,
                scratch_root=scratch_root,
                source_copy_root=src,
                destination_copy_root=dst,
                actions=actions,
            )
            if gap is None:
                continue
            key = (str(gap["projected_target"]), str(gap["link_target_text"]))
            gaps.setdefault(key, gap)
    return sorted(gaps.values(), key=lambda item: (str(item["projected_target"]), str(item["link_path"])))


def _validate_action_paths(actions: list[dict[str, Any]], *, source_root: Path, scratch_root: Path) -> None:
    for action in actions:
        src = Path(str(action["src"]))
        dst = Path(str(action["dst"]))
        if not _is_relative_to(src, source_root):
            raise ValueError(f"action src must be inside source_root: {src}")
        if not _is_relative_to(dst, scratch_root):
            raise ValueError(f"action dst must be inside scratch_root: {dst}")


def _scene_actions_for_targets(
    targets: list[dict[str, Any]],
    *,
    scenes_by_id: dict[str, dict[str, Any]],
    source_root: Path,
    scratch_root: Path,
) -> list[dict[str, Any]]:
    actions = []
    scene_ids = sorted({str(target["source_scene_id"]) for target in targets})
    for scene_id in scene_ids:
        scene = scenes_by_id.get(scene_id)
        if scene is None:
            raise ValueError(f"source_manifest is missing scene for target source_scene_id: {scene_id}")
        src = Path(str(scene["scene_dir"])).resolve()
        dst = Path(str(scene["scratch_scene_root"])).resolve()
        source_usd = Path(str(scene["source_usd"])).resolve()
        converted_usd = Path(str(scene["converted_usd"])).resolve()
        source_usd_variant = _source_usd_variant(scene.get("source_usd_variant") or source_usd.name)
        scratch_input_usd = (dst / source_usd_variant).resolve()
        if not _is_relative_to(src, source_root):
            raise ValueError(f"scene_dir must be inside source_root: {src}")
        if not _is_relative_to(source_usd, source_root):
            raise ValueError(f"source_usd must be inside source_root: {source_usd}")
        if not _is_relative_to(source_usd, src):
            raise ValueError(f"source_usd must be inside scene_dir: {source_usd}")
        if not _is_relative_to(dst, scratch_root):
            raise ValueError(f"scratch_scene_root must be inside scratch_root: {dst}")
        if not _is_relative_to(converted_usd, scratch_root):
            raise ValueError(f"converted_usd must be inside scratch_root: {converted_usd}")
        if not _is_relative_to(converted_usd, dst):
            raise ValueError(f"converted_usd must be inside scratch_scene_root: {converted_usd}")
        if not _is_relative_to(scratch_input_usd, scratch_root):
            raise ValueError(f"scratch_input_usd must be inside scratch_root: {scratch_input_usd}")
        if not _is_relative_to(scratch_input_usd, dst):
            raise ValueError(f"scratch_input_usd must be inside scratch_scene_root: {scratch_input_usd}")
        actions.append(
            {
                "kind": "scene_dir",
                "source_scene_id": scene_id,
                "source_scene_split": scene.get("source_scene_split"),
                "src": str(src),
                "dst": str(dst),
                "source_usd": str(source_usd),
                "source_usd_variant": source_usd_variant,
                "scratch_input_usd": str(scratch_input_usd),
                "converted_usd": str(converted_usd),
                "conversion_command": _no_mdl_command(scratch_input_usd),
                "copy_mode": "hardlink",
            }
        )
    return actions


def _model_actions_for_targets(
    targets: list[dict[str, Any]], *, source_root: Path, scratch_root: Path
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    actions_by_root: dict[Path, dict[str, Any]] = {}
    target_entries_by_root: dict[str, list[dict[str, Any]]] = {}
    for target in targets:
        model_path = _resolve_maybe_missing(Path(str(target["resolved_model_path"])))
        if not _is_relative_to(model_path, source_root):
            raise ValueError(f"resolved_model_path must be inside source_root: {model_path}")
        model_root = _model_root_for_path(model_path)
        if not _is_relative_to(model_root, source_root):
            raise ValueError(f"model_root must be inside source_root: {model_root}")
        dst = _planned_destination(model_root, source_root=source_root, scratch_root=scratch_root)
        counts = _tree_counts(model_root)
        split_root = _split_root_for_model(source_root, str(target.get("source_scene_split") or ""))
        materials_entry, warnings, required_roots = _materials_risk(
            model_root=model_root,
            split_root=split_root,
            source_root=source_root,
            scratch_root=scratch_root,
        )
        action = actions_by_root.setdefault(
            model_root,
            {
                "kind": "target_model_root",
                "src": str(model_root),
                "dst": str(dst),
                "copy_mode": "hardlink",
                "split_root": str(split_root),
                "source_relative_path": _relative_to(model_root, source_root),
                "scratch_relative_path": _relative_to(dst, scratch_root),
                "source_exists": model_root.exists(),
                "tree_counts": counts,
                "materials_entry": materials_entry,
                "required_external_resource_roots": required_roots,
                "warnings": warnings,
                "targets": [],
            },
        )
        action["targets"].append(
            {
                "source_scene_id": target["source_scene_id"],
                "object_instance_id": target["object_instance_id"],
                "target_prim_path": target["target_prim_path"],
                "object_category": target.get("object_category"),
                "reference_asset_path": target.get("reference_asset_path"),
                "resolved_model_path": target.get("resolved_model_path"),
                "linked_episode_ids": target.get("linked_episode_ids", []),
                "linked_episode_count": target.get("linked_episode_count", 0),
            }
        )
        target_entries_by_root[str(model_root)] = action["targets"]
    actions = sorted(actions_by_root.values(), key=lambda item: item["src"])
    return actions, target_entries_by_root


def _count_by_key(items: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def _dedup_external_roots(model_actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roots: dict[tuple[str, str], dict[str, Any]] = {}
    for action in model_actions:
        for root in action.get("required_external_resource_roots", []):
            key = (str(root.get("resource_name")), str(root.get("src")))
            roots.setdefault(key, root)
    return sorted(roots.values(), key=lambda item: (str(item.get("resource_name")), str(item.get("src"))))


def build_reference_closure_plan(
    source_manifest: dict[str, Any],
    target_manifest: dict[str, Any],
    *,
    limit_targets: int | None = None,
) -> dict[str, Any]:
    source_root, scratch_root = _dataset_roots(source_manifest)
    _validate_roots(source_root, scratch_root)
    _validate_target_manifest_provenance(target_manifest, source_root=source_root)

    records = _resolved_records(target_manifest)
    targets = _group_unique_targets(records, limit_targets=limit_targets)
    scenes_by_id = _scene_lookup(source_manifest)
    scene_actions = _scene_actions_for_targets(
        targets,
        scenes_by_id=scenes_by_id,
        source_root=source_root,
        scratch_root=scratch_root,
    )
    model_actions, _target_entries_by_root = _model_actions_for_targets(
        targets,
        source_root=source_root,
        scratch_root=scratch_root,
    )
    actions = scene_actions + model_actions
    _validate_action_paths(actions, source_root=source_root, scratch_root=scratch_root)

    gaps = _uncovered_symlink_targets(actions, source_root=source_root, scratch_root=scratch_root)
    estimated_model_counts = _merge_counts(action.get("tree_counts", {}) for action in model_actions)
    required_external_resource_roots = _dedup_external_roots(model_actions)
    warning_counts = _count_by_key(
        str(warning) for action in model_actions for warning in action.get("warnings", [])
    )
    materials_entry_counts = _count_by_key(
        str(action.get("materials_entry", {}).get("type", "unknown")) for action in model_actions
    )
    conversion_commands = [str(action["conversion_command"]) for action in scene_actions if action.get("conversion_command")]
    material_closure_status = (
        "requires_material_dependency_resolution"
        if gaps or required_external_resource_roots or warning_counts
        else "selected_model_roots_have_no_uncovered_symlink_targets"
    )
    return {
        "schema_version": 1,
        "status": "planned_reference_closure",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_reference_closure.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generator_git_commit": _git_commit(),
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "summary": {
            "episode_record_count": len(target_manifest.get("episode_records", []) or []),
            "resolved_episode_record_count": len(records),
            "unique_target_count": len(targets),
            "duplicate_episode_target_count": len(records) - sum(int(target["linked_episode_count"] > 0) for target in targets),
            "unique_scene_count": len(scene_actions),
            "unique_model_root_count": len(model_actions),
            "action_count": len(actions),
            "target_model_file_count": estimated_model_counts["file_count"],
            "target_model_dir_count": estimated_model_counts["dir_count"],
            "target_model_symlink_count": estimated_model_counts["symlink_count"],
            "uncovered_symlink_target_count": len(gaps),
            "materials_entry_counts": materials_entry_counts,
            "model_roots_requiring_external_materials": sum(
                1 for action in model_actions if action.get("required_external_resource_roots")
            ),
            "required_external_resource_root_count": len(required_external_resource_roots),
            "warning_counts": warning_counts,
            "model_root_only_materialization_safe": not bool(gaps or required_external_resource_roots or warning_counts),
            "material_closure_status": material_closure_status,
            "copy_mode": "hardlink",
            "planner_only": True,
        },
        "targets": targets,
        "actions": actions,
        "required_external_resource_roots": required_external_resource_roots,
        "uncovered_symlink_targets": gaps,
        "conversion_commands": conversion_commands,
        "notes": [
            "This is a planner-only artifact; it does not copy, hardlink, convert, render, or mutate assets.",
            "Uncovered symlink targets identify dependency roots that selected model directories still expect in scratch.",
            "Run no-MDL only on scratch_input_usd paths after a follow-up materializer has created the planned closure.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--target-manifest", type=Path, default=DEFAULT_TARGET_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit-targets", type=int, default=None)
    args = parser.parse_args()

    source_manifest = _load_json(args.source_manifest)
    target_manifest = _load_json(args.target_manifest)
    plan = build_reference_closure_plan(
        source_manifest,
        target_manifest,
        limit_targets=args.limit_targets,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} with {plan['summary']['unique_target_count']} unique targets, "
        f"{plan['summary']['unique_model_root_count']} model roots, "
        f"{plan['summary']['uncovered_symlink_target_count']} uncovered symlink targets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
