"""Replace the small PBD center Floor with the existing real-glass solid cap."""
import argparse,hashlib,json,shutil
from pathlib import Path


def replace_filter_targets(targets,cap,floor):
    if len(targets)!=145 or cap not in targets or floor in targets:raise ValueError('Expected145 rigid-only bottom targets including cap, excluding PBD Floor')
    result=[p for p in targets if p!=cap]
    assert len(result)==144 and set(result)==set(targets)-{cap}
    return result


def author(stage,root='/World'):
    from pxr import Usd,UsdPhysics,UsdGeom
    import numpy as np
    tube=root+'/obj_sample_tube';cap=tube+'/RigidSolidBottom/SolidCap';floor=tube+'/PBDBottomProxy/Floor';cp=stage.GetPrimAtPath(cap);fp=stage.GetPrimAtPath(floor)
    if not cp or not fp or not fp.IsActive():raise ValueError('Expected existing active cap and center Floor')
    cache=UsdGeom.XformCache();inverse=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(tube)).GetInverse()
    def vertices(p):
        m=cache.GetLocalToWorldTransform(p)*inverse
        return np.asarray([m.Transform(v) for v in p.GetAttribute('points').Get()])
    cv=vertices(cp);fv=vertices(fp);first=vertices(stage.GetPrimAtPath(tube+'/PBDBottomProxy/S000_00'));assert cv[:,2].max()<.001 and fv[:,2].max()>.00109
    filters={}
    for label in ['Sample','Bath']:
        api=UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System'));before=list(map(str,api.GetFilteredPairsRel().GetTargets()));after=replace_filter_targets(before,cap,floor);api.CreateFilteredPairsRel().SetTargets(after);filters[label]={'before':len(before),'after':len(after),'removed_only':cap,'unchanged_remaining_target_set':set(after)==set(before)-{cap}}
    fp.SetActive(False);assert not stage.GetPrimAtPath(floor).IsActive();assert cp.IsActive() and UsdPhysics.CollisionAPI(cp).GetCollisionEnabledAttr().Get();count=sum(p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False for p in Usd.PrimRange(stage.GetPrimAtPath(tube)));assert count==617
    return {'enabled_tube_colliders':count,'dedicated_PBD_bottom_ring_shapes':352,'shared_cap_shapes':1,'shared_straight_lip_shapes':120,'particle_filters':filters,'small_PBD_Floor_inactive':True,'no_double_active_center_Floor':True,'cap_vertices':len(cv),'cap_z_bounds_m':[float(cv[:,2].min()),float(cv[:,2].max())],'old_Floor_z_bounds_m':[float(fv[:,2].min()),float(fv[:,2].max())],'lowest_fine_ring_z_m':float(first[:,2].min()),'cap_to_fine_ring_axial_gap_m':float(first[:,2].min()-cv[:,2].max()),'cap_geometry_offsets_material_unchanged':True,'source_inner_cavity_lowest_z_m':.001,'cap_below_actual_cavity':bool(cv[:,2].max()<.001),'qualified':False,'scope':'Only original tiny PBD Floor inactive and existing real-glass cap removed from two PBD filter lists. No new or enlarged geometry.100.1um axial proxy seam must be tested, not claimed sealed by static inspection.'}


def build(source,out):
    from pxr import Usd,Sdf
    from sciben_waterbath_recovery_bath import invariant_snapshot
    source=Path(source).resolve();assert source.is_file();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);s=Usd.Stage.CreateInMemory();s.GetRootLayer().subLayerPaths=[str(source)];before=invariant_snapshot(s,'/World');audit=author(s);after=invariant_snapshot(s,'/World');assert {k:v for k,v in before.items() if not k.startswith('/World/obj_sample_tube/PBDBottomProxy/Floor::')}==after;layer=s.GetRootLayer();layer.subLayerPaths=[];delta=out/'shared_cap_delta.usda';layer.Export(str(delta));entry=Usd.Stage.CreateNew(str(out/'scene.usda'));entry.GetRootLayer().subLayerPaths=[str(delta),str(source)];entry.SetDefaultPrim(entry.GetPrimAtPath('/World'));entry.GetRootLayer().Save()
    shutil.copy2(source.parent/'probe.usda',out/'probe.usda');manifest=json.loads((source.parent/'manifest.json').read_text());manifest.update(status='shared_cap_candidate_pending',enabled_colliders={'obj_sample_tube':617,'obj_beaker':260},PBD_rigid_bottom_filter_targets=144,physical_delta_receipt=str(out/'receipt.json'));(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    audit.update(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),delta=str(delta),delta_sha256=hashlib.sha256(delta.read_bytes()).hexdigest(),generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),unchanged_attributes=len(after),mass_COM_I_visual_particle_attributes_unchanged=True,composition='shared_cap_delta strongest over solidcap then original table17 physical stack; authored /World mapped to /World/_scene in native runtime')
    (out/'receipt.json').write_text(json.dumps(audit,indent=2)+'\n');return audit
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.out),indent=2))
