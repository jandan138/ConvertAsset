# 2026-07-29 AAN Articulated Reset Capture Synchronization

## Trigger

The HCI955350 centrifuge package was blocked only by the AAN-06 rigid reset
gate for its driven lid (`/World/Centrifuge/group_23`). Static admission, cold
load, render readback, finite physics stepping, and scoped PhysX warning
checks passed.

## Investigation

The worker previously captured the initial transform immediately after its
bootstrap `world.reset()`, while every tested reset cycle captured after
`world.reset()` followed by `SimulationApp.update()`. The lid's angular drive
advances during that update, so the two samples were not equivalent lifecycle
states.

A controlled Isaac Sim 4.1 probe captured articulation DOFs and rigid-body
transforms over three reset sequences. At matched phases, all four scoped
rigid bodies had zero report-precision transform delta across resets. The
previous 20.55444 mm and 34.95695 mm failures were the deterministic movement
between reset-immediate and post-update samples, not reset nondeterminism.

## Decision

`runtime_smoke.py` now centralizes the reset sequence in `_reset_and_sync()`:

```text
world.reset()
simulation_app.update()
```

The bootstrap baseline and every reset cycle use that same helper before
capturing transforms. Evidence records the capture point as
`after_reset_and_app_update_before_warmup_and_render`.

This does not change the dynamic reset acceptance rule: scoped rigid-body
world transforms still compare against a 1 mm tolerance. No articulated-body
waiver, joint-state substitution, or tolerance increase was introduced.

The centrifuge lid drive was restored from the final diagnostic experiment
(`100000/2000`) to its prior authored values (`stiffness=2000`,
`damping=200`), and the source-bound physics profile hash was updated.

## Files

| File | Change |
| --- | --- |
| `convert_asset/asset_application_normalizer/runtime_smoke.py` | Synchronize bootstrap and cycle reset capture phases; persist the phase in evidence. |
| `tests/test_asset_application_normalizer_physics_admission.py` | Regression test for reset/update ordering. |
| `docs/design/asset-application-normalizer.md` | Document strict dynamic reset semantics and synchronized sampling. |

## Verification

```text
python -m pytest -q tests/test_asset_application_normalizer_physics_admission.py tests/test_asset_application_normalizer_cli.py
# 66 passed, 1 skipped

python -m pytest -q tests/test_asset_application_normalizer*.py
# 122 passed, 4 skipped

python -m ruff check convert_asset/asset_application_normalizer/runtime_smoke.py tests/test_asset_application_normalizer_physics_admission.py
# All checks passed
```

The full `normalize-asset --gates static,runtime` run against Isaac Sim 4.1
produced:

- package: `/cpfs/user/zhuzihou/dev/scenario-forge/outputs/tube_task_assets_20260729/centrifuge/package`
- manifest: `overall_status: pass`
- both reset cycles: scope and rigid-body `max_abs_delta_from_initial: 0.0`
- scoped PhysX warning gate: `pass` with zero attributable events
- source facade SHA-256:
  `c3f9d5e8800e667d84651cd16825ee0ee635718626520547755fbd298a227d5b`

The same updated worker was also rerun against the sibling dynamic packages:

- `test_tube/package.manifest.json`: `overall_status: pass`
- `tube_rack/package.manifest.json`: `overall_status: pass`

## Boundary

This evidence proves reproducibility at the explicitly recorded reset capture
phase. It does not prove robot contact behavior, task success, or arbitrary
downstream-instantiation behavior. The separate task/interaction qualification
remains responsible for those claims.
