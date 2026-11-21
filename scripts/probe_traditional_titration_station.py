#!/usr/bin/env python3
"""Runtime state-machine and articulation probe for the titration station."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
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
    parser.add_argument("--root", default="/World/TitrationStation")
    parser.add_argument("--output", type=Path, required=True)
    args, _ = parser.parse_known_args()

    original = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True})
    sys.argv = original
    report = {
        "schema_version": "aan.traditional_titration_station_runtime.v1",
        "status": "blocked",
        "usd": str(args.usd.resolve()),
        "root": args.root,
    }
    try:
        import carb.settings
        import numpy as np
        import omni.kit.app
        import omni.usd
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

        settings = carb.settings.get_settings()
        settings.set_bool("/app/omni.graph.scriptnode/enable_opt_in", False)
        settings.set_bool("/app/omni.graph.scriptnode/opt_in", True)
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
        for _ in range(20):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(Usd.EditTarget(stage.GetSessionLayer()))
        shader = UsdShade.Shader.Define(stage, "/World/ReceiverLiquid/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(0.92, 0.97, 1.0)
        )
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.18)
        root = stage.GetPrimAtPath(args.root)
        root.GetRelationship("titration:receiverLiquidShader").SetTargets(
            [shader.GetPath()]
        )
        root.GetAttribute("titration:target_container_inside").Set(True)

        try:
            from isaacsim.core.api import World
            from isaacsim.core.prims import SingleArticulation

            world = World(stage_units_in_meters=1.0, physics_dt=1.0 / 60.0)
            articulation = world.scene.add(
                SingleArticulation(args.root, name="titration_station_probe")
            )
        except ImportError:
            from omni.isaac.core import World
            from omni.isaac.core.articulations import Articulation

            world = World(stage_units_in_meters=1.0, physics_dt=1.0 / 60.0)
            articulation = world.scene.add(
                Articulation(args.root, name="titration_station_probe")
            )
        world.reset()
        world.play()

        def step(count: int) -> None:
            for _ in range(count):
                world.step(render=False)

        def value(name: str):
            return root.GetAttribute(name).Get()

        def set_angle(degrees: float, settle: int = 3) -> None:
            articulation.set_joint_positions(np.asarray([math.radians(degrees)]))
            step(settle)

        def run_until(name: str, threshold: float, max_steps: int) -> int:
            for index in range(max_steps):
                world.step(render=False)
                if float(value(name)) >= threshold:
                    return index + 1
            raise RuntimeError(f"{name} did not reach {threshold} in {max_steps} steps")

        base_path = args.root + "/Instance/Body"
        base = stage.GetPrimAtPath(base_path)
        base_initial = (
            UsdGeom.Xformable(base)
            .ComputeLocalToWorldTransform(Usd.TimeCode.Default())
            .ExtractTranslation()
        )
        column_path = args.root + "/Instance/Burette/body_link/Visual/liquid_column"
        column = stage.GetPrimAtPath(column_path)
        initial_column_height = float(UsdGeom.Cylinder(column).GetHeightAttr().Get())

        set_angle(0.0)
        closed_flow = float(value("titration:flow_rate_ml_s"))
        set_angle(90.0)
        open_steps = run_until("titration:dispensed_volume_ml", 14.4, 600)
        open_state = str(value("titration:valve_state"))
        set_angle(25.0)
        fine_steps = run_until("titration:dispensed_volume_ml", 14.7, 180)
        fine_state = str(value("titration:valve_state"))
        transition_color = list(shader.GetInput("diffuseColor").Get())
        set_angle(10.0)
        drip_steps = run_until("titration:dispensed_volume_ml", 15.0, 600)
        drip_state = str(value("titration:valve_state"))
        endpoint_color = list(shader.GetInput("diffuseColor").Get())
        endpoint_opacity = float(shader.GetInput("opacity").Get())
        set_angle(0.0)
        step(190)
        success_snapshot = {
            "dispensed_ml": float(value("titration:dispensed_volume_ml")),
            "remaining_ml": float(value("titration:burette_liquid_volume_ml")),
            "hold_seconds": float(value("titration:endpoint_hold_seconds")),
            "task_success": bool(value("titration:task_success")),
            "overshoot": bool(value("titration:overshoot")),
            "phase": str(value("titration:indicator_phase")),
            "visited": {
                "open": bool(value("titration:visited_open")),
                "fine": bool(value("titration:visited_fine")),
                "drip": bool(value("titration:visited_drip")),
            },
        }
        final_column_height = float(UsdGeom.Cylinder(column).GetHeightAttr().Get())

        root.GetAttribute("titration:reset_requested").Set(True)
        step(2)
        reset_snapshot = {
            "dispensed_ml": float(value("titration:dispensed_volume_ml")),
            "remaining_ml": float(value("titration:burette_liquid_volume_ml")),
            "phase": str(value("titration:indicator_phase")),
            "task_success": bool(value("titration:task_success")),
        }

        set_angle(90.0)
        run_until("titration:dispensed_volume_ml", 15.35, 700)
        overshoot_color = list(shader.GetInput("diffuseColor").Get())
        set_angle(0.0)
        step(190)
        overshoot_snapshot = {
            "dispensed_ml": float(value("titration:dispensed_volume_ml")),
            "overshoot": bool(value("titration:overshoot")),
            "task_success": bool(value("titration:task_success")),
            "phase": str(value("titration:indicator_phase")),
        }
        base_final = (
            UsdGeom.Xformable(base)
            .ComputeLocalToWorldTransform(Usd.TimeCode.Default())
            .ExtractTranslation()
        )
        base_drift = math.sqrt(
            sum(
                (float(base_final[index]) - float(base_initial[index])) ** 2
                for index in range(3)
            )
        )
        checks = {
            "one_dof_articulation": int(articulation.num_dof) == 1,
            "closed_flow_zero": abs(closed_flow) <= 1.0e-8,
            "ordered_states_observed": (open_state, fine_state, drip_state)
            == ("OPEN", "FINE", "DRIP"),
            "success_window": 14.7 <= success_snapshot["dispensed_ml"] <= 15.3,
            "endpoint_hold_three_seconds": success_snapshot["hold_seconds"] >= 3.0,
            "task_success": success_snapshot["task_success"] is True,
            "ordered_visits_latched": all(success_snapshot["visited"].values()),
            "liquid_column_decreased": final_column_height < initial_column_height,
            "endpoint_is_pale_pink": endpoint_color[0] >= 0.95
            and 0.40 <= endpoint_color[1] <= 0.60
            and 0.55 <= endpoint_color[2] <= 0.75
            and 0.65 <= endpoint_opacity <= 0.71,
            "reset_restores_initial_state": reset_snapshot
            == {
                "dispensed_ml": 0.0,
                "remaining_ml": 25.0,
                "phase": "colorless",
                "task_success": False,
            },
            "overshoot_latches_failure": overshoot_snapshot["overshoot"] is True
            and overshoot_snapshot["task_success"] is False
            and overshoot_snapshot["phase"] == "overshoot",
            "overshoot_color_deepens": overshoot_color[1] < endpoint_color[1],
            "fixed_base_stable": base_drift <= 5.0e-4,
            "controller_pose_valid": bool(value("titration:controller_pose_valid")),
            "source_unchanged": _sha(args.usd) == source_hash,
        }
        report.update(
            {
                "status": "pass" if all(checks.values()) else "blocked",
                "runtime_version": app.app.get_app_version(),
                "dof_count": int(articulation.num_dof),
                "dof_names": list(articulation.dof_names),
                "steps": {
                    "open": open_steps,
                    "fine": fine_steps,
                    "drip": drip_steps,
                },
                "colors": {
                    "transition": transition_color,
                    "endpoint": endpoint_color,
                    "overshoot": overshoot_color,
                },
                "column_height_m": {
                    "initial": initial_column_height,
                    "endpoint": final_column_height,
                },
                "success": success_snapshot,
                "reset": reset_snapshot,
                "overshoot": overshoot_snapshot,
                "base_drift_m": base_drift,
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
