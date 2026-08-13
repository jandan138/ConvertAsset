from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest

from convert_asset.asset_application_normalizer.interactive_fluid_scene import (
    InteractiveFluidSceneProfileError,
    load_interactive_fluid_scene_profile,
)


def _profile(tmp_path: Path) -> dict[str, object]:
    points = tmp_path / "points.json"
    points.write_text(json.dumps([[0.0, 0.0, 0.01], [0.0, 0.0, 0.02]]))
    return {
        "schema_version": "aan.interactive_fluid_scene_profile.v1",
        "profile_id": "example.fluid.v1",
        "revision": "v1",
        "runtime_profile": "isaac41",
        "component_root_prim": "/World/FluidWorkcell",
        "members": {
            "source_container": "/World/FluidWorkcell/SourceContainer",
            "target_container": "/World/FluidWorkcell/TargetContainer",
            "particle_system": "/World/FluidWorkcell/ParticleSystem",
            "particles": "/World/FluidWorkcell/ParticleSet",
        },
        "particles": {
            "kind": "PhysX_PBD",
            "count": 2,
            "authored_points_path": points.name,
            "authored_points_sha256": "AUTO",
            "display": "physx_isosurface",
        },
        "container_collision": {
            "strategy": "visual_mesh_convex_decomposition",
            "disable_existing_proxy_paths": [
                "/World/FluidWorkcell/SourceContainer/__aan_collision_proxy"
            ],
            "meshes": [
                {
                    "prim_path": "/World/FluidWorkcell/SourceContainer/Visual/HollowBody",
                    "approximation": "convexDecomposition",
                    "error_percentage": 0.01,
                }
            ],
        },
        "entrypoints": {
            "qualification_30hz": {"path": "qualification_30hz.usda", "physics_hz": 30},
            "consumer_60hz": {"path": "consumer_60hz.usda", "physics_hz": 60},
        },
        "classification_regions": {
            "source": {"kind": "cylinder", "radius_m": 0.02, "height_m": 0.25},
            "target": {"kind": "cylinder", "radius_m": 0.04, "height_m": 0.11},
        },
        "qualification": {
            "static_hold_seconds": 8.0,
            "minimum_source_retention_ratio": 0.8,
            "maximum_below_support_count": 0,
            "minimum_peak_target_ratio": 0.05,
            "performance": {
                "width": 960,
                "height": 540,
                "minimum_rtx_fps": 40.0,
                "required_repeats": 1,
                "gpu": "NVIDIA GeForce RTX 4090",
            },
        },
        "allowed_consumer_composition": [
            "visual_static_environment",
            "static_support",
            "robot_config_injection",
        ],
    }


def _profile_v2(tmp_path: Path) -> dict[str, object]:
    payload = _profile(tmp_path)
    payload["schema_version"] = "aan.interactive_fluid_scene_profile.v2"
    payload["profile_id"] = "example.fluid.v2"
    payload["revision"] = "r8.1"
    payload["container_collision"] = {
        "strategy": "visual_mesh_partitioned_convex_decomposition",
        "disable_existing_proxy_paths": [
            "/World/FluidWorkcell/SourceContainer/__aan_collision_proxy"
        ],
        "partition_candidates": [12, 24, 48],
        "selected_partition_count": 24,
        "source_visual_mesh": (
            "/World/FluidWorkcell/SourceContainer/Visual/HollowBody"
        ),
        "meshes": [
            {
                "prim_path": (
                    "/World/FluidWorkcell/SourceContainer/"
                    "VisibleCollisionPartitions/sector_000"
                ),
                "approximation": "convexDecomposition",
                "error_percentage": 10.0,
                "render_visible": True,
                "source_face_indices": [0, 1],
            },
            {
                "prim_path": (
                    "/World/FluidWorkcell/TargetContainer/Visual/HollowBody"
                ),
                "approximation": "convexDecomposition",
                "error_percentage": 10.0,
                "render_visible": True,
                "source_face_indices": [],
            },
        ],
    }
    payload["qualification"] = {
        "static_hold_seconds": 8.0,
        "minimum_source_retention_ratio": 0.95,
        "maximum_below_support_count": 0,
        "minimum_final_target_ratio": 0.8,
        "maximum_tabletop_spill_ratio": 0.05,
        "required_cold_runs": 3,
        "oracle": {
            "pivot_inside_target_rim_m": 0.025,
            "pivot_above_target_rim_m": 0.06,
            "tilt_axis": "local_y",
            "tilt_degrees": -110.0,
            "tilt_seconds": 3.0,
            "hold_seconds": 3.0,
            "settle_seconds": 2.0,
        },
        "performance": {
            "width": 960,
            "height": 540,
            "minimum_rtx_fps": 40.0,
            "required_repeats": 3,
            "gpu": "NVIDIA GeForce RTX 4090",
        },
    }
    return payload


