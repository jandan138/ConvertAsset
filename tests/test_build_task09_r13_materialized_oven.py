from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pxr import Usd, UsdPhysics

from scripts.build_task09_r13_materialized_oven import build_materialized_oven


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_materialized_oven_renames_entry_and_internal_joint_targets(tmp_path: Path) -> None:
    result = build_materialized_oven(tmp_path / "oven")

    stage = Usd.Stage.Open(str(result.asset_usd))
    assert stage and stage.GetDefaultPrim().GetPath() == "/World"
    assert not stage.GetPrimAtPath("/World/Oven125").IsValid()
    assert stage.GetPrimAtPath("/World/obj_oven").IsValid()
    joints = [
        prim
        for prim in stage.Traverse()
        if prim.IsA(UsdPhysics.Joint)
        and str(prim.GetPath()).startswith("/World/obj_oven/")
    ]
    assert len(joints) == 16
    assert sum(
        [str(path) for path in UsdPhysics.Joint(prim).GetBody0Rel().GetTargets()]
        == ["/World/obj_oven/Body"]
        for prim in joints
    ) == 15
    graph = stage.GetPrimAtPath(
        "/World/obj_oven/ControlPanel/Runtime/ControllerGraph"
    )
    assert graph.IsValid() and graph.IsActive()


def test_materialized_package_preserves_source_and_blocks_reference_consumption(
    tmp_path: Path,
) -> None:
    result = build_materialized_oven(tmp_path / "oven")

    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "candidate_runtime_qualification_pending"
    assert manifest["mounting"]["consumer_mode"] == "materialized_stage_base"
    assert manifest["mounting"]["reference_mount_allowed"] is False
    assert manifest["entrypoints"]["asset_entry_prim"] == "/World/obj_oven"
    source = result.output / "input/source_package/package/asset.usd"
    assert source.is_file()
    assert _sha(source) == manifest["source"]["asset_sha256"]
