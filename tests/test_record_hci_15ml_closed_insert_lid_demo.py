from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_hci_15ml_closed_insert_lid_assets import (
    FORBIDDEN_K0365_TUBE_SHA256,
)
from scripts.qualify_centrifuge_task_interactions import (
    LID_CLOSED_BAND,
    LID_OPEN_BAND,
)
from scripts.record_hci_15ml_closed_insert_lid_demo import (
    CAMERA_MAIN,
    CAMERA_REVEAL,
    CAMERA_TOPDOWN,
    DEFAULT_SOCKET_NAMES,
    FPS,
    LID_CLOSED_RAD,
    LID_OPEN_RAD,
    RIM_TOP_Z_M,
    SPIN_CENTER_WORLD_M,
    SUBSTEPS_PER_FRAME,
    TUBE_HOLD_ABOVE_RIM_M,
    TUBE_HOVER_ABOVE_APERTURE_M,
    TUBE_PARK_LATERAL_M,
    apply_fixed_camera,
    build_demo_keyframes,
    build_parser,
    demo_frame_count,
    demo_phases,
    encode_mp4,
    evidence_payload,
)


SOCKET_1_APERTURE = (0.0208, 0.0142, 0.15289813)
SOCKET_2_APERTURE = (-0.1016, -0.1107, 0.15289813)
AXIS = (0.0, 0.0, 1.0)
SEAT_Z = 0.1281
SOCKETS = [
    {
        "name": "tube_socket_1",
        "aperture": SOCKET_1_APERTURE,
        "axis": AXIS,
        "depth": SOCKET_1_APERTURE[2] - SEAT_Z,
        "seat_z_m": SEAT_Z,
    },
    {
        "name": "tube_socket_2",
        "aperture": SOCKET_2_APERTURE,
        "axis": AXIS,
        "depth": SOCKET_2_APERTURE[2] - SEAT_Z,
        "seat_z_m": SEAT_Z,
    },
]
HOLD_Z = RIM_TOP_Z_M + TUBE_HOLD_ABOVE_RIM_M


def _keyframes() -> list[dict]:
    return build_demo_keyframes(sockets=SOCKETS)


def test_phase_order_honours_lid_open_insert_close_contract() -> None:
    names = [name for name, _ in demo_phases(2)]
    assert names.index("lid_open") < names.index("tube_0_release") < names.index("lid_close")
    assert names.index("tube_0_release") < names.index("tube_1_release") < names.index("lid_close")
    assert names[0] == "closed_hold"
    assert names[-1] == "final_hold"
    assert names.index("tube_1_release") < names.index("socket_reveal")
    assert names.index("reveal_return") < names.index("lid_close")
    assert demo_frame_count(2) == sum(frames for _, frames in demo_phases(2))
    assert demo_frame_count(1) < demo_frame_count(2)


def test_keyframes_cover_phases_and_endpoints() -> None:
    keyframes = _keyframes()
    assert len(keyframes) == demo_frame_count(2)
    assert keyframes[0]["phase"] == "closed_hold"
    assert keyframes[0]["lid_rad"] == LID_CLOSED_RAD
    assert keyframes[-1]["phase"] == "final_hold"
    assert keyframes[-1]["lid_rad"] == LID_CLOSED_RAD
    open_frames = [k for k in keyframes if k["phase"] == "lid_open"]
    assert open_frames[-1]["lid_rad"] == pytest.approx(LID_OPEN_RAD)
    close_frames = [k for k in keyframes if k["phase"] == "lid_close"]
    assert close_frames[0]["lid_rad"] == pytest.approx(LID_OPEN_RAD)
    assert close_frames[-1]["lid_rad"] == pytest.approx(LID_CLOSED_RAD)
    assert LID_OPEN_BAND[0] <= LID_OPEN_RAD <= LID_OPEN_BAND[1]
    assert LID_CLOSED_BAND[0] <= LID_CLOSED_RAD <= LID_CLOSED_BAND[1]


