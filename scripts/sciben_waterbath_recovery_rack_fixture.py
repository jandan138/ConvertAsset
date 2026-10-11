"""Dynamic slot drop with real particles; independent bounded support fixture."""
import argparse,json,hashlib,importlib.util
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--out',required=True);p.add_argument('--raise-m',type=float,default=.12);p.add_argument('--release-gap-m',type=float,default=.005);p.add_argument('--max-particle-contacts',type=int,default=8388608);p.add_argument('--manifest',required=True);p.add_argument('--steps',type=int,default=600);args=p.parse_args()
producer=Path(__file__).with_name('sciben_silver_bad09_probe.py');spec=importlib.util.spec_from_file_location('producer',producer);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);inputs=module.case_inputs(args.baseline,'mixed_17');meta=module.load_pickle(inputs['metadata'])['task_data'];inputs['consumer_geometry']=Path(__file__).resolve().parent.parent/'outputs/sciben_waterbath_120hz_20261010/consumer_geometry.json';inputs['manifest']=Path(args.manifest).resolve();manifest=json.loads(inputs['manifest'].read_text());out=Path(args.out).resolve();out.mkdir(exist_ok=False)
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import numpy as np,carb,omni.usd,omni.physx
import omni.physx.bindings._physx as pb
from omni.isaac.core import World
from omni.isaac.dynamic_control import _dynamic_control
from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,PhysicsSchemaTools,Gf,Vt
root='/World/_scene';tube=root+'/obj_sample_tube';rack=root+'/obj_tube_rack'
f=Usd.Stage.CreateNew(str(out/'fixture.usda'));f.GetRootLayer().subLayerPaths=[str(inputs['scene'])];f.GetRootLayer().Save();f=None
settings=carb.settings.get_settings()
for k in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(k,True)
settings.set(pb.SETTING_SUPPRESS_READBACK,False);omni.physx.get_physx_interface().overwrite_gpu_setting(1)
omni.usd.get_context().open_stage(str(out/'fixture.usda'))
for _ in range(5):app.update()
s=omni.usd.get_context().get_stage()
s.GetPrimAtPath(tube+'/ReactionRuntime').SetActive(False)
particle_shift_z=args.raise_m if args.release_gap_m is None else 0.
for name,info in meta['initial_layout'].items():
 if info['type']=='robot':continue
 prim=s.GetPrimAtPath(info['prim_path']);x=UsdGeom.Xformable(prim);x.ClearXformOpOrder();pos=np.asarray(info['position'],float)+(np.array([0,0,particle_shift_z]) if str(prim.GetPath())==tube else 0);x.AddTranslateOp(opSuffix='supportFixture').Set(Gf.Vec3d(*pos));q=info['orientation'];x.AddOrientOp(opSuffix='supportFixture').Set(Gf.Quatf(float(q[0]),Gf.Vec3f(*map(float,q[1:]))));x.AddScaleOp(opSuffix='supportFixture').Set(Gf.Vec3f(*map(float,info.get('scale',[1,1,1]))))
if args.release_gap_m is not None:
 cache=UsdGeom.XformCache();rack_matrix=np.asarray(cache.GetLocalToWorldTransform(s.GetPrimAtPath(rack)));inverse=np.linalg.inv(rack_matrix);body_origin=np.asarray(cache.GetLocalToWorldTransform(s.GetPrimAtPath(tube)))[3,:];local_origin=body_origin@inverse
 geometry=json.loads((Path(__file__).resolve().parent.parent/'outputs/sciben_waterbath_120hz_20261010/consumer_geometry.json').read_text());selected=min(geometry['rack']['slots'],key=lambda v:np.linalg.norm(local_origin[:2]-v['center_xy_m']));assert selected['id']=='slot_15ml_r00_c05'
 mesh=s.GetPrimAtPath(tube+'/Visual/GlassShell');transform=np.asarray(cache.GetLocalToWorldTransform(mesh))@inverse;points=np.c_[np.asarray(mesh.GetAttribute('points').Get()),np.ones(len(mesh.GetAttribute('points').Get()))];lowest=float((points@transform)[:,2].min());target=selected['seat_bottom_z_m']+args.release_gap_m/np.linalg.norm(rack_matrix[2,:3]);particle_shift_z=(target-lowest)/inverse[2,2]
 translate=s.GetPrimAtPath(tube).GetAttribute('xformOp:translate:supportFixture');value=translate.Get();translate.Set(Gf.Vec3d(value[0],value[1],value[2]+particle_shift_z))
for label,info in meta['initial_particle_states'].items():
 prim=s.GetPrimAtPath(info['prim_path']);a=np.asarray(info['points'],np.float32).copy()
 if label=='SampleParticles':a[:,2]+=particle_shift_z
 for k in ['points','physxParticle:simulationPoints']:
  attr=prim.GetAttribute(k)
  if attr:attr.Set(Vt.Vec3fArray.FromNumpy(a))
 prim.GetAttribute('velocities').Set(Vt.Vec3fArray.FromNumpy(np.zeros_like(a)))
