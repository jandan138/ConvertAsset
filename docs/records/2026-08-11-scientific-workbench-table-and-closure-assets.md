# Scientific workbench table and 29/42 closure assets

Date: 2026-08-11

## Investigation

The downstream workcell had been authored around an approximate table, while
the reviewed hardware dimensions are `2000 × 800 × 755 mm`. The incoming
closure source contained a 29/42 stopper but no qualified matching vessel. The
available aluminum rack was also checked at source scale instead of being
silently resized to force a fit.

## Design decisions

- Preserve the LabUtopia table appearance and place its source geometry under
  an identity facade entry prim; metric correction belongs to the producer.
- Author the table as a static support with a default collider. Consumers may
  override support policy later, but they do not need a task-specific patch.
- Keep the delivered stopper source-bound. Add a metrically declared analytic
  flask and an open compound proxy so the 29/42 aperture remains usable.
- Treat rack compatibility as a geometry qualification, not an interaction or
  robot-policy claim.

## Delivered packages

- `outputs/scientific_workbench_standard_table_20260811/package`
  - source-bound LabUtopia table visual;
  - identity entry prim `/World/table`;
  - exact outer dimensions `2.000 × 0.800 × 0.755 m`;
  - static support collider with tabletop height `0.755 m`;
  - Isaac Sim 4.1 normalization and runtime gates pass.
- `outputs/scientific_workbench_closure_assets_20260811/packages/ground_glass_stopper_29_42`
  - source-bound package from the incoming 29/42 stopper archive;
  - cooked collision, stable support, root-motion parity, and bilateral proxy
    gripper-collision gates pass.
- `outputs/scientific_workbench_closure_assets_20260811/packages/conical_flask_250ml_29_42`
  - generated, metrically declared 250 ml-class 29/42 vessel;
  - open compound collision proxy preserves the mouth aperture;
  - the same four runtime qualification gates pass.
- `outputs/scientific_workbench_closure_assets_20260811/packages/stopper_rack_k100`
  - source-scale kinematic support rack;
  - geometry fit report at
    `outputs/scientific_workbench_closure_assets_20260811/evidence/stopper_rack_29_42_fit/report.json`.

## Fit evidence

The rack opening is approximately `28.33 mm`; the stopper joint section is
approximately `25.30 mm` and the handle is approximately `30.00 mm`. This is a
geometry-fit result only. It does not prove robot insertion, removal, retention,
or benchmark success.

## Consumer boundary

Scenario Forge consumes package entrypoints and manifests directly. It must not
add table scaling, stopper/flask colliders, mass or inertia patches, or warning
suppression. The original incoming stopper USD and the LabUtopia table source
remain unchanged.

## Code changes

- `component_facade.py` provides the narrow facade builder used by the profile.
- `scientific_workbench_lab001_table_2000x800x755.json` records the reviewed
  source scope, identity entrypoint, exact dimensions, and support collider.
- `build_scientific_workbench_standard_table.py` and
  `build_scientific_workbench_closure_assets.py` reproduce the packages and
  evidence.

## Verification

- `python -m pytest -q tests/test_component_facade_profile.py`
- `python -m pytest -q tests/test_scientific_workbench_closure_assets.py`
- Isaac Sim 4.1 package/runtime gates recorded in each delivered manifest.
- Scenario Forge consumed the manifests without downstream scale, collider,
  mass, or warning-suppression patches.

## Open issues

- The flask is a producer-declared analytic asset rather than a scanned vessel.
- Rack fit does not establish insertion success under a robot controller.
- Real material density and friction remain uncalibrated experimental values.
