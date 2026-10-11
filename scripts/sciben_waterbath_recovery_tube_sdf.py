"""Source glass SDF for rigid contacts; unchanged473 shapes exclusively support PBD."""
import argparse,hashlib,json,shutil
from pathlib import Path


def sdf_distances(extents,ratio=.01,resolution=512):
    import numpy as np
    extents=np.asarray(extents,float)
    if np.any(extents<=0) or ratio<=0:raise ValueError('Positive geometry and dimensionless ratio required')
    return {'AABB_diagonal_m':float(np.linalg.norm(extents)),'uniform_grid_spacing_m':float(extents.max()/resolution),'margin_ratio':ratio,'narrow_band_ratio':ratio,'margin_world_m':float(np.linalg.norm(extents)*ratio),'narrow_band_world_m':float(np.linalg.norm(extents)*ratio),'unit_basis':'Installed Isaac4.1 generatedSchema:fractions of mesh AABB diagonal; .01 defaults for both, not metre units.'}


def author(stage):
    from pxr import Usd,UsdPhysics,UsdGeom
    import numpy as np
    root='/World';tube=root+'/obj_sample_tube';glass=tube+'/Visual/GlassShell';g=stage.GetPrimAtPath(glass);assert g.GetAttribute('physics:approximation').Get()=='sdf';assert g.GetAttribute('physxSDFMeshCollision:sdfResolution').Get()==512;assert g.GetAttribute('physxSDFMeshCollision:sdfSubgridResolution').Get()==6
    cache=UsdGeom.XformCache();m=cache.GetLocalToWorldTransform(g)*cache.GetLocalToWorldTransform(stage.GetPrimAtPath(tube)).GetInverse();v=np.asarray([m.Transform(x) for x in g.GetAttribute('points').Get()]);audit=sdf_distances(np.ptp(v,axis=0));g.GetAttribute('physics:collisionEnabled').Set(True)
    for key in ['sdfMargin','sdfNarrowBandThickness']:g.GetAttribute('physxSDFMeshCollision:'+key).Set(.01)
    stage.GetPrimAtPath(tube+'/RigidSolidBottom').SetActive(False)
    for p in stage.GetPrimAtPath(tube+'/RigidWallProxy').GetChildren():
        if p.GetName().startswith('Bottom_'):p.SetActive(False)
    supplement=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(root+'/Bad09FluidOnlyGroups/Supplement'));rigid=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(root+'/Bad09FluidOnlyGroups/RigidScene'));wall=tube+'/RigidWallProxy';includes=list(supplement.GetCollidersCollectionAPI().GetIncludesRel().GetTargets());excludes=list(rigid.GetCollidersCollectionAPI().GetExcludesRel().GetTargets());supplement.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets(list(dict.fromkeys(includes+[wall])));rigid.GetCollidersCollectionAPI().CreateExcludesRel().SetTargets(list(dict.fromkeys(excludes+[wall])));filters={}
    for label in ['Sample','Bath']:
        api=UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System'));before=list(map(str,api.GetFilteredPairsRel().GetTargets()));managed=[p for p in before if p.startswith(tube+'/RigidWallProxy/Bottom_') or p.startswith(tube+'/RigidSolidBottom/')];assert len(managed)==145 and len(before)==145;remaining=[p for p in before if p not in managed];after=remaining+[glass];api.CreateFilteredPairsRel().SetTargets(after);filters[label]={'before':len(before),'after':len(after),'targets':after,'nonmanaged_before':remaining,'nonmanaged_after':remaining}
    sq=supplement.GetCollidersCollectionAPI().ComputeMembershipQuery();rq=rigid.GetCollidersCollectionAPI().ComputeMembershipQuery();enabled=[p for p in Usd.PrimRange(stage.GetPrimAtPath(tube)) if p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False];rigid_paths=[str(p.GetPath()) for p in enabled if rq.IsPathIncluded(p.GetPath())];pbd_paths=[str(p.GetPath()) for p in enabled if sq.IsPathIncluded(p.GetPath())];assert rigid_paths==[glass] and len(pbd_paths)==473 and len(enabled)==474;assert all('/RigidWallProxy/Wall_' in p or '/PBDBottomProxy/' in p for p in pbd_paths);assert set(map(str,supplement.GetFilteredGroupsRel().GetTargets()))=={str(supplement.GetPath()),str(rigid.GetPath())};assert supplement.GetPath() in rigid.GetFilteredGroupsRel().GetTargets();audit.update(rigid_tube_shapes=rigid_paths,PBD_only_shapes=len(pbd_paths),enabled_tube_colliders=len(enabled),particle_filters=filters,PBD_only_excluded_from_rigid_and_self=True,original_full_fine_inactive=not stage.GetPrimAtPath(tube+'/WaterbathCollision').IsActive() if stage.GetPrimAtPath(tube+'/WaterbathCollision') else True,rigid_sdf_excluded_from_both_PBD=True,closed_source_geometry_unchanged=True)
    return audit


def build(source,out):
    from pxr import Usd
    from sciben_waterbath_recovery_bath import invariant_snapshot
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);s=Usd.Stage.CreateInMemory();s.GetRootLayer().subLayerPaths=[str(source)];before=invariant_snapshot(s,'/World');audit=author(s);after=invariant_snapshot(s,'/World');glass='/World/obj_sample_tube/Visual/GlassShell';allowed={glass+'::'+k for k in ['physics:collisionEnabled','physxSDFMeshCollision:sdfMargin','physxSDFMeshCollision:sdfNarrowBandThickness']}
    def keep(k):return not k.startswith('/World/obj_sample_tube/RigidSolidBottom') and '/RigidWallProxy/Bottom_' not in k and k not in allowed
    assert {k:v for k,v in before.items() if keep(k)}=={k:v for k,v in after.items() if keep(k)};layer=s.GetRootLayer();layer.subLayerPaths=[];delta=out/'tube_sdf_rigid_delta.usda';layer.Export(str(delta));entry=Usd.Stage.CreateNew(str(out/'scene.usda'));entry.GetRootLayer().subLayerPaths=[str(delta),str(source)];entry.SetDefaultPrim(entry.GetPrimAtPath('/World'));entry.GetRootLayer().Save();shutil.copy2(source.parent/'probe.usda',out/'probe.usda');m=json.loads((source.parent/'manifest.json').read_text());m.update(status='source_sdf_rigid_candidate_pending',enabled_colliders={'obj_sample_tube':474,'obj_beaker':260},PBD_rigid_bottom_filter_targets=0,PBD_filtered_targets=['Visual/GlassShell'],physical_delta_receipt=str(out/'receipt.json'));(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');audit.update(status='STATIC_PASS_NO_DYNAMIC_QUALIFICATION',source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),delta=str(delta),delta_sha256=hashlib.sha256(delta.read_bytes()).hexdigest(),generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),unchanged_attribute_count=sum(keep(k) for k in before),mass_COM_I_visual_mesh_particle_state_offsets_except_two_dimensionless_SDF_values_unchanged=True,composition='Strongest above existing scene128/PBD128/solidcap/table17/source stack; old rigid bottom pieces inactive, Wall120+PBDBottom353 isolated to PBD. Source GlassShell sole rigid contact representation, with corrected schema-default SDF band/margin.',qualified=False);(out/'receipt.json').write_text(json.dumps(audit,indent=2)+'\n');return audit
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.out),indent=2))
