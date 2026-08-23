#!/usr/bin/env python3
"""Build LABSPIN X8 r3 with a USD-embedded lid behavior graph."""

from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT = r"""
def setup(db):
    db.per_instance_state.dc = None

def compute(db):
    import omni.isaac.dynamic_control._dynamic_control as dynamic_control
    dc = db.per_instance_state.dc or dynamic_control.acquire_dynamic_control_interface()
    db.per_instance_state.dc = dc
    articulation_path = str(db.node.get_prim_path()).rsplit("/", 2)[0]
    articulation = dc.get_articulation(articulation_path)
    if articulation == dynamic_control.INVALID_HANDLE:
        return True
    button = dc.find_articulation_dof(articulation, "lid_open_button_joint")
    lid = dc.find_articulation_dof(articulation, "lid_hinge_joint")
    rotor = dc.find_articulation_dof(articulation, "rotor_spin_joint")
    if min(button, lid, rotor) == dynamic_control.INVALID_HANDLE:
        return True
    button_position = dc.get_dof_position(button)
    lid_velocity = dc.get_dof_velocity(lid)
    rotor_velocity = dc.get_dof_velocity(rotor)
    if button_position >= 0.0021 and abs(rotor_velocity) <= 0.1:
        dc.set_dof_position_target(lid, -1.361356817)
    elif button_position <= 0.0004 and lid_velocity >= 0.05:
        dc.set_dof_position_target(lid, 0.0)
    return True

def cleanup(db):
    db.per_instance_state.dc = None
"""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        shutil.rmtree(a.out)
    shutil.copytree(a.source, a.out)
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True})
    sys.argv = original
    try:
        import omni.graph.core as og
        import omni.usd
        from pxr import UsdPhysics

        context = omni.usd.get_context()
        context.open_stage(str((a.out / "asset.usd").resolve()))
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetRootLayer())
        lid = stage.GetPrimAtPath("/World/Centrifuge/lid_hinge_joint")
        drive = UsdPhysics.DriveAPI.Apply(lid, "angular")
        drive.CreateStiffnessAttr(18.0)
        drive.CreateDampingAttr(4.0)
        drive.CreateMaxForceAttr(48.0)
        drive.CreateTargetPositionAttr(0.0)
        graph = "/World/Centrifuge/__device_behavior"
        K = og.Controller.Keys
        og.Controller.edit(
            {
                "graph_path": graph,
                "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND,
            },
            {
                K.CREATE_NODES: [
                    ("Tick", "omni.isaac.core_nodes.OnPhysicsStep"),
                    ("Behavior", "omni.graph.scriptnode.ScriptNode"),
                ],
                K.SET_VALUES: [("Behavior.inputs:script", SCRIPT)],
                K.CONNECT: [("Tick.outputs:step", "Behavior.inputs:execIn")],
            },
        )
        stage.GetRootLayer().Save()
        profile = a.out / "articulation/device_profile.json"
        d = json.loads(profile.read_text())
        d["revision"] = "r3-usd-embedded-lid-behavior"
        d["behavior"] = {
            "graph_prim": graph,
            "node_policy": "embedded_scriptnode_self_contained",
            "external_python_required": False,
            "open_button_threshold_m": 0.0021,
            "rotor_interlock_rad_s": 0.1,
            "lid_open_target_rad": -1.361356817,
            "manual_close_velocity_threshold_rad_s": 0.05,
        }
        profile.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
        print(a.out, flush=True)
        return 0
    except BaseException:
        import traceback

        traceback.print_exc()
        return 2
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
