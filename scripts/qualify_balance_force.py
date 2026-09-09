"""Measure the repaired balance with actual PhysX loads in independent processes."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--asset', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--init', choices=['omitted','zero','pressed'], default='zero')
    p.add_argument('--gpu', action='store_true')
    p.add_argument('--prefix',default='/World/obj_analytical_balance')
    args = p.parse_args()
    args.asset = args.asset.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp
    app = SimulationApp({'headless':True, 'multi_gpu':False})
    report = {'status':'failed','pid':os.getpid(),'initialization':args.init,
              'asset_sha256':hashlib.sha256((args.asset.parent/'asset.usda').read_bytes()).hexdigest(),
              'entry_sha256':hashlib.sha256(args.asset.read_bytes()).hexdigest(),'prefix':args.prefix}
    try:
        import numpy as np
        from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf
        try:
            from isaacsim.core.api import World
            from isaacsim.core.prims import SingleArticulation as Articulation
            from isaacsim.core.api.objects import DynamicCuboid
        except ImportError:
            from omni.isaac.core import World
            from omni.isaac.core.articulations import Articulation
            from omni.isaac.core.objects import DynamicCuboid
        report['runtime']=app.app.get_app_version()
        world=World(stage_units_in_meters=1,physics_dt=1/120,rendering_dt=1/120)
        stage=world.stage
        if args.gpu:
            world.get_physics_context().enable_gpu_dynamics(True)
            world.get_physics_context().set_broadphase_type('GPU')
        report['gpu']=args.gpu
        floor=UsdGeom.Cube.Define(stage,'/World/Floor')
        floor.CreateSizeAttr(1)
        floor.AddTranslateOp().Set(Gf.Vec3d(0,0,-.05))
        floor.AddScaleOp().Set(Gf.Vec3f(5,5,.1))
        UsdPhysics.CollisionAPI.Apply(floor.GetPrim())
        root=args.prefix
        prim=stage.DefinePrim(root,'Xform')
        prim.GetReferences().AddReference(str(args.asset),'/World/obj_analytical_balance')
        cache=UsdGeom.BBoxCache(0,['default'])
        feet=cache.ComputeWorldBound(stage.GetPrimAtPath(root+'/Instance/Body/Feet')).ComputeAlignedRange()
        prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(0,0,-feet.GetMin()[2]+.001))
        a=world.scene.add(Articulation(root,name='balance'))
        weights={}
        for idx,mass in enumerate([1,10,30,50,100,200]):
            weights[mass]=world.scene.add(DynamicCuboid('/World/Weight_'+str(mass),name='weight_'+str(mass),
                position=np.array([1+idx*.05,0,.1]),scale=np.array([.02,.02,.02]),mass=mass/1000))
        for w in weights.values():
            api=PhysxSchema.PhysxRigidBodyAPI.Apply(stage.GetPrimAtPath(w.prim_path))
            api.CreateSleepThresholdAttr(0)
            api.CreateStabilizationThresholdAttr(0)
        weight=weights[30]
        world.reset()
        view=a._articulation_view
        pan_index=view.body_names.index('WeighingPan')
        tare_index=a.dof_names.index('RightTarePress')
        if args.init!='omitted':
            a.set_joint_positions(np.array([.001 if args.init=='pressed' else 0.]),joint_indices=np.array([tare_index]))
        from omni.isaac.dynamic_control import _dynamic_control
        dc=_dynamic_control.acquire_dynamic_control_interface()
        pan_handle=dc.get_rigid_body(root+'/Instance/WeighingPan')
        report['body_names']=view.body_names
        report['dof_names']=a.dof_names
        samples=[]
        cases=[]
        tick=0
        filtered=None
        def steps(n,label,expected):
            nonlocal tick,filtered
            rows=[]
            for _ in range(n):
                world.step(render=False)
                tick+=1
                force=a.get_measured_joint_forces()[pan_index]
                raw=float(force[2])/9.81*1000-50
                filtered=raw if filtered is None else filtered+(1-math.exp(-1/120/.25))*(raw-filtered)
                row=dict(t=tick/120,case=label,raw_g=raw,filtered_g=filtered,
                         tare_m=float(a.get_joint_positions()[tare_index]))
                if tick%4==0:
                    samples.append(row)
                    rows.append(row)
            tail=[r['filtered_g'] for r in rows[-30:]]
            item=dict(name=label,expected_g=expected,mean_g=sum(tail)/len(tail),
                      error_g=max(abs(v-expected) for v in tail),range_g=max(tail)-min(tail))
            cases.append(item)
            print('CASE',item,flush=True)
        def place(mass_g,offset=0):
            nonlocal weight
            for idx,w in enumerate(weights.values()):
                w.set_world_pose(np.array([1+idx*.05,0,.1]))
                w.set_linear_velocity(np.zeros(3))
                w.set_angular_velocity(np.zeros(3))
            weight=weights.get(mass_g,weights[30])
            weight.set_linear_velocity(np.zeros(3))
            weight.set_angular_velocity(np.zeros(3))
            print('MASS',mass_g,weight.get_mass(),flush=True)
            if mass_g:
                pose=dc.get_rigid_body_pose(pan_handle)
                # Source pan top is z=.1659, y=.020 in its rigid body's frame.
                local=Gf.Vec3d(offset,.020,.1659+.011)
                q=Gf.Quatd(pose.r.w,Gf.Vec3d(pose.r.x,pose.r.y,pose.r.z))
                pt=Gf.Rotation(q).TransformDir(local)+Gf.Vec3d(pose.p.x,pose.p.y,pose.p.z)
                weight.set_world_pose(np.array(pt))
            else:
                weight.set_world_pose(np.array([1.,0.,.1]))
        steps(480,'empty',0)
        for mass,offset in [(1,0),(10,0),(30,0),(30,.035),(50,0),(100,0),(200,0)]:
            place(mass,offset)
            steps(480,f'load_{mass}_{offset}',mass)
        place(0)
        steps(480,'unload',0)
        origin,q=a.get_world_pose()
        # Prescribed rigid-body placement tests transfer the entire articulation,
        # not a claim of robot grasp success.
        a.set_world_pose(origin+np.array([.15,0,.2]),q)
        for _ in range(120):
            world.step(render=False)
        a.set_world_pose(origin+np.array([.15,0,0]),q)
        a.set_linear_velocity(np.zeros(3))
        a.set_angular_velocity(np.zeros(3))
        steps(600,'move_recovery_empty',0)
        place(30)
        steps(480,'move_recovery_load',30)
        for _ in range(3):
            a.set_joint_positions(np.array([0.]),joint_indices=np.array([tare_index]))
            for _ in range(20):
                world.step(render=False)
        report.update(status='measured',cases=cases,samples=samples,
                      protocol='known_rigid_loads_and_prescribed_articulation_transfer',robot_grasp_verified=False)
    except BaseException:
        import traceback
        report['exception']=traceback.format_exc()
        print(report['exception'],flush=True)
    finally:
        args.out.write_text(json.dumps(report,indent=2))
        print('REPORT',args.out,report['status'],flush=True)
        app.close()


if __name__=='__main__':
    main()
