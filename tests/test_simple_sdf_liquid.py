from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
import yaml

from convert_asset.simple_sdf_liquid import (
    SimpleSdfLiquidError,
    auto_cylinder_profile,
    evaluate_multi_set_runs,
    load_approved_collision_spec,
    load_multi_liquid_request,
    select_shared_recipe,
    target_particle_count,
)
from convert_asset.simple_sdf_liquid_runtime import (
    build_multi_liquid_candidate,
    build_simple_sdf_package,
    freeze_multi_liquid_editable,
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


def test_v2_request_accepts_inside_and_mouth_drop_auto_samplers(tmp_path: Path) -> None:
    scene = _scene(tmp_path / "scene.usda")
    request = tmp_path / "request.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.multi_liquid_sample_request.v2",
                "scene": str(scene),
                "validation": "quick",
                "sets": [
                    {
                        "id": "beaker",
                        "container_prim": "/World/Beaker",
                        "sampler": {
                            "mode": "inside_fill",
                            "fill_ratio": 0.4,
                            "visual_mesh_prim": "/World/Beaker/Visual",
                        },
                        "particle_scale": "task02_compatible",
                    },
                    {
                        "id": "bottle",
                        "container_prim": "/World/Bottle",
                        "sampler": {"mode": "mouth_drop", "fill_ratio": 0.8},
                        "particle_scale": "small_required",
                    },
                ],
            },
            sort_keys=False,
        )
    )

    parsed = load_multi_liquid_request(request)

    assert parsed.schema_version == "aan.multi_liquid_sample_request.v2"
    assert parsed.sets[0].sampler_mode == "inside_fill"
    assert parsed.sets[0].fill_ratio == pytest.approx(0.4)
    assert parsed.sets[0].visual_mesh_prim == "/World/Beaker/Visual"
    assert parsed.sets[1].sampler_mode == "mouth_drop"
    assert parsed.sets[1].fill_ratio == pytest.approx(0.8)
    assert parsed.sets[1].sampler_mesh_prim is None


def test_auto_cylinder_profile_keeps_inside_fill_in_vessel() -> None:
    profile = auto_cylinder_profile(
        {
            "center_xy_m": [0.1, -0.2],
            "radius_x_m": 0.03,
            "radius_y_m": 0.025,
            "floor_m": 0.01,
            "rim_m": 0.11,
        },
        mode="inside_fill",
        fill_ratio=0.4,
        spacing_m=0.001,
        particle_rest_offset_m=0.005,
    )

    assert profile.center_xy_m == pytest.approx((0.1, -0.2))
    assert profile.bottom_m == pytest.approx(0.0762)
    assert profile.top_m == pytest.approx(0.105)
    assert profile.radius_x_m < 0.03
    assert profile.radius_y_m < 0.025
    assert profile.initially_above_rim is False


def test_auto_cylinder_profile_stacks_mouth_drop_above_rim() -> None:
    low = auto_cylinder_profile(
        {
            "center_xy_m": [0.0, 0.0],
            "radius_x_m": 0.03,
            "radius_y_m": 0.03,
            "floor_m": 0.0,
            "rim_m": 0.1,
        },
        mode="mouth_drop",
        fill_ratio=0.2,
        spacing_m=0.001,
    )
    high = auto_cylinder_profile(
        {
            "center_xy_m": [0.0, 0.0],
            "radius_x_m": 0.03,
            "radius_y_m": 0.03,
            "floor_m": 0.0,
            "rim_m": 0.1,
        },
        mode="mouth_drop",
        fill_ratio=0.8,
        spacing_m=0.001,
    )

    assert low.bottom_m > 0.1
    assert high.bottom_m == pytest.approx(low.bottom_m)
    assert high.height_m > low.height_m
    assert high.top_m > 0.175
    assert high.initially_above_rim is True


def test_auto_cylinder_profile_falls_back_when_capacity_is_absent() -> None:
    cavity = {
        "center_xy_m": [0.0, 0.0],
        "radius_x_m": 0.007,
        "radius_y_m": 0.007,
        "floor_m": 0.002,
        "rim_m": 0.100,
    }

    profile = auto_cylinder_profile(
        cavity,
        mode="inside_fill",
        fill_ratio=0.4,
        spacing_m=0.001,
        capacity=None,
    )

    assert profile.target_volume_m3 == pytest.approx(
        math.pi * 0.007 * 0.007 * (0.002 + 0.4 * 0.098 - 0.002)
    )


