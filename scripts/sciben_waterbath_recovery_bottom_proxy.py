"""Localize dedicated PBD boundary geometry to the observed tube-bottom leak."""
from pathlib import Path
import sys
if str(Path(__file__).resolve().parent) not in sys.path:sys.path.insert(0,str(Path(__file__).resolve().parent))


def bottom_profile(profile,tolerance=.00005):
    import numpy as np
    from sciben_waterbath_geometry import collision_profile
    old=[list(map(float,p)) for p in collision_profile(profile) if p[0]<=.009]
    if not old or abs(old[-1][0]-.009)>1e-9:raise ValueError('Expected source hemisphere/cylinder join at9mm')
    def reduce(p):
        if len(p)<3:return p
        xyz=np.asarray(p);error=np.abs(np.interp(xyz[:,0],[p[0][0],p[-1][0]],[p[0][1],p[-1][1]])-xyz[:,1]);i=int(np.argmax(error))
        if error[i]<=tolerance:return [p[0],p[-1]]
        return reduce(p[:i+1])[:-1]+reduce(p[i:])
    return old,reduce(old)


def author(stage,root,profile):
    from pxr import Usd,UsdPhysics
    from sciben_waterbath_recovery_shared_tube import author as shared
    from sciben_waterbath_geometry import author_profile_colliders
    import numpy as np
    result=shared(stage,root);old,reduced=bottom_profile(profile);parent=root+'/obj_sample_tube/PBDBottomProxy'
    count=author_profile_colliders(stage,parent,reduced,.002,sectors=32)
    bottom=[p.GetPath() for p in Usd.PrimRange(stage.GetPrimAtPath(root+'/obj_sample_tube/RigidWallProxy')) if p.GetName().startswith('Bottom_') and p.HasAPI(UsdPhysics.CollisionAPI)]
    if len(bottom)!=144:raise ValueError('Expected144 existing rigid bottom cells')
    for label in ['Sample','Bath']:
        api=UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System'));targets=api.GetFilteredPairsRel().GetTargets();api.CreateFilteredPairsRel().SetTargets(list(dict.fromkeys(targets+bottom)))
    result['particle_filters']={label:{'effective_target_count':len(UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets()),'rigid_bottom_targets':144,'retained_non_tube_targets':result['particle_filters'][label]['remaining_targets'],'rigid_straight_lip_filtered':False} for label in ['Sample','Bath']}
    groups=root+'/Bad09FluidOnlyGroups';supp=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(groups+'/Supplement'));rigid=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(groups+'/RigidScene'))
    if not supp or not rigid:raise ValueError('Expected existing fluid-only groups')
    includes=supp.GetCollidersCollectionAPI().GetIncludesRel().GetTargets();supp.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets(list(dict.fromkeys(includes+[parent])))
    excludes=rigid.GetCollidersCollectionAPI().GetExcludesRel().GetTargets();rigid.GetCollidersCollectionAPI().CreateExcludesRel().SetTargets(list(dict.fromkeys(excludes+[parent])))
    a=np.asarray(old);b=np.asarray(reduced);error=float(np.abs(np.interp(a[:,0],b[:,0],b[:,1])-a[:,1]).max())
    result.update(bottom_PBD_shapes=count,tube_total_active_shapes=264+count,particle_excluded_bottom_shapes=144,particle_shared_straight_lip_shapes=120,bottom_profile=reduced,bottom_profile_error_vs_old_collision_m=error,bottom_angular_sectors=32,angular_overlap_rad=.001,PBD_bottom_radial_thickness_m=.002,PBD_wall_contact_rest_m=[.0014,.0005],PBD_floor_contact_rest_m=[.0016,.0006],original_full_fine_scope_inactive=True,scope='Shared straight/lip rigid proxy; separate filtered PBD bottom only')
    return result


def build(source,out):
    import json,hashlib,shutil
    from pxr import Usd,Sdf,UsdPhysics
    from sciben_waterbath_recovery_shared_tube import snapshot
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source.parent/'manifest.json').read_text());stage=Usd.Stage.CreateInMemory();stage.GetRootLayer().subLayerPaths=[str(source)];before=snapshot(stage,'/World')
    delta=stage.GetRootLayer();change=author(stage,'/World',manifest['liquids']['Sample']['cavity_profile_m']);after={k:v for k,v in snapshot(stage,'/World').items() if not k.startswith('/World/obj_sample_tube/PBDBottomProxy')};assert before==after
    # Prove group membership rather than merely authoring relationship names.
    supp=UsdPhysics.CollisionGroup(stage.GetPrimAtPath('/World/Bad09FluidOnlyGroups/Supplement'));rigid=UsdPhysics.CollisionGroup(stage.GetPrimAtPath('/World/Bad09FluidOnlyGroups/RigidScene'));sq=supp.GetCollidersCollectionAPI().ComputeMembershipQuery();rq=rigid.GetCollidersCollectionAPI().ComputeMembershipQuery()
    paths=[p.GetPath() for p in Usd.PrimRange(stage.GetPrimAtPath('/World/obj_sample_tube/PBDBottomProxy')) if p.HasAPI(UsdPhysics.CollisionAPI)];assert all(sq.IsPathIncluded(p) and not rq.IsPathIncluded(p) for p in paths)
    assert set(supp.GetFilteredGroupsRel().GetTargets())=={supp.GetPath(),rigid.GetPath()};assert supp.GetPath() in rigid.GetFilteredGroupsRel().GetTargets()
    filters={}
    for label in ['Sample','Bath']:
        targets=UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath('/World/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets();assert len(targets)==144 and all('/RigidWallProxy/Bottom_' in str(p) for p in targets);filters[label]={'count':len(targets),'all_only_rigid_bottom':True,'all_existing':all(bool(stage.GetPrimAtPath(p)) for p in targets)}
    delta.subLayerPaths=[];delta.Export(str(out/'bottom_hybrid_delta.usda'));entry=Usd.Stage.CreateNew(str(out/'scene.usda'));entry.GetRootLayer().subLayerPaths=[str(out/'bottom_hybrid_delta.usda'),str(source)];entry.SetDefaultPrim(entry.GetPrimAtPath('/World'));entry.GetRootLayer().Save()
    for name in ['manifest.json','probe.usda']:shutil.copy2(source.parent/name,out/name)
    receipt={'status':'STATIC_ONLY_COLD_LIFT_PENDING','source':str(source),'delta':str(out/'bottom_hybrid_delta.usda'),'delta_sha256':hashlib.sha256((out/'bottom_hybrid_delta.usda').read_bytes()).hexdigest(),'change':change,'unchanged_attributes_compared':len(before),'PBD_filters':filters,'new_PBD_bottom_excluded_from_rigid_and_self':True,'native_parsed_set_pending':True}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.out),indent=2))
