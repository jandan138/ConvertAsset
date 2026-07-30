from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.build_centrifuge_identity_root_facade_r9 import (
    BENCHTOP_SUPPORT_COLLIDER,
    MINIMUM_COM_SUPPORT_MARGIN_M,
    TARGET_COM_SUPPORT_MARGIN_M,
    _build,
    _plan_support_bounds,
    _rebind_physics_profile,
    _support_margins,
)


REAL_R8_ROOT = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/outputs/centrifuge_identity_root_r8"
)


def test_support_plan_uses_composed_visual_contact_footprint_not_literal_scale() -> None:
    # These are the composed world AABB edges of the low visual feet, not the
    # misleading parent-local Cube scale from r8.
    existing_minimum = [-0.147352, -0.160225, 0.000002]
    existing_maximum = [0.096379, 0.166912, 0.011095]
    combined_com = [0.011256, 0.0, 0.103633]

    minimum, maximum = _plan_support_bounds(
        existing_minimum,
        existing_maximum,
        combined_com,
        support_plane_z_m=0.0,
    )

    assert minimum == pytest.approx([-0.147352, -0.160225, 0.0])
    assert maximum == pytest.approx([0.096379, 0.166912, 0.008])
    assert maximum[0] - minimum[0] > 0.20
    assert maximum[1] - minimum[1] > 0.30
    margins = _support_margins(minimum, maximum, combined_com)
    assert min(margins.values()) >= MINIMUM_COM_SUPPORT_MARGIN_M
    assert margins["positive_x_m"] > TARGET_COM_SUPPORT_MARGIN_M


def test_physics_rebind_changes_only_source_identity_and_profile_revision() -> None:
    source = {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": "centrifuge.identity-root-r8",
        "revision": "r1-identity-root",
        "source_binding": {
            "sha256": "a" * 64,
            "stage_metrics": {"up_axis": "Z", "meters_per_unit": 1.0},
        },
        "scope_rules": [
            {
                "scope_path": "/World/Centrifuge",
                "body_rules": [
                    {
                        "relative_path": "group_0",
                        "mass_properties": {
                            "mass_kg": 5.0,
                            "center_of_mass_body_local": [0.0, 0.0, 0.0804],
                            "diagonal_inertia_kg_m2": [0.06, 0.05, 0.09],
                            "principal_axes": [1.0, 0.0, 0.0, 0.0],
                        },
                    }
                ],
            }
        ],
    }
    before = deepcopy(source)

    rebound = _rebind_physics_profile(source, source_sha256="b" * 64)

    assert source == before
    assert rebound["source_binding"]["sha256"] == "b" * 64
    assert rebound["profile_id"] == "centrifuge.identity-root-r8.benchtop-r9"
    assert rebound["revision"] == "r2-benchtop-support"
    assert rebound["scope_rules"] == before["scope_rules"]
    assert rebound["source_binding"]["stage_metrics"] == before["source_binding"][
        "stage_metrics"
    ]


def test_world_aligned_support_ops_match_the_r8_signed_axis_permutation() -> None:
    Gf = pytest.importorskip("pxr.Gf")
    from scripts.build_centrifuge_identity_root_facade_r9 import (
        _world_aligned_cube_parent_local_ops,
    )

    parent_world = Gf.Matrix4d(
        0.0,
        0.175,
        0.0,
        0.0,
        0.0,
        0.0,
        0.175,
        0.0,
        0.175,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.103633,
        1.0,
    )

    translation, scale = _world_aligned_cube_parent_local_ops(
        parent_world,
        world_minimum=[-0.04, -0.05, 0.0],
        world_maximum=[0.03, 0.05, 0.008],
        gf=Gf,
    )

    assert translation == pytest.approx([0.0, -0.5693314286, -0.0285714286])
    assert scale == pytest.approx(
        [0.1 / 0.175, 0.008 / 0.175, 0.07 / 0.175]
    )


@pytest.mark.skipif(
    not (REAL_R8_ROOT / "facade/facade.usda").is_file(),
    reason="real r8 delivery is not available in this checkout",
)
def test_real_r8_repair_measures_composed_support_world_aabb(
    tmp_path: Path,
) -> None:
    Usd = pytest.importorskip("pxr.Usd")
    UsdGeom = pytest.importorskip("pxr.UsdGeom")
    source = REAL_R8_ROOT / "facade/facade.usda"
    source_sha_before = sha256(source.read_bytes()).hexdigest()
    out_root = tmp_path / "r9"

    result = _build(
        argparse.Namespace(
            r8_facade=source,
            r8_provenance=REAL_R8_ROOT / "facade/facade_provenance.json",
            r8_physics=REAL_R8_ROOT / "centrifuge.physics.json",
            out_root=out_root,
        )
    )

    measurement = json.loads(
        (
            out_root / "facade/benchtop_support_measurement.json"
        ).read_text(encoding="utf-8")
    )
    contact = measurement["composed_visual_contact_footprint_m"]
    assert contact["max"][0] - contact["min"][0] > 0.20
    assert contact["max"][1] - contact["min"][1] > 0.30
    assert min(measurement["com_projection_margins"].values()) >= (
        MINIMUM_COM_SUPPORT_MARGIN_M
    )
    stage = Usd.Stage.Open(result["facade"])
    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_],
    )
    bound = cache.ComputeWorldBound(
        stage.GetPrimAtPath(BENCHTOP_SUPPORT_COLLIDER)
    ).ComputeAlignedBox()
    assert list(bound.GetMin()) == pytest.approx(
        measurement["world_bounds_m"]["min"]
    )
    assert list(bound.GetMax()) == pytest.approx(
        measurement["world_bounds_m"]["max"]
    )
    assert sha256(source.read_bytes()).hexdigest() == source_sha_before
