"""Diagnostic-only predeclared robot reports and read-only task USD tracing."""
import argparse,json,hashlib
from pathlib import Path
TRACE='''
# Diagnostic-only observer. No geometry, dynamics, actions or metric writes.
def _wb_diag_emit(db):
    import json,omni.usd,omni.physx
    from pxr import Usd,UsdGeom,UsdPhysics,PhysicsSchemaTools
    from omni.isaac.dynamic_control import _dynamic_control
    state=db.per_instance_state
    stage=omni.usd.get_context().get_stage()
    root=getattr(state,'five_item_root',None)
    if not root or not root.IsValid():return
    index=int(root.GetAttribute('repair:physics_step_index').Get() or 0)
    epoch=int(root.GetAttribute('repair:episode_revision').Get() or 0)
    key=(omni.usd.get_context().get_stage_id(),epoch,index)
    if getattr(state,'wb_diag_last',None)==key:return
    state.wb_diag_last=key
    if not(index<10 or index%60==0 or 2500<=index<=3800):return
    error=root.GetAttribute('repair:runtime_error').Get()
    if error:
        print('[WB_NATIVE_DIAG_ERROR]',json.dumps({'index':index,'epoch':epoch,'physics_error':str(error)}),flush=True)
        return
    dc=getattr(state,'wb_diag_dc',None)
    if dc is None:
        dc=_dynamic_control.acquire_dynamic_control_interface();state.wb_diag_dc=dc
    prefix=str(root.GetPath());robot=prefix+'/lift2';rack=prefix+'/obj_tube_rack'
    paths=[prefix+'/obj_sample_tube',prefix+'/obj_beaker']+[robot+'/lift2/lift2/'+side+'/'+link for side in ['fl','fr'] for link in ['link7','link8']]
    poses={}
    for path in paths:
        handle=dc.get_rigid_body(path)
        if not handle:
            poses[path]={'valid_native_handle':False};continue
        p=dc.get_rigid_body_pose(handle);v=dc.get_rigid_body_linear_velocity(handle);w=dc.get_rigid_body_angular_velocity(handle)
        poses[path]={'position':[p.p.x,p.p.y,p.p.z],'orientation_xyzw':[p.r.x,p.r.y,p.r.z,p.r.w],'linear_velocity_m_s':[v.x,v.y,v.z],'angular_velocity_rad_s':[w.x,w.y,w.z]}
    cache=UsdGeom.XformCache();matrix=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(rack))
    articulation=getattr(state,'wb_diag_articulation',None)
    if articulation is None:
        for prim in Usd.PrimRange(stage.GetPrimAtPath(robot)):
            if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                h=dc.get_articulation(str(prim.GetPath()))
                if h:articulation=h;state.wb_diag_articulation=h;break
    joints=dc.get_articulation_dof_states(articulation,_dynamic_control.STATE_ALL) if articulation else None
    headers,data=omni.physx.get_physx_simulation_interface().get_contact_report()
    matched=0
    for h in headers:
        actors=[str(PhysicsSchemaTools.intToSdfPath(h.actor0)),str(PhysicsSchemaTools.intToSdfPath(h.actor1))]
        colliders=[str(PhysicsSchemaTools.intToSdfPath(h.collider0)),str(PhysicsSchemaTools.intToSdfPath(h.collider1))]
        if not any(p in paths for p in actors) and not any(p.startswith(rack+'/') for p in colliders):continue
        n=int(h.num_contact_data);row={'index':index,'epoch':epoch,'actors':actors,'colliders':colliders,'type':str(h.type),'points':n,'minimum_separation_m':None,'negative_points':0,'nonnegative_points':0}
        if n:
            worst=min(range(h.contact_data_offset,h.contact_data_offset+n),key=lambda i:float(data[i].separation))
            row.update(negative_points=sum(float(data[i].separation)<0 for i in range(h.contact_data_offset,h.contact_data_offset+n)),nonnegative_points=sum(float(data[i].separation)>=0 for i in range(h.contact_data_offset,h.contact_data_offset+n)),minimum_separation_m=float(data[worst].separation),worst_position=list(map(float,data[worst].position)),worst_normal=list(map(float,data[worst].normal)))
        print('[WB_NATIVE_CONTACT]',json.dumps(row),flush=False);matched+=1
    row={'index':index,'epoch':epoch,'clock':getattr(state,'five_item_clock',{}),'poses':poses,'rack_world_matrix':[[float(matrix[i][j]) for j in range(4)] for i in range(4)],'rack_motion_model':'static collision assembly; matrix observed, no rigid root velocity invented','contact_headers':matched,'joint_positions':[float(x) for x in joints['pos']] if joints is not None else None,'joint_velocities':[float(x) for x in joints['vel']] if joints is not None else None}
    print('[WB_NATIVE_POSE]',json.dumps(row),flush=True)

_wb_diag_original_compute=compute
_wb_diag_original_cleanup=cleanup
def compute(db):
    result=_wb_diag_original_compute(db)
    try:_wb_diag_emit(db)
    except Exception as exc:
        print('[WB_NATIVE_DIAG_ERROR]',str(type(exc).__name__)+': '+str(exc),flush=True)
    return result

def cleanup(db):
    state=db.per_instance_state
    state.wb_diag_last=None;state.wb_diag_dc=None;state.wb_diag_articulation=None
    return _wb_diag_original_cleanup(db)
'''

