"""Use the existing open tube proxy for both PBD and rigid contacts."""
from pathlib import Path

def author(stage,root):
    from pxr import Usd,UsdPhysics
    tube=root+'/obj_sample_tube';fine=stage.GetPrimAtPath(tube+'/WaterbathCollision');proxy=stage.GetPrimAtPath(tube+'/RigidWallProxy')
    if not fine or not fine.IsActive() or not proxy:raise ValueError('Expected active fine wall and tube-v2 proxy')
    old=[p for p in Usd.PrimRange(fine) if p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get()]
    new=[p.GetPath() for p in Usd.PrimRange(proxy) if p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get()]
    if len(old)!=3745 or len(new)!=264:raise ValueError('This candidate requires exact 3745/264 source shape sets')
    changes={}
    for label in ['Sample','Bath']:
        p=stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System');api=UsdPhysics.FilteredPairsAPI(p);before=api.GetFilteredPairsRel().GetTargets()
        if not set(new).issubset(before):raise ValueError('Missing existing proxy particle filters')
        after=[v for v in before if v not in set(new)];api.CreateFilteredPairsRel().SetTargets(after);changes[label]={'removed_proxy_filters':len(before)-len(after),'remaining_targets':[str(v) for v in after]}
    # Inactive composition removes the subtree from the physics parser, not only
    # its rigid pair flags; source specs remain intact in the weaker layer.
    fine.SetActive(False)
    return {'retired_tube_fine_shapes':len(old),'shared_tube_convex_shapes':len(new),'particle_filters':changes,'bath_unchanged':True,'tube_mass_COM_inertia_visuals_unchanged':True,'particle_values_and_parameters_unchanged':True,'qualified':False}


def snapshot(stage,root):
    import hashlib
    from pxr import Usd
    result={}
    for suffix in ['/obj_sample_tube','/obj_beaker','/WaterbathFluid']:
        for p in Usd.PrimRange(stage.GetPrimAtPath(root+suffix)):
            path=str(p.GetPath())
            if path.startswith(root+'/obj_sample_tube/WaterbathCollision'):continue
            for a in p.GetAttributes():result[path+'::'+a.GetName()]=hashlib.sha256(str(a.Get()).encode()).hexdigest()
    return result


def build(source,out):
    import json,hashlib
    from pxr import Usd,Sdf
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);s=Usd.Stage.CreateInMemory();s.GetRootLayer().subLayerPaths=[str(source)];root='/World';before=snapshot(s,root)
    delta=s.GetRootLayer();change=author(s,root);after=snapshot(s,root)
    if before!=after:raise ValueError('Unexpected remaining geometry/mass/particle attribute change')
    delta.subLayerPaths=[];delta.Export(str(out/'shared_tube_delta.usda'));entry=Usd.Stage.CreateNew(str(out/'scene.usda'));entry.GetRootLayer().subLayerPaths=[str(out/'shared_tube_delta.usda'),str(source)];entry.SetDefaultPrim(entry.GetPrimAtPath('/World'));entry.GetRootLayer().Save()
    import shutil
    for name in ['probe.usda','manifest.json']:shutil.copy2(source.parent/name,out/name)
    receipt={'status':'STRUCTURAL_ONLY_COLD_LIFT_PENDING','source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'delta':str(out/'shared_tube_delta.usda'),'delta_sha256':hashlib.sha256((out/'shared_tube_delta.usda').read_bytes()).hexdigest(),'change':change,'compared_unchanged_attributes':len(before),'geometry_bounds_reference':'rigid_proxy_v2/profile_approximation_audit.json','inner_cavity_overfill_bound_m':.0001362966948437272,'straight_wall_inner_chord_bound_m':.00006844110900951694,'contact_offset_m':.0008,'rest_offset_m':0.,'note':'Existing proxy geometry/offsets remain unchanged; active particle boundary changes from fine walls to the same rigid proxy. Native per-step containment required.'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.out),indent=2))
