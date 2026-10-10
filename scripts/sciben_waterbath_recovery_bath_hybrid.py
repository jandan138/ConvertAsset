"""New strongest beaker rigid layer over the measured hybrid617 tube input."""
import argparse,hashlib,json
from pathlib import Path

def filter_audit(stage,root):
    from pxr import UsdPhysics
    result={}
    for label in ['Sample','Bath']:
        targets=list(map(str,UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets()))
        bottom=[p for p in targets if p.startswith(root+'/obj_sample_tube/RigidWallProxy/Bottom_')]
        bath=[p for p in targets if p.startswith(root+'/obj_beaker/RigidBathProxy/')]
        other=[p for p in targets if p not in bottom+bath]
        if len(bottom)!=144 or len(bath)!=96 or other or len(targets)!=240:raise ValueError('Expected exactly tube Bottom144 + bath96; got '+str((len(bottom),len(bath),other)))
        result[label]={'total':len(targets),'tube_bottom':len(bottom),'bath':len(bath),'other':other,'tube_straight_lip_shared_with_PBD':True}
    return result

def build(source,out):
    from pxr import Usd,Sdf,UsdPhysics
    from sciben_waterbath_recovery_bath import author,invariant_snapshot
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);root='/World/_scene'
    stage=Usd.Stage.CreateInMemory();stage.GetRootLayer().subLayerPaths=[str(source)]
    before=invariant_snapshot(stage,root);prior={label:list(map(str,UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets())) for label in ['Sample','Bath']}
    if any(len(v)!=144 or any('/RigidWallProxy/Bottom_' not in p for p in v) for v in prior.values()):raise ValueError('Source must be hybrid with144 bottom filters')
    intervention=author(stage,root);after=invariant_snapshot(stage,root)
    if before!=after:raise ValueError('Physical, particle or visible invariant changed')
    filters=filter_audit(stage,root);layer=stage.GetRootLayer();layer.subLayerPaths=[];layer.Export(str(out/'runtime_delta.usda'))
    package=Sdf.Layer.CreateNew(str(out/'bath_hybrid_delta.usda'));Sdf.CopySpec(layer,root,package,'/World');package.Save()
    wrapper=Usd.Stage.CreateNew(str(out/'scene.usda'));wrapper.GetRootLayer().subLayerPaths=[str(out/'runtime_delta.usda'),str(source)];wrapper.GetRootLayer().Save();assert filter_audit(wrapper,root)==filters
    enabled={}
    for obj in ['obj_sample_tube','obj_beaker']:
        enabled[obj]=sum(p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False for p in Usd.PrimRange(wrapper.GetPrimAtPath(root+'/'+obj)))
    if enabled!={'obj_sample_tube':617,'obj_beaker':354}:raise ValueError('Unexpected collider inventory '+str(enabled))
    delta=out/'bath_hybrid_delta.usda';receipt={'status':'STATIC_ONLY_RUNTIME_PENDING','source':str(source),'portable_delta':str(delta),'delta_sha256':hashlib.sha256(delta.read_bytes()).hexdigest(),'intervention':intervention,'invariants_unchanged':True,'invariant_attribute_count':len(before),'particle_filters':filters,'enabled_colliders':enabled,'composition':'bath hybrid delta strongest at /World over [counter_v2,bottom_hybrid,tube_v2,fluid,original]; mapped to /World/_scene','old_bath_v1_failure_retained':True,'scope':'No cold/lift, table impact or robot qualification inherited for new beaker proxy.'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.out),indent=2))
