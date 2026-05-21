#!/usr/bin/env python3
"""Project GRScenes world-space target bboxes into render image space."""

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
DEFAULT_PREFLIGHT_REPORT = RAW_DIR / "visibility_preflight_report.json"
DEFAULT_RENDER_SUMMARY = RAW_DIR / "recommended_paired_render_summary.json"
DEFAULT_OUTPUT = RAW_DIR / "target_projection_qa_report.json"
DEFAULT_MIN_AREA_PX = 1000.0
EPS = 1.0e-9


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def _vec3(values: Any, *, field: str) -> list[float]:
    if not isinstance(values, list | tuple) or len(values) != 3:
        raise ValueError(f"{field} must contain exactly three numeric values")
    out = [float(value) for value in values]
    if not all(math.isfinite(value) for value in out):
        raise ValueError(f"{field} values must be finite")
    return out


def _sub(a: list[float], b: list[float]) -> list[float]:
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _dot(a: list[float], b: list[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _normalize(a: list[float], *, field: str) -> list[float]:
    length = math.sqrt(_dot(a, a))
    if not math.isfinite(length) or length <= EPS:
        raise ValueError(f"{field} vector is degenerate")
    return [a[0] / length, a[1] / length, a[2] / length]


def _camera_basis(camera: dict[str, Any]) -> dict[str, list[float]]:
    eye = _vec3(camera.get("position_world"), field="camera.position_world")
    look_at = _vec3(camera.get("look_at") or camera.get("target_world"), field="camera.look_at")
    up_hint = _normalize(_vec3(camera.get("up_world", [0.0, 0.0, 1.0]), field="camera.up_world"), field="camera.up_world")
    forward = _normalize(_sub(look_at, eye), field="camera forward")
    right = _cross(forward, up_hint)
    if math.sqrt(_dot(right, right)) <= EPS:
        fallback = [1.0, 0.0, 0.0] if abs(forward[0]) < 0.9 else [0.0, 1.0, 0.0]
        right = _cross(forward, fallback)
    right = _normalize(right, field="camera right")
    up = _normalize(_cross(right, forward), field="camera up")
    return {"eye": eye, "forward": forward, "right": right, "up": up}


def _fovs(camera: dict[str, Any], *, image_width: int, image_height: int) -> tuple[float, float]:
    if camera.get("fov_h_deg") is not None:
        fov_h = math.radians(float(camera["fov_h_deg"]))
    else:
        focal = float(camera.get("focal_length_mm", 9.0))
        aperture = float(camera.get("horizontal_aperture_mm", 20.955))
        fov_h = 2.0 * math.atan(aperture / (2.0 * focal))
    aspect = float(image_width) / float(max(1, image_height))
    fov_v = 2.0 * math.atan(math.tan(fov_h * 0.5) / aspect)
    return fov_h, fov_v


def project_world_point(
    camera: dict[str, Any],
    point_world: list[float],
    *,
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    basis = _camera_basis(camera)
    point = _vec3(point_world, field="point_world")
    rel = _sub(point, basis["eye"])
    depth = _dot(rel, basis["forward"])
    if depth <= EPS:
        return {
            "pixel_xy": None,
            "depth": round(float(depth), 6),
            "in_front": False,
            "in_frame": False,
        }
    fov_h, fov_v = _fovs(camera, image_width=image_width, image_height=image_height)
    x_cam = _dot(rel, basis["right"])
    y_cam = _dot(rel, basis["up"])
    x_ndc = (x_cam / depth) / math.tan(fov_h * 0.5)
    y_ndc = (y_cam / depth) / math.tan(fov_v * 0.5)
    x_px = (x_ndc + 1.0) * 0.5 * float(image_width)
    y_px = (1.0 - y_ndc) * 0.5 * float(image_height)
    return {
        "pixel_xy": [round(x_px, 6), round(y_px, 6)],
        "depth": round(float(depth), 6),
        "in_front": True,
        "in_frame": 0.0 <= x_px <= image_width and 0.0 <= y_px <= image_height,
    }


def _bbox_corners(world_bbox: dict[str, Any]) -> list[list[float]]:
    lo = _vec3(world_bbox.get("min"), field="world_bbox.min")
    hi = _vec3(world_bbox.get("max"), field="world_bbox.max")
    mins = [min(lo[i], hi[i]) for i in range(3)]
    maxes = [max(lo[i], hi[i]) for i in range(3)]
    return [
        [x, y, z]
        for x in (mins[0], maxes[0])
        for y in (mins[1], maxes[1])
        for z in (mins[2], maxes[2])
    ]


def _round_box(box: list[float] | None) -> list[float] | None:
    return [round(float(value), 3) for value in box] if box is not None else None


def _clip_box(box: list[float], *, image_width: int, image_height: int) -> list[float]:
    return [
        max(0.0, min(float(image_width), box[0])),
        max(0.0, min(float(image_height), box[1])),
        max(0.0, min(float(image_width), box[2])),
        max(0.0, min(float(image_height), box[3])),
    ]


def _area(box: list[float] | None) -> float:
    if box is None:
        return 0.0
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def project_world_bbox(
    camera: dict[str, Any],
    world_bbox: dict[str, Any],
    *,
    image_width: int,
    image_height: int,
    min_area_px: float = DEFAULT_MIN_AREA_PX,
) -> dict[str, Any]:
    corner_projections = [
        project_world_point(camera, corner, image_width=image_width, image_height=image_height)
        for corner in _bbox_corners(world_bbox)
    ]
    front_pixels = [item["pixel_xy"] for item in corner_projections if item["pixel_xy"] is not None]
    center_projection = project_world_point(
        camera,
        _vec3(world_bbox.get("center"), field="world_bbox.center"),
        image_width=image_width,
        image_height=image_height,
    )
    if not front_pixels:
        return {
            "status": "projection_failed_no_front_corners",
            "bbox_xyxy": None,
            "raw_bbox_xyxy": None,
            "bbox_area_px": 0.0,
            "bbox_area_fraction": 0.0,
            "center_pixel_xy": center_projection["pixel_xy"],
            "center_in_frame": bool(center_projection["in_frame"]),
            "front_corner_count": 0,
        }
    xs = [float(item[0]) for item in front_pixels]
    ys = [float(item[1]) for item in front_pixels]
    raw = [min(xs), min(ys), max(xs), max(ys)]
    clipped = _clip_box(raw, image_width=image_width, image_height=image_height)
    area = _area(clipped)
    frame_area = float(image_width) * float(image_height)
    if area <= 0.0:
        status = "projection_outside_frame"
    elif area < float(min_area_px):
        status = "projection_too_small"
    elif not center_projection["in_frame"]:
        status = "projection_center_outside_frame"
    else:
        status = "projection_ok"
    return {
        "status": status,
        "bbox_xyxy": _round_box(clipped),
        "raw_bbox_xyxy": _round_box(raw),
        "bbox_area_px": round(area, 3),
        "bbox_area_fraction": round(area / frame_area, 6),
        "center_pixel_xy": _round_box(center_projection["pixel_xy"]),
        "center_in_frame": bool(center_projection["in_frame"]),
        "front_corner_count": len(front_pixels),
    }


def _recommended_pair_ids(preflight_report: dict[str, Any]) -> list[str]:
    return [str(item["pair_id"]) for item in preflight_report.get("recommended_pairs_by_target", {}).values()]


def _pair_lookup(render_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(pair.get("pair_id")): pair for pair in render_manifest.get("render_pairs", [])}


def _render_smoke_pass_lookup(render_summary: dict[str, Any]) -> dict[str, bool]:
    return {str(pair.get("pair_id")): bool(pair.get("render_smoke_pass")) for pair in render_summary.get("pairs", [])}


def _condition_target(condition: dict[str, Any], projection: dict[str, Any]) -> dict[str, Any]:
    target = dict(condition.get("target") or {})
    target["bbox_xyxy"] = projection["bbox_xyxy"]
    target["bbox_source"] = "projected_world_bbox_from_manifest_camera"
    return target


def _task_id(condition: dict[str, Any]) -> str:
    task = condition.get("task")
    if isinstance(task, dict):
        return str(task.get("task_id") or "s1_referred_object_localization")
    if task:
        return str(task)
    return "s1_referred_object_localization"


def build_projection_report(
    render_manifest: dict[str, Any],
    *,
    preflight_report: dict[str, Any],
    render_summary: dict[str, Any],
    min_area_px: float = DEFAULT_MIN_AREA_PX,
) -> dict[str, Any]:
    renderer_settings = render_manifest.get("renderer_settings") or {}
    image_width = int(renderer_settings.get("image_width") or 600)
    image_height = int(renderer_settings.get("image_height") or 450)
    pairs_by_id = _pair_lookup(render_manifest)
    render_smoke_pass = _render_smoke_pass_lookup(render_summary)
    pair_ids = _recommended_pair_ids(preflight_report)
    pair_reports: list[dict[str, Any]] = []
    scoring_records: list[dict[str, Any]] = []

    for pair_id in pair_ids:
        if pair_id not in pairs_by_id:
            raise KeyError(f"recommended pair missing from render_manifest: {pair_id}")
        pair = pairs_by_id[pair_id]
        condition0 = (pair.get("conditions") or [{}])[0]
        world_bbox = condition0.get("world_bbox") or pair.get("world_bbox")
        projection = project_world_bbox(
            pair.get("view", {}).get("camera") or {},
            world_bbox,
            image_width=image_width,
            image_height=image_height,
            min_area_px=min_area_px,
        )
        pair_status = projection["status"]
        if not render_smoke_pass.get(pair_id, False):
            pair_status = "blocked_render_smoke_missing_or_failed"
        pair_record = {
            "pair_id": pair_id,
            "target_id": pair.get("target_id"),
            "source_scene_id": pair.get("source_scene_id"),
            "view_id": (pair.get("view") or {}).get("view_id"),
            "target_prim_path": pair.get("target_prim_path"),
            "render_smoke_pass": render_smoke_pass.get(pair_id),
            "projection": projection,
            "status": pair_status,
        }
        pair_reports.append(pair_record)
        if pair_status == "projection_ok":
            for condition in pair.get("conditions", []):
                scoring_records.append(
                    {
                        "sample_id": condition.get("sample_id"),
                        "pair_id": pair_id,
                        "version": condition.get("material_condition"),
                        "task": _task_id(condition),
                        "image": {
                            "path": condition.get("output_image"),
                            "width": image_width,
                            "height": image_height,
                        },
                        "target": _condition_target(condition, projection),
                        "expected_answers": (condition.get("target") or {}).get("expected_answers"),
                        "prediction": None,
                    }
                )

    counts = Counter(item["status"] for item in pair_reports)
    return {
        "schema_version": 1,
        "status": "target_projection_qa_report",
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/project_target_bboxes.py",
        "summary": {
            "recommended_pair_count": len(pair_ids),
            "projection_ok_pair_count": int(counts.get("projection_ok", 0)),
            "projection_blocked_pair_count": len(pair_reports) - int(counts.get("projection_ok", 0)),
            "scoring_record_count": len(scoring_records),
            "image_width": image_width,
            "image_height": image_height,
            "min_area_px": float(min_area_px),
            "status_counts": dict(sorted(counts.items())),
            "claim_boundary": "projected_bbox_labels_only_requires_visual_or_depth_qa_before_final_vlm_claims",
        },
        "pairs": pair_reports,
        "scoring_records": scoring_records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-manifest", type=Path, default=DEFAULT_RENDER_MANIFEST)
    parser.add_argument("--preflight-report", type=Path, default=DEFAULT_PREFLIGHT_REPORT)
    parser.add_argument("--render-summary", type=Path, default=DEFAULT_RENDER_SUMMARY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-area-px", type=float, default=DEFAULT_MIN_AREA_PX)
    args = parser.parse_args(argv)

    render_manifest = _load_json(args.render_manifest)
    preflight_report = _load_json(args.preflight_report)
    render_summary = _load_json(args.render_summary)
    report = build_projection_report(
        render_manifest,
        preflight_report=preflight_report,
        render_summary=render_summary,
        min_area_px=args.min_area_px,
    )
    report["render_manifest"] = {
        "path": str(args.render_manifest),
        "hash_sha256": _sha256_file(args.render_manifest),
    }
    report["preflight_report"] = {
        "path": str(args.preflight_report),
        "hash_sha256": _sha256_file(args.preflight_report),
    }
    report["render_summary"] = {
        "path": str(args.render_summary),
        "hash_sha256": _sha256_file(args.render_summary),
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
        f"Wrote {args.out} projection_ok={report['summary']['projection_ok_pair_count']} "
        f"records={report['summary']['scoring_record_count']}"
    )
    return 0 if report["summary"]["projection_blocked_pair_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
