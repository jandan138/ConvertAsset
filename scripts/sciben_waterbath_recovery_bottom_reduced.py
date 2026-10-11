"""Single-variable 32->16 angular-sector PBD bottom diagnostic."""
import argparse,json,hashlib,math,shutil
from pathlib import Path

def author(stage,root,profile):
    from pxr import Usd,UsdPhysics
    from sciben_waterbath_geometry import author_profile_colliders
    old=stage.GetPrimAtPath(root+'/obj_sample_tube/PBDBottomProxy')
    count=sum(p.HasAPI(UsdPhysics.CollisionAPI) for p in Usd.PrimRange(old))
    if count!=353:raise ValueError('Expected353 PBD-only bottom cells')
    before={label:list(UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets()) for label in ['Sample','Bath']}
    old.SetActive(False);parent=root+'/obj_sample_tube/PBDBottomReduced';n=author_profile_colliders(stage,parent,profile,.002,sectors=16)
    groups=root+'/Bad09FluidOnlyGroups';supp=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(groups+'/Supplement'));rigid=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(groups+'/RigidScene'))
    rel=supp.GetCollidersCollectionAPI().GetIncludesRel();rel.SetTargets(list(dict.fromkeys(rel.GetTargets()+[parent])))
    rel=rigid.GetCollidersCollectionAPI().GetExcludesRel();rel.SetTargets(list(dict.fromkeys(rel.GetTargets()+[parent])))
    after={label:list(UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets()) for label in ['Sample','Bath']};assert before==after
    return {'old_shapes':count,'new_shapes':n,'angular_sectors_before_after':[32,16],'new_angular_chord_bound_m':max(p[1] for p in profile)*(1-math.cos(math.pi/16)),'PBD_profile_thickness_offsets_unchanged':True,'particle_filtered_targets_unchanged':True,'rigid_proxy_unchanged':True,'qualified':False}

def build(source,out):
    from pxr import Usd,UsdPhysics
    from sciben_waterbath_recovery_bottom_proxy import bottom_profile
    from sciben_waterbath_recovery_shared_tube import snapshot
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source.parent/'manifest.json').read_text());profile=bottom_profile(manifest['liquids']['Sample']['cavity_profile_m'])[1]
    stage=Usd.Stage.CreateInMemory();stage.GetRootLayer().subLayerPaths=[str(source)];before=snapshot(stage,'/World');result=author(stage,'/World',profile);after=snapshot(stage,'/World')
    def keep(k):return '/PBDBottomProxy/' not in k and '/PBDBottomReduced/' not in k
    assert {k:v for k,v in before.items() if keep(k)}=={k:v for k,v in after.items() if keep(k)}
    layer=stage.GetRootLayer();layer.subLayerPaths=[];delta=out/'bottom_reduced_delta.usda';layer.Export(str(delta));entry=Usd.Stage.CreateNew(str(out/'scene.usda'));entry.GetRootLayer().subLayerPaths=[str(delta),str(source)];entry.SetDefaultPrim(entry.GetPrimAtPath('/World'));entry.GetRootLayer().Save()
    for name in ['manifest.json','probe.usda']:shutil.copyfile(source.parent/name,out/name)
    result.update(source=str(source),delta_sha256=hashlib.sha256(delta.read_bytes()).hexdigest(),mass_COM_inertia_visuals_particles_unchanged=True,enabled_tube_colliders=sum(p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False for p in Usd.PrimRange(entry.GetPrimAtPath('/World/obj_sample_tube'))))
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.out),indent=2))
