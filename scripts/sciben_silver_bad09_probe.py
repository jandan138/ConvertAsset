#!/usr/bin/env python3
"""Independent bad09 direct-SDK diagnosis; never writes input/core/asset files."""
import argparse
import hashlib
import json
from pathlib import Path
import pickle


def normalize_action(value):
    """Return recorded16 joint targets and absolute base targets, unchanged."""
    import numpy as np
    action=np.asarray(value['arm_action'],dtype=np.float64)
    base=np.asarray(value['base_motion'],dtype=np.float64)
    if action.shape!=(16,) or base.shape!=(3,) or not np.isfinite(action).all() or not np.isfinite(base).all():
        raise ValueError('Expected finite16 joint and3 absolute base targets')
    return action,base


def sdk_base_targets(base, legacy_raw=False):
    """Baseline stores absolute yaw in degrees; old A/B retained raw near-zero yaw."""
    import numpy as np
    value=np.array(base,dtype=np.float64,copy=True)
    if not legacy_raw:value[2]=np.deg2rad(value[2])
    return value



def skip_contact_sampling(source):
    """Diagnostic only: keep view creation and all other reaction/PBD code."""
    needle="    contact=state.repair_contacts.get_contact_data(1/120)\n    count=bounded_contact_count(contact[4],config['contact_capacity'])"
    if source.count(needle)!=1:raise ValueError('Expected exactly one known contact sampling block')
    return source.replace(needle,"    count=0  # DIAGNOSTIC ONLY: wall sampling bypassed, never deliver",1)



def case_inputs(baseline,case):
    """Bind a mixed case to its own YAML scene and task metadata."""
    import re,yaml
    if not re.fullmatch(r'mixed_[0-9]+',case):raise ValueError('Expected mixed_N case')
    baseline=Path(baseline);task='task_z4_silver_mirror_reaction'
    config=baseline/f'configs/tasks/scientific_experiments/{task}/test/mixed/{case}.yml'
    value=yaml.safe_load(config.read_text())['evaluation_configs'][0]
    if value['task_name']!=f'scientific_experiments/{task}/{case}':raise ValueError('Mismatched YAML task case')
    if value.get('warmup_steps')!=300 or any(abs(value[k]-1/120)>1e-10 for k in ['physics_dt','rendering_dt']):raise ValueError('Case requires different initialization/clock')
    scene=baseline/'saved/assets'/Path(value['usd_name']+'.usda')
    return {'scene':scene,'metadata':baseline/f'saved/tasks/scientific_experiments/{task}/{case}/000/meta_info.pkl','case_yaml':config}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_pickle(path):
    """Read NumPy1/2 metadata without altering the installed SDK modules."""
    class Compatible(pickle.Unpickler):
        def find_class(self,module,name):
            return super().find_class(module.replace('numpy._core','numpy.core'),name)
    with open(path,'rb') as stream:return Compatible(stream).load()


def filter_supplement_robot(stage,root,robot):
    """Diagnostic only: exclude supplemental tube/bath shapes versus robot."""
    from pxr import UsdPhysics
    group=UsdPhysics.CollisionGroup.Define(stage,root+'/Bad09DiagnosticGroups/Supplement')
    other=UsdPhysics.CollisionGroup.Define(stage,root+'/Bad09DiagnosticGroups/Robot')
    paths=[root+'/obj_sample_tube/WaterbathCollision',root+'/obj_beaker/WaterbathCollision']
    group.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets(paths)
    other.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets([robot])
    group.CreateFilteredGroupsRel().SetTargets([other.GetPath()]);other.CreateFilteredGroupsRel().SetTargets([group.GetPath()])
    return {'supplemental_paths':paths,'excluded_against':robot,'original_tube_SDF_retained':True,'bath_rigid_contact_missing_by_design':True,'qualified_asset':False}



