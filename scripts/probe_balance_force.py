"""Independent Isaac 4.1/4.5 force-measurement feasibility fixture (not admission)."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--fixed', action='store_true')
    args = parser.parse_args()
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp
    app = SimulationApp({'headless': True, 'multi_gpu': False})
    try:
        import numpy as np
        from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf
        try:
            from isaacsim.core.api import World
            from isaacsim.core.prims import SingleArticulation as Articulation
        except ImportError:
            from omni.isaac.core import World
            from omni.isaac.core.articulations import Articulation
        world = World(stage_units_in_meters=1, physics_dt=1/120, rendering_dt=1/120)
        s = world.stage
        world.scene.add_default_ground_plane()
        root = UsdGeom.Xform.Define(s, '/World/Balance').GetPrim()
        UsdPhysics.ArticulationRootAPI.Apply(root)
        PhysxSchema.PhysxArticulationAPI.Apply(root).CreateEnabledSelfCollisionsAttr(False)

        def body(path, pos, size, mass):
            p = UsdGeom.Xform.Define(s, path).GetPrim()
            UsdGeom.Xformable(p).AddTranslateOp().Set(Gf.Vec3d(*pos))
            UsdPhysics.RigidBodyAPI.Apply(p)
            UsdPhysics.MassAPI.Apply(p).CreateMassAttr(mass)
            geom = UsdGeom.Cube.Define(s, path+'/Shape')
            geom.CreateSizeAttr(1)
            geom.AddScaleOp().Set(Gf.Vec3f(*size))
            UsdPhysics.CollisionAPI.Apply(geom.GetPrim())
            PhysxSchema.PhysxRigidBodyAPI.Apply(p).CreateSleepThresholdAttr(0)
            return p

        body('/World/Balance/Body', (0,0,.05), (.3,.3,.1), 6.8)
        body('/World/Balance/Pan', (0,0,.12), (.12,.12,.01), .05)
        j = UsdPhysics.FixedJoint.Define(s, '/World/Balance/LoadCell')
        j.CreateBody0Rel().SetTargets(['/World/Balance/Body'])
        j.CreateBody1Rel().SetTargets(['/World/Balance/Pan'])
        j.CreateLocalPos0Attr(Gf.Vec3f(0,0,.07))
        j.CreateLocalPos1Attr(Gf.Vec3f(0,0,0))
        if args.fixed:
            j = UsdPhysics.FixedJoint.Define(s, '/World/Balance/BaseFixed')
            j.CreateBody1Rel().SetTargets(['/World/Balance/Body'])
            j.CreateLocalPos0Attr(Gf.Vec3f(0,0,.05))
        body('/World/Balance/Tare', (.1,0,.12), (.01,.01,.01), .01)
        j = UsdPhysics.PrismaticJoint.Define(s, '/World/Balance/TarePress')
        j.CreateBody0Rel().SetTargets(['/World/Balance/Body'])
        j.CreateBody1Rel().SetTargets(['/World/Balance/Tare'])
        j.CreateLocalPos0Attr(Gf.Vec3f(.1,0,.07))
        j.CreateAxisAttr('Z')
        j.CreateLowerLimitAttr(0)
        j.CreateUpperLimitAttr(.0015)
        drive = UsdPhysics.DriveAPI.Apply(j.GetPrim(), 'linear')
        drive.CreateStiffnessAttr(1000)
        drive.CreateDampingAttr(50)
        drive.CreateTargetPositionAttr(0)
        body('/World/Weight', (0,0,.16), (.025,.025,.025), .03)
        a = world.scene.add(Articulation('/World/Balance', name='balance'))
        world.reset()
        a.set_joint_positions(np.array([0.0]))
        rows=[]
        for i in range(720):
            world.step(render=False)
            if i%12==0:
                rows.append({'t':i/120,'force':a.get_measured_joint_forces().tolist(),
                             'q':a.get_joint_positions().tolist()})
        report={'pid':os.getpid(), 'runtime':app.app.get_app_version(),
                'fixed':args.fixed,'body_names':a._articulation_view.body_names,'dof_names':a.dof_names,
                'rows':rows}
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(report,indent=2))
        print('BALANCE_REPORT',args.out,report['body_names'],rows[-1],flush=True)
    except BaseException:
        import traceback
        traceback.print_exc()
        sys.stderr.flush()
    finally:
        app.close()


if __name__ == '__main__':
    main()
