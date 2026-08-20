from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from convert_asset.simple_sdf_liquid import (
    SimpleSdfLiquidError,
    evaluate_multi_set_runs,
    load_approved_collision_spec,
    load_multi_liquid_request,
    select_shared_recipe,
)
from convert_asset.simple_sdf_liquid_runtime import (
    build_multi_liquid_candidate,
    build_simple_sdf_package,
)


def _scene(path: Path) -> Path:
    path.write_text('#usda 1.0\n(defaultPrim = "World")\ndef Xform "World" {}\n')
    return path


def test_collision_build_requires_explicit_bottom_plug_approval(tmp_path: Path) -> None:
    scene = _scene(tmp_path / "scene.usda")
    spec = tmp_path / "collision.yaml"
    spec.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.simple_sdf_collision_spec.v1",
                "source_scene": str(scene),
                "containers": [
                    {
                        "id": "tube",
                        "container_prim": "/World/Tube",
                        "visual_mesh_prim": "/World/Tube/Visual/Mesh",
                        "particle_scale": "small_required",
                        "bottom_plug": {
                            "mode": "approved_cube",
                            "approved": False,
                            "size_m": [0.002, 0.002, 0.002],
                            "translate_local_m": [0, 0, 0.0015],
                        },
                    }
                ],
            },
            sort_keys=False,
        )
    )

    with pytest.raises(SimpleSdfLiquidError, match="explicitly approved"):
        load_approved_collision_spec(spec)


def test_any_small_container_selects_one_scene_wide_small_recipe(tmp_path: Path) -> None:
    scene = _scene(tmp_path / "scene.usda")
    request = tmp_path / "liquid.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.multi_liquid_sample_request.v1",
                "scene": str(scene),
                "validation": "quick",
                "sets": [
                    {
                        "id": "bottle",
                        "container_prim": "/World/Bottle",
                        "sampler_mesh_prim": "/World/BottleSampler",
                        "particle_scale": "task02_compatible",
                    },
                    {
                        "id": "tube",
                        "container_prim": "/World/Tube",
                        "sampler_mesh_prim": "/World/TubeSampler",
                        "particle_scale": "small_required",
                    },
                ],
            },
            sort_keys=False,
        )
    )

    parsed = load_multi_liquid_request(request)
    recipe = select_shared_recipe(parsed.sets)

    assert recipe["recipe_id"] == "colleague_small_gpu_pbd_v1"
    assert recipe["particle_set"]["spacing_m"] == pytest.approx(0.001)
    assert recipe["particle_set"]["width_m"] == pytest.approx(0.001188)
    assert recipe["particle_set"]["maximum_count_per_set"] == 50_000
    assert recipe["particle_set"]["maximum_count_total"] == 100_000


def test_multi_set_request_preserves_one_sampler_to_one_unique_set(tmp_path: Path) -> None:
    scene = _scene(tmp_path / "scene.usda")
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "schema_version": "aan.multi_liquid_sample_request.v1",
                "scene": str(scene),
                "validation": "qualified",
                "sets": [
                    {
                        "id": "a",
                        "container_prim": "/World/A",
                        "sampler_mesh_prim": "/World/SamplerA",
                        "particle_scale": "task02_compatible",
                    },
                    {
                        "id": "b",
                        "container_prim": "/World/B",
                        "sampler_mesh_prim": "/World/SamplerB",
                        "particle_scale": "task02_compatible",
                    },
                ],
            }
        )
    )

    parsed = load_multi_liquid_request(request)

    assert [item.set_id for item in parsed.sets] == ["a", "b"]
    assert [item.particle_group for item in parsed.sets] == [0, 1]
    assert parsed.sets[0].particle_prim == "/__ScenarioForgeFluid/ParticleSets/a"
    assert parsed.sets[1].particle_prim == "/__ScenarioForgeFluid/ParticleSets/b"


def test_qualified_gate_is_per_set_not_only_aggregate() -> None:
    runs = [
        {
            "hard_errors": [],
            "sets": {
                "bottle": {"retention_ratio": 1.0, "below_floor_count": 0},
                "tube": {"retention_ratio": 0.98, "below_floor_count": 0},
            },
        }
    ] * 3

    result = evaluate_multi_set_runs(runs, set_ids=("bottle", "tube"), mode="qualified")

    assert result["overall_status"] == "blocked"
    assert "tube:retention_below_0.99" in result["blocked_reasons"]


def _closed_cube_scene(path: Path) -> Path:
    path.write_text(
        '''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "World"
{
    def Xform "Container" (
        prepend apiSchemas = ["PhysicsRigidBodyAPI"]
    )
    {
        def Mesh "Visual" (
            prepend apiSchemas = ["PhysicsCollisionAPI", "PhysicsMeshCollisionAPI"]
        )
        {
            point3f[] points = [(-0.01,-0.01,0), (0.01,-0.01,0), (0.01,0.01,0), (-0.01,0.01,0), (-0.01,-0.01,0.02), (0.01,-0.01,0.02), (0.01,0.01,0.02), (-0.01,0.01,0.02)]
            int[] faceVertexCounts = [4,4,4,4,4,4]
            int[] faceVertexIndices = [0,3,2,1,4,5,6,7,0,1,5,4,1,2,6,5,2,3,7,6,3,0,4,7]
            bool physics:collisionEnabled = 1
            uniform token physics:approximation = "convexHull"
        }
    }
}
''',
        encoding="utf-8",
    )
    return path


