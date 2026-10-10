#!/usr/bin/env python3
"""Native120 free drops onto the original table; no added support collider.

Upright 50 mm clear-bottom release of both original filled containers. Reaction
logic is disabled only in this independent physical fixture. No after-Play
pose, velocity, or particle writes are performed.
"""
import argparse,json,math
from pathlib import Path

def json_scalar(value):
    import numpy as np
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)

def run(source,out,steps,body_ccd=False):
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    import numpy as np,carb,omni.usd,omni.physx
    import omni.physx.bindings._physx as pb
    from omni.isaac.core import World
    from omni.isaac.dynamic_control import _dynamic_control
    from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,Gf,Sdf,Vt,PhysicsSchemaTools
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);source=Path(source).resolve();fixture=Usd.Stage.CreateNew(str(out/'fixture.usda'));fixture.GetRootLayer().subLayerPaths=[str(source)];fixture.GetRootLayer().Save();fixture=None
    settings=carb.settings.get_settings()
    for k in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(k,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False);omni.physx.get_physx_interface().overwrite_gpu_setting(1);omni.usd.get_context().open_stage(str(out/'fixture.usda'))
    for _ in range(5):app.update()
    stage=omni.usd.get_context().get_stage();root='/World/_scene';stage.GetPrimAtPath(root+'/obj_sample_tube/ReactionRuntime').SetActive(False)
    scene=UsdPhysics.Scene.Define(stage,'/World/PhysicsScene');scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));scene.CreateGravityMagnitudeAttr(9.81);pa=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    for k,v in {'EnableGPUDynamics':True,'EnableCCD':True,'EnableStabilization':True,'BroadphaseType':'GPU','SolverType':'TGS','TimeStepsPerSecond':120,'MinPositionIterationCount':64,'MaxPositionIterationCount':64,'GpuFoundLostAggregatePairsCapacity':16384,'GpuTotalAggregatePairsCapacity':16384,'GpuMaxParticleContacts':4194304}.items():getattr(pa,'Create'+k+'Attr')().Set(v)
    cache=UsdGeom.XformCache();table_top=float(UsdGeom.BBoxCache(0,['default','render','proxy']).ComputeWorldBound(stage.GetPrimAtPath(root+'/table')).ComputeAlignedRange().GetMax()[2]);objects={};initial_energy={}
    for label,obj,xy,visuals in [('Sample','obj_sample_tube',(.25,.2),['Visual/GlassShell']),('Bath','obj_beaker',(-.25,.2),['Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh','Visual/Source/Rolled_Rim/Torus','Visual/Source/Pour_Spout/Pour_Spout_Mesh'])]:
        path=root+'/'+obj;p=stage.GetPrimAtPath(path);old=cache.GetLocalToWorldTransform(p);vertices=[]
        for rel in visuals:
            mesh=stage.GetPrimAtPath(path+'/'+rel);mat=cache.GetLocalToWorldTransform(mesh)*old.GetInverse();vertices.extend([mat.Transform(Gf.Vec3d(*v)) for v in mesh.GetAttribute('points').Get()])
        vertices=np.asarray(vertices,float);start=np.array([xy[0],xy[1],table_top+.05-vertices[:,2].min()]);new=Gf.Matrix4d().SetTranslate(Gf.Vec3d(*start));x=UsdGeom.Xformable(p);x.ClearXformOpOrder();x.AddTransformOp(opSuffix='dropFixture').Set(new);assert not UsdPhysics.RigidBodyAPI(p).GetKinematicEnabledAttr().Get()
        if body_ccd:PhysxSchema.PhysxRigidBodyAPI.Apply(p).CreateEnableCCDAttr(True)
        # Explicit initial rest is part of the fixture, authored before Play only.
        UsdPhysics.RigidBodyAPI(p).CreateVelocityAttr(Gf.Vec3f(0));UsdPhysics.RigidBodyAPI(p).CreateAngularVelocityAttr(Gf.Vec3f(0));transform=old.GetInverse()*new;points=stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'Particles')
        for name in ['points','physxParticle:simulationPoints']:
            a=points.GetAttribute(name)
            if a and a.Get() is not None:a.Set(Vt.Vec3fArray([Gf.Vec3f(*transform.Transform(Gf.Vec3d(*v))) for v in a.Get()]))
        a=points.GetAttribute('velocities');a.Set(Vt.Vec3fArray([Gf.Vec3f(*transform.TransformDir(Gf.Vec3d(*v))) for v in a.Get()]))
        mass=UsdPhysics.MassAPI(p);m=float(mass.GetMassAttr().Get());com=np.asarray(mass.GetCenterOfMassAttr().Get());inertia=np.asarray(mass.GetDiagonalInertiaAttr().Get());principal=np.asarray(Gf.Matrix3d(Gf.Quatd(mass.GetPrincipalAxesAttr().Get())));water_mass=float(UsdPhysics.MassAPI(points).GetMassAttr().Get());xyz=np.asarray(points.GetAttribute('points').Get());vel=np.asarray(points.GetAttribute('velocities').Get());particle_mass=water_mass/len(xyz)
        e=m*9.81*(start[2]+com[2]-table_top)+particle_mass*(.5*np.sum(vel*vel)+9.81*np.sum(xyz[:,2]-table_top));initial_energy[label]=float(e);objects[label]={'path':path,'prim':p,'points':points,'vertices':vertices,'mass':m,'com':com,'inertia':inertia,'principal':principal,'particle_mass':particle_mass,'particle_count':len(xyz),'start':start,'initial_com_z':float(start[2]+com[2])}
        stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System').CreateRelationship('simulationOwner').SetTargets(['/World/PhysicsScene'])
    stage.GetRootLayer().Save();world=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1.,physics_prim_path='/World/PhysicsScene',set_defaults=False);dc=_dynamic_control.acquire_dynamic_control_interface();errors=[];native=[];events=[];tick=-1
    es=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)));clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda d:native.append(float(d)))
    def contact(headers,data):
        for h in headers:
            actors=[str(PhysicsSchemaTools.intToSdfPath(h.actor0)),str(PhysicsSchemaTools.intToSdfPath(h.actor1))]
            if any(o['path'] in actors for o in objects.values()):events.append({'step':tick,'actors':actors,'colliders':[str(PhysicsSchemaTools.intToSdfPath(h.collider0)),str(PhysicsSchemaTools.intToSdfPath(h.collider1))],'points':int(h.num_contact_data),'min_separation_m':min((float(data[j].separation) for j in range(h.contact_data_offset,h.contact_data_offset+h.num_contact_data)),default=None)})
    sub=omni.physx.get_physx_simulation_interface().subscribe_contact_report_events(contact);tick=-1;world.reset();rows=[]
    for tick in range(steps):
        world.step(render=True);row={'step':tick,'native_tick':len(native),'objects':{}}
        for label,o in objects.items():
            h=dc.get_rigid_body(o['path']);pose=dc.get_rigid_body_pose(h);pos=np.array([pose.p.x,pose.p.y,pose.p.z]);q=Gf.Quatd(pose.r.w,Gf.Vec3d(pose.r.x,pose.r.y,pose.r.z));rot=np.asarray(Gf.Matrix3d(q));lv=dc.get_rigid_body_linear_velocity(h);av=dc.get_rigid_body_angular_velocity(h);v=np.array([lv.x,lv.y,lv.z]);omega=np.array([av.x,av.y,av.z]);com=o['com']@rot+pos;local_omega=omega@rot.T@o['principal'].T
            xyz=np.asarray(o['points'].GetAttribute('points').Get(),float);vel=np.asarray(o['points'].GetAttribute('velocities').Get(),float);body_ke=.5*o['mass']*float(v@v)+.5*float(np.sum(o['inertia']*local_omega*local_omega));fluid_ke=.5*o['particle_mass']*float(np.sum(vel*vel));energy=body_ke+fluid_ke+o['mass']*9.81*(com[2]-table_top)+o['particle_mass']*9.81*float(np.sum(xyz[:,2]-table_top));minimum_z=float((o['vertices']@rot+pos)[:,2].min())
            row['objects'][label]={'position':pos.tolist(),'orientation_xyzw':[pose.r.x,pose.r.y,pose.r.z,pose.r.w],'linear_velocity_m_s':v.tolist(),'angular_velocity_rad_s':omega.tolist(),'COM_z':float(com[2]),'visible_bottom_gap_m':minimum_z-table_top,'body_kinetic_J':body_ke,'fluid_kinetic_J':fluid_ke,'mechanical_energy_J':energy,'particle_count':len(xyz),'finite':bool(np.isfinite(xyz).all() and np.isfinite(vel).all() and np.isfinite(energy))}
        rows.append(row)
        if tick%60==0:(out/'progress.json').write_text(json.dumps({'last':row,'errors':errors},indent=2)+'\n')
        if errors:break
    summary={}
    for label,o in objects.items():
        data=[r['objects'][label] for r in rows];table_events=[e for e in events if o['path'] in e['actors'] and any(p.startswith(root+'/table') for p in e['actors']) and e['points']>0];peak=max(r['mechanical_energy_J'] for r in data)
        summary[label]={'mass_kg':o['mass'],'particle_mass_total_kg':o['particle_mass']*o['particle_count'],'initial_energy_J':initial_energy[label],'peak_energy_J':peak,'peak_energy_ratio':peak/initial_energy[label],'maximum_COM_rise_above_release_m':max(r['COM_z'] for r in data)-o['initial_com_z'],'minimum_visible_table_gap_m':min(r['visible_bottom_gap_m'] for r in data),'table_contact_headers':len(table_events),'first_table_contact_step':min((r['step'] for r in table_events),default=None),'final':data[-1],'gates':{'finite_inventory':all(r['finite'] and r['particle_count']==o['particle_count'] for r in data),'actual_table_contact':bool(table_events),'no_visible_crossing_gt1mm':min(r['visible_bottom_gap_m'] for r in data)>=-.001,'no_upward_launch_gt10mm':bool(max(r['COM_z'] for r in data)<=o['initial_com_z']+.01),'mechanical_energy_budget':peak<=initial_energy[label]*1.05+1e-4}}
    report={'status':'PASS' if not errors and len(rows)==steps and all(abs(d-1/120)<1e-8 for d in native) and all(all(v['gates'].values()) for v in summary.values()) else 'FAIL','scope':'Independent 50mm upright release, original table, exact input composed physical assets, bodyCCD setting separately recorded, not rack placement or robot success','source':str(source),'body_ccd_diagnostic':body_ccd,'table_top_m':table_top,'release_bottom_gap_m':.05,'post_play_writes':False,'reaction_graph_disabled_in_fixture':True,'energy_budget_rule':'Per filled container mechanical energy <= initial*1.05+0.0001 J; includes body translation/rotation, fluid kinetic and gravity relative to original table. Numerical fixture tolerance, not a universal rule.','native_clock':{'count':len(native),'min_s':min(native),'max_s':max(native),'wrong_dt':sum(abs(d-1/120)>1e-8 for d in native)},'errors':errors,'summary':summary,'rows':rows,'contacts':events};(out/'report.json').write_text(json.dumps(report,indent=2,default=json_scalar)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','contacts']},default=json_scalar),flush=True);sub=None;app.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--steps',type=int,default=480);p.add_argument('--body-ccd',action='store_true');a=p.parse_args();run(a.source,a.out,a.steps,a.body_ccd)
