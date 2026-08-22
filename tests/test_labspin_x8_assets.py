from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from scripts.build_labspin_x8_assets import (
    CENTRIFUGE_ENTRY,
    EXISTING_TUBE_ENTRY,
    NATIVE_TUBE_ENTRY,
    build_labspin_x8_assets,
)


SOURCE_ARCHIVE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/离心机.zip"
)


@pytest.mark.skipif(not SOURCE_ARCHIVE.is_file(), reason="local intake archive unavailable")
def test_source_archive_is_exported_asset_bundle_not_generator() -> None:
    with zipfile.ZipFile(SOURCE_ARCHIVE) as archive:
        names = set(archive.namelist())
    assert "assets/usd/centrifuge.usd" in names
    assert "assets/usd/centrifuge_articulated.usda" in names
    assert "assets/usd/tube_body.usd" in names
    assert "assets/usd/tube_cap.usd" in names
    assert not any(name.endswith((".py", ".blend")) for name in names)


@pytest.mark.skipif(not SOURCE_ARCHIVE.is_file(), reason="local intake archive unavailable")
def test_builder_emits_identity_roots_open_sockets_and_profiles(tmp_path: Path) -> None:
    result = build_labspin_x8_assets(SOURCE_ARCHIVE, tmp_path)

    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    centrifuge_stage = Usd.Stage.Open(str(result["centrifuge_asset"]))
    assert centrifuge_stage.GetDefaultPrim().GetPath() == "/World"
    centrifuge = centrifuge_stage.GetPrimAtPath(CENTRIFUGE_ENTRY)
    assert centrifuge
    assert UsdGeom.Xformable(centrifuge).GetLocalTransformation() == Gf.Matrix4d(1.0)
    assert UsdPhysics.ArticulationRootAPI(centrifuge)
    base = centrifuge_stage.GetPrimAtPath(f"{CENTRIFUGE_ENTRY}/base_link")
    assert base.HasAPI(UsdPhysics.RigidBodyAPI)
    assert UsdPhysics.RigidBodyAPI(base).GetKinematicEnabledAttr().Get() is False
    assert centrifuge_stage.GetPrimAtPath(
        f"{CENTRIFUGE_ENTRY}/base_link/base_fixed_joint"
    ).IsA(UsdPhysics.FixedJoint)
    for link in (
        "lid_link",
        "rotor_link",
        "encoder_link",
        "start_button_link",
        "stop_button_link",
    ):
        ops = UsdGeom.Xformable(
            centrifuge_stage.GetPrimAtPath(f"{CENTRIFUGE_ENTRY}/{link}")
        ).GetOrderedXformOps()
        assert [op.GetOpName() for op in ops] == [
            "xformOp:translate",
            "xformOp:orient",
            "xformOp:scale",
        ]
        assert all(not op.GetAttr().GetTimeSamples() for op in ops)

    collision_prims = [
        prim
        for prim in centrifuge_stage.Traverse()
        if prim.HasAPI(UsdPhysics.CollisionAPI)
    ]
    assert collision_prims
    assert not centrifuge_stage.GetPrimAtPath(
        f"{CENTRIFUGE_ENTRY}/rotor_link/__aan_collision_proxy/full_mesh"
    )
    for index in range(24):
        socket = f"{CENTRIFUGE_ENTRY}/rotor_link/__aan_collision_proxy/socket_{index:02d}"
        assert centrifuge_stage.GetPrimAtPath(socket)
        assert centrifuge_stage.GetPrimAtPath(f"{socket}/floor").HasAPI(
            UsdPhysics.CollisionAPI
        )
        for panel in range(8):
            wall = centrifuge_stage.GetPrimAtPath(f"{socket}/wall_{panel:02d}")
            assert wall.HasAPI(UsdPhysics.CollisionAPI)
            assert "PhysxCollisionAPI" in wall.GetMetadata(
                "apiSchemas"
            ).GetAppliedItems()
            assert wall.GetAttribute("physxCollision:contactOffset").Get() == pytest.approx(0.0001)

    profile = json.loads(result["device_profile"].read_text(encoding="utf-8"))
    assert profile["asset_entry_prim"] == CENTRIFUGE_ENTRY
    assert profile["capacity"] == 24
    assert len(profile["tube_sockets"]) == 24
    assert len(profile["balanced_pairs"]) == 12
    assert profile["joints"]["lid"]["states"]["open"] == pytest.approx(
        [-1.361356817, -1.20]
    )
    assert profile["joints"]["rotor"]["low_speed_target_rad_s"] == 5.0

    tube_stage = Usd.Stage.Open(str(result["native_tube_asset"]))
    assert tube_stage.GetDefaultPrim().GetPath() == "/World"
    tube = tube_stage.GetPrimAtPath(NATIVE_TUBE_ENTRY)
    assert tube
    assert UsdGeom.Xformable(tube).GetLocalTransformation() == Gf.Matrix4d(1.0)
    assert tube.HasAPI(UsdPhysics.RigidBodyAPI)
    assert tube_stage.GetPrimAtPath(
        f"{NATIVE_TUBE_ENTRY}/__aan_collision_proxy/body"
    ).HasAPI(UsdPhysics.CollisionAPI)
    assert tube_stage.GetPrimAtPath(
        f"{NATIVE_TUBE_ENTRY}/__aan_collision_proxy/cap"
    ).HasAPI(UsdPhysics.CollisionAPI)

    tube_profile = json.loads(
        result["native_tube_profile"].read_text(encoding="utf-8")
    )
    assert tube_profile["closure_type"] == "snap_lip_non_threaded"
    assert tube_profile["threaded_closure"] is False

    existing_stage = Usd.Stage.Open(str(result["existing_15ml_compat_asset"]))
    existing_root = existing_stage.GetPrimAtPath(EXISTING_TUBE_ENTRY)
    assert existing_root
    assert UsdGeom.Xformable(existing_root).GetLocalTransformation() == Gf.Matrix4d(1.0)
    for collider in ("body", "cap"):
        prim = existing_stage.GetPrimAtPath(
            f"{EXISTING_TUBE_ENTRY}/__aan_collision_proxy/{collider}"
        )
        assert prim.GetAttribute("physxCollision:contactOffset").Get() == pytest.approx(
            0.0001
        )
        assert prim.GetRelationship("material:binding:physics").GetTargets() == [
            f"{EXISTING_TUBE_ENTRY}/__aan_labspin_insert_material"
        ]
    insert_material = existing_stage.GetPrimAtPath(
        f"{EXISTING_TUBE_ENTRY}/__aan_labspin_insert_material"
    )
    assert insert_material.GetAttribute("physics:dynamicFriction").Get() == pytest.approx(
        0.05
    )
    existing_profile = json.loads(
        result["existing_15ml_compat_profile"].read_text(encoding="utf-8")
    )
    assert existing_profile["geometry_and_mass_inherited_unchanged"] is True


@pytest.mark.skipif(not SOURCE_ARCHIVE.is_file(), reason="local intake archive unavailable")
def test_manifest_hash_binds_unchanged_archive_and_package(tmp_path: Path) -> None:
    result = build_labspin_x8_assets(SOURCE_ARCHIVE, tmp_path)
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "candidate_static_built"
    assert manifest["source"]["archive_sha256"]
    assert manifest["source"]["raw_files_unchanged"] is True
    assert manifest["entrypoints"]["asset_entry_prim"] == CENTRIFUGE_ENTRY
    assert manifest["claims"]["robot_policy_success"] is False
    assert manifest["claims"]["rated_high_speed_spin"] is False
