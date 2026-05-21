#!/usr/bin/env python3
"""Materialize the full GRScenes no-MDL scratch plan.

This script is intentionally pure Python. It consumes the read-only
`full_nomdl_scratch_plan.json`, mirrors only scratch-side trees, repairs
scratch scene pointer entries into relative symlinks, and never writes into the
source dataset.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper" / "shared" / "evidence" / "raw" / "grscene_vlm_grounding"
DEFAULT_PLAN = RAW_DIR / "full_nomdl_scratch_plan.json"
DEFAULT_OUTPUT = RAW_DIR / "full_nomdl_scratch_materialization_report.json"
COPY_MODES = ("hardlink", "copy")
TREE_ACTION_KINDS = {"resource_tree", "scene_dir"}
REPAIR_ACTION_KIND = "scene_entry_repair"
IGNORED_ACTION_KINDS = {"convert_no_mdl"}
REPAIR_ENTRY_NAMES = {"Materials", "models"}
NOMDL_OUTPUT_EXTENSIONS = (".usd", ".usda", ".usdc", ".usdz")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_maybe_missing(path: Path) -> Path:
    return path.resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        _resolve_maybe_missing(path).relative_to(_resolve_maybe_missing(parent))
    except ValueError:
        return False
    return True


def _assert_root_safety(plan: dict[str, Any]) -> tuple[Path, Path]:
    if plan.get("status") != "planned_full_grscenes_nomdl_scratch":
        raise ValueError("plan status must be planned_full_grscenes_nomdl_scratch")
    source_root = Path(str(plan.get("source_root") or "")).resolve()
    scratch_root = _resolve_maybe_missing(Path(str(plan.get("scratch_root") or "")))
    if not str(source_root) or not str(scratch_root):
        raise ValueError("plan must define source_root and scratch_root")
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")
    return source_root, scratch_root


def validate_output_path(output_path: Path, *, plan: dict[str, Any]) -> Path:
    source_root, scratch_root = _assert_root_safety(plan)
    output_path = _resolve_maybe_missing(output_path)
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


def _require_copy_mode(copy_mode: str) -> None:
    if copy_mode not in COPY_MODES:
        raise ValueError(f"copy_mode must be one of {', '.join(COPY_MODES)}")


def _copy_mode_for_action(action: dict[str, Any], override: str | None) -> str:
    copy_mode = str(override or action.get("copy_mode") or "hardlink")
    _require_copy_mode(copy_mode)
    return copy_mode


def _is_repairable_relative_path(relative_path: Path, repairable_entry_names: set[str]) -> bool:
    return bool(relative_path.parts) and relative_path.parts[0] in repairable_entry_names


def _tree_manifest(root: Path, *, repairable_entry_names: set[str] | None = None) -> dict[str, dict[str, Any]]:
    repairable_entry_names = repairable_entry_names or set()
    entries: dict[str, dict[str, Any]] = {}
    for path in root.rglob("*"):
        relative_path = path.relative_to(root)
        if _is_repairable_relative_path(relative_path, repairable_entry_names):
            continue
        relative_text = relative_path.as_posix()
        if path.is_symlink():
            entries[relative_text] = {"type": "symlink", "target": os.readlink(path)}
        elif path.is_dir():
            entries[relative_text] = {"type": "dir"}
        elif path.is_file():
            entries[relative_text] = {"type": "file", "size": path.stat().st_size}
        else:
            entries[relative_text] = {"type": "other"}
    return entries


def _compare_tree_files(src: Path, dst: Path, manifest: dict[str, dict[str, Any]]) -> None:
    for relative_text, entry in manifest.items():
        if entry["type"] != "file":
            continue
        source_file = src / relative_text
        destination_file = dst / relative_text
        if not filecmp.cmp(source_file, destination_file, shallow=False):
            raise ValueError(f"existing destination file differs from source: {destination_file}")


def _ensure_tree_destination_safe(dst: Path) -> None:
    if dst.is_symlink():
        raise ValueError(f"destination must not be a symlink: {dst}")
    if dst.exists() and not dst.is_dir():
        raise ValueError(f"destination must be a directory when it already exists: {dst}")


def _copy_file_hardlink(src: str, dst: str) -> None:
    os.link(src, dst)


def _copy_tree(src: Path, dst: Path, *, copy_mode: str) -> None:
    copy_function = _copy_file_hardlink if copy_mode == "hardlink" else shutil.copy2
    shutil.copytree(src, dst, symlinks=True, copy_function=copy_function)


def _iter_symlinks(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_symlink()]


def _projected_symlink_target(link_path: Path, *, source_copy_root: Path, destination_copy_root: Path) -> Path:
    link_target = Path(os.readlink(link_path))
    if link_target.is_absolute():
        return _resolve_maybe_missing(link_target)
    destination_link = destination_copy_root / link_path.relative_to(source_copy_root)
    return _resolve_maybe_missing(destination_link.parent / link_target)


def _validate_projected_symlink_targets(
    *,
    source_copy_root: Path,
    destination_copy_root: Path,
    scratch_root: Path,
) -> None:
    for link_path in _iter_symlinks(source_copy_root):
        projected_target = _projected_symlink_target(
            link_path,
            source_copy_root=source_copy_root,
            destination_copy_root=destination_copy_root,
        )
        if not _is_relative_to(projected_target, scratch_root):
            raise ValueError(f"symlink target would escape scratch_root: {link_path} -> {projected_target}")


def _tree_action_paths(action: dict[str, Any], *, source_root: Path, scratch_root: Path) -> tuple[Path, Path]:
    src = Path(str(action.get("src") or ""))
    dst = Path(str(action.get("dst") or ""))
    src_resolved = src.resolve()
    dst_resolved = _resolve_maybe_missing(dst.parent) / dst.name
    if not _is_relative_to(src_resolved, source_root):
        raise ValueError(f"tree action src must be inside source_root: {src}")
    if not _is_relative_to(dst_resolved, scratch_root):
        raise ValueError(f"tree action dst must be inside scratch_root: {dst}")
    _ensure_tree_destination_safe(dst_resolved)
    return src_resolved, dst_resolved


def _repair_action_paths(action: dict[str, Any], *, scratch_root: Path) -> tuple[Path, str, Path]:
    if action.get("mode") != "create_relative_symlink":
        raise ValueError("repair mode must be create_relative_symlink")
    if action.get("source_entry_type") != "file":
        raise ValueError("repair source_entry_type must be file")
    if action.get("entry_name") not in REPAIR_ENTRY_NAMES:
        raise ValueError(f"repair entry_name must be one of {', '.join(sorted(REPAIR_ENTRY_NAMES))}")
    dst_text = Path(str(action.get("dst") or ""))
    dst = _resolve_maybe_missing(dst_text.parent) / dst_text.name
    if not _is_relative_to(dst, scratch_root):
        raise ValueError(f"repair dst must be inside scratch_root: {dst}")
    target_text = str(action.get("target_text") or "").strip()
    if not target_text:
        raise ValueError("repair action must define target_text")
    if Path(target_text).is_absolute():
        raise ValueError(f"repair target_text must be relative: {target_text}")
    target_resolved = _resolve_maybe_missing(dst.parent / target_text)
    if not _is_relative_to(target_resolved, scratch_root):
        raise ValueError(f"repair target would escape scratch_root: {dst} -> {target_resolved}")
    return dst, target_text, target_resolved


def _validate_existing_tree(
    src: Path,
    dst: Path,
    *,
    repairable_entry_names: set[str],
    scratch_root: Path,
) -> dict[str, int]:
    source_manifest = _tree_manifest(src, repairable_entry_names=repairable_entry_names)
    destination_manifest = _tree_manifest(dst, repairable_entry_names=repairable_entry_names)
    if source_manifest != destination_manifest:
        raise ValueError(f"existing destination is incomplete or differs from source tree: {dst}")
    _compare_tree_files(src, dst, source_manifest)
    _validate_projected_symlink_targets(source_copy_root=dst, destination_copy_root=dst, scratch_root=scratch_root)
    return {"validated_entry_count": len(destination_manifest)}


def _materialize_tree_action(
    action: dict[str, Any],
    *,
    source_root: Path,
    scratch_root: Path,
    dry_run: bool,
    copy_mode_override: str | None,
) -> dict[str, Any]:
    src, dst = _tree_action_paths(action, source_root=source_root, scratch_root=scratch_root)
    copy_mode = _copy_mode_for_action(action, copy_mode_override)
    result = {
        "kind": action.get("kind"),
        "src": str(src),
        "dst": str(dst),
        "copy_mode": copy_mode,
        "status": "planned" if dry_run else "created",
    }
    if not src.exists():
        raise FileNotFoundError(src)
    if dry_run:
        return result
    repairable_entry_names = set(action.get("repairable_entry_names") or [])
    _validate_projected_symlink_targets(source_copy_root=src, destination_copy_root=dst, scratch_root=scratch_root)
    if dst.exists():
        return {
            **result,
            "status": "exists",
            **_validate_existing_tree(src, dst, repairable_entry_names=repairable_entry_names, scratch_root=scratch_root),
        }
    dst.parent.mkdir(parents=True, exist_ok=True)
    _copy_tree(src, dst, copy_mode=copy_mode)
    return result


def _source_entry_matches_destination(source_entry: Path, dst: Path) -> bool:
    if not source_entry.exists() or not dst.exists() or dst.is_symlink():
        return False
    if source_entry.is_file() and dst.is_file():
        return filecmp.cmp(source_entry, dst, shallow=False)
    if source_entry.is_dir() and dst.is_dir():
        return _tree_manifest(source_entry) == _tree_manifest(dst)
    return False


def _materialize_repair_action(
    action: dict[str, Any],
    *,
    source_root: Path,
    scratch_root: Path,
    dry_run: bool,
) -> dict[str, Any]:
    dst, target_text, target_resolved = _repair_action_paths(action, scratch_root=scratch_root)
    source_entry = Path(str(action.get("source_entry") or "")).resolve()
    if not _is_relative_to(source_entry, source_root):
        raise ValueError(f"repair source_entry must be inside source_root: {source_entry}")
    result = {
        "kind": action.get("kind"),
        "entry_name": action.get("entry_name"),
        "dst": str(dst),
        "target_text": target_text,
        "target_resolved": str(target_resolved),
        "status": "planned" if dry_run else "repaired",
    }
    if dry_run:
        return result
    if dst.is_symlink():
        if os.readlink(dst) == target_text:
            return {**result, "status": "exists"}
        raise ValueError(f"existing repair symlink has different target: {dst}")
    if dst.exists():
        if not _source_entry_matches_destination(source_entry, dst):
            raise ValueError(f"existing repair destination differs from source entry: {dst}")
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(target_text, dst, target_is_directory=True)
    return result


def _selected_actions(plan: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    tree_actions: list[dict[str, Any]] = []
    repair_actions: list[dict[str, Any]] = []
    ignored_actions: list[dict[str, Any]] = []
    for action in plan.get("actions") or []:
        kind = str(action.get("kind") or "")
        if kind in TREE_ACTION_KINDS:
            tree_actions.append(action)
        elif kind == REPAIR_ACTION_KIND:
            repair_actions.append(action)
        elif kind in IGNORED_ACTION_KINDS:
            ignored_actions.append(action)
        else:
            raise ValueError(f"unsupported action kind: {kind}")
    return tree_actions, repair_actions, ignored_actions


def _top_level_input_counts(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    existing: list[str] = []
    missing: list[str] = []
    for job in plan.get("conversion_jobs") or []:
        scratch_input = _resolve_maybe_missing(Path(str(job.get("scratch_input_usd") or "")))
        if scratch_input.exists():
            existing.append(str(scratch_input))
        else:
            missing.append(str(scratch_input))
    return sorted(existing), sorted(missing)


def _timestamped_siblings(expected_output: Path) -> list[str]:
    parent = expected_output.parent
    if not parent.exists():
        return []
    suffix = expected_output.suffix or ".usd"
    pattern = f"{expected_output.stem}_*{suffix}"
    return sorted(str(path) for path in parent.glob(pattern) if path.name != expected_output.name)


def _looks_like_nomdl_output(path: Path) -> bool:
    return path.suffix in NOMDL_OUTPUT_EXTENSIONS and "_noMDL" in path.stem


def _source_tree_nomdl_outputs(tree_actions: list[dict[str, Any]], *, source_root: Path, scratch_root: Path) -> list[str]:
    outputs: set[str] = set()
    for action in tree_actions:
        src, _dst = _tree_action_paths(action, source_root=source_root, scratch_root=scratch_root)
        if not src.exists():
            continue
        for path in src.rglob("*"):
            if path.is_file() and _looks_like_nomdl_output(path):
                outputs.add(str(path))
    return sorted(outputs)


def _existing_nomdl_outputs(
    plan: dict[str, Any],
    *,
    tree_actions: list[dict[str, Any]] | None = None,
    source_root: Path | None = None,
    scratch_root: Path | None = None,
    include_source_trees: bool = False,
) -> list[str]:
    existing: list[str] = []
    for job in plan.get("conversion_jobs") or []:
        expected_output = _resolve_maybe_missing(Path(str(job.get("expected_top_output_usd") or "")))
        if expected_output.exists():
            existing.append(str(expected_output))
        existing.extend(_timestamped_siblings(expected_output))
    if include_source_trees:
        if tree_actions is None or source_root is None or scratch_root is None:
            raise ValueError("source tree no-MDL scan requires tree actions and roots")
        existing.extend(_source_tree_nomdl_outputs(tree_actions, source_root=source_root, scratch_root=scratch_root))
    return sorted(set(existing))


def _status_count(results: list[dict[str, Any]], status: str) -> int:
    return sum(1 for result in results if result.get("status") == status)


def materialize_full_scratch_plan(
    plan: dict[str, Any],
    *,
    dry_run: bool = True,
    copy_mode: str | None = None,
) -> dict[str, Any]:
    """Materialize scratch trees and repairs from a full no-MDL scratch plan."""

    if copy_mode is not None:
        _require_copy_mode(copy_mode)
    source_root, scratch_root = _assert_root_safety(plan)
    tree_actions, repair_actions, ignored_actions = _selected_actions(plan)
    existing_nomdl_outputs = _existing_nomdl_outputs(
        plan,
        tree_actions=tree_actions,
        source_root=source_root,
        scratch_root=scratch_root,
        include_source_trees=not dry_run,
    )
    if existing_nomdl_outputs and not dry_run:
        raise ValueError(
            f"scratch contains existing no-MDL outputs; remove or choose a clean scratch root: "
            f"{existing_nomdl_outputs[:5]}"
        )
    tree_results = [
        _materialize_tree_action(
            action,
            source_root=source_root,
            scratch_root=scratch_root,
            dry_run=dry_run,
            copy_mode_override=copy_mode,
        )
        for action in tree_actions
    ]
    repair_results = [
        _materialize_repair_action(
            action,
            source_root=source_root,
            scratch_root=scratch_root,
            dry_run=dry_run,
        )
        for action in repair_actions
    ]
    top_level_existing, top_level_missing = _top_level_input_counts(plan)
    summary = {
        "tree_action_count": len(tree_actions),
        "repair_action_count": len(repair_actions),
        "ignored_convert_action_count": len(ignored_actions),
        "dry_run": dry_run,
        "planned_tree_action_count": _status_count(tree_results, "planned"),
        "created_tree_count": _status_count(tree_results, "created"),
        "existing_tree_count": _status_count(tree_results, "exists"),
        "planned_repair_action_count": _status_count(repair_results, "planned"),
        "repaired_scene_entry_count": _status_count(repair_results, "repaired"),
        "existing_scene_entry_count": _status_count(repair_results, "exists"),
        "existing_nomdl_output_count": len(existing_nomdl_outputs),
        "top_level_scratch_input_exists_count": len(top_level_existing),
        "top_level_scratch_input_missing_count": len(top_level_missing),
    }
    return {
        "schema_version": 1,
        "status": "full_grscenes_nomdl_scratch_materialization",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py",
        "generated_at_utc": _utc_now(),
        "dry_run": dry_run,
        "source_plan_status": plan.get("status"),
        "source_plan_generated_at_utc": plan.get("generated_at_utc"),
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "summary": summary,
        "tree_results": tree_results,
        "repair_results": repair_results,
        "ignored_actions": [
            {"kind": action.get("kind"), "conversion_job_id": action.get("conversion_job_id")}
            for action in ignored_actions
        ],
        "top_level_scratch_inputs": {
            "existing": top_level_existing,
            "missing": top_level_missing,
        },
        "existing_nomdl_outputs": existing_nomdl_outputs,
        "notes": [
            "This report does not run no-MDL conversion.",
            "Hardlink mode controls physical bytes but still creates scratch directory entries.",
            "After real materialization, rerun the full dependency closure report to prove recursive scratch inputs exist.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--copy-mode", choices=COPY_MODES, default=None)
    parser.add_argument("--apply", action="store_true", help="Create scratch hardlinks/copies and repairs")
    args = parser.parse_args()

    plan = _load_json(args.plan)
    output_path = validate_output_path(args.out, plan=plan)
    report = materialize_full_scratch_plan(plan, dry_run=not args.apply, copy_mode=args.copy_mode)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {output_path} with {report['summary']['tree_action_count']} tree actions, "
        f"{report['summary']['repair_action_count']} repair actions, dry_run={report['dry_run']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
