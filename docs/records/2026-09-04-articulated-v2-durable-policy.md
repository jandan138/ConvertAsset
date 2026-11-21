# Articulated v2 durable producer policy

## Investigation

The durable relocation design still described a kinematic chassis as the end
state even though OVEN 125 r16 had established a promoted fixed-base
articulation. Scenario Forge's former durable document also still selected a
Scope `Instance`. The implementation and dated evidence were correct, but the
long-lived guidance could send a later asset back to the rejected structure.

## Decision

The v1 kinematic relocation remains a legacy candidate stage. Every newly
promoted VR/eBench articulated appliance must then use an enabled articulation
root, identity-Xform `Instance`, non-kinematic links, and a producer-owned
`Instance/Joints/BaseFixed`. Existing public link, joint, collider, control, and
runtime-graph paths remain stable during migration.

ConvertAsset authors and qualifies that structure. Scenario Forge registers
the resulting links and validates the final scene; consumers never add an
articulation root, toggle kinematic state, or replace the fixed joint.

## Changes and verification

The durable design, operational runbook, and documentation indexes now state
the v2 final-package rule. A documentation regression test checks the key
producer invariants. The existing articulation and OVEN r16 tests remain the
behavioral evidence; no asset or historical output package is rewritten.

```bash
python -m pytest -q \
  tests/test_articulated_instance_layout_docs.py \
  tests/test_articulated_instance_layout.py \
  tests/test_build_ika_oven_r16_fixed_articulation.py
```

This policy does not claim robot-task success or a full Isaac Sim 4.5 control
qualification. Isaac Sim 4.1 remains the formal runtime gate.
