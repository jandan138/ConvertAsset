from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "profiles/visual"
BUILDER_PATH = ROOT / "scripts/build_scientific_workbench_glass_web_standard_inputs.py"

WEB_STANDARD_INPUTS = {
    "cutout_opacity": {"type": "float", "value": 0.0},
    "depth": {"type": "float", "value": 0.002},
    "enable_opacity": {"type": "bool", "value": False},
    "frosting_roughness": {"type": "float", "value": 0.035},
    "glass_color": {"type": "color3f", "value": [0.99, 0.998, 1.0]},
    "glass_ior": {"type": "float", "value": 1.47},
    "reflection_color": {"type": "color3f", "value": [1.0, 1.0, 1.0]},
    "roughness_texture_influence": {"type": "float", "value": 1.0},
    "thin_walled": {"type": "bool", "value": False},
}

PROFILE_TARGETS = {
    "scientific_workbench_graduated_cylinder_250ml_glass_web_standard_v1.json": {
        "/World/GraduatedCylinder250ml/Visual/Source/Hollow_Body/Hollow_Body_Mesh_002",
        "/World/GraduatedCylinder250ml/Visual/Source/Closed_Inner_Bottom/Cylinder_006",
        "/World/GraduatedCylinder250ml/Visual/Source/Pour_Spout/Pour_Spout_Mesh_002",
        "/World/GraduatedCylinder250ml/Visual/Source/Thickened_Rim/Torus_002",
        "/World/GraduatedCylinder250ml/Visual/Source/Hex_Base/Cylinder_004",
    },
    "scientific_workbench_beaker_325ml_glass_web_standard_v1.json": {
        "/World/Beaker325ml/Visual/Source/Rolled_Rim/Torus",
        "/World/Beaker325ml/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh",
        "/World/Beaker325ml/Visual/Source/Pour_Spout/Pour_Spout_Mesh",
    },
    "scientific_workbench_flat_bottom_flask_250ml_29_42_glass_web_standard_v1.json": {
        "/World/FlatBottomFlask2942/Visual/Source/Flat_Bottom_Flask_Hollow_Body/Flat_Bottom_Flask_Hollow_Body_Mesh",
        "/World/FlatBottomFlask2942/Visual/Source/Flask_Rolled_Rim/Torus",
    },
    "scientific_workbench_beaker_dynamic_glass_web_standard_v1.json": {
        "/World/Beaker/Visual/Source/Obj3d66_11490791_6_932/Obj3d66_11490791_6_932",
    },
}

GRADUATED_CYLINDER_V2_PROFILE = (
    "scientific_workbench_graduated_cylinder_250ml_glass_web_standard_v2.json"
)
GRADUATED_CYLINDER_V2_TARGETS = PROFILE_TARGETS[
    "scientific_workbench_graduated_cylinder_250ml_glass_web_standard_v1.json"
] | {
    "/World/GraduatedCylinder250ml/Visual/Source/Base_Connector/Cylinder_005",
}


def _load_builder():
    spec = importlib.util.spec_from_file_location("glass_web_standard_builder", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_web_standard_profiles_author_the_complete_page_material_state() -> None:
    for filename, expected_targets in PROFILE_TARGETS.items():
        profile = json.loads((PROFILE_ROOT / filename).read_text(encoding="utf-8"))
        assert profile["schema_version"] == "aan.visual_material_profile.v2"
        assert profile["revision"] == "glass_web_standard_v1"
        override = profile["override"]
        assert override["kind"] == "mdl_glass"
        assert override["source_sub_identifier"] == "OmniGlass"
        assert override["material_name"] == "WebStandardClearBorosilicate"
        assert override["mdl_inputs"] == WEB_STANDARD_INPUTS
        assert set(override["binding_targets"]) == expected_targets


def test_web_standard_keeps_non_clear_parts_outside_the_override() -> None:
    for filename in PROFILE_TARGETS:
        profile = json.loads((PROFILE_ROOT / filename).read_text(encoding="utf-8"))
        targets = "\n".join(profile["override"]["binding_targets"])
        assert "GroundGlass" not in targets
        assert "Ground_Joint" not in targets
        assert "Stopper" not in targets
        assert "DECAL_" not in targets


def test_graduated_cylinder_v2_includes_the_round_base_connector() -> None:
    profile = json.loads(
        (PROFILE_ROOT / GRADUATED_CYLINDER_V2_PROFILE).read_text(encoding="utf-8")
    )
    assert profile["schema_version"] == "aan.visual_material_profile.v2"
    assert profile["revision"] == "glass_web_standard_v2"
    override = profile["override"]
    assert override["material_name"] == "WebStandardClearBorosilicate"
    assert override["mdl_inputs"] == WEB_STANDARD_INPUTS
    assert set(override["binding_targets"]) == GRADUATED_CYLINDER_V2_TARGETS


def test_manual_vessels_use_the_reviewed_simready_sources_without_visual_facades(
    tmp_path: Path,
) -> None:
    builder = _load_builder()
    archive = ROOT.parent / "scenario-forge/external_artifacts/incoming/manual_glassware_v1.tar.gz"
    results = builder.build_inputs(archive=archive, out=tmp_path)

    expected = {
        "reagent_bottle_90x55": (
            "manual_glassware_v1/simready/reagent_bottle_90x55.usdc",
            "5406c5359ab7a1d8d18023f339bfe8d39661b499f758f8ce97f1e910493c0231",
        ),
        "erlenmeyer_flask_250ml_90x35": (
            "manual_glassware_v1/simready/erlenmeyer_flask_250ml_90x35.usdc",
            "ca085be7ed1765ea305ab859a7d74a520ff3c7edf03a3c388e63c065cf177ed7",
        ),
    }
    with tarfile.open(archive, "r:gz") as bundle:
        for asset_id, (member_name, expected_sha) in expected.items():
            paths = results[asset_id]
            assert set(paths) == {
                "source",
                "source_dependency",
                "interaction",
                "physics",
                "provenance",
            }
            stream = bundle.extractfile(member_name)
            assert stream is not None
            assert paths["source"].read_bytes() == stream.read()
            assert builder._sha(paths["source"]) == expected_sha
            dependency_member = builder.VESSELS[asset_id]["source_dependency_member"]
            dependency_stream = bundle.extractfile(dependency_member)
            assert dependency_stream is not None
            assert paths["source_dependency"].read_bytes() == dependency_stream.read()
            assert paths["source_dependency"].parent.name == "source_usd"

            provenance = json.loads(paths["provenance"].read_text(encoding="utf-8"))
            assert provenance["archive_member"] == member_name
            assert provenance["source_modified"] is False
            assert provenance["visual_material_policy"] == "preserve_original_simready"

            interaction = json.loads(
                paths["interaction"].read_text(encoding="utf-8")
            )
            assert interaction["asset_entry_prim"] == "/ObjectRoot"
            assert interaction["source_binding"]["stage_metrics"] == {
                "meters_per_unit": 1.0,
                "kilograms_per_unit": 1.0,
                "up_axis": "Z",
                "time_codes_per_second": 60.0,
                "frames_per_second": 60.0,
            }
            assert all(
                collider["relative_path"].startswith("Model/")
                for collider in interaction["colliders"]
            )
            assert interaction["source_binding"]["sha256"] == expected_sha

            physics = json.loads(paths["physics"].read_text(encoding="utf-8"))
            assert physics["scope_rules"][0]["scope_path"] == "/ObjectRoot"
            assert physics["source_binding"]["sha256"] == expected_sha
