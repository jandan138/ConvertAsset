# AAN static-support role and Lab001 table admission

Date: 2026-08-06

## Decision

`visual_static` keeps its existing zero-physics meaning. Load-bearing tables now
use the separate `static_support` asset role and a source-bound
`aan.static_support_profile.v1`. Scenario consumers must consume the qualified
package and must not synthesize a table slab.

The v1 contract prefers a declared, active source collider and falls back to a
package-owned Cube proxy only when that collider is unavailable. It guarantees
the declared tabletop and its edges, not legs, cabinets, drawers, or measured
real-world contact parameters. A stronger consumer layer may replace it only by
explicitly disabling every collider path named in the manifest.

## Default material

- static friction: 0.5
- dynamic friction: 0.5
- restitution: 0
- friction combine: `max`
- restitution combine: `multiply`
- calibration status: `provisional_unmeasured`

These are simulator candidates, not measurements.

## Lab001 package

- source: LabUtopia `lab_001_localized_20260707/lab_001.usd`
- immutable source SHA-256:
  `b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2`
- scope: `/World/table`
- selected collider: `/World/table/surface/mesh`
- selection: `preserved_source`
- package: `outputs/labutopia_lab001_table_static_support_r2/`
- manifest: `outputs/labutopia_lab001_table_static_support_r2/evidence/manifest.json`

The Isaac Sim 4.1 runtime gate passed all six probes: center drop, four near-edge
drops, and a horizontal side impact. The package has no rigid body, mass,
articulation, or joint semantics in the declared scope. The raw LabUtopia source
was not modified.

The r2 promotion also applies scope-first USD extraction to `static_support`.
The package therefore retains the declared `/World/table` subtree and its
bound materials without admitting unrelated siblings from `lab_001.usd`.

## Compatibility

Existing `visual_static` table packages and Scenario Forge v0.2 bindings remain
readable historical artifacts, but are not valid defaults for load-bearing task
tables. New formal Scenario Forge packages must bind the `static_support`
package and fail closed when its contract or runtime qualification is absent.
