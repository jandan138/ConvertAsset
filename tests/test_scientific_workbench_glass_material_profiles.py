from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "profiles/visual"
EXPECTED_INPUTS = {
    "cutout_opacity": {"type": "float", "value": 0.0},
    "enable_opacity": {"type": "bool", "value": False},
    "frosting_roughness": {"type": "float", "value": 0.0},
    "reflection_color": {
        "type": "color3f",
        "value": [0.86629593, 0.97533488, 0.98841697],
    },
    "roughness_texture_influence": {"type": "float", "value": 1.0},
}
EXPECTED_TARGETS = {
    "scientific_workbench_graduated_cylinder_250ml_glass_v1.json": {
        "/World/GraduatedCylinder250ml/Visual/Source/Hollow_Body/Hollow_Body_Mesh_002",
        "/World/GraduatedCylinder250ml/Visual/Source/Closed_Inner_Bottom/Cylinder_006",
        "/World/GraduatedCylinder250ml/Visual/Source/Pour_Spout/Pour_Spout_Mesh_002",
        "/World/GraduatedCylinder250ml/Visual/Source/Thickened_Rim/Torus_002",
    },
    "scientific_workbench_beaker_325ml_glass_v1.json": {
        "/World/Beaker325ml/Visual/Source/Rolled_Rim/Torus",
        "/World/Beaker325ml/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh",
        "/World/Beaker325ml/Visual/Source/Pour_Spout/Pour_Spout_Mesh",
    },
    "scientific_workbench_flat_bottom_flask_250ml_29_42_glass_v1.json": {
        "/World/FlatBottomFlask2942/Visual/Source/Flat_Bottom_Flask_Hollow_Body/Flat_Bottom_Flask_Hollow_Body_Mesh",
        "/World/FlatBottomFlask2942/Visual/Source/Flask_Rolled_Rim/Torus",
    },
    "scientific_workbench_beaker_dynamic_glass_v1.json": {
        "/World/Beaker/Visual/Source/Obj3d66_11490791_6_932/Obj3d66_11490791_6_932",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_glass_v1_profiles_share_the_reviewed_parameters_and_exact_targets() -> None:
    for filename, targets in EXPECTED_TARGETS.items():
        profile = json.loads((PROFILE_ROOT / filename).read_text(encoding="utf-8"))
        assert profile["schema_version"] == "aan.visual_material_profile.v2"
        assert profile["revision"] == "glass_v1"
        override = profile["override"]
        assert override["kind"] == "mdl_glass"
        assert override["source_sub_identifier"] == "OmniGlass"
        assert override["material_name"] == "OmniGlassRenderChangeV1"
        assert override["mdl_inputs"] == EXPECTED_INPUTS
        assert set(override["binding_targets"]) == targets
        assert _sha256(Path(override["source_mdl"])) == (
            "d71555550deb30af245c0ec939c8647442df5709a2977549cad7f6ddcc8c1182"
        )
        dependencies = override["source_mdl_dependencies"]
        assert len(dependencies) == 1
        assert Path(dependencies[0]).name == "OmniGlass_Opacity.mdl"
        assert _sha256(Path(dependencies[0])) == (
            "c7083b339c08371c9d8b9acda49e61fec294d380a6ce2b81fa9419583c0ef86d"
        )


def test_glass_v1_profiles_are_bound_to_the_current_facades() -> None:
    for filename in EXPECTED_TARGETS:
        profile = json.loads((PROFILE_ROOT / filename).read_text(encoding="utf-8"))
        source_path = ROOT / profile["source_binding"]["source_path"]
        assert source_path.is_file()
        assert profile["source_binding"]["sha256"] == _sha256(source_path)


def test_flat_flask_profile_preserves_the_frosted_ground_joint() -> None:
    profile = json.loads(
        (PROFILE_ROOT / "scientific_workbench_flat_bottom_flask_250ml_29_42_glass_v1.json").read_text(
            encoding="utf-8"
        )
    )
    targets = "\n".join(profile["override"]["binding_targets"])
    assert "Ground_Joint" not in targets
    assert "Stopper" not in targets