scene=UsdPhysics.Scene.Define(s,'/World/PhysicsScene');scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));scene.CreateGravityMagnitudeAttr(9.81);a=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
for k,v in {'EnableGPUDynamics':True,'EnableCCD':True,'EnableStabilization':True,'BroadphaseType':'GPU','SolverType':'TGS','TimeStepsPerSecond':120,'MinPositionIterationCount':64,'MaxPositionIterationCount':64,'GpuFoundLostAggregatePairsCapacity':16384,'GpuTotalAggregatePairsCapacity':16384,'GpuMaxParticleContacts':args.max_particle_contacts}.items():getattr(a,'Create'+k+'Attr')().Set(v)
UsdPhysics.RigidBodyAPI(s.GetPrimAtPath(tube)).CreateKinematicEnabledAttr(False);PhysxSchema.PhysxContactReportAPI.Apply(s.GetPrimAtPath(tube)).CreateThresholdAttr(0.)
for label in ['Sample','Bath']:s.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System').CreateRelationship('simulationOwner').SetTargets(['/World/PhysicsScene'])
s.GetRootLayer().Save();rack_inverse=np.linalg.inv(np.asarray(UsdGeom.XformCache().GetLocalToWorldTransform(s.GetPrimAtPath(rack))));geo=json.loads((Path(__file__).resolve().parent.parent/'outputs/sciben_waterbath_120hz_20261010/consumer_geometry.json').read_text());initial=meta['initial_layout']['sample_tube']['position'];local=(np.r_[initial,1]@rack_inverse)[:3];slot=min(geo['rack']['slots'],key=lambda t:np.linalg.norm(local[:2]-t['center_xy_m']));assert slot['id']=='slot_15ml_r00_c05';seat=slot['seat_bottom_z_m'];errors=[];ticks=[];events=[];last_contact_points=0
mesh=s.GetPrimAtPath(tube+'/Visual/GlassShell');cache=UsdGeom.XformCache();body_matrix=cache.GetLocalToWorldTransform(s.GetPrimAtPath(tube));scale=np.linalg.norm(np.asarray(body_matrix)[:3,:3],axis=1);to_body=cache.GetLocalToWorldTransform(mesh)*body_matrix.GetInverse();vertices=np.asarray([to_body.Transform(Gf.Vec3d(*v)) for v in mesh.GetAttribute('points').Get()]);homogeneous=np.c_[vertices,np.ones(len(vertices))]
def on_contact(headers,data):
 global last_contact_points
 for h in headers:
  paths=[str(PhysicsSchemaTools.intToSdfPath(h.collider0)),str(PhysicsSchemaTools.intToSdfPath(h.collider1))]
  if not any(x.startswith(rack+'/') for x in paths) or int(h.num_contact_data)==0:continue
  depth=min(float(data[i].separation) for i in range(h.contact_data_offset,h.contact_data_offset+h.num_contact_data));last_contact_points+=int(h.num_contact_data);events.append({'native_tick':len(ticks),'points':int(h.num_contact_data),'min_separation_m':depth,'colliders':paths})
cs=omni.physx.get_physx_simulation_interface().subscribe_contact_report_events(on_contact);es=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)) if len(errors)<32 else None);clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda d:ticks.append(float(d)))
w=World(physics_dt=1/120,rendering_dt=1/120,physics_prim_path='/World/PhysicsScene',set_defaults=False)
for k in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(k,True)
settings.set(pb.SETTING_SUPPRESS_READBACK,False);w.reset();dc=_dynamic_control.acquire_dynamic_control_interface();h=dc.get_rigid_body(tube);trace=[];finite=True;counts=True;outside_max={label:0 for label in manifest['liquids']};first_outside={}
from sciben_waterbath_geometry import outside_count
body_scales={}
for label,info in manifest['liquids'].items():
 transform=np.asarray(UsdGeom.XformCache().GetLocalToWorldTransform(s.GetPrimAtPath(info['container'].replace('/World',root,1))))
 body_scales[label]=np.linalg.norm(transform[:3,:3],axis=1)
