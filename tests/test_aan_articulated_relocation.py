from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path

import pytest
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

from convert_asset.asset_application_normalizer.articulated_relocation import (
    normalize_articulated,
)
from convert_asset.asset_application_normalizer.articulated_relocation_profile import (
    ArticulatedRelocationProfile,
)
from convert_asset.asset_application_normalizer.articulated_relocation_qualification import (
    resolve_promotion,
)
from convert_asset.asset_application_normalizer.cli import (
    add_normalize_articulated_parser,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(path: Path) -> tuple[str, str]:
    stage = Usd.Stage.CreateNew(str(path))
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    UsdGeom.Xform.Define(stage, "/World/Device")
    chassis = UsdGeom.Xform.Define(stage, "/World/Device/Chassis").GetPrim()
    UsdGeom.Xformable(chassis).AddTranslateOp().Set(Gf.Vec3d(10.0, 0.0, 0.0))
    lid = UsdGeom.Xform.Define(stage, "/World/Device/Lid").GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(lid)
    joint = UsdPhysics.RevoluteJoint.Define(stage, "/World/Device/Joints/Lid")
    joint.CreateBody1Rel().SetTargets([lid.GetPath()])
    joint.CreateLocalPos0Attr().Set(Gf.Vec3f(12.0, 2.0, 3.0))
    joint.CreateLocalRot0Attr().Set(Gf.Quatf(1.0))
    joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0))
    joint.CreateLocalRot1Attr().Set(Gf.Quatf(1.0))
    controller = UsdGeom.Xform.Define(
        stage, "/World/Device/Runtime/ControllerGraph/Controller"
    ).GetPrim()
    script = '''import math
ROOT = "/World/Device"
CP = ROOT + "/ControlPanel"
RUNTIME = CP + "/Runtime"
PAGES = RUNTIME + "/Pages"
OVERLAYS = RUNTIME + "/Overlays"
BUTTON_ROOT = CP + "/Buttons"
KNOB_ROOT = CP + "/ControlKnob"
LAMP_ROOT = ROOT + "/Interior/ChamberLamp"
def _prim(stage, path):
    return stage.GetPrimAtPath(path)
def sample(path):
    value = _PHYSX.get_rigidbody_transformation(path)
def setup(db):
    pass
def compute(db):
    pass
def cleanup(db):
    pass
'''
    controller.CreateAttribute("inputs:script", Sdf.ValueTypeNames.String).Set(script)
    stage.GetRootLayer().Save()
    return script, hashlib.sha256(script.encode()).hexdigest()


