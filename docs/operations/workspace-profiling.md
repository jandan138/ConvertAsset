# Workspace Profiling Runbook

> Purpose: repeatable methodology for source-bound eBench workspace
> integration profiles, internalized from the 2026-07 LabUtopia/external-room
> deliveries. Read this before profiling any new room.

## Tooling

- `python main.py workspace-profile <source.usd> --assembly <root>... --anchor X Y Z --units-per-meter U [--shell-prefix P]...`
  runs the clearance audit and writes a v0.1 profile.
- `python main.py build-facade <raw.usd> --out <dir> --mount /world=/World/world ...`
  builds a consumer facade for multi-root stages (binding retarget included).
- Module API: `convert_asset.workspace.{geometry,audit,profiles,render}`,
  `convert_asset.asset_application_normalizer.{facade,batch}`.

For generated rooms with a deliberately reserved workcell, the v1 zone
request may declare `clearance_footprint_m: [width, depth]`.  The audit rotates
that complete consumer envelope by the reviewed zone yaw.  Requests that omit
the field retain the historical `2.345 x 2.645 m` eBench-table footprint for
backward compatibility.  Use the larger envelope when the room must prove
robot landing and circulation space as well as table placement; do not enlarge
an admitted room downstream to manufacture clearance.

## Placement rules (learned the hard way)

1. **Complete assemblies only.** Inactive sets must be whole assembly roots.
   Flat floor/counter decals may be listed as *optional* inactives with full
   paths; scattered ungrouped props force `not_applicable` (never mask
   anonymous meshes). An optional inactive assembly root covers its complete
   USD descendant subtree; do not enumerate the assembly's leaf meshes.
2. **Room shell is always kept.** Floor/walls/ceiling/windows intersecting
   the clearance are background, not blockers.
3. **Check table depth vs the host row depth.** A centered anchor on a
   shallow row drives the table through the wall behind it (067 R2). If the
   row is shallower than the table, compute the wall-flush position instead.
4. **Check aisle width vs table width/depth.** Wall-flush protrusion must
   not bite the next interior row (067 R3: north aisle 1.88 m < 2.645 m
   table depth => not_applicable).
5. **Verify the robot landing spot.** The fixed robot spawns 1.26 m from the
   anchor in the composer frame; that spot must be free floor, not wall or
   furniture (067 R1/R2).
6. **Prefer interior embedding.** Wall-adjacent placements tend to give
   blank-wall backgrounds; interior islands keep lab context behind the
   workcell (067 R1, 084 success).
7. **Measure the coordinate scale physically.** Counter-band measurement
   against the 0.90 m reference; publish the exact audit-consumed
   `source_composed_units_per_meter`, never a rounded prose value (profile-2
   request). Bench-local bands beat global histograms when furniture series
   differ in height (067 scale correction).
8. **Pick yaw from row orientation.** x-axis rows validated at yaw 90
   (083), y-axis islands at yaw 0 (066/059); confirm with a robot-view
   render, not just a closeup.

## not_applicable contract

Returning `not_applicable` with a measured reason is a first-class outcome,
not a failure: record the aisle/depth/prop numbers that block every
candidate spot. Never manufacture a placement (see 081/085/067 profiles).

## Facade pattern (multi-root sources)

Some sources split content across top-level namespaces (e.g. `/world`
materials, `/Root` geometry, `/Render` settings) with cross-namespace
bindings. Consuming one namespace alone loses the room. The facade:

1. mounts every namespace under one consumer scope (`/World/<ns>`);
2. retargets `material:binding` targets by namespace prefix with a stronger
   overlay layer (raw tree immutable);
3. records the raw->facade namespace mapping and source SHA-256 in
   `facade_provenance.json`.

Then run `normalize-asset` on the facade with scope `/World` and role
`visual_static_environment`; the closure and scope snapshot make every
dependency package-local. Watch for **inactive material variants** in the
source: bindings to them are dead and are skipped by closure (AAN-03R).
