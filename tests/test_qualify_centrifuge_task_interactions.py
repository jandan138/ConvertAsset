from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from scripts.qualify_centrifuge_task_interactions import (
    FIVE_INTERACTION_GATES,
    _all_values_within,
    _arc_positions,
    _json_value,
    _lid_pusher_centers,
    _load_device_profile,
    _observed_state_values,
    _orientation_wxyz_for_z_axis,
    _qualified_package_identity,
    _runtime_report_inputs,
    _write_report,
)


def _frame(parent_prim: str) -> dict[str, object]:
    return {
        "parent_prim": parent_prim,
        "translation_parent_local_m": [0.0, 0.0, 0.1],
        "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
        "authoritative": True,
    }


def _r9_profile(source_sha256: str) -> dict[str, object]:
    return {
        "schema_version": "aan.articulated_device_profile.v1",
        "profile_id": "hci955350.centrifuge.identity-root.r9",
        "revision": "r5-identity-root-benchtop",
        "source_sha256": source_sha256,
        "asset_entry_prim": "/World/Centrifuge",
        "articulation_root_prim": "/World/Centrifuge",
        "required_runtime_task_gates": [
            *FIVE_INTERACTION_GATES,
            "benchtop_stability",
        ],
        "named_frames": {
            "tube_socket_0_aperture": _frame(
                "/World/Centrifuge/group_6"
            ),
            "tube_socket_0_inserted_bottom_parked_root": _frame(
                "/World/Centrifuge"
            ),
            "lid_close_contact": _frame("/World/Centrifuge/group_23"),
            "start_button_press": _frame("/World/Centrifuge/group_2"),
            "support": {
                **_frame("/World/Centrifuge"),
                "translation_parent_local_m": [0.0, 0.0, 0.0],
            },
        },
    }


def test_observed_state_values_retains_a_pressed_sample_after_overshoot() -> None:
    records = [
        {"button_runtime_position_m": 0.0},
        {"button_runtime_position_m": -0.0048},
        {"button_runtime_position_m": -0.034663904},
    ]

    assert _observed_state_values(
        records,
        "button_runtime_position_m",
        (-0.0055, -0.0045),
    ) == [-0.0048]


def test_lid_travel_check_rejects_an_out_of_limit_reverse_probe() -> None:
    assert _all_values_within([-1.5556, -0.0798], (-1.5557, 0.0))
    assert not _all_values_within([-3.8563, -1.5556], (-1.5557, 0.0))


def test_arc_positions_follow_the_joint_axis() -> None:
    positions = _arc_positions(
        center=np.asarray([0.0, 0.0, 0.0]),
        start_offset=np.asarray([1.0, 2.0, 0.0]),
        axis=np.asarray([0.0, 1.0, 0.0]),
        sweep_rad=math.pi / 2.0,
        increment_rad=math.pi / 4.0,
        np=np,
    )

    assert len(positions) == 3
    assert positions[0] == pytest.approx([1.0, 2.0, 0.0])
    assert positions[-1] == pytest.approx([0.0, 2.0, -1.0])


def test_orientation_for_z_axis_rotates_the_pusher_face_normal() -> None:
    orientation = _orientation_wxyz_for_z_axis(np.asarray([1.0, 0.0, 0.0]), np)
    w, x, y, z = orientation
    quaternion_vector = np.asarray([x, y, z])
    local_z = np.asarray([0.0, 0.0, 1.0])
    twice_cross = 2.0 * np.cross(quaternion_vector, local_z)
    rotated_z = (
        local_z
        + w * twice_cross
        + np.cross(quaternion_vector, twice_cross)
    )

    assert rotated_z == pytest.approx([1.0, 0.0, 0.0])


def test_lid_pusher_centers_keep_the_thin_face_on_the_contact_arc() -> None:
    contact_positions = [np.asarray([1.0, 0.0, 0.0])]
    centers, face_normals = _lid_pusher_centers(
        contact_positions,
        pivot=np.zeros(3),
        axis=np.asarray([0.0, 1.0, 0.0]),
        direction_sign=1.0,
        pusher_half_depth_m=0.02,
        clearance_m=0.001,
        np=np,
    )

    assert face_normals[0] == pytest.approx([0.0, 0.0, -1.0])
    assert centers[0] + face_normals[0] * 0.021 == pytest.approx(
        contact_positions[0]
    )


def test_runtime_report_replaces_nonfinite_drive_values_with_json(
    tmp_path: Path,
) -> None:
    report_path = _write_report(
        tmp_path,
        {"drive_value": _json_value(float("inf"))},
    )

    assert json.loads(report_path.read_text(encoding="utf-8")) == {
        "drive_value": "unbounded"
    }


