#!/usr/bin/env python3
"""Source-bound, static-only task09 contact and grain sleep candidate overlays."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    """Return SHA256 for the source or small producer output."""
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def build_profiles(source, out):
    """Write independent contact and sleep overrides; never mutate the source."""
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics

    source, out = Path(source).resolve(), Path(out).resolve()
    source_hash = digest(source)
    stage = Usd.Stage.Open(str(source))
    if UsdGeom.GetStageMetersPerUnit(stage) != 1.0:
        raise ValueError('This task-specific profile requires a meter-unit stage')
    roots = [f'/World/obj_grain_{index:02d}' for index in range(1, 6)]
    bodies = [*roots, '/World/obj_weighing_boat']
    colliders, originals = [], {}
    for path in bodies:
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            raise ValueError(f'missing rigid body {path}')
        found = []
        for child in Usd.PrimRange(prim):
            if child.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(child).GetCollisionEnabledAttr().Get():
                found.append(str(child.GetPath()))
                originals[str(child.GetPath())] = {
                    name: child.GetAttribute(name).Get() for name in ['physxCollision:contactOffset', 'physxCollision:restOffset']
                }
        if not found:
            raise ValueError(f'no enabled colliders under {path}')
        colliders.extend(found)
    out.mkdir(parents=True, exist_ok=True)
    contact_path = out / 'contact_1mm.usda'
    contact = Usd.Stage.CreateNew(str(contact_path))
    for path in colliders:
        prim = contact.OverridePrim(path)
        prim.SetMetadata('apiSchemas', Sdf.TokenListOp.Create(prependedItems=['PhysxCollisionAPI']))
        prim.CreateAttribute('physxCollision:contactOffset', Sdf.ValueTypeNames.Float, custom=False).Set(0.001)
        prim.CreateAttribute('physxCollision:restOffset', Sdf.ValueTypeNames.Float, custom=False).Set(0.0)
    contact.GetRootLayer().Save()
    sleep_path = out / 'grain_sleep.usda'
    sleep = Usd.Stage.CreateNew(str(sleep_path))
    for path in roots:
        prim = sleep.OverridePrim(path)
        prim.SetMetadata('apiSchemas', Sdf.TokenListOp.Create(prependedItems=['PhysxRigidBodyAPI']))
        prim.CreateAttribute('physxRigidBody:sleepThreshold', Sdf.ValueTypeNames.Float, custom=False).Set(5e-4)
        prim.CreateAttribute('physxRigidBody:stabilizationThreshold', Sdf.ValueTypeNames.Float, custom=False).Set(5e-5)
    sleep.GetRootLayer().Save()
    if digest(source) != source_hash:
        raise RuntimeError('source changed while producing candidates')
    report = {
        'format': 'convertasset.task09.contact-sleep-candidates.v1',
        'source': str(source), 'source_sha256': source_hash,
        'producer_sha256': digest(__file__), 'collider_paths': colliders,
        'original_collider_values': originals, 'grain_body_paths': roots,
        'original_grain_thresholds': {path: {name: stage.GetPrimAtPath(path).GetAttribute(name).Get()
            for name in ['physxRigidBody:sleepThreshold', 'physxRigidBody:stabilizationThreshold']} for path in roots},
        'candidates': [
            {'layer': contact_path.name, 'sha256': digest(contact_path),
             'contact_offset_m': 0.001, 'rest_offset_m': 0, 'runtime_qualified': False},
            {'layer': sleep_path.name, 'sha256': digest(sleep_path),
             'sleep_threshold': 5e-4, 'stabilization_threshold': 5e-5, 'runtime_qualified': False},
        ],
        'usage': 'Compose either or both layers stronger than the scene and mass profile; the two candidates have disjoint property opinions.',
        'limits': ['Static-only candidates; no claim of stability, compiler qualification or runtime equivalence.',
                   'No geometry, mass, transforms, inertia, kinematic state, velocities or runtime wake behavior changed.',
                   'Sleep thresholds are energy-per-unit-mass parameters, not a velocity cutoff; runtime tests must distinguish sleeping from forced freezing.'],
    }
    (out / 'contact_profiles.json').write_text(json.dumps(report, indent=2) + '\n')
    return report



def build_solver_profile(source, balance_source, out):
    """Produce solver-only opinions bound to task09 bodies and task14 balance."""
    from pxr import Sdf, Usd, UsdPhysics

    source, balance_source, out = Path(source).resolve(), Path(balance_source).resolve(), Path(out).resolve()
    stages = {'task09': Usd.Stage.Open(str(source)), 'task14': Usd.Stage.Open(str(balance_source))}
    source_paths = {'task09': source, 'task14': balance_source}
    bindings = [{'role': role, 'path': str(path), 'sha256': digest(path),
                 'used_layers': [{'path': layer.realPath, 'sha256': digest(layer.realPath)}
                                 for layer in stages[role].GetUsedLayers() if layer.realPath]}
                for role, path in source_paths.items()]
    balance = '/World/obj_analytical_balance'
    specs = [(f'/World/obj_grain_{i:02d}', 'task09', 'physxRigidBody', 'PhysxRigidBodyAPI') for i in range(1, 6)]
    specs.extend([
        ('/World/obj_weighing_boat', 'task09', 'physxRigidBody', 'PhysxRigidBodyAPI'),
        (balance, 'task14', 'physxArticulation', 'PhysxArticulationAPI'),
        (balance + '/Instance/WeighingPan', 'task14', 'physxRigidBody', 'PhysxRigidBodyAPI'),
    ])
    targets = []
    for path, role, namespace, api in specs:
        prim = stages[role].GetPrimAtPath(path)
        expected = UsdPhysics.ArticulationRootAPI if namespace == 'physxArticulation' else UsdPhysics.RigidBodyAPI
        if not prim or not prim.HasAPI(expected):
            raise ValueError(f'{role} missing expected physics target {path}')
        targets.append({'path': path, 'source_role': role, 'namespace': namespace,
                        'original': {suffix: prim.GetAttribute(namespace + ':' + suffix).Get()
                                     for suffix in ['solverPositionIterationCount', 'solverVelocityIterationCount']}})
    out.mkdir(parents=True, exist_ok=True)
    target = out / 'solver64_32.usda'
    overlay = Usd.Stage.CreateNew(str(target))
    overlay.GetRootLayer().customLayerData = {
        'producer': 'ConvertAsset task09 solver candidate',
        'qualification': 'static_only_not_runtime_qualified',
        'source_task09_sha256': bindings[0]['sha256'],
        'source_task14_sha256': bindings[1]['sha256'],
        'provenance_manifest': 'solver_profiles.json',
    }
    for path, role, namespace, api in specs:
        prim = overlay.OverridePrim(path)
        prim.SetMetadata('apiSchemas', Sdf.TokenListOp.Create(prependedItems=[api]))
        prim.CreateAttribute(namespace + ':solverPositionIterationCount', Sdf.ValueTypeNames.Int, custom=False).Set(64)
        prim.CreateAttribute(namespace + ':solverVelocityIterationCount', Sdf.ValueTypeNames.Int, custom=False).Set(32)
    overlay.GetRootLayer().Save()
    for binding in bindings:
        if digest(binding['path']) != binding['sha256']:
            raise RuntimeError('source changed during solver profile generation')
    report = {
        'format': 'convertasset.task09.solver-candidate.v1',
        'source_bindings': bindings, 'targets': targets, 'layer': target.name,
        'layer_sha256': digest(target), 'producer_sha256': digest(__file__),
        'solver_position_iteration_count': 64, 'solver_velocity_iteration_count': 32,
        'runtime_qualified': False,
        'consumer': 'Compose stronger than the merged task09 scene with task14 balance. Compatible with independent mass/contact/sleep overlays.',
        'limits': ['Static target/schema and source-hash checks only; no GPU run or stability claim.',
                   'Only solver iteration attributes and relevant API metadata are authored; no joint, geometry, mass, kinematic or velocity changes.'],
    }
    (out / 'solver_profiles.json').write_text(json.dumps(report, indent=2) + '\n')
    return report

def main():
    """Generate both optional A/B profile layers and their evidence manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--balance-source', type=Path, help='Generate solver-only profile bound to this task14 source')
    args = parser.parse_args()
    if args.balance_source:
        report = build_solver_profile(args.source, args.balance_source, args.out)
        print(json.dumps({'out': str(args.out), 'layer': report['layer'], 'targets': report['targets']}, indent=2))
        return
    report = build_profiles(args.source, args.out)
    print(json.dumps({'out': str(args.out), 'collider_paths': report['collider_paths'],
                      'candidates': report['candidates']}, indent=2))


if __name__ == '__main__':
    main()
