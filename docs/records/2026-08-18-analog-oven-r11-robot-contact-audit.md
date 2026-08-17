# Analog oven r11 robot-contact audit

## Investigation

Scenario Forge r11.1 and EOS attempted a real Lift2 contact opening against the
promoted analog oven r11 release3 package.  The package loads correctly, keeps
all eleven articulation DOFs, passes its state-cycle qualification, and retains
the source-authored main-door mesh collision.  No source USD, package USD,
drive, mass, inertia, or collider was changed during this audit.

The main door uses one `convexHull` collision mesh.  Its authoritative
`door_grasp` frame is parented to `Source/group_4` at
`[0.077, -0.0416, 0.327]` in parent-local metres.  In the robot trial, the
right fingers were commanded closed but remained at 43.349 and 43.322 mm, and
the first pull left the main-door joint at `2.73e-14 rad`.  The frame therefore
does not provide a physically enclosing Lift2 grasp against the current cooked
shape.

## Decision

The r11 release3 package remains valid within its recorded claim: articulated
state travel/readback, locked-joint stability, shelf support, and benchtop
stability.  That evidence explicitly excluded robot contact.  It must not be
relabelled as robot-contact-ready.

A future interaction revision must identify a door-coupled grasp feature,
author a source-bound compound collider only if the measured geometry requires
one, and pass an Isaac 4.1 contact open/hold/close cycle before Scenario Forge
consumes it.  Scenario Forge and EOS must not add an oven-specific collider or
direct articulation-state workaround.

## Verification evidence

The downstream blocked bundle retains the exact package device/physics profiles
and EOS contact trace at
`/cpfs/user/zhuzihou/dev/scenario-forge-runtime-evidence/scientific_workbench_r11_1/blocked/task09/`.

The focused r11 asset-builder suite passes (`3 passed`).  This audit changes no
asset builder, source, package, or runtime qualification output.

## Open issue

The separate `group_2` door-latch geometry protrudes from the front of the
appliance, but the current source articulation does not establish it as a
door-coupled task handle.  Do not move or re-parent it without a new measured
topology review and runtime qualification.
