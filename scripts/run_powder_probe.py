"""Bounded Isaac 4.5 powder qualification fixture, with recorded physical states."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=22)
    parser.add_argument('--mode', choices=['settle', 'scoop'], default='scoop')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    report = {'status': 'failed', 'scene_sha256': hashlib.sha256(args.scene.read_bytes()).hexdigest()}
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp
    app = SimulationApp({'headless': True, 'multi_gpu': False})
    try:
        import numpy as np
        import omni.usd
        import omni.physx
        import omni.physics.tensors as tensors
        import carb.settings
        from pxr import Usd, Gf
        from isaacsim.core.api import World
        from isaacsim.core.prims import RigidPrim
        meta = json.loads(args.scene.with_suffix('.json').read_text())
        cfg = meta['config']
        hz = cfg['physics_hz']
        dt = 1 / hz
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        ctx = omni.usd.get_context()
        ctx.open_stage(str(args.scene.resolve()))
        while ctx.get_stage_loading_status()[2]:
            app.update()
        stage = ctx.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        registry = Usd.SchemaRegistry()
        checked = set()
        for prim in stage.Traverse():
            names = prim.GetAppliedSchemas()
            definitions = [registry.FindAppliedAPIPrimDefinition(n) for n in names if n.startswith('Physx')]
            for attr in prim.GetAuthoredAttributes():
                key = (tuple(names), attr.GetName(), str(attr.GetTypeName()))
                if not attr.GetName().startswith('physx') or key in checked:
                    continue
                declared = [d.GetSchemaAttributeSpec(attr.GetName()) for d in definitions if d]
                declared = [d for d in declared if d]
                if not declared or declared[0].typeName != attr.GetTypeName():
                    raise RuntimeError('Unsupported or mistyped attribute: ' + str(attr.GetPath()))
                checked.add(key)
        world = World(physics_dt=dt, rendering_dt=1/30, physics_prim_path='/World/PhysicsScene', set_defaults=False)
        world.get_physics_context().enable_gpu_dynamics(True)
        world.get_physics_context().set_broadphase_type('GPU')
        powder = world.scene.add(RigidPrim('/World/Powder/g_.*', name='powder', reset_xform_properties=False))
        world.reset()
        settings = carb.settings.get_settings()
        settings.set_bool('/physics/updateToUsd', False)
        settings.set_bool('/physics/updateVelocitiesToUsd', False)
        sim = tensors.create_simulation_view('numpy')
        sim.set_subspace_roots('/')
        spoon_view = sim.create_rigid_body_view('/World/Spoon')
        target = spoon_view.get_transforms().copy()
        indices = np.array([0], dtype=np.uint32)
        grain_view = sim.create_rigid_body_view('/World/Powder/g_*')
        inertia = grain_view.get_inertias().reshape(-1,3,3)
        report['runtime_inertia_diagonal_range'] = [np.diagonal(inertia,axis1=1,axis2=2).min(0).tolist(), np.diagonal(inertia,axis1=1,axis2=2).max(0).tolist()]
        report['runtime_scene'] = {a.GetName(): str(a.Get()) for a in stage.GetPrimAtPath('/World/PhysicsScene').GetAuthoredAttributes()}
        masses = np.asarray(powder.get_masses()).reshape(-1)
        if len(masses) != cfg['count'] or not np.allclose(masses, meta['mass_per_grain_kg'], rtol=1e-4, atol=1e-12):
            raise RuntimeError('Runtime count or masses differ from source')
        waypoints = [(0,(-.007,0,.040),0),(3,(-.007,0,.040),0),
            (5,(-.007,0,.008),0),(7,(.007,0,.008),0),
            (9,(.007,0,.040),0),(13,(.070,0,.040),0),
            (15,(.070,0,.024),100),(17,(.070,0,.040),100),(20,(.115,0,.045),0)]
        def command(t):
            if args.mode == 'settle':
                return np.array(waypoints[0][1]), 0.
            for (ta,pa,aa),(tb,pb,ab) in zip(waypoints,waypoints[1:]):
                if ta <= t <= tb:
                    s = (t-ta)/(tb-ta)
                    s = s*s*(3-2*s)
                    return (1-s)*np.array(pa)+s*np.array(pb), (1-s)*aa+s*ab
            return np.array(waypoints[-1][1]), float(waypoints[-1][2])
        rows, positions, orientations, tools, times, step_ms = [], [], [], [], [], []
        start = time.perf_counter()
        for i in range(round(args.seconds*hz)):
            t = i*dt
            pos, angle = command(t)
            q = Gf.Rotation(Gf.Vec3d(0,1,0), angle).GetQuat()
            target[0] = [*pos, *q.GetImaginary(), q.GetReal()]
            spoon_view.set_kinematic_targets(target, indices)
            tick = time.perf_counter()
            omni.physx.get_physx_interface().update_simulation(dt, t)
            omni.physx.get_physx_simulation_interface().fetch_results()
            step_ms.append((time.perf_counter()-tick)*1000)
            if i % (hz//30):
                continue
            p, rot = powder.get_world_poses(usd=False)
            p, rot = np.array(p), np.array(rot)
            v = np.asarray(powder.get_linear_velocities())
            if not np.isfinite(p).all() or not np.isfinite(v).all():
                raise RuntimeError('Nonfinite physical state')
            in_pan = (abs(p[:,0]-.070)<.017)&(abs(p[:,1])<.015)&(p[:,2]>.0055)&(p[:,2]<.025)
            in_source = (abs(p[:,0])<.016)&(abs(p[:,1])<.013)&(p[:,2]>.0055)&(p[:,2]<.03)
            row = dict(time_s=t+dt, pan_count=int(in_pan.sum()), source_count=int(in_source.sum()),
                       below_ground_count=int((p[:,2]<-.001).sum()), moving_fraction=float((np.linalg.norm(v,axis=1)>.002).mean()),
                       p95_speed=float(np.percentile(np.linalg.norm(v,axis=1),95)), min_xyz=p.min(0).tolist(), max_xyz=p.max(0).tolist())
            rows.append(row)
            positions.append(p.astype('float32'))
            orientations.append(rot.astype('float32'))
            observed_tool = spoon_view.get_transforms()[0].copy()
            tools.append(observed_tool[[0,1,2,6,3,4,5]])
            times.append(t+dt)
            if i % hz == 0:
                print('SAMPLE', row, 'step_ms', step_ms[-1], flush=True)
        report.update(status='observed', runtime=app.app.get_app_version(), config=cfg, mode=args.mode,
                      physics_dt=dt, mass_per_grain_kg=float(masses[0]), rows=rows,
                      wall_seconds=time.perf_counter()-start,
                      step_ms_p50=float(np.percentile(step_ms,50)), step_ms_p95=float(np.percentile(step_ms,95)),
                      checked_signatures=len(checked), robot_grasp_verified=False)
        np.savez_compressed(args.out/'states.npz', times=times, positions=positions, orientations=orientations,
                            tools=tools, masses=masses, paths=np.array(powder.prim_paths))
        report['checks'] = {'finite': True, 'no_below_ground': not any(r['below_ground_count'] for r in rows),
                            'transfer': args.mode == 'settle' or rows[-1]['pan_count'] > 50}
        report['status'] = 'passed' if all(report['checks'].values()) else 'failed'
    except BaseException:
        report['exception'] = traceback.format_exc()
        print(report['exception'], flush=True)
    finally:
        (args.out/'report.json').write_text(json.dumps(report, indent=2))
        print('REPORT', args.out, report['status'], flush=True)
        app.close(wait_for_replicator=False)


if __name__ == '__main__':
    main()
