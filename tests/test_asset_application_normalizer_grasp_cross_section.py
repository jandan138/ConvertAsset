"""TDD coverage for source-bound grasp-section collision admission."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.grasp_cross_section import (
    evaluate_grasp_cross_section,
)
from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.pipeline import normalize_asset


_ASSET_PATH = "/World/Asset"
_GRASP_Y = 0.14
_VISUAL_DIAMETER_M = 0.04701


def _cylinder_mesh_usda() -> str:
    """Return a 12-sided visual tube in millimetre mesh coordinates.

    The parent root rotates in world and the mesh has a 1e-4 scale.  A checker
    that slices world-Y or reads raw point coordinates will therefore measure
    the wrong section/units.
    """

    # The mesh's declared 1e-4 scale intentionally makes these raw values
    # differ from metres.  The physical section is still 47.01 mm wide.
    radius_mm = _VISUAL_DIAMETER_M * 10000.0 / 2.0
    lower_y_mm = 1000.0
    upper_y_mm = 1800.0
    points: list[str] = []
    for y in (lower_y_mm, upper_y_mm):
        for index in range(12):
            angle = 2.0 * math.pi * index / 12.0
            points.append(
                "(%0.9f, %0.9f, %0.9f)"
                % (radius_mm * math.cos(angle), y, radius_mm * math.sin(angle))
            )
    indices: list[int] = []
    for index in range(12):
        next_index = (index + 1) % 12
        lower = index
        lower_next = next_index
        upper = 12 + index
        upper_next = 12 + next_index
        indices.extend((lower, lower_next, upper, lower, upper, upper_next))
    return """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    timeCodesPerSecond = 60
    framesPerSecond = 24
)
def Xform "World"
{
    def Xform "Asset"
    {
        double3 xformOp:rotateXYZ = (90, 0, 0)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]

        def Mesh "mesh"
        {
            point3f[] points = [%s]
            int[] faceVertexCounts = [%s]
            int[] faceVertexIndices = [%s]
            double3 xformOp:scale = (0.0001, 0.0001, 0.0001)
            uniform token[] xformOpOrder = ["xformOp:scale"]
        }
    }
}
""" % (
        ", ".join(points),
        ", ".join("3" for _ in range(24)),
        ", ".join(str(item) for item in indices),
    )


def _cube_usda(
    name: str,
    *,
    translation: tuple[float, float, float],
    rotation_y_deg: float,
    scale: tuple[float, float, float],
    collision_enabled: bool = True,
) -> str:
    return """        def Cube \"%s\" (
            prepend apiSchemas = [\"PhysicsCollisionAPI\"]
        )
        {
            float size = 1
            bool physics:collisionEnabled = %s
            double3 xformOp:translate = (%0.12f, %0.12f, %0.12f)
            double xformOp:rotateY = %0.12f
            double3 xformOp:scale = (%0.12f, %0.12f, %0.12f)
            uniform token[] xformOpOrder = [\"xformOp:translate\", \"xformOp:rotateY\", \"xformOp:scale\"]
        }
""" % (
        name,
        "true" if collision_enabled else "false",
        *translation,
        rotation_y_deg,
        *scale,
    )


def _package_usda(
    source: Path,
    *,
    wall_center_radius_m: float,
    wall_tangent_width_m: float,
    base_center_y_m: float = 0.003,
    include_unknown_active_mesh: bool = False,
) -> str:
    cubes = [
        _cube_usda(
            "bottom",
            translation=(0.0, base_center_y_m, 0.0),
            rotation_y_deg=0.0,
            scale=(0.1171587, 0.006, 0.1171587),
        )
    ]
    for index in range(12):
        angle = 2.0 * math.pi * index / 12.0
        cubes.append(
            _cube_usda(
                f"wall_{index:02d}",
                translation=(
                    wall_center_radius_m * math.cos(angle),
                    _GRASP_Y,
                    wall_center_radius_m * math.sin(angle),
                ),
                rotation_y_deg=-math.degrees(angle),
                scale=(0.004, 0.20, wall_tangent_width_m),
            )
        )
    unknown = """
        def Mesh "unknown_active_mesh" (
            prepend apiSchemas = ["PhysicsCollisionAPI"]
        )
        {
            bool physics:collisionEnabled = true
            point3f[] points = [(0, 0.12, 0), (0.01, 0.12, 0), (0, 0.16, 0)]
            int[] faceVertexCounts = [3]
            int[] faceVertexIndices = [0, 1, 2]
        }
""" if include_unknown_active_mesh else ""
    return """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    timeCodesPerSecond = 60
    framesPerSecond = 24
    subLayers = [@%s@]
)
over "World"
{
    over "Asset"
    {
        def Xform "__aan_collision_proxy"
        {
%s%s        }
    }
}
""" % (source.as_posix(), "".join(cubes), unknown)


def _config() -> dict[str, object]:
    return {
        "required": True,
        "frame": "grasp",
        "axis_body_local": [0.0, 1.0, 0.0],
        "sample_offsets_body_local_usd": [-0.002, 0.0, 0.002],
        "source_visual_mesh_relative_paths": ["mesh"],
        "closing_axis_body_local": [1.0, 0.0, 0.0],
        "expected_visual_width_m": _VISUAL_DIAMETER_M,
        "visual_width_tolerance_m": 0.0005,
        "collision_visual_width_tolerance_m": 0.003,
        "max_gripper_opening_m": 0.088,
        "minimum_opening_clearance_m": 0.001,
        "claim_boundary": "Static geometry preflight is not an EOS/GenManip grasp claim.",
    }


def _declared_colliders() -> list[dict[str, object]]:
    return [
        {
            "prim_path": f"{_ASSET_PATH}/__aan_collision_proxy/bottom",
            "purpose": ["support", "containment"],
        },
        *[
            {
                "prim_path": f"{_ASSET_PATH}/__aan_collision_proxy/wall_{index:02d}",
                "purpose": ["gripper", "containment"],
            }
            for index in range(12)
        ],
    ]


def _evaluate(
    source: Path,
    package: Path,
) -> dict[str, object]:
    return evaluate_grasp_cross_section(
        source_usd=source,
        package_usd=package,
        asset_entry_prim=_ASSET_PATH,
        grasp_cross_section=_config(),
        named_frames={
            "grasp": {
                "translation_body_local_usd": [0.0, _GRASP_Y, 0.0],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            }
        },
        declared_colliders=_declared_colliders(),
    )


def _write_package(
    tmp_path: Path,
    *,
    wall_center_radius_m: float,
    wall_tangent_width_m: float,
    base_center_y_m: float = 0.003,
    include_unknown_active_mesh: bool = False,
) -> tuple[Path, Path]:
    source = tmp_path / "source.usda"
    source.write_text(_cylinder_mesh_usda(), encoding="utf-8")
    package = tmp_path / "package.usda"
    package.write_text(
        _package_usda(
            source,
            wall_center_radius_m=wall_center_radius_m,
            wall_tangent_width_m=wall_tangent_width_m,
            base_center_y_m=base_center_y_m,
            include_unknown_active_mesh=include_unknown_active_mesh,
        ),
        encoding="utf-8",
    )
    return source, package


def test_grasp_cross_section_rejects_r2_scale_proxy_in_body_local_metric_space(
    tmp_path: Path,
) -> None:
    source, package = _write_package(
        tmp_path,
        wall_center_radius_m=0.0555,
        wall_tangent_width_m=0.03,
    )

    report = _evaluate(source, package)

    assert report["status"] == "blocked"
    assert report["algorithm_id"] == "aan.grasp_cross_section.v1"
    samples = report["samples"]
    assert isinstance(samples, list) and len(samples) == 3
    center = samples[1]
    assert center["source_visual"]["max_in_plane_width_m"] == pytest.approx(
        _VISUAL_DIAMETER_M, abs=1.0e-5
    )
    assert center["source_visual"]["closing_axis_width_m"] == pytest.approx(
        _VISUAL_DIAMETER_M, abs=1.0e-5
    )
    assert center["collision"]["max_in_plane_width_m"] > 0.115
    assert center["checks"]["collision_within_max_gripper_opening"] is False
    assert report["summary"]["support_colliders_intersect_grasp_band"] == []


def test_grasp_cross_section_accepts_narrow_tube_with_wide_low_support_base(
    tmp_path: Path,
) -> None:
    source, package = _write_package(
        tmp_path,
        wall_center_radius_m=0.021505,
        wall_tangent_width_m=0.0112,
    )

    report = _evaluate(source, package)

    assert report["status"] == "pass"
    center = report["samples"][1]
    assert center["package_visual"]["max_in_plane_width_m"] == pytest.approx(
        _VISUAL_DIAMETER_M, abs=1.0e-5
    )
    assert center["collision"]["closing_axis_width_m"] == pytest.approx(
        _VISUAL_DIAMETER_M, abs=1.0e-5
    )
    assert center["collision"]["max_in_plane_width_m"] < 0.051
    assert center["checks"]["collision_matches_visual"] is True
    assert center["checks"]["collision_within_max_gripper_opening"] is True
    assert report["summary"]["support_colliders_intersect_grasp_band"] == []


def test_grasp_cross_section_blocks_support_collider_that_enters_grasp_band(
    tmp_path: Path,
) -> None:
    source, package = _write_package(
        tmp_path,
        wall_center_radius_m=0.021505,
        wall_tangent_width_m=0.0112,
        base_center_y_m=_GRASP_Y,
    )

    report = _evaluate(source, package)

    assert report["status"] == "blocked"
    assert report["summary"]["support_colliders_intersect_grasp_band"] == [
        f"{_ASSET_PATH}/__aan_collision_proxy/bottom"
    ]


def test_grasp_cross_section_fails_closed_for_unknown_active_collision_geometry(
    tmp_path: Path,
) -> None:
    source, package = _write_package(
        tmp_path,
        wall_center_radius_m=0.021505,
        wall_tangent_width_m=0.0112,
        include_unknown_active_mesh=True,
    )

    report = _evaluate(source, package)

    assert report["status"] == "blocked"
    assert report["summary"]["unsupported_active_collision_prims"] == [
        f"{_ASSET_PATH}/__aan_collision_proxy/unknown_active_mesh"
    ]


def _interaction_profile(
    source: Path,
    profile: Path,
    *,
    wall_center_radius_m: float,
    wall_tangent_width_m: float,
) -> Path:
    source_hash = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
    colliders: list[dict[str, object]] = [
        {"relative_path": "mesh", "mode": "disable", "purpose": []},
        {
            "relative_path": "__aan_collision_proxy/bottom",
            "mode": "author",
            "purpose": ["support", "containment"],
            "geometry": {
                "type": "Cube",
                "size": 1.0,
                "translation_body_local_usd": [0.0, 0.003, 0.0],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "scale_body_local_usd": [0.1171587, 0.006, 0.1171587],
            },
        },
    ]
    for index in range(12):
        angle = 2.0 * math.pi * index / 12.0
        colliders.append(
            {
                "relative_path": f"__aan_collision_proxy/wall_{index:02d}",
                "mode": "author",
                "purpose": ["gripper", "containment"],
                "geometry": {
                    "type": "Cube",
                    "size": 1.0,
                    "translation_body_local_usd": [
                        wall_center_radius_m * math.cos(angle),
                        0.14,
                        wall_center_radius_m * math.sin(angle),
                    ],
                    "rotation_body_local_wxyz": [
                        math.cos(angle / 2.0),
                        0.0,
                        -math.sin(angle / 2.0),
                        0.0,
                    ],
                    "scale_body_local_usd": [0.004, 0.16, wall_tangent_width_m],
                },
            }
        )
    profile.write_text(
        json.dumps(
            {
                "schema_version": "aan.object_interaction_profile.v1",
                "profile_id": "tests.grasp-section",
                "revision": "r3",
                "source_binding": {
                    "sha256": source_hash,
                    "stage_metrics": {
                        "meters_per_unit": 1.0,
                        "kilograms_per_unit": 1.0,
                        "up_axis": "Z",
                        "time_codes_per_second": 60.0,
                        "frames_per_second": 24.0,
                    },
                },
                "asset_entry_prim": _ASSET_PATH,
                "rigid_root": {
                    "motion_role": "dynamic",
                    "disable_descendant_rigid_bodies": True,
                    "remove_descendant_mass_api": True,
                },
                "colliders": colliders,
                "open_top": {
                    "required": True,
                    "axis_body_local": [0.0, 1.0, 0.0],
                    "aperture_frame": "opening",
                    "evidence": {
                        "status": "declared",
                        "method": "fixture_open_top_intent",
                        "claim_boundary": "Static intent requires a cooked aperture probe.",
                    },
                },
                "named_frames": {
                    "opening": {
                        "translation_body_local_usd": [0.0, 0.18, 0.0],
                        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                    },
                    "grasp": {
                        "translation_body_local_usd": [0.0, _GRASP_Y, 0.0],
                        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                    },
                    "support": {
                        "translation_body_local_usd": [0.0, 0.0, 0.0],
                        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                    },
                },
                "grasp_cross_section": _config(),
                "runtime_gates": {
                    "root_motion": {"required": True, "min_translation_m": 0.01},
                    "stable_support": {"required": True},
                    "gripper_collision": {"required": True},
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return profile


def _physics_profile(source: Path, profile: Path) -> Path:
    source_hash = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
    profile.write_text(
        json.dumps(
            {
                "schema_version": "aan.physics_profile.v1",
                "profile_id": "tests.grasp-section-mass",
                "revision": "r1",
                "source_binding": {
                    "sha256": source_hash,
                    "stage_metrics": {
                        "meters_per_unit": 1.0,
                        "kilograms_per_unit": 1.0,
                        "up_axis": "Z",
                        "time_codes_per_second": 60.0,
                        "frames_per_second": 24.0,
                    },
                },
                "evidence": {
                    "parameter_status": "provisional_geometry",
                    "claim_boundary": "Fixture mass is not a measurement.",
                    "replacement_contract": "Replace the source-bound bundle in a new revision.",
                },
                "scope_rules": [
                    {
                        "scope_path": _ASSET_PATH,
                        "body_rules": [
                            {
                                "relative_path": ".",
                                "motion_role": "dynamic",
                                "clear_density": True,
                                "mass_properties": {
                                    "mode": "explicit",
                                    "quality_tier": "provisional_geometry",
                                    "mass_kg": 0.15,
                                    "diagonal_inertia_kg_m2": [0.001, 0.001, 0.001],
                                    "center_of_mass_body_local": [0.0, 0.09, 0.0],
                                    "principal_axes": [1.0, 0.0, 0.0, 0.0],
                                },
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return profile


@pytest.mark.parametrize(
    ("wall_center_radius_m", "wall_tangent_width_m", "expected_status"),
    [
        (0.021505, 0.0112, "pass"),
        (0.0555, 0.03, "blocked"),
    ],
    ids=["r3-narrow-tube", "r2-wide-wall-regression"],
)
def test_pipeline_emits_package_bound_grasp_section_gate_without_changing_interaction_contract_abi(
    tmp_path: Path,
    wall_center_radius_m: float,
    wall_tangent_width_m: float,
    expected_status: str,
) -> None:
    source = tmp_path / "source.usda"
    # This integration fixture needs an inherited source collision to exercise
    # profile-owned disabling before the Cube-only static measurement.
    source.write_text(
        _cylinder_mesh_usda().replace(
            '        def Mesh "mesh"\n        {',
            '        def Mesh "mesh" (\n'
            '            prepend apiSchemas = ["PhysicsCollisionAPI"]\n'
            '        )\n'
            '        {\n'
            '            bool physics:collisionEnabled = 1',
        ),
        encoding="utf-8",
    )
    original_hash = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
    interaction = _interaction_profile(
        source,
        tmp_path / "interaction.json",
        wall_center_radius_m=wall_center_radius_m,
        wall_tangent_width_m=wall_tangent_width_m,
    )
    physics = _physics_profile(source, tmp_path / "physics.json")
    out_dir = tmp_path / "package"
    manifest_path = tmp_path / "manifest.json"

    result = normalize_asset(
        NormalizeAssetRequest(
            source_usd=source,
            out_dir=out_dir,
            asset_id="grasp-section-fixture",
            asset_class="rigid",
            asset_role="dynamic",
            source_runtime="isaac51",
            target_runtime="isaac41",
            target_benchmark="scenario-forge",
            task_id="AAN.GraspSection",
            required_prims=[_ASSET_PATH],
            asset_scope_prims=[_ASSET_PATH],
            gates=["static"],
            evidence_out=manifest_path,
            physics_profile=physics,
            interaction_profile=interaction,
        )
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cross_section = manifest["physics_closure"]["grasp_cross_section"]
    assert result.overall_status == expected_status
    assert cross_section["status"] == expected_status
    gate = next(
        item
        for item in manifest["stage_gates"]
        if item["check_id"] == "AAN-05G-grasp-cross-section"
    )
    assert gate["status"] == expected_status
    assert __import__("hashlib").sha256(source.read_bytes()).hexdigest() == original_hash
    if expected_status == "pass":
        assert result.return_code == 0
        assert cross_section["report_path"] == "interaction/grasp_cross_section.json"
        report = out_dir / cross_section["report_path"]
        assert report.is_file()
        assert __import__("hashlib").sha256(report.read_bytes()).hexdigest() == cross_section[
            "report_sha256"
        ]
        contract = manifest["interaction_contract"]
        assert set(contract) == {
            "schema_version",
            "status",
            "profile",
            "asset_entry_prim",
            "runtime_identity",
            "disabled_source_rigid_bodies",
            "collider_prims",
            "open_top",
            "named_frames",
            "closure",
            "root_motion_gate",
            "stable_support_gate",
            "gripper_collision_gate",
        }
        assert "interaction/grasp_cross_section.json" in {
            item["path"] for item in contract["closure"]["artifacts"]
        }
    else:
        assert result.return_code == 5