def wrap_trace_script(source,trace_start=2500,trace_end=3800,include_palms=False):
    import ast
    ast.parse(source)
    if not 0<=trace_start<=trace_end:raise ValueError('Invalid native trace interval')
    fragment=TRACE.replace('2500<=index<=3800',str(trace_start)+'<=index<='+str(trace_end))
    if include_palms:fragment=fragment.replace("for link in ['link7','link8']","for link in ['link6','link7','link8']")
    code=source+'\n'+fragment;compile(code,'diagnostic_trace','exec');return code

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def snapshot(stage):
    values={}
    for p in stage.TraverseAll():
        for a in p.GetAttributes():
            if not a.GetName().startswith('physxContactReport:'):values[str(p.GetPath())+'::'+a.GetName()]=str(a.Get())
        for r in p.GetRelationships():
            if not r.GetName().startswith('physxContactReport:'):values[str(p.GetPath())+'::'+r.GetName()]=list(map(str,r.GetTargets()))
    return values

def build(runtime,out,task='task_12_fehling_test',case='mixed_5',trace_start=2500,trace_end=3800,include_palms=False):
    from pxr import Usd,Sdf
    runtime=Path(runtime).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    from sciben_silver_bad09_probe import case_inputs,reaction_names
    inputs=case_inputs(runtime,case,task);scene=inputs['scene'];robot=runtime/'saved/assets/robot_usds/lift2/robot.usd';graph=reaction_names(task)[1]
    src=Usd.Stage.Open(str(scene));node='/World/_scene/obj_sample_tube/ReactionRuntime/'+graph+'/FlowController';original=src.GetPrimAtPath(node).GetAttribute('inputs:script').Get();patched=wrap_trace_script(original,trace_start,trace_end,include_palms)
    layer=Usd.Stage.CreateNew(str(out/'scene_trace_delta.usda'));layer.OverridePrim('/World/obj_sample_tube/ReactionRuntime/'+graph+'/FlowController').CreateAttribute('inputs:script',Sdf.ValueTypeNames.String).Set(patched);layer.GetRootLayer().Save();(out/'original_script.py').write_text(original);(out/'diagnostic_script.py').write_text(patched)
    delta=Usd.Stage.CreateNew(str(out/'robot_report_delta.usda'));paths=[]
    for side in ['fl','fr']:
        for link in ['link7','link8']:
            path='/Root/lift2/lift2/'+side+'/'+link;p=delta.OverridePrim(path);p.AddAppliedSchema('PhysxContactReportAPI');p.CreateAttribute('physxContactReport:threshold',Sdf.ValueTypeNames.Float).Set(0.);paths.append(path)
    delta.GetRootLayer().Save();wrapper=Usd.Stage.CreateNew(str(out/'robot_observer.usda'));wrapper.GetRootLayer().subLayerPaths=[str(out/'robot_report_delta.usda'),str(robot)];wrapper.SetDefaultPrim(wrapper.GetPrimAtPath('/Root'));wrapper.GetRootLayer().Save();source_robot=Usd.Stage.Open(str(robot));before=snapshot(source_robot);after=snapshot(wrapper);assert before==after
    # No robot ancestor over enters the scene before original create_robot.
    inspect=Usd.Stage.CreateInMemory();inspect.GetRootLayer().subLayerPaths=[str(scene)];p=inspect.OverridePrim('/World/_scene');p.GetReferences().AddReference(str(out/'scene_trace_delta.usda'),'/World');assert not inspect.GetPrimAtPath('/World/_scene/lift2').IsValid()
    receipt={'status':'DIAGNOSTIC_ONLY_STATIC_PASS_NATIVE_SMOKE_PENDING','runtime_source':str(runtime),'task':task,'case':case,'source_binding':{k:{'path':str(v),'sha256':sha(v)} for k,v in inputs.items()},'dense_native_interval':[trace_start,trace_end],'palm_pose_readout':include_palms,'scene_trace_delta':str(out/'scene_trace_delta.usda'),'scene_trace_sha256':sha(out/'scene_trace_delta.usda'),'original_task_script_sha256':hashlib.sha256(original.encode()).hexdigest(),'diagnostic_task_script_sha256':hashlib.sha256(patched.encode()).hexdigest(),'original_compute_and_cleanup_bodies_preserved':patched.startswith(original),'trace_window':'native index'+str(trace_start)+'..'+str(trace_end)+' every index; before/after every60 plus first10, keyed by stage+epoch+index','trace_sinks':['stdout WB_NATIVE_POSE','stdout WB_NATIVE_CONTACT','stdout WB_NATIVE_DIAG_ERROR'],'robot_wrapper':str(out/'robot_observer.usda'),'robot_wrapper_sha256':sha(out/'robot_observer.usda'),'robot_delta':str(out/'robot_report_delta.usda'),'robot_delta_sha256':sha(out/'robot_report_delta.usda'),'original_robot':str(robot),'original_robot_sha256':sha(robot),'original_loader_expected_entry':'saved/assets/robot_usds/lift2/robot.usd','robot_default_prim':'/Root','predeclared_finger_paths':paths,'non_report_attributes_and_relationships_identical':before==after,'compared_properties':len(before),'scene_composition':'Reference scene_trace_delta /World at /World/_scene strongest, above unchanged source physical stack; no robot overs in scene','robot_composition':'New isolated diagnostic robot.usd entry can reference/layer robot_observer.usda. Its layers are robot_report_delta then untouched original robot; keep other URDF/config/material dependencies available unchanged. Never replace shared robot source.','no_play_time_API_authoring':True,'no_tensor_contact_view':True,'no_physics_or_action_or_metric_changes':True,'not_delivery_artifact':True};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--out',required=True);p.add_argument('--task',default='task_12_fehling_test');p.add_argument('--case',default='mixed_5');p.add_argument('--trace-start',type=int,default=2500);p.add_argument('--trace-end',type=int,default=3800);p.add_argument('--include-palms',action='store_true');a=p.parse_args();print(json.dumps(build(a.runtime,a.out,a.task,a.case,a.trace_start,a.trace_end,a.include_palms),indent=2))
