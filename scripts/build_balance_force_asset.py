"""Repair the task09 balance in its producer; retain the immutable incoming ZIP."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import zipfile

ROOT = '/World/obj_analytical_balance'


def repaired_mass(authored, declared):
    if declared is None or not 0 < declared < 100:
        raise ValueError('credible declared balance mass required')
    return float(declared)


def safe_member(name):
    p = PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts


def build(source, out, fixed=False, grain_mass_g=10.):
    from pxr import Usd, UsdGeom, UsdPhysics, Sdf, Gf
    if not math.isfinite(grain_mass_g) or grain_mass_g <= 0:
        raise ValueError('grain mass must be finite and positive')
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as z:
        for n in z.namelist():
            if not safe_member(n):
                raise ValueError('unsafe ZIP member')
        z.extractall(out/'incoming')
    original = out/'incoming/task_09_solid_weighing/scene.usd'
    shutil.copytree(original.parent/'SubUSDs', out/'SubUSDs', dirs_exist_ok=True)
    src = Usd.Stage.Open(str(original), load=Usd.Stage.LoadNone)
    src.GetRootLayer().Export(str(out/'scene_support.usda'))
    support = Usd.Stage.Open(str(out/'scene_support.usda'), load=Usd.Stage.LoadNone)
    awake_loads = []
    for load in support.Traverse():
        if load.HasAPI(UsdPhysics.RigidBodyAPI) and not str(load.GetPath()).startswith(ROOT):
            load.AddAppliedSchema('PhysxRigidBodyAPI')
            for name in ('sleepThreshold', 'stabilizationThreshold'):
                load.CreateAttribute('physxRigidBody:'+name, Sdf.ValueTypeNames.Float).Set(0)
            awake_loads.append(str(load.GetPath()))
            if load.GetName().startswith('obj_grain_'):
                UsdPhysics.MassAPI(load).CreateMassAttr(grain_mass_g/1000)
    support.GetRootLayer().Save()
    stage = Usd.Stage.CreateNew(str(out/'asset.usda'))
    UsdGeom.Xform.Define(stage, '/World')
    Sdf.CopySpec(src.GetRootLayer(), ROOT, stage.GetRootLayer(), ROOT)
    stage.SetDefaultPrim(stage.GetPrimAtPath(ROOT))
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    UsdGeom.SetStageUpAxis(stage, 'Z')
    body_old = ROOT+'/Instance/Chassis'
    body = ROOT+'/Instance/Body'
    batch = Sdf.BatchNamespaceEdit()
    batch.Add(body_old, body)
    assert stage.GetRootLayer().Apply(batch)
    stage.RemovePrim(body+'/FixedJoint')
    pan = ROOT+'/Instance/WeighingPan'
    batch = Sdf.BatchNamespaceEdit()
    batch.Add(body+'/Pan', pan)
    assert stage.GetRootLayer().Apply(batch)
    stage.GetPrimAtPath(pan).SetTypeName('Xform')
    root = stage.GetPrimAtPath(ROOT)
    for name in ('asset_id','revision'):
        root.CreateAttribute('balance:source_'+name,Sdf.ValueTypeNames.String).Set(
            str(root.GetAttribute('balance:'+name).Get()))
    root.GetAttribute('balance:asset_id').Set('analytical_balance_force_r1')
    root.GetAttribute('balance:revision').Set('force_weighing_r1')
    source_pose = list(root.GetAttribute('xformOp:translate').Get())
    root.GetAttribute('xformOp:translate').Set(Gf.Vec3d(0))
    pbody = stage.GetPrimAtPath(body)
    # Keep local assembly placement, remove numerical drift in saved quaternions.
    offset = pbody.GetAttribute('xformOp:translate').Get()
    pbody.GetAttribute('xformOp:orient').Set(Gf.Quatf(1))
    UsdGeom.Xformable(stage.GetPrimAtPath(pan)).AddTranslateOp().Set(offset)
    mass = repaired_mass(pbody.GetAttribute('physics:mass').Get(),
                         pbody.GetAttribute('balance:mass_kg').Get())
    pbody.GetAttribute('physics:mass').Set(mass)
    tare = stage.GetPrimAtPath(ROOT+'/Instance/RightTare')
    stage.GetPrimAtPath(str(tare.GetPath())+'/KeyCap_RightTare').GetAttribute('balance:role').Set('spring_return_tare_button')
    tare.GetAttribute('xformOp:translate').Set(offset)
    tare.GetAttribute('xformOp:orient').Set(Gf.Quatf(1))
    UsdPhysics.RigidBodyAPI.Apply(stage.GetPrimAtPath(pan))
    UsdPhysics.MassAPI.Apply(stage.GetPrimAtPath(pan)).CreateMassAttr(.05)
    root.AddAppliedSchema('PhysxArticulationAPI')
    root.CreateAttribute('physxArticulation:enabledSelfCollisions', Sdf.ValueTypeNames.Bool).Set(False)
    root.CreateAttribute('physxArticulation:sleepThreshold', Sdf.ValueTypeNames.Float).Set(0)
    root.CreateAttribute('physxArticulation:stabilizationThreshold', Sdf.ValueTypeNames.Float).Set(0)
    root.CreateAttribute('physxArticulation:solverPositionIterationCount', Sdf.ValueTypeNames.Int).Set(16)
    root.CreateAttribute('physxArticulation:solverVelocityIterationCount', Sdf.ValueTypeNames.Int).Set(4)
    for p in stage.Traverse():
        if p.HasAPI(UsdPhysics.RigidBodyAPI):
            api = UsdPhysics.RigidBodyAPI(p)
            api.CreateVelocityAttr(Gf.Vec3f(0))
            api.CreateAngularVelocityAttr(Gf.Vec3f(0))
            api.CreateKinematicEnabledAttr(False)
            p.AddAppliedSchema('PhysxRigidBodyAPI')
            p.CreateAttribute('physxRigidBody:sleepThreshold', Sdf.ValueTypeNames.Float).Set(0)
            p.CreateAttribute('physxRigidBody:solverPositionIterationCount', Sdf.ValueTypeNames.Int).Set(4)
            p.CreateAttribute('physxRigidBody:solverVelocityIterationCount', Sdf.ValueTypeNames.Int).Set(1)
        for rel in p.GetRelationships():
            targets = rel.GetTargets()
            if targets:
                rel.SetTargets([Sdf.Path(str(t).replace(body_old, body)) for t in targets])
        for a in p.GetAttributes():
            if a.GetTypeName() == Sdf.ValueTypeNames.Asset:
                v = a.Get()
                if v and 'SubUSDs/' in v.path:
                    a.Set(Sdf.AssetPath('./SubUSDs/'+v.path.split('SubUSDs/',1)[1]))
        if p.GetTypeName() == 'Mesh' and p.HasAPI(UsdPhysics.CollisionAPI):
            api = UsdPhysics.MeshCollisionAPI.Apply(p)
            if not api.GetApproximationAttr().Get() or api.GetApproximationAttr().Get() == 'none':
                api.CreateApproximationAttr('convexHull')
    stage.RemovePrim(ROOT+'/Joints')
    joints = ROOT+'/Instance/Joints'
    UsdGeom.Scope.Define(stage, joints)
    j = UsdPhysics.FixedJoint.Define(stage, joints+'/LoadCell')
    j.CreateBody0Rel().SetTargets([body])
    j.CreateBody1Rel().SetTargets([pan])
    j.CreateLocalPos0Attr(Gf.Vec3f(0))
    j.CreateLocalPos1Attr(Gf.Vec3f(0))
    j.CreateCollisionEnabledAttr(False)
    j = UsdPhysics.PrismaticJoint.Define(stage, joints+'/RightTarePress')
    j.CreateBody0Rel().SetTargets([body])
    j.CreateBody1Rel().SetTargets([tare.GetPath()])
    j.CreateAxisAttr('Z')
    pos = Gf.Vec3f(.108, -.13356, .09698)
    rot = Gf.Quatf(-.22010158, Gf.Vec3f(.975477,0,0))
    j.CreateLocalPos0Attr(pos)
    j.CreateLocalPos1Attr(pos)
    j.CreateLocalRot0Attr(rot)
    j.CreateLocalRot1Attr(rot)
    j.CreateLowerLimitAttr(0)
    j.CreateUpperLimitAttr(.0015)
    j.CreateCollisionEnabledAttr(False)
    drive = UsdPhysics.DriveAPI.Apply(j.GetPrim(),'linear')
    drive.CreateStiffnessAttr(1000)
    drive.CreateDampingAttr(5)
    drive.CreateMaxForceAttr(10)
    drive.CreateTargetPositionAttr(0)
    if fixed:
        j = UsdPhysics.FixedJoint.Define(stage, joints+'/BaseFixed')
        j.CreateBody0Rel().SetTargets([ROOT])
        j.CreateBody1Rel().SetTargets([body])
        j.CreateLocalPos0Attr(Gf.Vec3f(*offset))
        j.CreateLocalPos1Attr(Gf.Vec3f(0))
    # Eliminate the old baked-only display. Existing segment geometry is reused
    # by the consumer's live display, including inactive segments.
    stage.GetRootLayer().Save()
    manifest = dict(schema_version='balance_force_producer.v1', status='candidate',
                    source_zip_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    source_scene_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                    asset_sha256=hashlib.sha256((out/'asset.usda').read_bytes()).hexdigest(),
                    root=ROOT, source_root_translation=source_pose, movable=not fixed,
                    body_mass_kg=mass, pan_mass_kg=.05, pan_link=pan,
                    awake_loads=awake_loads,
                    grain_mass_g=grain_mass_g,
                    scene_support_sha256=hashlib.sha256((out/'scene_support.usda').read_bytes()).hexdigest(),
                    load_cell_joint=joints+'/LoadCell', tare_joint=joints+'/RightTarePress',
                    path_migration={body_old:body, body_old+'/Pan':pan},
                    qualification='pending independent runtime measurements')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--fixed',action='store_true')
    p.add_argument('--grain-mass-g',type=float,default=10.)
    a = p.parse_args()
    print(json.dumps(build(a.source.resolve(),a.out.resolve(),a.fixed,a.grain_mass_g),indent=2))
