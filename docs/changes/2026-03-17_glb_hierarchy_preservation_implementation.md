# 2026-03-17 GLB Hierarchy Preservation Implementation

## Summary

This change replaces the old flat `USD -> GLB` export path with a hierarchy-preserving scene-graph export path.

The goal of the implementation is **static pose fidelity**:

- preserve parent-child `Xform` relationships
- preserve mesh local transforms through glTF node matrices
- keep articulated assets visually correct in the exported GLB

This change does **not** attempt to preserve USD physics, articulation, or joint schemas inside GLB.

## Code Changes

- Added `convert_asset/glb/usd_scene.py`
  - extracts exported nodes
  - preserves parent-child relationships
  - computes local matrices
  - inserts a synthetic root node for Z-up stages
- Updated `convert_asset/glb/writer.py`
  - added explicit scene-root and child-attachment APIs
  - preserved compatibility with flat-path callers through `add_to_scene_root`
- Updated `convert_asset/glb/converter.py`
  - now orchestrates scene-graph extraction before mesh conversion
  - creates nodes separately from mesh payloads
  - resets internal state per `process_stage(...)`
- Updated `convert_asset/glb/usd_mesh.py`
  - geometry extraction now stays in mesh-local space
  - stage/root up-axis correction is no longer baked into vertices
- Added `tests/glb/test_hierarchy_export.py`
  - covers Z-up synthetic-root behavior
  - covers articulated direct export
  - covers articulated export without negative scale
  - covers a rigid control asset

## Design Decisions

### 1. Use glTF node matrices instead of TRS decomposition

Version 1 of the fix uses `node.matrix` directly.

Reasons:

- avoids early bugs around quaternion / scale decomposition
- handles negative scale more safely
- keeps the migration focused on hierarchy correctness first

### 2. Use a synthetic root node for Z-up stages

The old exporter rotated each mesh's vertices directly.

The new exporter inserts one synthetic root node when `UsdGeom.GetStageUpAxis(stage) == "Z"`.

This keeps:

- mesh geometry in local space
- hierarchy semantics consistent
- stage up-axis correction isolated to one place

### 3. Keep `P0` scope limited

This implementation intentionally does **not** expand support to:

- `PointInstancer`
- `Skel` / `Skeleton`
- `instance proxy`
- non-triangle meshes
- articulation physics round-trip

Those remain separate follow-up items.

## Validation

### Automated

```bash
./scripts/isaac_python.sh -m unittest discover -s tests/glb -p 'test_*.py'
```

Result:

- `4` tests passed
- covered Z-up, articulated hierarchy, articulated non-negative-scale, and rigid control cases

### Manual

```bash
./scripts/isaac_python.sh ./main.py export-glb \
  assets/usd/chestofdrawers_nomdl/chestofdrawers_0004/instance_noMDL.usd \
  --out /tmp/chest0004_export.glb

./scripts/isaac_python.sh ./main.py usd-to-glb \
  assets/usd/chestofdrawers_nomdl/chestofdrawers_0004/instance.usd \
  --out /tmp/chest0004_pipeline.glb
```

Observed result:

- both commands succeeded
- both exports produced `34` nodes / `25` meshes / `25` materials
- both exports produced `33` transform nodes
- both exports had a single scene root instead of a flat root list of all meshes

## Residual Risks

- vertex normals are still only emitted when `len(normals) == len(points)`
- negative-scale shading / mirrored normal-map behavior is still a follow-up risk
- `purpose`, `visibility`, `PointInstancer`, and `Skel` semantics are still not expanded in this change

## Follow-up

- decide whether `purpose/proxy/guide` filtering should be aligned with mesh tooling
- add synthetic fixtures for unsupported-but-important categories
- investigate tangent / mirrored normal-map behavior on negative-scale assets
