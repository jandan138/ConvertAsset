"""Exact solid-glass bottom repartition below the lowest cavity point."""
import argparse,json,hashlib
from pathlib import Path

def clip_z(vertices,cut,below):
    import numpy as np
    from scipy.spatial import ConvexHull
    v=np.asarray(vertices);h=ConvexHull(v);edges={tuple(sorted((int(a),int(b)))) for f in h.simplices for a,b in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]};sign=(v[:,2]-cut)*(1 if below else -1);points=[p for p,d in zip(v,sign) if d<=1e-13]
    for a,b in edges:
        if sign[a]*sign[b]<0:points.append(v[a]+(cut-v[a,2])/(v[b,2]-v[a,2])*(v[b]-v[a]))
    points=np.unique(np.asarray(points),axis=0)
    if len(points)<4:return None
    h=ConvexHull(points);return points[h.vertices]

def repartition(cells):
    import numpy as np
    from scipy.spatial import ConvexHull
    if len(cells)!=144:raise ValueError('Expected144 original v2 rigid bottom cells')
    inner=np.concatenate([v[np.linalg.norm(v-[0,0,.009],axis=1)<.0085] for v in cells.values()]);inner_z=float(inner[:,2].min());cut=inner_z-1e-7;lower=[];upper={};original_volume=0
    for name,v in cells.items():
        if v[:,2].min()>=cut:continue
        lo=clip_z(v,cut,True);hi=clip_z(v,cut,False)
        if lo is None or hi is None:raise ValueError('Expected both lower solid and upper remainder')
        lower.append(lo);upper[name]=hi;original_volume+=ConvexHull(v).volume
    if len(upper)!=48:raise ValueError('Unexpected intersected polar bands')
    all_points=np.concatenate(lower);weld=np.unique(np.round(all_points,9),axis=0);h=ConvexHull(weld);cap=weld[h.vertices];h=ConvexHull(cap)
    if len(cap)>64 or cap[:,2].max()>=inner_z:raise ValueError('GPU vertex or cavity boundary violation')
    old_lower_out=float(np.max(all_points@h.equations[:,:3].T+h.equations[:,3]));boundary=[cap]
    for f in h.simplices:
        xyz=cap[f];boundary.extend([xyz.mean(0)[None,:],((xyz+np.roll(xyz,1,axis=0))/2)])
    sample=np.concatenate(boundary);distance=[]
    for v in lower:
        hull=ConvexHull(v);distance.append(np.max(sample@hull.equations[:,:3].T+hull.equations[:,3],axis=1))
    new_out=float(np.max(np.min(np.asarray(distance),axis=0)));new_volume=h.volume+sum(ConvexHull(v).volume for v in upper.values());relative=new_volume/original_volume-1
    if abs(relative)>1e-6 or max(old_lower_out,new_out)>2e-9:raise ValueError('Source union preservation failed')
    audit={'cut_z_m':cut,'minimum_inner_z_m':inner_z,'inner_cavity_clearance_guard_m':inner_z-float(cap[:,2].max()),'changed_source_shapes':len(upper),'untouched_shapes':144-len(upper),'cap_vertices':len(cap),'max_upper_vertices':max(len(v) for v in upper.values()),'original_changed_volume_m3':original_volume,'repartition_volume_m3':new_volume,'relative_volume_delta':relative,'old_lower_vertices_outside_new_cap_m':old_lower_out,'new_cap_boundary_outside_old_union_m':new_out,'boundary_sampling':'All hull vertices, edge midpoints and triangle centroids; cap convexity additionally tested by union volume.1nm weld only.','cavity_not_filled':True}
    return cap,upper,audit

def author_mesh(stage,path,xyz,source):
    import numpy as np
    from scipy.spatial import ConvexHull
    from pxr import UsdGeom,UsdShade,Gf,Sdf
    h=ConvexHull(xyz);xyz=xyz[h.vertices];h=ConvexHull(xyz)
    if len(xyz)>64:raise ValueError('Convex vertex count above64')
    center=(xyz.min(0)+xyz.max(0))/2;scale=np.maximum(xyz.max(0)-xyz.min(0),1e-9);faces=[]
    for face,equation in zip(h.simplices,h.equations):
        face=list(map(int,face))
        if np.dot(np.cross(xyz[face[1]]-xyz[face[0]],xyz[face[2]]-xyz[face[0]]),equation[:3])<0:face[1],face[2]=face[2],face[1]
        faces.append(face)
    mesh=UsdGeom.Mesh.Define(stage,path);mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in (xyz-center)/scale]);mesh.CreateFaceVertexCountsAttr([3]*len(faces));mesh.CreateFaceVertexIndicesAttr([i for f in faces for i in f]);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible');mesh.AddTranslateOp().Set(Gf.Vec3d(*center));mesh.AddScaleOp().Set(Gf.Vec3f(*scale));p=mesh.GetPrim();p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']));p.CreateAttribute('physics:collisionEnabled',Sdf.ValueTypeNames.Bool).Set(True);p.CreateAttribute('physics:approximation',Sdf.ValueTypeNames.Token).Set('convexHull')
    for key in ['physxCollision:contactOffset','physxCollision:restOffset','physxConvexHullCollision:minThickness']:p.CreateAttribute(key,Sdf.ValueTypeNames.Float).Set(source.GetAttribute(key).Get())
    mat=UsdShade.MaterialBindingAPI(source).ComputeBoundMaterial('physics')[0]
    if mat:UsdShade.MaterialBindingAPI.Apply(p).Bind(mat,materialPurpose='physics')
    return p.GetPath()