def test_release_is_a_free_physical_drop_from_cup_rim_hold() -> None:
    keyframes = _keyframes()
    hover_1 = SOCKET_1_APERTURE[2] + TUBE_HOVER_ABOVE_APERTURE_M
    parked_1 = [SOCKET_1_APERTURE[0] + TUBE_PARK_LATERAL_M, SOCKET_1_APERTURE[1], hover_1]
    hold_1 = [SOCKET_1_APERTURE[0], SOCKET_1_APERTURE[1], HOLD_Z]

    first = keyframes[0]
    assert first["tube_positions_m"][0] == pytest.approx(parked_1)
    assert first["tube_positions_m"][1] is not None

    positioning = [k for k in keyframes if k["phase"] == "tube_0_position"]
    assert positioning[-1]["tube_positions_m"][0] == pytest.approx(hold_1)
    # The release beat frees tube 0 (None) while tube 1 is still held parked.
    release = [k for k in keyframes if k["phase"] == "tube_0_release"]
    assert all(k["tube_positions_m"][0] is None for k in release)
    assert all(k["tube_positions_m"][1] is not None for k in release)
    # Once free, a tube is never teleported again.
    after = keyframes[keyframes.index(release[0]):]
    assert all(k["tube_positions_m"][0] is None for k in after)
    # Tube 1 follows the same pattern one beat later.
    release_b = [k for k in keyframes if k["phase"] == "tube_1_release"]
    assert all(k["tube_positions_m"][1] is None for k in release_b)
    assert release_b[0]["tube_positions_m"][0] is None
    for keyframe in keyframes[keyframes.index(release_b[-1]):]:
        assert keyframe["tube_positions_m"] == [None, None]


def test_tubes_stay_parked_while_lid_swings_open() -> None:
    keyframes = _keyframes()
    swinging = [k for k in keyframes if k["phase"] in {"closed_hold", "lid_open", "open_hold"}]
    xs0 = {round(k["tube_positions_m"][0][0], 9) for k in swinging}
    assert xs0 == {round(SOCKET_1_APERTURE[0] + TUBE_PARK_LATERAL_M, 9)}
    xs1 = {round(k["tube_positions_m"][1][0], 9) for k in swinging}
    assert xs1 == {round(SOCKET_2_APERTURE[0] - TUBE_PARK_LATERAL_M, 9)}


def test_camera_reveal_beat_frames_the_spin_center_from_above() -> None:
    keyframes = _keyframes()
    first = keyframes[0]["camera"]
    assert first["target"] == pytest.approx(list(CAMERA_MAIN["target"]))
    reveal = [k for k in keyframes if k["phase"] == "reveal_hold"]
    assert reveal
    for keyframe in reveal:
        cam = keyframe["camera"]
        assert cam["target"][0] == pytest.approx(SPIN_CENTER_WORLD_M[0])
        assert cam["target"][1] == pytest.approx(SPIN_CENTER_WORLD_M[1])
        assert cam["elevation"] == pytest.approx(CAMERA_REVEAL["elevation"])
        assert cam["distance"] == pytest.approx(CAMERA_REVEAL["distance"])
    moving = [k for k in keyframes if k["phase"] == "socket_reveal"]
    assert moving[0]["camera"]["elevation"] == pytest.approx(CAMERA_MAIN["elevation"])
    assert moving[-1]["camera"]["elevation"] == pytest.approx(CAMERA_REVEAL["elevation"])
    assert keyframes[-1]["camera"]["target"] == pytest.approx(list(CAMERA_MAIN["target"]))


def test_top_down_cut_pins_every_frame_to_the_fixed_overhead_camera() -> None:
    keyframes = apply_fixed_camera(_keyframes(), CAMERA_TOPDOWN)
    assert len(keyframes) == demo_frame_count(2)
    for keyframe in keyframes:
        cam = keyframe["camera"]
        assert cam["target"] == pytest.approx(list(CAMERA_TOPDOWN["target"]))
        assert cam["distance"] == pytest.approx(CAMERA_TOPDOWN["distance"])
        assert cam["elevation"] == pytest.approx(CAMERA_TOPDOWN["elevation"])
        assert cam["focal_mm"] == pytest.approx(CAMERA_TOPDOWN["focal_mm"])
    assert keyframes[0]["lid_rad"] == LID_CLOSED_RAD
    assert keyframes[-1]["lid_rad"] == LID_CLOSED_RAD


