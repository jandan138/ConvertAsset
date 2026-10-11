"""Explicit original-table contact margin; no added shape or rest-distance shift."""
import argparse,hashlib,json
from pathlib import Path

def author(stage,root,margin=.009):
    from pxr import Usd,UsdPhysics,Sdf
    if margin not in [.009,.017]:raise ValueError('Use only measured9mm translational or17mm angular margin')
    table=stage.GetPrimAtPath(root+'/table');shapes=[p for p in Usd.PrimRange(table) if p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False]
    if len(shapes)!=1:raise ValueError('Expected exactly one original table collider')
    p=shapes[0];old={'contactOffset':p.GetAttribute('physxCollision:contactOffset').Get(),'restOffset':p.GetAttribute('physxCollision:restOffset').Get()};rest_authored=bool(p.GetAttribute('physxCollision:restOffset') and p.GetAttribute('physxCollision:restOffset').HasAuthoredValueOpinion());p.AddAppliedSchema('PhysxCollisionAPI');p.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(margin)
    for obj in ['obj_sample_tube','obj_beaker']:
        body=stage.GetPrimAtPath(root+'/'+obj);body.AddAppliedSchema('PhysxRigidBodyAPI')
        for key in ['physxRigidBody:enableCCD','physxRigidBody:enableSpeculativeCCD']:body.CreateAttribute(key,Sdf.ValueTypeNames.Bool).Set(False)
    return {'table_shape':str(p.GetPath()),'original_table_offsets':old,'original_auto_contact_offset_runtime_value_unknown':old['contactOffset'] is None or old['contactOffset']==float('-inf'),'table_contactOffset_m':margin,'table_restOffset_unchanged':True,'table_restOffset_previously_authored':rest_authored,'two_body_sweep_and_speculative_CCD':False,'added_shapes':0,'container_heater_PBD_offsets_unchanged':True,'basis':('Measured no-CCD50mm initial drop crosses8.19mm/tick.' if margin==.009 else 'Measured later150mm tube upper-rim toppling crosses15.124mm/tick;17mm table+0.8mm container leaves2.676mm margin.')+' Bounded native120 fixture, not a universal default.','qualified':False}

def build(source,out,margin=.009):
    from pxr import Usd,Sdf
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);s=Usd.Stage.CreateInMemory();s.GetRootLayer().subLayerPaths=[str(source)];r=author(s,'/World/_scene',margin);layer=s.GetRootLayer();layer.subLayerPaths=[];layer.Export(str(out/'runtime_delta.usda'));p=out/'table_margin_no_ccd_delta.usda';dest=Sdf.Layer.CreateNew(str(p));Sdf.CopySpec(layer,'/World/_scene',dest,'/World');dest.Save();entry=Usd.Stage.CreateNew(str(out/'scene.usda'));entry.GetRootLayer().subLayerPaths=[str(out/'runtime_delta.usda'),str(source)];entry.GetRootLayer().Save();r.update(source=str(source),delta_sha256=hashlib.sha256(p.read_bytes()).hexdigest());(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--margin',type=float,default=.009);a=p.parse_args();print(json.dumps(build(a.source,a.out,a.margin),indent=2))
