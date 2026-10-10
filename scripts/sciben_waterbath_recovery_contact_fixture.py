#!/usr/bin/env python3
"""Isolated native4.1 contact-read conformance, including actual sleeping touch."""
import argparse,json
from pathlib import Path

def run(out):
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    import omni.usd,omni.physx
    import omni.physics.tensors as tensors
    from omni.isaac.core import World
    from omni.isaac.dynamic_control import _dynamic_control
    from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf,PhysicsSchemaTools
    from sciben_waterbath_recovery_events import contact_header_count,PersistentContactCounts,PERSISTENT_EMBEDDED
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    world=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1.,physics_prim_path='/World/PhysicsScene')
    stage=omni.usd.get_context().get_stage();sim=omni.physx.get_physx_simulation_interface();dc=_dynamic_control.acquire_dynamic_control_interface()
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    physics=PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath('/World/PhysicsScene'));physics.CreateEnableGPUDynamicsAttr(True);physics.CreateBroadphaseTypeAttr('GPU');physics.CreateSolverTypeAttr('TGS');physics.CreateTimeStepsPerSecondAttr(120)
    for name,scale,z,kinematic in [('bath',(.1,.1,.02),0,True),('tube',(.02,.02,.02),.04,False)]:
        m=UsdGeom.Cube.Define(stage,'/World/'+name);m.CreateSizeAttr(1);m.AddTranslateOp().Set(Gf.Vec3d(0,0,z));m.AddOrientOp().Set(Gf.Quatf(1));m.AddScaleOp().Set(Gf.Vec3f(*scale));p=m.GetPrim();UsdPhysics.CollisionAPI.Apply(p);b=UsdPhysics.RigidBodyAPI.Apply(p);b.CreateKinematicEnabledAttr(kinematic);UsdPhysics.MassAPI.Apply(p).CreateMassAttr(.18 if kinematic else .018);PhysxSchema.PhysxContactReportAPI.Apply(p).CreateThresholdAttr(0.)
    stage.GetRootLayer().Export(str(out/'fixture.usda'))
    native=[];errors=[];clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda dt:native.append(float(dt)));error=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)))
    from types import SimpleNamespace
    runtime={'PersistentContactCounts':PersistentContactCounts,'cleanup':lambda db:None};exec(PERSISTENT_EMBEDDED,runtime)
    state=SimpleNamespace();rows=[];events=[]
    subscription=sim.subscribe_contact_report_events(lambda headers,data:events.extend(headers))
    def capture(phase,step,view,counter,late,epoch):
        headers,data=sim.get_contact_report();decode=lambda v:str(PhysicsSchemaTools.intToSdfPath(v));immediate=contact_header_count(headers,'/World/tube','/World/bath',8192,decode);event=contact_header_count(events,'/World/tube','/World/bath',8192,decode);tensor=int(view.get_contact_data(1/120)[4].sum());h=dc.get_rigid_body('/World/tube');pose=dc.get_rigid_body_pose(h)
        sleeping=sim.is_sleeping(omni.usd.get_context().get_stage_id(),PhysicsSchemaTools.sdfPathToInt('/World/tube'))
        try:active=runtime['_repair_persistent_contact_count'](counter,epoch,step,'/World/tube','/World/bath',8192);active_error=None
        except RuntimeError as exc:active=None;active_error=str(exc)
        try:late_count=runtime['_repair_persistent_contact_count'](late,epoch,step,'/World/tube','/World/bath',8192) if late else None;late_error=None
        except RuntimeError as exc:late_count=None;late_error=str(exc)
        rows.append({'active_pair_count':active,'active_error':active_error,'late_count':late_count,'late_error':late_error,'phase':phase,'step':step,'native_tick':len(native),'immediate':immediate,'events':event,'tensor':tensor,'sleeping':sleeping,'bottom_gap_m':float(pose.p.z)-.02})
    for iteration in range(3):
        epoch=min(iteration,1)  # third restart tests index rollback even with epoch unchanged
        world.reset();v=tensors.create_simulation_view('numpy');v.set_subspace_roots('/');cv=v.create_rigid_contact_view(['/World/tube'],filter_patterns=[['/World/bath']],max_contact_data_count=8192)
        counter=state;late=None
        for i in range(780):
            if i==600:late=SimpleNamespace();sim.put_to_sleep(omni.usd.get_context().get_stage_id(),PhysicsSchemaTools.sdfPathToInt('/World/tube'))
            if i==660:
                h=dc.get_rigid_body('/World/tube');pose=dc.get_rigid_body_pose(h);pose.p.z=.2;dc.set_rigid_body_pose(h,pose);dc.set_rigid_body_linear_velocity(h,(0,0,0));dc.wake_up_rigid_body(h)
            events.clear();world.step(render=False);capture(('reset' if epoch else 'initial')+('_settle' if i<600 else '_forced_sleep' if i<660 else '_released'),i,cv,counter,late,epoch)
        world.stop();cv=None;v=None
    sleepy=[r for r in rows if r['sleeping'] and abs(r['bottom_gap_m'])<.001]
    missing=[r for r in sleepy if not r['active_pair_count']]
    late_sleep=[r for r in sleepy if r['step']>=600 and r['step']<660]
    released=[r for r in rows if r['step']==665]
    late_gate=bool(late_sleep) and all(r['late_error'] or r['late_count'] for r in late_sleep)
    release_gate=len(released)==3 and all(r['active_pair_count']==0 and r['late_count']==0 for r in released)
    runtime['cleanup'](SimpleNamespace(per_instance_state=state))
    cleanup_gate=state.repair_pair_key is None and state.repair_pair_counter is None and state.repair_pair_last_index==-1
    report={'cleanup_gate':cleanup_gate,'embedded_runtime_wrapper_exercised':True,'epoch_and_index_reset_exercised':True,'status':'PASS' if not errors and not missing and bool(sleepy) and late_gate and release_gate and cleanup_gate and all(abs(x-1/120)<1e-8 for x in native) else 'FAIL','scope':'Isolated boxes, not task engine or scientific success qualification','native_count':len(native),'errors':errors,'sleeping_touch_frames':len(sleepy),'active_missing_sleeping_touch_frames':len(missing),'late_initialization_fail_closed':late_gate,'release_gate':release_gate,'immediate_missing_sleeping_touch_frames':sum(r['immediate']==0 for r in sleepy),'tensor_missing_sleeping_touch_frames':sum(r['tensor']==0 for r in sleepy),'immediate_event_mismatch_frames':sum(r['immediate']!=r['events'] for r in rows),'rows':rows}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True);subscription=None;clock=None;error=None;app.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();run(a.out)
