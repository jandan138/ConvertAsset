"""Diagnostic immediate PhysX tube/beaker contact reports, embedded in USD."""
def contact_header_count(headers,tube,bath,capacity,decode):
    actors=frozenset((tube,bath));count=0
    for h in headers:
        if frozenset((decode(h.actor0),decode(h.actor1)))!=actors:continue
        n=int(h.num_contact_data)
        if n<0:raise RuntimeError('Negative immediate contact count')
        count+=n
    if count>capacity:raise RuntimeError('Rigid contact report capacity exceeded: '+str(count))
    return count


class PersistentContactCounts:
    """Block on current reported contacts or retained sleeping active pairs."""
    def __init__(self,tube,bath,capacity):
        self.actors=frozenset((tube,bath));self.capacity=capacity;self.pairs={};self.initialized=False

    def read(self,headers,decode,tube_sleeping):
        pairs=self.pairs.copy();reported=0
        try:
            for h in headers:
                if frozenset((decode(h.actor0),decode(h.actor1)))!=self.actors:continue
                key=tuple(sorted((decode(h.collider0),decode(h.collider1))));kind=str(h.type)
                if kind.endswith('CONTACT_LOST'):pairs.pop(key,None)
                elif kind.endswith(('CONTACT_FOUND','CONTACT_PERSIST')):
                    n=int(h.num_contact_data)
                    if n<=0:raise RuntimeError('Active contact report has no valid contact points')
                    pairs[key]=n;reported+=n
                else:raise RuntimeError('Unknown contact event type: '+kind)
            known=self.initialized or not tube_sleeping
            count=max(sum(pairs.values()),reported)
            if count>self.capacity:raise RuntimeError('Active contact record capacity exceeded: '+str(count))
            if not known and count==0:raise RuntimeError('Contact state uninitialized while sample tube sleeps; heating blocked')
        except Exception:
            self.pairs={};self.initialized=False
            raise
        self.pairs=pairs;self.initialized=known
        return count


PERSISTENT_EMBEDDED='''
def _repair_persistent_contact_count(state,epoch,index,tube_path,bath_path,capacity):
    import omni.physx,omni.usd
    from pxr import PhysicsSchemaTools
    sim=omni.physx.get_physx_simulation_interface()
    stage_id=omni.usd.get_context().get_stage_id()
    key=(stage_id,epoch,tube_path,bath_path)
    if getattr(state,'repair_pair_key',None)!=key or index<getattr(state,'repair_pair_last_index',-1):
        state.repair_pair_counter=PersistentContactCounts(tube_path,bath_path,capacity)
        state.repair_pair_key=key
    state.repair_pair_last_index=index
    headers,data=sim.get_contact_report()
    sleeping=sim.is_sleeping(stage_id,PhysicsSchemaTools.sdfPathToInt(tube_path))
    return state.repair_pair_counter.read(headers,lambda value:str(PhysicsSchemaTools.intToSdfPath(value)),sleeping)

_repair_pairs_original_cleanup=cleanup
def cleanup(db):
    state=db.per_instance_state
    state.repair_pair_key=None
    state.repair_pair_counter=None
    state.repair_pair_last_index=-1
    _repair_pairs_original_cleanup(db)
'''


EMBEDDED='''
def _repair_immediate_contact_count(tube_path,bath_path,capacity):
    import omni.physx
    from pxr import PhysicsSchemaTools
    headers,data=omni.physx.get_physx_simulation_interface().get_contact_report()
    return contact_header_count(headers,tube_path,bath_path,capacity,lambda value:str(PhysicsSchemaTools.intToSdfPath(value)))
'''


