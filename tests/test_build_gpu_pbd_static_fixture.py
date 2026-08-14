from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path


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
