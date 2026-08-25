from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from convert_asset.cli import main
from convert_asset.fluid_interaction_asset import (
    evaluate_qualification_runs,
    FluidInteractionError,
    load_approved_proposal,
    normalized_collision_presets,
    qualification_policy,
)
from convert_asset.fluid_interaction_runtime import (
    _conduit_outlet_outer_radius,
    build_unqualified_asset_package,
)
from convert_asset.liquid_recipe import load_liquid_recipe, liquid_recipe_sha256


REPO = Path(__file__).resolve().parents[1]
COLLEAGUE_RECIPE = REPO / "profiles/gpu_pbd/colleague_small_gpu_pbd_v1.json"
SMALL_V2_RECIPE = REPO / "profiles/gpu_pbd/scientific_workbench_small_gpu_pbd_v2.json"


def _proposal(tmp_path: Path, *, behavior: str = "reservoir") -> Path:
    source = tmp_path / "source.usda"
    source.write_text(
        '#usda 1.0\n(defaultPrim = "World")\n'
        'def Xform "World"\n{\n'
        '    def Xform "Object"\n    {\n'
        '        def Mesh "Wall"\n        {\n'
        '            point3f[] points = [(0,0,0), (1,0,0), (0,1,0)]\n'
        '            int[] faceVertexCounts = [3]\n'
        '            int[] faceVertexIndices = [0,1,2]\n'
        '        }\n    }\n}\n',
        encoding="utf-8",
    )
    payload = {
        "schema_version": "aan.fluid_interaction_proposal.v1",
        "source_binding": {
            "source_usd": str(source.resolve()),
            "source_sha256": "AUTO",
            "scope_prim": "/World/Object",
        },
        "behavior": {"suggested": behavior, "confirmed": behavior},
        "geometry": {
            "axis_local": [0.0, 0.0, 1.0],
            "minimum_clearance_radius_m": 0.025,
            "roles": [
                {
                    "prim_path": "/World/Object/Wall",
                    "role": "wall",
                    "approximation": "sdf",
                }
            ],
            "frames": {"opening": {"position_m": [0.0, 0.0, 0.2]}},
        },
        "physics": {"material_class": "glass", "mass_source": "provisional_geometry"},
        "review": {"status": "approved", "reviewer": "fixture"},
    }
    path = tmp_path / "proposal.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_normalized_collision_presets_preserve_small_throats() -> None:
    large = normalized_collision_presets(0.025)
    small = normalized_collision_presets(0.0137)

    assert [item["sdf_resolution"] for item in large] == [128, 256, 512]
    assert large[1]["contact_offset_m"] == pytest.approx(0.005)
    assert small[1]["contact_offset_m"] < large[1]["contact_offset_m"]
    assert small[1]["sdf_margin_m"] < 0.01


def test_approved_proposal_requires_confirmed_behavior_and_review(tmp_path: Path) -> None:
    path = _proposal(tmp_path)
    payload = yaml.safe_load(path.read_text())
    payload["review"]["status"] = "pending"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(FluidInteractionError, match="approved"):
        load_approved_proposal(path)


def test_qualification_policies_are_behavior_specific() -> None:
    reservoir = qualification_policy("reservoir")
    conduit = qualification_policy("conduit")
    guide = qualification_policy("surface_guide")

    assert reservoir["minimum_static_retention_ratio"] == 0.99
    assert reservoir["minimum_pour_outflow_ratio"] == 0.50
    assert conduit["minimum_legal_outlet_ratio"] == 0.90
    assert conduit["maximum_structural_leak_count"] == 0
    assert guide["minimum_capture_improvement_ratio"] == 0.20
    assert guide["failure_disposition"] == "not_applicable"


def test_qualification_aggregation_enforces_outlet_and_guide_boundaries() -> None:
    conduit = evaluate_qualification_runs(
        "conduit",
        [
            {"legal_outlet_ratio": 0.93, "structural_leak_count": 0, "hard_errors": []},
            {"legal_outlet_ratio": 0.91, "structural_leak_count": 0, "hard_errors": []},
            {"legal_outlet_ratio": 0.90, "structural_leak_count": 0, "hard_errors": []},
        ],
    )
    guide = evaluate_qualification_runs(
        "surface_guide",
        [
            {"capture_ratio": 0.7, "baseline_capture_ratio": 0.65, "structural_leak_count": 0, "hard_errors": []}
        ]
        * 3,
    )

    assert conduit["overall_status"] == "pass"
    assert guide["overall_status"] == "not_applicable"
    assert "surface_guide_effect_not_established" in guide["blocked_reasons"]


