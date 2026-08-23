#!/usr/bin/env python3
"""Build LABSPIN X8 r4 with contact-correct controls and embedded state."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from hashlib import sha256
from pathlib import Path


ROOT = "/World/Centrifuge"
LID_BUTTON_CENTER = (0.194, -0.263, 0.198)
LID_OPEN_RAD = -1.361356817
ROTOR_INTERLOCK_RAD_S = 0.1

SCRIPT = r'''
def setup(db):
    db.per_instance_state.dc = None
    db.per_instance_state.mode = "locked"

def compute(db):
    import omni.isaac.dynamic_control._dynamic_control as dynamic_control
    import omni.usd
    dc = db.per_instance_state.dc or dynamic_control.acquire_dynamic_control_interface()
    db.per_instance_state.dc = dc
    root = str(db.node.get_prim_path()).rsplit("/", 2)[0]
    articulation = dc.get_articulation(root)
    if articulation == dynamic_control.INVALID_HANDLE:
        return True
    button = dc.find_articulation_dof(articulation, "lid_open_button_joint")
    stop = dc.find_articulation_dof(articulation, "stop_button_joint")
    lid = dc.find_articulation_dof(articulation, "lid_hinge_joint")
    rotor = dc.find_articulation_dof(articulation, "rotor_spin_joint")
    if min(button, stop, lid, rotor) == dynamic_control.INVALID_HANDLE:
        return True

    button_position = dc.get_dof_position(button)
    stop_position = dc.get_dof_position(stop)
    lid_position = dc.get_dof_position(lid)
    lid_velocity = dc.get_dof_velocity(lid)
    rotor_velocity = dc.get_dof_velocity(rotor)
    stage = omni.usd.get_context().get_stage()
    device = stage.GetPrimAtPath(root)

    if stop_position >= 0.0021:
        device.GetAttribute("device:powerState").Set("off")
        dc.set_dof_velocity_target(rotor, 0.0)

    mode = db.per_instance_state.mode
    if mode in ("closed", "locked"):
        dc.set_dof_position_target(lid, 0.0)
        if button_position >= 0.0021 and abs(rotor_velocity) <= 0.1:
            mode = "opening"
            dc.set_dof_position_target(lid, -1.361356817)
    elif mode == "opening":
        dc.set_dof_position_target(lid, -1.361356817)
        if lid_position <= -1.30:
            mode = "open_hold"
    elif mode == "open_hold":
        dc.set_dof_position_target(lid, -1.361356817)
        if lid_velocity >= 0.05 or lid_position >= -1.15:
            mode = "closing"
            dc.set_dof_position_target(lid, 0.0)
    elif mode == "closing":
        dc.set_dof_position_target(lid, 0.0)
        if lid_position >= -0.03:
            mode = "locked"
    else:
        mode = "closed"

    db.per_instance_state.mode = mode
    device.GetAttribute("device:lidState").Set(mode)
    return True

def cleanup(db):
    db.per_instance_state.dc = None
    db.per_instance_state.mode = "locked"
'''


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        shutil.rmtree(args.out)
    shutil.copytree(args.source, args.out)

    original_argv = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True})
    sys.argv = original_argv
    try:
        import omni.graph.core as og
        import omni.usd
        from pxr import Gf, Sdf, UsdGeom, UsdPhysics

        asset = args.out / "asset.usd"
        context = omni.usd.get_context()
        context.open_stage(str(asset.resolve()))
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetRootLayer())

        # r2 placed the child geometry at the body0 anchor even though the
        # dynamic link frame was already constrained there. Rebase the visual
        # and collider to the link origin so contact occurs at the visible cap.
        for suffix in ("Visual", "__aan_collision_proxy/button"):
            prim = stage.GetPrimAtPath(f"{ROOT}/lid_open_button_link/{suffix}")
            xform = UsdGeom.Xformable(prim)
            translate = next(
                op for op in xform.GetOrderedXformOps()
                if op.GetOpType() == UsdGeom.XformOp.TypeTranslate
            )
            translate.Set(Gf.Vec3d(0.0, 0.0, 0.0))

        joint = UsdPhysics.PrismaticJoint.Get(
            stage, f"{ROOT}/lid_open_button_joint"
        )
        joint.CreateLocalPos0Attr(Gf.Vec3f(*LID_BUTTON_CENTER))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0.0, 0.0, 0.0))

        device = stage.GetPrimAtPath(ROOT)
        device.CreateAttribute("device:lidState", Sdf.ValueTypeNames.String).Set(
            "locked"
        )
        device.CreateAttribute("device:powerState", Sdf.ValueTypeNames.String).Set(
            "on"
        )

        graph = f"{ROOT}/__device_behavior"
        behavior = stage.GetPrimAtPath(f"{graph}/Behavior")
        if behavior:
            behavior.GetAttribute("inputs:script").Set(SCRIPT)
        else:
            keys = og.Controller.Keys
            og.Controller.edit(
                {
                    "graph_path": graph,
                    "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND,
                },
                {
                    keys.CREATE_NODES: [
                        ("Tick", "omni.isaac.core_nodes.OnPhysicsStep"),
                        ("Behavior", "omni.graph.scriptnode.ScriptNode"),
                    ],
                    keys.SET_VALUES: [("Behavior.inputs:script", SCRIPT)],
                    keys.CONNECT: [("Tick.outputs:step", "Behavior.inputs:execIn")],
                },
            )
        stage.GetRootLayer().Save()

        profile_path = args.out / "articulation/device_profile.json"
        profile = json.loads(profile_path.read_text())
        profile["revision"] = "r4-contact-controls-and-device-state"
        profile["behavior"] = {
            "graph_prim": graph,
            "node_policy": "embedded_scriptnode_self_contained",
            "external_python_required": False,
            "lid_states": ["closed", "opening", "open_hold", "closing", "locked"],
            "power_states": ["on", "off"],
            "open_button_threshold_m": 0.0021,
            "rotor_interlock_rad_s": ROTOR_INTERLOCK_RAD_S,
            "lid_open_target_rad": LID_OPEN_RAD,
            "manual_close_velocity_threshold_rad_s": 0.05,
            "observable_attributes": {
                "lid_state": f"{ROOT}.device:lidState",
                "power_state": f"{ROOT}.device:powerState",
            },
        }
        _write_json(profile_path, profile)
        _write_json(
            args.out / "evidence/r4_build_manifest.json",
            {
                "schema_version": "aan.labspin_x8_r4_build.v1",
                "status": "built_pending_runtime_qualification",
                "source_package": str(args.source.resolve()),
                "asset_usd_sha256": _sha(asset),
                "changes": [
                    "lid_open_button_visual_and_collider_rebased_to_link_origin",
                    "embedded_explicit_lid_state_machine",
                    "observable_power_state_and_stop_transition",
                    "rotor_open_interlock",
                ],
                "unchanged": [
                    "source_visual_facade",
                    "rotor_socket_geometry",
                    "lid_joint_limits",
                    "existing_start_and_stop_button_geometry",
                ],
            },
        )
        print(args.out)
        return 0
    except BaseException:
        import traceback

        traceback.print_exc()
        return 2
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
