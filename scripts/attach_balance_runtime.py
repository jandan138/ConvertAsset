"""Producer-owned live display and supplied portable device-controller attachment."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def attach(asset, policy, bridge, template, config):
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf
    root='/World/obj_analytical_balance'
    stage=Usd.Stage.Open(str(asset))
    prim=stage.GetPrimAtPath(root)
    panel=root+'/Instance/Body/ControlPanel'
    original=panel+'/Digits'
    UsdGeom.Imageable(stage.GetPrimAtPath(original)).CreateVisibilityAttr('invisible')
    live=panel+'/LiveDigits'
    UsdGeom.Xform.Define(stage,live)
    material=UsdShade.Material(stage.GetPrimAtPath(root+'/Looks/LCDDigits'))
    for i in range(8):
        for seg in 'abcdefg':
            src=stage.GetPrimAtPath(original+'/Inactive/Digit_0_'+seg)
            path=live+f'/D{i}_{seg}'
            Sdf.CopySpec(stage.GetRootLayer(),src.GetPath(),stage.GetRootLayer(),path)
            mesh=UsdGeom.Mesh(stage.GetPrimAtPath(path))
            points=[Gf.Vec3f((p[0]+.0205)*.58-.021+i*.011,p[1]-.00025,p[2]+.00052)
                    for p in mesh.GetPointsAttr().Get()]
            mesh.GetPointsAttr().Set(points)
            mesh.CreateExtentAttr(UsdGeom.PointBased(mesh).ComputeExtent(points))
            mesh.CreateVisibilityAttr('invisible')
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
        stage.RemovePrim(live+f'/P{i}')
        dot=UsdGeom.Sphere.Define(stage,live+f'/P{i}')
        dot.CreateRadiusAttr(.00065)
        dot.AddTranslateOp().Set(Gf.Vec3d(-.0155+i*.011,-.1462,.0935))
        dot.CreateVisibilityAttr('invisible')
        UsdShade.MaterialBindingAPI.Apply(dot.GetPrim()).Bind(material)
    # Supplied code is part of this producer artifact and content-hashed, not
    # imported from the consumer repository at runtime.
    lines=policy.read_text().splitlines(keepends=True)
    # Offline target validation belongs to compilation, not the device script.
    for node in reversed(ast.parse(''.join(lines)).body):
        if isinstance(node,ast.FunctionDef) and node.name=='validate_target':
            del lines[node.lineno-1:node.end_lineno+2]
    code=''.join(lines)+'\n'+bridge.read_text().replace('from scripts.balance_force_state import BalanceState, vertical_mass_g','')
    old='/World/obj_titration_station/Instance/Runtime/TitrationFlowGraph'
    graph=root+'/BalanceRuntime/Graph'
    UsdGeom.Xform.Define(stage,root+'/BalanceRuntime')
    source=Usd.Stage.Open(str(template))
    Sdf.CopySpec(source.GetRootLayer(),old,stage.GetRootLayer(),graph)
    for p in Usd.PrimRange(stage.GetPrimAtPath(graph)):
        for a in p.GetAttributes():
            connections=a.GetConnections()
            if connections:
                a.SetConnections([Sdf.Path(str(c).replace(old,graph)) for c in connections])
    stage.GetPrimAtPath(graph+'/FlowController').GetAttribute('inputs:script').Set(code)
    values=dict(resolution_g=.01,target_g=30.,tolerance_g=.02,capacity_g=200.,pan_mass_g=50.,
                gravity_m_s2=9.81,tabletop_z=0.,feet_min_z=0.,spoon_home_xyz=(0.,0.,0.),
                gross_g=0.,net_g=0.,tare_g=0.,target_hold_s=0.,completed_net_g=0.,tare_position_m=0.,
                valid=False,stable=False,tared=False,tare_pending=False,success=False,reset_requested=False,
                status='initializing',error='',lcd_readout='------')
    values.update(config)
    body=stage.GetPrimAtPath(root+'/Instance/Body')
    cache=UsdGeom.BBoxCache(0,['default'])
    feet=cache.ComputeRelativeBound(stage.GetPrimAtPath(str(body.GetPath())+'/Feet'),body).ComputeAlignedRange()
    values['feet_min_z']=float(feet.GetMin()[2])
    for k,v in values.items():
        kind=(Sdf.ValueTypeNames.Bool if isinstance(v,bool) else Sdf.ValueTypeNames.String if isinstance(v,str)
              else Sdf.ValueTypeNames.Double3 if isinstance(v,(list,tuple)) else Sdf.ValueTypeNames.Double)
        prim.CreateAttribute('balance:'+k,kind).Set(Gf.Vec3d(*v) if isinstance(v,(tuple,list)) else v)
    for name in ('container','spoon','samples'):
        prim.CreateRelationship('balance:'+name)
    stage.GetRootLayer().Save()
    compat=Usd.Stage.CreateNew(str(asset.parent/'asset_isaac41.usda'))
    compat.GetRootLayer().subLayerPaths=['./'+asset.name]
    compat.OverridePrim(graph+'/OnPhysicsStep').CreateAttribute('node:type',Sdf.ValueTypeNames.Token).Set('omni.isaac.core_nodes.OnPhysicsStep')
    compat.GetRootLayer().Save()
    manifest_path=asset.parent/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest.update(asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
                    controller_sha256=hashlib.sha256(code.encode()).hexdigest(),
                    configuration=values,status='candidate',requires_awake_loads=True,
                    entrypoints={'isaac45':asset.name,'isaac41':'asset_isaac41.usda'})
    manifest_path.write_text(json.dumps(manifest,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('asset','policy','bridge','template','config'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    attach(a.asset,a.policy,a.bridge,a.template,json.loads(a.config.read_text()))