def test_target_particle_count_uses_existing_spacing_lattice() -> None:
    assert target_particle_count(
        target_volume_m3=0.0003795, spacing_m=0.00582, limit=10_000
    ) == 1925


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


def _hollow_cylinder_scene(path: Path) -> Path:
    from pxr import Gf, Usd, UsdGeom

    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    UsdGeom.Xform.Define(stage, "/World/Container")
    mesh = UsdGeom.Mesh.Define(stage, "/World/Container/Hollow_Body")
    points = []
    segments = 16
    for z, radius in ((0.0, 0.02), (0.1, 0.02), (0.0, 0.018), (0.1, 0.018)):
        points.extend(
            Gf.Vec3f(radius * math.cos(2 * math.pi * i / segments),
                     radius * math.sin(2 * math.pi * i / segments), z)
            for i in range(segments)
        )
    counts = []
    indices = []
    for lower, upper in ((0, segments), (2 * segments, 3 * segments)):
        for i in range(segments):
            j = (i + 1) % segments
            counts.append(4)
            indices.extend([lower + i, lower + j, upper + j, upper + i])
    mesh.CreatePointsAttr(points)
    mesh.CreateFaceVertexCountsAttr(counts)
    mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    stage.GetRootLayer().Save()
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


def test_v2_candidate_authors_package_local_mouth_drop_sampler(tmp_path: Path) -> None:
    scene = _hollow_cylinder_scene(tmp_path / "hollow.usda")
    request = tmp_path / "liquid.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.multi_liquid_sample_request.v2",
                "scene": str(scene),
                "validation": "quick",
                "sets": [
                    {
                        "id": "liquid",
                        "container_prim": "/World/Container",
                        "sampler": {
                            "mode": "mouth_drop",
                            "fill_ratio": 0.2,
                            "visual_mesh_prim": "/World/Container/Hollow_Body",
                        },
                        "particle_scale": "task02_compatible",
                    }
                ],
            },
            sort_keys=False,
        )
    )

    output = tmp_path / "candidate"
    build_multi_liquid_candidate(request_path=request, output=output)

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["schema_version"] == "aan.multi_liquid_sample_result.v2"
    assert manifest["entrypoints"]["auto_samplers_usd"] == "evidence/auto_samplers.usda"
    assert manifest["sets"][0]["sampler_mode"] == "mouth_drop"
    assert manifest["sets"][0]["profile"]["initially_above_rim"] is True
    assert manifest["sets"][0]["opening"]["method"] == "highest_concentric_inner_ring"
    assert manifest["sets"][0]["capacity"]["method"] == "longest_repeated_inner_wall_ring"
    assert manifest["sets"][0]["particle_count"] > 0
    assert (output / "evidence/auto_samplers.usda").is_file()
    scene_text = (output / "scene.usda").read_text()
    assert "auto_samplers.usda" not in scene_text


def test_v3_candidate_delivers_frozen_and_height_editable_sampler(tmp_path: Path) -> None:
    from pxr import Usd, UsdShade

    scene = _hollow_cylinder_scene(tmp_path / "hollow.usda")
    request = tmp_path / "liquid.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.multi_liquid_sample_request.v3",
                "scene": str(scene),
                "validation": "quick",
                "delivery_mode": "dual_editable_frozen",
                "sets": [
                    {
                        "id": "beaker_liquid",
                        "container_prim": "/World/Container",
                        "sampler": {
                            "mode": "mouth_drop",
                            "fill_ratio": 0.4,
                            "editable_axis": "height_z",
                            "visual_mesh_prim": "/World/Container/Hollow_Body",
                        },
                        "particle_scale": "task02_compatible",
                        "preview_color": [0.11, 0.22, 0.33],
                    }
                ],
            },
            sort_keys=False,
        )
    )

    output = tmp_path / "candidate"
    build_multi_liquid_candidate(request_path=request, output=output)

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["schema_version"] == "aan.multi_liquid_sample_result.v3"
    assert manifest["entrypoints"]["root_usd"] == "scene.usda"
    assert manifest["entrypoints"]["editable_root_usd"] == "scene_liquid_edit.usda"
    assert manifest["sampling"]["runtime_resampling"] == "editable_only"
    assert manifest["rendering"]["color_source"] == (
        "shared_particle_system_material"
    )
    assert manifest["sets"][0]["editable_axis"] == "height_z"
    assert manifest["sets"][0]["particle_prim"].endswith("/beaker_liquid")
    assert manifest["sets"][0]["preview_color_requested"] == [0.11, 0.22, 0.33]

    frozen = Usd.Stage.Open(str(output / "liquid_overlay.usda"))
    particle_set = frozen.GetPrimAtPath(manifest["sets"][0]["particle_prim"])
    assert particle_set.IsValid()
    assert not particle_set.GetAttribute(
        "primvars:displayColor"
    ).HasAuthoredValueOpinion()
    assert not particle_set.GetAttribute(
        "primvars:displayOpacity"
    ).HasAuthoredValueOpinion()
    particle_material, _ = UsdShade.MaterialBindingAPI(
        particle_set
    ).ComputeBoundMaterial()
    system_material, _ = UsdShade.MaterialBindingAPI(
        frozen.GetPrimAtPath(manifest["entrypoints"]["particle_system_prim"])
    ).ComputeBoundMaterial()
    assert particle_material.GetPath() == system_material.GetPath()
    shader = UsdShade.Shader(
        frozen.GetPrimAtPath(str(particle_material.GetPath()) + "/PreviewSurface")
    )
    assert tuple(shader.GetInput("diffuseColor").Get()) == pytest.approx(
        (0.11, 0.22, 0.33)
    )

    editable = Usd.Stage.Open(str(output / "scene_liquid_edit.usda"))
    sampler = editable.GetPrimAtPath(
        "/__ScenarioForgeFluid/Samplers/beaker_liquid/Volume"
    )
    assert sampler.IsValid()
    assert "PhysxParticleSamplingAPI" in (
        output / "editable_samplers.usda"
    ).read_text()
    assert [
        str(path)
        for path in sampler.GetRelationship(
            "physxParticleSampling:particles"
        ).GetTargets()
    ] == [manifest["sets"][0]["particle_prim"]]