def patch_source(source,keep_tensor_view=True,persistent=False):
    import inspect
    needle="    contact=state.repair_contacts.get_contact_data(1/120)\n    count=bounded_contact_count(contact[4],config['contact_capacity'])"
    if source.count(needle)!=1:raise ValueError('Expected exactly one known sampling block')
    replacement="    count=_repair_immediate_contact_count(str(tube.GetPath()),str(bath.GetPath()),config['contact_capacity'])"
    if not keep_tensor_view:
        block="    if getattr(state,'repair_contact_epoch',None)!=epoch:\n        state.repair_sim=tensors.create_simulation_view('numpy');state.repair_sim.set_subspace_roots('/')\n        state.repair_contacts=state.repair_sim.create_rigid_contact_view([str(tube.GetPath())],filter_patterns=[[str(bath.GetPath())]],max_contact_data_count=config['contact_capacity'])\n        state.repair_contact_epoch=epoch\n"
        if source.count(block)!=1:raise ValueError('Expected exactly one known tensor view creation block')
        source=source.replace(block,'',1)
    if persistent:
        import ast
        from pathlib import Path
        text=Path(__file__).read_text();node=next(v for v in ast.parse(text).body if isinstance(v,ast.ClassDef) and v.name=='PersistentContactCounts')
        class_source=''.join(text.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
        replacement="    count=_repair_persistent_contact_count(state,epoch,int(stage.GetPrimAtPath(root).GetAttribute('repair:physics_step_index').Get()),str(tube.GetPath()),str(bath.GetPath()),config['contact_capacity'])"
        return source.replace(needle,replacement,1)+'\n'+class_source+'\n'+PERSISTENT_EMBEDDED
    return source.replace(needle,replacement,1)+'\n'+inspect.getsource(contact_header_count)+'\n'+EMBEDDED


def build_delta(source,out,persistent=False):
    import json,hashlib
    from pathlib import Path
    from pxr import Usd,Sdf
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    stage=Usd.Stage.Open(str(source));root='/World/_scene';matches=[]
    for p in Usd.PrimRange(stage.GetPrimAtPath(root+'/obj_sample_tube/ReactionRuntime')):
        a=p.GetAttribute('inputs:script')
        if a and 'state.repair_contacts.get_contact_data(1/120)' in str(a.Get()):matches.append(a)
    if len(matches)!=1:raise ValueError('Expected one reaction sampling script')
    a=matches[0];original=a.Get();patched=patch_source(original,keep_tensor_view=False,persistent=persistent)
    compile(patched,'<embedded-reaction>','exec')
    layer=Sdf.Layer.CreateAnonymous();stage.GetRootLayer().subLayerPaths.insert(0,layer.identifier);stage.SetEditTarget(layer);a.Set(patched)
    target=out/('active_contact_delta.usda' if persistent else 'immediate_contact_delta.usda');portable=Sdf.Layer.CreateNew(str(target));Sdf.CopySpec(layer,root,portable,'/World');portable.Save()
    (out/'reaction_original.py').write_text(original);(out/'reaction_immediate.py').write_text(patched)
    receipt={'status':'DIAGNOSTIC_PENDING','source_wrapper':str(source),'source_wrapper_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_script_sha256':hashlib.sha256(original.encode()).hexdigest(),'new_script_sha256':hashlib.sha256(patched.encode()).hexdigest(),'delta':str(target),'delta_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'authoring_root':'/World','runtime_root':'/World/_scene','patched_attribute':str(a.GetPath()).replace(root,'/World',1),'change':'Only detailed tensor contact read and its unused view initialization replaced by stateless immediate PhysX header point count; same heating_gate and capacity.','tensor_contact_view_created':False,'collision_geometry_changed':False,'threshold_requirement':'tube and bath PhysxContactReportAPI threshold0; already authored in D v2','lifecycle':'No contact subscriptions or persistent contact count state added; live sleeping-touch/reset qualification pending.'}
    if persistent:
        receipt['change']='Only contact readout backend changes: active collider-pair records from immediate native reports, kept across sleeping ticks, explicit LOST release, epoch/index/cleanup resets; original heating gate remains.'
        receipt['lifecycle']='State keyed by stage id, episode revision, actor paths; native index rollback and cleanup clear state. Only awake sampling establishes complete clear state. Partial reports during late sleeping initialization may block on positive evidence but never establish clearance; unknown empty state and invalid data fail closed.'
        receipt['wall_contact_count_semantics']='Maximum of current-step reported contact points and retained active-pair point counts (including sleep). A transient FOUND then LOST still blocks that step. Not newly measured points each frame.'
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--persistent',action='store_true');a=p.parse_args();print(json.dumps(build_delta(a.source,a.out,a.persistent),indent=2))