def fluid_only_supplements(stage,root):
    """Candidate diagnosis: original hollow SDFs carry every rigid contact."""
    from pxr import UsdPhysics
    paths=[root+'/obj_sample_tube/WaterbathCollision',root+'/obj_beaker/WaterbathCollision']
    g=root+'/Bad09FluidOnlyGroups'
    walls=UsdPhysics.CollisionGroup.Define(stage,g+'/Supplement')
    rigid=UsdPhysics.CollisionGroup.Define(stage,g+'/RigidScene')
    walls.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets(paths)
    rigid.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets([root])
    rigid.GetCollidersCollectionAPI().CreateExcludesRel().SetTargets(paths+[root+'/WaterbathFluid'])
    walls.CreateFilteredGroupsRel().SetTargets([walls.GetPath(),rigid.GetPath()])
    rigid.CreateFilteredGroupsRel().SetTargets([walls.GetPath()])
    sdf=[root+'/obj_sample_tube/Visual/GlassShell',root+'/obj_beaker/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh']
    for path in sdf:
        p=stage.GetPrimAtPath(path)
        if not p or not p.HasAPI(UsdPhysics.CollisionAPI):raise ValueError('Missing original rigid SDF '+path)
        UsdPhysics.CollisionAPI(p).CreateCollisionEnabledAttr(True)
    return {'supplemental_paths':paths,'rigid_scene_root':root,'particle_exclusion':root+'/WaterbathFluid','original_rigid_sdfs':sdf,'supplement_rigid_and_self_filtered':True,'qualified_asset':False}


