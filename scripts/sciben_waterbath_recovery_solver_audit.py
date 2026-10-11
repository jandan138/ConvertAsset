"""Bounded SDK property audit; getters are not per-frame executed-iteration counters."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--out',required=True);p.add_argument('--scene-max',required=True,type=int);a=p.parse_args()
from sciben_silver_bad09_probe import case_inputs,load_pickle
inputs=case_inputs(a.runtime,'mixed_5','task_12_fehling_test');metadata=load_pickle(inputs['metadata'])['task_data'];out=Path(a.out).resolve();out.mkdir(exist_ok=False);robot_asset=Path(a.runtime)/'saved/assets/robot_usds/lift2/robot.usd'
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import numpy as np,carb,omni.usd,omni.physx
import omni.physx.bindings._physx as pb
from omni.isaac.core import World
from omni.isaac.core.robots import Robot
from omni.isaac.dynamic_control import _dynamic_control
from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,Gf,Vt
f=Usd.Stage.CreateNew(str(out/'fixture.usda'));f.GetRootLayer().subLayerPaths=[str(inputs['scene'])];f.GetRootLayer().Save();f=None
settings=carb.settings.get_settings()
for key in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(key,True)
settings.set(pb.SETTING_SUPPRESS_READBACK,False);omni.physx.get_physx_interface().overwrite_gpu_setting(1);omni.usd.get_context().open_stage(str(out/'fixture.usda'))
for _ in range(5):app.update()
s=omni.usd.get_context().get_stage();root='/World/_scene';s.GetPrimAtPath(root+'/obj_sample_tube/ReactionRuntime').SetActive(False)
def pose(p,v):
 x=UsdGeom.Xformable(p);x.ClearXformOpOrder();x.AddTranslateOp(opSuffix="solverAudit").Set(Gf.Vec3d(*map(float,v['position'])));q=v['orientation'];x.AddOrientOp(opSuffix="solverAudit").Set(Gf.Quatf(float(q[0]),Gf.Vec3f(*map(float,q[1:]))));x.AddScaleOp(opSuffix="solverAudit").Set(Gf.Vec3f(*map(float,v.get('scale',[1,1,1]))))
for name,v in metadata['initial_layout'].items():
 if v['type']!='robot':pose(s.GetPrimAtPath(v['prim_path']),v)
for v in metadata['initial_particle_states'].values():
 p=s.GetPrimAtPath(v['prim_path']);xyz=np.asarray(v['points'],dtype=np.float32)
 for key in ['points','physxParticle:simulationPoints']:
  if p.GetAttribute(key):p.GetAttribute(key).Set(Vt.Vec3fArray.FromNumpy(xyz))
 p.GetAttribute('velocities').Set(Vt.Vec3fArray.FromNumpy(np.zeros_like(xyz)))
scene=UsdPhysics.Scene.Define(s,'/World/PhysicsScene');scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));scene.CreateGravityMagnitudeAttr(9.81);api=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
for key,value in {'EnableGPUDynamics':True,'EnableCCD':True,'EnableStabilization':True,'BroadphaseType':'GPU','SolverType':'TGS','TimeStepsPerSecond':120,'MinPositionIterationCount':64,'MaxPositionIterationCount':a.scene_max,'GpuFoundLostAggregatePairsCapacity':16384,'GpuTotalAggregatePairsCapacity':16384,'GpuMaxParticleContacts':8388608}.items():getattr(api,'Create'+key+'Attr')().Set(value)
for label in ['Sample','Bath']:s.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System').CreateRelationship('simulationOwner').SetTargets(['/World/PhysicsScene'])
robot_path=root+'/lift2';rp=s.DefinePrim(robot_path,'Xform');rp.GetReferences().AddReference(str(robot_asset));rinfo=metadata['initial_layout']['lift2'];pose(rp,rinfo)
w=World(physics_dt=1/120,rendering_dt=1/120,physics_prim_path='/World/PhysicsScene',set_defaults=False);robot=w.scene.add(Robot(prim_path=robot_path,name='lift2'));robot.set_solver_position_iteration_count(128);robot.set_solver_velocity_iteration_count(4);robot.set_stabilization_threshold(.005)
# Same original loader request before reset. No request override to64.
s.GetRootLayer().Save();errors=[];dt=[];es=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)));cs=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda d:dt.append(float(d)));w.reset();q=np.asarray(rinfo['joint_positions'],np.float32);robot.set_joint_positions(q);robot.set_joint_velocities(np.zeros_like(q));robot._articulation_view.set_joint_position_targets(q);dc=_dynamic_control.acquire_dynamic_control_interface()
def read():
 rows=[]
 for p in s.Traverse():
  path=str(p.GetPath())
  if p.HasAPI(UsdPhysics.ArticulationRootAPI):
   h=dc.get_articulation(path);prop=dc.get_articulation_properties(h) if h else None;rows.append({'path':path,'kind':'articulation','USD_position_request':PhysxSchema.PhysxArticulationAPI(p).GetSolverPositionIterationCountAttr().Get(),'SDK_object_position_property':int(prop.solver_position_iteration_count) if prop else None})
  if p.HasAPI(UsdPhysics.RigidBodyAPI):
   h=dc.get_rigid_body(path);prop=dc.get_rigid_body_properties(h) if h else None;rows.append({'path':path,'kind':'rigid','USD_position_request':PhysxSchema.PhysxRigidBodyAPI(p).GetSolverPositionIterationCountAttr().Get(),'SDK_object_position_property':int(prop.solver_position_iteration_count) if prop else None})
 return {'native_count':len(dt),'scene_min':api.GetMinPositionIterationCountAttr().Get(),'scene_max':api.GetMaxPositionIterationCountAttr().Get(),'PBD_USD_requests':{k:s.GetPrimAtPath(root+'/WaterbathFluid/'+k+'System').GetAttribute('solverPositionIterationCount').Get() for k in ['Sample','Bath']},'actors':rows}
rows=[read()]
for _ in range(3):w.step(render=True);rows.append(read())
result={'status':'PASS_READ_ONLY_AUDIT' if not errors else 'FAIL','scope':'Diagnostic property audit, original loader robot request128 before reset, task graph disabled. SDK object getter values are not actual executed solver-loop counters; scene constraints interpreted using installed4.1 schema. No full physics/replay qualification.','runtime_source':a.runtime,'scene_max':a.scene_max,'errors':errors,'native_clock':{'count':len(dt),'wrong_dt':sum(abs(d-1/120)>1e-8 for d in dt)},'snapshots':rows,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'robot_sha256':hashlib.sha256(robot_asset.read_bytes()).hexdigest()};(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'native_count':len(dt),'errors':errors,'last_articulations':[r for r in rows[-1]['actors'] if r['kind']=='articulation']}));app.close()
