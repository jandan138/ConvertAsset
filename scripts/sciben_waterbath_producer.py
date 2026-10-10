#!/usr/bin/env python3
"""Source-bound Task12/Task18 dynamic bath and sample PBD producer.

Build is SDK-free USD authoring; probe starts Isaac explicitly and records native
physics callbacks. Consumer owns reaction eligibility, timers, and robot replay.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'))
from sciben_waterbath_geometry import profile_volume,seed_profile,author_profile_colliders,outside_count,collision_profile

TUBE='/World/obj_sample_tube'
BATH='/World/obj_beaker'
FLUID='/World/WaterbathFluid'


def sha(path):
    """Hash exact source and delivery bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def particles(stage,label,points,spacing,mass,material):
    """Author dynamic independent liquid phase, exact mass and live isosurface."""
    from pxr import Gf,Sdf,UsdGeom,UsdPhysics,UsdShade
    from task10_pbd_producer import attr
    system=stage.DefinePrim(FLUID+'/'+label+'System','PhysxParticleSystem')
    system.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysxParticleIsosurfaceAPI','PhysxParticleAnisotropyAPI','PhysxParticleSmoothingAPI']))
    values={'particleContactOffset':spacing*.85,'contactOffset':spacing*1.65,'restOffset':spacing,'solidRestOffset':spacing*.35,'fluidRestOffset':spacing*(.572 if label=='Bath' else .645),'maxVelocity':.2,'maxDepenetrationVelocity':2.,'physxParticleIsosurface:gridSpacing':spacing*.5,'physxParticleIsosurface:surfaceDistance':spacing*.8,'physxParticleIsosurface:gridSmoothingRadius':2.,'physxParticleAnisotropy:scale':1.,'physxParticleAnisotropy:min':.5,'physxParticleAnisotropy:max':2.}
    for k,v in values.items():attr(system,k,Sdf.ValueTypeNames.Float,v)
    for k,v in {'solverPositionIterationCount':64,'physxParticleIsosurface:maxVertices':1000000,'physxParticleIsosurface:maxTriangles':2000000,'physxParticleIsosurface:maxSubgrids':10000,'physxParticleIsosurface:numMeshSmoothingPasses':1,'physxParticleIsosurface:numMeshNormalSmoothingPasses':1}.items():attr(system,k,Sdf.ValueTypeNames.Int,v)
    for k in ['enableCCD','particleSystemEnabled','physxParticleIsosurface:isosurfaceEnabled','physxParticleAnisotropy:particleAnisotropyEnabled']:attr(system,k,Sdf.ValueTypeNames.Bool,True)
    attr(system,'physxParticleSmoothing:particleSmoothingEnabled',Sdf.ValueTypeNames.Bool,False)
    attr(system,'physxParticleIsosurface:gridFilteringPasses',Sdf.ValueTypeNames.String,'GSRS')
    UsdShade.MaterialBindingAPI.Apply(system).Bind(UsdShade.Material(stage.GetPrimAtPath(material)))
    pm=stage.DefinePrim(FLUID+'/'+label+'Physics','Material');pm.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysxPBDMaterialAPI']))
    for k,v in {'density':1000.,'friction':.1,'viscosity':0.,'cohesion':0.,'surfaceTension':0.,'adhesion':0.}.items():attr(pm,'physxPBDMaterial:'+k,Sdf.ValueTypeNames.Float,v)
    UsdShade.MaterialBindingAPI.Apply(system).Bind(UsdShade.Material(pm),materialPurpose='physics')
    geom=UsdGeom.Points.Define(stage,FLUID+'/'+label+'Particles');p=geom.GetPrim()
    p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysxParticleSetAPI','PhysicsMassAPI','MaterialBindingAPI']))
    geom.CreatePointsAttr([Gf.Vec3f(*v) for v in points]);geom.CreateVelocitiesAttr([Gf.Vec3f(0)]*len(points));geom.CreateWidthsAttr([spacing]*len(points));geom.CreateIdsAttr(list(range(len(points))))
    for k in ['fluid','selfCollision','particleEnabled']:attr(p,'physxParticle:'+k,Sdf.ValueTypeNames.Bool,True)
    attr(p,'physxParticle:particleGroup',Sdf.ValueTypeNames.Int,0 if label=='Bath' else 1)
    p.CreateRelationship('physxParticle:particleSystem').SetTargets([system.GetPath()]);UsdPhysics.MassAPI(p).CreateMassAttr(mass)
    UsdShade.MaterialBindingAPI(p).Bind(UsdShade.Material(stage.GetPrimAtPath(material)))