def test_runtime_report_recursively_replaces_nonfinite_contact_values(
    tmp_path: Path,
) -> None:
    report_path = _write_report(
        tmp_path,
        {"contact": {"force_n": [float("-inf"), 1.0]}},
    )

    assert json.loads(report_path.read_text(encoding="utf-8")) == {
        "contact": {"force_n": ["unbounded", 1.0]}
    }


def test_qualified_package_identity_is_portable_and_hash_bound() -> None:
    identity = _qualified_package_identity(
        asset_entry_prim="/World/Centrifuge",
        runtime_profile="isaac41",
        prequalification_manifest_sha256="a" * 64,
        asset_sha256_before="b" * 64,
        asset_sha256_after="b" * 64,
    )

    assert identity == {
        "asset_path": "asset.usd",
        "asset_entry_prim": "/World/Centrifuge",
        "runtime_profile": "isaac41",
        "prequalification_manifest_sha256": "a" * 64,
        "asset_usd_sha256_before": "b" * 64,
        "asset_usd_sha256_after": "b" * 64,
    }


def test_r9_profile_accepts_support_and_requires_five_real_interaction_gates(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / "device_profile.json"
    profile_path.write_text(
        json.dumps(_r9_profile("a" * 64)),
        encoding="utf-8",
    )

    profile = _load_device_profile(
        profile_path,
        source_sha256="a" * 64,
        articulation_root_prim="/World/Centrifuge",
    )

    assert profile["named_frames"]["support"]["authoritative"] is True
    assert set(FIVE_INTERACTION_GATES).issubset(
        profile["required_runtime_task_gates"]
    )


def test_device_profile_still_requires_all_measured_interaction_frames(
    tmp_path: Path,
) -> None:
    profile = _r9_profile("a" * 64)
    del profile["named_frames"]["start_button_press"]
    profile_path = tmp_path / "device_profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(ValueError, match="start_button_press"):
        _load_device_profile(
            profile_path,
            source_sha256="a" * 64,
            articulation_root_prim="/World/Centrifuge",
        )


def test_device_profile_rejects_missing_five_gate_contract(tmp_path: Path) -> None:
    profile = _r9_profile("a" * 64)
    profile["required_runtime_task_gates"].remove("lid_contact_cycle")
    profile_path = tmp_path / "device_profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(ValueError, match="lid_contact_cycle"):
        _load_device_profile(
            profile_path,
            source_sha256="a" * 64,
            articulation_root_prim="/World/Centrifuge",
        )


def test_base_report_inputs_bind_exact_r9_profile_source_and_manifest() -> None:
    profile = _r9_profile("1" * 64)
    hashes = {
        "centrifuge_manifest_sha256": "2" * 64,
        "centrifuge_asset_usd_sha256_before": "3" * 64,
        "centrifuge_asset_usd_sha256_after": "3" * 64,
        "tube_manifest_sha256": "4" * 64,
        "tube_asset_usd_sha256_before": "5" * 64,
        "tube_asset_usd_sha256_after": "5" * 64,
    }

    inputs = _runtime_report_inputs(
        centrifuge_package=Path("/producer/r9/package"),
        tube_package=Path("/producer/tube/package"),
        profile=profile,
        profile_sha256="6" * 64,
        input_hashes=hashes,
    )

    assert inputs["device_profile"] == {
        "schema_version": "aan.articulated_device_profile.v1",
        "profile_sha256": "6" * 64,
        "source_sha256": "1" * 64,
    }
    assert inputs["qualified_package"][
        "prequalification_manifest_sha256"
    ] == "2" * 64
    assert inputs["qualified_package"]["asset_usd_sha256_before"] == "3" * 64
    assert inputs["qualified_package"]["asset_usd_sha256_after"] == "3" * 64
    assert inputs["integrity"]["status"] == "pass"


def test_base_report_inputs_reject_asset_mutation() -> None:
    profile = _r9_profile("1" * 64)
    hashes = {
        "centrifuge_manifest_sha256": "2" * 64,
        "centrifuge_asset_usd_sha256_before": "3" * 64,
        "centrifuge_asset_usd_sha256_after": "7" * 64,
        "tube_manifest_sha256": "4" * 64,
        "tube_asset_usd_sha256_before": "5" * 64,
        "tube_asset_usd_sha256_after": "5" * 64,
    }

    inputs = _runtime_report_inputs(
        centrifuge_package=Path("/producer/r9/package"),
        tube_package=Path("/producer/tube/package"),
        profile=profile,
        profile_sha256="6" * 64,
        input_hashes=hashes,
    )

    assert inputs["integrity"]["status"] == "blocked"
