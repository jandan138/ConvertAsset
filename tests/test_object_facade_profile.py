from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.object_facade import (
    ObjectFacadeProfileError,
    build_object_facade,
)


def _write_source(path: Path) -> None:
    path.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 0.01
    upAxis = "Y"
)

def Xform "World"
{
    double3 xformOp:translate = (3, 4, 5)
    uniform token[] xformOpOrder = ["xformOp:translate"]

    def Cube "Mesh"
    {
        double size = 2
    }
}
""",
        encoding="utf-8",
    )


def _write_profile(path: Path, source: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "aan.object_facade_profile.v1",
                "source": {
                    "sha256": sha256(source.read_bytes()).hexdigest(),
                    "prim_path": "/World",
                    "expected_up_axis": "Y",
                    "expected_meters_per_unit": 0.01,
                },
                "entry": {
                    "prim_path": "/World/Beaker",
                    "visual_child_name": "Visual",
                    "require_identity": True,
                },
                "normalization": {
                    "rotation_wxyz": [0.7071067811865476, 0.7071067811865475, 0, 0],
                    "uniform_scale": 0.05,
                    "support_plane_z_m": 0.0,
                    "target_up_axis": "Z",
                    "target_meters_per_unit": 1.0,
                },
                "geometry_claim": {
                    "status": "provisional_geometry",
                    "basis": "task-compatible nominal envelope",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_object_facade_has_identity_entry_and_support_plane(tmp_path: Path) -> None:
    from pxr import Usd, UsdGeom

    source = tmp_path / "source.usda"
    profile = tmp_path / "profile.json"
    _write_source(source)
    _write_profile(profile, source)

    result = build_object_facade(source, tmp_path / "out", profile)

    stage = Usd.Stage.Open(str(result.facade_path))
    assert stage
    assert stage.GetDefaultPrim().GetPath().pathString == "/World"
    entry = stage.GetPrimAtPath("/World/Beaker")
    assert entry
    assert UsdGeom.Xformable(entry).GetOrderedXformOps() == []
    bbox = (
        UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        .ComputeWorldBound(entry)
        .ComputeAlignedRange()
    )
    assert bbox.GetMin()[2] == pytest.approx(0.0, abs=1e-6)
    assert (bbox.GetMin()[0] + bbox.GetMax()[0]) / 2.0 == pytest.approx(0.0, abs=1e-6)
    assert (bbox.GetMin()[1] + bbox.GetMax()[1]) / 2.0 == pytest.approx(0.0, abs=1e-6)

    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    assert provenance["profile"]["schema_version"] == "aan.object_facade_profile.v1"
    assert provenance["source"]["sha256"] == sha256(source.read_bytes()).hexdigest()
    assert provenance["entry"]["identity_transform"] is True
    assert provenance["normalization"]["centered_on_entry_xy"] is True
    assert stage.GetPrimAtPath("/World/Beaker/Visual/Source")
    assert provenance["geometry_claim"]["status"] == "provisional_geometry"


def test_object_facade_rejects_source_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    profile = tmp_path / "profile.json"
    _write_source(source)
    _write_profile(profile, source)
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload["source"]["sha256"] = "0" * 64
    profile.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ObjectFacadeProfileError, match="SHA-256"):
        build_object_facade(source, tmp_path / "out", profile)
