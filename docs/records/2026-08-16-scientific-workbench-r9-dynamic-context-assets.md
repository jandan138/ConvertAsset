# 2026-08-16 Scientific Workbench r9 Dynamic Context Assets

## Result

Six tabletop assets from the immutable
`refined_assets_on_table_no_operation.zip` source were admitted as
source-bound dynamic-context packages for Scenario Forge r9:

- amber reagent bottle;
- clear reagent bottle;
- pipette carousel;
- closed pipette-tip box;
- wash bottle; and
- 100 mL library graduated cylinder.

All six package manifests report `overall_status: pass` and an Isaac Sim 4.1
runtime smoke pass. The source archive SHA-256 is
`63d3cae3af2c5ef843d950130423b27d6ba1a1939c406332b88d0e7e52b2bf1b`.
The packages are written below
`outputs/scientific_workbench_r9_dynamic_context_assets_20260816/packages/`.

## Conversion ownership

ConvertAsset owns the package-authored compound Cube/Cylinder collision
proxies and the complete provisional-geometry mass/inertia bundles. The
consumer must mount `asset.usd` at the identity `/ObjectRoot` entry prim and
must not add asset-specific collider, scale, mass, inertia, or warning-hiding
patches.

The six context profiles require root-motion and stable-support qualification
when used in a composed task scene. They deliberately do not require a gripper
collision gate. Their claim boundary is physical scene context only: no grasp,
manipulation, task, policy, or benchmark readiness is asserted.

## Selection boundary

The source archive also contains duplicate beakers, racks, and a closed
carousel duplicate. They were not admitted for this release because they would
duplicate task-looking objects, consume unnecessary package size, or weaken
the fixed room-specific dressing presets. This is a release selection, not a
negative compatibility claim about those source assets.

## Evidence boundary

The runtime gate covers cold load, render readback, 120 physics frames, and two
reset cycles in Isaac Sim 4.1. It does not substitute for Scenario Forge's
composed-scene 960-step stability checks, visual layout review, or Task 02
liquid-transfer oracle evidence.
