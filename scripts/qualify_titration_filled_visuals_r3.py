"""Isaac 4.5 standalone station qualification; joint-position fixture, not robot proof."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import os


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    argv = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp
    app = SimulationApp({'headless': True})
    sys.argv = argv
    report = {'status': 'blocked', 'process_id': os.getpid(), 'asset_sha256': sha256((args.package/'asset.usd').read_bytes()).hexdigest(),
              'protocol': 'standalone_fixed_base_prescribed_joint_positions', 'robot_policy_success': False}
    try:
        import carb.settings
        import numpy as np
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from pxr import Usd, UsdGeom
        settings = carb.settings.get_settings()
        settings.set_bool('/app/omni.graph.scriptnode/enable_opt_in', False)
        settings.set_bool('/app/omni.graph.scriptnode/opt_in', True)
        context = omni.usd.get_context()
        context.open_stage(str(args.package/'asset.usd'))
        while context.get_stage_loading_status()[2]:
            app.update()
        for _ in range(20):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(Usd.EditTarget(stage.GetSessionLayer()))
        root = '/World/TitrationStation'
        station = stage.GetPrimAtPath(root)
        station.GetAttribute('titration:target_container_inside').Set(True)
        visual = root+'/Instance/Burette/body_link/Visual/'

        def value(name):
            return station.GetAttribute('titration:'+name).Get()

        def sample():
            col = stage.GetPrimAtPath(visual+'liquid_column')
            cap = stage.GetPrimAtPath(visual+'liquid_meniscus')
            return {'remaining_ml': value('burette_liquid_volume_ml'),
                    'surface_z': float(cap.GetAttribute('xformOp:translate').Get()[2]),
                    'column_visible': UsdGeom.Imageable(col).ComputeVisibility() != 'invisible',
                    'precharge_visible': UsdGeom.Imageable(stage.GetPrimAtPath(visual+'liquid_precharge')).ComputeVisibility() != 'invisible'}

        states = {'pre_run': sample()}
        world = World(stage_units_in_meters=1, physics_dt=1/60)
        articulation = world.scene.add(SingleArticulation(root, name='station'))
        world.reset()
        world.play()
        initial_pose = articulation.get_world_pose()[0].copy()

        def step(n):
            for _ in range(n):
                world.step(render=False)

        def angle(degrees):
            articulation.set_joint_positions(np.asarray([math.radians(degrees)]))
            step(3)

        def until(volume, budget=1000):
            for _ in range(budget):
                if value('dispensed_volume_ml') >= volume:
                    return
                step(1)
            raise RuntimeError(f'volume did not reach {volume}')

        step(3)
        states['running_initial'] = sample()
        angle(90)
        until(12.5)
        states['mid'] = sample()
        until(14.4)
        angle(25)
        until(14.7)
        angle(10)
        until(15)
        angle(0)
        step(190)
        success = bool(value('task_success'))
        hold = float(value('endpoint_hold_seconds'))
        endpoint = float(value('dispensed_volume_ml'))
        angle(90)
        until(25)
        angle(0)
        states['end_scale'] = sample()
        overshoot_failed = not bool(value('task_success'))
        station.GetAttribute('titration:reset_requested').Set(True)
        step(3)
        states['reset'] = sample()
        checks = {'one_dof': articulation.num_dof == 1, 'endpoint_success': success,
                  'endpoint_window': 14.7 <= endpoint <= 15.3, 'hold': hold >= 3,
                  'overshoot_fails': overshoot_failed, 'reset': value('dispensed_volume_ml') == 0,
                  'fixed_base_stable': float(np.linalg.norm(articulation.get_world_pose()[0]-initial_pose)) < 1e-4,
                  'lower_charge_present_all_states': all(s['precharge_visible'] for s in states.values()),
                  'initial_visible': states['pre_run']['column_visible'],
                  'empty_scale_hidden': not states['end_scale']['column_visible'],
                  'reset_visible': states['reset']['column_visible'],
                  'levels_match_volume': all(abs(s['surface_z']-(-0.09+0.32*s['remaining_ml']/25)) < 1e-5 for s in states.values())}
        report.update(status='pass' if all(checks.values()) else 'blocked', checks=checks,
                      states=states, runtime_version=app.app.get_app_version(), endpoint_ml=endpoint)
    except Exception as error:
        report['error'] = str(error)
    finally:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2)+'\n')
        app.close()
    return 0 if report['status'] == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())
