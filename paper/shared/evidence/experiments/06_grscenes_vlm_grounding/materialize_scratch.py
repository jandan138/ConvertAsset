#!/usr/bin/env python3
"""Materialize selected GRScenes source scenes into a no-MDL scratch tree.

This script is pure Python and intentionally does not import pxr or Isaac Sim.
It prepares the filesystem layout that ConvertAsset's no-MDL command can safely
operate on without writing sidecar files into the immutable GRScenes source
dataset.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_INPUT = (
    PROJECT_ROOT
    / "paper"
    / "shared"
    / "evidence"
    / "raw"
    / "grscene_vlm_grounding"
    / "source_manifest.json"
)
DEFAULT_OUTPUT = DEFAULT_INPUT.with_name("scratch_materialization_report.json")
RESOURCE_NAMES = ("Materials", "models")
COPY_MODES = ("hardlink", "copy")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _resolve_maybe_missing(path: Path) -> Path:
    return path.resolve(strict=False)


def _dataset_roots(manifest: dict[str, Any]) -> tuple[Path, Path]:
    roles = manifest.get("dataset_roles") or {}
    benchmark = roles.get("benchmark_source_dataset") or {}
    intervention = roles.get("intervention_outputs") or {}
    source_root_text = str(benchmark.get("local_root") or "").strip()
    scratch_root_text = str(intervention.get("scratch_root") or "").strip()
    if not source_root_text or not scratch_root_text:
        raise ValueError("manifest must define benchmark source_root and intervention scratch_root")
    source_root = Path(source_root_text)
    scratch_root = Path(scratch_root_text)
    return source_root.resolve(), scratch_root.resolve()


def _ensure_tree_destination_safe(dst: Path) -> None:
    if dst.is_symlink():
        raise ValueError(f"destination must not be a symlink: {dst}")
    if dst.exists() and not dst.is_dir():
        raise ValueError(f"destination must be a directory when it already exists: {dst}")


def _tree_manifest(root: Path) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for path in root.rglob("*"):
        relative_path = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries[relative_path] = {"type": "symlink", "target": os.readlink(path)}
            continue
        if path.is_dir():
            entries[relative_path] = {"type": "dir"}
        elif path.is_file():
            entries[relative_path] = {"type": "file", "size": path.stat().st_size}
    return entries


def _tree_counts_from_manifest(manifest: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = {"file_count": 0, "dir_count": 0, "symlink_count": 0}
    for entry in manifest.values():
        entry_type = entry["type"]
        if entry_type == "file":
            counts["file_count"] += 1
        elif entry_type == "dir":
            counts["dir_count"] += 1
        elif entry_type == "symlink":
            counts["symlink_count"] += 1
    return counts


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


def _validate_existing_tree(src: Path, dst: Path, *, scratch_root: Path) -> dict[str, dict[str, int]]:
    source_manifest = _tree_manifest(src)
    destination_manifest = _tree_manifest(dst)
    source_counts = _tree_counts_from_manifest(source_manifest)
    destination_counts = _tree_counts_from_manifest(destination_manifest)
    if source_manifest != destination_manifest:
        raise ValueError(
            f"existing destination is incomplete or differs from source tree: "
            f"{dst} has {destination_counts}, expected {source_counts}"
        )
    _validate_symlink_targets(source_copy_root=dst, destination_copy_root=dst, scratch_root=scratch_root)
    return {"source_counts": source_counts, "destination_counts": destination_counts}


def validate_action_paths(actions: list[dict[str, Any]], *, source_root: Path, scratch_root: Path) -> None:
    for action in actions:
        src = Path(str(action["src"]))
        dst = Path(str(action["dst"]))
        _ensure_tree_destination_safe(dst)
        if not _is_relative_to(src, source_root):
            raise ValueError(f"action src must be inside source_root: {src}")
        if not _is_relative_to(_resolve_maybe_missing(dst), scratch_root):
            raise ValueError(f"action dst must be inside scratch_root: {dst}")


def selected_scenes(manifest: dict[str, Any], *, limit_scenes: int | None = None) -> list[dict[str, Any]]:
    scenes = list(manifest.get("scenes") or [])
    if limit_scenes is not None:
        if limit_scenes < 0:
            raise ValueError("limit_scenes must be non-negative")
        scenes = scenes[:limit_scenes]
    return scenes


def validate_manifest_safety(manifest: dict[str, Any], *, limit_scenes: int | None = None) -> tuple[Path, Path]:
    source_root, scratch_root = _dataset_roots(manifest)
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")

    for scene in selected_scenes(manifest, limit_scenes=limit_scenes):
        scene_dir = Path(str(scene.get("scene_dir") or "")).resolve()
        source_usd = Path(str(scene.get("source_usd") or "")).resolve()
        scratch_scene_root = Path(str(scene.get("scratch_scene_root") or "")).resolve()
        converted_usd = Path(str(scene.get("converted_usd") or "")).resolve()
        if not _is_relative_to(scene_dir, source_root):
            raise ValueError(f"scene_dir must be inside source_root: {scene_dir}")
        if not _is_relative_to(source_usd, source_root):
            raise ValueError(f"source_usd must be inside source_root: {source_usd}")
        if not _is_relative_to(scratch_scene_root, scratch_root):
            raise ValueError(f"scratch_scene_root must be inside scratch_root: {scratch_scene_root}")
        if not _is_relative_to(converted_usd, scratch_root):
            raise ValueError(f"converted_usd must be inside scratch_root: {converted_usd}")
    return source_root, scratch_root


def split_root_for_scene(scene_dir: Path) -> Path:
    """Return the GRScenes split root containing `models`, `Materials`, and `scenes`."""

    return scene_dir.resolve().parent.parent


def _scratch_split_root(scene: dict[str, Any]) -> Path:
    return Path(str(scene["scratch_scene_root"])).resolve().parent.parent


def build_materialization_plan(
    manifest: dict[str, Any],
    *,
    limit_scenes: int | None = None,
    copy_mode: str = "hardlink",
) -> dict[str, Any]:
    if copy_mode not in COPY_MODES:
        raise ValueError(f"copy_mode must be one of {', '.join(COPY_MODES)}")
    source_root, scratch_root = validate_manifest_safety(manifest, limit_scenes=limit_scenes)

    actions: list[dict[str, Any]] = []
    resource_keys: set[tuple[str, str]] = set()
    scenes = selected_scenes(manifest, limit_scenes=limit_scenes)
    for scene in scenes:
        scene_dir = Path(str(scene["scene_dir"])).resolve()
        split_root = split_root_for_scene(scene_dir)
        scratch_split_root = _scratch_split_root(scene)
        for resource_name in RESOURCE_NAMES:
            src = split_root / resource_name
            dst = scratch_split_root / resource_name
            key = (str(src), str(dst))
            if key in resource_keys:
                continue
            resource_keys.add(key)
            actions.append(
                {
                    "kind": "resource_tree",
                    "resource_name": resource_name,
                    "src": str(src),
                    "dst": str(dst),
                    "copy_mode": copy_mode,
                }
            )
    actions.sort(key=lambda item: (item["kind"], item.get("dst", "")))

    for scene in scenes:
        actions.append(
            {
                "kind": "scene_dir",
                "source_scene_id": scene.get("source_scene_id"),
                "source_scene_split": scene.get("source_scene_split"),
                "src": str(Path(str(scene["scene_dir"])).resolve()),
                "dst": str(Path(str(scene["scratch_scene_root"])).resolve()),
                "copy_mode": copy_mode,
            }
        )
    validate_action_paths(actions, source_root=source_root, scratch_root=scratch_root)

    conversion_commands = [str(scene.get("conversion_command")) for scene in scenes if scene.get("conversion_command")]
    return {
        "schema_version": 1,
        "status": "planned_scratch_materialization",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "summary": {
            "scene_count": len(scenes),
            "resource_tree_count": len(resource_keys),
            "action_count": len(actions),
            "copy_mode": copy_mode,
            "conversion_command_count": len(conversion_commands),
        },
        "actions": actions,
        "conversion_commands": conversion_commands,
    }


def _copy_file_hardlink(src: str, dst: str) -> None:
    os.link(src, dst)


def _copy_tree(src: Path, dst: Path, *, copy_mode: str) -> None:
    copy_function = _copy_file_hardlink if copy_mode == "hardlink" else shutil.copy2
    shutil.copytree(src, dst, symlinks=True, copy_function=copy_function)


def materialize_from_plan(plan: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
    source_root = Path(str(plan["source_root"])).resolve()
    scratch_root = Path(str(plan["scratch_root"])).resolve()
    validate_action_paths(list(plan.get("actions", [])), source_root=source_root, scratch_root=scratch_root)
    results: list[dict[str, Any]] = []
    for action in plan.get("actions", []):
        src = Path(str(action["src"]))
        dst = Path(str(action["dst"]))
        result = {
            "kind": action.get("kind"),
            "src": str(src),
            "dst": str(dst),
            "copy_mode": action.get("copy_mode"),
            "status": "planned" if dry_run else "created",
        }
        if not src.exists():
            raise FileNotFoundError(src)
        if dry_run:
            results.append(result)
            continue
        if dst.exists():
            results.append({**result, "status": "exists", **_validate_existing_tree(src, dst, scratch_root=scratch_root)})
            continue
        _validate_symlink_targets(source_copy_root=src, destination_copy_root=dst, scratch_root=scratch_root)
        dst.parent.mkdir(parents=True, exist_ok=True)
        _copy_tree(src, dst, copy_mode=str(action.get("copy_mode") or "hardlink"))
        results.append(result)

    status_counts: dict[str, int] = {}
    for result in results:
        status = str(result["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        **plan,
        "dry_run": bool(dry_run),
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
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit-scenes", type=int, default=None)
    parser.add_argument("--copy-mode", choices=COPY_MODES, default="hardlink")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = _load_json(args.source_manifest)
    plan = build_materialization_plan(
        manifest,
        limit_scenes=args.limit_scenes,
        copy_mode=args.copy_mode,
    )
    report = materialize_from_plan(plan, dry_run=bool(args.dry_run))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} with {report['summary']['scene_count']} scenes, "
        f"{report['summary']['resource_tree_count']} resource trees, dry_run={report['dry_run']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