def run(args):
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    import numpy as np,carb,omni.usd,omni.physx
    import omni.physx.bindings._physx as pb
    from omni.isaac.core import World
    from omni.isaac.core.robots import Robot
    from omni.isaac.dynamic_control import _dynamic_control
    from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,Gf,Sdf,Vt
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    baseline=Path(args.baseline).resolve();scene=baseline/'saved/assets/scene_usds/scientific_experiments/task_z4_silver_mirror_reaction/unseen_scene_1/scene.usda'
    meta=baseline/'saved/tasks/scientific_experiments/task_z4_silver_mirror_reaction/mixed_1/000/meta_info.pkl'
    bound=case_inputs(baseline,args.case) if args.case else None
    if bound:scene=bound['scene'];meta=bound['metadata']
    robot_asset=baseline/'saved/assets/robot_usds/lift2/robot.usd'
    inputs={'scene':str(scene),'metadata':str(meta),'robot':str(robot_asset),'actions':str(Path(args.actions).resolve())}
    if bound:inputs['case_yaml']=str(bound['case_yaml'])
    if args.bad_case_matrix:
        entries=json.loads(Path(args.bad_case_matrix).read_text());matches=[v for v in entries if v['task']=='task_z4_silver_mirror_reaction' and v['case']==args.case and Path(v['path'])/'meta_record.pkl'==Path(args.actions)]
        if len(matches)!=1:raise ValueError('Action source does not match case matrix')
        inputs['bad_case_matrix']=str(Path(args.bad_case_matrix).resolve())
    hashes={k:sha(v) for k,v in inputs.items()}
    metadata=load_pickle(meta)['task_data'];actions=load_pickle(args.actions)['model_output'];assert args.steps<=len(actions)
    normalized=[normalize_action(a) for a in actions[:args.steps]]
    root='/World/_scene';tube=root+'/obj_sample_tube';bath=root+'/obj_beaker';robot_path=root+'/lift2'
    fixture=Usd.Stage.CreateNew(str(out/'fixture.usda'));fixture.GetRootLayer().subLayerPaths=[str(scene)];UsdGeom.SetStageMetersPerUnit(fixture,1.);UsdGeom.SetStageUpAxis(fixture,'Z');fixture.GetRootLayer().Save();fixture=None
    settings=carb.settings.get_settings();settings.set_bool('/app/omni.graph.scriptnode/enable_opt_in',False);settings.set_bool('/app/omni.graph.scriptnode/opt_in',True)
    for key in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(key,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False);omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    omni.usd.get_context().open_stage(str(out/'fixture.usda'))
    for _ in range(5):app.update()
    stage=omni.usd.get_context().get_stage();physics=UsdPhysics.Scene.Define(stage,'/World/PhysicsScene');physics.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));physics.CreateGravityMagnitudeAttr(9.81);pa=PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim())
    for key,value in {'EnableGPUDynamics':True,'EnableCCD':True,'EnableStabilization':True,'BroadphaseType':'GPU','SolverType':'TGS','TimeStepsPerSecond':120,'MinPositionIterationCount':64,'MaxPositionIterationCount':64,'GpuFoundLostAggregatePairsCapacity':16384,'GpuTotalAggregatePairsCapacity':16384,'GpuMaxParticleContacts':4194304}.items():getattr(pa,'Create'+key+'Attr')().Set(value)
    def pose(prim,info):
        x=UsdGeom.Xformable(prim);x.ClearXformOpOrder();x.AddTranslateOp(opSuffix='bad09').Set(Gf.Vec3d(*map(float,info['position'])));q=info['orientation'];x.AddOrientOp(opSuffix='bad09').Set(Gf.Quatf(float(q[0]),Gf.Vec3f(*map(float,q[1:]))));x.AddScaleOp(opSuffix='bad09').Set(Gf.Vec3f(*map(float,info.get('scale',[1,1,1]))))
    for name,info in metadata['initial_layout'].items():
        if info['type']=='robot':continue
        pose(stage.GetPrimAtPath(info['prim_path']),info)
    for key,value in metadata.get('initial_prim_attributes',{}).items():
        path,name=key.rsplit('::',1);a=stage.GetPrimAtPath(path).GetAttribute(name)
        if not a:raise ValueError('Missing task attribute '+key)
        if a.GetTypeName() in [Sdf.ValueTypeNames.Int,Sdf.ValueTypeNames.UInt,Sdf.ValueTypeNames.Int64,Sdf.ValueTypeNames.UInt64]:value=int(value)
        if isinstance(value,np.ndarray):value=value.tolist()
        value_type=a.GetTypeName().type.pythonClass
        if value_type is not None:value=value_type(value)
        a.Set(value)
    for info in metadata['initial_particle_states'].values():
        prim=stage.GetPrimAtPath(info['prim_path']);points=np.asarray(info['points'],dtype=np.float32)
        for key in ['points','physxParticle:simulationPoints']:
            a=prim.GetAttribute(key)
            if a:a.Set(Vt.Vec3fArray.FromNumpy(points))
        prim.GetAttribute('velocities').Set(Vt.Vec3fArray.FromNumpy(np.zeros_like(points)))
    for label in ['Bath','Sample']:stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System').CreateRelationship('simulationOwner').SetTargets(['/World/PhysicsScene'])
    rp=stage.DefinePrim(robot_path,'Xform');rp.GetReferences().AddReference(str(robot_asset));rinfo=metadata['initial_layout']['lift2'];pose(rp,rinfo)
    for p in Usd.PrimRange(rp):
        if p.HasAPI(UsdPhysics.RigidBodyAPI):PhysxSchema.PhysxRigidBodyAPI.Apply(p).CreateMaxDepenetrationVelocityAttr(1.)
        path=str(p.GetPath())
        if p.IsA(UsdPhysics.Joint) and ('/fl/' in path or '/fr/' in path) and path.endswith(tuple('joint'+str(i) for i in range(1,7))):PhysxSchema.PhysxJointAPI.Apply(p).CreateArmatureAttr(.01)
    mat=stage.GetPrimAtPath(robot_path+'/lift2/lift2/PhysicsMaterial');pm=UsdPhysics.MaterialAPI(mat);pm.CreateStaticFrictionAttr(2.5);pm.CreateDynamicFrictionAttr(2.5);pm.CreateRestitutionAttr(0.);px=PhysxSchema.PhysxMaterialAPI.Apply(mat);px.CreateFrictionCombineModeAttr('max');px.CreateRestitutionCombineModeAttr('multiply');px.CreateImprovePatchFrictionAttr(True)
    drive=UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath(robot_path+'/lift2/lift2/base_link/joint4'),'linear');drive.CreateStiffnessAttr(1e6);drive.CreateDampingAttr(1e4);drive.CreateMaxForceAttr(1e6)
    intervention=filter_supplement_robot(stage,root,robot_path) if args.filter_supplement_robot else None
    if args.fluid_only_supplements:
        if args.filter_supplement_robot:raise ValueError('Use only one collision intervention')
        intervention=fluid_only_supplements(stage,root)
    if args.restore_bath_sdf:
        p=stage.GetPrimAtPath(bath+'/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh')
        assert p and p.HasAPI(UsdPhysics.CollisionAPI)
        UsdPhysics.CollisionAPI(p).CreateCollisionEnabledAttr(True)
        intervention=dict(intervention or {},bath_hollow_SDF_restored=True,bath_rigid_contact_missing_by_design=False)
    if args.skip_contact_sampling:
        a=stage.GetPrimAtPath(tube+'/ReactionRuntime/TollensGraph/FlowController').GetAttribute('inputs:script')
        original=a.Get();patched=skip_contact_sampling(original);a.Set(patched)
        (out/'reaction_original.py').write_text(original);(out/'reaction_no_contact_sampling.py').write_text(patched)
        intervention=dict(intervention or {},contact_sampling_skipped=True,wall_guard_disabled_diagnostic_only=True)
    if args.disable_graph:stage.GetPrimAtPath(tube+'/ReactionRuntime').SetActive(False)
    stage.GetRootLayer().Save()
    if args.case:
        layers={l.realPath:sha(l.realPath) for l in stage.GetUsedLayers() if l.realPath and Path(l.realPath).is_file() and Path(l.realPath).resolve()!=out/'fixture.usda'}
        (out/'bound_scene_layers.json').write_text(json.dumps(layers,indent=2)+'\n')
    (out/'inputs.json').write_text(json.dumps({'inputs':inputs,'sha256':hashes,'script_sha256':sha(__file__),'graph_enabled':not args.disable_graph,'intervention':intervention,'warmup':300,'action_cadence':'one original action per native120Hz step','base_mode':'absolute','legacy_raw_yaw':args.legacy_raw_yaw,'limits':'Direct SDK reproducer; no GenManip metric/FK/camera pipeline. Metadata particles restored with zero velocities exactly as baseline loader.'},indent=2)+'\n')
    contact_events={};contact_subscription=None
    if args.record_contacts:
        from pxr import PhysicsSchemaTools
        def contact_event(headers,data):
            for h in headers:
                actor=[str(PhysicsSchemaTools.intToSdfPath(h.actor0)),str(PhysicsSchemaTools.intToSdfPath(h.actor1))]
                if tube not in actor and bath not in actor:continue
                colliders=[str(PhysicsSchemaTools.intToSdfPath(h.collider0)),str(PhysicsSchemaTools.intToSdfPath(h.collider1))]
                key=' | '.join(sorted(actor))
                row=contact_events.setdefault(key,{'headers':0,'max_contact_points':0,'events':{},'collider_pairs':[]})
                row['headers']+=1;row['max_contact_points']=max(row['max_contact_points'],int(h.num_contact_data))
                if int(h.num_contact_data):
                    depth=min(float(data[i].separation) for i in range(h.contact_data_offset,h.contact_data_offset+h.num_contact_data))
                    row['min_separation_m']=min(row.get('min_separation_m',float('inf')),depth)
                row.setdefault('first_native_tick',len(native));row['last_native_tick']=len(native)
                kind=str(h.type);row['events'][kind]=row['events'].get(kind,0)+1
                pair=sorted(colliders)
                if pair not in row['collider_pairs'] and len(row['collider_pairs'])<32:row['collider_pairs'].append(pair)
        contact_subscription=omni.physx.get_physx_simulation_interface().subscribe_contact_report_events(contact_event)
    errors=[];native=[]
    def error(event):
        message=str(event.payload)
        if len(errors)<32:errors.append(message)
        print('DIAGNOSTIC_PHYSICS_ERROR',message,flush=True)
    es=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(error);clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda dt:native.append(float(dt)))
    world=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1,physics_prim_path='/World/PhysicsScene',set_defaults=False);robot=world.scene.add(Robot(prim_path=robot_path,name='lift2'))
    for key in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(key,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False);world.reset();robot.set_solver_position_iteration_count(128);robot.set_solver_velocity_iteration_count(4);robot.set_stabilization_threshold(.005)
    q=np.asarray(rinfo['joint_positions'],np.float32);robot.set_joint_positions(q);robot.set_joint_velocities(np.zeros_like(q));robot._articulation_view.set_joint_position_targets(q)
    dc=_dynamic_control.acquire_dynamic_control_interface();indices=np.asarray([10,12,14,16,18,20,23,24,9,11,13,15,17,19,21,22],dtype=np.int32);trace=[];failure=None;completed=0
    def snapshot(step):
        poses={}
        for path in [tube,bath,robot_path+'/lift2/lift2/fl/link7',robot_path+'/lift2/lift2/fl/link8']:
            h=dc.get_rigid_body(path)
            if not h:continue
            v=dc.get_rigid_body_pose(h);poses[path]={'position':[v.p.x,v.p.y,v.p.z],'orientation_xyzw':[v.r.x,v.r.y,v.r.z,v.r.w]}
        p=stage.GetPrimAtPath(tube);state={k:p.GetAttribute('tollens:'+k).Get() for k in ['pbd_valid','runtime_error','heated_seconds','heating_enabled','heating_block_reason','wall_contact_count']}
        return {'step':step,'native_count':len(native),'poses':poses,'state':state,'joints':robot.get_joint_positions().tolist(),'rack_matrix_rowmajor':np.asarray(UsdGeom.XformCache().GetLocalToWorldTransform(stage.GetPrimAtPath(root+'/obj_tube_rack'))).tolist()}
    dense=open(out/'poses_each_step.jsonl','w') if args.dense_pose_trace else None
    for step in range(-300,args.steps):
        if step>=0:
            action,base=normalized[step];robot._articulation_view.set_joint_position_targets(action.astype(np.float32),joint_indices=indices);robot._articulation_view.set_joint_position_targets(sdk_base_targets(base,args.legacy_raw_yaw).astype(np.float32),joint_indices=np.asarray([0,1,2]))
        world.step(render=True)
        if errors:failure='PhysX error';break
        q=robot.get_joint_positions()
        if not np.isfinite(q).all():failure='Nonfinite joints';break
        if step>=0:completed=step+1
        dense_row=snapshot(step) if dense else None
        if dense:dense.write(json.dumps(dense_row)+'\n')
        if step==args.steps-1 or step%30==0 or (1900<=step<=2200 and step%5==0):
            if dense:dense.flush()
            row=dense_row or snapshot(step);trace.append(row);print('BAD09',json.dumps(row),flush=True);(out/'progress.json').write_text(json.dumps({'completed_actions':completed,'trace':trace,'errors':errors},indent=2)+'\n')
    if dense:dense.close()
    report={'status':'PASS_BOUNDED_ENGINE' if not failure else 'FAIL_ENGINE','failure':failure,'completed_actions':completed,'requested_actions':args.steps,'native_clock':{'count':len(native),'min_s':min(native),'max_s':max(native),'wrong_dt':sum(abs(v-1/120)>1e-8 for v in native)},'errors':errors,'intervention':intervention,'graph_enabled':not args.disable_graph,'input_hashes':hashes,'source_inputs_unchanged':all(sha(inputs[k])==h for k,h in hashes.items()),'contact_events':contact_events,'trace':trace,'limits':['No task success claim',('Supplement-only filtering removes necessary beaker contact' if args.filter_supplement_robot and not args.restore_bath_sdf else 'Diagnostic only; separate containment and full baseline qualification required'),'No camera/FK pipeline replication']}
    if report['native_clock']['wrong_dt']:report['status']='FAIL_CLOCK'
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('REPORT',json.dumps({k:v for k,v in report.items() if k!='trace'}),flush=True);app.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--case');p.add_argument('--bad-case-matrix');p.add_argument('--dense-pose-trace',action='store_true');p.add_argument('--actions',required=True);p.add_argument('--out',required=True);p.add_argument('--steps',type=int,default=2300);p.add_argument('--filter-supplement-robot',action='store_true');p.add_argument('--disable-graph',action='store_true');p.add_argument('--skip-contact-sampling',action='store_true');p.add_argument('--restore-bath-sdf',action='store_true');p.add_argument('--fluid-only-supplements',action='store_true');p.add_argument('--record-contacts',action='store_true');p.add_argument('--legacy-raw-yaw',action='store_true');run(p.parse_args())