def _profile(path: Path, source: Path, script_sha: str) -> Path:
    value = {
        "schema_version": "aan.articulated_relocation_profile.v1",
        "profile_id": "test_device_identity_root",
        "source": {"usd_sha256": _sha256(source)},
        "entry_prim": "/World/Device",
        "chassis_prim": "/World/Device/Chassis",
        "joint_scope_prim": "/World/Device",
        "topology": "jointed_rigid_graph",
        "support_frame": {
            "prim": "/World/Device",
            "local_support_z_m": 0.0,
        },
        "controller_hooks": [
            {
                "kind": "scriptnode_root_from_node_path",
                "strategy": "contextvar_node_path_v1",
                "controller_prim": "/World/Device/Runtime/ControllerGraph/Controller",
                "controller_suffix": "/Runtime/ControllerGraph/Controller",
                "source_root": "/World/Device",
                "source_script_sha256": script_sha,
            }
        ],
        "promotion": {
            "requested_tier": "relocatable_task_scoped",
            "required_functions": ["open", "close"],
        },
    }
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_profile_rejects_ambiguous_or_unpinned_contract(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source.usd_sha256"):
        ArticulatedRelocationProfile.from_mapping(
            {
                "schema_version": "aan.articulated_relocation_profile.v1",
                "profile_id": "bad",
                "source": {},
                "entry_prim": "/World/Device",
                "chassis_prim": "/World/Device/Chassis",
                "joint_scope_prim": "/World/Device",
                "topology": "jointed_rigid_graph",
                "support_frame": {"prim": "/World/Device", "local_support_z_m": 0},
                "controller_hooks": [],
                "promotion": {
                    "requested_tier": "relocatable_full",
                    "required_functions": [],
                },
            }
        )


def test_normalizer_rebinds_world_anchor_and_keeps_identity_entry(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    original_script, script_sha = _source(source)
    source_hash = _sha256(source)
    profile_path = _profile(tmp_path / "profile.json", source, script_sha)

    result = normalize_articulated(source, tmp_path / "out", profile_path)

    assert _sha256(source) == source_hash
    assert result.manifest_path.is_file()
    stage = Usd.Stage.Open(str(result.asset_usd))
    assert stage
    entry = stage.GetPrimAtPath("/World/Device")
    assert entry.IsValid()
    assert not UsdGeom.Xformable(entry).GetOrderedXformOps()
    chassis = stage.GetPrimAtPath("/World/Device/Chassis")
    assert chassis.HasAPI(UsdPhysics.RigidBodyAPI)
    assert chassis.GetAttribute("physics:kinematicEnabled").Get() is True
    joint = UsdPhysics.Joint(stage.GetPrimAtPath("/World/Device/Joints/Lid"))
    assert [str(path) for path in joint.GetBody0Rel().GetTargets()] == [
        "/World/Device/Chassis"
    ]
    assert tuple(round(float(v), 6) for v in joint.GetLocalPos0Attr().Get()) == (
        2.0,
        2.0,
        3.0,
    )
    controller = stage.GetPrimAtPath(
        "/World/Device/Runtime/ControllerGraph/Controller"
    )
    rewritten = controller.GetAttribute("inputs:script").Get()
    assert rewritten != original_script
    assert 'ROOT = "/World/Device"' not in rewritten
    assert "db.node.get_prim_path()" in rewritten
    compile(rewritten, "<test-controller>", "exec")
    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["overall_status"] == "candidate_runtime_qualification_pending"
    assert manifest["relocatability"]["world_anchored_joints_rebound"] == 1
    assert manifest["promotion"]["requested_tier"] == "relocatable_task_scoped"


def test_normalizer_fails_closed_on_controller_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    _, script_sha = _source(source)
    profile_path = _profile(tmp_path / "profile.json", source, script_sha)
    value = json.loads(profile_path.read_text())
    value["controller_hooks"][0]["source_script_sha256"] = "0" * 64
    profile_path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="controller script SHA-256"):
        normalize_articulated(source, tmp_path / "out", profile_path)


def test_cli_exposes_profile_driven_articulated_normalization() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_normalize_articulated_parser(subparsers)

    args = parser.parse_args(
        [
            "normalize-articulated",
            "source.usd",
            "--out",
            "candidate",
            "--profile",
            "profile.json",
        ]
    )

    assert args.command == "normalize-articulated"
    assert args.profile == "profile.json"


def test_promotion_never_uses_task_scope_to_waive_portability() -> None:
    blocked = resolve_promotion(
        requested_tier="relocatable_full",
        portability_checks={"vr_scene": False, "runtime_obj": True},
        full_function_checks={"all_controls": False},
        scoped_function_checks={"task09": True, "task12": True},
    )
    assert blocked.status == "blocked"
    assert blocked.promoted_tier is None

    scoped = resolve_promotion(
        requested_tier="relocatable_full",
        portability_checks={"vr_scene": True, "runtime_obj": True},
        full_function_checks={"all_controls": False},
        scoped_function_checks={"task09": True, "task12": True},
    )
    assert scoped.status == "pass"
    assert scoped.promoted_tier == "relocatable_task_scoped"

    full = resolve_promotion(
        requested_tier="relocatable_full",
        portability_checks={"vr_scene": True, "runtime_obj": True},
        full_function_checks={"all_controls": True},
        scoped_function_checks={"task09": True, "task12": True},
    )
    assert full.promoted_tier == "relocatable_full"
