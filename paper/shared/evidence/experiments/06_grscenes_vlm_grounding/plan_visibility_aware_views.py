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
        output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    return [line for line in output.splitlines() if line]


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
                "status": "blocked_camera_inside_obstacle",
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
            "status": "blocked_line_of_sight",
            "blocker_prim_path": best_blocker["prim_path"],
            "blocker_interval": best_blocker["blocker_interval"],
            "target_interval": target_interval,
        }

    return {
        "status": "clear",
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


def build_visibility_report(
    render_manifest: dict[str, Any],
    *,
    geometry_index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    pair_reviews: list[dict[str, Any]] = []
    recommended: dict[str, dict[str, Any]] = {}
    for pair in render_manifest.get("render_pairs", []):
        scene_id = str(pair.get("source_scene_id"))
        target_id = str(pair.get("target_id"))
        view = pair.get("view") or {}
        result = classify_visibility_candidate(
            camera=dict(view.get("camera") or {}),
            target_bbox=_pair_target_bbox(pair),
            obstacles=geometry_index.get(scene_id, []),
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
        if result["status"] == "clear" and target_id not in recommended:
            recommended[target_id] = {
                "pair_id": pair.get("pair_id"),
                "view_id": view.get("view_id"),
                "source_scene_id": scene_id,
                "selection_reason": "first_clear_candidate_in_manifest_order",
            }

    clear_count = len([item for item in pair_reviews if item["visibility_status"] == "clear"])
    return {
        "schema_version": 1,
        "status": "visibility_preflight_report",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_visibility_aware_views.py",
        "generated_at_utc": _utc_now(),
        "summary": {
            "render_pair_count": len(pair_reviews),
            "clear_pair_count": clear_count,
            "blocked_pair_count": len(pair_reviews) - clear_count,
            "recommended_target_count": len(recommended),
            "geometry_source": "provided_geometry_index",
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
