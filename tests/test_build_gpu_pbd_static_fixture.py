from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest
from pxr import Usd, UsdGeom


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/build_gpu_pbd_static_fixture.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("build_gpu_pbd_fixture", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_builds_0812_parameter_fixture_with_particles_above_floor(
    tmp_path: Path,
) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/GraduatedCylinder250ml",
                "collision": {
                    "mesh_prim": (
                        "/World/GraduatedCylinder250ml/Visual/Source/"
                        "PBD_Unified_Vessel/PBD_Unified_Vessel_Mesh"
                    )
                },
            }
        )
    )

    result = module.build_fixture(container_package=package, output=tmp_path / "out")

    assert result["particle_count"] == 548
    points = json.loads((tmp_path / "out/authored_particle_points.json").read_text())
    assert min(point[2] for point in points) >= 0.011705 + 0.005
    minimum_spacing = min(
        math.dist(left, right)
        for index, left in enumerate(points)
        for right in points[index + 1 :]
    )
    assert minimum_spacing >= 0.0058
    assert max(math.hypot(point[0], point[1]) for point in points) <= (
        0.019185 - 0.005 - 0.001 - 0.0005
    )
    assert max(point[2] for point in points) < 0.27824
    component = (tmp_path / "out/component.usda").read_text()
    assert 'prepend apiSchemas = ["PhysicsRigidBodyAPI"]' in component
    assert "physics:kinematicEnabled = 1" in component
    assert "particleContactOffset = 0.005" in component
    assert "restOffset = 0" in component
    assert "fluidRestOffset = -inf" in component
    assert "solidRestOffset = -inf" in component
    assert "maxDepenetrationVelocity = inf" in component
    assert "physxParticle:fluid" not in component
    assert "physxParticle:selfCollision" not in component
    assert "physxParticle:particleGroup" not in component
    assert "solverPositionIterationCount" not in component
    qualification_text = (tmp_path / "out/qualification.usda").read_text()
    assert "enableGPUDynamics = 1" in qualification_text
    assert 'matrix4d xformOp:transform = (' in qualification_text
    assert 'xformOpOrder = ["xformOp:transform"]' in qualification_text
    assert "gpuFoundLostAggregatePairsCapacity = 1500" in (
        tmp_path / "out/qualification.usda"
    ).read_text()


def test_accepts_partition_collision_root(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/GraduatedCylinder250ml",
                "collision": {
                    "root_prim": (
                        "/World/GraduatedCylinder250ml/PBD_GPU_Collision"
                    )
                },
            }
        )
    )

    module.build_fixture(container_package=package, output=tmp_path / "out")

    fixture = json.loads((tmp_path / "out/fixture_profile.json").read_text())
    assert fixture["container_actor_mode"] == "kinematic_rigid_body"
    assert fixture["collision_mesh_prim"].endswith("/PBD_GPU_Collision")


def test_can_match_0812_dynamic_container_actor_mode(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/Beaker325ml",
                "collision": {"root_prim": "/World/Beaker325ml/Collision"},
            }
        )
    )

    module.build_fixture(
        container_package=package,
        output=tmp_path / "out",
        actor_mode="dynamic_rigid_body",
    )

    component = (tmp_path / "out/component.usda").read_text()
    assert "physics:kinematicEnabled = 0" in component
    fixture = json.loads((tmp_path / "out/fixture_profile.json").read_text())
    assert fixture["container_actor_mode"] == "dynamic_rigid_body"


