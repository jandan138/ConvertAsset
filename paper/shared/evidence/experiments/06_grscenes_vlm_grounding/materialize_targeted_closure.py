#!/usr/bin/env python3
"""Materialize the targeted GRScenes VLM closure into scratch.

This script is intentionally pure Python: it does not import pxr or Isaac Sim.
It consumes the reference-closure plan plus the material-dependency closure
plan, then either dry-runs or applies only the selected scene/model/material
subset needed by the current ACL/VLM pilot.
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
DEFAULT_REFERENCE_PLAN = RAW_DIR / "reference_closure_plan.json"
DEFAULT_MATERIAL_PLAN = RAW_DIR / "material_dependency_closure_plan.json"
DEFAULT_OUTPUT = RAW_DIR / "targeted_materialization_report.json"
COPY_MODES = ("hardlink", "copy")
SCENE_ENTRY_NAMES = ("Materials", "models")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def _resolve_maybe_missing(path: Path) -> Path:
    return path.resolve(strict=False)


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


def _iter_symlinks(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_symlink()]


def _projected_symlink_target(link_path: Path, *, source_copy_root: Path, destination_copy_root: Path) -> Path:
    link_target = Path(os.readlink(link_path))
    if link_target.is_absolute():
        return _resolve_maybe_missing(link_target)
    destination_link = destination_copy_root / link_path.relative_to(source_copy_root)
    return _resolve_maybe_missing(destination_link.parent / link_target)


def _validate_symlink_targets(
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


def _compare_tree_files(
    src: Path,
    dst: Path,
    manifest: dict[str, dict[str, Any]],
) -> None:
    for relative_text, entry in manifest.items():
        if entry["type"] != "file":
            continue
        source_file = src / relative_text
        destination_file = dst / relative_text
        if not filecmp.cmp(source_file, destination_file, shallow=False):
            raise ValueError(f"existing destination file differs from source: {destination_file}")


def _validate_existing_tree(
    src: Path,
    dst: Path,
    *,
    scratch_root: Path,
    repairable_entry_names: set[str] | None = None,
) -> dict[str, int]:
    repairable_entry_names = repairable_entry_names or set()
    source_manifest = _tree_manifest(src, repairable_entry_names=repairable_entry_names)
    destination_manifest = _tree_manifest(dst, repairable_entry_names=repairable_entry_names)
    if source_manifest != destination_manifest:
        raise ValueError(f"existing destination is incomplete or differs from source tree: {dst}")
    _compare_tree_files(src, dst, source_manifest)
    _validate_symlink_targets(source_copy_root=dst, destination_copy_root=dst, scratch_root=scratch_root)
    return {"validated_entry_count": len(destination_manifest)}


def _require_copy_mode(copy_mode: str) -> None:
    if copy_mode not in COPY_MODES:
        raise ValueError(f"copy_mode must be one of {', '.join(COPY_MODES)}")


def _dataset_roots(reference_plan: dict[str, Any], material_plan: dict[str, Any]) -> tuple[Path, Path]:
    source_root = Path(str(reference_plan.get("source_root") or "")).resolve()
    scratch_root = Path(str(reference_plan.get("scratch_root") or "")).resolve()
    material_source_root = Path(str(material_plan.get("source_root") or "")).resolve()
    material_scratch_root = Path(str(material_plan.get("scratch_root") or "")).resolve()
    if not str(source_root) or not str(scratch_root):
        raise ValueError("reference plan must define source_root and scratch_root")
    if source_root != material_source_root:
        raise ValueError("reference and material plans must use the same source_root")
    if scratch_root != material_scratch_root:
        raise ValueError("reference and material plans must use the same scratch_root")
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")
    return source_root, scratch_root


def _assert_source_path(path: Path, source_root: Path, *, label: str) -> Path:
    resolved = path.resolve()
    if not _is_relative_to(resolved, source_root):
        raise ValueError(f"{label} must be inside source_root: {path}")
    return resolved


def _assert_scratch_path(path: Path, scratch_root: Path, *, label: str) -> Path:
    resolved = _resolve_maybe_missing(path)
    if not _is_relative_to(resolved, scratch_root):
        raise ValueError(f"{label} must be inside scratch_root: {path}")
    return resolved


def _split_root_from_scene_dir(scene_dir: Path) -> Path:
    return scene_dir.resolve().parent.parent


def _scratch_split_root_from_scene_dst(scene_dst: Path) -> Path:
    return scene_dst.resolve(strict=False).parent.parent


def _copy_action_from_reference(
    action: dict[str, Any],
    *,
    source_root: Path,
    scratch_root: Path,
    copy_mode: str,
) -> dict[str, Any]:
    kind = str(action.get("kind") or "")
    if kind not in {"scene_dir", "target_model_root"}:
        raise ValueError(f"unsupported reference action kind: {kind}")
    src = _assert_source_path(Path(str(action["src"])), source_root, label=f"{kind} src")
    dst = _assert_scratch_path(Path(str(action["dst"])), scratch_root, label=f"{kind} dst")
    copied = {
        **action,
        "src": str(src),
        "dst": str(dst),
        "copy_mode": copy_mode,
    }
    if kind == "scene_dir":
        copied["repairable_entry_names"] = list(SCENE_ENTRY_NAMES)
    elif kind == "target_model_root" and (action.get("materials_entry") or {}).get("type") in {
        "missing",
        "pointer_file",
    }:
        copied["repairable_entry_names"] = ["Materials"]
    return copied


def _material_file_action(
    action: dict[str, Any],
    *,
    source_root: Path,
    scratch_root: Path,
    copy_mode: str,
) -> dict[str, Any]:
    src = _assert_source_path(Path(str(action["src"])), source_root, label="material action src")
    dst = _assert_scratch_path(Path(str(action["dst"])), scratch_root, label="material action dst")
    if src.is_dir():
        raise ValueError(f"material action src must be a file, not a directory: {src}")
    return {
        **action,
        "kind": "material_asset_file",
        "src": str(src),
        "dst": str(dst),
        "copy_mode": copy_mode,
    }


def _relative_symlink_action_safe(action: dict[str, Any], *, scratch_root: Path) -> dict[str, Any]:
    dst = _assert_scratch_path(Path(str(action["dst"])), scratch_root, label=f"{action['kind']} dst")
    target_text = str(action.get("target_text") or "").strip()
    if not target_text:
        raise ValueError(f"{action['kind']} must define target_text")
    if Path(target_text).is_absolute():
        raise ValueError(f"{action['kind']} target_text must be relative: {target_text}")
    target_path = _resolve_maybe_missing(dst.parent / target_text)
    if not _is_relative_to(target_path, scratch_root):
        raise ValueError(f"{action['kind']} target would escape scratch_root: {dst} -> {target_path}")
    return {**action, "dst": str(dst), "target_text": target_text, "target_resolved": str(target_path)}


def _scene_entry_target_text(source_entry: Path) -> str:
    if source_entry.is_symlink():
        target_text = os.readlink(source_entry).strip()
    elif source_entry.is_file():
        target_text = source_entry.read_text(encoding="utf-8").strip()
    else:
        raise ValueError(f"scene entry must be a pointer file or symlink: {source_entry}")
    if "\n" in target_text or not target_text:
        raise ValueError(f"scene entry pointer must contain one relative target: {source_entry}")
    if Path(target_text).is_absolute():
        raise ValueError(f"scene entry pointer must be relative: {source_entry}")
    return target_text


def _scene_entry_repair_actions(
    scene_action: dict[str, Any],
    *,
    source_root: Path,
    scratch_root: Path,
) -> list[dict[str, Any]]:
    scene_src = Path(str(scene_action["src"]))
    scene_dst = Path(str(scene_action["dst"]))
    split_root = _split_root_from_scene_dir(scene_src)
    scratch_split_root = _scratch_split_root_from_scene_dst(scene_dst)
    repairs: list[dict[str, Any]] = []
    for entry_name in SCENE_ENTRY_NAMES:
        source_entry = scene_src / entry_name
        source_entry_type = _path_type(source_entry)
        if source_entry_type == "dir":
            continue
        if source_entry_type == "missing":
            raise ValueError(f"scene entry is missing: {source_entry}")
        target_text = _scene_entry_target_text(source_entry)
        source_target = _resolve_maybe_missing(source_entry.parent / target_text)
        expected_source_target = _resolve_maybe_missing(split_root / entry_name)
        if source_target != expected_source_target:
            raise ValueError(
                f"scene entry pointer must resolve to split-level {entry_name}: "
                f"{source_entry} -> {source_target}, expected {expected_source_target}"
            )
        scratch_entry = scene_dst / entry_name
        expected_scratch_target = scratch_split_root / entry_name
        repair = {
            "kind": "scene_entry_repair",
            "mode": "create_relative_symlink",
            "entry_name": entry_name,
            "dst": str(scratch_entry),
            "target_text": target_text,
            "source_scene_id": scene_action.get("source_scene_id"),
            "source_scene_split": scene_action.get("source_scene_split"),
            "source_entry": str(_assert_source_path(source_entry, source_root, label="scene entry source")),
            "source_entry_type": source_entry_type,
            "source_target": str(source_target),
            "scratch_scene_root": str(scene_dst),
            "scratch_split_resource_root": str(_assert_scratch_path(expected_scratch_target, scratch_root, label="scene repair target")),
            "reason": "scene_pointer_file_must_resolve_to_split_resource_in_scratch",
        }
        repairs.append(_relative_symlink_action_safe(repair, scratch_root=scratch_root))
    return repairs


def _dedupe_by_destination(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []
    for action in actions:
        key = str(action["dst"])
        existing = seen.get(key)
        if existing is None:
            seen[key] = action
            ordered.append(action)
            continue
        if existing.get("src") != action.get("src") or existing.get("kind") != action.get("kind"):
            raise ValueError(f"conflicting actions for destination: {key}")
    return ordered


def build_targeted_materialization_plan(
    reference_plan: dict[str, Any],
    material_plan: dict[str, Any],
    *,
    copy_mode: str = "hardlink",
) -> dict[str, Any]:
    """Build a storage-safe scratch materialization plan."""

    _require_copy_mode(copy_mode)
    source_root, scratch_root = _dataset_roots(reference_plan, material_plan)

    reference_actions = list(reference_plan.get("actions") or [])
    scene_actions = [
        _copy_action_from_reference(action, source_root=source_root, scratch_root=scratch_root, copy_mode=copy_mode)
        for action in reference_actions
        if action.get("kind") == "scene_dir"
    ]
    model_actions = [
        _copy_action_from_reference(action, source_root=source_root, scratch_root=scratch_root, copy_mode=copy_mode)
        for action in reference_actions
        if action.get("kind") == "target_model_root"
    ]
    material_actions = _dedupe_by_destination(
        [
            _material_file_action(action, source_root=source_root, scratch_root=scratch_root, copy_mode=copy_mode)
            for action in material_plan.get("material_file_actions", [])
        ]
    )
    scene_repairs: list[dict[str, Any]] = []
    for scene_action in scene_actions:
        scene_repairs.extend(
            _scene_entry_repair_actions(scene_action, source_root=source_root, scratch_root=scratch_root)
        )
    model_repairs = [
        _relative_symlink_action_safe(action, scratch_root=scratch_root)
        for action in material_plan.get("materials_entry_repair_actions", [])
    ]

    actions = [*scene_actions, *model_actions, *material_actions, *scene_repairs, *model_repairs]
    conversion_commands = list(reference_plan.get("conversion_commands") or [])
    summary = {
        "scene_dir_count": len(scene_actions),
        "target_model_root_count": len(model_actions),
        "material_file_count": len(material_actions),
        "scene_entry_repair_count": len(scene_repairs),
        "model_materials_entry_repair_count": len(model_repairs),
        "entry_repair_count": len(scene_repairs) + len(model_repairs),
        "resource_tree_count": 0,
        "action_count": len(actions),
        "copy_mode": copy_mode,
        "conversion_command_count": len(conversion_commands),
        "planner_only": False,
        "dry_run_default": True,
        "known_scene_dependency_gap": True,
    }
    return {
        "schema_version": 1,
        "status": "planned_targeted_materialization",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_targeted_closure.py",
        "generated_at_utc": _utc_now(),
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "reference_plan_status": reference_plan.get("status"),
        "material_plan_status": material_plan.get("status"),
        "summary": summary,
        "actions": actions,
        "conversion_commands": conversion_commands,
        "notes": [
            "This plan does not mirror split-level Materials or models resource trees.",
            "Scene-local pointer files are repaired only in scratch.",
            "Whole-scene conversion needs a broader scene dependency closure for unselected model references.",
        ],
    }


def _copy_file_hardlink(src: str, dst: str) -> None:
    os.link(src, dst)


def _copy_file(src: Path, dst: Path, *, copy_mode: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if copy_mode == "hardlink":
        os.link(src, dst)
    else:
        shutil.copy2(src, dst)


def _copy_tree(src: Path, dst: Path, *, copy_mode: str) -> None:
    copy_function = _copy_file_hardlink if copy_mode == "hardlink" else shutil.copy2
    shutil.copytree(src, dst, symlinks=True, copy_function=copy_function)


def _copy_tree_action(action: dict[str, Any], *, scratch_root: Path, dry_run: bool) -> dict[str, Any]:
    src = Path(str(action["src"]))
    dst = Path(str(action["dst"]))
    if not src.is_dir():
        raise FileNotFoundError(src)
    result = {
        "kind": action["kind"],
        "src": str(src),
        "dst": str(dst),
        "copy_mode": action.get("copy_mode"),
        "status": "planned" if dry_run else "created",
    }
    if dry_run:
        return result
    if dst.exists():
        if dst.is_symlink() or not dst.is_dir():
            raise ValueError(f"existing tree destination must be a directory: {dst}")
        validation = _validate_existing_tree(
            src,
            dst,
            scratch_root=scratch_root,
            repairable_entry_names=set(action.get("repairable_entry_names") or []),
        )
        return {**result, "status": "exists", **validation}
    _assert_scratch_path(dst, scratch_root, label=f"{action['kind']} dst")
    _validate_symlink_targets(source_copy_root=src, destination_copy_root=dst, scratch_root=scratch_root)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _copy_tree(src, dst, copy_mode=str(action.get("copy_mode") or "hardlink"))
    return result


def _copy_material_file_action(action: dict[str, Any], *, scratch_root: Path, dry_run: bool) -> dict[str, Any]:
    src = Path(str(action["src"]))
    dst = Path(str(action["dst"]))
    if not src.is_file():
        raise FileNotFoundError(src)
    result = {
        "kind": action["kind"],
        "src": str(src),
        "dst": str(dst),
        "copy_mode": action.get("copy_mode"),
        "status": "planned" if dry_run else "created",
    }
    if dry_run:
        return result
    if dst.exists():
        if not dst.is_file():
            raise ValueError(f"existing material destination must be a file: {dst}")
        if not filecmp.cmp(src, dst, shallow=False):
            raise ValueError(f"existing material destination differs from source: {dst}")
        return {**result, "status": "exists"}
    _assert_scratch_path(dst, scratch_root, label="material action dst")
    _copy_file(src, dst, copy_mode=str(action.get("copy_mode") or "hardlink"))
    return result


def _repair_symlink_action(action: dict[str, Any], *, scratch_root: Path, dry_run: bool) -> dict[str, Any]:
    action = _relative_symlink_action_safe(action, scratch_root=scratch_root)
    dst = Path(str(action["dst"]))
    target_text = str(action["target_text"])
    result = {
        "kind": action["kind"],
        "dst": str(dst),
        "target_text": target_text,
        "status": "planned" if dry_run else "created",
    }
    if dry_run:
        return result
    if dst.is_symlink():
        if os.readlink(dst) == target_text:
            return {**result, "status": "exists"}
        dst.unlink()
    elif dst.exists():
        if dst.is_dir():
            raise ValueError(f"repair destination is an existing directory: {dst}")
        dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(target_text)
    return result


def _validate_plan_paths(plan: dict[str, Any]) -> tuple[Path, Path]:
    source_root = Path(str(plan["source_root"])).resolve()
    scratch_root = Path(str(plan["scratch_root"])).resolve()
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")
    for action in plan.get("actions", []):
        kind = action.get("kind")
        if kind in {"scene_dir", "target_model_root", "material_asset_file"}:
            _assert_source_path(Path(str(action["src"])), source_root, label=f"{kind} src")
        if kind in {"scene_dir", "target_model_root", "material_asset_file"}:
            _assert_scratch_path(Path(str(action["dst"])), scratch_root, label=f"{kind} dst")
        elif kind in {"scene_entry_repair", "model_materials_entry_repair"}:
            _relative_symlink_action_safe(action, scratch_root=scratch_root)
        else:
            raise ValueError(f"unsupported materialization action kind: {kind}")
    return source_root, scratch_root


def materialize_from_plan(plan: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
    """Apply or dry-run a targeted materialization plan."""

    _source_root, scratch_root = _validate_plan_paths(plan)
    results: list[dict[str, Any]] = []
    for action in plan.get("actions", []):
        kind = action.get("kind")
        if kind in {"scene_dir", "target_model_root"}:
            results.append(_copy_tree_action(action, scratch_root=scratch_root, dry_run=dry_run))
        elif kind == "material_asset_file":
            results.append(_copy_material_file_action(action, scratch_root=scratch_root, dry_run=dry_run))
        elif kind in {"scene_entry_repair", "model_materials_entry_repair"}:
            results.append(_repair_symlink_action(action, scratch_root=scratch_root, dry_run=dry_run))
        else:
            raise ValueError(f"unsupported materialization action kind: {kind}")

    status_counts: dict[str, int] = {}
    for result in results:
        status = str(result["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        **plan,
        "dry_run": bool(dry_run),
        "reported_at_utc": _utc_now(),
        "results": results,
        "summary": {
            **plan.get("summary", {}),
            "dry_run": bool(dry_run),
            "planned_count": status_counts.get("planned", 0),
            "created_count": status_counts.get("created", 0),
            "exists_count": status_counts.get("exists", 0),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-plan", type=Path, default=DEFAULT_REFERENCE_PLAN)
    parser.add_argument("--material-plan", type=Path, default=DEFAULT_MATERIAL_PLAN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--copy-mode", choices=COPY_MODES, default="hardlink")
    parser.add_argument("--apply", action="store_true", help="write to scratch; default is dry-run")
    args = parser.parse_args()

    reference_plan = _load_json(args.reference_plan)
    material_plan = _load_json(args.material_plan)
    plan = build_targeted_materialization_plan(reference_plan, material_plan, copy_mode=args.copy_mode)
    report = materialize_from_plan(plan, dry_run=not bool(args.apply))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} with {report['summary']['action_count']} actions, "
        f"dry_run={report['dry_run']}, scene_dirs={report['summary']['scene_dir_count']}, "
        f"model_roots={report['summary']['target_model_root_count']}, "
        f"material_files={report['summary']['material_file_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