def test_v3_freeze_preserves_one_set_per_sampler_and_shared_system(tmp_path: Path) -> None:
    scene = _hollow_cylinder_scene(tmp_path / "hollow.usda")
    request = tmp_path / "liquid.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.multi_liquid_sample_request.v3",
                "scene": str(scene),
                "validation": "quick",
                "delivery_mode": "dual_editable_frozen",
                "sets": [
                    {
                        "id": "first",
                        "container_prim": "/World/Container",
                        "sampler": {
                            "mode": "mouth_drop",
                            "fill_ratio": 0.2,
                            "editable_axis": "height_z",
                        },
                        "particle_scale": "task02_compatible",
                    },
                    {
                        "id": "second",
                        "container_prim": "/World/Container",
                        "sampler": {
                            "mode": "mouth_drop",
                            "fill_ratio": 0.4,
                            "editable_axis": "height_z",
                        },
                        "particle_scale": "task02_compatible",
                    },
                ],
            },
            sort_keys=False,
        )
    )
    source = tmp_path / "candidate"
    build_multi_liquid_candidate(request_path=request, output=source)

    frozen = tmp_path / "frozen"
    freeze_multi_liquid_editable(source=source, output=frozen)
    manifest = json.loads((frozen / "manifest.json").read_text())

    assert len({item["particle_prim"] for item in manifest["sets"]}) == 2
    assert len({item["particle_group"] for item in manifest["sets"]}) == 2
    assert manifest["entrypoints"]["particle_system_prim"] == (
        "/__ScenarioForgeFluid/ParticleSystem"
    )


def test_shared_particle_system_rejects_distinct_preview_colors(tmp_path: Path) -> None:
    scene = _hollow_cylinder_scene(tmp_path / "hollow.usda")
    request = tmp_path / "liquid.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "schema_version": "aan.multi_liquid_sample_request.v3",
                "scene": str(scene),
                "validation": "quick",
                "delivery_mode": "dual_editable_frozen",
                "sets": [
                    {
                        "id": "first",
                        "container_prim": "/World/Container",
                        "sampler": {
                            "mode": "mouth_drop",
                            "fill_ratio": 0.2,
                            "editable_axis": "height_z",
                        },
                        "particle_scale": "task02_compatible",
                        "preview_color": [0.1, 0.2, 0.3],
                    },
                    {
                        "id": "second",
                        "container_prim": "/World/Container",
                        "sampler": {
                            "mode": "mouth_drop",
                            "fill_ratio": 0.4,
                            "editable_axis": "height_z",
                        },
                        "particle_scale": "task02_compatible",
                        "preview_color": [0.3, 0.2, 0.1],
                    },
                ],
            },
            sort_keys=False,
        )
    )

    with pytest.raises(
        SimpleSdfLiquidError,
        match="shared ParticleSystem cannot render distinct preview colors",
    ):
        build_multi_liquid_candidate(
            request_path=request,
            output=tmp_path / "candidate",
        )