def test_cli_can_propose_a_surface_guide_without_qualifying_it(
    tmp_path: Path,
) -> None:
    source = tmp_path / "rod.usda"
    source.write_text(
        '#usda 1.0\n(defaultPrim = "World")\n'
        'def Xform "World"\n{\n    def Xform "GlassRod"\n    {\n    }\n}\n',
        encoding="utf-8",
    )
    out = tmp_path / "review"

    assert main(
        [
            "fluid-interaction-propose",
            str(source),
            "--prim",
            "/World/GlassRod",
            "--out",
            str(out),
        ]
    ) == 0

    proposal = yaml.safe_load((out / "proposal.yaml").read_text())
    assert proposal["behavior"]["suggested"] == "surface_guide"
    assert proposal["review"]["status"] == "pending"
    assert (out / "evidence/geometry_roles.svg").is_file()
    assert (out / "evidence/axial_sections.svg").is_file()
    report = json.loads((out / "proposal_report.json").read_text())
    assert report["status"] == "review_required"


def test_cli_refuses_to_qualify_pending_proposal(tmp_path: Path) -> None:
    proposal = _proposal(tmp_path)
    payload = yaml.safe_load(proposal.read_text())
    payload["review"]["status"] = "pending"
    proposal.write_text(yaml.safe_dump(payload), encoding="utf-8")

    assert main(
        [
            "fluid-interaction-qualify",
            "--proposal",
            str(proposal),
            "--out",
            str(tmp_path / "package"),
            "--no-runtime-qualification",
        ]
    ) == 5
    assert not (tmp_path / "package/manifest.json").exists()


def test_candidate_package_authors_collision_without_shipping_particles(tmp_path: Path) -> None:
    proposal = _proposal(tmp_path)

    manifest_path = build_unqualified_asset_package(
        proposal_path=proposal, output=tmp_path / "package"
    )

    manifest = json.loads(manifest_path.read_text())
    assert manifest["overall_status"] == "candidate"
    stage_text = (tmp_path / "package/asset.usda").read_text()
    assert "PhysicsCollisionAPI" in stage_text
    assert "PhysxCollisionAPI" in stage_text
    assert "PhysxSDFMeshCollisionAPI" in stage_text
    assert "physxCollision:contactOffset" in stage_text
    assert 'physics:approximation = "sdf"' in stage_text
    assert "PhysxParticleSystem" not in stage_text
    assert "ParticleSet" not in stage_text


def test_colleague_small_recipe_is_explicit_and_hashable() -> None:
    recipe = load_liquid_recipe(COLLEAGUE_RECIPE)

    assert recipe["recipe_id"] == "colleague_small_gpu_pbd_v1"
    assert recipe["particle_set"]["spacing_m"] == pytest.approx(0.001)
    assert recipe["particle_set"]["width_m"] == pytest.approx(0.001188)
    assert recipe["particle_system"]["particle_contact_offset_m"] == pytest.approx(
        0.001
    )
    assert recipe["particle_system"]["effective_rest_offset_m"] == pytest.approx(
        0.005
    )
    assert len(liquid_recipe_sha256(recipe)) == 64


def test_small_v2_changes_only_offsets_from_colleague_recipe() -> None:
    colleague = load_liquid_recipe(COLLEAGUE_RECIPE)
    revised = load_liquid_recipe(SMALL_V2_RECIPE)

    assert revised["particle_set"] == colleague["particle_set"]
    assert revised["material"] == colleague["material"]
    assert revised["particle_system"]["max_velocity_m_s"] == colleague[
        "particle_system"
    ]["max_velocity_m_s"]
    assert revised["particle_system"]["particle_contact_offset_m"] == pytest.approx(
        0.0007
    )
    assert revised["particle_system"]["effective_rest_offset_m"] == pytest.approx(
        0.00055
    )


def test_conduit_outlet_uses_outer_shell_radius_not_inner_throat() -> None:
    geometry = {
        "minimum_clearance_radius_m": 0.0035,
        "cavity": {"inner_outer_radial_ratio": 0.7},
    }

    assert _conduit_outlet_outer_radius(geometry) == pytest.approx(0.005)


def test_candidate_copies_and_hash_binds_selected_liquid_recipe(tmp_path: Path) -> None:
    proposal = _proposal(tmp_path, behavior="conduit")

    manifest_path = build_unqualified_asset_package(
        proposal_path=proposal,
        output=tmp_path / "package",
        liquid_recipe_path=COLLEAGUE_RECIPE,
    )

    manifest = json.loads(manifest_path.read_text())
    copied = tmp_path / "package/interaction/liquid_recipe.json"
    profile = json.loads(
        (tmp_path / "package/interaction/fluid_profile.json").read_text()
    )
    recipe = load_liquid_recipe(copied)
    assert manifest["liquid_recipe"]["id"] == "colleague_small_gpu_pbd_v1"
    assert manifest["liquid_recipe"]["sha256"] == liquid_recipe_sha256(recipe)
    assert profile["liquid_recipe"] == manifest["liquid_recipe"]
    assert profile["collision_parameters"]["contact_offset_m"] == pytest.approx(
        0.0005
    )
    assert profile["collision_parameters"]["selection"] == (
        "small_recipe_half_particle_contact_cap"
    )
