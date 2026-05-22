#!/usr/bin/env python3
"""Plan visibility-aware GRScenes render views.

This first gate is intentionally pure Python. It classifies planned cameras
against already-extracted axis-aligned obstacle boxes. A later USD/PXR pass can
populate those boxes from composed stages without changing the classification
contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_RENDER_MANIFEST = RAW_DIR / "render_manifest.json"
DEFAULT_OUTPUT = RAW_DIR / "visibility_preflight_report.json"
EPS = 1.0e-9


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _git_status_porcelain() -> list[str]:
    try:
        tracked_output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        untracked_output = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    lines = [line for line in tracked_output.splitlines() if line]
    untracked_count = len([line for line in untracked_output.splitlines() if line])
    if untracked_count:
        lines.append(f"?? {untracked_count} untracked files omitted from provenance")
    return lines


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vec3(values: Any, *, field: str) -> list[float]:
    if not isinstance(values, list | tuple) or len(values) != 3:
        raise ValueError(f"{field} must contain exactly three values")
    out = [float(value) for value in values]
    if not all(math.isfinite(value) for value in out):
        raise ValueError(f"{field} values must be finite")
    return out


def _round_interval(t_enter: float, t_exit: float) -> dict[str, float]:
    return {"t_enter": round(float(t_enter), 9), "t_exit": round(float(t_exit), 9)}


def _bbox_min_max(box: dict[str, Any]) -> tuple[list[float], list[float]]:
    lo = _vec3(box.get("min"), field="bbox.min")
    hi = _vec3(box.get("max"), field="bbox.max")
    return [min(lo[i], hi[i]) for i in range(3)], [max(lo[i], hi[i]) for i in range(3)]


def _point_inside_bbox(point: list[float], box: dict[str, Any], *, padding: float = 0.0) -> bool:
    lo, hi = _bbox_min_max(box)
    return all(lo[i] - padding <= point[i] <= hi[i] + padding for i in range(3))


def segment_aabb_interval(start: list[float], end: list[float], box: dict[str, Any]) -> dict[str, float] | None:
    """Return segment parameter interval where start->end intersects an AABB."""

    origin = _vec3(start, field="segment.start")
    target = _vec3(end, field="segment.end")
    lo, hi = _bbox_min_max(box)
    direction = [target[i] - origin[i] for i in range(3)]
    t_enter = 0.0
    t_exit = 1.0
    for axis in range(3):
        if abs(direction[axis]) <= EPS:
            if origin[axis] < lo[axis] or origin[axis] > hi[axis]:
                return None
            continue
        inv = 1.0 / direction[axis]
        t0 = (lo[axis] - origin[axis]) * inv
        t1 = (hi[axis] - origin[axis]) * inv
        if t0 > t1:
            t0, t1 = t1, t0
        t_enter = max(t_enter, t0)
        t_exit = min(t_exit, t1)
        if t_enter > t_exit:
            return None
    if t_exit < 0.0 or t_enter > 1.0:
        return None
    return _round_interval(max(0.0, t_enter), min(1.0, t_exit))


def _target_interval(camera_position: list[float], look_at: list[float], target_bbox: dict[str, Any]) -> dict[str, float]:
    interval = segment_aabb_interval(camera_position, look_at, target_bbox)
    if interval is not None:
        return interval
    return {"t_enter": 1.0, "t_exit": 1.0}


def classify_visibility_candidate(
    *,
    camera: dict[str, Any],
    target_bbox: dict[str, Any],
    obstacles: list[dict[str, Any]],
    padding: float = 0.0,
) -> dict[str, Any]:
    """Classify one planned camera using approximate AABB line-of-sight tests."""

    position = _vec3(camera.get("position_world"), field="camera.position_world")
    look_at = _vec3(camera.get("look_at") or camera.get("target_world"), field="camera.look_at")
    target_interval = _target_interval(position, look_at, target_bbox)

    for obstacle in obstacles:
        obstacle_bbox = obstacle.get("bbox") or {}
        if _point_inside_bbox(position, obstacle_bbox, padding=padding):
            return {
                "status": "blocked_camera_inside_obstacle_aabb",
                "blocker_prim_path": obstacle.get("prim_path"),
                "blocker_interval": {"t_enter": 0.0, "t_exit": 0.0},
                "target_interval": target_interval,
            }

    best_blocker: dict[str, Any] | None = None
    for obstacle in obstacles:
        interval = segment_aabb_interval(position, look_at, obstacle.get("bbox") or {})
        if interval is None:
            continue
        if interval["t_enter"] < target_interval["t_enter"] - EPS:
            if best_blocker is None or interval["t_enter"] < best_blocker["blocker_interval"]["t_enter"]:
                best_blocker = {
                    "prim_path": obstacle.get("prim_path"),
                    "blocker_interval": interval,
                }

    if best_blocker is not None:
        return {
            "status": "blocked_centerline_aabb",
            "blocker_prim_path": best_blocker["prim_path"],
            "blocker_interval": best_blocker["blocker_interval"],
            "target_interval": target_interval,
        }

    return {
        "status": "centerline_clear",
        "blocker_prim_path": None,
        "blocker_interval": None,
        "target_interval": target_interval,
    }


def _pair_target_bbox(pair: dict[str, Any]) -> dict[str, Any]:
    if pair.get("world_bbox"):
        return dict(pair["world_bbox"])
    for condition in pair.get("conditions", []):
        if condition.get("world_bbox"):
            return dict(condition["world_bbox"])
    raise KeyError(f"world_bbox missing for pair {pair.get('pair_id')}")


def normalize_geometry_index(geometry_index: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], str]:
    """Accept either a direct scene mapping or the full geometry-index report."""

    if not isinstance(geometry_index, dict):
        raise TypeError("geometry_index must be a dictionary")
    if isinstance(geometry_index.get("geometry_index"), dict):
        mapping = geometry_index["geometry_index"]
        schema = "visibility_geometry_index_report"
    else:
        mapping = geometry_index
        schema = "scene_id_mapping"
    normalized: dict[str, list[dict[str, Any]]] = {}
    for scene_id, obstacles in mapping.items():
        if not isinstance(obstacles, list):
            raise TypeError(f"geometry obstacles for scene {scene_id!r} must be a list")
        normalized[str(scene_id)] = [dict(item) for item in obstacles]
    return normalized, schema


def _manifest_scene_ids(render_manifest: dict[str, Any]) -> list[str]:
    return sorted({str(pair.get("source_scene_id")) for pair in render_manifest.get("render_pairs", []) if pair.get("source_scene_id")})


def _validate_geometry_coverage(
    render_manifest: dict[str, Any],
    geometry_index: dict[str, list[dict[str, Any]]],
) -> list[str]:
    scene_ids = _manifest_scene_ids(render_manifest)
    missing = [scene_id for scene_id in scene_ids if scene_id not in geometry_index]
    if missing:
        preview = ", ".join(missing[:10])
        suffix = "" if len(missing) <= 10 else f", ... (+{len(missing) - 10} more)"
        raise ValueError(f"missing geometry scenes: {preview}{suffix}")
    return [scene_id for scene_id in scene_ids if not geometry_index.get(scene_id)]


def build_visibility_report(
    render_manifest: dict[str, Any],
    *,
    geometry_index: dict[str, Any],
) -> dict[str, Any]:
    normalized_geometry, geometry_source_schema = normalize_geometry_index(geometry_index)
    empty_geometry_scene_ids = _validate_geometry_coverage(render_manifest, normalized_geometry)
    pair_reviews: list[dict[str, Any]] = []
    recommended: dict[str, dict[str, Any]] = {}
    for pair in render_manifest.get("render_pairs", []):
        scene_id = str(pair.get("source_scene_id"))
        target_id = str(pair.get("target_id"))
        view = pair.get("view") or {}
        result = classify_visibility_candidate(
            camera=dict(view.get("camera") or {}),
            target_bbox=_pair_target_bbox(pair),
            obstacles=normalized_geometry.get(scene_id, []),
        )
        review = {
            "pair_id": pair.get("pair_id"),
            "target_id": target_id,
            "source_scene_id": scene_id,
            "view_id": view.get("view_id"),
            "visibility_status": result["status"],
            "blocker_prim_path": result["blocker_prim_path"],
            "blocker_interval": result["blocker_interval"],
            "target_interval": result["target_interval"],
        }
        pair_reviews.append(review)
        if result["status"] == "centerline_clear" and target_id not in recommended:
            recommended[target_id] = {
                "pair_id": pair.get("pair_id"),
                "view_id": view.get("view_id"),
                "source_scene_id": scene_id,
                "selection_reason": "first_centerline_clear_candidate_in_manifest_order",
            }

    status_counts = Counter(item["visibility_status"] for item in pair_reviews)
    centerline_clear_count = int(status_counts.get("centerline_clear", 0))
    return {
        "schema_version": 1,
        "status": "visibility_preflight_report",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_visibility_aware_views.py",
        "generated_at_utc": _utc_now(),
        "summary": {
            "render_pair_count": len(pair_reviews),
            "visibility_method": "single_centerline_vs_non_target_aabb_preflight",
            "claim_boundary": "preflight_only_not_rendered_visibility_or_vlm_evidence",
            "geometry_source_schema": geometry_source_schema,
            "centerline_clear_pair_count": centerline_clear_count,
            "clear_pair_count": centerline_clear_count,
            "blocked_pair_count": len(pair_reviews) - centerline_clear_count,
            "recommended_target_count": len(recommended),
            "geometry_source": "provided_geometry_index",
            "empty_geometry_scene_count": len(empty_geometry_scene_ids),
            "empty_geometry_scene_ids": empty_geometry_scene_ids,
            "visibility_status_counts": dict(sorted(status_counts.items())),
        },
        "recommended_pairs_by_target": recommended,
        "pair_reviews": pair_reviews,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-manifest", type=Path, default=DEFAULT_RENDER_MANIFEST)
    parser.add_argument("--geometry-index", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    render_manifest = _load_json(args.render_manifest)
    geometry_index = _load_json(args.geometry_index)
    report = build_visibility_report(render_manifest, geometry_index=geometry_index)
    report["render_manifest"] = {
        "path": str(args.render_manifest),
        "hash_sha256": _sha256_file(args.render_manifest),
    }
    report["geometry_index"] = {
        "path": str(args.geometry_index),
        "hash_sha256": _sha256_file(args.geometry_index),
    }
    report["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} clear={report['summary']['clear_pair_count']} "
        f"blocked={report['summary']['blocked_pair_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