def build(source,out,seed_from=None):
    """Copy exact colleague source and author portable stronger physical opinions."""
    import numpy as np
    from pxr import Gf,Sdf,Usd,UsdGeom,UsdPhysics
    from task10_pbd_producer import attr
    source=Path(source).resolve();out=Path(out).resolve()
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True);shutil.copytree(source.parent,out/'source')
    original=Usd.Stage.Open(str(source)); stage=Usd.Stage.CreateNew(str(out/'scene.usda'));stage.GetRootLayer().subLayerPaths=['source/scene.usd']
    stage.SetDefaultPrim(stage.GetPrimAtPath('/World'));UsdGeom.SetStageMetersPerUnit(stage,UsdGeom.GetStageMetersPerUnit(original));UsdGeom.SetStageUpAxis(stage,UsdGeom.GetStageUpAxis(original))
    prefix='fehlings' if original.GetPrimAtPath(TUBE).HasAttribute('fehlings:cavity_profile_m') else 'tollens'
    tube_profile=[list(v) for v in original.GetPrimAtPath(TUBE).GetAttribute(prefix+':cavity_profile_m').Get()]
    height=float(original.GetPrimAtPath(TUBE).GetAttribute(prefix+':sample_height_m').Get())
    sample_profile=[v for v in tube_profile if v[0]<height]+[[height,float(np.interp(height,np.array(tube_profile)[:,0],np.array(tube_profile)[:,1]))]]
    bath_fill=[list(v) for v in original.GetPrimAtPath(BATH+'/VisualWater').GetAttribute('water:profile_m').Get()]
    body=original.GetPrimAtPath(BATH+'/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh')
    xyz=np.asarray(body.GetAttribute('points').Get());levels=np.unique(np.round(xyz[:,2],7));radius=np.linalg.norm(xyz[:,:2],axis=1)
    bath_profile=[]
    for z in levels[1:]:
        rr=radius[(np.abs(xyz[:,2]-z)<1e-7)&(radius>.001)]
        bath_profile.append([float(z),float(rr.min())])
    manifest={'schema':'sciben_waterbath_producer.v1','status':'runtime_pending','source':str(source),'source_sha256':sha(source),'physics_hz':120,'solver_position_iterations':64,'reaction_namespace':prefix,'liquids':{},'claims':{'robot_success':False,'arbitrary_motion':False,'physical_chemistry':False},'consumer_requirements':['GPU dynamics','native 1/120 physics callbacks','reset/remap world-space particle seed with each object initial pose before Play','drive SampleSystem bound material with original reaction progress; root owns heat eligibility'],'appearance_change':'Fehling dynamic sample uses original Layer0 material continuously; five fixed spatial liquid bands removed. Silver wall coating preserved separately.'}
    cache=UsdGeom.XformCache()
    for label,parent,cavity,fill,spacing,material,volume in [
        ('Bath',BATH,bath_profile,bath_fill,.0015,BATH+'/VisualWater/Looks/Water',profile_volume(bath_fill)),
        ('Sample',TUBE,tube_profile,sample_profile,.0008,TUBE+('/VisualLiquid/Looks/Layer0' if prefix=='fehlings' else '/VisualLiquid/Looks/ColorlessSolution'),8e-6)]:
        for p in Usd.PrimRange(original.GetPrimAtPath(parent)):
            path=str(p.GetPath())
            if p.GetTypeName()=='Mesh' and (('/VisualWater/' in path) or ('/VisualLiquid/' in path)):
                attr(stage.OverridePrim(path),'visibility',Sdf.ValueTypeNames.Token,'invisible')
            if p.GetAttribute('physics:collisionEnabled').Get():
                q=stage.OverridePrim(path);attr(q,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.0008);attr(q,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,0.)
        if label=='Sample':
            attr(stage.OverridePrim(TUBE+'/Visual/GlassShell'),'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True)
        else:
            attr(stage.OverridePrim(BATH+'/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh'),'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,False)
        count=author_profile_colliders(stage,parent+'/WaterbathCollision',cavity,.001 if label=='Sample' else .002)
        local=seed_profile(fill,spacing,spacing*.6);matrix=cache.GetLocalToWorldTransform(original.GetPrimAtPath(parent));world=np.asarray([matrix.Transform(Gf.Vec3d(*v)) for v in local])
        velocities=None
        if seed_from:
            saved=np.load(seed_from)
            local=saved[label+'_local_points'];local_v=saved[label+'_local_velocities']
            if len(local)!=len(world) or local.shape!=local_v.shape or not np.isfinite(local_v).all():raise ValueError('settled seed arrays/count changed')
            if outside_count(local,cavity,.001):raise ValueError('settled seed outside measured cavity')
            world=np.asarray([matrix.Transform(Gf.Vec3d(*v)) for v in local])
            velocities=np.asarray([matrix.TransformDir(Gf.Vec3d(*v)) for v in local_v])
        particles(stage,label,world,spacing,volume*1000,material)
        if velocities is not None:stage.GetPrimAtPath(FLUID+'/'+label+'Particles').GetAttribute('velocities').Set([Gf.Vec3f(*v) for v in velocities])
        manifest['liquids'][label]={'container':parent,'cavity_profile_m':cavity,'initial_fill_profile_m':fill,'nominal_volume_ml':volume*1e6,'mass_kg':volume*1000,'particle_count':len(local),'spacing_m':spacing,'particle_mass_kg':volume*1000/len(local),'points':FLUID+'/'+label+'Particles','system':FLUID+'/'+label+'System','material':material,'collision_cells':count,'collision_profile_m':collision_profile(cavity),'collision_profile_max_radial_error_m':float(max(abs(np.interp(np.asarray(cavity)[:,0],np.asarray(collision_profile(cavity))[:,0],np.asarray(collision_profile(cavity))[:,1])-np.asarray(cavity)[:,1]))),'particle_system_parameters':{a.GetName():a.Get() for a in stage.GetPrimAtPath(FLUID+'/'+label+'System').GetAttributes() if a.HasAuthoredValueOpinion() and isinstance(a.Get(),(int,float,bool,str))},'initial_container_world_matrix':np.asarray(matrix).tolist()}
    # Keep rack hole geometry; static triangle collision cannot seal its holes.
    rack=stage.GetPrimAtPath('/World/obj_tube_rack/Cube_015')
    attr(rack,'physics:approximation',Sdf.ValueTypeNames.Token,'none')
    schemas=[x for x in rack.GetMetadata('apiSchemas').GetAppliedItems() if x!='PhysxSDFMeshCollisionAPI'];rack.SetMetadata('apiSchemas',Sdf.TokenListOp.CreateExplicit(schemas))
    attr(rack,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.0005);attr(rack,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,0.)
    from task10_pbd_producer import material_closure
    core=Path('/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/lib/python3.10/site-packages/omni/mdl/core')
    manifest['material_closure']=material_closure(original,out,'isaac41',core)
    stage.GetRootLayer().subLayerPaths=['materials/isaac41/materials.usda','source/scene.usd']
    stage.GetRootLayer().Save()
    # A separate native validation entry leaves the delivery free of PhysicsScene.
    demo=Usd.Stage.CreateNew(str(out/'probe.usda'));demo.GetRootLayer().subLayerPaths=['scene.usda'];UsdGeom.SetStageMetersPerUnit(demo,1.);UsdGeom.SetStageUpAxis(demo,'Z')
    scene=UsdPhysics.Scene.Define(demo,'/World/PhysicsScene').GetPrim();scene.AddAppliedSchema('PhysxSceneAPI')
    for k,v in {'physxScene:enableGPUDynamics':True,'physxScene:enableCCD':True}.items():attr(scene,k,Sdf.ValueTypeNames.Bool,v)
    attr(scene,'physxScene:broadphaseType',Sdf.ValueTypeNames.Token,'GPU');attr(scene,'physxScene:timeStepsPerSecond',Sdf.ValueTypeNames.UInt,120)
    for k in ['minPositionIterationCount','maxPositionIterationCount']:attr(scene,'physxScene:'+k,Sdf.ValueTypeNames.UInt,64)
    for k in ['gpuFoundLostAggregatePairsCapacity','gpuTotalAggregatePairsCapacity']:attr(scene,'physxScene:'+k,Sdf.ValueTypeNames.UInt,16384)
    scene.CreateAttribute('physics:gravityDirection',Sdf.ValueTypeNames.Vector3f).Set(Gf.Vec3f(0,0,-1));scene.CreateAttribute('physics:gravityMagnitude',Sdf.ValueTypeNames.Float).Set(9.81)
    demo.GetRootLayer().Save()
    if seed_from:manifest['settled_seed']={'path':str(seed_from),'sha256':sha(seed_from),'velocities_preserved':True}
    manifest['scene_sha256']=sha(out/'scene.usda');(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:{a:v[a] for a in ['particle_count','nominal_volume_ml','collision_cells']} for k,v in manifest['liquids'].items()}))


