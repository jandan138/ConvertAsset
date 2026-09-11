"""Original task09 + repaired balance + shallow hollow bottle and obj_ grains.

All physical modifications belong to this producer revision. Incoming and older
qualified packages are immutable inputs. Runtime qualification is separate.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import shutil

FALSE_FLOOR = .131
BOTTLE = '/World/obj_powder_bottle'
SPOON = '/World/obj_sampling_spoon'
BOAT = '/World/obj_weighing_boat'
BALANCE = '/World/obj_analytical_balance'


def signed_volume(points, triangles):
    volume = 0.
    for i in range(0,len(triangles),3):
        a,b,c = (points[triangles[i+j]] for j in range(3))
        volume += (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])
                   +a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    return volume


def outward_winding(points, triangles):
    volume = signed_volume(points,triangles)
    if not math.isfinite(volume) or abs(volume)<1e-15:
        raise ValueError('Collision shell has no finite enclosed volume')
    result = list(triangles)
    if volume<0:
        for i in range(0,len(result),3):
            result[i+1],result[i+2] = result[i+2],result[i+1]
    return result,abs(volume)


def powder_centers(count, seed):
    spacing = .00132
    radius = .0169
    layers = []
    dz = spacing*math.sqrt(2/3)
    for k in range(8):
        layer = []
        for y in range(-18,19):
            for x in range(-18,19):
                px = (x+.5*(y%2)+.5*(k%2))*spacing
                py = y*spacing*math.sqrt(3)/2+(k%2)*spacing*math.sqrt(3)/6
                if px*px+py*py < radius*radius:
                    layer.append((px,py,FALSE_FLOOR+.00072+k*dz))
        if FALSE_FLOOR+.00072+k*dz+.00061 < .1397:
            layers.extend(layer)
    if count <= 0 or count>len(layers):
        raise ValueError('powder exceeds shallow bottle pocket')
    rng = random.Random(seed)
    return [tuple(v+rng.uniform(-1e-5,1e-5) for v in point) for point in layers[:count]]


def add_grain(stage, prototype_layer, path, position, orientation):
    from pxr import Sdf,UsdGeom,UsdPhysics,Gf
    root = UsdGeom.Xform.Define(stage,path)
    root.AddTranslateOp().Set(Gf.Vec3d(*position))
    root.AddOrientOp().Set(orientation)
    root.AddScaleOp().Set(Gf.Vec3f(1))
    Sdf.CopySpec(prototype_layer,'/World/Powder/g_00000',stage.GetRootLayer(),path+'/Mesh')
    mesh = stage.GetPrimAtPath(path+'/Mesh')
    for schema in ('PhysicsRigidBodyAPI','PhysicsMassAPI','PhysxRigidBodyAPI'):
        mesh.RemoveAppliedSchema(schema)
        root.GetPrim().AddAppliedSchema(schema)
    body_names = set(UsdPhysics.MassAPI.GetSchemaAttributeNames()) | set(UsdPhysics.RigidBodyAPI.GetSchemaAttributeNames())
    for attr in list(mesh.GetAuthoredAttributes()):
        name = attr.GetName()
        if name in body_names or name.startswith('physxRigidBody:'):
            root.GetPrim().CreateAttribute(name,attr.GetTypeName(),custom=False).Set(attr.Get())
            mesh.RemoveProperty(name)
    UsdGeom.Xformable(mesh).SetXformOpOrder([op for op in UsdGeom.Xformable(mesh).GetOrderedXformOps()
                                          if op.GetOpType()==UsdGeom.XformOp.TypeScale])
    for name in ('xformOp:translate','xformOp:orient'):
        mesh.RemoveProperty(name)
    UsdPhysics.RigidBodyAPI(root).CreateKinematicEnabledAttr(False)
    root.GetPrim().CreateAttribute('physxRigidBody:solverPositionIterationCount',Sdf.ValueTypeNames.Int).Set(32)
    root.GetPrim().CreateAttribute('physxRigidBody:solverVelocityIterationCount',Sdf.ValueTypeNames.Int).Set(4)
    root.GetPrim().CreateAttribute('physxRigidBody:enableCCD',Sdf.ValueTypeNames.Bool).Set(True)
    return root.GetPrim(),mesh


def build(source, bottle, balance, table, prototype, controller, out, count=2048, seed=42, boat_model=None):
    from pxr import Usd,UsdGeom,UsdPhysics,UsdShade,UsdLux,Sdf,Gf
    out.mkdir(parents=True,exist_ok=False)
    for name,path in [('balance',balance),('table',table),('bottle',bottle)]:
        shutil.copytree(path,out/'deps'/name)
    shutil.copytree(source.parent/'SubUSDs',out/'SubUSDs')
    src = Usd.Stage.Open(str(source),load=Usd.Stage.LoadNone)
    original = {}
    for prim in src.GetPrimAtPath('/World').GetChildren():
        if prim.GetName().startswith('obj_'):
            original[str(prim.GetPath())] = list(map(list,UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(0)))
    src.GetRootLayer().Export(str(out/'scene.usda'))
    stage = Usd.Stage.Open(str(out/'scene.usda'),load=Usd.Stage.LoadNone)
    stage.RemovePrim('/World/table')
    stage.DefinePrim('/World/table','Xform').GetReferences().AddReference('./deps/table/asset.usd','/World/table')
    original_balance_pose = {name:src.GetPrimAtPath(BALANCE).GetAttribute(name).Get()
                             for name in ('xformOp:translate','xformOp:orient','xformOp:scale')}
    stage.RemovePrim(BALANCE)
    root = stage.DefinePrim(BALANCE,'Xform')
    root.GetReferences().AddReference('./deps/balance/asset.usda',BALANCE)
    for name,value in original_balance_pose.items():
        if value is not None:
            root.GetAttribute(name).Set(value)
    stage.Load()
    cache = UsdGeom.BBoxCache(0,['default','render'])
    tabletop = float(cache.ComputeWorldBound(stage.GetPrimAtPath('/World/table')).ComputeAlignedRange().GetMax()[2])
    feet = cache.ComputeWorldBound(stage.GetPrimAtPath(BALANCE+'/Instance/Body/Feet')).ComputeAlignedRange()
    translation = root.GetAttribute('xformOp:translate').Get()
    translation[2] += tabletop-float(feet.GetMin()[2])+.0005
    root.GetAttribute('xformOp:translate').Set(translation)
    root.GetAttribute('balance:tabletop_z').Set(tabletop)
    root.GetAttribute('balance:resolution_g').Set(.01)
    root.GetAttribute('physxArticulation:solverPositionIterationCount').Set(32)
    # Standalone instrument mode: keep the five original samples but do not
    # reinterpret a powder transfer as success in the old 30 g block task.
    root.GetRelationship('balance:container').ClearTargets(True)
    for prim in stage.Traverse():
        for attr in prim.GetAttributes():
            if attr.GetTypeName()==Sdf.ValueTypeNames.Asset:
                value = attr.Get()
                if value and 'SubUSDs/' in value.path:
                    attr.Set(Sdf.AssetPath('./SubUSDs/'+value.path.split('SubUSDs/',1)[1]))
                if value and (value.path in ('OmniGlass.mdl','OmniSurface.mdl','OmniPBR.mdl')
                              or 'SubUSDs/materials/' in value.path):
                    leaf = Path(value.path).name
                    if 'SubUSDs/materials/' in value.path and leaf in ('OmniGlass.mdl','OmniSurface.mdl','OmniPBR.mdl'):
                        leaf = 'incoming_'+leaf
                    local = out/'deps/balance/materials/isaac45/deps/mdl'/leaf
                    if not local.exists():
                        raise ValueError('Qualified source MDL closure missing: '+str(local))
                    attr.Set(Sdf.AssetPath('./'+str(local.relative_to(out))))
    powder_stage = Usd.Stage.Open(str(prototype))
    for prim in list(stage.Traverse()):
        if prim.IsA(UsdPhysics.Scene):
            stage.RemovePrim(prim.GetPath())
    Sdf.CopySpec(powder_stage.GetRootLayer(),'/World/PhysicsScene',stage.GetRootLayer(),'/World/PhysicsScene')
    physics = stage.GetPrimAtPath('/World/PhysicsScene')
    physics.GetAttribute('physxScene:frictionOffsetThreshold').Set(.005)
    physics.GetAttribute('physxScene:enableCCD').Set(True)
    physics.GetAttribute('physxScene:timeStepsPerSecond').Set(480)
    physics.GetAttribute('physxScene:solverType').Set('PGS')

    visual_mat = UsdShade.Material.Define(stage,'/World/PowderLooks/Surface')
    shader = UsdShade.Shader.Define(stage,'/World/PowderLooks/Surface/Shader')
    shader.CreateIdAttr('UsdPreviewSurface')
    shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(.78,.63,.20))
    shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.8)
    visual_mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
    material = UsdShade.Material.Define(stage,'/World/PowderLooks/Contact')
    api = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    api.CreateStaticFrictionAttr(.65)
    api.CreateDynamicFrictionAttr(.5)
    api.CreateRestitutionAttr(0.)

    vessel = stage.DefinePrim(BOTTLE,'Xform')
    vessel.GetReferences().AddReference('./deps/bottle/bottle.usd','/Bottle')
    bottle_xyz = Gf.Vec3d(-.080,-.065,tabletop+.001)
    UsdGeom.Xformable(vessel).AddTranslateOp().Set(bottle_xyz)
    UsdGeom.Xformable(vessel).AddOrientOp().Set(Gf.Quatf(1))
    insert = UsdGeom.Mesh.Define(stage,BOTTLE+'/Colliders/FalseBottom')
    n = 24
    insert.CreatePointsAttr([Gf.Vec3f(.0282*math.cos(2*math.pi*i/n),.0282*math.sin(2*math.pi*i/n),z)
                            for z in (.003,FALSE_FLOOR) for i in range(n)])
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    insert.CreateFaceVertexCountsAttr([len(face) for face in faces])
    insert.CreateFaceVertexIndicesAttr([v for face in faces for v in face])
    insert.CreateSubdivisionSchemeAttr('none')
    UsdPhysics.MeshCollisionAPI.Apply(insert.GetPrim()).CreateApproximationAttr('convexHull')
    insert.CreateDisplayColorAttr([Gf.Vec3f(.72,.70,.62)])
    UsdPhysics.CollisionAPI.Apply(insert.GetPrim())
    # A shallow cup in the fixed insert concentrates a useful scoop depth
    # without simulating the entire 56 mm diameter bottle volume.
    for i in range(16):
        a,b = 2*math.pi*i/16,2*math.pi*(i+1)/16
        wall = UsdGeom.Mesh.Define(stage,BOTTLE+f'/Colliders/PocketWall_{i:02d}')
        verts = [Gf.Vec3f(r*math.cos(t),r*math.sin(t),z) for z in (FALSE_FLOOR-.0005,.139)
                 for r,t in [(.018,a),(.0283,a),(.0283,b),(.018,b)]]
        faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        wall.CreatePointsAttr(verts)
        wall.CreateFaceVertexCountsAttr([4]*6)
        wall.CreateFaceVertexIndicesAttr([v for face in faces for v in face])
        wall.CreateSubdivisionSchemeAttr('none')
        wall.CreateDisplayColorAttr([Gf.Vec3f(.72,.70,.62)])
        UsdPhysics.CollisionAPI.Apply(wall.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(wall.GetPrim()).CreateApproximationAttr('convexHull')
    for prim in Usd.PrimRange(vessel):
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            prim.AddAppliedSchema('PhysxCollisionAPI')
            prim.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.00005)
            prim.CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(0.)
            UsdShade.MaterialBindingAPI.Apply(prim).Bind(material,materialPurpose='physics')
    # Bottle mass includes its fixed insert as an engineering fixture mass.
    for body_path in (BOTTLE,SPOON,BOAT):
        prim = stage.GetPrimAtPath(body_path)
        prim.AddAppliedSchema('PhysxRigidBodyAPI')
        for name,value in [('sleepThreshold',0.),('stabilizationThreshold',0.)]:
            prim.CreateAttribute('physxRigidBody:'+name,Sdf.ValueTypeNames.Float).Set(value)
        prim.CreateAttribute('physxRigidBody:solverPositionIterationCount',Sdf.ValueTypeNames.Int).Set(32)
        prim.CreateAttribute('physxRigidBody:solverVelocityIterationCount',Sdf.ValueTypeNames.Int).Set(4)
        prim.CreateAttribute('physxRigidBody:enableCCD',Sdf.ValueTypeNames.Bool).Set(body_path!=BOAT)

    def sdf_mesh(prim):
        UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
        UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr('sdf')
        prim.AddAppliedSchema('PhysxSDFMeshCollisionAPI')
        prim.CreateAttribute('physxSDFMeshCollision:sdfResolution',Sdf.ValueTypeNames.UInt).Set(512)
        prim.AddAppliedSchema('PhysxCollisionAPI')
        prim.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.00005)
        prim.CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(0.)
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(material,materialPurpose='physics')
    spoon_mesh = next(p for p in Usd.PrimRange(stage.GetPrimAtPath(SPOON)) if p.IsA(UsdGeom.Mesh))
    sdf_mesh(spoon_mesh)
    # Replace the six gapped hull proxies by collision on the original visible
    # hollow boat surface. The visual mesh and its placement are unchanged.
    for prim in Usd.PrimRange(stage.GetPrimAtPath(BOAT)):
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            prim.GetAttribute('physics:collisionEnabled').Set(False)
    boat_mesh = stage.GetPrimAtPath(BOAT+'/Visual/HunyuanSurface')
    # The original visual surface is watertight but has inward triangle winding.
    # Keep its appearance byte-for-byte and cook an outward collision copy.
    mesh_to_root = (UsdGeom.Xformable(boat_mesh).ComputeLocalToWorldTransform(0)
                    *UsdGeom.Xformable(stage.GetPrimAtPath(BOAT)).ComputeLocalToWorldTransform(0).GetInverse())
    shell_points = [Gf.Vec3f(mesh_to_root.Transform(Gf.Vec3d(*point)))
                    for point in UsdGeom.Mesh(boat_mesh).GetPointsAttr().Get()]
    counts = list(UsdGeom.Mesh(boat_mesh).GetFaceVertexCountsAttr().Get())
    if any(count!=3 for count in counts):
        raise ValueError('Expected triangulated original boat shell')
    original_indices = list(UsdGeom.Mesh(boat_mesh).GetFaceVertexIndicesAttr().Get())
    shell_indices,shell_volume = outward_winding(shell_points,original_indices)
    shell = UsdGeom.Mesh.Define(stage,BOAT+'/PowderCollisionShell')
    shell.CreatePointsAttr(shell_points)
    shell.CreateFaceVertexCountsAttr(counts)
    shell.CreateFaceVertexIndicesAttr(shell_indices)
    shell.CreateSubdivisionSchemeAttr('none')
    shell.CreateOrientationAttr('rightHanded')
    shell.CreateVisibilityAttr('invisible')
    sdf_mesh(shell.GetPrim())
    if boat_model:
        geometry = json.loads(boat_model.read_text())
        boat_root = stage.GetPrimAtPath(BOAT)
        boat_root.GetAttribute('xformOp:scale').Set(Gf.Vec3f(*geometry['root_scale']))
        mass_api = UsdPhysics.MassAPI.Apply(boat_root)
        mass_api.CreateMassAttr(geometry['mass_kg'])
        if 'diagonal_inertia_kg_m2' in geometry:
            mass_api.CreateCenterOfMassAttr(Gf.Vec3f(*geometry['center_of_mass_m']))
            mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(*geometry['diagonal_inertia_kg_m2']))
            q = geometry['principal_axes_wxyz']
            mass_api.CreatePrincipalAxesAttr(Gf.Quatf(q[0],Gf.Vec3f(*q[1:])))
        for prim in list(Usd.PrimRange(stage.GetPrimAtPath(BOAT))):
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                prim.SetActive(False)
        boat_mesh.SetActive(False)
        boat_material = UsdShade.Material.Define(stage,'/World/PowderLooks/BoatSurface')
        boat_shader = UsdShade.Shader.Define(stage,'/World/PowderLooks/BoatSurface/Shader')
        boat_shader.CreateIdAttr('UsdPreviewSurface')
        boat_shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(.83,.84,.82))
        boat_shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.65)
        boat_material.CreateSurfaceOutput().ConnectToSource(boat_shader.ConnectableAPI(),'surface')
        for name,data,collision in [('Visual/ProceduralBoat',geometry['visual'],False)]+[(f"PowderProxy/{part['name']}",part,True) for part in geometry['colliders']]:
            mesh = UsdGeom.Mesh.Define(stage,BOAT+'/'+name)
            mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in data['points']])
            mesh.CreateFaceVertexCountsAttr([len(face) for face in data['faces']])
            mesh.CreateFaceVertexIndicesAttr([v for face in data['faces'] for v in face])
            mesh.CreateSubdivisionSchemeAttr('none')
            if collision:
                mesh.CreateVisibilityAttr('invisible')
                UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
                UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr('convexHull')
                mesh.GetPrim().AddAppliedSchema('PhysxCollisionAPI')
                mesh.GetPrim().CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.00005)
                mesh.GetPrim().CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(0.)
                UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material,materialPurpose='physics')
            else:
                UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(boat_material)
        shutil.copytree(boat_model.parent,out/'source_boat')

    rng = random.Random(seed)
    for i,point in enumerate(powder_centers(count,seed)):
        q = [rng.gauss(0,1) for _ in range(4)]
        length = math.sqrt(sum(v*v for v in q))
        quat = Gf.Quatf(q[0]/length,Gf.Vec3f(*(v/length for v in q[1:])))
        _,mesh = add_grain(stage,powder_stage.GetRootLayer(),f'/World/obj_powder_grain_{i:05d}',
                         bottle_xyz+Gf.Vec3d(*point),quat)
        UsdShade.MaterialBindingAPI.Apply(mesh).Bind(visual_mat)
        UsdShade.MaterialBindingAPI.Apply(mesh).Bind(material,materialPurpose='physics')
    sources = [controller/name for name in ('balance_force_state.py','balance_force_runtime.py','powder_balance_runtime.py','task09_powder_runtime.py')]
    code = '\n'.join(path.read_text() for path in sources)
    code = code.replace('from scripts.balance_force_state import BalanceState, vertical_mass_g','')
    code = code.replace('from scripts.balance_force_runtime import BalanceRuntime','')
    code = code.replace('from scripts.powder_balance_runtime import PowderBalanceRuntime, compute as base_compute','base_compute = compute')
    compile(code,'task09_powder_controller','exec')
    stage.GetPrimAtPath(BALANCE+'/BalanceRuntime/Graph/FlowController').GetAttribute('inputs:script').Set(code)
    pan = stage.GetPrimAtPath(BALANCE+'/Instance/WeighingPan')
    pan.AddAppliedSchema('PhysxContactReportAPI')
    pan.CreateAttribute('physxContactReport:threshold',Sdf.ValueTypeNames.Float).Set(0.)
    root.CreateAttribute('balance:measurement_source',Sdf.ValueTypeNames.String).Set('pan_contact_force')
    for name in ('joint_gross_g','channel_disagreement_g','contact_raw_gross_g'):
        root.CreateAttribute('balance:'+name,Sdf.ValueTypeNames.Double).Set(0.)
    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            prim.CreateAttribute('physxRigidBody:solverPositionIterationCount',Sdf.ValueTypeNames.Int).Set(32)
    light = UsdLux.DomeLight.Define(stage,'/World/task09_powder_light')
    light.CreateIntensityAttr(650)
    key = UsdLux.DistantLight.Define(stage,'/World/task09_powder_key')
    key.CreateIntensityAttr(1800)
    key.CreateAngleAttr(3)
    key.AddRotateXYZOp().Set(Gf.Vec3f(-35,-20,35))
    stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
    stage.GetRootLayer().Save()
    preserved = {}
    for path,transform in original.items():
        if path!=BALANCE and not (boat_model and path==BOAT):
            current = list(map(list,UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(0)))
            if current!=transform:
                raise ValueError('Original placement changed: '+path)
            preserved[path] = transform
    metadata = dict(schema_version='task09_powder_bottle.v1',status='candidate',count=count,seed=seed,
                    physics_hz=480,solver='PGS',position_iterations=32,false_floor_m=FALSE_FLOOR,bottle_xyz=list(bottle_xyz),tabletop_z=tabletop,
                    powder_pocket_radius_m=.018,powder_pocket_top_m=.139,
                    paths=dict(bottle=BOTTLE,spoon=SPOON,boat=BOAT,balance=BALANCE,powder_pattern='/World/obj_powder_grain_*'),
                    mass_per_grain_kg=7.853981633974482e-7,bottle_and_insert_mass_kg=.15,
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    prototype_sha256=hashlib.sha256(prototype.read_bytes()).hexdigest(),
                    preserved_object_transforms=preserved,measurement_source='pan_contact_force',display_resolution_g=.01,
                    physics_repairs=['512 SDF original spoon surface','outward-wound hidden 512 SDF boat collision shell'],
                    boat_collision_signed_volume_m3=shell_volume,
                    boat_source_signed_volume_m3=signed_volume(shell_points,original_indices),
                    entrypoints={'45':'scene.usda'})
    (out/'scene_config.json').write_text(json.dumps(metadata,indent=2))
    if boat_model:
        metadata['physics_repairs'] = ['512 SDF original spoon surface','Blender flared weighing boat with sealed convex compound']
        metadata['boat_model_sha256'] = hashlib.sha256(boat_model.read_bytes()).hexdigest()
        metadata['boat_original_transform'] = original[BOAT]
        metadata['boat_root_scale_normalized'] = geometry['root_scale']
        (out/'scene_config.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps({'out':str(out),'tabletop_z':tabletop,'count':count,'preserved':len(preserved)}))


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source','bottle','balance','table','prototype','controller','out'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--count',type=int,default=2048)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--boat-model',type=Path)
    a = p.parse_args()
    build(a.source,a.bottle,a.balance,a.table,a.prototype,a.controller,a.out,a.count,a.seed,a.boat_model)
