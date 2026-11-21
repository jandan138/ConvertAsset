"""Produce task09 r3 from the immutable, qualified r2 scene and a Blender bottle."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import shutil

BOTTLE = '/World/obj_powder_bottle'
GRAIN = '/World/obj_powder_grain_'


def section_at(z, profile):
    if z<=profile[0]['z']:
        return profile[0]['radius'],profile[0]['exponent']
    for a,b in zip(profile,profile[1:]):
        if a['z']<=z<=b['z']:
            t = (z-a['z'])/(b['z']-a['z'])
            return ((1-t)*a['radius']+t*b['radius'],(1-t)*a['exponent']+t*b['exponent'])
    return profile[-1]['radius'],profile[-1]['exponent']


def in_profile(point, profile, margin=0.):
    x,y,z = point
    radius,exponent = section_at(z,profile)
    radial = math.hypot(x,y)
    if radial==0:
        return True
    c,s = x/radial,y/radial
    limit = radius/(abs(c)**exponent+abs(s)**exponent)**(1/exponent)
    return radial < limit-margin


def grain_properties(radius):
    if not math.isfinite(radius) or radius<=0:
        raise ValueError('positive finite grain radius required')
    ratio = radius/.0005
    return 1500*4*math.pi*radius**3/3, 7.940871538884148e-14*ratio**5


def fill_positions(profile, floor, count, radius, seed):
    bound = radius*1.182056
    spacing = 2*bound+.00014
    dz = spacing*math.sqrt(2/3)
    padding = .00075+bound+.00012
    points = []
    k = 0
    while floor+bound+.00015+k*dz < profile[-1]['z']-.003-bound:
        z = floor+bound+.00015+k*dz
        extent = math.ceil(max(row['radius'] for row in profile)*1.5/spacing)
        for iy in range(-extent,extent+1):
            y = iy*spacing*math.sqrt(3)/2+(k%2)*spacing*math.sqrt(3)/6
            for ix in range(-extent,extent+1):
                x = (ix+.5*(iy%2)+.5*(k%2))*spacing
                if in_profile((x,y,z),profile,padding):
                    points.append((x,y,z))
        k += 1
    if not 0<count<=len(points):
        raise ValueError(f'Initial cavity capacity {len(points)} is smaller than {count}')
    rng = random.Random(seed)
    return [tuple(v+rng.uniform(-1e-5,1e-5) for v in point) for point in points[:count]]


def build(base, model, out, count=16384, radius=.0007, seed=42, hz=240, *, positions=None):
    import numpy as np
    from pxr import Usd,UsdGeom,UsdPhysics,UsdShade,Sdf,Gf,Vt
    data = json.loads(model.read_text())
    floor = data['metadata']['insert_top_m']
    points = fill_positions(data['inner_profile'],floor,count,radius,seed) if positions is None else positions
    if len(points)!=count or not np.isfinite(points).all():
        raise ValueError('Initial positions must be finite and match the grain count')
    out.mkdir(parents=True,exist_ok=False)
    for folder in ('SubUSDs','source_boat'):
        shutil.copytree(base/folder,out/folder)
    for folder in ('balance','table'):
        shutil.copytree(base/'deps'/folder,out/'deps'/folder)
    shutil.copytree(model.parent,out/'source_bottle')
    source = Usd.Stage.Open(str(base/'scene.usda'))
    source.GetRootLayer().Export(str(out/'scene.usda'))
    layer = Sdf.Layer.FindOrOpen(str(out/'scene.usda'))
    original = {str(p.GetPath()):list(map(list,UsdGeom.Xformable(p).ComputeLocalToWorldTransform(0)))
                for p in source.GetPrimAtPath('/World').GetChildren()
                if p.GetName().startswith('obj_') and not str(p.GetPath()).startswith(GRAIN) and str(p.GetPath())!=BOTTLE}
    old_bottle_pose = source.GetPrimAtPath(BOTTLE).GetAttribute('xformOp:translate').Get()
    template = source.Flatten()
    edits = Sdf.BatchNamespaceEdit()
    for p in source.GetPrimAtPath('/World').GetChildren():
        if str(p.GetPath()).startswith(GRAIN) or str(p.GetPath())==BOTTLE:
            edits.Add(p.GetPath(),Sdf.Path.emptyPath)
    if not layer.Apply(edits):
        raise RuntimeError('Unable to replace bottle/grain roots')
    stage = Usd.Stage.Open(layer)
    bottle = UsdGeom.Xform.Define(stage,BOTTLE)
    bottle.AddTranslateOp().Set(old_bottle_pose)
    bottle.AddOrientOp().Set(Gf.Quatf(1))
    bottle.AddScaleOp().Set(Gf.Vec3f(1))
    UsdPhysics.RigidBodyAPI.Apply(bottle.GetPrim()).CreateKinematicEnabledAttr(False)
    mass_api = UsdPhysics.MassAPI.Apply(bottle.GetPrim())
    mass_api.CreateMassAttr(data['mass_kg'])
    mass_api.CreateCenterOfMassAttr(Gf.Vec3f(*data['center_of_mass_m']))
    mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(*data['diagonal_inertia_kg_m2']))
    mass_api.CreatePrincipalAxesAttr(Gf.Quatf(1))
    bottle.GetPrim().AddAppliedSchema('PhysxRigidBodyAPI')
    for name,typ,value in [('sleepThreshold',Sdf.ValueTypeNames.Float,0.),('stabilizationThreshold',Sdf.ValueTypeNames.Float,0.),
                           ('solverPositionIterationCount',Sdf.ValueTypeNames.Int,32),('solverVelocityIterationCount',Sdf.ValueTypeNames.Int,4)]:
        bottle.GetPrim().CreateAttribute('physxRigidBody:'+name,typ).Set(value)
    def material(name,color,roughness):
        mat = UsdShade.Material.Define(stage,'/World/CompactBottleLooks/'+name)
        shader = UsdShade.Shader.Define(stage,str(mat.GetPath())+'/Shader')
        shader.CreateIdAttr('UsdPreviewSurface')
        shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(roughness)
        mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
        return mat
    mats = {'bottle':material('HDPE',(.82,.835,.80),.38),
            'insert':material('InnerTray',(.77,.785,.75),.48),
            'accent':material('Accent',(.68,.70,.67),.45)}
    physics_mat = UsdShade.Material(stage.GetPrimAtPath('/World/PowderLooks/Contact'))
    for part,collision in [(part,False) for part in data['visual_meshes']]+[(part,True) for part in data['colliders']]:
        path = BOTTLE+('/Colliders/' if collision else '/Visual/')+part['name']
        mesh = UsdGeom.Mesh.Define(stage,path)
        vertices = np.asarray(part['points'],dtype=np.float32)
        mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(vertices))
        mesh.CreateFaceVertexCountsAttr([len(face) for face in part['faces']])
        mesh.CreateFaceVertexIndicesAttr([i for face in part['faces'] for i in face])
        mesh.CreateSubdivisionSchemeAttr('none')
        mesh.CreateOrientationAttr('rightHanded')
        if collision:
            mesh.CreateVisibilityAttr('invisible')
            UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
            UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr('convexHull')
            mesh.GetPrim().AddAppliedSchema('PhysxCollisionAPI')
            mesh.GetPrim().CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.00005)
            mesh.GetPrim().CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(0.)
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(physics_mat,materialPurpose='physics')
        else:
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mats[part['material']])
            if part['material']=='bottle':
                normals = np.zeros_like(vertices)
                for face in part['faces']:
                    for j in range(1,len(face)-1):
                        ids = [face[0],face[j],face[j+1]]
                        a,b,c = vertices[ids]
                        normal = np.cross(b-a,c-a)
                        normals[ids] += normal
                normals /= np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
                mesh.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(normals))
                mesh.SetNormalsInterpolation('vertex')
    mass,inertia = grain_properties(radius)
    rng = random.Random(seed)
    # Batch Sdf edits avoid one composition notice per individual object.
    with Sdf.ChangeBlock():
        for i,point in enumerate(points):
            path = GRAIN+f'{i:05d}'
            Sdf.CopySpec(template,GRAIN+'00000',stage.GetRootLayer(),path)
            spec = stage.GetRootLayer().GetPrimAtPath(path)
            q = [rng.gauss(0,1) for _ in range(4)]
            norm = math.sqrt(sum(v*v for v in q))
            spec.attributes['xformOp:translate'].default = old_bottle_pose+Gf.Vec3d(*point)
            spec.attributes['xformOp:orient'].default = Gf.Quatf(q[0]/norm,Gf.Vec3f(*(v/norm for v in q[1:])))
            spec.attributes['physics:mass'].default = mass
            spec.attributes['physics:diagonalInertia'].default = Gf.Vec3f(inertia)
            stage.GetRootLayer().GetPrimAtPath(path+'/Mesh').attributes['xformOp:scale'].default = Gf.Vec3f(radius)
    stage.GetPrimAtPath('/World/PhysicsScene').GetAttribute('physxScene:timeStepsPerSecond').Set(hz)
    cfg = json.loads((base/'scene_config.json').read_text())
    cfg.update(schema_version='task09_compact_powder.v3',revision='r3',status='candidate',count=count,seed=seed,
               physics_hz=hz,false_floor_m=floor,bottle_height_m=data['metadata']['height_m'],
               inner_profile=data['inner_profile'],grain_radius_m=radius,grain_bound_m=radius*1.182056,
               grain_spacing_m=2*radius*1.182056+.00014,mass_per_grain_kg=mass,
               bottle_and_insert_mass_kg=data['mass_kg'],powder_surface_target_m=floor+.011,
               target_bed_depth_m=[.010,.012],bottle_model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
               base_scene_sha256=hashlib.sha256((base/'scene.usda').read_bytes()).hexdigest(),
               calibration_counts=[0,round(.1/(mass*1000)),round(.4/(mass*1000)),round(.8/(mass*1000)),0],
               carry_window_s=[33,35],minimum_scoop_seconds=50)
    cfg.pop('powder_pocket_radius_m',None)
    cfg.pop('powder_pocket_top_m',None)
    # Original spoon geometry is unchanged; use its actual geometry to bound
    # floor and mouth clearance for the new, deeper cavity.
    spoon = stage.GetPrimAtPath(cfg['paths']['spoon'])
    spoon_mesh = next(p for p in Usd.PrimRange(spoon) if p.IsA(UsdGeom.Mesh))
    m = UsdGeom.Xformable(spoon_mesh).ComputeLocalToWorldTransform(0)*UsdGeom.Xformable(spoon).ComputeLocalToWorldTransform(0).GetInverse()
    verts = np.array([m.Transform(Gf.Vec3d(*v)) for v in UsdGeom.Mesh(spoon_mesh).GetPointsAttr().Get()])
    cfg['spoon_floor_envelope'] = [[angle,float((-(verts[:,0]-.087)*math.sin(math.radians(angle))
                                                      +verts[:,2]*math.cos(math.radians(angle))).min())]
                                     for angle in range(0,81,5)]
    for path,transform in original.items():
        if list(map(list,UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(0)))!=transform:
            raise ValueError('Unrelated object changed: '+path)
    cfg['preserved_r2_object_transforms'] = original
    stage.GetRootLayer().Save()
    (out/'scene_config.json').write_text(json.dumps(cfg,indent=2))
    print(json.dumps({'out':str(out),'particles':count,'powder_g':mass*count*1000,'physics_hz':hz,
                      'bottle_mass_g':data['mass_kg']*1000,'mouth':data['metadata']['mouth_inner_diameter_m']}))


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('base','model','out'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--count',type=int,default=16384)
    p.add_argument('--radius',type=float,default=.0007)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--hz',type=int,default=240)
    a = p.parse_args()
    build(a.base,a.model,a.out,a.count,a.radius,a.seed,a.hz)
