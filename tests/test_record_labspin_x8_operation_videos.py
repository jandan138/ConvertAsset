from __future__ import annotations

from pathlib import Path

import pytest

from scripts.record_labspin_x8_operation_videos import (
    FPS,
    build_insert_keyframes,
    evidence_payload,
)


def test_insert_keyframes_cover_open_insert_release_and_close() -> None:
    frames = build_insert_keyframes(
        aperture=(0.078, 0.005, 0.301),
        bottom=(0.120, 0.005, 0.212),
        axis_out=(-0.42, 0.0, 0.91),
    )
    phases = [frame["phase"] for frame in frames]
    assert phases[0] == "closed_hold"
    assert "lid_open" in phases
    assert "tube_position" in phases
    assert "tube_release" in phases
    assert "lid_close" in phases
    assert phases[-1] == "final_hold"
    assert frames[0]["lid_rad"] == 0.0
    assert frames[-1]["lid_rad"] == 0.0
    assert any(frame["tube_position_m"] is None for frame in frames)
    assert len(frames) / FPS >= 6.0


def test_evidence_does_not_overclaim_robot_or_high_speed(tmp_path: Path) -> None:
    mp4 = tmp_path / "demo.mp4"
    mp4.write_bytes(b"video")
    payload = evidence_payload(
        mode="scripted_insert",
        tube_label="native",
        mp4=mp4,
        centrifuge_asset_sha="a" * 64,
        tube_asset_sha="b" * 64,
        observations={"status": "pass"},
    )
    assert payload["engine"] == "isaac_sim_4.1"
    assert payload["robot_policy_success"] is False
    assert payload["rated_high_speed_spin"] is False
    assert payload["observations"]["status"] == "pass"
    assert payload["mp4_sha256"]
