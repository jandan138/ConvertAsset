#!/usr/bin/env python3
"""Actual task USD reaction gate under bounded native kinematic interventions.

No robot/action demonstration. Particle seed is transformed once before Play;
then fluid and bath remain dynamic. No post-Play particle writes.
"""
import argparse,json,math
from pathlib import Path

def run(source,out,bottom_manifest=None,expected_script_sha=None,max_particle_contacts=4194304,scene_max_position_iterations=64):
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    import numpy as np,carb,omni.usd,omni.physx
    import omni.physics.tensors as tensors
    import omni.physx.bindings._physx as pb
    from omni.isaac.core import World
    from omni.isaac.dynamic_control import _dynamic_control
    from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,Gf,Sdf,Vt,PhysicsSchemaTools
    from sciben_waterbath_recovery_events import patch_source
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);source=Path(source).resolve()
    fixture=Usd.Stage.CreateNew(str(out/'fixture.usda'));fixture.GetRootLayer().subLayerPaths=[str(source)];fixture.GetRootLayer().Save();fixture=None
    settings=carb.settings.get_settings();settings.set_bool('/app/omni.graph.scriptnode/enable_opt_in',False);settings.set_bool('/app/omni.graph.scriptnode/opt_in',True)
    for k in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(k,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False);omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    omni.usd.get_context().open_stage(str(out/'fixture.usda'))
    for _ in range(5):app.update()
    stage=omni.usd.get_context().get_stage();root='/World/_scene';tube=root+'/obj_sample_tube';bath=root+'/obj_beaker';heater=root+'/obj_magnetic_stirrer'
    tp=stage.GetPrimAtPath(tube);config=json.loads(tp.GetAttribute('repair:waterbath_config').Get());namespace=config['namespace']
    if bottom_manifest:
        from sciben_waterbath_recovery_bottom_proxy import author as author_bottom
        author_bottom(stage,root,json.loads(Path(bottom_manifest).read_text())['liquids']['Sample']['cavity_profile_m'])
    scripts=[a for p in Usd.PrimRange(tp.GetChild('ReactionRuntime')) for a in p.GetAttributes() if a.GetName()=='inputs:script' and a.Get()];assert len(scripts)==1
    import hashlib
    code=scripts[0].Get()
    if 'state.repair_contacts.get_contact_data(1/120)' in code:code=patch_source(code,keep_tensor_view=False,persistent=True);scripts[0].Set(code)
    elif not expected_script_sha:raise ValueError('Precomposed reaction requires explicit expected script hash')
    loaded_script_sha=hashlib.sha256(code.encode()).hexdigest()
    if expected_script_sha and loaded_script_sha!=expected_script_sha:raise ValueError('Unexpected candidate reaction script')
    (out/'loaded_reaction_script.py').write_text(code)

    scene=UsdPhysics.Scene.Define(stage,'/World/PhysicsScene');scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));scene.CreateGravityMagnitudeAttr(9.81);pa=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    for k,v in {'EnableGPUDynamics':True,'EnableCCD':True,'EnableStabilization':True,'BroadphaseType':'GPU','SolverType':'TGS','TimeStepsPerSecond':120,'MinPositionIterationCount':64,'MaxPositionIterationCount':scene_max_position_iterations,'GpuFoundLostAggregatePairsCapacity':16384,'GpuTotalAggregatePairsCapacity':16384,'GpuMaxParticleContacts':max_particle_contacts}.items():getattr(pa,'Create'+k+'Attr')().Set(v)
    cache=UsdGeom.XformCache();old=cache.GetLocalToWorldTransform(tp);bp=np.array(cache.GetLocalToWorldTransform(stage.GetPrimAtPath(bath)).ExtractTranslation());hm=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(heater));hp=np.array(hm.ExtractTranslation());hq=hm.ExtractRotationQuat();heater_q=np.array([*hq.GetImaginary(),hq.GetReal()],np.float32)
    start=bp+np.array([0,0,.02]);x=UsdGeom.Xformable(tp);x.ClearXformOpOrder();x.AddTranslateOp(opSuffix='gateFixture').Set(Gf.Vec3d(*start));x.AddOrientOp(opSuffix='gateFixture').Set(Gf.Quatf(1));UsdPhysics.RigidBodyAPI(tp).CreateKinematicEnabledAttr(True);UsdPhysics.RigidBodyAPI.Apply(stage.GetPrimAtPath(heater)).CreateKinematicEnabledAttr(True)
    for path in [tube,heater]:PhysxSchema.PhysxRigidBodyAPI.Apply(stage.GetPrimAtPath(path)).CreateEnableCCDAttr(False)  # Kinematic-only fixture; unsupported CCD is not ignored.
    transform=old.GetInverse()*Gf.Matrix4d().SetTranslate(Gf.Vec3d(*start));sample=stage.GetPrimAtPath(root+'/WaterbathFluid/SampleParticles')
    for name in ['points','physxParticle:simulationPoints']:
        a=sample.GetAttribute(name)
        if a and a.Get() is not None:a.Set(Vt.Vec3fArray([Gf.Vec3f(*transform.Transform(Gf.Vec3d(*v))) for v in a.Get()]))
    a=sample.GetAttribute('velocities');a.Set(Vt.Vec3fArray([Gf.Vec3f(*transform.TransformDir(Gf.Vec3d(*v))) for v in a.Get()]))
    for label in ['Sample','Bath']:stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System').CreateRelationship('simulationOwner').SetTargets(['/World/PhysicsScene'])
    stage.GetRootLayer().Save();world=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1.,physics_prim_path='/World/PhysicsScene',set_defaults=False)
    errors=[];native=[];es=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)));clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda d:native.append(float(d)))
    world.reset();view=tensors.create_simulation_view('numpy');view.set_subspace_roots('/');tv=view.create_rigid_body_view(tube);hv=view.create_rigid_body_view(heater);bv=view.create_rigid_body_view(bath);held_bath=None;dc=_dynamic_control.acquire_dynamic_control_interface();rows=[];previous=np.zeros(3)
    phases=[('centered',2.,[0,0,0]),('touch_wall',2.,[.027,0,0]),('restore_center',2.,[0,0,0]),('off_center',1.,[0,.025,0]),('restore_plate',2.,[0,0,0]),('tilt_plate',1.,[0,0,7.]),('restore_level',2.,[0,0,0]),('epoch_reset',1.,[0,0,0])]
    for phase,duration,goal in phases:
        if phase=='off_center':
            held_bath=bv.get_transforms().copy()
            PhysxSchema.PhysxRigidBodyAPI.Apply(stage.GetPrimAtPath(bath)).CreateEnableCCDAttr(False)
            UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath(bath)).CreateKinematicEnabledAttr(True)
        if phase=='epoch_reset':a=stage.GetPrimAtPath(root).GetAttribute('repair:episode_revision');a.Set(int(a.Get() or 0)+1)
        goal=np.array(goal,float);steps=round(duration*120)
        for i in range(steps):
            alpha=min(1.,(i+1)/(steps*.6));smooth=alpha*alpha*(3-2*alpha);v=previous+(goal-previous)*smooth
            # Tiny ongoing native target motion establishes observable awake state after epoch reset.
            z_dither=.0001*math.sin(2*math.pi*i/120) if phase in ['centered','epoch_reset'] else 0
            pos=start+np.array([v[0],0,z_dither]);tv.set_kinematic_targets(np.array([[*pos,0,0,0,1]],np.float32),np.array([0],np.uint32))
            if held_bath is not None:bv.set_kinematic_targets(held_bath,np.array([0],np.uint32))
            q=Gf.Quatd(math.cos(math.radians(v[2])/2),Gf.Vec3d(math.sin(math.radians(v[2])/2),0,0))*Gf.Quatd(hq)
            hv.set_kinematic_targets(np.array([[*(hp+np.array([v[1],0,0])),*q.GetImaginary(),q.GetReal()]],np.float32),np.array([0],np.uint32));world.step(render=True)
            state={k:tp.GetAttribute(namespace+':'+k).Get() for k in ['pbd_valid','heating_enabled','heating_block_reason','wall_contact_count','heated_seconds','runtime_error','immersed']};poses={}
            for label,path in [('bath',bath),('heater',heater),('tube',tube)]:
                pose=dc.get_rigid_body_pose(dc.get_rigid_body(path));poses[label]={'position':[pose.p.x,pose.p.y,pose.p.z],'orientation_xyzw':[pose.r.x,pose.r.y,pose.r.z,pose.r.w]}
            sleeping={name:bool(omni.physx.get_physx_simulation_interface().is_sleeping(omni.usd.get_context().get_stage_id(),PhysicsSchemaTools.sdfPathToInt(path))) for name,path in [('tube',tube),('bath',bath)]}
            r={'sleeping':sleeping,'poses':poses,'phase':phase,'phase_step':i,'native_tick':len(native),'state':state};rows.append(r)
            if errors:break
            if i%120==0 or i==steps-1:(out/'progress.json').write_text(json.dumps({'last':r,'errors':errors},indent=2)+'\n')
        previous=goal
        if errors:break
    summary={phase:{'enabled_frames':sum(r['state']['heating_enabled'] is True for r in rows if r['phase']==phase),'reasons':sorted(set(str(r['state']['heating_block_reason']) for r in rows if r['phase']==phase)),'max_contacts':max((int(r['state']['wall_contact_count'] or 0) for r in rows if r['phase']==phase),default=0)} for phase,_,_ in phases}
    inventory={label:len(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'Particles').GetAttribute('points').Get()) for label in ['Sample','Bath']}
    gates={'centered_heats':summary['centered']['enabled_frames']>0,'wall_stops':'tube_touches_beaker' in summary['touch_wall']['reasons'],'off_center_stops':'bath_off_center' in summary['off_center']['reasons'],'tilt_stops':'tilted_bath_or_heater' in summary['tilt_plate']['reasons'],'restored_center_heats':summary['restore_center']['enabled_frames']>0,'restored_plate_heats':summary['restore_plate']['enabled_frames']>0,'restored_level_heats':summary['restore_level']['enabled_frames']>0,'epoch_heats':summary['epoch_reset']['enabled_frames']>0}
    def hold_pass(phase,reason=None):
        tail=[r['state'] for r in rows if r['phase']==phase][-30:]
        if len(tail)!=30 or not all(r['pbd_valid'] and r['immersed'] and not r['runtime_error'] for r in tail):return False
        elapsed=float(tail[-1]['heated_seconds'])-float(tail[0]['heated_seconds'])
        if reason:return all(not r['heating_enabled'] and r['heating_block_reason']==reason for r in tail) and abs(elapsed)<1e-8
        return all(r['heating_enabled'] for r in tail) and elapsed>.2
    gates.update(centered_hold=hold_pass('centered'),wall_hold=hold_pass('touch_wall','tube_touches_beaker'),offcenter_hold=hold_pass('off_center','bath_off_center'),tilt_hold=hold_pass('tilt_plate','tilted_bath_or_heater'),restore_center_hold=hold_pass('restore_center'),restore_plate_hold=hold_pass('restore_plate'),restore_level_hold=hold_pass('restore_level'),epoch_hold=hold_pass('epoch_reset'))
    result={'status':'PASS' if all(gates.values()) and not errors and all(abs(d-1/120)<1e-8 for d in native) else 'FAIL','scope':'Actual task reaction graph and dynamic fluid under isolated kinematic tube/heater interventions; no task success claim','source':str(source),'namespace':namespace,'loaded_script_sha256':loaded_script_sha,'native_count':len(native),'native_clock':{'min_s':min(native),'max_s':max(native),'wrong_dt':sum(abs(d-1/120)>1e-8 for d in native)},'max_particle_contacts':max_particle_contacts,'scene_iteration_bounds':{'min':pa.GetMinPositionIterationCountAttr().Get(),'max':pa.GetMaxPositionIterationCountAttr().Get()},'bottom_hybrid_manifest':str(bottom_manifest) if bottom_manifest else None,'errors':errors,'gates':gates,'phase_summary':summary,'inventory':inventory,'particle_seed_remap_before_play_only':True,'fixture_constraints':'Tube and heater prescribed throughout; bath dynamic for centered/wall/restore_center, then explicitly held kinematic for offcenter and later pose-gate isolation. Liquid remains dynamic. Not free-body qualification.','rows':rows};(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True);app.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--bottom-hybrid-manifest');p.add_argument('--expected-script-sha');p.add_argument('--max-particle-contacts',type=int,default=4194304);p.add_argument('--scene-max-position-iterations',type=int,default=64);a=p.parse_args();run(a.source,a.out,a.bottom_hybrid_manifest,a.expected_script_sha,a.max_particle_contacts,a.scene_max_position_iterations)
