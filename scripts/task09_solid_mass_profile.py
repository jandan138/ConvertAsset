#!/usr/bin/env python3
"""Audit task09 salt geometry and author mass-only USD candidate overlays.

This producer performs static geometry checks, never runtime qualification.
USD and NumPy imports are lazy so importing the entry point needs neither SDK.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

DENSITY_KG_M3 = 2160.0
DENSITY_SOURCE = 'https://www.sigmaaldrich.com/US/en/product/sial/s7653'


def closed_mesh_volume(points_m, triangles):
    """Return translated-origin signed volume after topology/winding checks.

The narrow producer accepts one closed triangular shell. It checks edge and
vertex manifoldness, rejects degenerate faces, and requires coherent winding.
It does not certify the absence of geometric self-intersection.
"""
    import numpy as np

    points = np.asarray(points_m, dtype=float)
    faces = np.asarray(triangles, dtype=int)
    if points.ndim != 2 or points.shape[1] != 3 or not np.all(np.isfinite(points)):
        raise ValueError('points must be finite Nx3 coordinates')
    if faces.ndim != 2 or faces.shape[1] != 3 or len(faces) < 4:
        raise ValueError('closed manifold requires triangular faces')
    if faces.min() < 0 or faces.max() >= len(points):
        raise ValueError('face index out of bounds')
    edges = defaultdict(list)
    links = defaultdict(lambda: defaultdict(set))
    for index, (a, b, c) in enumerate(faces):
        if len({int(a), int(b), int(c)}) != 3:
            raise ValueError('degenerate triangle')
        if np.linalg.norm(np.cross(points[b] - points[a], points[c] - points[a])) <= 1e-20:
            raise ValueError('degenerate triangle area')
        for u, v in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted((int(u), int(v))))].append((int(u), int(v), index))
        for u, v, w in ((a, b, c), (b, c, a), (c, a, b)):
            links[int(u)][int(v)].add(int(w))
            links[int(u)][int(w)].add(int(v))
    face_graph = defaultdict(set)
    for pair in edges.values():
        if len(pair) != 2:
            raise ValueError('mesh is not a closed edge manifold')
        if pair[0][:2] != pair[1][:2][::-1]:
            raise ValueError('mesh has inconsistent winding')
        face_graph[pair[0][2]].add(pair[1][2])
        face_graph[pair[1][2]].add(pair[0][2])

    def reachable(graph, start):
        seen, todo = set(), [start]
        while todo:
            value = todo.pop()
            if value not in seen:
                seen.add(value)
                todo.extend(graph[value] - seen)
        return seen

    if len(reachable(face_graph, 0)) != len(faces):
        raise ValueError('multiple closed shells require separate volume analysis')
    for ring in links.values():
        if any(len(neighbors) != 2 for neighbors in ring.values()) or len(reachable(ring, next(iter(ring)))) != len(ring):
            raise ValueError('mesh is not a vertex manifold')
    centered = points - points.mean(axis=0)
    signed = float(np.einsum('ij,ij->i', centered[faces[:, 0]], np.cross(centered[faces[:, 1]], centered[faces[:, 2]])).sum() / 6.0)
    if abs(signed) <= 1e-24:
        raise ValueError('mesh encloses zero volume')
    return {
        'volume_m3': abs(signed), 'signed_volume_m3': signed,
        'vertices': len(points), 'triangles': len(faces),
        'edge_manifold': True, 'vertex_manifold': True,
        'consistent_winding': True, 'connected_shells': 1,
        'self_intersection_checked': False,
        'world_bounds_size_m': (points.max(axis=0) - points.min(axis=0)).tolist(),
    }


def audit_body(stage, body_path, density_kg_m3):
    """Measure a body's single triangular mesh using its complete USD transform."""
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    body = stage.GetPrimAtPath(body_path)
    if not body or not body.HasAPI(UsdPhysics.RigidBodyAPI):
        raise ValueError(f'missing rigid body: {body_path}')
    meshes = [UsdGeom.Mesh(p) for p in Usd.PrimRange(body) if p.IsA(UsdGeom.Mesh)]
    if len(meshes) != 1:
        raise ValueError(f'{body_path}: expected exactly one physical solid mesh')
    mesh = meshes[0]
    if set(mesh.GetFaceVertexCountsAttr().Get()) != {3}:
        raise ValueError(f'{body_path}: only triangular source meshes supported')
    transform = UsdGeom.XformCache().GetLocalToWorldTransform(mesh.GetPrim())
    meters = UsdGeom.GetStageMetersPerUnit(stage)
    points = [[float(v) * meters for v in transform.Transform(Gf.Vec3d(*p))] for p in mesh.GetPointsAttr().Get()]
    indices = list(mesh.GetFaceVertexIndicesAttr().Get())
    result = closed_mesh_volume(points, [indices[i:i + 3] for i in range(0, len(indices), 3)])
    mass_api = UsdPhysics.MassAPI(body)
    kilograms = UsdPhysics.GetStageKilogramsPerUnit(stage)
    mass = float(mass_api.GetMassAttr().Get() or 0) * kilograms
    if mass <= 0:
        raise ValueError(f'{body_path}: expected explicit positive source mass')
    result.update({
        'body_path': body_path, 'mesh_path': str(mesh.GetPath()),
        'original_mass_kg': mass,
        'reference_mass_kg': result['volume_m3'] * density_kg_m3,
        'stage_meters_per_unit': meters, 'stage_kilograms_per_unit': kilograms,
        'world_transform': [[float(transform[i][j]) for j in range(4)] for i in range(4)],
        'original_diagonal_inertia_stage_units': list(mass_api.GetDiagonalInertiaAttr().Get() or (0, 0, 0)),
    })
    result['original_mass_reference_ratio'] = mass / result['reference_mass_kg']
    return result