def test_collision_package_disables_old_proxy_and_applies_visual_sdf(tmp_path: Path) -> None:
    scene = _closed_cube_scene(tmp_path / "scene.usda")
    spec = tmp_path / "collision.yaml"
    spec.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.simple_sdf_collision_spec.v1",
                "source_scene": str(scene),
                "containers": [
                    {
                        "id": "container",
                        "container_prim": "/World/Container",
                        "visual_mesh_prim": "/World/Container/Visual",
                        "particle_scale": "small_required",
                        "bottom_plug": {"mode": "none"},
                    }
                ],
            },
            sort_keys=False,
        )
    )

    build_simple_sdf_package(spec_path=spec, output=tmp_path / "package")

    overlay = (tmp_path / "package/collision_overlay.usda").read_text()
    assert 'physics:approximation = "sdf"' in overlay
    manifest = json.loads((tmp_path / "package/manifest.json").read_text())
    assert manifest["containers"][0]["collision"] == "sdf"
    assert (tmp_path / "package/deps/source/asset.usd").is_file()


def test_candidate_bakes_one_points_prim_per_sampler_on_one_system(tmp_path: Path) -> None:
    scene = _closed_cube_scene(tmp_path / "scene.usda")
    request = tmp_path / "liquid.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.multi_liquid_sample_request.v1",
                "scene": str(scene),
                "validation": "quick",
                "sets": [
                    {
                        "id": "first",
                        "container_prim": "/World/Container",
                        "sampler_mesh_prim": "/World/Container/Visual",
                        "particle_scale": "small_required",
                    },
                    {
                        "id": "second",
                        "container_prim": "/World/Container",
                        "sampler_mesh_prim": "/World/Container/Visual",
                        "sampler_usd": str(scene),
                        "particle_scale": "small_required",
                    },
                ],
            },
            sort_keys=False,
        )
    )

    # The same physical sampler cannot silently feed two identities.
    with pytest.raises(SimpleSdfLiquidError, match="exactly one ParticleSet"):
        build_multi_liquid_candidate(request_path=request, output=tmp_path / "blocked")

    payload = yaml.safe_load(request.read_text())
    payload["sets"] = [payload["sets"][0]]
    request.write_text(yaml.safe_dump(payload, sort_keys=False))
    build_multi_liquid_candidate(request_path=request, output=tmp_path / "candidate")

    manifest = json.loads((tmp_path / "candidate/manifest.json").read_text())
    assert manifest["entrypoints"]["particle_system_prim"] == "/__ScenarioForgeFluid/ParticleSystem"
    assert manifest["sets"][0]["particle_prim"] == "/__ScenarioForgeFluid/ParticleSets/first"
    assert manifest["sets"][0]["particle_group"] == 0
    overlay = (tmp_path / "candidate/liquid_overlay.usda").read_text()
    assert overlay.count("PhysxParticleSystem") == 1
    assert 'scenarioForge:setId = "first"' in overlay


def test_multi_liquid_preserves_collision_package_overlay_and_stage_units(
    tmp_path: Path,
) -> None:
    from pxr import Usd, UsdGeom

    scene = _closed_cube_scene(tmp_path / "scene.usda")
    spec = tmp_path / "collision.yaml"
    spec.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.simple_sdf_collision_spec.v1",
                "source_scene": str(scene),
                "containers": [
                    {
                        "id": "container",
                        "container_prim": "/World/Container",
                        "visual_mesh_prim": "/World/Container/Visual",
                        "particle_scale": "small_required",
                        "bottom_plug": {
                            "mode": "approved_cube",
                            "approved": True,
                            "size_m": [0.002, 0.002, 0.002],
                            "translate_local_m": [0, 0, 0.001],
                        },
                    }
                ],
            },
            sort_keys=False,
        )
    )
    collision = tmp_path / "collision_package"
    build_simple_sdf_package(spec_path=spec, output=collision)
    request = tmp_path / "liquid.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.multi_liquid_sample_request.v1",
                "scene": str(collision / "asset.usda"),
                "validation": "quick",
                "sets": [
                    {
                        "id": "liquid",
                        "container_prim": "/World/Container",
                        "sampler_mesh_prim": "/World/Container/Visual",
                        "particle_scale": "small_required",
                    }
                ],
            },
            sort_keys=False,
        )
    )

    candidate = tmp_path / "candidate"
    build_multi_liquid_candidate(request_path=request, output=candidate)

    preserved = candidate / "deps/source/collision_overlay.usda"
    assert preserved.is_file()
    assert "__aan_simple_sdf_bottom_plug" in preserved.read_text()
    stage = Usd.Stage.Open(str(candidate / "scene.usda"))
    assert stage.GetPrimAtPath(
        "/World/Container/__aan_simple_sdf_bottom_plug"
    ).IsValid()
    assert UsdGeom.GetStageMetersPerUnit(stage) == pytest.approx(1.0)
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z
