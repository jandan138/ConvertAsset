"""Three native ticks to validate registered SDF schema and parsed scene statistics."""
import argparse,json
from pathlib import Path

def run(source,out):
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    try:
        import omni.usd,omni.physx
        from omni.isaac.core import World
        from omni.physx.bindings._physx import PhysicsSceneStats
        from pxr import Usd,UsdPhysics,PhysxSchema,Gf,UsdUtils,PhysicsSchemaTools
        out=Path(out).resolve();out.mkdir(exist_ok=False)
        f=Usd.Stage.CreateNew(str(out/'fixture.usda'));f.GetRootLayer().subLayerPaths=[str(Path(source).resolve())];f.GetRootLayer().Save();f=None
        omni.usd.get_context().open_stage(str(out/'fixture.usda'))
        for _ in range(5):app.update()
        s=omni.usd.get_context().get_stage();s.GetPrimAtPath('/World/_scene/obj_sample_tube/ReactionRuntime').SetActive(False)
        scene=UsdPhysics.Scene.Define(s,'/World/PhysicsScene');scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));scene.CreateGravityMagnitudeAttr(9.81);pa=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
        for k,v in {'EnableGPUDynamics':True,'EnableCCD':True,'EnableStabilization':True,'BroadphaseType':'GPU','SolverType':'TGS','TimeStepsPerSecond':120,'MinPositionIterationCount':64,'MaxPositionIterationCount':128,'GpuFoundLostAggregatePairsCapacity':16384,'GpuTotalAggregatePairsCapacity':16384,'GpuMaxParticleContacts':8388608}.items():getattr(pa,'Create'+k+'Attr')().Set(v)
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        p=s.GetPrimAtPath('/World/_scene/obj_sample_tube/RimPartition/LowerSDF')
        assert p.HasAPI(PhysxSchema.PhysxSDFMeshCollisionAPI) and p.HasAPI(PhysxSchema.PhysxCollisionAPI)
        assert UsdPhysics.MeshCollisionAPI(p).GetApproximationAttr().Get()=='sdf'
        errors=[];ticks=[];es=omni.physx.get_physx_interface().get_error_event_stream().create_subscription_to_push(lambda e:errors.append(str(e.payload)));clock=omni.physx.get_physx_interface().subscribe_physics_step_events(lambda d:ticks.append(float(d)))
        w=World(physics_dt=1/120,rendering_dt=1/120,stage_units_in_meters=1.,physics_prim_path='/World/PhysicsScene',set_defaults=False);w.reset();w.step(render=True);w.pause()
        stats=PhysicsSceneStats();ok=omni.physx.get_physx_statistics_interface().get_physx_scene_statistics(UsdUtils.StageCache.Get().Insert(s).ToLongInt(),PhysicsSchemaTools.sdfPathToInt('/World/PhysicsScene'),stats)
        values={}
        for k in dir(stats):
            if k.startswith('nb_'):
                value=getattr(stats,k)
                if isinstance(value,(int,float,bool)):values[k]=value
        r={'status':'PARSE_SCHEMA_READY_LOG_DOWNGRADE_GATE_REQUIRED' if not errors and ok else 'FAIL','source':str(Path(source).resolve()),'registered_apis':p.GetAppliedSchemas(),'raw_apiSchemas':list(p.GetMetadata('apiSchemas').explicitItems),'sdf_api_recognized':p.HasAPI(PhysxSchema.PhysxSDFMeshCollisionAPI),'approximation':UsdPhysics.MeshCollisionAPI(p).GetApproximationAttr().Get(),'native_ticks':len(ticks),'native_dt':ticks,'errors':errors,'statistics_available':ok,'scene_statistics':values,'limits':['Global scene statistics do not identify a single shape geometry; parser warning audit is separately mandatory.','No robot/containment qualification.']}
        (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
    except Exception as exc:
        import traceback
        failure={'status':'FAIL_PARSE_HELPER','exception':repr(exc),'traceback':traceback.format_exc()}
        (Path(out)/'report.json').write_text(json.dumps(failure,indent=2)+'\n');print(json.dumps(failure),flush=True)
    finally:app.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.source,a.out)