def mass_candidates(reference_masses_kg, cap_kg=0.01):
    """Create the 1/2/5 decade sequence capped individually, plus 10g baseline."""
    import math

    if not reference_masses_kg or any(not math.isfinite(m) or m <= 0 for m in reference_masses_kg):
        raise ValueError('reference masses must be finite and positive')
    if not math.isfinite(cap_kg) or cap_kg <= 0:
        raise ValueError('mass cap must be finite and positive')
    results, decade = [], 1
    while True:
        for step in (1, 2, 5):
            multiplier = decade * step
            masses = [min(m * multiplier, cap_kg) for m in reference_masses_kg]
            results.append({'id': f'reference_x{multiplier}', 'requested_multiplier': multiplier, 'masses_kg': masses})
            if all(m == cap_kg for m in masses):
                results.append({'id': 'original_10g', 'requested_multiplier': None, 'masses_kg': [cap_kg] * len(masses)})
                return results
        decade *= 10


def write_mass_layer(path, bodies, masses_kg):
    """Write only mass opinions, scaling explicit inertia if the source has it."""
    from pxr import Gf, Usd, UsdPhysics

    if len(bodies) != len(masses_kg):
        raise ValueError('mass/body count mismatch')
    stage = Usd.Stage.CreateNew(str(path))
    for body, mass in zip(bodies, masses_kg):
        prim = stage.OverridePrim(body['body_path'])
        api = UsdPhysics.MassAPI.Apply(prim)
        api.CreateMassAttr(float(mass / body['stage_kilograms_per_unit']))
        inertia = body['original_diagonal_inertia_stage_units']
        if any(inertia):
            if not all(v > 0 for v in inertia):
                raise ValueError('partially specified inertia requires manual audit')
            api.CreateDiagonalInertiaAttr(Gf.Vec3f(*(v * mass / body['original_mass_kg'] for v in inertia)))
    stage.GetRootLayer().Save()


def sha256(path):
    """Return a file content digest without loading it wholly into memory."""
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    """Produce five-grain source-bound audit JSON and independent USD overlays."""
    from pxr import Usd

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    stage = Usd.Stage.Open(str(source))
    bodies = [audit_body(stage, f'/World/obj_grain_{i:02d}', DENSITY_KG_M3) for i in range(1, 6)]
    candidates = mass_candidates([body['reference_mass_kg'] for body in bodies])
    args.out.mkdir(parents=True, exist_ok=True)
    for candidate in candidates:
        path = args.out / f"{candidate['id']}.usda"
        write_mass_layer(path, bodies, candidate['masses_kg'])
        candidate.update({'layer': path.name, 'sha256': sha256(path), 'total_mass_kg': sum(candidate['masses_kg']),
                          'actual_reference_ratios': [m / b['reference_mass_kg'] for m, b in zip(candidate['masses_kg'], bodies)],
                          'runtime_qualified': False})
    used_layers = [{'path': layer.realPath, 'sha256': sha256(layer.realPath)} for layer in stage.GetUsedLayers() if layer.realPath]
    report = {
        'format': 'convertasset.task09.solid-mass-profile.v1',
        'source': str(source), 'source_sha256': sha256(source),
        'producer_script_sha256': sha256(__file__), 'used_source_layers': sorted(used_layers, key=lambda x: x['path']),
        'density_kg_m3': DENSITY_KG_M3, 'density_source': DENSITY_SOURCE,
        'density_source_accessed': '2026-10-08', 'density_temperature_c': 25,
        'material_assumption': 'Pure solid NaCl; source SaltWhite material name is suggestive, not chemical identification.',
        'volume_method': 'Closed, coherently wound triangle signed tetrahedral sum after full world transform and stage units; centroid translation for conditioning.',
        'limits': ['No geometric self-intersection test.', 'No runtime stability or collision qualification.', 'Source zero inertia remains simulator auto-computed; positive explicit inertia scales proportionally with mass.', 'Do not reuse after changing mesh or world scale without regeneration.'],
        'bodies': bodies, 'candidates': candidates,
        'consumer': 'Compose one candidate layer stronger than the task scene. It contains no source path, dependencies, transforms, collision edits, or geometry.',
    }
    (args.out / 'mass_profiles.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'manifest': str(args.out / 'mass_profiles.json'), 'reference_masses_g': [b['reference_mass_kg'] * 1000 for b in bodies], 'candidate_ids': [c['id'] for c in candidates]}, indent=2))


if __name__ == '__main__':
    main()
