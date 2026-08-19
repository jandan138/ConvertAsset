from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_hci_15ml_closed_insert_lid_assets import (
    DEFAULT_SOURCE,
    ENTRY_PRIM,
    FORBIDDEN_K0365_TUBE_SHA256,
    K_D,
    K_H,
    K_H_SHORT,
    K_H_SHORT_BAND,
    assert_not_forbidden_k0365_tube_hash,
    bake_closed_usda,
    build,
    scaled_geometry,
)
from scripts.qualify_centrifuge_task_interactions import build_parser
from scripts.qualify_hci_15ml_closed_insert_lid import (
    CLOSED_TUBE_ENTRY_PRIM,
    reject_forbidden_tube_hash,
)


FIXTURE = """#usda 1.0
(
    defaultPrim = "root"
    doc = "Blender fixture"
    endTimeCode = 48
    metersPerUnit = 1
    startTimeCode = 1
    upAxis = "Z"
)

def Xform "root"
{
    float3 xformOp:rotateXYZ = (0, -0, 180)
    uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]

    def Xform "centrifuge_tube_15ml_red_cap_ROOT"
    {
        def Xform "Cap_Controller"
        {
            float3 xformOp:rotateXYZ.timeSamples = {
                1: (0, -0, 0),
                2: (0, -0, 90),
            }
            double3 xformOp:translate.timeSamples = {
                1: (0, 0, 0),
                2: (0, 0, 0.025),
            }
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]

            def Mesh "Cap_Shell_Mesh"
            {
                float3[] extent = [(-0.01042, -0.01042, 0.10096), (0.01042, 0.01042, 0.1197)]
                normal3f[] normals = [(0, 0, 1)]
                point3f[] points = [(0.01042, 0, 0.1197), (0, 0, 0)]
            }
        }

        def Xform "Label"
        {
            double3 xformOp:translate = (0.002, -0.00855, 0.08799999952316284)
            float3 xformOp:rotateXYZ = (0, -0, 0)
            float3 xformOp:scale = (1, 1, 1)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
        }
    }
}
"""


def test_hci_fit_midpoint_scale_lands_in_admission_bands() -> None:
    geometry = scaled_geometry(K_D, K_H)

    assert 0.50 <= geometry["k_d"] <= 0.55
    assert 0.33 <= geometry["k_h"] <= 0.37
    assert 10.4 <= geometry["cap_od_mm"] <= 11.5
    assert 39.5 <= geometry["assembled_height_mm"] <= 44.3
    assert 0.5 <= geometry["radial_clearance_in_hci_hole_mm"][0] <= 1.5
    assert 0.5 <= geometry["radial_clearance_in_hci_hole_mm"][1] <= 1.5
    assert geometry["tube_radius_m"] == pytest.approx(0.01042 * K_D)
    assert geometry["tube_height_m"] == pytest.approx(0.1197 * K_H)


def test_baker_scales_points_and_translates_not_rotates_and_freezes_cap() -> None:
    baked = bake_closed_usda(FIXTURE, k_d=K_D, k_h=K_H)

    assert "timeSamples" not in baked
    assert "endTimeCode = 1" in baked
    assert "float3 xformOp:rotateXYZ = (0, -0, 180)" in baked
    assert "float3 xformOp:scale = (1, 1, 1)" in baked
    assert f"({0.01042 * K_D:.12g}, 0, {0.1197 * K_H:.12g})" in baked
    assert f"({0.002 * K_D:.12g}, {-0.00855 * K_D:.12g}, {0.08799999952316284 * K_H:.12g})" in baked
    assert "0.025" not in baked
    assert "frozen_closed_frame_1" in baked
    assert "double3 xformOp:translate = (0, 0, 0)" in baked


def test_builder_writes_identity_root_closed_facade(tmp_path: Path) -> None:
    source = tmp_path / "centrifuge_tube_15ml_red_cap.usda"
    source.write_text(FIXTURE, encoding="utf-8")
    before = source.read_bytes()

    result = build(source=source, out=tmp_path / "out")

    assert source.read_bytes() == before
    facade = result["facade"].read_text(encoding="utf-8")
    interaction = json.loads(result["interaction"].read_text(encoding="utf-8"))
    physics = json.loads(result["physics"].read_text(encoding="utf-8"))
    provenance = json.loads(result["manifest"].read_text(encoding="utf-8"))
    entry_header, visual = facade.split('def Xform "CentrifugeTube15mlClosed"', 1)[1].split(
        'def Xform "Visual"', 1
    )

    assert 'def Xform "World"' in facade
    assert "xformOp:" not in entry_header
    assert "xformOp:scale" not in visual.split("{", 1)[0]
    assert result["baked"].name in facade
    assert interaction["asset_entry_prim"] == ENTRY_PRIM
    assert interaction["named_frames"]["support"]["translation_body_local_usd"] == [
        0.0,
        0.0,
        0.0,
    ]
    assert interaction["colliders"][1]["geometry"]["radius"] == pytest.approx(0.01042 * K_D)
    assert physics["scope_rules"][0]["scope_path"] == ENTRY_PRIM
    assert provenance["bake"]["weld_cap_to_body"] is True
    assert provenance["bake"]["root_scale"] == [1.0, 1.0, 1.0]
    assert FORBIDDEN_K0365_TUBE_SHA256 in provenance["forbidden_reuse"]
    assert provenance["source"]["unchanged"] is True


