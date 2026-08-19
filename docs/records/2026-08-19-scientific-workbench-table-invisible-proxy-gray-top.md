# Scientific workbench table: invisible support proxy and gray top

Date: 2026-08-19

## Decision

Package-owned `static_support` proxy cubes are display-invisible by default.
Collision, the six drop/side-impact gates, and the physics material are
unchanged. The cube remains in the contract; consumers hide it by not drawing
it, not by deleting it.

The scientific workbench Lab001 table
(`scientific_workbench.lab001.table.2000x800x755`) additionally deactivates
the furniture `Body` and binds an opaque mid-lab-gray `UsdPreviewSurface` on
the `Surface` mesh. Other `static_support` assets keep their source appearance.

## Why

The workbench table's proxy cube occupied the same 0.755 m slab as the visual
surface. RTX then drew a default opaque cube: striped z-fighting in
RayTracedLighting, and blocked transmission through glassware. The LabUtopia
surface material was also `Plastic_Thick_Translucent` with `diffuse_weight
0.08`, so the top itself was not a solid bench.

## Rules

1. `static_support_authoring.py` always sets
   `UsdGeom.Imageable(proxy).CreateVisibilityAttr()` to `invisible` after
   defining the Cube and applying `PhysicsCollisionAPI`. This is not a profile
   field. Existing packages pick it up on the next normalize.
2. Workbench-only visual overlay `overlays/workbench_table_visual.usda`:
   `Body` `active = false`; `Surface/Source/mesh` bound
   `strongerThanDescendants` to `WorkbenchTableTop` with
   `diffuseColor (0.70, 0.72, 0.74)`, `metallic 0`, `roughness 0.40`,
   `opacity 1`. The composed `source.usda` is the AAN source.

## Packages

- Immutable historical package:
  `outputs/scientific_workbench_standard_table_20260811/`
- New package:
  `outputs/scientific_workbench_standard_table_20260819/`
  - AAN source: `source.usda` (visual overlay + facade)
  - Isaac Sim 4.1 static + runtime gates pass, including the six support
    probes
  - proxy `visibility = invisible`; collision enabled
  - composed Body inactive; tabletop PreviewSurface gray

LabUtopia `lab_001.usd` was not modified.
