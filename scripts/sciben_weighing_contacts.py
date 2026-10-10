#!/usr/bin/env python3
"""Source-bound static cavity and collision inventory; never changes USD assets.

This does not cook PhysX shapes or qualify robot contacts. Use the generated
inventory to select contact traces rather than guessing offset corrections.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

BOTTLE = '/World/obj_weighing_bottle_body'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def triangulate(counts, indices):
    result, cursor = [], 0
    for count in counts:
        face = indices[cursor:cursor + count]
        result.extend((face[0], face[i], face[i + 1]) for i in range(1, count - 1))
        cursor += count
    return np.asarray(result, dtype=np.int64).reshape(-1, 3)


def topology(faces):
    directed = Counter((int(a), int(b)) for f in faces for a, b in zip(f, np.roll(f, -1)))
    undirected = Counter()
    for (a, b), n in directed.items():
        undirected[tuple(sorted((a, b)))] += n
    boundary = sum(n == 1 for n in undirected.values())
    nonmanifold = sum(n > 2 for n in undirected.values())
    inconsistent = sum(directed[(a, b)] != directed[(b, a)] for a, b in undirected)
    return dict(boundary_edges=boundary, nonmanifold_edges=nonmanifold,
                inconsistently_oriented_edges=inconsistent,
                closed_two_manifold=bool(undirected) and not (boundary or nonmanifold))


def vertical_hits(points, faces, xy):
    """Intersections with the infinite vertical line, deduplicating shared edges."""
    triangles = points[faces]
    a, u, v = triangles[:, 0], triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    delta = np.asarray(xy) - a[:, :2]
    determinant = u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]
    valid = np.abs(determinant) > 1e-16
    alpha = np.zeros(len(a)); beta = np.zeros(len(a))
    alpha[valid] = (delta[valid, 0] * v[valid, 1] - delta[valid, 1] * v[valid, 0]) / determinant[valid]
    beta[valid] = (u[valid, 0] * delta[valid, 1] - u[valid, 1] * delta[valid, 0]) / determinant[valid]
    valid &= (alpha >= -1e-9) & (beta >= -1e-9) & (alpha + beta <= 1 + 1e-9)
    hits = sorted((a[:, 2] + alpha * u[:, 2] + beta * v[:, 2])[valid])
    return [float(z) for i, z in enumerate(hits) if i == 0 or abs(z - hits[i - 1]) > 1e-8]


def mesh_data(prim):
    from pxr import UsdGeom
    mesh = UsdGeom.Mesh(prim)
    points = np.asarray(mesh.GetPointsAttr().Get(), dtype=np.float64)
    faces = triangulate(list(mesh.GetFaceVertexCountsAttr().Get()), list(mesh.GetFaceVertexIndicesAttr().Get()))
    return points, faces


def audit(path):
    from pxr import Usd, UsdGeom, UsdPhysics
    stage = Usd.Stage.Open(str(path))
    if stage is None:
        raise ValueError(f'Cannot open {path}')
    result = {'path': str(Path(path).resolve()), 'sha256': sha(path),
              'meters_per_unit': UsdGeom.GetStageMetersPerUnit(stage),
              'scope': 'static_authored_geometry_and_schema_only', 'objects': []}
    root = stage.GetPrimAtPath('/World')
    for obj in root.GetChildren():
        colliders, rigid, geometry = [], [], []
        for prim in Usd.PrimRange(obj):
            if prim.IsA(UsdGeom.Gprim):
                geometry.append(str(prim.GetPath()))
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                rigid.append({'path': str(prim.GetPath()), 'mass_kg': UsdPhysics.MassAPI(prim).GetMassAttr().Get()})
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                colliders.append({'path': str(prim.GetPath()),
                                  'enabled': UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get(),
                                  'approximation': UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get(),
                                  'contact_offset': prim.GetAttribute('physxCollision:contactOffset').Get(),
                                  'rest_offset': prim.GetAttribute('physxCollision:restOffset').Get()})
        result['objects'].append({'path': str(obj.GetPath()), 'geometry_count': len(geometry),
                                  'rigid_bodies': rigid, 'colliders': colliders,
                                  'enabled_collider_count': sum(c['enabled'] is not False for c in colliders)})
    body = stage.GetPrimAtPath(BOTTLE + '/PhysicsCollision/BodySDF')
    if body:
        points, faces = mesh_data(body)
        visual_points, visual_faces = mesh_data(stage.GetPrimAtPath(BOTTLE + '/Geometry/WeighingBottleBody'))
        profile = []
        for z in np.unique(points[:, 2]):
            radius = np.linalg.norm(points[points[:, 2] == z, :2], axis=1)
            profile.append({'z_m': float(z), 'min_radius_m': float(radius.min()), 'max_radius_m': float(radius.max())})
        result['bottle'] = {'collision_path': str(body.GetPath()), 'points': len(points), 'triangles': len(faces),
                            'mesh_sha256': hashlib.sha256(points.tobytes() + faces.tobytes()).hexdigest(),
                            'bounds_local_m': [points.min(0).tolist(), points.max(0).tolist()],
                            'topology': topology(faces), 'profile': profile,
                            'visual_collider_geometry_equal': np.array_equal(points, visual_points) and np.array_equal(faces, visual_faces),
                            'vertical_intersections_m': {str(xy): vertical_hits(points, faces, xy) for xy in [(0.001321, 0.002411), (0.01, 0.005), (0.02, 0.002)]}}
    return result


BACKGROUND_PATHS = tuple('/World/obj_r9_' + name for name in (
    'amber_bottle', 'tip_box', 'wash_bottle', 'clear_bottle', 'pipette_carousel'))


def author_background_candidate(source, output, object_paths=BACKGROUND_PATHS):
    """Author only missing tabletop collisions; no pose/mesh/material overrides.

    Caller must validate this candidate in the intended robot runtime. The
    layer deliberately has no source sublayer, so the consumer composes it over
    its own source-bound scene rather than importing the old task contents.
    """
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics
    stage = Usd.Stage.Open(str(source))
    paths = []
    for path in object_paths:
        root = stage.GetPrimAtPath(path)
        if not root:
            raise ValueError(f'Missing source object: {path}')
        ancestor = root.GetParent()
        while ancestor and not ancestor.IsPseudoRoot():
            if ancestor.HasAPI(UsdPhysics.RigidBodyAPI):
                raise ValueError(f'Dynamic background ancestor: {ancestor.GetPath()}')
            if ancestor.HasAPI(UsdPhysics.CollisionAPI):
                raise ValueError(f'Existing collision ancestor requires review: {ancestor.GetPath()}')
            ancestor = ancestor.GetParent()
        for prim in Usd.PrimRange(root):
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                raise ValueError(f'Dynamic background is outside static candidate scope: {prim.GetPath()}')
            if prim.IsA(UsdGeom.Gprim):
                if prim.GetTypeName() not in ('Mesh', 'Cube', 'Cylinder', 'Cone', 'Sphere', 'Capsule'):
                    raise ValueError(f'Unsupported background shape: {prim.GetPath()}')
                if prim.HasAPI(UsdPhysics.CollisionAPI):
                    raise ValueError(f'Existing collision opinion requires review: {prim.GetPath()}')
                paths.append((str(prim.GetPath()), prim.IsA(UsdGeom.Mesh)))
    layer = Sdf.Layer.CreateNew(str(output))
    patch = Usd.Stage.Open(layer)
    for path, is_mesh in paths:
        prim = patch.OverridePrim(path)
        UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
        if is_mesh:
            UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr('none')
    layer.Save()
    return {'source': str(source), 'source_sha256': sha(source),
            'layer': str(output), 'layer_sha256': sha(output),
            'paths': [p for p, _ in paths], 'shape_count': len(paths),
            'status': 'STATIC_CANDIDATE_REQUIRES_ROBOT_RUNTIME_VALIDATION',
            'scope': 'exact static geometry on explicitly selected tabletop background props',
            'object_roots': list(object_paths),
            'unchanged': ['all visible geometry', 'poses', 'materials', 'task objects',
                          'masses', 'collision offsets', 'room', 'balance articulation']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    reports = [audit(p) for p in args.source]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({'status': 'STATIC_AUDIT_ONLY', 'producer_script_sha256': sha(__file__),
                                  'runtime_validation': False, 'repair_authored': False, 'scenes': reports}, indent=2) + '\n')


if __name__ == '__main__':
    main()
