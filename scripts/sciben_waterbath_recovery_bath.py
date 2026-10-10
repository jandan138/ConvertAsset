#!/usr/bin/env python3
"""Producer-side open beaker rigid cells; no runtime/core/trajectory changes."""
import math
BODY='Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh'
RIM='Visual/Source/Rolled_Rim/Torus'
SPOUT='Visual/Source/Pour_Spout/Pour_Spout_Mesh'


def bath_cells(sectors=32):
    """Measured source profile in beaker coordinates, metres; open at the top.

    Original body has 128 angular samples, rim 128 x 16 samples. Each
    cell keeps the five source angular samples within its 11.25 degree span.
    Inner chord intrusion is bounded by 0.177 mm (36.69 mm radius).
    """
    import numpy as np
    if sectors!=32:raise ValueError('Only source-aligned 32-sector decomposition qualified structurally')
    cells=[]
    for i in range(sectors):
        angles=[2*math.pi*(4*i+k)/128 for k in range(5)]
        profile=[(.03727,0),(.03869,.11349),(.03669,.11349),(.03527,.003)]
        cells.append((f'Wall_{i:02d}',np.array([[r*math.cos(a),r*math.sin(a),z] for r,z in profile for a in angles])))
        cells.append((f'Floor_{i:02d}',np.array([[0,0,0],[0,0,.003]]+[[.03727*math.cos(a),.03727*math.sin(a),z] for z in [0,.003] for a in angles])))
        cells.append((f'Rim_{i:02d}',np.array([[(.0389675+.0022775*math.cos(t))*math.cos(a),(.0389675+.0022775*math.cos(t))*math.sin(a),.11349+.0016*math.sin(t)] for t in [2*math.pi*k/16 for k in range(16)] for a in [angles[0],angles[-1]]])))
    return cells


def author(stage,root):
    import numpy as np
    from scipy.spatial import ConvexHull
    from pxr import UsdGeom,UsdPhysics,UsdShade,Gf,Sdf
    base=root+'/obj_beaker';original=[stage.GetPrimAtPath(base+'/'+rel) for rel in [BODY,RIM]]
    for p in original:
        if not p or not p.HasAPI(UsdPhysics.CollisionAPI):raise ValueError('Missing source collider')
    paths=[]
    for name,xyz in bath_cells():
        material=UsdShade.MaterialBindingAPI(original[1 if name.startswith('Rim') else 0]).ComputeBoundMaterial('physics')[0]
        hull=ConvexHull(xyz);center=(xyz.min(0)+xyz.max(0))/2;scale=np.maximum(xyz.max(0)-xyz.min(0),1e-9);faces=[]
        for face,equation in zip(hull.simplices,hull.equations):
            face=list(map(int,face))
            if np.dot(np.cross(xyz[face[1]]-xyz[face[0]],xyz[face[2]]-xyz[face[0]]),equation[:3])<0:face[1],face[2]=face[2],face[1]
            faces.append(face)
        mesh=UsdGeom.Mesh.Define(stage,base+'/RigidBathProxy/'+name);mesh.CreatePointsAttr([Gf.Vec3f(*v) for v in (xyz-center)/scale]);mesh.CreateFaceVertexCountsAttr([3]*len(faces));mesh.CreateFaceVertexIndicesAttr([i for f in faces for i in f]);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible');mesh.AddTranslateOp().Set(Gf.Vec3d(*center));mesh.AddScaleOp().Set(Gf.Vec3f(*scale));p=mesh.GetPrim()
        p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
        for key,typ,value in [('physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True),('physics:approximation',Sdf.ValueTypeNames.Token,'convexHull'),('physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float,0.),('physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.0008),('physxCollision:restOffset',Sdf.ValueTypeNames.Float,0.)]:p.CreateAttribute(key,typ).Set(value)
        if material:UsdShade.MaterialBindingAPI.Apply(p).Bind(material,materialPurpose='physics')
        paths.append(p.GetPath())
    for p in original:UsdPhysics.CollisionAPI(p).CreateCollisionEnabledAttr(False)
    for label in ['Sample','Bath']:
        p=stage.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System')
        if not p:raise ValueError('Missing particle system')
        api=UsdPhysics.FilteredPairsAPI.Apply(p);existing=api.GetFilteredPairsRel().GetTargets();api.CreateFilteredPairsRel().SetTargets(list(dict.fromkeys(existing+paths)))
    return {'rigid_proxy_count':len(paths),'beaker_body_and_rim_SDF_replaced':True,'spout_unchanged':True,'mass_COM_inertia_and_visible_mesh_unchanged':True,'PBD_filtered_only_against_new_proxies':True,'qualified_asset':False}


def invariant_snapshot(stage,root):
    """Snapshot complete visible geometry, PBD and rigid mass state for audit."""
    import hashlib
    from pxr import Usd
    result={}
    for suffix in ['/obj_beaker','/obj_sample_tube','/WaterbathFluid']:
        for p in Usd.PrimRange(stage.GetPrimAtPath(root+suffix)):
            path=str(p.GetPath())
            if '/RigidBathProxy' in path:continue
            for a in p.GetAttributes():
                name=a.GetName()
                if name=='physics:collisionEnabled' and path in [root+'/obj_beaker/'+BODY,root+'/obj_beaker/'+RIM]:continue
                result[path+'::'+name]=hashlib.sha256(str(a.Get()).encode()).hexdigest()
    return result


def build_delta(source,out):
    import json
    from pathlib import Path
    import numpy as np
    from pxr import Usd,UsdGeom,Sdf
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    stage=Usd.Stage.Open(str(source));root='/World/_scene';base=stage.GetPrimAtPath(root+'/obj_beaker')
    cache=UsdGeom.XformCache();inv=cache.GetLocalToWorldTransform(base).GetInverse()
    measured={}
    for rel,expected in [(BODY,[[0,.11349],[.0000001,.03869]]),(RIM,[[.11189,.11509],[.03669,.041245]])]:
        from pxr import Gf
        p=stage.GetPrimAtPath(str(base.GetPath())+'/'+rel);matrix=cache.GetLocalToWorldTransform(p)*inv
        xyz=np.array([matrix.Transform(Gf.Vec3d(*map(float,v))) for v in UsdGeom.Mesh(p).GetPointsAttr().Get()]);radius=np.linalg.norm(xyz[:,:2],axis=1)
        actual=[[xyz[:,2].min(),xyz[:,2].max()],[radius.min(),radius.max()]]
        if not np.allclose(actual,expected,atol=1e-7,rtol=0):raise ValueError('Source dimensions differ: '+rel+str(actual))
        measured[rel]=actual
    before=invariant_snapshot(stage,root)
    layer=Sdf.Layer.CreateNew(str(out/'runtime_delta.usda'));stage.GetRootLayer().subLayerPaths.insert(0,layer.identifier);stage.SetEditTarget(layer)
    intervention=author(stage,root);after=invariant_snapshot(stage,root)
    if before!=after:raise ValueError('Unexpected source invariant changed')
    layer.Save()
    # Portable package layer targets /World, to reference at /World/_scene.
    package=Sdf.Layer.CreateNew(str(out/'bath_rigid_proxy_delta.usda'));Sdf.CopySpec(layer,root,package,'/World');package.Save()
    receipt={'source':str(source),'measured_body_local_dimensions':measured,'intervention':intervention,'invariant_attribute_count':len(before),'invariants_unchanged':before==after,'inner_chord_bound_m':.03669*(1-math.cos(math.pi/32)),'note':'Structural audit only; native120 cold/lift/robot validation required.'}
    (out/'composition_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(build_delta(a.source,a.out),indent=2))
