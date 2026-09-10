"""Compose a producer-owned powder/contact fixture with the qualified force balance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def build(powder, balance, out, controller_source=None, iterations=24):
    from pxr import Usd, UsdGeom, UsdPhysics, UsdShade, Sdf, Gf
    out.mkdir(parents=True,exist_ok=False)
    shutil.copytree(balance,out/'balance')
    src = Usd.Stage.Open(str(powder))
    src.GetRootLayer().Export(str(out/'scene.usda'))
    stage = Usd.Stage.Open(str(out/'scene.usda'))
    root = '/World/obj_analytical_balance'
    scale = stage.DefinePrim(root,'Xform')
    scale.GetReferences().AddReference('./balance/asset.usda',root)
    scale.GetAttribute('xformOp:translate').Set(Gf.Vec3d(0))
    scale.GetAttribute('balance:tabletop_z').Set(0.)
    # Task completion is not the five-block task. The instrument still weighs.
    scale.GetRelationship('balance:container').ClearTargets(True)
    cache = UsdGeom.BBoxCache(0,['default'])
    pan = stage.GetPrimAtPath(root+'/Instance/WeighingPan')
    bound = cache.ComputeWorldBound(pan).ComputeAlignedRange()
    feet = cache.ComputeWorldBound(stage.GetPrimAtPath(root+'/Instance/Body/Feet')).ComputeAlignedRange()
    center = (bound.GetMin()+bound.GetMax())/2
    scale.GetAttribute('xformOp:translate').Set(Gf.Vec3d(.18-center[0],-center[1],.0005-feet.GetMin()[2]))
    cache.Clear()
    surface = cache.ComputeWorldBound(pan).ComputeAlignedRange().GetMax()[2]
    offset = float(surface)+.003-.006
    for name in ('Source','Spoon','Pan'):
        attr = stage.GetPrimAtPath('/World/'+name).GetAttribute('xformOp:translate')
        value = attr.Get()
        value[2] += offset
        if name == 'Pan':
            value[0] = .18
        attr.Set(value)
    for grain in stage.GetPrimAtPath('/World/Powder').GetChildren():
        attr = grain.GetAttribute('xformOp:translate')
        value = attr.Get()
        value[2] += offset
        attr.Set(value)
        grain.GetAttribute('physxRigidBody:enableCCD').Set(True)
        grain.GetAttribute('physxRigidBody:solverPositionIterationCount').Set(iterations)
    receiver = stage.GetPrimAtPath('/World/Pan')
    UsdPhysics.RigidBodyAPI.Apply(receiver).CreateRigidBodyEnabledAttr(True)
    UsdPhysics.MassAPI.Apply(receiver).CreateMassAttr(.01)
    receiver.AddAppliedSchema('PhysxRigidBodyAPI')
    for name,kind,value in [('sleepThreshold',Sdf.ValueTypeNames.Float,0.),
                            ('stabilizationThreshold',Sdf.ValueTypeNames.Float,0.),
                            ('solverPositionIterationCount',Sdf.ValueTypeNames.Int,iterations),
                            ('solverVelocityIterationCount',Sdf.ValueTypeNames.Int,4)]:
        receiver.CreateAttribute('physxRigidBody:'+name,kind).Set(value)
    stand = UsdGeom.Cube.Define(stage,'/World/SourceStand')
    stand.CreateSizeAttr(1)
    stand.AddTranslateOp().Set(Gf.Vec3d(0,0,(offset+.004)/2))
    stand.AddScaleOp().Set(Gf.Vec3f(.034,.028,offset+.004))
    UsdPhysics.CollisionAPI.Apply(stand.GetPrim())
    UsdShade.MaterialBindingAPI.Apply(stand.GetPrim()).Bind(UsdShade.Material(stage.GetPrimAtPath('/World/Materials/SourceSurface')))
    ground = stage.GetPrimAtPath('/World/Ground')
    ground.GetAttribute('xformOp:scale').Set(Gf.Vec3f(.85,.65,.04))
    ground.GetAttribute('xformOp:translate').Set(Gf.Vec3d(.06,0,-.02))
    ground.GetAttribute('physxCollision:contactOffset').Set(.005)
    physics = stage.GetPrimAtPath('/World/PhysicsScene')
    # Macro instrument contacts can rest ~1 mm apart. A 30 um friction
    # activation threshold suppresses their support friction and causes drift.
    physics.GetAttribute('physxScene:frictionOffsetThreshold').Set(.005)
    physics.GetAttribute('physxScene:enableCCD').Set(True)
    if iterations != 24:
        scale.GetAttribute('physxArticulation:solverPositionIterationCount').Set(iterations)
    controller_hash = None
    if controller_source:
        sources = [controller_source/name for name in ('balance_force_state.py','balance_force_runtime.py','powder_balance_runtime.py')]
        code = '\n'.join(path.read_text() for path in sources)
        code = code.replace('from scripts.balance_force_state import BalanceState, vertical_mass_g','')
        code = code.replace('from scripts.balance_force_runtime import BalanceRuntime','')
        compile(code,'embedded_powder_balance','exec')
        stage.GetPrimAtPath(root+'/BalanceRuntime/Graph/FlowController').GetAttribute('inputs:script').Set(code)
        contact = stage.GetPrimAtPath(root+'/Instance/WeighingPan')
        contact.AddAppliedSchema('PhysxContactReportAPI')
        contact.CreateAttribute('physxContactReport:threshold',Sdf.ValueTypeNames.Float).Set(0.)
        scale.CreateAttribute('balance:measurement_source',Sdf.ValueTypeNames.String).Set('pan_contact_force')
        for name in ('joint_gross_g','channel_disagreement_g','contact_raw_gross_g'):
            scale.CreateAttribute('balance:'+name,Sdf.ValueTypeNames.Double).Set(0.)
        controller_hash = hashlib.sha256(code.encode()).hexdigest()
    stage.GetRootLayer().Save()
    meta = json.loads(powder.with_suffix('.json').read_text())
    meta['config'].update(friction_offset_threshold_m=.005,enable_ccd=True,position_iterations=iterations)
    meta['articulation_position_iterations'] = iterations if iterations != 24 else 16
    meta.update(workspace_offset=[0,0,offset], receiver_x=.18, receiver_mass_kg=.01,
                balance_asset_sha256=hashlib.sha256((balance/'asset.usda').read_bytes()).hexdigest(),
                powder_source_sha256=hashlib.sha256(powder.read_bytes()).hexdigest(),
                pan_surface_z=float(surface), validation='candidate; integrated runtime pending')
    meta['measurement_source'] = 'pan_contact_force' if controller_source else 'incoming_joint_force'
    meta['controller_sha256'] = controller_hash
    (out/'scene.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps({'workspace_offset':meta['workspace_offset'],'pan_surface_z':surface}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('powder','balance','out'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--controller-source',type=Path)
    p.add_argument('--iterations',type=int,default=24)
    a = p.parse_args()
    build(a.powder,a.balance,a.out,a.controller_source,a.iterations)
