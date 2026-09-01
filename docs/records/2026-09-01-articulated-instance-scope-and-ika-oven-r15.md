# Articulated Instance Scope and IKA OVEN r15

## Decision

New articulated packages keep their placement root stable and materialize the
complete device subtree below a case-sensitive `Instance` Scope. `Instance` is
deliberately not an Xform. Isaac Sim 4.1 testing showed that an additional
identity Xform, as well as a reference facade, preserved the oven door but
disabled the non-articulation DriveAPI used by buttons and knobs.

## IKA OVEN r15

`outputs/ika_oven_125_task09_r15_instance_layout_20260901/` preserves r14 and
publishes `/World/obj_oven/Instance/{Body,Door,ControlPanel,Joints,...}`. All
nineteen RigidBodyAPI links and all internal joint body targets are below the
Scope. The ControllerGraph moves with ControlPanel and discovers
`/World/obj_oven/Instance` as its device root.

The final qualification materializes three namespaces rather than referencing
the package: canonical `/World/obj_oven`, arbitrary prefix
`/World/task_fixture/obj_oven`, and VR `/World/_scene/obj_oven`. Primary and
auxiliary physical rotation/press, controller state, scale endpoints 0.85/1.0/1.15,
door 60-degree hold/close, and base stability pass in Isaac Sim 4.1.

## Boundary

The generic layout helper is producer-owned. Consumers must not wrap legacy
assets or rewrite link paths. Historical r14 artifacts remain unchanged. Robot
policy and benchmark success are not claimed.

## Validation

```text
python -m pytest -q tests/test_articulated_instance_layout.py \
  tests/test_build_ika_oven_r15_instance_layout.py
# 4 passed
```