startup_no_advance=0
for i in range(args.steps):
 last_contact_points=0;before_tick=len(ticks);w.step(render=True)
 if len(ticks)!=before_tick+1:
  errors.append('Native step cadence differs from one tick');break
 if errors:break
 pose=dc.get_rigid_body_pose(h);vel=dc.get_rigid_body_linear_velocity(h);mat=np.asarray(Gf.Matrix4d().SetScale(Gf.Vec3d(*scale))*Gf.Matrix4d().SetRotate(Gf.Quatd(pose.r.w,Gf.Vec3d(pose.r.x,pose.r.y,pose.r.z)))*Gf.Matrix4d().SetTranslate(Gf.Vec3d(pose.p.x,pose.p.y,pose.p.z)));relative=mat@rack_inverse;axis=relative[2,:3]/np.linalg.norm(relative[2,:3]);lowest=float((homogeneous@relative)[:,2].min());row={'step':i,'native_tick':len(ticks),'position':[pose.p.x,pose.p.y,pose.p.z],'origin_seat_gap_mm':float((relative[3,2]-seat)*1000),'visual_lowest_seat_gap_mm':(lowest-seat)*1000,'tilt_deg':float(np.rad2deg(np.arccos(np.clip(axis[2],-1,1)))),'vertical_velocity_m_s':float(vel.z),'contact_points':last_contact_points};radius=.009*max(np.linalg.norm(relative[0,:3]),np.linalg.norm(relative[1,:3]));origin=relative[3,:3]
 toppt=origin+axis*((slot['aperture_top_z_m']-origin[2])/axis[2]) if axis[2]>1e-9 else np.full(3,np.inf)
 distance=max(np.linalg.norm(origin[:2]-slot['center_xy_m']),np.linalg.norm(toppt[:2]-slot['center_xy_m']))
 margin=slot['aperture_radius_m']+.0005-distance-radius/axis[2] if axis[2]>1e-9 else -float('inf')
 row['same_slot_radial_margin_mm']=float(margin*1000);row['same_slot_id']=slot['id'];trace.append(row)
 for info in meta['initial_particle_states'].values():
  data=np.asarray(s.GetPrimAtPath(info['prim_path']).GetAttribute('points').Get());finite &= bool(np.isfinite(data).all());counts &= len(data)==len(info['points'])
 for label,info in manifest['liquids'].items():
  path=info['container'].replace('/World',root,1);q=dc.get_rigid_body_pose(dc.get_rigid_body(path));matrix=np.asarray(Gf.Matrix4d().SetScale(Gf.Vec3d(*body_scales[label]))*Gf.Matrix4d().SetRotate(Gf.Quatd(q.r.w,Gf.Vec3d(q.r.x,q.r.y,q.r.z)))*Gf.Matrix4d().SetTranslate(Gf.Vec3d(q.p.x,q.p.y,q.p.z)));data=np.asarray(s.GetPrimAtPath(info['points'].replace('/World',root,1)).GetAttribute('points').Get());local_points=(np.c_[data,np.ones(len(data))]@np.linalg.inv(matrix))[:,:3];n=outside_count(local_points,info['cavity_profile_m'],.001);outside_max[label]=max(outside_max[label],n)
  if n and label not in first_outside:first_outside[label]={'step':i,'outside_count':n}
 row['outside_counts_max_so_far']=outside_max.copy()
 if i%60==0:print('SUPPORT',json.dumps(row),flush=True)
 with open(out/'trace.jsonl','a') as stream:stream.write(json.dumps(row)+'\n')
tail=trace[-120:];supported=len(tail)==120 and all(-1<=x['visual_lowest_seat_gap_mm']<=5 and x['tilt_deg']<=20 and abs(x['vertical_velocity_m_s'])<.02 and x['same_slot_radial_margin_mm']>=0 for x in tail);passed=not errors and len(trace)==args.steps and supported and bool(events) and finite and counts and all(abs(v-1/120)<1e-8 for v in ticks)
r={'status':'PASS_DYNAMIC_SLOT_SUPPORT' if passed else 'FAIL','scope':('original mixed17 c05; visible tube bottom initialized exactly'+str(args.release_gap_m)+' world metres above seat' if args.release_gap_m is not None else 'original mixed17 c05; tube initialized'+str(args.raise_m)+'m higher')+'; fully dynamic600steps afterPlay, no robot/task success claim','initial_shift_world_z_m':float(particle_shift_z),'requested_release_gap_world_m':args.release_gap_m,'slot':slot,'support_thresholds':{'final_steps':120,'visual_lowest_seat_gap_mm':[-1,5],'tilt_deg_max':20,'abs_vertical_velocity_m_s_max':.02,'same_c05_slot_radial_margin_mm_min':0,'aperture_extra_m':.0005},'requested_steps':args.steps,'completed_steps':len(trace),'supported_final120_steps':supported,'final':trace[-1] if trace else None,'tail_lowest_gap_range_mm':[min(x['visual_lowest_seat_gap_mm'] for x in tail),max(x['visual_lowest_seat_gap_mm'] for x in tail)] if tail else None,'minimum_contact_separation_m':min((x['min_separation_m'] for x in events),default=None),'events':events,'errors':errors,'particle_containment':{'max_outside_count':outside_max,'first_outside':first_outside,'tolerance_m':.001,'all_steps_contained':all(v==0 for v in outside_max.values()),'scope':'Separate observation; original fixed support criteria unchanged'},'particle_arrays_finite':finite,'particle_counts_unchanged':counts,'native_clock':{'count':len(ticks),'wrong_dt':sum(abs(v-1/120)>1e-8 for v in ticks)},'no_particle_or_rigid_pose_rewrite_during_simulation':True,'source_hashes':{k:module.sha(v) for k,v in inputs.items()},'script_sha256':module.sha(__file__),'max_particle_contacts':args.max_particle_contacts,'fixture_scope':'Exact final composed root; original source metadata; only 5mm initial seed/body placement before Play, real fluid and dynamic tube thereafter. Reaction graph disabled only for support fixture.'};(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='events'}),flush=True);app.close()
