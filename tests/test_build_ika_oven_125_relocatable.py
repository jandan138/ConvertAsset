from __future__ import annotations

import hashlib
from pathlib import Path

from pxr import Usd, UsdPhysics

from scripts.build_ika_oven_125_relocatable import (
    ARCHIVE_SHA256,
    CONTROLLER_PATH,
    DEVICE_PATH,
    PRIMARY_SHA256,
    STANDARD_BENCHTOP_HEIGHT_M,
    build_package,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_builder_preserves_source_and_rebinds_world_anchored_joints(
    tmp_path: Path,
) -> None:
    output = tmp_path / "oven"

    manifest_path = build_package(output)

    assert manifest_path.is_file()
    assert _sha256(output / "input/source.7z") == ARCHIVE_SHA256
    assert _sha256(output / "package/deps/source.usd") == PRIMARY_SHA256
    stage = Usd.Stage.Open(str(output / "package/asset.usd"))
    assert stage
    assert stage.GetDefaultPrim().GetPath() == "/World"
    device = stage.GetPrimAtPath(DEVICE_PATH)
    assert device.IsValid()
    assert not device.GetAttribute("xformOp:translate").IsValid()
    door_translation = stage.GetPrimAtPath(
        DEVICE_PATH + "/Door"
    ).GetAttribute("xformOp:translate").Get()
    assert float(door_translation[2]) == STANDARD_BENCHTOP_HEIGHT_M

    joints = [
        prim
        for prim in stage.Traverse()
        if prim.IsA(UsdPhysics.Joint)
    ]
    assert len(joints) == 16
    body0_targets = {
        str(prim.GetPath()): [str(path) for path in UsdPhysics.Joint(prim).GetBody0Rel().GetTargets()]
        for prim in joints
    }
    assert sum(not targets for targets in body0_targets.values()) == 15
    assert sum(bool(targets) for targets in body0_targets.values()) == 1


def test_controller_uses_context_local_instance_root(tmp_path: Path) -> None:
    output = tmp_path / "oven"
    build_package(output)
    stage = Usd.Stage.Open(str(output / "package/asset.usd"))
    controller = stage.GetPrimAtPath(CONTROLLER_PATH)
    script = controller.GetAttribute("inputs:script").Get()

    assert isinstance(script, str)
    assert 'ROOT = "/World/Oven125"' not in script
    assert "db.node.get_prim_path()" in script
    assert "contextvars.ContextVar" in script
    assert "_bind_instance_root(db)" in script
    assert "get_rigidbody_transformation(str(path))" in script
    compile(script, "<oven125-inline-controller>", "exec")
