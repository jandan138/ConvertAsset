"""Native PhysX parsed-collider and rigid mass inspection after World.reset."""
import argparse,json,time
from pathlib import Path

def run(source,out,root):
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    import omni.usd,omni.physx
    from omni.isaac.core import World
    from omni.isaac.dynamic_control import _dynamic_control
    from omni.physx.scripts.propertyQueryRigidBody import QueryManager,Query
    from pxr import Usd,PhysicsSchemaTools
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);fixture=Usd.Stage.CreateNew(str(out/'fixture.usda'));fixture.GetRootLayer().subLayerPaths=[str(Path(source).resolve())];fixture.GetRootLayer().Save();fixture=None
    omni.usd.get_context().open_stage(str(out/'fixture.usda'))
    for _ in range(5):app.update()
    stage=omni.usd.get_context().get_stage();stage.GetPrimAtPath(root+'/obj_sample_tube/ReactionRuntime').SetActive(False);omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    world=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1.,physics_prim_path='/World/PhysicsScene',set_defaults=False);errors=[];native=[];es=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)));clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda d:native.append(float(d)));world.reset();world.step(render=True);dc=_dynamic_control.acquire_dynamic_control_interface();body={}
    for name in ['obj_sample_tube','obj_beaker']:
        path=root+'/'+name;h=dc.get_rigid_body(path);props=dc.get_rigid_body_properties(h);prim=stage.GetPrimAtPath(path);body[name]={'authored_mass_kg':float(prim.GetAttribute('physics:mass').Get()),'authored_inertia_kg_m2':list(prim.GetAttribute('physics:diagonalInertia').Get()),'authored_COM_m':list(prim.GetAttribute('physics:centerOfMass').Get()),'dynamic_control_mass_kg':float(props.mass),'dynamic_control_moment_kg_m2':[float(v) for v in props.moment]}
    world.pause();queries={name:QueryManager() for name in body}
    for name,q in queries.items():q.submit_query(stage.GetPrimAtPath(root+'/'+name))
    deadline=time.monotonic()+30
    while time.monotonic()<deadline and any(q.get_query_status()==Query.Status.IN_PROGRESS for q in queries.values()):app.update()
    for name,q in queries.items():
        r=q.get_query_result();paths=[str(PhysicsSchemaTools.intToSdfPath(v)) for v in r.colliders_path_ids]
        body[name].update(query_status=q.get_query_status().name,mass_kg=float(r.mass),diagonal_inertia_kg_m2=list(r.diagonal_inertia),center_of_mass_m=list(r.center_of_mass),principal_axes_wxyz=[r.principal_axes.GetReal(),*r.principal_axes.GetImaginary()],collider_paths=paths,collider_count=len(paths),old_fine_collider_count=sum('/obj_sample_tube/WaterbathCollision/' in p for p in paths),shared_proxy_count=sum('/obj_sample_tube/RigidWallProxy/' in p for p in paths),PBD_bottom_proxy_count=sum('/obj_sample_tube/PBDBottomProxy/' in p for p in paths))
    for v in body.values():
        v['mass_inertia_COM_match']=abs(v['dynamic_control_mass_kg']-v['authored_mass_kg'])<1e-8 and all(abs(x-y)<1e-10 for x,y in zip(v['dynamic_control_moment_kg_m2'],v['authored_inertia_kg_m2'])) and all(abs(x-y)<1e-7 for x,y in zip(v['center_of_mass_m'],v['authored_COM_m']))
    result={'status':'PASS' if not errors and all(v['mass_inertia_COM_match'] for v in body.values()) and all(q.get_query_status()==Query.Status.COMPLETE for q in queries.values()) and body['obj_sample_tube']['old_fine_collider_count']==0 and body['obj_sample_tube']['shared_proxy_count']==264 else 'FAIL','scope':'Independent native PhysX property query after reset and 1 step, then paused for read-only query completion. No containment/robot qualification.','source':str(Path(source).resolve()),'native_ticks_before_pause':len(native),'errors':errors,'bodies':body};(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({**result,'bodies':{k:{a:b for a,b in v.items() if a!='collider_paths'} for k,v in body.items()}}),flush=True);app.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--root',default='/World');a=p.parse_args();run(a.source,a.out,a.root)
