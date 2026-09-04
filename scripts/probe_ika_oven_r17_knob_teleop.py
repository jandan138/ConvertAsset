#!/usr/bin/env python3
"""Isaac 4.1/4.5 VR-like knob profile for OVEN 125 r17."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

try:
    from isaacsim import SimulationApp
except ImportError:
    from omni.isaac.kit import SimulationApp


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", type=Path, required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--knob", choices=("primary", "auxiliary"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--script-opt-in", choices=("true", "false"), default="true")
    args, _ = parser.parse_known_args()

    original = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True})
    sys.argv = original
    positive = args.script_opt_in == "true"
    report = {
        "schema_version": "aan.ika_oven_r17_knob_teleop_probe.v1",
        "status": "blocked",
        "usd": str(args.usd.resolve()),
        "root": args.root,
        "knob": args.knob,
        "script_opt_in": positive,
    }
    try:
        import carb.settings
        import omni.kit.app
        import omni.timeline
        import omni.usd
        from pxr import Usd

        settings = carb.settings.get_settings()
        settings.set_bool("/app/omni.graph.scriptnode/enable_opt_in", not positive)
        settings.set_bool("/app/omni.graph.scriptnode/opt_in", positive)
        settings.set_bool("/app/scripting/ignoreWarningDialog", True)
        manager = omni.kit.app.get_app().get_extension_manager()
        for extension in ("omni.graph.action_nodes", "omni.graph.scriptnode"):
            manager.set_extension_enabled_immediate(extension, True)

        source_hash = _sha(args.usd)
        context = omni.usd.get_context()
        if context.open_stage(str(args.usd.resolve())) is False:
            raise RuntimeError(f"Isaac could not open stage: {args.usd}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(16):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(Usd.EditTarget(stage.GetSessionLayer()))
        instance = args.root.rstrip("/") + "/Instance"
        control_path = instance + "/ControlPanel"
        knob_name = "ControlKnob" if args.knob == "primary" else "AuxControlKnob"
        knob_path = control_path + "/" + knob_name
        joint_path = knob_path + "/Joints/Rotation"
        control = stage.GetPrimAtPath(control_path)
        knob = stage.GetPrimAtPath(knob_path)
        joint = stage.GetPrimAtPath(joint_path)
        if not control or not knob or not joint:
            raise RuntimeError("required oven control prims are missing")

        for name, value in {
            "oven:mainsPower": True,
            "oven:heatingEnabled": False,
            "oven:heaterActive": False,
            "oven:controlsLocked": False,
            "oven:temperatureSetpointC": 60.0,
            "oven:operatingState": "idle",
            "ui:page": "home",
            "ui:selectedField": "home",
            "ui:eventSequence": 0,
            "ui:lastInput": "none",
        }.items():
            control.GetAttribute(name).Set(value)
        stage.GetPrimAtPath(instance + "/Joints/MainsRocker").GetAttribute(
            "drive:angular:physics:targetPosition"
        ).Set(8.0)

        drive_names = {
            "target_velocity": "drive:angular:physics:targetVelocity",
            "stiffness": "drive:angular:physics:stiffness",
            "damping": "drive:angular:physics:damping",
            "max_force": "drive:angular:physics:maxForce",
        }
        authored = {
            key: joint.GetAttribute(name).Get() for key, name in drive_names.items()
        }
        joint.GetAttribute(drive_names["stiffness"]).Set(0.0)
        joint.GetAttribute(drive_names["damping"]).Set(0.4)
        joint.GetAttribute(drive_names["max_force"]).Set(5.0)
        velocity = joint.GetAttribute(drive_names["target_velocity"])

        timeline = omni.timeline.get_timeline_interface()

        def step(count: int) -> None:
            for _ in range(count):
                app.update()

        def setpoint() -> float:
            return float(control.GetAttribute("oven:temperatureSetpointC").Get())

        def event_sequence() -> int:
            return int(control.GetAttribute("ui:eventSequence").Get())

        def drive(target_velocity: float, frames: int, settle: int = 8) -> None:
            velocity.Set(target_velocity)
            step(frames)
            velocity.Set(0.0)
            step(settle)

        timeline.play()
        step(30)
        initial = {"setpoint": setpoint(), "event_sequence": event_sequence()}

        jitter_before = setpoint()
        drive(30.0, 2, settle=2)
        drive(-30.0, 2, settle=8)
        jitter_after = setpoint()

        smooth_before = setpoint()
        drive(180.0, 12)
        smooth_after = setpoint()

        rapid_before = setpoint()
        drive(1440.0, 8, settle=12)
        rapid_after = setpoint()

        timeline.pause()
        step(5)
        pause_before = setpoint()
        timeline.play()
        step(4)
        drive(-180.0, 12)
        pause_after = setpoint()
        final_sequence = event_sequence()
        timeline.stop()

        for key, name in drive_names.items():
            joint.GetAttribute(name).Set(authored[key])

        diagnostics = {
            "physical_pose_sample_valid": bool(
                knob.GetAttribute("oven:physicalPoseSampleValid").Get()
            ),
            "pose_miss_count": int(knob.GetAttribute("oven:poseMissCount").Get()),
            "last_physical_delta_degrees": float(
                knob.GetAttribute("oven:lastPhysicalDeltaDegrees").Get()
            ),
            "detent_event_count": int(knob.GetAttribute("oven:detentEventCount").Get()),
        }
        profiles = {
            "subthreshold_jitter": {
                "before": jitter_before,
                "after": jitter_after,
                "delta": jitter_after - jitter_before,
            },
            "smooth_rotation": {
                "before": smooth_before,
                "after": smooth_after,
                "delta": smooth_after - smooth_before,
            },
            "rapid_rotation": {
                "before": rapid_before,
                "after": rapid_after,
                "delta": rapid_after - rapid_before,
            },
            "pause_resume": {
                "before": pause_before,
                "after": pause_after,
                "delta": pause_after - pause_before,
            },
        }
        if positive:
            checks = {
                "pose_sample_valid": diagnostics["physical_pose_sample_valid"],
                "jitter_does_not_change_setpoint": abs(
                    profiles["subthreshold_jitter"]["delta"]
                )
                < 0.5,
                "smooth_rotation_changes_setpoint": profiles["smooth_rotation"]["delta"]
                >= 1.0,
                "rapid_rotation_changes_setpoint": profiles["rapid_rotation"]["delta"]
                >= 2.0,
                "pause_resume_changes_setpoint": profiles["pause_resume"]["delta"]
                <= -1.0,
                "detent_events_recorded": diagnostics["detent_event_count"] >= 4,
                "event_sequence_advanced": final_sequence > initial["event_sequence"],
                "source_unchanged": _sha(args.usd) == source_hash,
            }
        else:
            checks = {
                "setpoint_stays_static_without_script_trust": setpoint()
                == initial["setpoint"],
                "event_sequence_stays_static_without_script_trust": final_sequence
                == initial["event_sequence"],
                "source_unchanged": _sha(args.usd) == source_hash,
            }
        report.update(
            {
                "status": "pass" if all(checks.values()) else "blocked",
                "runtime_version": app.app.get_app_version(),
                "initial": initial,
                "final": {"setpoint": setpoint(), "event_sequence": final_sequence},
                "profiles": profiles,
                "diagnostics": diagnostics,
                "checks": checks,
            }
        )
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        app.close()
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
