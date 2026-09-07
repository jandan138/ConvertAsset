"""Source-bound visual-only precharge revision of the promoted titration station."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'outputs/traditional_titration_assets_r2_long_handle_20260905/packages/station'
OUTPUT = ROOT/'outputs/traditional_titration_assets_r3_filled_visuals_20260907'
ENTRY = '/World/TitrationStation'
VISUAL = ENTRY+'/Instance/Burette/body_link/Visual'
CONTROLLER = ENTRY+'/Instance/Runtime/TitrationFlowGraph/FlowController'
DEPTH = 0.0003


def column_state(remaining, initial):
    """Keep the original 25 mL scale mapping; precharge is outside that range."""
    height = 0.32*max(0.0, min(1.0, remaining/initial))
    return {'bottom_z': -0.09, 'surface_z': -0.09+height,
            'height': max(0.0001, height-DEPTH), 'visible': height > 0.0001}


def lower_profile():
    """Radial liquid core inside the existing outlet/cone/neck envelopes, in meters."""
    return [(-0.2798, 0.00175), (-0.2300, 0.00012), (-0.2296, 0.0015),
            (-0.185, 0.0015), (-0.174, 0.0046), (-0.1202, 0.0046),
            (-0.1198, 0.005), (-0.09, 0.005)]


def meniscus_mesh():
    """Shallow concave cap, local z=0 is the peripheral liquid reading."""
    n, radius = 64, 0.005
    points = [(0, 0, -DEPTH)]
    points += [(radius*math.cos(2*math.pi*i/n), radius*math.sin(2*math.pi*i/n), 0) for i in range(n)]
    points += [(x, y, -DEPTH) for x, y, _ in points[1:]]
    counts, indices = [], []
    for i in range(n):
        a, b = i+1, (i+1)%n+1
        counts.extend([3, 4, 3])
        indices.extend([0, a, b, a, a+n, b+n, b, 0, b+n, a+n])
    return points, counts, indices


def lathe(profile):
    n = 64
    points = [(r*math.cos(2*math.pi*i/n), r*math.sin(2*math.pi*i/n), z)
              for z, r in profile for i in range(n)]
    counts, indices = [], []
    for ring in range(len(profile)-1):
        for i in range(n):
            a, b = ring*n+i, ring*n+(i+1)%n
            counts.append(4)
            indices.extend([a, b, b+n, a+n])
    bottom, top = len(points), len(points)+1
    points.extend([(0, 0, profile[0][0]), (0, 0, profile[-1][0])])
    for i in range(n):
        j = (i+1)%n
        counts.extend([3, 3])
        indices.extend([bottom, j, i, top, (len(profile)-1)*n+i, (len(profile)-1)*n+j])
    return points, counts, indices


def physical_signature(stage):
    """Compare every authored physical prim including shape and link transforms."""
    result = {}
    for prim in stage.TraverseAll():
        schemas = list(prim.GetAppliedSchemas())
        if any('Physics' in s or 'Physx' in s for s in schemas) or 'Joint' in prim.GetTypeName():
            result[str(prim.GetPath())] = {
                'schemas': schemas, 'type': prim.GetTypeName(),
                'attributes': {a.GetName(): str(a.Get()) for a in prim.GetAttributes()},
                'relationships': {r.GetName(): [str(p) for p in r.GetTargets()] for r in prim.GetRelationships()}}
    return result


def audit_precharge_envelope(stage):
    """Sample the liquid surface against the union of the actual source primitive envelopes."""
    from pxr import Gf, UsdGeom
    cache = UsdGeom.XformCache()
    frame = cache.GetLocalToWorldTransform(stage.GetPrimAtPath(VISUAL))
    shapes = []
    for name in ('tube', 'glass_valve_neck', 'ptfe_valve_body', 'glass_outlet', 'delivery_tip'):
        prim = stage.GetPrimAtPath(VISUAL+'/'+name)
        shapes.append((prim, frame*cache.GetLocalToWorldTransform(prim).GetInverse()))
    samples = []
    profile = lower_profile()
    for (z0, r0), (z1, r1) in zip(profile, profile[1:]):
        for i in range(65):
            z, r = z0+(z1-z0)*i/64, r0+(r1-r0)*i/64
            samples.extend((r*math.cos(a*math.pi/4), r*math.sin(a*math.pi/4), z) for a in range(8))
    outside = []
    for point in samples:
        contained = False
        for prim, transform in shapes:
            xyz = transform.Transform(Gf.Vec3d(*point))
            axis = {'X': 0, 'Y': 1, 'Z': 2}[str(prim.GetAttribute('axis').Get())]
            h = float(prim.GetAttribute('height').Get())
            radius = float(prim.GetAttribute('radius').Get())
            if abs(xyz[axis]) > h/2+1e-7:
                continue
            if prim.GetTypeName() == 'Cone':
                radius *= 0.5-xyz[axis]/h
            if math.sqrt(sum(xyz[j]**2 for j in range(3) if j != axis)) <= radius+1e-7:
                contained = True
                break
        if not contained:
            outside.append(point)
    if outside:
        raise ValueError(f'liquid outside source envelopes: {outside[:3]} ({len(outside)} points)')
    return len(samples)


def author(stage):
    from pxr import Gf, Sdf, UsdGeom, UsdShade

    material_path = ENTRY+'/Instance/Burette/Materials/liquid'
    stage.RemovePrim(material_path)
    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, material_path+'/Shader')
    shader.SetSourceAsset(Sdf.AssetPath('deps/mdl/OmniGlass.mdl'), 'mdl')
    shader.SetSourceAssetSubIdentifier('OmniGlass', 'mdl')
    for name, kind, value in (
        ('glass_color', Sdf.ValueTypeNames.Color3f, Gf.Vec3f(0.97, 0.99, 1.0)),
        ('reflection_color', Sdf.ValueTypeNames.Color3f, Gf.Vec3f(1.0)),
        ('glass_ior', Sdf.ValueTypeNames.Float, 1.333),
        ('frosting_roughness', Sdf.ValueTypeNames.Float, 0.02),
        ('depth', Sdf.ValueTypeNames.Float, 0.05),
        ('thin_walled', Sdf.ValueTypeNames.Bool, False),
        ('enable_opacity', Sdf.ValueTypeNames.Bool, False),
        ('cutout_opacity', Sdf.ValueTypeNames.Float, 1.0),
    ):
        shader.CreateInput(name, kind).Set(value)
    shader.CreateOutput('out', Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput('mdl').ConnectToSource(shader.ConnectableAPI(), 'out')
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), 'out')
    for path, data in ((VISUAL+'/liquid_meniscus', meniscus_mesh()),
                       (VISUAL+'/liquid_precharge', lathe(lower_profile()))):
        stage.RemovePrim(path)
        mesh = UsdGeom.Mesh.Define(stage, path)
        points, counts, indices = data
        mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in points])
        mesh.CreateFaceVertexCountsAttr(counts)
        mesh.CreateFaceVertexIndicesAttr(indices)
        mesh.CreateSubdivisionSchemeAttr('none')
        mesh.CreateDoubleSidedAttr(True)
        mesh.GetPrim().SetCustomDataByKey('visualOnly', True)
    state = column_state(25, 25)
    column = UsdGeom.Cylinder(stage.GetPrimAtPath(VISUAL+'/liquid_column'))
    column.GetHeightAttr().Set(state['height'])
    column.GetPrim().GetAttribute('xformOp:translate').Set(Gf.Vec3d(0, 0, -0.09+state['height']/2))
    UsdGeom.Xformable(stage.GetPrimAtPath(VISUAL+'/liquid_meniscus')).AddTranslateOp().Set(Gf.Vec3d(0, 0, state['surface_z']))
    for name in ('liquid_column', 'liquid_meniscus', 'liquid_precharge'):
        prim = stage.GetPrimAtPath(VISUAL+'/'+name)
        UsdGeom.Imageable(prim).CreateVisibilityAttr('inherited')
        UsdGeom.PrimvarsAPI(prim).CreatePrimvar('doNotCastShadows', Sdf.ValueTypeNames.Bool).Set(True)
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
    script_attr = stage.GetPrimAtPath(CONTROLLER).GetAttribute('inputs:script')
    script = script_attr.Get()
    replacements = {
        'Set(max(0.0001, height))': 'Set(max(0.0001, height - 0.0003))',
        '-0.09 + height/2.0': '-0.09 + max(0.0001, height - 0.0003)/2.0',
    }
    for old, new in replacements.items():
        if script.count(old) != 1:
            raise ValueError(f'unexpected source controller: {old}')
        script = script.replace(old, new)
    script_attr.Set(script)


def build(source=SOURCE, out=OUTPUT, refresh=False):
    from pxr import Usd, UsdUtils

    package = out/'packages/station'
    if package.exists():
        if not refresh or json.loads((package/'evidence/manifest.json').read_text())['overall_status'] != 'runtime_pending':
            raise FileExistsError(package)
        shutil.copy2(source/'asset.usd', package/'asset.usd')
    else:
        shutil.copytree(source, package, ignore=lambda directory, names: {'evidence'} if Path(directory) == source else set())
    evidence = package/'evidence'
    evidence.mkdir(exist_ok=True)
    stage = Usd.Stage.Open(str(package/'asset.usd'))
    before = physical_signature(stage)
    author(stage)
    stage.GetRootLayer().Save()
    after = physical_signature(stage)
    if before != after:
        raise ValueError('physical content changed')
    sample_count = audit_precharge_envelope(stage)
    layers, assets, unresolved = UsdUtils.ComputeAllDependencies(str(package/'asset.usd'))
    paths = [Path(layer.realPath).resolve() for layer in layers if layer.realPath]+[Path(str(a)).resolve() for a in assets]
    if unresolved or any(not p.is_relative_to(package.resolve()) for p in paths):
        raise ValueError('package closure failed')
    manifest = {'schema_version': 'aan.traditional_titration_asset.v1',
                'package_id': 'traditional_titration_station_r3', 'asset_role': 'articulated_object',
                'overall_status': 'runtime_pending', 'blocked_reasons': ['runtime_pending'],
                'entrypoints': {'root_usd': 'asset.usd', 'default_prim': 'World', 'asset_entry_prim': ENTRY},
                'source': {'package_id': 'traditional_titration_station_r2', 'asset_path': str(source/'asset.usd'),
                           'asset_sha256': sha256((source/'asset.usd').read_bytes()).hexdigest()},
                'asset_sha256': sha256((package/'asset.usd').read_bytes()).hexdigest(),
                'visual_recipe': {'color': [0.97, 0.99, 1.0], 'ior': 1.333, 'roughness': 0.02,
                                  'depth_m': 0.05, 'casts_shadow': False, 'precharge_counts_toward_25ml': False},
                'claims': {'physical_content_unchanged': True, 'pbd_liquid': False,
                           'robot_policy_success': False, 'benchmark_success': False}}
    (evidence/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (evidence/'static_audit.json').write_text(json.dumps({'status': 'pass', 'physical_prim_count': len(before),
        'physical_content_identical': True, 'dependency_closure': True,
        'precharge_envelope_samples': sample_count, 'outside_envelope_samples': 0,
        'lower_profile_m': lower_profile()}, indent=2)+'\n')
    print(package)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--out', type=Path, default=OUTPUT)
    parser.add_argument('--refresh-candidate', action='store_true')
    args = parser.parse_args()
    build(args.source, args.out, args.refresh_candidate)
