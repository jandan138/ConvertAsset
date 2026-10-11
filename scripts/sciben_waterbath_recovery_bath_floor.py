"""Merge adjacent coplanar beaker floor wedges without shifting their boundary."""
import argparse,json,hashlib
from pathlib import Path

def merge_floor_cells(cells):
    import numpy as np
    if len(cells)!=32:raise ValueError('Expected32 floor cells')
    return [np.unique(np.concatenate(cells[i:i+4]),axis=0) for i in range(0,32,4)]

def author(stage,root):
    import numpy as np
    from scipy.spatial import ConvexHull
    from pxr import UsdGeom,UsdPhysics,UsdShade,Gf,Sdf
    base=root+'/obj_beaker';old=[stage.GetPrimAtPath(base+'/RigidBathProxy/Floor_'+str(i).zfill(2)) for i in range(32)]
    if not all(p and p.IsActive() and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() for p in old):raise ValueError('Expected32 active source floor colliders')
    cache=UsdGeom.XformCache();inv=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(base)).GetInverse();cells=[]
    for p in old:
        m=cache.GetLocalToWorldTransform(p)*inv;cells.append(np.asarray([m.Transform(Gf.Vec3d(*v)) for v in p.GetAttribute('points').Get()]))
    merged=merge_floor_cells(cells);oldvol=sum(ConvexHull(v).volume for v in cells);newvol=sum(ConvexHull(v).volume for v in merged)
    if abs(newvol/oldvol-1)>1e-6:raise ValueError('Merged volume differs beyond source float precision')
    source_points=np.concatenate(cells);bounds=np.array([source_points.min(0),source_points.max(0)])
    material=UsdShade.MaterialBindingAPI(old[0]).ComputeBoundMaterial('physics')[0];paths=[];cooked_vertex_counts=[];roundtrip=[]
    offsets={key:old[0].GetAttribute(key).Get() for key in ['physxCollision:contactOffset','physxCollision:restOffset','physxConvexHullCollision:minThickness']}
    for i,xyz in enumerate(merged):
        hull=ConvexHull(xyz);xyz=xyz[hull.vertices];hull=ConvexHull(xyz);cooked_vertex_counts.append(len(xyz))
        if len(xyz)>64:raise ValueError('Exceeds conservative64-vertex GPU convex limit')
        center=(xyz.min(0)+xyz.max(0))/2;scale=np.maximum(xyz.max(0)-xyz.min(0),1e-9);faces=[]
        for face,equation in zip(hull.simplices,hull.equations):
            face=list(map(int,face))
            if np.dot(np.cross(xyz[face[1]]-xyz[face[0]],xyz[face[2]]-xyz[face[0]]),equation[:3])<0:face[1],face[2]=face[2],face[1]
            faces.append(face)
        mesh=UsdGeom.Mesh.Define(stage,base+'/RigidBathFloorMerged/Floor_'+str(i).zfill(2));mesh.CreatePointsAttr([Gf.Vec3f(*v) for v in (xyz-center)/scale]);mesh.CreateFaceVertexCountsAttr([3]*len(faces));mesh.CreateFaceVertexIndicesAttr([j for f in faces for j in f]);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible');mesh.AddTranslateOp().Set(Gf.Vec3d(*center));mesh.AddScaleOp().Set(Gf.Vec3f(*scale));p=mesh.GetPrim();p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
        for key,typ,value in [('physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True),('physics:approximation',Sdf.ValueTypeNames.Token,'convexHull')]+[(k,Sdf.ValueTypeNames.Float,v) for k,v in offsets.items()]:p.CreateAttribute(key,typ).Set(value)
        if material:UsdShade.MaterialBindingAPI.Apply(p).Bind(material,materialPurpose='physics')
        paths.append(p.GetPath());stored=np.asarray(mesh.GetPointsAttr().Get())*np.asarray(Gf.Vec3f(*scale))+center;roundtrip.append(float(np.max(np.linalg.norm(stored-xyz,axis=1))))
    oldpaths={p.GetPath() for p in old};filters={}
    for label in ['Sample','Bath']:
        api=UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System'));before=api.GetFilteredPairsRel().GetTargets()
        if len(before)!=240 or not oldpaths.issubset(before):raise ValueError('Expected unchanged240 source particle filters')
        after=[p for p in before if p not in oldpaths]+paths;api.CreateFilteredPairsRel().SetTargets(after);assert len(after)==216;filters[label]={'before':len(before),'after':len(after),'retained_non_floor_targets':len(before)-len(oldpaths),'new_floor_targets':len(paths)}
    for p in old:p.SetActive(False)
    return {'floor_shapes_before_after':[32,8],'source_union_volume_m3':oldvol,'merged_union_volume_m3':newvol,'relative_volume_delta':newvol/oldvol-1,'source_bounds_local_m':bounds.tolist(),'floor_z_boundary_unchanged':True,'boundary_proof':'Each45degree cell is union of four adjacent11.25degree source disk sectors; source arc vertices are reused. Convex union has same128-angle polygon boundary up to source float roundoff.','max_authored_roundtrip_vertex_error_m':max(roundtrip),'convex_hull_vertices':cooked_vertex_counts,'offsets_unchanged':offsets,'filters':filters,'qualified':False}

def build(source,out):
    from pxr import Usd,Sdf,UsdPhysics
    from sciben_waterbath_recovery_bath import invariant_snapshot
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);stage=Usd.Stage.CreateInMemory();stage.GetRootLayer().subLayerPaths=[str(source)];root='/World/_scene';before=invariant_snapshot(stage,root);r=author(stage,root);after=invariant_snapshot(stage,root)
    def keep(k):return '/RigidBathProxy/Floor_' not in k and '/RigidBathFloorMerged/' not in k
    assert {k:v for k,v in before.items() if keep(k)}=={k:v for k,v in after.items() if keep(k)}
    layer=stage.GetRootLayer();layer.subLayerPaths=[];layer.Export(str(out/'runtime_delta.usda'));p=out/'bath_floor_delta.usda';package=Sdf.Layer.CreateNew(str(p));Sdf.CopySpec(layer,root,package,'/World');package.Save();wrapper=Usd.Stage.CreateNew(str(out/'scene.usda'));wrapper.GetRootLayer().subLayerPaths=[str(out/'runtime_delta.usda'),str(source)];wrapper.GetRootLayer().Save();r.update(source=str(source),delta_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mass_COM_inertia_visible_particle_attributes_unchanged=True,enabled_beaker_colliders=sum(p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False for p in Usd.PrimRange(wrapper.GetPrimAtPath(root+'/obj_beaker'))));assert r['enabled_beaker_colliders']==330
    (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build(a.source,a.out),indent=2))
