#!/usr/bin/env python3
"""Blender tooth-entry relief and same-process control for native gear assets."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


def relief_point(point, depth):
    """Preserve the hole, hub, Z coordinates and tooth section above 9 mm."""
    if not 0 <= depth <= 0.003:
        raise ValueError('Relief depth must lie between zero and 3 mm')
    x, y, z = point
    if depth == 0 or z >= 0.009:
        return list(point)
    dx = x - 0.02025
    radius = math.hypot(dx, y)
    if radius <= 0.015:
        return list(point)
    radial_weight = min(1., (radius - 0.015) / 0.00375)
    height_weight = min(1., max(0., (0.009 - z) / 0.004))
    factor = (radius - depth * radial_weight * height_weight) / radius
    return [0.02025 + dx * factor, y * factor, z]


def blender_phase(data_path, output):
    import bpy
    import bmesh

    data = json.loads(data_path.read_text())
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for tag, depth in [('control', 0.), ('leadin', 0.002)]:
        mesh = bpy.data.meshes.new(tag)
        mesh.from_pydata(data['points'], [], data['faces'])
        bm = bmesh.new()
        bm.from_mesh(mesh)
        # Both branches get the same cut, so deformation ends at an actual ring.
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                              dist=1e-8, plane_co=(0, 0, 0.009), plane_no=(0, 0, 1),
                              clear_inner=False, clear_outer=False)
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        for vertex in bm.verts:
            vertex.co = relief_point(vertex.co, depth)
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        obj = bpy.data.objects.new(tag, mesh)
        bpy.context.collection.objects.link(obj)
        result = {'points': [list(v.co) for v in mesh.vertices],
                  'faces': [list(f.vertices) for f in mesh.polygons],
                  'normals': [list(n.vector) for n in mesh.corner_normals],
                  'depth': depth, 'blender_version': bpy.app.version_string}
        (output / (tag + '.json')).write_text(json.dumps(result))
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'gear_leadin.blend'))


def build(source, blender, output, mass_readback=None):
    import numpy as np
    import trimesh
    from pxr import Gf, Usd, UsdGeom, UsdPhysics, Vt

    profile = None
    if mass_readback is not None:
        readback = json.loads(mass_readback.read_text())
        profile = readback['properties']
        inertia = np.asarray(profile['inertia_matrix_at_com_body_frame'])
        if (readback['status'] != 'completed' or readback['object_id'] != '04'
                or readback['meters_per_stage_unit'] != 1
                or readback['kilograms_per_stage_mass_unit'] != 1
                or not np.array_equal(inertia, np.diag(np.diag(inertia)))
                or profile['center_of_mass_local_orientation_xyzw'] != [0, 0, 0, 1]
                or profile['mass'] <= 0 or np.min(np.diag(inertia)) <= 0):
            raise ValueError('Require unit-scale source gear diagonal runtime profile')
        if hashlib.sha256(source.read_bytes()).hexdigest() not in {
                layer['sha256'] for layer in readback['target_source_layers']}:
            raise ValueError('Runtime profile does not bind the source layer')

    stage = Usd.Stage.Open(str(source))
    root = stage.GetDefaultPrim().GetPath().AppendChild('obj_04')
    meshes = [p for p in Usd.PrimRange(stage.GetPrimAtPath(root)) if p.IsA(UsdGeom.Mesh)]
    if len(meshes) != 2 or {p.GetName() for p in meshes} != {'visuals', 'collisions'}:
        raise ValueError('Expected native target visual and collision meshes')
    visual = UsdGeom.Mesh(next(p for p in meshes if p.GetName() == 'visuals'))
    points = np.asarray(visual.GetPointsAttr().Get())
    indices = np.asarray(visual.GetFaceVertexIndicesAttr().Get())
    if not np.all(np.asarray(visual.GetFaceVertexCountsAttr().Get()) == 3):
        raise ValueError('Source must be triangulated')
    for prim in meshes:
        mesh = UsdGeom.Mesh(prim)
        if (not np.array_equal(points, mesh.GetPointsAttr().Get()) or
                not np.array_equal(indices, mesh.GetFaceVertexIndicesAttr().Get())):
            raise ValueError('Source visual/collision geometry mismatch')
        if any(p.HasAuthoredValue() for p in UsdGeom.PrimvarsAPI(prim).GetPrimvars()):
            raise ValueError('Primvar remapping is required for textured source meshes')
    output.mkdir(parents=True, exist_ok=False)
    data = output / 'mesh_input.json'
    data.write_text(json.dumps({'points': points.tolist(), 'faces': indices.reshape(-1, 3).tolist()}))
    command = [str(blender), '--background', '--factory-startup', '--python',
               str(Path(__file__).resolve()), '--', '--blender-phase', '--source', str(data),
               '--output', str(output)]
    with (output / 'blender.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    control = json.loads((output / 'control.json').read_text())
    leadin = json.loads((output / 'leadin.json').read_text())
    if control['faces'] != leadin['faces']:
        raise ValueError('Paired topology differs')
    cp, lp = np.asarray(control['points']), np.asarray(leadin['points'])
    preserved = (cp[:, 2] >= 0.009) | (np.linalg.norm(cp[:, :2]-[0.02025, 0], axis=1) <= 0.015)
    if not np.array_equal(cp[preserved], lp[preserved]) or not np.array_equal(cp[:, 2], lp[:, 2]):
        raise ValueError('Protected geometry changed')
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    results = []
    for tag, result in [('control', control), ('leadin', leadin)]:
        package = output / tag
        package.mkdir()
        dest = Usd.Stage.CreateNew(str(package / 'scene.usd'))
        dest.GetRootLayer().subLayerPaths = [str(source.resolve())]
        dest.SetDefaultPrim(dest.GetPrimAtPath(stage.GetDefaultPrim().GetPath()))
        if profile is not None:
            mass = UsdPhysics.MassAPI.Apply(dest.OverridePrim(root))
            mass.CreateMassAttr().Set(profile['mass'])
            mass.CreateCenterOfMassAttr().Set(Gf.Vec3f(*profile['center_of_mass_local_position']))
            mass.CreateDiagonalInertiaAttr().Set(Gf.Vec3f(*np.diag(inertia).tolist()))
            mass.CreatePrincipalAxesAttr().Set(Gf.Quatf(1.))
        pts = np.asarray(result['points'])
        faces = np.asarray(result['faces'])
        for prim in meshes:
            mesh = UsdGeom.Mesh(dest.OverridePrim(prim.GetPath()))
            mesh.GetPointsAttr().Set(Vt.Vec3fArray.FromNumpy(pts.astype(np.float32)))
            mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray.FromNumpy(faces.reshape(-1).astype(np.int32)))
            mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray.FromNumpy(np.full(len(faces), 3, dtype=np.int32)))
            mesh.GetNormalsAttr().Set(Vt.Vec3fArray.FromNumpy(np.asarray(result['normals'], dtype=np.float32)))
            mesh.SetNormalsInterpolation('faceVarying')
            mesh.GetExtentAttr().Set(Vt.Vec3fArray.FromNumpy(np.array([pts.min(0), pts.max(0)], dtype=np.float32)))
        dest.GetRootLayer().Save()
        (package / 'scene.usda').write_text(source.with_suffix('.usda').read_text())
        solid = trimesh.Trimesh(vertices=pts, faces=faces, process=True)
        if not solid.is_watertight or not solid.is_winding_consistent or solid.volume <= 0:
            raise ValueError('Invalid output solid')
        results.append({'condition': tag, 'scene': str(package / 'scene.usda'),
                        'content_sha256': hashlib.sha256((package/'scene.usd').read_bytes()).hexdigest(),
                        'vertices': len(pts), 'faces': len(faces), 'volume': float(solid.volume),
                        'watertight': bool(solid.is_watertight),
                        'blender_version': result['blender_version']})
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise ValueError('Source was modified')
    report = {'schema': 'convertasset.ebench.gear_leadin.v1', 'source': str(source),
              'source_sha256': source_hash,
              'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'changed_vertices': int(np.any(cp != lp, axis=1).sum()),
              'max_radial_relief': float(np.linalg.norm(cp-lp, axis=1).max()),
              'upper_geometry_and_hole_preserved': True, 'conditions': results,
              'mass_reference': None if mass_readback is None else {
                  'path': str(mass_readback),
                  'sha256': hashlib.sha256(mass_readback.read_bytes()).hexdigest(),
                  'properties': profile},
              'scope': 'Source-bound native prototype. Authored mass properties require fresh '
                       'runtime verification in both generated conditions.'}
    (output / 'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--blender', type=Path)
    parser.add_argument('--mass-readback', type=Path)
    parser.add_argument('--blender-phase', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    if args.blender_phase:
        blender_phase(args.source, args.output)
    else:
        if args.blender is None:
            parser.error('--blender is required')
        build(args.source.resolve(), args.blender, args.output.resolve(), args.mass_readback)
