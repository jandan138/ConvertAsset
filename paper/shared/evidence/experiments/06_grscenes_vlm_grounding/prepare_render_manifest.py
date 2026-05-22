#!/usr/bin/env python3
"""Prepare paired render plans for the GRScenes VLM grounding pilot.

This script is intentionally pure Python. It does not open USD stages, run
Isaac Sim, render images, or mutate source/scratch datasets. It turns resolved
target prims and world bboxes into deterministic original/no-MDL render jobs.
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
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_INPUT = (
    PROJECT_ROOT
    / "paper"
    / "shared"
    / "evidence"
    / "raw"
    / "grscene_vlm_grounding"
    / "target_manifest.json"
)
DEFAULT_OUTPUT = DEFAULT_INPUT.with_name("render_manifest.json")
DEFAULT_RENDER_ROOT = DEFAULT_INPUT.parent / "renders"
DEFAULT_VIEW_AZIMUTHS = (30.0, 120.0, 210.0, 300.0)
DEFAULT_ELEVATION_DEG = 25.0
DEFAULT_RADIUS_SCALE = 2.4
DEFAULT_MIN_DISTANCE = 1.25
DEFAULT_CAMERA_PRIM_PATH = "/World/GRScenesVLMTargetCamera"
DEFAULT_FOCAL_LENGTH_MM = 9.0
DEFAULT_HORIZONTAL_APERTURE_MM = 20.955
DEFAULT_WIDTH = 600
DEFAULT_HEIGHT = 450
DEFAULT_RENDERER = "RayTracedLighting"
DEFAULT_WAIT_FRAMES = 8


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _hash_json(value: Any, *, length: int = 16) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)[:length]


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


def _parse_azimuths(value: str) -> list[float]:
    out = []
    for item in value.split(","):
        token = item.strip()
        if not token:
            continue
        out.append(float(token))
    if not out:
        raise ValueError("at least one azimuth is required")
    return out


def _safe_token(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value).strip("_") or "item"


def _scene_lookup(target_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(scene["source_scene_id"]): scene for scene in target_manifest.get("scenes", [])}


def _nomdl_scene_overrides(nomdl_run_report: dict[str, Any] | None) -> dict[tuple[str, str, str], dict[str, str]]:
    if nomdl_run_report is None:
        return {}
    if nomdl_run_report.get("status") != "completed_full_grscenes_nomdl_multi_root_run":
        raise ValueError("no-MDL run report must be a completed apply report")
    if nomdl_run_report.get("dry_run") is not False:
        raise ValueError("no-MDL run report must be non-dry-run evidence")
    results_by_id = {
        str(result.get("conversion_job_id")): result
        for result in nomdl_run_report.get("results", [])
    }
    overrides: dict[tuple[str, str, str], dict[str, str]] = {}
    for job in nomdl_run_report.get("jobs", []):
        job_id = str(job.get("conversion_job_id"))
        result = results_by_id.get(job_id)
        if result is None:
            continue
        scratch_input = Path(str(result.get("scratch_input_usd") or job.get("scratch_input_usd")))
        converted_usd = Path(str(result.get("top_output_usd") or job.get("expected_top_output_usd")))
        key = (
            str(job.get("source_scene_split")),
            str(job.get("source_scene_id")),
            str(job.get("source_usd_variant") or Path(str(job.get("scratch_input_usd", ""))).name),
        )
        overrides[key] = {
            "scratch_scene_root": str(scratch_input.parent),
            "scratch_input_usd": str(scratch_input),
            "converted_usd": str(converted_usd),
            "conversion_command": "full_no_mdl_multi_root_apply",
            "conversion_report": str(DEFAULT_INPUT.with_name("full_nomdl_multi_root_run_report.json")),
        }
    return overrides


def _scene_lookup_with_nomdl_overrides(
    target_manifest: dict[str, Any],
    *,
    nomdl_run_report: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    overrides = _nomdl_scene_overrides(nomdl_run_report)
    scenes = {}
    for scene in target_manifest.get("scenes", []):
        scene_copy = dict(scene)
        key = (
            str(scene_copy.get("source_scene_split")),
            str(scene_copy.get("source_scene_id")),
            str(scene_copy.get("source_usd_variant", "start_result_raw.usd")),
        )
        if key in overrides:
            scene_copy.update(overrides[key])
        scenes[str(scene_copy["source_scene_id"])] = scene_copy
    return scenes


def _resolved_records(target_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        record
        for record in target_manifest.get("episode_records", [])
        if str(record.get("mapping_status", "")).startswith("resolved_")
        and record.get("target_prim_path")
        and record.get("world_bbox")
    ]


def _target_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(record.get("source_scene_id")),
        str(record.get("object_instance_id")),
        str(record.get("target_prim_path")),
    )


def _group_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(_target_key(record), []).append(record)

    targets = []
    for key, items in grouped.items():
        items = sorted(items, key=lambda item: str(item.get("stable_episode_id", "")))
        _validate_duplicate_target_metadata(items)
        first = items[0]
        target_id = _hash_json({"key": key, "bbox": first.get("world_bbox")}, length=20)
        targets.append(
            {
                "target_id": target_id,
                "source_scene_id": key[0],
                "object_instance_id": key[1],
                "target_prim_path": key[2],
                "target_category": first.get("object_category"),
                "world_bbox": first.get("world_bbox"),
                "bbox_method": first.get("bbox_method"),
                "resolved_model_path": first.get("resolved_model_path"),
                "reference_asset_path": first.get("reference_asset_path"),
                "mapping_status": first.get("mapping_status"),
                "mapping_confidence": first.get("mapping_confidence"),
                "linked_episode_ids": [str(item.get("stable_episode_id")) for item in items],
                "linked_episode_count": len(items),
                "linked_episodes": [
                    {
                        "stable_episode_id": item.get("stable_episode_id"),
                        "episode_family": item.get("episode_family"),
                        "episode_file": item.get("episode_file"),
                        "instruction": item.get("instruction"),
                        "prompt": item.get("prompt"),
                    }
                    for item in items
                ],
                "paper_claim_eligible": all(bool(item.get("paper_claim_eligible")) for item in items),
            }
        )
    return sorted(targets, key=lambda item: (item["source_scene_id"], item["object_instance_id"], item["target_prim_path"]))


def _bbox_signature(world_bbox: dict[str, Any]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    center = tuple(round(float(value), 6) for value in world_bbox.get("center", []))
    size = tuple(round(float(value), 6) for value in world_bbox.get("size", []))
    return center, size


def _validate_duplicate_target_metadata(items: list[dict[str, Any]]) -> None:
    if len(items) <= 1:
        return
    first = items[0]
    first_signature = _bbox_signature(first.get("world_bbox") or {})
    first_category = first.get("object_category")
    for item in items[1:]:
        if item.get("object_category") != first_category:
            raise ValueError("inconsistent duplicate target metadata: object_category differs")
        if _bbox_signature(item.get("world_bbox") or {}) != first_signature:
            raise ValueError("inconsistent duplicate target metadata: world_bbox differs")
        if item.get("bbox_method") != first.get("bbox_method"):
            raise ValueError("inconsistent duplicate target metadata: bbox_method differs")
        if item.get("resolved_model_path") != first.get("resolved_model_path"):
            raise ValueError("inconsistent duplicate target metadata: resolved_model_path differs")


def _bbox_center_size(world_bbox: dict[str, Any]) -> tuple[list[float], list[float], float]:
    center = [float(value) for value in world_bbox.get("center", [])]
    size = [float(value) for value in world_bbox.get("size", [])]
    if len(center) != 3 or len(size) != 3:
        raise ValueError("world_bbox must include 3D center and size")
    if not all(math.isfinite(value) for value in center + size):
        raise ValueError("world_bbox center/size must be finite")
    diagonal = float(world_bbox.get("diagonal") or math.sqrt(sum(value * value for value in size)))
    if not math.isfinite(diagonal) or diagonal <= 0:
        raise ValueError("world_bbox diagonal must be positive")
    return center, size, diagonal


def _camera_for_view(
    world_bbox: dict[str, Any],
    *,
    view_id: str,
    azimuth_deg: float,
    elevation_deg: float,
    image_width: int,
    image_height: int,
    radius_scale: float,
    min_distance: float,
    focal_length_mm: float,
    camera_prim_path: str,
) -> dict[str, Any]:
    center, size, diagonal = _bbox_center_size(world_bbox)
    distance = max(float(min_distance), diagonal * float(radius_scale), max(size) * 1.5)
    azimuth = math.radians(float(azimuth_deg))
    elevation = math.radians(float(elevation_deg))
    horizontal = distance * math.cos(elevation)
    position = [
        center[0] + horizontal * math.cos(azimuth),
        center[1] + horizontal * math.sin(azimuth),
        center[2] + distance * math.sin(elevation),
    ]
    near_clip = max(0.01, distance - diagonal * 2.0)
    far_clip = max(distance + diagonal * 3.0, 100.0)
    aspect = float(image_width) / float(max(1, image_height))
    focal_length_mm = float(focal_length_mm)
    if not math.isfinite(focal_length_mm) or focal_length_mm <= 0.0:
        raise ValueError("focal_length_mm must be positive and finite")
    horizontal_aperture_mm = DEFAULT_HORIZONTAL_APERTURE_MM
    vertical_aperture_mm = horizontal_aperture_mm / aspect
    fov_h_deg = math.degrees(2.0 * math.atan(horizontal_aperture_mm / (2.0 * focal_length_mm)))
    return {
        "view_id": view_id,
        "mode": "target_centered_static_orbit_plan",
        "camera_prim_path": camera_prim_path,
        "position_world": [round(value, 6) for value in position],
        "target_world": [round(value, 6) for value in center],
        "look_at": [round(value, 6) for value in center],
        "up_world": [0.0, 0.0, 1.0],
        "azimuth_deg": float(azimuth_deg),
        "elevation_deg": float(elevation_deg),
        "distance": round(distance, 6),
        "bbox_center": [round(value, 6) for value in center],
        "bbox_size_xyz": [round(float(value), 6) for value in size],
        "focal_length_mm": focal_length_mm,
        "horizontal_aperture_mm": horizontal_aperture_mm,
        "vertical_aperture_mm": round(vertical_aperture_mm, 6),
        "fov_h_deg": round(fov_h_deg, 6),
        "aspect": round(aspect, 6),
        "clipping_range": [round(near_clip, 6), round(far_clip, 6)],
        "start_frame": 0,
        "end_frame": 0,
        "time_codes_per_second": 24,
        "projection_matrix": None,
        "view_matrix": None,
    }


def _hash_if_exists(path: Path) -> str | None:
    return _sha256_file(path) if path.exists() and path.is_file() else None


def _condition_record(
    *,
    pair_id: str,
    target: dict[str, Any],
    scene: dict[str, Any],
    view: dict[str, Any],
    condition: str,
    paired_condition: str,
    render_root: Path,
    image_width: int,
    image_height: int,
    renderer: str,
    wait_frames: int,
) -> dict[str, Any]:
    source_usd = Path(scene["source_usd"])
    scratch_input_usd = Path(str(scene.get("scratch_input_usd") or scene.get("source_usd")))
    converted_usd = Path(scene["converted_usd"])
    usd_path = scratch_input_usd if condition == "original" else converted_usd
    target_dir = render_root / _safe_token(str(scene["source_scene_id"])) / target["target_id"] / view["view_id"]
    condition_dir = target_dir / condition
    output_image = condition_dir / f"{condition}_0000.png"
    camera_stage_path = condition_dir / f"{condition}_camera.usd"
    input_exists = usd_path.exists()
    camera_stage_exists = camera_stage_path.exists()
    if not input_exists:
        render_status = "blocked_missing_material_input"
    elif not camera_stage_exists:
        render_status = "planned_camera_stage_pending"
    else:
        render_status = "planned_input_ready"
    sample_id = f"{pair_id}.{condition}"
    output_dir = str(output_image.parent)
    render_command = [
        "./scripts/isaac_python.sh",
        "scripts/render_with_viewport_capture.py",
        "--usd-path",
        str(camera_stage_path),
        "--camera",
        str(view["camera"]["camera_prim_path"]),
        "--output-dir",
        output_dir,
        "--prefix",
        condition,
        "--ext",
        "png",
        "--width",
        str(image_width),
        "--height",
        str(image_height),
        "--start-frame",
        "0",
        "--end-frame",
        "0",
        "--frame-step",
        "1",
        "--renderer",
        renderer,
        "--wait-frames",
        str(wait_frames),
        "--headless",
    ]
    return {
        "sample_id": sample_id,
        "pair_id": pair_id,
        "target_id": target["target_id"],
        "source_scene_id": scene.get("source_scene_id"),
        "source_scene_split": scene.get("source_scene_split"),
        "dataset_role": scene.get("dataset_role"),
        "source_dataset_root": scene.get("source_dataset_root"),
        "source_usd": scene.get("source_usd"),
        "source_usd_hash_sha256": _hash_if_exists(source_usd),
        "scratch_scene_root": scene.get("scratch_scene_root"),
        "scratch_input_usd": str(scratch_input_usd),
        "scratch_input_usd_hash_sha256": _hash_if_exists(scratch_input_usd),
        "converted_usd": scene.get("converted_usd"),
        "converted_usd_hash_sha256": _hash_if_exists(converted_usd),
        "usd_path": str(usd_path),
        "input_exists": input_exists,
        "camera_stage_exists": camera_stage_exists,
        "camera_stage_status": "ready" if camera_stage_exists else "pending_authoring",
        "material_condition": condition,
        "paired_material_condition": paired_condition,
        "target_prim_path": target.get("target_prim_path"),
        "object_instance_id": target.get("object_instance_id"),
        "object_category": target.get("target_category"),
        "world_bbox": target.get("world_bbox"),
        "bbox_method": target.get("bbox_method"),
        "linked_episode_ids": target.get("linked_episode_ids", []),
        "linked_episode_count": target.get("linked_episode_count", 0),
        "camera": view["camera"],
        "camera_stage_path": str(camera_stage_path),
        "image": {
            "path": str(output_image),
            "hash_sha256": None,
            "width": image_width,
            "height": image_height,
            "format": "png",
        },
        "output_image": str(output_image),
        "target": {
            "bbox_xyxy": None,
            "bbox_source": "pending_projection_from_world_bbox",
            "category": target.get("target_category"),
            "expected_answers": [target.get("target_category")] if target.get("target_category") else [],
        },
        "task": "s1_referred_object_localization",
        "prompt_text": _prompt_text(target),
        "source_episode_instructions": _source_episode_instructions(target),
        "source_episode_prompts": _source_episode_prompts(target),
        "prompt_template_id": "grscenes_target_category_pointing_v1",
        "vlm_input_preprocessing": {
            "resize": [image_width, image_height],
            "coordinate_space": "image_pixels_xy",
        },
        "conversion_command": scene.get("conversion_command"),
        "conversion_log": None,
        "render_command": render_command,
        "render_log": None,
        "render_status": render_status,
        "visual_review": {
            "review_group_id": pair_id,
            "blind_pair_key": _hash_json({"pair_id": pair_id}, length=12),
            "expected_target_visible": True,
            "review_image_role": "candidate",
            "recommended_skill": "render-visual-reviewer",
        },
    }


def _prompt_text(target: dict[str, Any]) -> str:
    category = target.get("target_category") or "target object"
    return f"Point to the {category}."


def _source_episode_instructions(target: dict[str, Any]) -> list[str]:
    linked = target.get("linked_episodes") or []
    return [str(item["instruction"]) for item in linked if item.get("instruction")]


def _source_episode_prompts(target: dict[str, Any]) -> list[str]:
    linked = target.get("linked_episodes") or []
    return [str(item["prompt"]) for item in linked if item.get("prompt")]


def _render_pair(
    *,
    target: dict[str, Any],
    scene: dict[str, Any],
    view: dict[str, Any],
    render_root: Path,
    image_width: int,
    image_height: int,
    renderer: str,
    wait_frames: int,
) -> dict[str, Any]:
    pair_id = f"{target['target_id']}.{view['view_id']}"
    original = _condition_record(
        pair_id=pair_id,
        target=target,
        scene=scene,
        view=view,
        condition="original",
        paired_condition="converted",
        render_root=render_root,
        image_width=image_width,
        image_height=image_height,
        renderer=renderer,
        wait_frames=wait_frames,
    )
    converted = _condition_record(
        pair_id=pair_id,
        target=target,
        scene=scene,
        view=view,
        condition="converted",
        paired_condition="original",
        render_root=render_root,
        image_width=image_width,
        image_height=image_height,
        renderer=renderer,
        wait_frames=wait_frames,
    )
    return {
        "pair_id": pair_id,
        "target_id": target["target_id"],
        "source_scene_id": target["source_scene_id"],
        "target_prim_path": target["target_prim_path"],
        "linked_episode_ids": target["linked_episode_ids"],
        "view": view,
        "conditions": [original, converted],
        "pair_fairness": {
            "shared_camera": True,
            "shared_resolution": True,
            "shared_renderer_settings": True,
            "material_condition_only_intended_difference": True,
        },
    }


def build_render_manifest(
    target_manifest: dict[str, Any],
    *,
    render_root: Path,
    nomdl_run_report: dict[str, Any] | None = None,
    view_azimuths: list[float] | tuple[float, ...] = DEFAULT_VIEW_AZIMUTHS,
    view_id_prefix: str = "view",
    view_index_offset: int = 0,
    elevation_deg: float = DEFAULT_ELEVATION_DEG,
    image_width: int = DEFAULT_WIDTH,
    image_height: int = DEFAULT_HEIGHT,
    radius_scale: float = DEFAULT_RADIUS_SCALE,
    min_distance: float = DEFAULT_MIN_DISTANCE,
    focal_length_mm: float = DEFAULT_FOCAL_LENGTH_MM,
    renderer: str = DEFAULT_RENDERER,
    wait_frames: int = DEFAULT_WAIT_FRAMES,
    camera_prim_path: str = DEFAULT_CAMERA_PRIM_PATH,
    require_converted: bool = False,
) -> dict[str, Any]:
    scenes = _scene_lookup_with_nomdl_overrides(
        target_manifest,
        nomdl_run_report=nomdl_run_report,
    )
    resolved_records = _resolved_records(target_manifest)
    render_targets = _group_records(resolved_records)
    render_root = render_root.resolve()

    render_pairs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    missing_converted: list[str] = []

    for target in render_targets:
        scene = scenes.get(str(target["source_scene_id"]))
        if scene is None:
            raise KeyError(f"scene entry missing for {target['source_scene_id']}")
        for idx, azimuth in enumerate(view_azimuths):
            view_id = f"{_safe_token(str(view_id_prefix))}_{int(view_index_offset) + idx:03d}"
            camera = _camera_for_view(
                target["world_bbox"],
                view_id=view_id,
                azimuth_deg=float(azimuth),
                elevation_deg=float(elevation_deg),
                image_width=int(image_width),
                image_height=int(image_height),
                radius_scale=float(radius_scale),
                min_distance=float(min_distance),
                focal_length_mm=float(focal_length_mm),
                camera_prim_path=camera_prim_path,
            )
            view = {
                "view_id": view_id,
                "azimuth_deg": float(azimuth),
                "elevation_deg": float(elevation_deg),
                "camera": camera,
            }
            pair = _render_pair(
                target=target,
                scene=scene,
                view=view,
                render_root=render_root,
                image_width=int(image_width),
                image_height=int(image_height),
                renderer=renderer,
                wait_frames=int(wait_frames),
            )
            render_pairs.append(pair)
            records.extend(pair["conditions"])
            for condition_record in pair["conditions"]:
                if condition_record["material_condition"] == "converted" and not condition_record["input_exists"]:
                    missing_converted.append(str(condition_record["usd_path"]))

    if require_converted and missing_converted:
        raise FileNotFoundError(f"converted USD is missing for {len(missing_converted)} render jobs")

    missing_jobs = [record for record in records if not record["input_exists"]]
    missing_camera_stage_jobs = [record for record in records if not record["camera_stage_exists"]]
    ready_to_run_jobs = [
        record
        for record in records
        if record["input_exists"] and record["camera_stage_exists"]
    ]
    return {
        "schema_version": 1,
        "status": "planned_render_manifest",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py",
        "generator_git_commit": _git_commit(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dataset_roles": target_manifest.get("dataset_roles", {}),
        "selection": target_manifest.get("selection", {}),
        "paper_claim_gate": target_manifest.get("paper_claim_gate", {}),
        "target_resolution_summary": target_manifest.get("resolution_summary", {}),
        "render_summary": {
            "episode_records_input": len(resolved_records),
            "unique_render_targets": len(render_targets),
            "duplicate_episode_records_collapsed": len(resolved_records) - len(render_targets),
            "views_per_target": len(view_azimuths),
            "view_id_prefix": _safe_token(str(view_id_prefix)),
            "view_index_offset": int(view_index_offset),
            "render_pairs": len(render_pairs),
            "render_jobs": len(records),
            "material_conditions": ["original", "converted"],
            "render_jobs_missing_input_count": len(missing_jobs),
            "render_jobs_missing_material_input_count": len(missing_jobs),
            "converted_jobs_missing_input_count": len(missing_converted),
            "material_input_ready_jobs": len(records) - len(missing_jobs),
            "camera_stage_missing_count": len(missing_camera_stage_jobs),
            "render_jobs_ready_to_run": len(ready_to_run_jobs),
            "image_space_bbox_status": "pending_projection_after_render",
        },
        "renderer_settings": {
            "image_width": int(image_width),
            "image_height": int(image_height),
            "image_format": "png",
            "renderer": renderer,
            "headless": True,
            "wait_frames": int(wait_frames),
            "render_steps": int(wait_frames),
            "camera_policy": "target_centered_static_orbit_plan",
            "view_azimuths_deg": [float(value) for value in view_azimuths],
            "elevation_deg": float(elevation_deg),
            "radius_scale": float(radius_scale),
            "min_distance": float(min_distance),
            "focal_length_mm": float(focal_length_mm),
            "camera_prim_path": camera_prim_path,
        },
        "render_root": str(render_root),
        "render_targets": render_targets,
        "render_pairs": render_pairs,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-manifest", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--nomdl-run-report", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--render-root", type=Path, default=DEFAULT_RENDER_ROOT)
    parser.add_argument("--view-azimuths", default=",".join(str(v) for v in DEFAULT_VIEW_AZIMUTHS))
    parser.add_argument("--view-id-prefix", default="view")
    parser.add_argument("--view-index-offset", type=int, default=0)
    parser.add_argument("--elevation-deg", type=float, default=DEFAULT_ELEVATION_DEG)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--radius-scale", type=float, default=DEFAULT_RADIUS_SCALE)
    parser.add_argument("--min-distance", type=float, default=DEFAULT_MIN_DISTANCE)
    parser.add_argument("--focal-length-mm", type=float, default=DEFAULT_FOCAL_LENGTH_MM)
    parser.add_argument("--renderer", default=DEFAULT_RENDERER)
    parser.add_argument("--wait-frames", type=int, default=DEFAULT_WAIT_FRAMES)
    parser.add_argument("--camera-prim-path", default=DEFAULT_CAMERA_PRIM_PATH)
    parser.add_argument("--require-converted", action="store_true")
    args = parser.parse_args()

    target_manifest = _load_json(args.target_manifest)
    nomdl_run_report = _load_json(args.nomdl_run_report) if args.nomdl_run_report else None
    try:
        result = build_render_manifest(
            target_manifest,
            render_root=args.render_root,
            nomdl_run_report=nomdl_run_report,
            view_azimuths=_parse_azimuths(args.view_azimuths),
            view_id_prefix=args.view_id_prefix,
            view_index_offset=args.view_index_offset,
            elevation_deg=args.elevation_deg,
            image_width=args.width,
            image_height=args.height,
            radius_scale=args.radius_scale,
            min_distance=args.min_distance,
            focal_length_mm=args.focal_length_mm,
            renderer=args.renderer,
            wait_frames=args.wait_frames,
            camera_prim_path=args.camera_prim_path,
            require_converted=args.require_converted,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2
    result["target_manifest"] = {
        "path": str(args.target_manifest),
        "hash_sha256": _sha256_file(args.target_manifest),
    }
    if args.nomdl_run_report:
        result["nomdl_run_report"] = {
            "path": str(args.nomdl_run_report),
            "hash_sha256": _sha256_file(args.nomdl_run_report),
        }
    source_manifest = target_manifest.get("source_manifest")
    if isinstance(source_manifest, dict) and source_manifest.get("path"):
        source_path = Path(str(source_manifest["path"]))
        result["source_manifest"] = {
            "path": str(source_path),
            "hash_sha256": _sha256_file(source_path) if source_path.exists() else source_manifest.get("hash_sha256"),
        }
    else:
        result["source_manifest"] = None
    result["generator_provenance"] = {
        "command": [sys.executable, *sys.argv],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_status_porcelain": _git_status_porcelain(),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} with {result['render_summary']['unique_render_targets']} targets, "
        f"{result['render_summary']['render_pairs']} pairs, "
        f"{result['render_summary']['render_jobs']} jobs"
    )
    if args.require_converted and result["render_summary"]["converted_jobs_missing_input_count"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