def test_can_clone_authored_0812_particle_seed_from_usd(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/Beaker325ml",
                "collision": {"root_prim": "/World/Beaker325ml/Collision"},
                "cavity": {
                    "center_xy_m": [0.0, 0.0],
                    "radius_m": 0.05,
                    "floor_z_m": 0.003,
                    "rim_z_m": 0.12,
                    "support_z_m": 0.0,
                },
            }
        )
    )
    seed_usd = tmp_path / "seed.usda"
    stage = Usd.Stage.CreateNew(str(seed_usd))
    particles = UsdGeom.Points.Define(stage, "/World/ParticleSet")
    particles.GetPointsAttr().Set(
        [(0.28, 0.06, 0.78), (0.29, 0.06, 0.78), (0.28, 0.07, 0.79)]
    )
    stage.GetRootLayer().Save()
    bounds = tmp_path / "bounds.json"
    bounds.write_text(json.dumps({"center_xy_m": [0.28, 0.06]}))

    module.build_fixture(
        container_package=package,
        output=tmp_path / "out",
        particle_seed_usd=seed_usd,
        particle_seed_prim="/World/ParticleSet",
        particle_seed_bounds=bounds,
        particle_seed_mapping="rigid_translate_authored_cloud",
    )

    points = json.loads((tmp_path / "out/authored_particle_points.json").read_text())
    assert len(points) == 3
    assert points[0] == pytest.approx([0.0, 0.0, 0.008], abs=1e-8)
    fixture = json.loads((tmp_path / "out/fixture_profile.json").read_text())
    assert fixture["particle_parameters"]["initial_state"]["kind"] == (
        "source_authored_particle_cloud"
    )
    assert fixture["particle_parameters"]["initial_state"]["source_prim"] == (
        "/World/ParticleSet"
    )


def test_fixture_records_complete_world_space_containment_bounds(
    tmp_path: Path,
) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/GraduatedCylinder250ml",
                "collision": {"root_prim": "/World/GraduatedCylinder250ml/Collision"},
            }
        )
    )

    module.build_fixture(container_package=package, output=tmp_path / "out")

    fixture = json.loads((tmp_path / "out/fixture_profile.json").read_text())
    assert fixture["containment_bounds"] == {
        "center_xy_m": [0.0, 0.0],
        "floor_z_m": 0.011705,
        "radius_m": 0.019185,
        "rim_z_m": 0.27824,
        "support_z_m": 0.0,
    }


def test_fixture_uses_container_profile_cavity_instead_of_cylinder_constants(
    tmp_path: Path,
) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/Beaker325ml",
                "collision": {
                    "root_prim": "/World/Beaker325ml/PBD_GPU_Collision",
                    "contact_offset_m": 0.001,
                },
                "cavity": {
                    "center_xy_m": [0.0, 0.0],
                    "radius_m": 0.03527,
                    "floor_z_m": 0.003,
                    "rim_z_m": 0.11509,
                    "support_z_m": 0.0,
                },
            }
        )
    )

    result = module.build_fixture(container_package=package, output=tmp_path / "out")

    assert result["particle_count"] == 548
    fixture = json.loads((tmp_path / "out/fixture_profile.json").read_text())
    assert fixture["entry_prim"] == "/World/Beaker325ml"
    assert fixture["containment_bounds"] == {
        "center_xy_m": [0.0, 0.0],
        "radius_m": 0.03527,
        "floor_z_m": 0.003,
        "rim_z_m": 0.11509,
        "support_z_m": 0.0,
    }
    points = json.loads((tmp_path / "out/authored_particle_points.json").read_text())
    assert min(point[2] for point in points) >= 0.003 + 0.005
    assert max(point[2] for point in points) < 0.11509 - 0.005
    assert max(math.hypot(point[0], point[1]) for point in points) <= (
        0.03527 - 0.005 - 0.001 - 0.0005
    )


def test_can_build_single_particle_collider_probe(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/GraduatedCylinder250ml",
                "collision": {
                    "root_prim": "/World/GraduatedCylinder250ml/Collision",
                    "contact_offset_m": 0.001,
                },
            }
        )
    )

    result = module.build_fixture(
        container_package=package, output=tmp_path / "out", particle_count=1
    )

    assert result["particle_count"] == 1
    points = json.loads((tmp_path / "out/authored_particle_points.json").read_text())
    assert points == [[0.0, 0.0, 0.016705]]


def test_remaps_stable_reference_cloud_into_cylinder_without_density_squash() -> None:
    module = _module()
    reference = [
        [0.30, 0.10, 0.78],
        [0.32, 0.10, 0.78],
        [0.30, 0.12, 0.80],
        [0.32, 0.12, 0.80],
    ]

    remapped, transform = module.remap_reference_particle_cloud(
        reference,
        source_center_xy_m=(0.31, 0.11),
        target_radial_limit_m=0.012,
    )

    assert len(remapped) == 4
    assert max(math.hypot(point[0], point[1]) for point in remapped) <= 0.012
    assert min(point[2] for point in remapped) == 0.016705
    assert max(point[2] for point in remapped) < 0.27824 - 0.005
    assert transform["mapping"] == "volume_preserving_radial_fit"
    assert transform["vertical_scale"] == 1 / transform["radial_scale"] ** 2