def author(stage,root):
    import numpy as np
    from pxr import UsdGeom,UsdPhysics,Gf
    tube=root+'/obj_sample_tube';cache=UsdGeom.XformCache();inv=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(tube)).GetInverse();prims={};cells={}
    for p in stage.GetPrimAtPath(tube+'/RigidWallProxy').GetChildren():
        if p.GetName().startswith('Bottom_'):
            m=cache.GetLocalToWorldTransform(p)*inv;cells[p.GetName()]=np.asarray([m.Transform(Gf.Vec3d(*v)) for v in p.GetAttribute('points').Get()]);prims[p.GetName()]=p
    cap,upper,audit=repartition(cells);parent=tube+'/RigidSolidBottom';new=[author_mesh(stage,parent+'/SolidCap',cap,prims[next(iter(upper))])]
    for name,v in upper.items():new.append(author_mesh(stage,parent+'/Upper_'+name,v,prims[name]))
    old={prims[name].GetPath() for name in upper};filters={}
    for label in ['Sample','Bath']:
        api=UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System'));targets=api.GetFilteredPairsRel().GetTargets()
        if len(targets)!=144 or not old.issubset(targets):raise ValueError('Expected original144 filtered rigid bottom targets')
        after=[p for p in targets if p not in old]+new;api.CreateFilteredPairsRel().SetTargets(after);filters[label]={'before':len(targets),'retained':len(targets)-len(old),'added':len(new),'after':len(after)}
    for name in upper:prims[name].SetActive(False)
    supp=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(root+'/Bad09FluidOnlyGroups/Supplement')).GetCollidersCollectionAPI().ComputeMembershipQuery();rigid=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(root+'/Bad09FluidOnlyGroups/RigidScene')).GetCollidersCollectionAPI().ComputeMembershipQuery();assert all(rigid.IsPathIncluded(p) and not supp.IsPathIncluded(p) for p in new)
    audit.update(new_rigid_shapes=len(new),retired_rigid_shapes=len(old),PBD_filter_targets=filters,PBD_boundaries_unchanged=True,new_cap_and_remainders_in_rigid_scene=True,source_mass_COM_inertia_visual_and_particle_fields_unchanged=True,qualified=False)
    return audit

def build(source,out):
    from pxr import Usd,Sdf,UsdPhysics
    from sciben_waterbath_recovery_bath import invariant_snapshot
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);s=Usd.Stage.CreateInMemory();s.GetRootLayer().subLayerPaths=[str(source)];root='/World/_scene';before=invariant_snapshot(s,root);audit=author(s,root);after=invariant_snapshot(s,root)
    def keep(k):return '/RigidWallProxy/Bottom_' not in k and '/RigidSolidBottom/' not in k
    assert {k:v for k,v in before.items() if keep(k)}=={k:v for k,v in after.items() if keep(k)}
    layer=s.GetRootLayer();layer.subLayerPaths=[];layer.Export(str(out/'runtime_delta.usda'));d=out/'solid_cap_delta.usda';portable=Sdf.Layer.CreateNew(str(d));Sdf.CopySpec(layer,root,portable,'/World');portable.Save();entry=Usd.Stage.CreateNew(str(out/'scene.usda'));entry.GetRootLayer().subLayerPaths=[str(out/'runtime_delta.usda'),str(source)];entry.GetRootLayer().Save();counts={obj:sum(p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False for p in Usd.PrimRange(entry.GetPrimAtPath(root+'/'+obj))) for obj in ['obj_sample_tube','obj_beaker']};assert counts=={'obj_sample_tube':618,'obj_beaker':260};audit.update(source=str(source),delta_sha256=hashlib.sha256(d.read_bytes()).hexdigest(),enabled_colliders=counts,composition='solid_cap_delta strongest over unchanged table17 physical stack, /World mapped at /World/_scene')
    (out/'receipt.json').write_text(json.dumps(audit,indent=2)+'\n');return audit

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.out),indent=2))
