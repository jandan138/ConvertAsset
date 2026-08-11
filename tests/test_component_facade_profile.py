from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.component_facade import (
    ComponentFacadeProfileError,
    build_component_facade,
)


def _write_source(path: Path) -> None:
    path.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{
    def Xform "table"
    {
        def Cube "body"
        {
            double size = 1
        }
        def Cube "surface"
        {
            double size = 1
        }
    }
}
""",
        encoding="utf-8",
    )


def _write_profile(path: Path, source: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "aan.component_facade_profile.v1",
                "source": {
                    "sha256": sha256(source.read_bytes()).hexdigest(),
                    "expected_up_axis": "Z",
                    "expected_meters_per_unit": 1.0,
                },
                "entry": {"prim_path": "/World/table", "require_identity": True},
                "components": [
                    {
                        "name": "Body",
                        "source_prim_path": "/World/table/body",
                        "target_bounds_m": {
                            "min": [-0.8, -0.325, 0.0],
                            "max": [0.8, 0.325, 0.715],
                        },
                    },
                    {
                        "name": "Surface",
                        "source_prim_path": "/World/table/surface",
                        "target_bounds_m": {
                            "min": [-1.0, -0.4, 0.715],
                            "max": [1.0, 0.4, 0.755],
                        },
                    },
                ],
                "geometry_claim": {
                    "status": "measured_geometry",
                    "size_m": [2.0, 0.8, 0.755],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_component_facade_has_identity_entry_and_exact_bounds(tmp_path: Path) -> None:
    from pxr import Usd, UsdGeom

    source = tmp_path / "source.usda"
    profile = tmp_path / "profile.json"
    _write_source(source)
    _write_profile(profile, source)

    result = build_component_facade(source, tmp_path / "out", profile)

    stage = Usd.Stage.Open(str(result.facade_path))
    assert stage
    entry = stage.GetPrimAtPath("/World/table")
    assert UsdGeom.Xformable(entry).GetOrderedXformOps() == []
    bbox = (
        UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        .ComputeWorldBound(entry)
        .ComputeAlignedRange()
    )
    assert tuple(bbox.GetMin()) == pytest.approx((-1.0, -0.4, 0.0), abs=1e-6)
    assert tuple(bbox.GetMax()) == pytest.approx((1.0, 0.4, 0.755), abs=1e-6)

    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    assert provenance["entry"]["identity_transform"] is True
    assert provenance["final_bounds_m"]["size"] == pytest.approx([2.0, 0.8, 0.755])
    assert [item["name"] for item in provenance["components"]] == ["Body", "Surface"]


def test_component_facade_rejects_source_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    profile = tmp_path / "profile.json"
    _write_source(source)
    _write_profile(profile, source)
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload["source"]["sha256"] = "0" * 64
    profile.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ComponentFacadeProfileError, match="SHA-256"):
        build_component_facade(source, tmp_path / "out", profile)