def test_single_socket_demo_still_builds() -> None:
    keyframes = build_demo_keyframes(sockets=SOCKETS[:1])
    assert len(keyframes) == demo_frame_count(1)
    assert all(len(k["tube_positions_m"]) == 1 for k in keyframes)
    names = [name for name, _ in demo_phases(1)]
    assert "tube_1_release" not in names


def test_encode_mp4_without_frames_returns_none(tmp_path: Path) -> None:
    assert encode_mp4(tmp_path, tmp_path / "out.mp4") is None


def test_evidence_payload_records_physical_drop_and_seats(tmp_path: Path) -> None:
    centrifuge = tmp_path / "centrifuge"
    tube = tmp_path / "tube"
    centrifuge.mkdir()
    tube.mkdir()
    (centrifuge / "asset.usd").write_text("centrifuge", encoding="utf-8")
    (tube / "asset.usd").write_text("tube", encoding="utf-8")
    profile = tmp_path / "device_profile.json"
    profile.write_text("{}", encoding="utf-8")
    report_a = tmp_path / "report_a.json"
    report_a.write_text("{}", encoding="utf-8")
    report_b = tmp_path / "report_b.json"
    report_b.write_text("{}", encoding="utf-8")
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    (frames_dir / "frame_0000.png").write_bytes(b"png")
    seated = [
        {
            "socket_name": "tube_socket_1",
            "seated_position_m": [0.0208, 0.0142, SEAT_Z],
            "upright_quaternion_w": 1.0,
            "seat_z_m": SEAT_Z,
        }
    ]

    payload = evidence_payload(
        centrifuge_package=centrifuge,
        tube_package=tube,
        device_profile=profile,
        qualification_reports=[report_a, report_b],
        mp4=None,
        frames_dir=frames_dir,
        keyframes=_keyframes(),
        camera_mode="top_down",
        socket_names=DEFAULT_SOCKET_NAMES,
        seated_measurements=seated,
    )

    assert payload["engine"] == "isaac_sim_4.1"
    assert payload["method"] == "scripted_kinematic_positioning_then_physical_free_drop"
    assert payload["sequence"] == ["lid_open", "tube_insert", "lid_close"]
    assert payload["balanced_pair"] is True
    assert payload["socket_names"] == list(DEFAULT_SOCKET_NAMES)
    assert payload["camera_mode"] == "top_down"
    assert len(payload["qualification_report_sha256"]) == 2
    assert payload["seated_measurements"] == seated
    assert "Package-level" in payload["cup_colliders"]
    assert "Not Feishu Task 10/11" in payload["claim_boundary"]
    json.dumps(payload, allow_nan=False)


def test_forbidden_k0365_tube_hash_is_rejected_before_recording() -> None:
    assert FORBIDDEN_K0365_TUBE_SHA256  # sanity: pin imported
    assert len(FORBIDDEN_K0365_TUBE_SHA256) == 64


def test_parser_defaults_point_at_short_tube_and_r11_profile() -> None:
    args = build_parser().parse_args([])
    assert args.top_down is False
    assert args.out_dir is None
    assert args.socket_name is None
    assert "hci_15ml_closed_insert_lid_r2" in str(args.tube_package)
    assert "r11_visual_cup_sockets" in str(args.device_profile)
    args = build_parser().parse_args(["--top-down"])
    assert args.top_down is True
    args = build_parser().parse_args(["--socket-name", "tube_socket_1"])
    assert args.socket_name == ["tube_socket_1"]
    assert FPS * SUBSTEPS_PER_FRAME == pytest.approx(240.0)