def test_forbidden_k0365_hash_is_rejected() -> None:
    with pytest.raises(ValueError, match="k=0.365"):
        assert_not_forbidden_k0365_tube_hash(FORBIDDEN_K0365_TUBE_SHA256)
    with pytest.raises(ValueError, match="k=0.365"):
        reject_forbidden_tube_hash(FORBIDDEN_K0365_TUBE_SHA256)
    assert_not_forbidden_k0365_tube_hash("0" * 64)
    reject_forbidden_tube_hash("0" * 64)


def test_qualify_parser_accepts_closed_tube_entry_and_dimensions() -> None:
    args = build_parser().parse_args(
        [
            "--device-profile",
            "/tmp/profile.json",
            "--tube-entry-prim",
            CLOSED_TUBE_ENTRY_PRIM,
            "--tube-radius-m",
            "0.0055226",
            "--tube-height-m",
            "0.041895",
        ]
    )

    assert args.tube_entry_prim == "/World/CentrifugeTube15mlClosed"
    assert args.tube_radius_m == pytest.approx(0.0055226)
    assert args.tube_height_m == pytest.approx(0.041895)


def test_qualify_parser_accepts_balanced_socket_pair_selection() -> None:
    args = build_parser().parse_args(
        [
            "--device-profile",
            "/tmp/profile.json",
            "--socket-name",
            "tube_socket_1",
            "--additional-parked-socket",
            "tube_socket_2",
        ]
    )

    assert args.socket_name == "tube_socket_1"
    assert args.additional_parked_socket == "tube_socket_2"


def test_device_profile_validation_follows_selected_socket_names(tmp_path: Path) -> None:
    import json

    from scripts.qualify_centrifuge_task_interactions import _load_device_profile

    profile = {
        "schema_version": "aan.articulated_device_profile.v1",
        "source_sha256": "a" * 64,
        "asset_entry_prim": "/World/Centrifuge",
        "articulation_root_prim": "/World/Centrifuge",
        "required_runtime_task_gates": [
            "lid_contact_cycle",
            "button_contact_cycle",
            "button_reset_stability",
            "rotor_reset_stability",
            "socket_insertion_clearance",
        ],
        "named_frames": {
            "lid_close_contact": {
                "authoritative": True,
                "parent_prim": "/World/Centrifuge/group_23",
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "translation_parent_local_m": [0.0, 0.0, 0.0],
            },
            "start_button_press": {
                "authoritative": True,
                "parent_prim": "/World/Centrifuge/group_2",
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "translation_parent_local_m": [0.0, 0.0, 0.0],
            },
        },
    }
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(ValueError, match="tube_socket_1_aperture"):
        _load_device_profile(
            path,
            source_sha256="a" * 64,
            articulation_root_prim="/World/Centrifuge",
            socket_names=("tube_socket_1",),
        )
    with pytest.raises(ValueError, match="tube_socket_0_aperture"):
        _load_device_profile(
            path,
            source_sha256="a" * 64,
            articulation_root_prim="/World/Centrifuge",
        )


def test_short_cup_variant_fits_visual_cup_and_closed_lid() -> None:
    geometry = scaled_geometry(K_D, K_H_SHORT, k_h_band=K_H_SHORT_BAND)

    assert K_H_SHORT_BAND[0] <= geometry["k_h"] <= K_H_SHORT_BAND[1]
    # Seat on the measured visual cup floor (0.1281 m): cap top must stay
    # below the measured closed-lid inner surface (0.1569 m) with margin.
    cap_top = 0.1281 + geometry["assembled_height_mm"] / 1000.0
    assert cap_top <= 0.1569 - 0.002
    # The cap still fits the cup mouth (~17 mm) and the band test for the
    # default long variant still rejects the short k_h.
    assert geometry["cap_od_mm"] <= 17.0
    with pytest.raises(ValueError, match="k_h"):
        scaled_geometry(K_D, K_H_SHORT)


@pytest.mark.skipif(not DEFAULT_SOURCE.is_file(), reason="lab-library 15 mL USDA is not on this host")
def test_real_15ml_bake_matches_cap_od_and_height_bands() -> None:
    baked = bake_closed_usda(DEFAULT_SOURCE.read_text(encoding="utf-8"))
    geometry = scaled_geometry()

    assert "timeSamples" not in baked
    assert f"({geometry['tube_radius_m']:.12g}, 0, " in baked
    assert 10.4 <= geometry["cap_od_mm"] <= 11.5
    assert 39.5 <= geometry["assembled_height_mm"] <= 44.3
