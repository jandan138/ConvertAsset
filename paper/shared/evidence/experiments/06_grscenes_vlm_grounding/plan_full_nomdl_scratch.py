#!/usr/bin/env python3
"""Plan full GRScenes no-MDL scratch preparation.

This script is intentionally read-only and pure Python. It does not import pxr,
open USD stages, copy files, hardlink resources, run no-MDL, or create scratch
asset directories. Its job is to make the full-dataset route explicit before
any conversion command can touch generated asset trees.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper" / "shared" / "evidence" / "raw" / "grscene_vlm_grounding"
DEFAULT_SOURCE_ROOT = Path("/cpfs/user/zhuzihou/assets/zzh-grscenes")
DEFAULT_SCRATCH_ROOT = Path("/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521")
DEFAULT_OUTPUT = RAW_DIR / "full_nomdl_scratch_plan.json"
SCENE_SPLITS = ("home_scenes", "commercial_scenes")
SCENE_USD_CANDIDATES = (
    "start_result_raw.usd",
    "start_result_navigation.usd",
    "start_result_interaction.usd",
)
DEFAULT_SOURCE_USD_VARIANTS = ("start_result_raw.usd",)
RESOURCE_NAMES = ("models", "Materials")
COPY_MODES = ("hardlink", "copy")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_maybe_missing(path: Path) -> Path:
    return path.resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        _resolve_maybe_missing(path).relative_to(_resolve_maybe_missing(parent))
    except ValueError:
        return False
    return True


def _assert_root_safety(source_root: Path, scratch_root: Path) -> tuple[Path, Path]:
    source_root = source_root.resolve()
    scratch_root = _resolve_maybe_missing(scratch_root)
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")
    return source_root, scratch_root


def validate_output_path(output_path: Path, *, source_root: Path, scratch_root: Path) -> Path:
    """Return a resolved report path that cannot write into source or scratch."""

    output_path = _resolve_maybe_missing(output_path)
    source_root = source_root.resolve()
    scratch_root = _resolve_maybe_missing(scratch_root)
    if _is_relative_to(output_path, source_root):
        raise ValueError("output path must not be inside source_root")
    if _is_relative_to(output_path, scratch_root):
        raise ValueError("output path must not be inside scratch_root")
    return output_path


def _path_type(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "dir"
    if path.is_file():
        return "file"
    if path.exists():
        return "other"
    return "missing"


def _source_to_scratch(path: Path, *, source_root: Path, scratch_root: Path) -> Path:
    resolved = path.resolve() if path.exists() and not path.is_symlink() else _resolve_maybe_missing(path)
    if not _is_relative_to(resolved, source_root):
        raise ValueError(f"path must be inside source_root: {path}")
    return scratch_root / resolved.relative_to(source_root)


def _scene_split_root(source_root: Path, split: str) -> Path:
    return source_root / "scenes" / "GRScenes-100" / split


def _scene_dirs(source_root: Path, split: str) -> list[Path]:
    scenes_dir = _scene_split_root(source_root, split) / "scenes"
    if not scenes_dir.exists():
        raise FileNotFoundError(scenes_dir)
    return sorted(path for path in scenes_dir.glob("*_usd") if path.is_dir())


def _normalize_variants(source_usd_variants: tuple[str, ...] | list[str] | None) -> list[str]:
    variants = list(source_usd_variants or DEFAULT_SOURCE_USD_VARIANTS)
    variants = list(dict.fromkeys(str(item) for item in variants))
    if not variants:
        raise ValueError("at least one source USD variant is required")
    invalid = [item for item in variants if item not in SCENE_USD_CANDIDATES]
    if invalid:
        raise ValueError(f"source_usd_variants must be chosen from {', '.join(SCENE_USD_CANDIDATES)}")
    return variants


def _sidecar_path(path: Path) -> Path:
    suffix = path.suffix or ".usd"
    return path.with_name(f"{path.stem}_noMDL{suffix}")


def _read_scene_entry_target(entry: Path) -> str:
    if entry.is_symlink():
        target_text = os.readlink(entry).strip()
    elif entry.is_file():
        target_text = entry.read_text(encoding="utf-8").strip()
    else:
        raise ValueError(f"scene entry must be a pointer file or symlink: {entry}")
    if not target_text or "\n" in target_text:
        raise ValueError(f"scene entry pointer must contain one relative target: {entry}")
    if Path(target_text).is_absolute():
        raise ValueError(f"scene entry pointer must be relative: {entry}")
    return target_text


def _scene_entry_info(
    *,
    entry: Path,
    entry_name: str,
    split_root: Path,
    scratch_entry: Path,
    scratch_split_root: Path,
) -> dict[str, Any]:
    entry_type = _path_type(entry)
    info: dict[str, Any] = {
        "entry_name": entry_name,
        "source_entry": str(entry),
        "source_entry_type": entry_type,
        "scratch_entry": str(scratch_entry),
    }
    if entry_type in {"file", "symlink"}:
        target_text = _read_scene_entry_target(entry)
        source_target = _resolve_maybe_missing(entry.parent / target_text)
        expected_source_target = _resolve_maybe_missing(split_root / entry_name)
        scratch_target = _resolve_maybe_missing(scratch_entry.parent / target_text)
        expected_scratch_target = _resolve_maybe_missing(scratch_split_root / entry_name)
        info.update(
            {
                "target_text": target_text,
                "source_target": str(source_target),
                "expected_source_target": str(expected_source_target),
                "scratch_target": str(scratch_target),
                "expected_scratch_target": str(expected_scratch_target),
                "target_matches_split_resource": source_target == expected_source_target,
                "scratch_target_matches_split_resource": scratch_target == expected_scratch_target,
            }
        )
    return info


def _scene_entry_repair_action(
    *,
    scene_id: str,
    split: str,
    entry_info: dict[str, Any],
    scratch_root: Path,
) -> dict[str, Any]:
    dst = Path(str(entry_info["scratch_entry"]))
    target_text = str(entry_info["target_text"])
    target_resolved = _resolve_maybe_missing(dst.parent / target_text)
    if not _is_relative_to(target_resolved, scratch_root):
        raise ValueError(f"scene entry repair would escape scratch_root: {dst} -> {target_resolved}")
    return {
        "kind": "scene_entry_repair",
        "mode": "create_relative_symlink",
        "source_scene_id": scene_id,
        "source_scene_split": split,
        "entry_name": entry_info["entry_name"],
        "dst": str(dst),
        "target_text": target_text,
        "target_resolved": str(target_resolved),
        "source_entry": entry_info["source_entry"],
        "source_entry_type": entry_info["source_entry_type"],
        "reason": "scene_pointer_file_must_resolve_to_split_resource_in_scratch",
    }


def _resource_action(
    *,
    source_root: Path,
    scratch_root: Path,
    split: str,
    resource_name: str,
    copy_mode: str,
) -> dict[str, Any]:
    split_root = _scene_split_root(source_root, split)
    src = split_root / resource_name
    dst = _source_to_scratch(src, source_root=source_root, scratch_root=scratch_root)
    return {
        "kind": "resource_tree",
        "split": split,
        "resource_name": resource_name,
        "src": str(src),
        "dst": str(dst),
        "src_type": _path_type(src),
        "copy_mode": copy_mode,
        "exists_policy": "fail_if_different",
        "scan_policy": "root_only_no_deep_walk",
    }


def _conversion_job(
    *,
    scene_id: str,
    split: str,
    variant: str,
    source_usd: Path,
    scratch_input_usd: Path,
) -> dict[str, Any]:
    expected_output = _sidecar_path(scratch_input_usd)
    job_id = f"{split}:{scene_id}:{variant}"
    argv = ["./scripts/isaac_python.sh", "./main.py", "no-mdl", "--only-new-usd", str(scratch_input_usd)]
    command = " ".join(argv)
    return {
        "kind": "convert_no_mdl",
        "conversion_job_id": job_id,
        "source_scene_id": scene_id,
        "source_scene_split": split,
        "source_usd_variant": variant,
        "source_usd": str(source_usd),
        "scratch_input_usd": str(scratch_input_usd),
        "expected_top_output_usd": str(expected_output),
        "command": command,
        "argv": argv,
        "command_is_preview_only": True,
        "safe_to_execute_now": False,
        "blocked_by": [
            "single_process_multi_root_runner_missing",
            "whole_scene_dependency_closure_not_scanned",
            "recursive_nomdl_output_collision_scan_missing",
        ],
    }


def build_full_nomdl_scratch_plan(
    *,
    source_root: Path,
    scratch_root: Path,
    source_usd_variants: tuple[str, ...] | list[str] | None = None,
    copy_mode: str = "hardlink",
) -> dict[str, Any]:
    """Build a read-only full GRScenes no-MDL scratch plan."""

    if copy_mode not in COPY_MODES:
        raise ValueError(f"copy_mode must be one of {', '.join(COPY_MODES)}")
    source_root, scratch_root = _assert_root_safety(source_root, scratch_root)
    variants = _normalize_variants(source_usd_variants)

    scenes: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    conversion_jobs: list[dict[str, Any]] = []
    existing_source_sidecars: list[str] = []
    split_inventory: dict[str, Any] = {}
    scene_entry_repair_count = 0
    scene_entry_symlink_projectable_count = 0
    scene_entry_unexpected_target_count = 0
    missing_planned_source_usds: list[str] = []

    for split in SCENE_SPLITS:
        split_root = _scene_split_root(source_root, split)
        scratch_split_root = _source_to_scratch(split_root, source_root=source_root, scratch_root=scratch_root)
        scene_dirs = _scene_dirs(source_root, split)
        source_usd_counts = {candidate: 0 for candidate in SCENE_USD_CANDIDATES}
        entry_counts = {
            entry_name: {"file": 0, "symlink": 0, "dir": 0, "missing": 0, "other": 0}
            for entry_name in RESOURCE_NAMES
        }

        for resource_name in RESOURCE_NAMES:
            actions.append(
                _resource_action(
                    source_root=source_root,
                    scratch_root=scratch_root,
                    split=split,
                    resource_name=resource_name,
                    copy_mode=copy_mode,
                )
            )

        for scene_dir in scene_dirs:
            scene_id = scene_dir.name
            scratch_scene_dir = _source_to_scratch(scene_dir, source_root=source_root, scratch_root=scratch_root)
            scene_action = {
                "kind": "scene_dir",
                "source_scene_id": scene_id,
                "source_scene_split": split,
                "src": str(scene_dir),
                "dst": str(scratch_scene_dir),
                "copy_mode": copy_mode,
                "exists_policy": "fail_if_different",
                "repairable_entry_names": list(RESOURCE_NAMES),
            }
            actions.append(scene_action)

            scene_entries: dict[str, Any] = {}
            for entry_name in RESOURCE_NAMES:
                entry = scene_dir / entry_name
                scratch_entry = scratch_scene_dir / entry_name
                info = _scene_entry_info(
                    entry=entry,
                    entry_name=entry_name,
                    split_root=split_root,
                    scratch_entry=scratch_entry,
                    scratch_split_root=scratch_split_root,
                )
                scene_entries[entry_name] = info
                entry_type = str(info["source_entry_type"])
                entry_counts[entry_name][entry_type] = entry_counts[entry_name].get(entry_type, 0) + 1
                if info.get("target_matches_split_resource") is False or info.get("scratch_target_matches_split_resource") is False:
                    scene_entry_unexpected_target_count += 1
                if entry_type == "file":
                    actions.append(
                        _scene_entry_repair_action(
                            scene_id=scene_id,
                            split=split,
                            entry_info=info,
                            scratch_root=scratch_root,
                        )
                    )
                    scene_entry_repair_count += 1
                elif entry_type == "symlink" and info.get("scratch_target_matches_split_resource") is True:
                    scene_entry_symlink_projectable_count += 1

            available_variants: list[str] = []
            planned_source_usds: list[dict[str, Any]] = []
            for candidate in SCENE_USD_CANDIDATES:
                candidate_path = scene_dir / candidate
                if candidate_path.exists():
                    source_usd_counts[candidate] += 1
                    available_variants.append(candidate)

            for variant in variants:
                source_usd = scene_dir / variant
                if not source_usd.exists():
                    missing_planned_source_usds.append(str(source_usd))
                    continue
                scratch_input_usd = scratch_scene_dir / variant
                source_sidecar = _sidecar_path(source_usd)
                if source_sidecar.exists():
                    existing_source_sidecars.append(str(source_sidecar))
                job = _conversion_job(
                    scene_id=scene_id,
                    split=split,
                    variant=variant,
                    source_usd=source_usd,
                    scratch_input_usd=scratch_input_usd,
                )
                conversion_jobs.append(job)
                actions.append(job)
                planned_source_usds.append(
                    {
                        "variant": variant,
                        "source_usd": str(source_usd),
                        "scratch_input_usd": str(scratch_input_usd),
                        "expected_top_output_usd": job["expected_top_output_usd"],
                        "source_hash_sha256": _sha256_file(source_usd),
                        "source_size_bytes": source_usd.stat().st_size,
                        "source_mtime_ns": source_usd.stat().st_mtime_ns,
                        "existing_source_nomdl_sidecar": str(source_sidecar) if source_sidecar.exists() else None,
                        "conversion_job_id": job["conversion_job_id"],
                    }
                )

            scenes.append(
                {
                    "source_scene_id": scene_id,
                    "source_scene_split": split,
                    "source_scene_dir": str(scene_dir),
                    "scratch_scene_dir": str(scratch_scene_dir),
                    "available_source_usd_variants": available_variants,
                    "planned_source_usd_variants": [item["variant"] for item in planned_source_usds],
                    "scene_entries": scene_entries,
                    "source_usds": planned_source_usds,
                }
            )

        split_inventory[split] = {
            "split_root": str(split_root),
            "scratch_split_root": str(scratch_split_root),
            "scene_count": len(scene_dirs),
            "source_usd_counts": source_usd_counts,
            "scene_entry_counts": entry_counts,
            "resource_roots": {
                resource_name: {
                    "path": str(split_root / resource_name),
                    "scratch_path": str(scratch_split_root / resource_name),
                    "type": _path_type(split_root / resource_name),
                    "scan_policy": "root_only_no_deep_walk",
                }
                for resource_name in RESOURCE_NAMES
            },
        }

    warnings = [
        "per_scene_cli_commands_are_preview_only_because_no_mdl_recursively_writes_dependency_sidecars",
        "resource_tree_actions_are_not_applied_by_this_planner",
    ]
    if existing_source_sidecars:
        warnings.append("source_tree_has_existing_nomdl_sidecars")
    if scene_entry_unexpected_target_count:
        warnings.append("scene_entry_targets_do_not_match_expected_split_resources")

    apply_blockers = [
        "single_process_multi_root_runner_missing",
        "whole_scene_dependency_closure_not_scanned",
        "recursive_nomdl_output_collision_scan_missing",
        "scratch_cleanliness_not_verified",
    ]
    if missing_planned_source_usds:
        apply_blockers.append("planned_source_usds_missing")
    if scene_entry_unexpected_target_count:
        apply_blockers.append("scene_entry_target_mismatch")

    scene_dir_action_count = sum(1 for action in actions if action["kind"] == "scene_dir")
    resource_tree_action_count = sum(1 for action in actions if action["kind"] == "resource_tree")
    convert_action_count = sum(1 for action in actions if action["kind"] == "convert_no_mdl")
    summary = {
        "scene_count": len(scenes),
        "home_scene_count": split_inventory.get("home_scenes", {}).get("scene_count", 0),
        "commercial_scene_count": split_inventory.get("commercial_scenes", {}).get("scene_count", 0),
        "input_usd_count": len(conversion_jobs),
        "conversion_job_count": len(conversion_jobs),
        "scene_dir_action_count": scene_dir_action_count,
        "resource_tree_action_count": resource_tree_action_count,
        "scene_entry_repair_count": scene_entry_repair_count,
        "scene_entry_symlink_projectable_count": scene_entry_symlink_projectable_count,
        "scene_entry_unexpected_target_count": scene_entry_unexpected_target_count,
        "convert_no_mdl_action_count": convert_action_count,
        "action_count": len(actions),
        "existing_source_nomdl_sidecar_count": len(existing_source_sidecars),
        "missing_planned_source_usd_count": len(missing_planned_source_usds),
        "planner_only": True,
        "safe_to_apply": False,
    }

    return {
        "schema_version": 1,
        "status": "planned_full_grscenes_nomdl_scratch",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_nomdl_scratch.py",
        "generator_git_commit": _git_commit(),
        "generated_at_utc": _utc_now(),
        "planner_only": True,
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "config": {
            "scene_scope": "GRScenes-100_all_available_scenes",
            "source_usd_variants": variants,
            "copy_mode": copy_mode,
            "nomdl_args": ["--only-new-usd"],
            "listed_command_strategy": "per_scene_cli_preview_only",
            "recommended_conversion_strategy": "single_process_multi_root_runner",
            "require_clean_scratch": True,
            "resource_inventory_policy": "bounded_scene_scan_no_deep_models_walk",
        },
        "safety": {
            "source_root_immutable": True,
            "scratch_outside_source_root": not _is_relative_to(scratch_root, source_root),
            "source_outside_scratch_root": not _is_relative_to(source_root, scratch_root),
            "safe_to_apply": False,
            "apply_blockers": apply_blockers,
            "warnings": warnings,
        },
        "summary": summary,
        "inventory": {
            "grscenes_root": str(source_root / "scenes" / "GRScenes-100"),
            "splits": split_inventory,
            "scene_usd_candidates": list(SCENE_USD_CANDIDATES),
            "existing_source_nomdl_sidecars": sorted(existing_source_sidecars),
            "missing_planned_source_usds": missing_planned_source_usds,
        },
        "dependency_closure": {
            "usd_dependency_count": None,
            "missing_dependency_count": None,
            "outside_source_root_ref_count": None,
            "expected_recursive_nomdl_output_count": None,
            "output_collision_count": None,
            "status": "not_scanned_by_this_read_only_planner",
        },
        "nomdl_side_effect_plan": {
            "uses_only_new_usd": True,
            "writes_summary_or_audit": False,
            "expected_top_output_usd_count": len(conversion_jobs),
            "would_write_top_level_usd_sidecars": [job["expected_top_output_usd"] for job in conversion_jobs],
            "recursive_dependency_sidecars": "not_scanned",
            "per_scene_cli_can_duplicate_recursive_dependency_outputs": True,
            "timestamped_output_risk": True,
            "reason": "Processor.done is per process; separate CLI runs do not deduplicate shared recursive dependencies.",
        },
        "actions": actions,
        "scenes": scenes,
        "conversion_jobs": conversion_jobs,
        "post_apply_validation": {
            "no_new_files_under_source_root": "required",
            "all_expected_top_outputs_exist": "required",
            "no_unexpected_timestamped_outputs": "required",
            "scratch_symlinks_resolve_inside_scratch_root": "required",
        },
        "notes": [
            "This is not an apply plan. It is a full-dataset route planner.",
            "The checked commands are preview commands and remain blocked until a single-process multi-root runner exists.",
            "The planner scans scene directories and split-level resource roots only; it intentionally avoids a deep models/Materials walk.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--scratch-root", type=Path, default=DEFAULT_SCRATCH_ROOT)
    parser.add_argument("--source-usd", choices=SCENE_USD_CANDIDATES, action="append", default=None)
    parser.add_argument("--all-scene-usds", action="store_true", help="Plan raw, navigation, and interaction inputs")
    parser.add_argument("--copy-mode", choices=COPY_MODES, default="hardlink")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    variants = tuple(SCENE_USD_CANDIDATES) if args.all_scene_usds else tuple(args.source_usd or DEFAULT_SOURCE_USD_VARIANTS)
    plan = build_full_nomdl_scratch_plan(
        source_root=args.source_root,
        scratch_root=args.scratch_root,
        source_usd_variants=variants,
        copy_mode=args.copy_mode,
    )
    output_path = validate_output_path(
        args.out,
        source_root=Path(str(plan["source_root"])),
        scratch_root=Path(str(plan["scratch_root"])),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(
        f"Wrote {output_path} with {plan['summary']['scene_count']} scenes, "
        f"{plan['summary']['input_usd_count']} planned input USDs, "
        f"safe_to_apply={plan['safety']['safe_to_apply']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