def probe(package,out,seconds,motion=False,render=False):
    """Run true native120 World stepping, measuring every post-fetch particle set."""
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    import numpy as np
    import carb
    import omni.usd
    import omni.physx
    import omni.physx.bindings._physx as pb
    from omni.isaac.core import World
    from pxr import Gf,Usd,UsdGeom,UsdPhysics
    package=Path(package).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((package/'manifest.json').read_text())
    settings=carb.settings.get_settings();settings.set('/physics/updateToUsd',True);settings.set('/physics/updateParticlesToUsd',True);settings.set('/physics/updateVelocitiesToUsd',True);settings.set('/physics/fabricEnabled',False)
    omni.usd.get_context().open_stage(str(package/'probe.usda'))
    for _ in range(10):app.update()
    stage=omni.usd.get_context().get_stage()
    # Original legacy reaction graph is a consumer concern. Static physics probe
    # disables its execution, preserving source code in the deliverable.
    stage.GetPrimAtPath(TUBE+'/ReactionRuntime').SetActive(False)
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    errors=[]
    error_sub=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)))
    if motion:UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath(TUBE)).CreateKinematicEnabledAttr(True)
    world=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1.,physics_prim_path='/World/PhysicsScene',set_defaults=False)
    for key in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(key,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False)
    dt=[]
    clock_sub=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda v:dt.append(float(v)))
    stats={k:{'initial_count':v['particle_count'],'max_outside_count':0,'min_count':v['particle_count'],'max_count':v['particle_count'],'samples':0,'height_range_m':[1e9,-1e9]} for k,v in manifest['liquids'].items()}
    from omni.isaac.dynamic_control import _dynamic_control
    dc=_dynamic_control.acquire_dynamic_control_interface()
    post_errors=[]
    first_violations={}
    native_points={}
    def measure_native(dt_value):
        try:
            omni.physx.get_physx_interface().update_transformations(False,True,True)
            for label,v in manifest['liquids'].items():
                points=np.asarray(stage.GetPrimAtPath(v['points']).GetAttribute('points').Get(),dtype=float)
                q=dc.get_rigid_body_pose(dc.get_rigid_body(v['container']))
                rotation=np.asarray(Gf.Matrix3d(Gf.Quatd(q.r.w,Gf.Vec3d(q.r.x,q.r.y,q.r.z))))
                local=(points-np.asarray([q.p.x,q.p.y,q.p.z]))@rotation.T
                st=stats[label];outside=outside_count(local,v['cavity_profile_m'],.001)
                if outside and label not in first_violations:
                    pr=np.asarray(v['cavity_profile_m']);bad=(np.linalg.norm(local[:,:2],axis=1)>np.interp(local[:,2],pr[:,0],pr[:,1])+.001)|(local[:,2]<pr[0,0]-.001)|(local[:,2]>pr[-1,0]+.001)
                    first_violations[label]={'step':len(dt),'local_points':local[bad][:32].tolist(),'container_position':[q.p.x,q.p.y,q.p.z]}
                st['max_outside_count']=max(st['max_outside_count'],outside);st['min_count']=min(st['min_count'],len(points));st['max_count']=max(st['max_count'],len(points));st['samples']+=1
                st['height_range_m'][0]=min(st['height_range_m'][0],float(local[:,2].max()));st['height_range_m'][1]=max(st['height_range_m'][1],float(local[:,2].max()))
                native_points[label]=points.copy()
        except Exception as exc:post_errors.append(repr(exc))
    post_sub=omni.physx.get_physx_interface().subscribe_physics_on_step_events(measure_native,False,100000)
    world.reset()
    warmup_native_steps=len(dt)
    if motion:
        import omni.physics.tensors
        tensor_view=omni.physics.tensors.create_simulation_view('numpy');tensor_view.set_subspace_roots('/')
        tube_view=tensor_view.create_rigid_body_view(TUBE)
        home=np.asarray(tube_view.get_transforms()).copy()
    for i in range(round(seconds*120)):
        if motion:
            # Bounded slow120mm vertical lift and return, no teleport/reset of liquid.
            z=.12*math.sin(math.pi*min(1.,max(0.,(i/120-3)/12)))**2
            target=home.copy();target[0,2]+=z
            tube_view.set_kinematic_targets(target,np.asarray([0],dtype=np.uint32))
        world.step(render=False)
        if i%4==3:
            before_refresh=len(dt);world.render()
            if len(dt)!=before_refresh:post_errors.append('graphics refresh advanced physics')
        cache=UsdGeom.XformCache()
        if i<12:
            for label,v in manifest['liquids'].items():
                after=np.asarray(stage.GetPrimAtPath(v['points']).GetAttribute('points').Get())
                if label not in native_points or not np.array_equal(after,native_points[label]):post_errors.append('post/fetch particle mismatch '+label)
        if i%120==0:
            print('STEP',i,stats,flush=True)
            data={}
            for label,v in manifest['liquids'].items():
                data[label+'_points']=np.asarray(stage.GetPrimAtPath(v['points']).GetAttribute('points').Get())
                data[label+'_matrix']=np.asarray(cache.GetLocalToWorldTransform(stage.GetPrimAtPath(v['container'])))
            np.savez_compressed(out/f'frame_{i:05d}.npz',**data)
    if render:
        import omni.replicator.core as rep
        from pxr import UsdLux
        light=UsdLux.DomeLight.Define(stage,'/World/ProbeDome');light.CreateIntensityAttr(1000.)
        camera=UsdGeom.Camera.Define(stage,'/World/ProbeCamera')
        eye=Gf.Vec3d(.28,-.85,1.24);target=Gf.Vec3d(-.12,-.18,.88)
        matrix=Gf.Matrix4d().SetLookAt(eye,target,Gf.Vec3d(0,0,1)).GetInverse()
        camera.AddTransformOp().Set(matrix);camera.CreateFocalLengthAttr(35.);camera.CreateClippingRangeAttr(Gf.Vec2f(.01,100.))
        product=rep.create.render_product('/World/ProbeCamera',(1280,720));annotator=rep.AnnotatorRegistry.get_annotator('rgb');annotator.attach([product])
        for _ in range(40):world.render()
        from PIL import Image
        Image.fromarray(annotator.get_data()).save(out/'preview.png')
    saved={}
    for label,v in manifest['liquids'].items():
        q=dc.get_rigid_body_pose(dc.get_rigid_body(v['container']))
        rot=np.asarray(Gf.Matrix3d(Gf.Quatd(q.r.w,Gf.Vec3d(q.r.x,q.r.y,q.r.z))))
        geom=stage.GetPrimAtPath(v['points']);xyz=np.asarray(geom.GetAttribute('points').Get());vel=np.asarray(geom.GetAttribute('velocities').Get())
        saved[label+'_local_points']=(xyz-np.asarray([q.p.x,q.p.y,q.p.z]))@rot.T
        saved[label+'_local_velocities']=vel@rot.T
    np.savez_compressed(out/'final_local_state.npz',**saved)
    clock={'count':len(dt),'min_s':min(dt) if dt else None,'max_s':max(dt) if dt else None,'sum_s':sum(dt),'world_dt':world.get_physics_dt()}
    passed=not errors and not post_errors and bool(dt) and all(abs(v-1/120)<1e-8 for v in dt) and all(s['samples']==len(dt) and s['max_outside_count']==0 and s['min_count']==s['max_count']==s['initial_count'] for s in stats.values())
    report={'status':'PASS' if passed else 'FAIL','scope':'prescribed120mm_lift_return' if motion else 'static_cold','runtime':'Isaac4.1','seconds':seconds,'native_clock':clock,'liquids':stats,'manifest_sha256':sha(package/'manifest.json'),'scene_sha256':sha(package/'scene.usda'),'containment_tolerance_m':.001,'no_particle_rewrite':True,'dynamic_containers':not motion,'motion_driver':'native_kinematic_targets_liquid_dynamic' if motion else None,'robot_replay':False,'physics_errors':errors,'post_errors':post_errors,'first_violations':first_violations,'warmup_native_steps':warmup_native_steps,'sampling':'every_native_post_step_including_sdk_warmup','post_fetch_checks':min(12,round(seconds*120))}
    report['script_sha256']=sha(__file__)
    report['cooking_log_audit_required']=True
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);app.close()


