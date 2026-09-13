"""Build/audit the Blender-owned chemistry tube package; no simulator startup.

Runtime promotion is metadata-only and delegated to the exact Fehling r7
integration owner; see the dated producer record for the three-pass handoff.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
ENTRY = '/World/TestTube'
MESH = ENTRY + '/Visual/GlassShell'
PACKAGE_ID = 'chemistry_test_tube_18x150_r1'


def file_sha(path):
    """Return the SHA-256 digest of exact on-disk bytes."""
    from hashlib import sha256
    return sha256(Path(path).read_bytes()).hexdigest()


def _helpers():
    sys.path.insert(0, str(ROOT/'scripts'))
    from build_threaded_tube15_fusion import _glass_material, _set_sdf
    # This admitted beaker retains BOTH MDL files (the older tube source does not).
    mdl = ROOT/'outputs/scientific_workbench_beaker_325ml_sdf_web_standard_20260824/package/deps/mdl/OmniGlass.mdl'
    return mdl, _glass_material, _set_sdf


def _mdl_closure(directory):
    """Check local OmniGlass imports; SDK standard modules remain built-ins."""
    pending, checked = ['OmniGlass'], {}
    while pending:
        name = pending.pop()
        if name in checked:
            continue
        path = directory/f'{name}.mdl'
        text = path.read_text()
        checked[path.name] = file_sha(path)
        pending.extend(re.findall(r'using\s+(\w+)\s+import', text))
        # Only these SDK modules are used by the retained NVIDIA source.
        imports = re.findall(r'import\s+::(\w+)::', text)
        if set(imports) - {'anno', 'base', 'df', 'math', 'state', 'tex'}:
            raise ValueError(f'Unexpected nonlocal MDL import in {path}')
        if re.search(r'texture_\w+\s*\(\s*"[^"\s]+"', text):
            raise ValueError('Unexpected MDL texture dependency')
    return checked


def write_asset(data, package):
    """Author exact JSON points/faces, physical moments and local OmniGlass."""
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade
    source_mdl, glass_material, set_sdf = _helpers()
    package = Path(package).resolve()
    if (package/'asset.usd').exists():
        raise FileExistsError('Refusing to overwrite frozen asset.usd')
    dependencies = _mdl_closure(source_mdl.parent)
    (package/'deps/mdl').mkdir(parents=True, exist_ok=True)
    for name in dependencies:
        shutil.copy2(source_mdl.parent/name, package/'deps/mdl'/name)
    stage = Usd.Stage.CreateNew(str(package/'asset.usd'))
    UsdGeom.SetStageMetersPerUnit(stage, 1.)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, '/World')
    stage.SetDefaultPrim(world.GetPrim())
    root = UsdGeom.Xform.Define(stage, ENTRY).GetPrim()
    root.SetCustomDataByKey('parameter_status', 'engineering_geometry')
    rigid = UsdPhysics.RigidBodyAPI.Apply(root)
    rigid.CreateRigidBodyEnabledAttr(True)
    rigid.CreateKinematicEnabledAttr(False)
    mass = UsdPhysics.MassAPI.Apply(root)
    mass.CreateMassAttr(data['mass_kg'])
    mass.CreateCenterOfMassAttr(Gf.Vec3f(*data['center_of_mass_m']))
    mass.CreateDiagonalInertiaAttr(Gf.Vec3f(*data['diagonal_inertia_kg_m2']))
    mass.CreatePrincipalAxesAttr(Gf.Quatf(1, 0, 0, 0))
    UsdGeom.Scope.Define(stage, ENTRY+'/Visual')
    mesh = UsdGeom.Mesh.Define(stage, MESH)
    mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in data['mesh']['points']])
    mesh.CreateFaceVertexCountsAttr([3]*len(data['mesh']['faces']))
    mesh.CreateFaceVertexIndicesAttr([i for face in data['mesh']['faces'] for i in face])
    mesh.CreateSubdivisionSchemeAttr('none')
    mesh.CreateOrientationAttr('rightHanded')
    mesh.CreateDoubleSidedAttr(False)
    mesh.CreateExtentAttr(UsdGeom.PointBased.ComputeExtent(mesh.GetPointsAttr().Get()))
    # Smooth normals from the actual triangulated surface, no geometry modifier.
    import numpy as np
    points = np.asarray(data['mesh']['points'])
    faces = np.asarray(data['mesh']['faces'])
    a, b, c = points[faces].transpose(1, 0, 2)
    normals = np.zeros_like(points)
    face_normals = np.cross(b-a, c-a)
    for k in range(3):
        np.add.at(normals, faces[:, k], face_normals)
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    mesh.CreateNormalsAttr([Gf.Vec3f(*n) for n in normals])
    mesh.SetNormalsInterpolation('vertex')
    set_sdf(mesh.GetPrim(), contact=.00025, rest=0.)
    material = glass_material(stage, ENTRY)
    shader = UsdShade.Shader(stage.GetPrimAtPath(str(material.GetPath())+'/Shader'))
    for name, kind, value in [
            ('glass_color', Sdf.ValueTypeNames.Color3f, Gf.Vec3f(1)),
            ('reflection_color', Sdf.ValueTypeNames.Color3f, Gf.Vec3f(1)),
            ('glass_ior', Sdf.ValueTypeNames.Float, 1.47),
            ('frosting_roughness', Sdf.ValueTypeNames.Float, .02),
            ('depth', Sdf.ValueTypeNames.Float, .001),
            ('thin_walled', Sdf.ValueTypeNames.Bool, False),
            ('enable_opacity', Sdf.ValueTypeNames.Bool, False),
            ('cutout_opacity', Sdf.ValueTypeNames.Float, 1.)]:
        shader.CreateInput(name, kind).Set(value)
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
    stage.GetRootLayer().Save()


def audit_asset(package, data):
    """Read-only fail-closed static audit against exact source geometry/moments."""
    import numpy as np
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, UsdUtils
    package = Path(package).resolve()
    stage = Usd.Stage.Open(str(package/'asset.usd'), Usd.Stage.LoadAll)

    def check(condition, message):
        if not condition:
            raise ValueError(message)

    check(stage and stage.GetDefaultPrim().GetPath() == '/World', 'defaultPrim')
    check(UsdGeom.GetStageMetersPerUnit(stage) == 1 and UsdGeom.GetStageUpAxis(stage) == 'Z', 'units')
    root = stage.GetPrimAtPath(ENTRY)
    check(root and root.HasAPI(UsdPhysics.MassAPI), 'mass root')
    check([str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)] == [ENTRY], 'single rigid root')
    check(root.GetAttribute('physics:rigidBodyEnabled').Get() is True
          and root.GetAttribute('physics:kinematicEnabled').Get() is False, 'dynamic body')
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath(MESH))
    check([str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)] == [MESH], 'single glass mesh')
    check([str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)] == [MESH], 'single shell collider')
    check(UsdGeom.XformCache().GetLocalToWorldTransform(mesh.GetPrim()) == Gf.Matrix4d(1), 'identity transforms')
    points = np.asarray(mesh.GetPointsAttr().Get())
    check(points.shape == np.asarray(data['mesh']['points']).shape
          and np.max(np.abs(points-data['mesh']['points'])) < 1e-8, 'exact geometry points')
    check(list(mesh.GetFaceVertexCountsAttr().Get()) == [3]*len(data['mesh']['faces']), 'triangle counts')
    check(list(mesh.GetFaceVertexIndicesAttr().Get()) == [i for f in data['mesh']['faces'] for i in f], 'exact triangle winding')
    check(mesh.GetOrientationAttr().Get() == 'rightHanded' and not mesh.GetDoubleSidedAttr().Get(), 'orientation')
    for name, value in [('physics:approximation', 'sdf'), ('physics:collisionEnabled', True),
                        ('physxSDFMeshCollision:sdfResolution', 512),
                        ('physxCollision:restOffset', 0.)]:
        check(mesh.GetPrim().GetAttribute(name).Get() == value, f'{name}: expected {value}')
    check(abs(mesh.GetPrim().GetAttribute('physxCollision:contactOffset').Get()-.00025) < 1e-10, 'contactOffset')
    # Plain pxr can read authored PhysX API tokens without registering Kit plugins.
    check('PhysxSDFMeshCollisionAPI' in mesh.GetPrim().GetMetadata('apiSchemas').GetAppliedItems(), 'SDF API')
    for attr, key in [('mass', 'mass_kg'), ('centerOfMass', 'center_of_mass_m'),
                      ('diagonalInertia', 'diagonal_inertia_kg_m2')]:
        check(np.allclose(root.GetAttribute('physics:'+attr).Get(), data[key], rtol=1e-6, atol=1e-12), f'physical moment {key}')
    check(root.GetAttribute('physics:principalAxes').Get() == Gf.Quatf(1, 0, 0, 0), 'principal axes')
    normals = np.asarray(mesh.GetNormalsAttr().Get())
    check(normals.shape == points.shape and np.allclose(np.linalg.norm(normals, axis=1), 1, atol=1e-6), 'unit vertex normals')
    triangles = points[np.asarray(data['mesh']['faces'])]
    a, b, c = triangles.transpose(1, 0, 2)
    face_normals = np.cross(b-a, c-a)
    check(np.all(np.einsum('ij,ij->i', face_normals, normals[np.asarray(data['mesh']['faces'])].sum(axis=1)) > 0), 'normal/winding agreement')
    material = UsdShade.MaterialBindingAPI(mesh).ComputeBoundMaterial()[0]
    check(material and str(material.GetPath()) == ENTRY+'/Looks/TransparentTube', 'glass binding')
    shader = UsdShade.Shader(stage.GetPrimAtPath(str(material.GetPath())+'/Shader'))
    check(shader.GetSourceAsset('mdl').path == 'deps/mdl/OmniGlass.mdl', 'local OmniGlass')
    check(shader.GetSourceAssetSubIdentifier('mdl') == 'OmniGlass', 'MDL identifier')
    for name, expected in [('glass_color', [1, 1, 1]), ('reflection_color', [1, 1, 1]),
                           ('glass_ior', 1.47), ('frosting_roughness', .02),
                           ('thin_walled', False), ('enable_opacity', False)]:
        check(np.allclose(shader.GetInput(name).Get(), expected), f'glass parameter {name}')
    for context in ('surface', 'volume', 'displacement'):
        connection = material.GetOutput('mdl:'+context).GetConnectedSource()
        check(connection and connection[0].GetPrim() == shader.GetPrim(), 'MDL output '+context)
    layers, assets, unresolved = UsdUtils.ComputeAllDependencies(str(package/'asset.usd'))
    check(not unresolved, f'unresolved USD dependencies: {unresolved}')
    for path in [Path(layer.realPath) for layer in layers] + [Path(p) for p in assets]:
        check(path.is_file() and path.resolve().is_relative_to(package), f'nonlocal dependency: {path}')
    for prim in stage.Traverse():
        for attr in prim.GetAttributes():
            if attr.GetTypeName() == Sdf.ValueTypeNames.Asset and attr.Get():
                check(not Path(attr.Get().path).is_absolute(), 'absolute asset path')
    mdl = _mdl_closure(package/'deps/mdl')
    return dict(status='pass', asset_sha256=file_sha(package/'asset.usd'),
                scope='USD static source equivalence, authored physics and dependency closure; no runtime',
                entry_prim=ENTRY, mesh_prim=MESH,
                hierarchy=[str(p.GetPath()) for p in stage.Traverse()],
                vertices=len(points), triangles=len(triangles),
                bounds_m=[points.min(axis=0).tolist(), points.max(axis=0).tolist()],
                local_mdl_sha256=mdl, unresolved_dependencies=[],
                collision='single closed glass-shell sdf, resolution512, contact0.00025 rest0',
                checks=dict(source_mesh_equivalence='pass', normal_winding='pass',
                            physical_moments='pass', material_bindings='pass',
                            local_dependencies='pass', single_dynamic_root='pass'),
                warnings=['SDF not cooked; Isaac Sim 4.5 GPU contact and r7 integration pending',
                          'MDL intentionally retained; built-in SDK modules require an MDL renderer'])


def build(source, package):
    """Require actual hashed Blender creation/reopen evidence before packaging."""
    source, package = Path(source).resolve(), Path(package).resolve()
    if package.exists():
        raise FileExistsError(f'Refusing to overwrite package: {package}')
    data = json.loads((source/'geometry.json').read_text())
    reports = {}
    for name in ('blender_production.json', 'blender_reopen.json'):
        report = json.loads((source/name).read_text())
        if (report['status'] != 'pass' or report['blender_version'] != '4.4.3'
                or report['blend_sha256'] != file_sha(source/'tube.blend')
                or report['geometry_sha256'] != file_sha(source/'geometry.json')):
            raise ValueError(f'Unverified Blender source: {name}')
        reports[name] = report
    if not reports['blender_reopen.json']['independent_process_reopen']:
        raise ValueError('Independent reopen required')
    previews = reports['blender_production.json']['previews']
    for name in ('preview_overview.png', 'preview_mouth.png'):
        if previews.get(name) != file_sha(source/name):
            raise ValueError('Missing/changed CPU glass preview')
    (package/'source').mkdir(parents=True)
    (package/'evidence').mkdir()
    for name in ('tube.blend', 'geometry.json'):
        shutil.copy2(source/name, package/'source'/name)
    for name in list(reports) + list(previews):
        shutil.copy2(source/name, package/'evidence'/name)
    write_asset(data, package)
    audit = audit_asset(package, data)
    audit.update(geometry_sha256=file_sha(source/'geometry.json'), blend_sha256=file_sha(source/'tube.blend'))
    _write_json(package/'evidence/static_validation.json', audit)
    manifest = {key: data[key] for key in (
        'parameter_status', 'cavity_profile_m', 'outer_radius_m', 'max_rim_radius_m',
        'mouth_z_m', 'mass_kg', 'volume_m3', 'center_of_mass_m', 'diagonal_inertia_kg_m2',
        'density_kg_m3', 'wall_thickness_m', 'cavity_interpolation', 'source_evidence')}
    manifest.update(
        package_id=PACKAGE_ID, overall_status='runtime_pending',
        entrypoints=dict(root_usd='asset.usd', asset_entry_prim=ENTRY, default_prim='World'),
        asset_sha256=audit['asset_sha256'],
        static_validation=dict(path='evidence/static_validation.json', status='pass',
                               asset_sha256=audit['asset_sha256']),
        source=dict(blend='source/tube.blend', geometry='source/geometry.json',
                    blend_sha256=file_sha(source/'tube.blend'), geometry_sha256=file_sha(source/'geometry.json')),
        stage_metrics=dict(meters_per_unit=1, up_axis='Z', root_scale=[1, 1, 1]),
        physics=dict(rigid_root=ENTRY, collision_mesh=MESH, approximation='sdf',
                     sdf_resolution=512, contact_offset_m=.00025, rest_offset_m=0),
        material=dict(route='local NVIDIA OmniGlass', glass_color=[1, 1, 1],
                      ior=1.47, frosting_roughness=.02, thin_walled=False, enable_opacity=False),
        claims=dict(static_geometry=True, runtime_qualified=False, robot_qualified=False,
                    heat_qualified=False, pbd_qualified=False, manufacturer_replica=False),
        runtime_evidence=[],
        promotion='Main integration owner: three distinct exact Fehling r7 cold-start passes, '
        'bound to frozen scene hash and embedded asset bytes; metadata-only, fixture-scoped qualification.')
    _write_json(package/'evidence/manifest.json', manifest)
    return manifest


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def audit_package(package):
    """Audit delivery hashes, source/reopen evidence and USD without writing bytes."""
    package = Path(package).resolve()
    manifest = json.loads((package/'evidence/manifest.json').read_text())
    asset_sha = file_sha(package/'asset.usd')
    if manifest['asset_sha256'] != asset_sha:
        raise ValueError('manifest asset hash is stale')
    static = manifest['static_validation']
    if static != dict(path='evidence/static_validation.json', status='pass', asset_sha256=asset_sha):
        raise ValueError('Static validation binding is stale')
    recorded = json.loads((package/static['path']).read_text())
    if recorded['status'] != 'pass' or recorded['asset_sha256'] != asset_sha:
        raise ValueError('Static report asset hash is stale')
    for filename, key in [('geometry.json', 'geometry_sha256'), ('tube.blend', 'blend_sha256')]:
        digest = file_sha(package/'source'/filename)
        if digest != manifest['source'][key] or digest != recorded[key]:
            raise ValueError(f'Stale source hash: {filename}')
        for report_name in ('blender_production.json', 'blender_reopen.json'):
            report = json.loads((package/'evidence'/report_name).read_text())
            if report['status'] != 'pass' or report[key] != digest:
                raise ValueError(f'Stale Blender evidence: {report_name}')
    for name, digest in json.loads((package/'evidence/blender_production.json').read_text())['previews'].items():
        if file_sha(package/'evidence'/name) != digest:
            raise ValueError('Stale preview hash')
    if _mdl_closure(package/'deps/mdl') != recorded['local_mdl_sha256']:
        raise ValueError('MDL dependency hash is stale')
    data = json.loads((package/'source/geometry.json').read_text())
    for key in ('cavity_profile_m', 'outer_radius_m', 'max_rim_radius_m', 'mouth_z_m',
                'mass_kg', 'volume_m3', 'center_of_mass_m', 'diagonal_inertia_kg_m2',
                'parameter_status'):
        if data[key] != manifest[key]:
            raise ValueError(f'Stale scalar/profile contract: {key}')
    result = audit_asset(package, data)
    result['package_evidence_hashes'] = 'pass'
    return result


def main(argv=None):
    """Build fresh package or print a read-only repeat static audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args(argv)
    if args.audit_only:
        result = audit_package(args.package)
    else:
        if not args.source:
            parser.error('--source required for build')
        result = build(args.source, args.package)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
