#!/usr/bin/env python3
"""Author audited closed lower-SDF / convex-rim partition, no simulator run."""
import argparse
import hashlib
import json
from pathlib import Path


def authored_api_tokens(prim):
    """Preserve runtime-specific API tokens even when this USD registry lacks them."""
    metadata = prim.GetMetadata('apiSchemas')
    if metadata is None:
        return []
    assert metadata.isExplicit, 'Composed API metadata must be explicit'
    return list(metadata.explicitItems)


def is_collision_downgrade(line):
    text = line.lower()
    return (('falling back' in text or 'downgrade' in text)
            and ('convexhull' in text or 'convex hull' in text
                 or 'parse collision' in text or 'collision approximation' in text))


def build(source, audit_dir, out):
    import numpy as np
    from pxr import Usd, UsdGeom, UsdPhysics, Sdf, Gf, Vt
    source, audit_dir, out = map(lambda p: Path(p).resolve(), (source, audit_dir, out))
    out.mkdir(exist_ok=False)
    old = Usd.Stage.Open(str(source))
    original_path = '/World/_scene/obj_sample_tube/Visual/GlassShell'
    original = old.GetPrimAtPath(original_path)
    assert original.GetAttribute('physics:collisionEnabled').Get()
    assert abs(original.GetAttribute('physxSDFMeshCollision:sdfMargin').Get() - .01) < 1e-8
    assert old.GetPrimAtPath('/World/_scene/obj_sample_tube').GetAttribute('physxRigidBody:enableSpeculativeCCD').Get()
    assert old.GetPrimAtPath('/World/_scene/table/obj_table/table/Cube').GetAttribute('physics:approximation').Get() == 'convexHull'
    meshes = np.load(audit_dir / 'clipped_meshes.npz')
    parts = json.loads((audit_dir / 'proposed_rim_parts.json').read_text())
    proof = json.loads((audit_dir / 'feasibility.json').read_text())
    assert len(parts) == 24 and proof['all24pieces_closed_consistently_wound']
    physics_attrs = [(a.GetName(), a.GetTypeName(), a.Get()) for a in original.GetAttributes()
                     if a.GetName().startswith(('physics:', 'physx'))]
    schemas = authored_api_tokens(original)
    assert {'PhysxCollisionAPI', 'PhysxSDFMeshCollisionAPI'} <= set(schemas)

    def author(stage, root):
        targets = []
        full = stage.OverridePrim(root + '/obj_sample_tube/Visual/GlassShell')
        full.CreateAttribute('physics:collisionEnabled', Sdf.ValueTypeNames.Bool).Set(False)
        for name, verts, faces, sdf in [('LowerSDF', meshes['lower_vertices'], meshes['lower_faces'], True)] + [
                (f'Rim_{i:02d}', np.array(p['vertices']), np.array(p['triangles']), False)
                for i, p in enumerate(parts)]:
            path = root + '/obj_sample_tube/RimPartition/' + name
            mesh = UsdGeom.Mesh.Define(stage, path)
            prim = mesh.GetPrim()
            prim.SetMetadata('apiSchemas', Sdf.TokenListOp.CreateExplicit(schemas if sdf else [
                'PhysicsCollisionAPI', 'PhysicsMeshCollisionAPI', 'PhysxCollisionAPI', 'MaterialBindingAPI']))
            mesh.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*v) for v in verts]))
            mesh.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(faces)))
            mesh.CreateFaceVertexIndicesAttr(Vt.IntArray(faces.ravel().tolist()))
            mesh.CreateSubdivisionSchemeAttr('none')
            mesh.CreateVisibilityAttr('invisible')
            mesh.CreateExtentAttr(Vt.Vec3fArray([Gf.Vec3f(*verts.min(0)), Gf.Vec3f(*verts.max(0))]))
            for key, typ, value in physics_attrs:
                if sdf or not key.startswith('physxSDF'):
                    prim.CreateAttribute(key, typ).Set(value)
            prim.CreateAttribute('physics:collisionEnabled', Sdf.ValueTypeNames.Bool).Set(True)
            prim.CreateAttribute('physics:approximation', Sdf.ValueTypeNames.Token).Set('sdf' if sdf else 'convexHull')
            for rel in original.GetRelationships():
                if rel.GetName().startswith('material:'):
                    prim.CreateRelationship(rel.GetName()).SetTargets([
                        str(p).replace('/World/_scene', root, 1) for p in rel.GetTargets()])
            targets.append(path)
        for system in ['Sample', 'Bath']:
            p = stage.OverridePrim(root + '/WaterbathFluid/' + system + 'System')
            p.CreateRelationship('physics:filteredPairs').SetTargets(targets)
        return targets

    delta = Usd.Stage.CreateNew(str(out / 'rim_partition_delta.usda'))
    author(delta, '/World'); delta.GetRootLayer().Save()
    stage = Usd.Stage.CreateNew(str(out / 'scene.usda'))
    stage.GetRootLayer().subLayerPaths = [str(source)]
    targets = author(stage, '/World/_scene'); stage.GetRootLayer().Save()
    attr_changes, rel_changes = [], []
    for p in old.Traverse():
        new = stage.GetPrimAtPath(p.GetPath())
        assert new and authored_api_tokens(p) == authored_api_tokens(new)
        for a in p.GetAttributes():
            if str(a.Get()) != str(new.GetAttribute(a.GetName()).Get()):
                attr_changes.append(str(a.GetPath()))
        for r in p.GetRelationships():
            if r.GetTargets() != new.GetRelationship(r.GetName()).GetTargets():
                rel_changes.append(str(r.GetPath()))
    assert attr_changes == [original_path + '.physics:collisionEnabled'], attr_changes
    assert set(rel_changes) == {'/World/_scene/WaterbathFluid/' + t + 'System.physics:filteredPairs' for t in ['Sample', 'Bath']}, rel_changes
    enabled = [p for p in Usd.PrimRange(stage.GetPrimAtPath('/World/_scene/obj_sample_tube'))
               if p.HasAPI(UsdPhysics.CollisionAPI) and p.GetAttribute('physics:collisionEnabled').Get()]
    assert len(enabled) == 498, len(enabled)
    assert authored_api_tokens(stage.GetPrimAtPath('/World/_scene/obj_sample_tube/RimPartition/LowerSDF')) == schemas
    assert sum(str(p.GetPath()).startswith('/World/_scene/obj_sample_tube/RimPartition/') for p in enabled) == 25
    for t in ['Sample', 'Bath']:
        assert [str(x) for x in stage.GetPrimAtPath('/World/_scene/WaterbathFluid/' + t + 'System').GetRelationship('physics:filteredPairs').GetTargets()] == targets
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    result = {'status': 'STATIC_PARTITION_PASS_RUNTIME_PENDING', 'qualified': False,
              'source': str(source), 'source_sha256': sha(source),
              'delta': str(out / 'rim_partition_delta.usda'), 'delta_sha256': sha(out / 'rim_partition_delta.usda'),
              'scene': str(out / 'scene.usda'), 'scene_sha256': sha(out / 'scene.usda'),
              'old_attr_changes': attr_changes, 'old_rel_changes': rel_changes,
              'tube_enabled_colliders': 498, 'tube_rigid': 25, 'tube_PBD_only': 473,
              'particle_filter_count_each': 25, 'targets': targets,
              'lower_SDF_complete_apiSchemas': schemas, 'original_full_SDF_disabled': True, 'visual_mass_COM_I_unchanged': True,
              'margin': .01, 'narrowBand': .01, 'resolution': 512, 'speculativeCCD': True,
              'static_geometry_proof': str(audit_dir / 'feasibility.json'),
              'static_geometry_proof_sha256': sha(audit_dir / 'feasibility.json'),
              'script_sha256': sha(__file__), 'limits': proof['risks']}
    (out / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'delta_sha256', 'tube_enabled_colliders', 'particle_filter_count_each']}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--source', required=True); p.add_argument('--audit-dir', required=True); p.add_argument('--out', required=True)
    a = p.parse_args(); build(a.source, a.audit_dir, a.out)