def robot_probe(package,out,episode,steps=900,filter_tube=False,composed_scene=None,contact_capacity=128):
    """Isolated Isaac4.1 replay of exact Lift2 USD/LMDB actions, no GenManip imports."""
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    import pickle,lmdb,numpy as np,io
    class CompatUnpickler(pickle.Unpickler):
        def find_class(self,module,name):
            return super().find_class(module.replace('numpy._core','numpy.core'),name)
    import omni.usd,omni.physx,carb
    import omni.physx.bindings._physx as pb
    from omni.isaac.core import World
    from omni.isaac.core.robots import Robot
    from omni.isaac.dynamic_control import _dynamic_control
    from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,Gf,Sdf
    from sciben_waterbath_geometry import separate_tube_contacts
    package=Path(package).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);episode=Path(episode)
    metadata=CompatUnpickler(open(episode/'meta_info.pkl','rb')).load();layout=metadata['task_data']['initial_layout'];manifest=json.load(open(package/'manifest.json'))
    with lmdb.open(str(episode/'lmdb'),readonly=True,lock=False,create=False).begin() as txn:
        arm=np.asarray(CompatUnpickler(io.BytesIO(txn.get(b'arm_action'))).load());grip=np.asarray(CompatUnpickler(io.BytesIO(txn.get(b'gripper_action'))).load());base=np.asarray(CompatUnpickler(io.BytesIO(txn.get(b'base_motion'))).load())
    settings=carb.settings.get_settings()
    for k in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(k,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False);omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    scene_root='/World/_scene' if composed_scene else '/World'
    tube=scene_root+'/obj_sample_tube'
    if composed_scene:
        for v in manifest['liquids'].values():
            for k in ['container','points','system','material']:v[k]=v[k].replace('/World/',scene_root+'/')
        host=Usd.Stage.CreateNew(str(out/'fixture.usda'));host.GetRootLayer().subLayerPaths=[str(Path(composed_scene).resolve())];host.DefinePrim('/World','Xform');host.SetDefaultPrim(host.GetPrimAtPath('/World'));UsdGeom.SetStageMetersPerUnit(host,1.);UsdGeom.SetStageUpAxis(host,'Z')
        Sdf.CreatePrimInLayer(host.GetRootLayer(),'/World')
        Sdf.CopySpec(Sdf.Layer.FindOrOpen(str(package/'probe.usda')),'/World/PhysicsScene',host.GetRootLayer(),'/World/PhysicsScene');host.GetRootLayer().Save();host=None
        entry=out/'fixture.usda'
    else:entry=package/'probe.usda'
    omni.usd.get_context().open_stage(str(entry))
    for _ in range(5):app.update()
    stage=omni.usd.get_context().get_stage();stage.GetPrimAtPath(tube+'/ReactionRuntime').SetActive(False)
    scene=stage.GetPrimAtPath('/World/PhysicsScene');scene.CreateAttribute('physxScene:gpuMaxParticleContacts',Sdf.ValueTypeNames.UInt).Set(4194304)
    scene.CreateAttribute('physxScene:enableStabilization',Sdf.ValueTypeNames.Bool).Set(True)
    cache=UsdGeom.XformCache();old={k:cache.GetLocalToWorldTransform(stage.GetPrimAtPath(v['container'])) for k,v in manifest['liquids'].items()}
    def pose(prim,position,orientation,scale=(1,1,1)):
        x=UsdGeom.Xformable(prim);x.ClearXformOpOrder();x.AddTranslateOp(opSuffix='robotProbe').Set(Gf.Vec3d(*position));x.AddOrientOp(opSuffix='robotProbe').Set(Gf.Quatf(float(orientation[0]),Gf.Vec3f(*orientation[1:])));x.AddScaleOp(opSuffix='robotProbe').Set(Gf.Vec3f(*scale))
    for name,v in layout.items():
        if v['type']=='robot':continue
        p=stage.GetPrimAtPath(v['prim_path'].replace('/World/_scene',scene_root));pose(p,v['position'],v['orientation'],v['scale'])
    cache=UsdGeom.XformCache()
    for k,v in manifest['liquids'].items():
        transform=old[k].GetInverse()*cache.GetLocalToWorldTransform(stage.GetPrimAtPath(v['container']));geom=UsdGeom.Points(stage.GetPrimAtPath(v['points']))
        geom.GetPointsAttr().Set([Gf.Vec3f(*transform.Transform(Gf.Vec3d(*p))) for p in geom.GetPointsAttr().Get()]);geom.GetVelocitiesAttr().Set([Gf.Vec3f(*transform.TransformDir(Gf.Vec3d(*p))) for p in geom.GetVelocitiesAttr().Get()])
        stage.GetPrimAtPath(v['system']).CreateRelationship('simulationOwner').SetTargets(['/World/PhysicsScene'])
        PhysxSchema.PhysxContactReportAPI.Apply(stage.GetPrimAtPath(v['container'])).CreateThresholdAttr(0.)
    robot_path=scene_root+'/lift2';robot_usd=Path('/mnt/data/zhuzihou/GenManip-Sim/saved/assets/robot_usds/lift2/robot.usd')
    rp=stage.DefinePrim(robot_path,'Xform');rp.GetReferences().AddReference(str(robot_usd));robot_layout=layout['lift2'];pose(rp,robot_layout['position'],robot_layout['orientation'])
    for p in Usd.PrimRange(rp):
        if p.HasAPI(UsdPhysics.RigidBodyAPI):PhysxSchema.PhysxRigidBodyAPI.Apply(p).CreateMaxDepenetrationVelocityAttr(1.)
        path=str(p.GetPath())
        if p.IsA(UsdPhysics.Joint) and any(v in path for v in ['/fl/','/fr/']) and path.endswith(tuple('joint'+str(i) for i in range(1,7))):PhysxSchema.PhysxJointAPI.Apply(p).CreateArmatureAttr(.01)
    mat=stage.GetPrimAtPath(robot_path+'/lift2/lift2/PhysicsMaterial');phys=UsdPhysics.MaterialAPI(mat);phys.CreateStaticFrictionAttr(2.5);phys.CreateDynamicFrictionAttr(2.5);phys.CreateRestitutionAttr(0.)
    api=PhysxSchema.PhysxMaterialAPI.Apply(mat);api.CreateFrictionCombineModeAttr('max');api.CreateRestitutionCombineModeAttr('multiply');api.CreateImprovePatchFrictionAttr(True)
    lift=stage.GetPrimAtPath(robot_path+'/lift2/lift2/base_link/joint4');drive=UsdPhysics.DriveAPI.Get(lift,'linear');drive.CreateStiffnessAttr(1000000.);drive.CreateDampingAttr(10000.);drive.CreateMaxForceAttr(1000000.)
    filters=separate_tube_contacts(stage,scene_root) if filter_tube else None
    if composed_scene:stage.GetRootLayer().Save()
    else:
        stage.GetRootLayer().Export(str(out/'fixture.usda'))
        fixture_layer=Sdf.Layer.FindOrOpen(str(out/'fixture.usda'));fixture_layer.subLayerPaths=[str(package/'scene.usda')];fixture_layer.Save()
    world=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1,physics_prim_path='/World/PhysicsScene',set_defaults=False)
    robot=world.scene.add(Robot(prim_path=robot_path,name='lift2'))
    for k in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(k,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False)
    errors=[];dt=[];error_sub=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)) if len(errors)<32 else None)
    clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda v:dt.append(float(v)))
    world.reset();reset_native_steps=len(dt);robot.set_solver_position_iteration_count(128);robot.set_solver_velocity_iteration_count(4);robot.set_stabilization_threshold(.005)
    q=np.asarray(robot_layout['joint_positions'],dtype=np.float32);robot.set_joint_positions(q);robot.set_joint_velocities(np.zeros_like(q));robot._articulation_view.set_joint_position_targets(q)
    dc=_dynamic_control.acquire_dynamic_control_interface();trace=[];indices=np.asarray([10,12,14,16,18,20,23,24,9,11,13,15,17,19,21,22],dtype=np.int32)
    import omni.physics.tensors as tensors
    contact_sim=tensors.create_simulation_view('numpy');contact_sim.set_subspace_roots('/')
    contact_view=contact_sim.create_rigid_contact_view([tube],filter_patterns=[[scene_root+'/obj_beaker']],max_contact_data_count=contact_capacity) if contact_capacity>0 else None
    max_contacts=0
    failed=None
    for i in range(300+steps):
        source=max(0,((i-300)//3)*2+(((i-300)%3)>=1)) if i>=300 else None
        if source is not None:
            action=np.r_[arm[source,:6],grip[source,:2],arm[source,6:],grip[source,2:]].astype(np.float32)
            robot._articulation_view.set_joint_position_targets(action,joint_indices=indices)
            robot._articulation_view.set_joint_position_targets(base[source],joint_indices=np.asarray([0,1,2]))
        world.step(render=True)
        if errors:failed='PhysX error';break
        contact_count=int(np.asarray(contact_view.get_contact_data(1/120)[4]).sum()) if contact_view is not None else 0;max_contacts=max(max_contacts,contact_count)
        pos=robot.get_joint_positions()
        if not np.isfinite(pos).all():failed='nonfinite joint state';break
        if i%30==0:
            bp=dc.get_rigid_body_pose(dc.get_rigid_body(tube));row={'step':i,'contact_count':contact_count,'source_frame':source,'tube_position':[bp.p.x,bp.p.y,bp.p.z],'left_finger_positions':pos[[23,24]].tolist(),'joint_max_abs':float(np.max(np.abs(pos)))}
            trace.append(row);print('ROBOT',json.dumps(row),flush=True);(out/'progress.json').write_text(json.dumps({'trace':trace,'errors':errors},indent=2))
    if failed is None and (len(dt)!=reset_native_steps+300+steps or not all(abs(v-1/120)<1e-8 for v in dt)):failed='native physics clock mismatch'
    result={'status':'PASS' if failed is None else 'FAIL','scope':'isolated_Lift2_recorded_contact_replay_no_GenManip','composed_scene':str(composed_scene) if composed_scene else None,'composed_scene_sha256':sha(composed_scene) if composed_scene else None,'filter_tube':filter_tube,'filters':filters,'failure':failed,'errors':errors,'max_contact_count':max_contacts,'contact_capacity':contact_capacity,'last_step':i,'requested_steps':steps,'warmup_steps':300,'native_clock':{'count':len(dt),'min_s':min(dt),'max_s':max(dt)},'source_step_pattern':[1,2],'scene_sha256':sha(package/'scene.usda'),'metadata_sha256':sha(episode/'meta_info.pkl'),'robot_usd':str(robot_usd),'robot_usd_sha256':sha(robot_usd),'trace':trace,'caveat':'Isolated source scene, no background or GenManip task logic. Not task-success or liquid-containment qualification.'}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);app.close()


def wall_probe(package,out,contact_capacity=128):
    """Bounded bottom/side contacts; kinematic tube, dynamic bath and real fluids."""
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    import numpy as np,carb,omni.usd,omni.physx,omni.physics.tensors as tensors
    import omni.physx.bindings._physx as pb
    from omni.isaac.core import World
    from omni.isaac.dynamic_control import _dynamic_control
    from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf,Sdf
    package=Path(package).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);manifest=json.load(open(package/'manifest.json'))
    settings=carb.settings.get_settings()
    for key in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(key,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False);omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    omni.usd.get_context().open_stage(str(package/'probe.usda'))
    for _ in range(5):app.update()
    stage=omni.usd.get_context().get_stage();stage.GetPrimAtPath(TUBE+'/ReactionRuntime').SetActive(False)
    scene=stage.GetPrimAtPath('/World/PhysicsScene');scene.CreateAttribute('physxScene:gpuMaxParticleContacts',Sdf.ValueTypeNames.UInt).Set(4194304)
    cache=UsdGeom.XformCache();old=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(TUBE));bath_home=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(BATH)).ExtractTranslation()
    start=Gf.Vec3d(bath_home[0],bath_home[1],bath_home[2]+.13)
    x=UsdGeom.Xformable(stage.GetPrimAtPath(TUBE));x.ClearXformOpOrder();x.AddTranslateOp(opSuffix='wallProbe').Set(start)
    UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath(TUBE)).CreateKinematicEnabledAttr(True)
    transform=old.GetInverse()*Gf.Matrix4d().SetTranslate(start);geom=UsdGeom.Points(stage.GetPrimAtPath(manifest['liquids']['Sample']['points']))
    geom.GetPointsAttr().Set([Gf.Vec3f(*transform.Transform(Gf.Vec3d(*p))) for p in geom.GetPointsAttr().Get()]);geom.GetVelocitiesAttr().Set([Gf.Vec3f(*transform.TransformDir(Gf.Vec3d(*v))) for v in geom.GetVelocitiesAttr().Get()])
    for v in manifest['liquids'].values():
        PhysxSchema.PhysxContactReportAPI.Apply(stage.GetPrimAtPath(v['container'])).CreateThresholdAttr(0.)
        stage.GetPrimAtPath(v['system']).CreateRelationship('simulationOwner').SetTargets(['/World/PhysicsScene'])
    world=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1.,physics_prim_path='/World/PhysicsScene',set_defaults=False)
    for key in [pb.SETTING_UPDATE_TO_USD,pb.SETTING_UPDATE_PARTICLES_TO_USD,pb.SETTING_UPDATE_VELOCITIES_TO_USD]:settings.set(key,True)
    settings.set(pb.SETTING_SUPPRESS_READBACK,False)
    errors=[];dt=[];error_sub=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)) if len(errors)<32 else None)
    clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda d:dt.append(float(d)))
    world.reset();reset_count=len(dt)
    view=tensors.create_simulation_view('numpy');view.set_subspace_roots('/');body=view.create_rigid_body_view(TUBE);contacts=view.create_rigid_contact_view([TUBE],filter_patterns=[[BATH]],max_contact_data_count=contact_capacity)
    dc=_dynamic_control.acquire_dynamic_control_interface();trace=[];max_counts={};failure=None;finite=True
    # Absolute bounded fixture trajectory; the dynamic beaker may move under contact.
    segments=[('settle',1.,0.,.13),('lower_bottom',3.,0.,.0035),('bottom_hold',1.,0.,.0035),('clear_bottom',1.,0.,.025),('approach_side',3.,.028,.025),('side_hold',1.,.028,.025),('withdraw_side',2.,0.,.025)]
    prev=np.array([0.,.13]);step=0
    for phase,duration,tx,tz in segments:
        max_counts[phase]=0;target=np.array([tx,tz]);n=round(duration*120)
        for j in range(n):
            alpha=(j+1)/n;smooth=alpha*alpha*(3-2*alpha);local=prev+(target-prev)*smooth
            pos=np.array([bath_home[0]+local[0],bath_home[1],bath_home[2]+local[1]],dtype=np.float32)
            body.set_kinematic_targets(np.asarray([[*pos,0,0,0,1]],dtype=np.float32),np.asarray([0],dtype=np.uint32));world.step(render=True);step+=1
            if errors:failure='PhysX error';break
            data=contacts.get_contact_data(1/120);count=int(np.asarray(data[4]).sum());max_counts[phase]=max(max_counts[phase],count)
            for v in manifest['liquids'].values():
                pts=np.asarray(stage.GetPrimAtPath(v['points']).GetAttribute('points').Get());finite &= bool(np.isfinite(pts).all() and len(pts)==v['particle_count'])
            bp=dc.get_rigid_body_pose(dc.get_rigid_body(BATH));finite &= bool(np.isfinite([bp.p.x,bp.p.y,bp.p.z]).all())
            if not finite:failure='Nonfinite state or changed particle count';break
            if step%30==0 or count>0 and max_counts[phase]==count and step%10==0:
                row={'step':step,'phase':phase,'contact_count':count,'bath_position':[bp.p.x,bp.p.y,bp.p.z],'tube_target':pos.tolist()};trace.append(row);print('WALL',json.dumps(row),flush=True)
                (out/'progress.json').write_text(json.dumps({'trace':trace,'max_counts':max_counts,'errors':errors},indent=2))
        if failure:break
        prev=target
    contact_gate=max_counts.get('bottom_hold',0)>0 and max_counts.get('side_hold',0)>0
    capacity_gate=max(max_counts.values(),default=0)<=contact_capacity
    clock_gate=len(dt)==reset_count+step and all(abs(d-1/120)<1e-8 for d in dt)
    result={'status':'PASS' if not failure and contact_gate and clock_gate and capacity_gate else 'FAIL','scope':'bounded_kinematic_tube_dynamic_beaker_actual_bottom_and_side_contact','contact_capacity':contact_capacity,'max_contact_counts':max_counts,'contact_gate':contact_gate,'capacity_gate':capacity_gate,'finite_states_and_particle_counts':finite,'errors':errors,'failure':failure,'native_clock':{'count':len(dt),'min_s':min(dt),'max_s':max(dt)},'steps':step,'reset_native_steps':reset_count,'scene_sha256':sha(package/'scene.usda'),'manifest_sha256':sha(package/'manifest.json'),'script_sha256':sha(__file__),'trace':trace,'limits':['No robot or reaction qualification','No collision filtering or geometry changes','Tube initial pose and particle seed remapped beforePlay; tube then moves bynativekinematictargets','No liquid-containment qualification from this contact stress fixture']}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);app.close()


def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('build');p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--seed-from')
    p=sub.add_parser('probe');p.add_argument('--package',required=True);p.add_argument('--out',required=True);p.add_argument('--seconds',type=float,default=15);p.add_argument('--motion',action='store_true');p.add_argument('--render',action='store_true')
    p=sub.add_parser('robot_probe');p.add_argument('--package',required=True);p.add_argument('--out',required=True);p.add_argument('--episode',required=True);p.add_argument('--steps',type=int,default=900);p.add_argument('--filter-tube',action='store_true');p.add_argument('--composed-scene');p.add_argument('--contact-capacity',type=int,default=128)
    p=sub.add_parser('wall_probe');p.add_argument('--package',required=True);p.add_argument('--out',required=True);p.add_argument('--contact-capacity',type=int,default=128)
    args=parser.parse_args();values=vars(args);command=values.pop('command');globals()[command](**values)

if __name__=='__main__':main()
