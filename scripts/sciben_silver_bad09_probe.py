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



def native_step_decision(before,after,warmup):
    """Only passive startup may render without physics; actions require one tick."""
    delta=after-before
    if delta==1:return True
    if delta==0 and warmup:return False
    raise RuntimeError('Expected one native physics tick, observed '+str(delta))


def reaction_names(task):
    names={'task_z4_silver_mirror_reaction':('tollens','TollensGraph'),'task_12_fehling_test':('fehlings','FehlingsGraph')}
    if task not in names:raise ValueError('Unsupported waterbath task')
    return names[task]


def case_inputs(baseline,case,task='task_z4_silver_mirror_reaction'):
    """Bind a mixed case to its own YAML scene and task metadata."""
    import re,yaml
    if not re.fullmatch(r'mixed_[0-9]+',case):raise ValueError('Expected mixed_N case')
    baseline=Path(baseline);reaction_names(task)
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



def tube_proxy_cells(sectors=24):
    """Source-matched1mm glass wall, hemispherical bottom and open rolled lip."""
    import math,numpy as np
    import importlib.util
    spec=importlib.util.spec_from_file_location("_readonly_task10_geometry",Path(__file__).with_name("task10_pbd_producer.py"));helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);annular_wedge=helper.annular_wedge
    levels=[.001,.003,.006,.009,.147,.148,.149,.149+math.sqrt(.5)*.001,.15]
    def radii(z):
        if z<=.009:return math.sqrt(max(0,.008**2-(z-.009)**2)),math.sqrt(max(0,.009**2-(z-.009)**2))
        if z<=.147:return .008,.009
        if z<=.149:
            t=(z-.147)/.002
            return .008,.009+.001*(t*t*(3-2*t))
        span=math.sqrt(max(0,.001**2-(z-.149)**2))
        return .009-span,.009+span
    cells=[]
    for j,(lo,hi) in enumerate(zip(levels,levels[1:])):
        ri0,ro0=radii(lo);ri1,ro1=radii(hi)
        for i in range(sectors):
            v,_,_=annular_wedge(ri0,ro0,ri1,ro1,lo,hi,2*math.pi*i/sectors,2*math.pi*(i+1)/sectors)
            cells.append((f'Wall_{j:02d}_{i:02d}',np.unique(np.asarray(v,float),axis=0)))
    cap=[[0.,0.,0.]]
    for z in [.0005,.001]:
        r=math.sqrt(.009**2-(z-.009)**2)
        cap.extend([[r*math.cos(2*math.pi*i/sectors),r*math.sin(2*math.pi*i/sectors),z] for i in range(sectors)])
    cells.append(('BottomCap',np.asarray(cap,float)))
    return cells



def tube_proxy_cells_v2(sectors=24):
    """Spherical inner/outer bottom surfaces share the measured9mm-center height."""
    import math,numpy as np
    cells=[(n,v) for n,v in tube_proxy_cells(sectors) if n.startswith('Wall_') and int(n.split('_')[1])>=3]
    for j in range(6):
        polar=[math.pi*j/12,math.pi*(j+1)/12]
        for i in range(sectors):
            angles=[2*math.pi*i/sectors,2*math.pi*(i+1)/sectors]
            xyz=[[r*math.sin(theta)*math.cos(a),r*math.sin(theta)*math.sin(a),.009-r*math.cos(theta)] for r in [.008,.009] for theta in polar for a in angles]
            cells.append((f'Bottom_{j:02d}_{i:02d}',np.unique(np.asarray(xyz,float),axis=0)))
    return cells


