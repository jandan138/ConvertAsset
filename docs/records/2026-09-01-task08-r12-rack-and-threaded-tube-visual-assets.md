# Task 08 r12 rack and threaded-tube visual assets

## Outcome

`outputs/scientific_workbench_task08_r12_assets_20260901/` contains three
producer-owned packages for the VR action-collection scene:

- `mixed_rack_18plus4_scaled_sdf_r3`;
- `tube15_long_neck_threaded_body_glass_v1_2`;
- `tube15_long_neck_threaded_closed_cap_red_v1_2`.

The mixed rack geometry and named frames bake local scale `(1.1, 1.1, 1.3)`.
Its approximate extent is therefore `192.5 x 139.7 x 93.6 mm`. The prior static
triangle-mesh collision is replaced by visual-mesh SDF at resolution 256 and
subgrid 6. All eighteen 15 mL positions receive invisible primitive bottom
supports; no Scenario Forge rack-specific physics patch is required.

The tube body and cap retain the v1.1 geometry, SDF, mass and inertia. The body
uses the complete nine-input webpage-standard `WebStandardClearBorosilicate`
state. The cap uses the existing Task 11 red PP state. These are visual-only
variants and do not promote thread engagement.

## Evidence

Three Isaac Sim 4.1 rack cold starts each retained three open tubes in adjacent
`r00_c01/c02/c03` slots for 960 steps. Maximum radial offset was about 0.020 mm,
maximum upright angle about 2.09 degrees, and no selected hard error was found.
The glass body and red cap each passed three dynamic cold starts.

Local render review confirms the open threaded body, transparent material,
closed red cap, and complete rack geometry. The isolated thick-wall glass render
has strong environment reflections, so the final room render remains the visual
authority for task use.

## Claim boundary

The asset set claims scaled-rack SDF readiness and visual-material-variant
readiness. `thread_interaction_ready`, `task08_success`, robot-policy success and
benchmark success remain false. Mass and inertia remain the inherited provisional
v1.1 values.

## Validation

```text
python -m pytest -q tests/test_build_task08_r12_assets.py \
  tests/test_qualify_task08_r12_assets.py
# 4 passed

python -m ruff check scripts/build_task08_r12_assets.py \
  scripts/qualify_task08_r12_rack.py \
  scripts/qualify_task08_r12_assets.py \
  scripts/qualify_wangshuai_dynamic_assets.py \
  tests/test_build_task08_r12_assets.py \
  tests/test_qualify_task08_r12_assets.py
# All checks passed
```