def test_profile_accepts_arbitrary_fixed_particle_count(tmp_path: Path) -> None:
    payload = _profile(tmp_path)
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(payload))

    profile = load_interactive_fluid_scene_profile(profile_path)

    assert profile.particle_count == 2
    assert profile.entrypoint_hz == {"qualification_30hz": 30, "consumer_60hz": 60}
    assert profile.points_sha256
    assert profile.collision_meshes == (
        "/World/FluidWorkcell/SourceContainer/Visual/HollowBody",
    )


def test_profile_rejects_illegal_convex_error_percentage(tmp_path: Path) -> None:
    payload = _profile(tmp_path)
    payload["container_collision"]["meshes"][0]["error_percentage"] = 0.0  # type: ignore[index]
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(payload))

    with pytest.raises(InteractiveFluidSceneProfileError, match="error_percentage"):
        load_interactive_fluid_scene_profile(profile_path)


def test_profile_rejects_particle_count_or_hash_mismatch(tmp_path: Path) -> None:
    payload = _profile(tmp_path)
    payload["particles"]["count"] = 548  # type: ignore[index]
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(payload))
    with pytest.raises(InteractiveFluidSceneProfileError, match="particle count"):
        load_interactive_fluid_scene_profile(profile_path)

    payload = _profile(tmp_path)
    payload["particles"]["authored_points_sha256"] = "0" * 64  # type: ignore[index]
    profile_path.write_text(json.dumps(payload))
    with pytest.raises(InteractiveFluidSceneProfileError, match="points hash"):
        load_interactive_fluid_scene_profile(profile_path)


def test_profile_rejects_absolute_entrypoint_and_unapproved_composition(tmp_path: Path) -> None:
    payload = _profile(tmp_path)
    payload["entrypoints"]["consumer_60hz"]["path"] = "/tmp/scene.usd"  # type: ignore[index]
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(payload))
    with pytest.raises(InteractiveFluidSceneProfileError, match="package-relative"):
        load_interactive_fluid_scene_profile(profile_path)

    payload = _profile(tmp_path)
    payload["allowed_consumer_composition"] = ["arbitrary_usd_overlay"]
    profile_path.write_text(json.dumps(payload))
    with pytest.raises(InteractiveFluidSceneProfileError, match="composition"):
        load_interactive_fluid_scene_profile(profile_path)


def test_v2_profile_accepts_visible_partitioned_convex_decomposition(
    tmp_path: Path,
) -> None:
    payload = _profile_v2(tmp_path)
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(payload))

    profile = load_interactive_fluid_scene_profile(profile_path)

    assert profile.schema_version.endswith(".v2")
    assert profile.collision_strategy == (
        "visual_mesh_partitioned_convex_decomposition"
    )
    assert profile.selected_partition_count == 24


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda p: p["container_collision"].update(selected_partition_count=16), "partition"),
        (
            lambda p: p["container_collision"]["meshes"][0].update(render_visible=False),
            "render_visible",
        ),
        (lambda p: p["qualification"].update(required_cold_runs=1), "cold runs"),
        (
            lambda p: p["qualification"].update(minimum_final_target_ratio=0.05),
            "target ratio",
        ),
    ],
)
def test_v2_profile_rejects_weaker_or_hidden_partition_contract(
    tmp_path: Path, mutation: Callable[[dict[str, object]], None], message: str
) -> None:
    payload = _profile_v2(tmp_path)
    mutation(payload)
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(payload))

    with pytest.raises(InteractiveFluidSceneProfileError, match=message):
        load_interactive_fluid_scene_profile(profile_path)
