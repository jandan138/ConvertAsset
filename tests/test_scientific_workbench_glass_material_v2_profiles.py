from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "profiles/visual"
EXPECTED_SHARED_INPUTS = {
    "depth": {"type": "float", "value": 0.002},
    "frosting_roughness": {"type": "float", "value": 0.035},
    "glass_color": {"type": "color3f", "value": [0.99, 0.998, 1.0]},
    "glass_ior": {"type": "float", "value": 1.47},
    "reflection_color": {"type": "color3f", "value": [1.0, 1.0, 1.0]},
}
PROFILE_TARGETS = {
    "scientific_workbench_graduated_cylinder_250ml_glass_v2.json": {
        "/World/GraduatedCylinder250ml/Visual/Source/Hollow_Body/Hollow_Body_Mesh_002",
        "/World/GraduatedCylinder250ml/Visual/Source/Closed_Inner_Bottom/Cylinder_006",
        "/World/GraduatedCylinder250ml/Visual/Source/Pour_Spout/Pour_Spout_Mesh_002",
        "/World/GraduatedCylinder250ml/Visual/Source/Thickened_Rim/Torus_002",
        "/World/GraduatedCylinder250ml/Visual/Source/Hex_Base/Cylinder_004",
    },
    "scientific_workbench_beaker_325ml_glass_v2.json": {
        "/World/Beaker325ml/Visual/Source/Rolled_Rim/Torus",
        "/World/Beaker325ml/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh",
        "/World/Beaker325ml/Visual/Source/Pour_Spout/Pour_Spout_Mesh",
    },
    "scientific_workbench_flat_bottom_flask_250ml_29_42_glass_v2.json": {
        "/World/FlatBottomFlask2942/Visual/Source/Flat_Bottom_Flask_Hollow_Body/Flat_Bottom_Flask_Hollow_Body_Mesh",
        "/World/FlatBottomFlask2942/Visual/Source/Flask_Rolled_Rim/Torus",
    },
    "scientific_workbench_beaker_dynamic_glass_v2.json": {
        "/World/Beaker/Visual/Source/Obj3d66_11490791_6_932/Obj3d66_11490791_6_932",
    },
    "scientific_workbench_reagent_bottle_90x55_glass_v2.json": {
        "/World/ReagentBottle90x55/Visual/Source/VIS_ReagentBottle_ClearGlass/VIS_ReagentBottle_ClearGlass_Mesh/MAT_Borosilicate_Clear",
    },
    "scientific_workbench_erlenmeyer_flask_250ml_90x35_glass_v2.json": {
        "/World/ErlenmeyerFlask250ml90x35/Visual/Source/VIS_ErlenmeyerFlask_ClearGlass/VIS_ErlenmeyerFlask_ClearGlass_Mesh/MAT_Borosilicate_Clear",
    },
}


def test_glass_v2_profiles_share_the_clear_borosilicate_recipe_and_exact_targets() -> None:
    for filename, expected_targets in PROFILE_TARGETS.items():
        profile = json.loads((PROFILE_ROOT / filename).read_text(encoding="utf-8"))
        assert profile["schema_version"] == "aan.visual_material_profile.v2"
        assert profile["revision"] == "glass_v2"
        override = profile["override"]
        assert override["kind"] == "mdl_glass"
        assert override["source_sub_identifier"] == "OmniGlass"
        assert override["material_name"] == "ClearBorosilicateV2"
        assert {
            key: value
            for key, value in override["mdl_inputs"].items()
            if key != "thin_walled"
        } == EXPECTED_SHARED_INPUTS
        assert set(override["binding_targets"]) == expected_targets


def test_only_the_graduated_cylinder_uses_the_reviewed_thin_wall_mode() -> None:
    for filename in PROFILE_TARGETS:
        profile = json.loads((PROFILE_ROOT / filename).read_text(encoding="utf-8"))
        thin_walled = profile["override"]["mdl_inputs"]["thin_walled"]
        assert thin_walled["type"] == "bool"
        assert thin_walled["value"] is filename.startswith(
            "scientific_workbench_graduated_cylinder_250ml"
        )


def test_glass_v2_keeps_ground_glass_and_labels_outside_the_override() -> None:
    for filename in PROFILE_TARGETS:
        profile = json.loads((PROFILE_ROOT / filename).read_text(encoding="utf-8"))
        targets = "\n".join(profile["override"]["binding_targets"])
        assert "GroundGlass" not in targets
        assert "Ground_Joint" not in targets
        assert "Stopper" not in targets
        assert "DECAL_" not in targets


def test_graduated_cylinder_v2_explicitly_includes_the_hexagonal_base() -> None:
    profile = json.loads(
        (
            PROFILE_ROOT
            / "scientific_workbench_graduated_cylinder_250ml_glass_v2.json"
        ).read_text(encoding="utf-8")
    )
    targets = profile["override"]["binding_targets"]
    assert "/World/GraduatedCylinder250ml/Visual/Source/Hex_Base/Cylinder_004" in targets
    assert "plastic base" not in profile["override"]["claim_boundary"].lower()