def test_translates_stable_reference_cloud_without_changing_pairwise_spacing() -> None:
    module = _module()
    reference = [
        [0.30, 0.10, 0.78],
        [0.32, 0.10, 0.78],
        [0.30, 0.12, 0.80],
    ]

    translated, transform = module.translate_reference_particle_cloud(
        reference,
        source_center_xy_m=(0.31, 0.11),
        target_center_xy_m=(0.0, 0.0),
        target_floor_z_m=0.003,
        target_cavity_radius_m=0.04,
        target_rim_z_m=0.115,
    )

    assert math.isclose(
        math.dist(translated[0], translated[1]),
        math.dist(reference[0], reference[1]),
    )
    assert math.isclose(min(point[2] for point in translated), 0.008)
    assert transform["mapping"] == "rigid_translate_settled_cloud"


def test_fixture_can_use_provenanced_reference_particle_state(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/GraduatedCylinder250ml",
                "collision": {
                    "root_prim": "/World/GraduatedCylinder250ml/Collision",
                    "contact_offset_m": 0.001,
                },
            }
        )
    )
    seed = tmp_path / "reference_positions.json"
    seed.write_text(
        json.dumps(
            {
                "positions": [
                    [0.30, 0.10, 0.78],
                    [0.32, 0.10, 0.78],
                    [0.30, 0.12, 0.80],
                    [0.32, 0.12, 0.80],
                ]
            }
        )
    )
    bounds = tmp_path / "reference_bounds.json"
    bounds.write_text(json.dumps({"center_xy_m": [0.31, 0.11]}))

    result = module.build_fixture(
        container_package=package,
        output=tmp_path / "out",
        particle_seed=seed,
        particle_seed_bounds=bounds,
    )

    assert result["particle_count"] == 4
    fixture = json.loads((tmp_path / "out/fixture_profile.json").read_text())
    assert fixture["particle_parameters"]["initial_state"]["kind"] == (
        "normalized_reference_particle_cloud"
    )
    assert fixture["particle_parameters"]["initial_state"]["source_sha256"]


def test_fixture_accepts_promoted_plain_list_particle_state(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/Beaker325ml",
                "collision": {
                    "root_prim": "/World/Beaker325ml/PBD_GPU_Collision",
                    "contact_offset_m": 0.001,
                },
                "cavity": {
                    "center_xy_m": [0.0, 0.0],
                    "radius_m": 0.03527,
                    "floor_z_m": 0.003,
                    "rim_z_m": 0.11509,
                    "support_z_m": 0.0,
                },
            }
        )
    )
    seed = tmp_path / "promoted_points.json"
    seed.write_text(json.dumps([[0.30, 0.10, 0.78], [0.32, 0.10, 0.80]]))
    bounds = tmp_path / "reference_bounds.json"
    bounds.write_text(json.dumps({"center_xy_m": [0.31, 0.10]}))

    result = module.build_fixture(
        container_package=package,
        output=tmp_path / "out",
        particle_seed=seed,
        particle_seed_bounds=bounds,
    )

    assert result["particle_count"] == 2


def test_fixture_authors_scaled_particle_contact_offset(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "container"
    package.mkdir()
    (package / "asset.usd").write_text("#usda 1.0\n")
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/GraduatedCylinder250ml",
                "collision": {
                    "root_prim": "/World/GraduatedCylinder250ml/Collision",
                    "contact_offset_m": 0.004,
                },
            }
        )
    )

    module.build_fixture(
        container_package=package,
        output=tmp_path / "out",
        particle_contact_offset_m=0.0025,
    )

    component = (tmp_path / "out/component.usda").read_text()
    fixture = json.loads((tmp_path / "out/fixture_profile.json").read_text())
    assert "float particleContactOffset = 0.0025" in component
    assert fixture["particle_parameters"]["particle_contact_offset_m"] == 0.0025