def author_tube_rigid_proxy(stage,root,curved_bottom=False):
    """Replace rigid SDF duty with193 open-wall convex cells; preserve PBD walls."""
    import numpy as np
    from scipy.spatial import ConvexHull
    from pxr import UsdGeom,UsdPhysics,UsdShade,Gf,Sdf
    tube=root+'/obj_sample_tube';glass=stage.GetPrimAtPath(tube+'/Visual/GlassShell')
    if not glass or not glass.HasAPI(UsdPhysics.CollisionAPI):raise ValueError('Missing original glass collision mesh')
    material=UsdShade.MaterialBindingAPI(glass).ComputeBoundMaterial('physics')[0]
    paths=[]
    for name,xyz in (tube_proxy_cells_v2() if curved_bottom else tube_proxy_cells()):
        hull=ConvexHull(xyz);center=(xyz.min(0)+xyz.max(0))/2;scale=np.maximum(xyz.max(0)-xyz.min(0),1e-9);faces=[]
        for face,equation in zip(hull.simplices,hull.equations):
            face=list(map(int,face))
            if np.dot(np.cross(xyz[face[1]]-xyz[face[0]],xyz[face[2]]-xyz[face[0]]),equation[:3])<0:face[1],face[2]=face[2],face[1]
            faces.append(face)
        mesh=UsdGeom.Mesh.Define(stage,tube+'/RigidWallProxy/'+name);mesh.CreatePointsAttr([Gf.Vec3f(*v) for v in (xyz-center)/scale]);mesh.CreateFaceVertexCountsAttr([3]*len(faces));mesh.CreateFaceVertexIndicesAttr([i for f in faces for i in f]);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible');mesh.AddTranslateOp().Set(Gf.Vec3d(*center));mesh.AddScaleOp().Set(Gf.Vec3f(*scale));p=mesh.GetPrim()
        p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
        for key,typ,value in [('physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True),('physics:approximation',Sdf.ValueTypeNames.Token,'convexHull'),('physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float,0.),('physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.0008),('physxCollision:restOffset',Sdf.ValueTypeNames.Float,0.)]:p.CreateAttribute(key,typ).Set(value)
        if material:UsdShade.MaterialBindingAPI.Apply(p).Bind(material,materialPurpose='physics')
        paths.append(mesh.GetPath())
    UsdPhysics.CollisionAPI(glass).CreateCollisionEnabledAttr(False)
    for label in ['Sample','Bath']:
        prim=stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System')
        if not prim:raise ValueError('Missing particle system '+label)
        api=UsdPhysics.FilteredPairsAPI.Apply(prim);existing=api.GetFilteredPairsRel().GetTargets();api.CreateFilteredPairsRel().SetTargets(list(dict.fromkeys(existing+paths)))
    return {'original_visible_glass_unchanged':True,'original_rigid_SDF_replaced':True,'rigid_proxy_count':len(paths),'profile_variant':'spherical_bottom_v2' if curved_bottom else 'axial_bottom_v1','particle_systems_filtered_only_against_new_proxies':True,'tube_mass_inertia_unchanged':True,'open_mouth':True,'qualified_asset':False}


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
    namespace,graph_name=reaction_names(args.task)
    if args.task!='task_z4_silver_mirror_reaction' and not args.case:raise ValueError('Explicit case required for Fehling')
    bound=case_inputs(baseline,args.case,args.task) if args.case else None
    if bound:scene=bound['scene'];meta=bound['metadata']
    robot_asset=Path(args.robot_observer_wrapper).resolve() if args.robot_observer_wrapper else baseline/'saved/assets/robot_usds/lift2/robot.usd'
    inputs={'scene':str(scene),'metadata':str(meta),'robot':str(robot_asset),'actions':str(Path(args.actions).resolve())}
    if bound:inputs['case_yaml']=str(bound['case_yaml'])
    if args.asset_delta and args.scene_observer_delta:raise ValueError('Use one explicit composed asset/observer delta, not two implicit orders')
    if args.asset_delta:inputs['producer_asset_delta']=str(Path(args.asset_delta).resolve())
    if args.scene_observer_delta:inputs['scene_observer_delta']=str(Path(args.scene_observer_delta).resolve())
    if args.bottom_hybrid_manifest:inputs['bottom_hybrid_manifest']=str(Path(args.bottom_hybrid_manifest).resolve())
    if args.bottom_reduced_manifest:inputs['bottom_reduced_manifest']=str(Path(args.bottom_reduced_manifest).resolve())
    if args.bad_case_matrix:
        entries=json.loads(Path(args.bad_case_matrix).read_text());matches=[v for v in entries if v['task']==args.task and v['case']==args.case and Path(v['path'])/'meta_record.pkl'==Path(args.actions)]
        if len(matches)!=1:raise ValueError('Action source does not match case matrix')
        inputs['bad_case_matrix']=str(Path(args.bad_case_matrix).resolve())
    hashes={k:sha(v) for k,v in inputs.items()}
    metadata=load_pickle(meta)['task_data'];actions=load_pickle(args.actions)['model_output'];assert args.steps<=len(actions)
    normalized=[normalize_action(a) for a in actions[:args.steps]]
    root='/World/_scene';tube=root+'/obj_sample_tube';bath=root+'/obj_beaker';robot_path=root+'/lift2'
    fixture=Usd.Stage.CreateNew(str(out/'fixture.usda'));fixture.GetRootLayer().subLayerPaths=[str(scene)]
    extra_delta=args.asset_delta or args.scene_observer_delta
    if extra_delta:fixture.OverridePrim('/World/_scene').GetReferences().AddReference(str(Path(extra_delta).resolve()),'/World')
    UsdGeom.SetStageMetersPerUnit(fixture,1.);UsdGeom.SetStageUpAxis(fixture,'Z');fixture.GetRootLayer().Save();fixture=None
    settings=carb.settings.get_settings();settings.set_bool('/app/omni.graph.scriptnode/enable_opt_in',False);settings.set_bool('/app/omni.graph.scriptnode/opt_in',True)
    for key in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(key,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False);omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    omni.usd.get_context().open_stage(str(out/'fixture.usda'))
    for _ in range(5):app.update()
    stage=omni.usd.get_context().get_stage();physics=UsdPhysics.Scene.Define(stage,'/World/PhysicsScene');physics.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));physics.CreateGravityMagnitudeAttr(9.81);pa=PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim())
    for key,value in {'EnableGPUDynamics':True,'EnableCCD':True,'EnableStabilization':True,'BroadphaseType':'GPU','SolverType':args.solver,'TimeStepsPerSecond':120,'MinPositionIterationCount':64,'MaxPositionIterationCount':args.scene_max_position_iterations,'GpuFoundLostAggregatePairsCapacity':16384,'GpuTotalAggregatePairsCapacity':16384,'GpuMaxParticleContacts':args.max_particle_contacts}.items():getattr(pa,'Create'+key+'Attr')().Set(value)
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
    if args.tube_rigid_proxy:
        intervention=author_tube_rigid_proxy(stage,root,args.proxy_curved_bottom)
    if args.bath_rigid_proxy:
        from sciben_waterbath_recovery_bath import author as author_bath_proxy
        intervention=dict(intervention or {},bath_proxy=author_bath_proxy(stage,root))
    if args.merge_bath_floor:
        from sciben_waterbath_recovery_bath_floor import author as author_bath_floor
        intervention=dict(intervention or {},bath_floor_merge=author_bath_floor(stage,root))
    if args.restore_bath_sdf:
        p=stage.GetPrimAtPath(bath+'/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh')
        assert p and p.HasAPI(UsdPhysics.CollisionAPI)
        UsdPhysics.CollisionAPI(p).CreateCollisionEnabledAttr(True)
        intervention=dict(intervention or {},bath_hollow_SDF_restored=True,bath_rigid_contact_missing_by_design=False)
    if args.skip_contact_sampling:
        a=stage.GetPrimAtPath(tube+'/ReactionRuntime/'+graph_name+'/FlowController').GetAttribute('inputs:script')
        original=a.Get();patched=skip_contact_sampling(original);a.Set(patched)
        (out/'reaction_original.py').write_text(original);(out/'reaction_no_contact_sampling.py').write_text(patched)
        intervention=dict(intervention or {},contact_sampling_skipped=True,wall_guard_disabled_diagnostic_only=True)
    if args.contact_event_sampling:
        from sciben_waterbath_recovery_events import patch_source
        if args.skip_contact_sampling:raise ValueError('Event sampling and bypass are mutually exclusive')
        a=stage.GetPrimAtPath(tube+'/ReactionRuntime/'+graph_name+'/FlowController').GetAttribute('inputs:script')
        original=a.Get();patched=patch_source(original,keep_tensor_view=not args.no_contact_tensor_view,persistent=args.persistent_contact_events);a.Set(patched)
        (out/'reaction_event_sampling.py').write_text(patched)
        intervention=dict(intervention or {},contact_event_sampling=True,tensor_view_creation_retained=not args.no_contact_tensor_view,wall_guard_active=True,persistent_active_pair_records=args.persistent_contact_events)
    if args.bottom_hybrid_manifest:
        if args.shared_tube_colliders or args.bath_rigid_proxy:raise ValueError('Use one tube boundary candidate; preserve beaker')
        from sciben_waterbath_recovery_bottom_proxy import author as author_bottom_hybrid
        profile=json.loads(Path(args.bottom_hybrid_manifest).read_text())['liquids']['Sample']['cavity_profile_m']
        intervention=dict(intervention or {},bottom_hybrid_colliders=author_bottom_hybrid(stage,root,profile))
    if args.bottom_reduced_manifest:
        if args.bottom_hybrid_manifest or args.shared_tube_colliders:raise ValueError('Reduced bottom requires precomposed353-cell baseline')
        from sciben_waterbath_recovery_bottom_reduced import author as author_bottom_reduced
        from sciben_waterbath_recovery_bottom_proxy import bottom_profile
        profile=bottom_profile(json.loads(Path(args.bottom_reduced_manifest).read_text())['liquids']['Sample']['cavity_profile_m'])[1]
        intervention=dict(intervention or {},reduced_bottom=author_bottom_reduced(stage,root,profile))
    if args.shared_tube_colliders:
        if args.bath_rigid_proxy:raise ValueError('Shared-tube candidate keeps beaker unchanged')
        from sciben_waterbath_recovery_shared_tube import author as author_shared_tube
        intervention=dict(intervention or {},shared_tube_colliders=author_shared_tube(stage,root))
    if args.body_ccd or args.speculative_ccd:
        if args.body_ccd and args.speculative_ccd:raise ValueError('Keep sweep and speculative CCD diagnostics separate')
        for path in [tube,bath]:
            prim=stage.GetPrimAtPath(path)
            if UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get():raise ValueError('CCD diagnostic requires dynamic bodies')
            api=PhysxSchema.PhysxRigidBodyAPI.Apply(prim);api.CreateEnableCCDAttr(args.body_ccd);api.CreateEnableSpeculativeCCDAttr(args.speculative_ccd)
        intervention=dict(intervention or {},body_sweep_CCD=args.body_ccd,body_speculative_CCD=args.speculative_ccd,CCD_bodies=[tube,bath],scene_CCD_already_enabled=True)
    if args.table_margin_no_ccd:
        if args.body_ccd or args.speculative_ccd:raise ValueError('Table-margin diagnostic disables both body CCD modes')
        from sciben_waterbath_recovery_contact_margin import author as author_table_margin
        intervention=dict(intervention or {},table_margin_no_ccd=author_table_margin(stage,root,args.table_contact_offset))
    finger_report_paths=[robot_path+'/lift2/lift2/'+side+'/'+link for side in ['fl','fr'] for link in ['link7','link8']]
    if args.finger_contact_reports:
        for path in finger_report_paths:
            p=stage.GetPrimAtPath(path)
            if not p or not p.HasAPI(UsdPhysics.RigidBodyAPI):raise ValueError('Missing finger rigid body '+path)
            PhysxSchema.PhysxContactReportAPI.Apply(p).CreateThresholdAttr(0.)
        intervention=dict(intervention or {},diagnostic_finger_contact_reports=finger_report_paths,robot_physics_unchanged=True,observer_not_deliverable=True)
    if args.disable_graph:stage.GetPrimAtPath(tube+'/ReactionRuntime').SetActive(False)
    stage.GetRootLayer().Save()
    loaded_code=stage.GetPrimAtPath(tube+'/ReactionRuntime/'+graph_name+'/FlowController').GetAttribute('inputs:script').Get()
    (out/'loaded_reaction_script.py').write_text(loaded_code)
    loaded_binding={'USD_script_sha256':hashlib.sha256(loaded_code.encode()).hexdigest(),'fixture_sha256':sha(out/'fixture.usda'),'source_input_hash_scope':list(inputs),'solver':args.solver,'max_particle_contacts':args.max_particle_contacts,'external_substeps':1,'scene_iteration_bounds':{'min':pa.GetMinPositionIterationCountAttr().Get(),'max':pa.GetMaxPositionIterationCountAttr().Get()},'robot_position_request':128,'warmup_contract':'300 measured native ticks after SDK reset; zero-advance render calls only allowed during passive startup; original actions require exactly one tick each'}
    (out/'loaded_script_binding.json').write_text(json.dumps(loaded_binding,indent=2)+'\n')
    if args.case:
        layers={l.realPath:sha(l.realPath) for l in stage.GetUsedLayers() if l.realPath and Path(l.realPath).is_file() and Path(l.realPath).resolve()!=out/'fixture.usda'}
        (out/'bound_scene_layers.json').write_text(json.dumps(layers,indent=2)+'\n')
    (out/'inputs.json').write_text(json.dumps({'inputs':inputs,'sha256':hashes,'script_sha256':sha(__file__),'graph_enabled':not args.disable_graph,'intervention':intervention,'warmup':300,'action_cadence':'one original action per native120Hz step','base_mode':'absolute','legacy_raw_yaw':args.legacy_raw_yaw,'limits':'Direct SDK reproducer; no GenManip metric/FK/camera pipeline. Metadata particles restored with zero velocities exactly as baseline loader.'},indent=2)+'\n')
    contact_events={};contact_subscription=None;active_step=None
    contact_stream=open(out/'contact_events_each_header.jsonl','w') if args.contact_timeline else None
    if args.record_contacts:
        from pxr import PhysicsSchemaTools
        def contact_event(headers,data):
            for h in headers:
                actor=[str(PhysicsSchemaTools.intToSdfPath(h.actor0)),str(PhysicsSchemaTools.intToSdfPath(h.actor1))]
                if tube not in actor and bath not in actor and not (args.finger_contact_reports and any(p in actor for p in finger_report_paths)):continue
                colliders=[str(PhysicsSchemaTools.intToSdfPath(h.collider0)),str(PhysicsSchemaTools.intToSdfPath(h.collider1))]
                key=' | '.join(sorted(actor))
                row=contact_events.setdefault(key,{'headers':0,'max_contact_points':0,'events':{},'collider_pairs':[]})
                row['headers']+=1;row['max_contact_points']=max(row['max_contact_points'],int(h.num_contact_data))
                if int(h.num_contact_data):
                    depth=min(float(data[i].separation) for i in range(h.contact_data_offset,h.contact_data_offset+h.num_contact_data))
                    row['min_separation_m']=min(row.get('min_separation_m',float('inf')),depth)
                row.setdefault('first_native_tick',len(native));row['last_native_tick']=len(native)
                if contact_stream:
                    record={'action_step':active_step,'native_tick_before_callback':len(native),'actors':actor,'colliders':colliders,'type':str(h.type),'contact_points':int(h.num_contact_data),'minimum_separation_m':None}
                    if int(h.num_contact_data):
                        worst=min(range(h.contact_data_offset,h.contact_data_offset+h.num_contact_data),key=lambda i:float(data[i].separation))
                        record.update(minimum_separation_m=float(data[worst].separation),worst_position=list(map(float,data[worst].position)),worst_normal=list(map(float,data[worst].normal)))
                    contact_stream.write(json.dumps(record)+'\n')

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
        for path in [tube,bath,robot_path+'/lift2/lift2/fl/link7',robot_path+'/lift2/lift2/fl/link8',robot_path+'/lift2/lift2/fr/link7',robot_path+'/lift2/lift2/fr/link8']:
            h=dc.get_rigid_body(path)
            if not h:continue
            v=dc.get_rigid_body_pose(h);poses[path]={'position':[v.p.x,v.p.y,v.p.z],'orientation_xyzw':[v.r.x,v.r.y,v.r.z,v.r.w]}
            lv=dc.get_rigid_body_linear_velocity(h);av=dc.get_rigid_body_angular_velocity(h);poses[path].update(linear_velocity_m_s=[lv.x,lv.y,lv.z],angular_velocity_rad_s=[av.x,av.y,av.z])
        p=stage.GetPrimAtPath(tube);state={k:p.GetAttribute(namespace+':'+k).Get() for k in ['pbd_valid','runtime_error','heated_seconds','heating_enabled','heating_block_reason','wall_contact_count']}
        return {'step':step,'native_count':len(native),'poses':poses,'state':state,'joints':robot.get_joint_positions().tolist(),'rack_matrix_rowmajor':np.asarray(UsdGeom.XformCache().GetLocalToWorldTransform(stage.GetPrimAtPath(root+'/obj_tube_rack'))).tolist()}
    dense=open(out/'poses_each_step.jsonl','w') if args.dense_pose_trace else None
    native_before_warmup=len(native);warmup_native_steps=0;startup_no_advance_calls=0;clock_failure=False;step=-300
    while step<args.steps:
        active_step=step
        if step>=0:
            action,base=normalized[step];robot._articulation_view.set_joint_position_targets(action.astype(np.float32),joint_indices=indices);robot._articulation_view.set_joint_position_targets(sdk_base_targets(base,args.legacy_raw_yaw).astype(np.float32),joint_indices=np.asarray([0,1,2]))
        before_native=len(native);world.step(render=True)
        if errors:failure='PhysX error';break
        try:advanced=native_step_decision(before_native,len(native),step<0)
        except RuntimeError as exc:failure=str(exc);clock_failure=True;break
        if not advanced:
            startup_no_advance_calls+=1
            if startup_no_advance_calls>600:failure='Startup did not advance native physics';clock_failure=True;break
            continue
        if step<0:warmup_native_steps+=1
        q=robot.get_joint_positions()
        if not np.isfinite(q).all():failure='Nonfinite joints';break
        if step>=0:completed=step+1
        dense_row=snapshot(step) if dense else None
        if dense:dense.write(json.dumps(dense_row)+'\n')
        if step==args.steps-1 or step%30==0 or (1900<=step<=2200 and step%5==0):
            if dense:dense.flush()
            if contact_stream:contact_stream.flush()
            row=dense_row or snapshot(step);trace.append(row);print('BAD09',json.dumps(row),flush=True);(out/'progress.json').write_text(json.dumps({'completed_actions':completed,'trace':trace,'errors':errors},indent=2)+'\n')
        step+=1
    if dense:dense.close()
    if contact_stream:contact_stream.close()
    report={'status':'PASS_BOUNDED_ENGINE' if not failure else 'FAIL_ENGINE','failure':failure,'completed_actions':completed,'requested_actions':args.steps,'native_clock':{'count':len(native),'min_s':min(native),'max_s':max(native),'wrong_dt':sum(abs(v-1/120)>1e-8 for v in native)},'errors':errors,'intervention':intervention,'graph_enabled':not args.disable_graph,'input_hashes':hashes,'source_inputs_unchanged':all(sha(inputs[k])==h for k,h in hashes.items()),'contact_events':contact_events,'trace':trace,'limits':['No task success claim',('Supplement-only filtering removes necessary beaker contact' if args.filter_supplement_robot and not args.restore_bath_sdf else 'Diagnostic only; separate containment and full baseline qualification required'),'No camera/FK pipeline replication']}
    report.update(native_before_warmup=native_before_warmup,warmup_native_steps=warmup_native_steps,startup_no_advance_calls=startup_no_advance_calls,action_native_cadence_checked=True,loaded_script_binding=loaded_binding,fixture_file_unchanged=sha(out/'fixture.usda')==loaded_binding['fixture_sha256'])
    if not failure and (warmup_native_steps!=300 or len(native)!=native_before_warmup+300+completed):clock_failure=True;report['failure']='Native warmup/action total mismatch'
    if report['native_clock']['wrong_dt'] or clock_failure:report['status']='FAIL_CLOCK'
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('REPORT',json.dumps({k:v for k,v in report.items() if k!='trace'}),flush=True);app.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['task_z4_silver_mirror_reaction','task_12_fehling_test'],default='task_z4_silver_mirror_reaction');p.add_argument('--baseline',required=True);p.add_argument('--case');p.add_argument('--bad-case-matrix');p.add_argument('--dense-pose-trace',action='store_true');p.add_argument('--actions',required=True);p.add_argument('--out',required=True);p.add_argument('--steps',type=int,default=2300);p.add_argument('--filter-supplement-robot',action='store_true');p.add_argument('--disable-graph',action='store_true');p.add_argument('--skip-contact-sampling',action='store_true');p.add_argument('--restore-bath-sdf',action='store_true');p.add_argument('--fluid-only-supplements',action='store_true');p.add_argument('--tube-rigid-proxy',action='store_true');p.add_argument('--proxy-curved-bottom',action='store_true');p.add_argument('--bath-rigid-proxy',action='store_true');p.add_argument('--merge-bath-floor',action='store_true');p.add_argument('--table-margin-no-ccd',action='store_true');p.add_argument('--table-contact-offset',type=float,default=.009);p.add_argument('--contact-event-sampling',action='store_true');p.add_argument('--no-contact-tensor-view',action='store_true');p.add_argument('--persistent-contact-events',action='store_true');p.add_argument('--body-ccd',action='store_true');p.add_argument('--speculative-ccd',action='store_true');p.add_argument('--solver',choices=['TGS','PGS'],default='TGS');p.add_argument('--max-particle-contacts',type=int,default=4194304);p.add_argument('--scene-max-position-iterations',type=int,default=64);p.add_argument('--shared-tube-colliders',action='store_true');p.add_argument('--bottom-hybrid-manifest');p.add_argument('--bottom-reduced-manifest');p.add_argument('--record-contacts',action='store_true');p.add_argument('--finger-contact-reports',action='store_true');p.add_argument('--robot-observer-wrapper');p.add_argument('--scene-observer-delta');p.add_argument('--asset-delta');p.add_argument('--contact-timeline',action='store_true');p.add_argument('--legacy-raw-yaw',action='store_true');run(p.parse_args())
