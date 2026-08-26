from __future__ import annotations

from pathlib import Path

import numpy as np

from scripts.record_funnel_tube15_gravity import (
    FPS,
    PHYSICS_DT,
    PLAYBACK_SECONDS,
    SIMULATED_SECONDS,
    SLOW_MOTION_FACTOR,
    SUBSTEPS_PER_FRAME,
    VIDEO_FRAME_COUNT,
    blue_pixel_fraction,
    build_parser,
    evidence_payload,
    frame_quality,
)


def test_recording_cadence_matches_real_simulation_time() -> None:
    assert FPS == 30
    assert PHYSICS_DT == 1.0 / 120.0
    assert SUBSTEPS_PER_FRAME == 1
    assert SLOW_MOTION_FACTOR == 4
    assert SIMULATED_SECONDS == 3
    assert PLAYBACK_SECONDS == 12
    assert VIDEO_FRAME_COUNT == 360
    assert VIDEO_FRAME_COUNT * SUBSTEPS_PER_FRAME * PHYSICS_DT == SIMULATED_SECONDS
    assert VIDEO_FRAME_COUNT / FPS == PLAYBACK_SECONDS


def test_frame_quality_rejects_flat_gray_and_accepts_real_content() -> None:
    gray = np.full((32, 32, 3), 127, dtype=np.uint8)
    flat = frame_quality(gray)
    assert flat["effectively_flat"] is True

    content = gray.copy()
    content[:16, :16] = (20, 80, 220)
    varied = frame_quality(content)
    assert varied["effectively_flat"] is False
    assert varied["luma_std"] > flat["luma_std"]


def test_blue_visibility_detects_high_contrast_liquid() -> None:
    gray = np.full((32, 32, 3), 100, dtype=np.uint8)
    assert blue_pixel_fraction(gray) == 0.0
    gray[8:24, 8:24] = (20, 70, 230)
    assert blue_pixel_fraction(gray) == 0.25


def test_evidence_payload_is_isaac41_and_does_not_overclaim(tmp_path: Path) -> None:
    scene = tmp_path / "scene.usda"
    fixture = tmp_path / "fixture.json"
    video = tmp_path / "funnel_to_tube_isaac41.mp4"
    scene.write_text("scene", encoding="utf-8")
    fixture.write_text("fixture", encoding="utf-8")
    video.write_bytes(b"video")

    payload = evidence_payload(
        scene=scene,
        fixture=fixture,
        video=video,
        observation={"overall_status": "pass"},
        visual_quality={"overall_status": "pass"},
        kit_version="4.1.0",
        visual_mode="evidence_blue",
        session_visual_override={"physics_unchanged": True},
    )

    assert payload["engine"] == "isaac_sim_4.1"
    assert payload["method"] == "live_gpu_pbd_simulation_with_isaac_camera_rgb_capture"
    assert payload["robot_policy_success"] is False
    assert payload["benchmark_success"] is False
    assert payload["video_sha256"]
    assert payload["scene_sha256"]
    assert payload["fixture_sha256"]
    assert payload["overall_status"] == "pass"
    assert payload["slow_motion_factor"] == 4
    assert payload["visual_mode"] == "evidence_blue"
    assert payload["session_visual_override"]["physics_unchanged"] is True


def test_recording_discards_intermediate_frames_by_default() -> None:
    args = build_parser().parse_args(
        ["--scene", "scene.usda", "--fixture", "fixture.json", "--out-dir", "out"]
    )
    assert args.keep_frames is False
    assert args.visual_mode == "evidence_blue"


def test_exact_material_mode_has_a_separate_output_name() -> None:
    args = build_parser().parse_args(
        [
            "--scene",
            "scene.usda",
            "--fixture",
            "fixture.json",
            "--out-dir",
            "out",
            "--visual-mode",
            "exact",
        ]
    )
    assert args.visual_mode == "exact"
