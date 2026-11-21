#!/usr/bin/env python3
"""Build a common inner-support collider for bounded gear acquisition diagnostics."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def blender_phase(config, output):
    import bpy

    data = json.loads(config.read_text())
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=data['radius'], depth=0.01,
                                       location=(*data['center_xy'], data['top_z']-0.005))
    obj = bpy.context.object
    payload = {'points': [list(obj.matrix_world @ v.co) for v in obj.data.vertices],
               'faces': [list(p.vertices) for p in obj.data.polygons],
               'blender_version': bpy.app.version_string}
    (output/'support_mesh.json').write_text(json.dumps(payload))
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'support.blend'))


def build(manifest_path, layout_path, blender, output, radius, align_initial_pose=False):
    import numpy as np
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

    if not 0.006 <= radius <= 0.014:
        raise ValueError('Support radius must be 6–14 mm; runtime contact-region checks are required')
    manifest = json.loads(manifest_path.read_text())
    layout = json.loads(layout_path.read_text())['task_data']['initial_layout']['04']
    if not np.allclose(layout['scale'], [1, 1, 1]):
        raise ValueError('This probe requires unit-scale gear instances')
    source = Usd.Stage.Open(manifest['source'])
    root = source.GetDefaultPrim().GetPath()
    root_matrix = UsdGeom.XformCache().GetLocalToWorldTransform(source.GetPrimAtPath(root))
    if not np.allclose(np.array(root_matrix), np.eye(4)):
        raise ValueError('Source root transform must be identity')
    table = source.GetPrimAtPath(root.AppendPath('obj_table/table'))
    points = UsdGeom.Mesh(table).GetPointsAttr().Get()
    matrix = UsdGeom.XformCache().GetLocalToWorldTransform(table)
    top = max(matrix.Transform(Gf.Vec3d(*v))[2] for v in points)
    q = layout['orientation']
    offset = Gf.Quatd(q[0], Gf.Vec3d(*q[1:])).Transform(Gf.Vec3d(0.02025, 0, 0))
    center = np.array(layout['position']) + np.array(offset)
    material_targets = table.GetRelationship('material:binding:physics').GetTargets()
    if len(material_targets) != 1:
        raise ValueError('Require one source table physics material')
    material = UsdPhysics.MaterialAPI(source.GetPrimAtPath(material_targets[0]))
    material_values = {'static_friction': material.GetStaticFrictionAttr().Get(),
                       'dynamic_friction': material.GetDynamicFrictionAttr().Get(),
                       'restitution': material.GetRestitutionAttr().Get()}
    for row in manifest['conditions']:
        content = Path(row['scene']).with_suffix('.usd')
        if hashlib.sha256(content.read_bytes()).hexdigest() != row['content_sha256']:
            raise ValueError('Producer geometry changed')
    output.mkdir(parents=True, exist_ok=False)
    config = output/'support_input.json'
    config.write_text(json.dumps({'radius': radius, 'center_xy': center[:2].tolist(), 'top_z': top}))
    with (output/'blender.log').open('w') as log:
        subprocess.run([str(blender), '--background', '--factory-startup', '--python',
                        str(Path(__file__).resolve()), '--', '--blender-phase', '--input',
                        str(config), '--output', str(output)], check=True, timeout=180,
                       stdout=log, stderr=subprocess.STDOUT)
    mesh_data = json.loads((output/'support_mesh.json').read_text())
    mesh_points = np.array(mesh_data['points'])
    if abs(mesh_points[:, 2].max()-top) > 1e-7:
        raise ValueError('Support top differs from source table')
    if np.linalg.norm(mesh_points[:, :2]-center[:2], axis=1).max() > radius+1e-7:
        raise ValueError('Support extends beyond declared radius')
    results = []
    for row in manifest['conditions']:
        condition = row['condition']
        directory = output/condition
        directory.mkdir()
        stage = Usd.Stage.CreateNew(str(directory/'scene.usd'))
        stage.GetRootLayer().subLayerPaths = [str(Path(row['scene']).with_suffix('.usd').resolve())]
        stage.SetDefaultPrim(stage.GetPrimAtPath(root))
        target = stage.OverridePrim(root.AppendChild('obj_04'))
        if align_initial_pose:
            transform = Gf.Transform()
            transform.SetTranslation(Gf.Vec3d(*layout['position']))
            transform.SetRotation(Gf.Rotation(Gf.Quatd(layout['orientation'][0],
                                                        Gf.Vec3d(*layout['orientation'][1:]))))
            transform.SetScale(Gf.Vec3d(*layout['scale']))
            UsdGeom.Xformable(target).MakeMatrixXform().Set(transform.GetMatrix())
        if UsdPhysics.FilteredPairsAPI(target).GetFilteredPairsRel().GetTargets():
            raise ValueError('Unexpected inherited collision filtering')
        UsdPhysics.FilteredPairsAPI.Apply(target).CreateFilteredPairsRel().SetTargets(
            [root.AppendChild('obj_table')])
        support = UsdGeom.Xform.Define(stage, root.AppendChild('initial_support_probe')).GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(support).CreateKinematicEnabledAttr().Set(True)
        support.SetMetadata('apiSchemas', Sdf.TokenListOp.Create(
            prependedItems=['PhysicsRigidBodyAPI', 'PhysxContactReportAPI']))
        support.CreateAttribute('physxContactReport:threshold', Sdf.ValueTypeNames.Float).Set(0.)
        mesh = UsdGeom.Mesh.Define(stage, support.GetPath().AppendChild('collider'))
        mesh.GetPointsAttr().Set(Vt.Vec3fArray.FromNumpy(mesh_points.astype(np.float32)))
        mesh.GetFaceVertexCountsAttr().Set([len(face) for face in mesh_data['faces']])
        mesh.GetFaceVertexIndicesAttr().Set([i for face in mesh_data['faces'] for i in face])
        mesh.GetExtentAttr().Set(Vt.Vec3fArray.FromNumpy(
            np.array([mesh_points.min(0), mesh_points.max(0)], dtype=np.float32)))
        mesh.GetVisibilityAttr().Set('invisible')
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr().Set('convexHull')
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim())
        mesh.GetPrim().CreateRelationship('material:binding:physics').SetTargets(material_targets)
        group = UsdPhysics.CollisionGroup.Define(stage, root.AppendPath('support_filter_groups/support'))
        others = UsdPhysics.CollisionGroup.Define(stage, root.AppendPath('support_filter_groups/others'))
        group.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets([mesh.GetPath()])
        others.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets([root])
        others.GetCollidersCollectionAPI().CreateExcludesRel().SetTargets([target.GetPath(), support.GetPath()])
        group.CreateFilteredGroupsRel().SetTargets([others.GetPath()])
        for original in Usd.PrimRange(source.GetPrimAtPath(root.AppendChild('obj_table'))):
            current = stage.GetPrimAtPath(original.GetPath())
            for attr in original.GetAttributes():
                if attr.Get() != current.GetAttribute(attr.GetName()).Get():
                    raise ValueError('Original table changed')
        stage.GetRootLayer().Save()
        (directory/'scene.usda').write_text(Path(row['scene']).read_text())
        results.append({'condition': condition, 'scene': str(directory/'scene.usda'),
                        'content_sha256': hashlib.sha256((directory/'scene.usd').read_bytes()).hexdigest()})
    report = {'schema': 'convertasset.gear_support_probe.v1', 'conditions': results,
              'source_manifest': str(manifest_path),
              'source_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              'source_layout_sha256': hashlib.sha256(layout_path.read_bytes()).hexdigest(),
              'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'support_radius': radius, 'center_xy': center[:2].tolist(), 'top_z': top,
              'preload_target_pose_matches_task_layout': align_initial_pose,
              'physics_material': str(material_targets[0]), 'source_material_values': material_values,
              'support_collision_scope': 'target only; all other scene colliders filtered through collision groups',
              'blender_version': mesh_data['blender_version'],
              'scope': 'Acquisition-prefix diagnostic only. Target-original-table collisions excluded; '
                       'not a full-task benchmark asset or policy success condition.'}
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--layout', type=Path)
    parser.add_argument('--blender', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--radius', type=float, default=0.01)
    parser.add_argument('--blender-phase', action='store_true')
    parser.add_argument('--align-initial-pose', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    if args.blender_phase:
        blender_phase(args.input, args.output)
    else:
        if None in (args.manifest, args.layout, args.blender):
            parser.error('--manifest, --layout and --blender are required')
        build(args.manifest.resolve(), args.layout.resolve(), args.blender,
              args.output.resolve(), args.radius, args.align_initial_pose)
