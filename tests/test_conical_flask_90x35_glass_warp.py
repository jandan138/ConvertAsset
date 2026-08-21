from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_conical_flask_90x35_glass_warp import (
    ENTRY_PRIM,
    IDENTITY_FACADE_SHA256,
    IDENTITY_PACKAGE,
    K_H,
    TARGET_BELLY_OD_MM,
    TARGET_HEIGHT_MM,
    TARGET_INNER_MOUTH_MM,
    Z_BELLY_M,
    Z_MOUTH_M,
    build,
    measure_flask_mm,
    radial_scale,
    warp_points,
)


IDENTITY_FACADE = IDENTITY_PACKAGE / "facade" / "facade.usda"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_radial_scale_hits_belly_and_mouth_anchors() -> None:
    assert radial_scale(Z_BELLY_M) == pytest.approx(90.0 / 113.3053223)
    assert radial_scale(Z_MOUTH_M) == pytest.approx(35.0 / 49.19089655)
    assert K_H == pytest.approx(150.0 / 196.5674179)


def test_synthetic_ring_mesh_hits_90_35_150_after_warp() -> None:
    rings = [
        (0.05665266115, 0.0, Z_BELLY_M),
        (0.0, 0.05665266115, Z_BELLY_M),
        (0.024595448275, 0.0, Z_MOUTH_M),
        (0.0, 0.024595448275, Z_MOUTH_M),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.1965674179),
    ]
    warped = warp_points(rings)
    measured = measure_flask_mm(warped, belly_z_m=Z_BELLY_M * K_H, mouth_z_m=Z_MOUTH_M * K_H)

    assert measured["belly_od_mm"] == pytest.approx(TARGET_BELLY_OD_MM, abs=1.0)
    assert measured["inner_mouth_mm"] == pytest.approx(TARGET_INNER_MOUTH_MM, abs=1.0)
    assert measured["height_mm"] == pytest.approx(TARGET_HEIGHT_MM, abs=1.0)


def test_builder_keeps_identity_package_hash_and_identity_root_scale(tmp_path: Path) -> None:
    assert IDENTITY_FACADE.is_file()
    assert _sha256(IDENTITY_FACADE) == IDENTITY_FACADE_SHA256
    before = _tree_hashes(IDENTITY_PACKAGE)

    result = build(source_package=IDENTITY_PACKAGE, out=tmp_path)

    assert _tree_hashes(IDENTITY_PACKAGE) == before
    assert _sha256(IDENTITY_FACADE) == IDENTITY_FACADE_SHA256

    facade = result["facade"].read_text(encoding="utf-8")
    interaction = json.loads(result["interaction"].read_text(encoding="utf-8"))
    physics = json.loads(result["physics"].read_text(encoding="utf-8"))
    provenance = json.loads(result["manifest"].read_text(encoding="utf-8"))
    entry_header, visual = facade.split('def Xform "ConicalFlask90x35Warp"', 1)[1].split(
        'def Xform "Visual"', 1
    )

    assert 'def Xform "World"' in facade
    assert "xformOp:" not in entry_header
    assert "xformOp:scale" not in visual.split("{", 1)[0]
    assert result["baked"].name in facade
    assert interaction["asset_entry_prim"] == ENTRY_PRIM
    assert interaction["named_frames"]["support"]["translation_body_local_usd"] == [0.0, 0.0, 0.0]
    assert interaction["named_frames"]["opening"]["translation_body_local_usd"][2] == pytest.approx(0.15)
    assert interaction["colliders"][0]["mode"] == "preserve"
    assert interaction["colliders"][0]["approximation"] == "sdf"
    assert interaction["open_top"]["required"] is True
    assert physics["scope_rules"][0]["scope_path"] == ENTRY_PRIM
    assert provenance["bake"]["root_scale"] == [1.0, 1.0, 1.0]
    assert provenance["bake"]["method"] == "axisymmetric_krz_and_kh"
    assert provenance["source"]["unchanged"] is True
    baked_text = result["baked"].read_text(encoding="utf-8")
    assert "OmniSurface_Glass" in baked_text
    assert "PhysicsCollisionAPI" in baked_text
    assert 'uniform token physics:approximation = "sdf"' in baked_text


def test_warped_facade_mesh_measures_within_one_mm(tmp_path: Path) -> None:
    result = build(source_package=IDENTITY_PACKAGE, out=tmp_path)
    measured = measure_flask_mm(
        result["warped_points"],
        belly_z_m=Z_BELLY_M * K_H,
        mouth_z_m=Z_MOUTH_M * K_H,
    )

    assert measured["belly_od_mm"] == pytest.approx(TARGET_BELLY_OD_MM, abs=1.0)
    assert measured["inner_mouth_mm"] == pytest.approx(TARGET_INNER_MOUTH_MM, abs=1.0)
    assert measured["height_mm"] == pytest.approx(TARGET_HEIGHT_MM, abs=1.0)
    assert measured["opening_mm"] == pytest.approx(TARGET_HEIGHT_MM, abs=1.0)
