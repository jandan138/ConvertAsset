# Task 02 GPU-PBD four-fill qualification v2

Date: 2026-08-17

## Outcome

ConvertAsset extended the existing source-bound Task 02 dynamic-loaded-start
contract without changing the qualified cylinder/beaker component, collision
topology, particle material, or the 0812-derived particle parameters. Four
independent promoted packages are available at:

```text
outputs/task02_gpu_pbd_fill_sweep_20260817_r60/final_packages/{fill20,fill40,fill60,fill80}/
```

Each package binds its particle-state hash, target fill profile, three cold
Isaac Sim 4.1 observations, and the existing prescribed-transfer qualification.
Scenario Forge consumes these packages; it must not reconstruct or patch their
USD/physics state.

## Investigation and design

The original v1 contract proved a stable loaded start but had no way to
distinguish multiple liquid amounts. The v2 extension therefore adds only:

- `fill_level_id`, target ratio, tolerance, and the measurement definition
  `live_points_source_local_z_q95`;
- live below-floor particle count and settled fill ratio in every cold run;
- a measured ratio range in the qualification report and promoted manifest.

Particle seeds are deterministic build inputs only. Their authored q95 is not
a runtime claim; every seed must still pass three independent live cold runs.
The v1 contract remains accepted for existing deliveries.

## Code changes

- `scripts/build_gpu_pbd_fill_sweep_states.py`: derives deterministic staged
  seeds while keeping particle count and authored q95 separately tunable.
- `scripts/observe_gpu_pbd_dynamic_loaded_start.py`: records source-local q95,
  below-floor particles, and live settled-fill ratio.
- `scripts/qualify_gpu_pbd_dynamic_loaded_start.py`: emits v2 contracts/reports
  and gates fill tolerance plus below-floor escape.
- `scripts/promote_gpu_pbd_dynamic_loaded_start.py`: validates matching v1/v2
  report schemas and binds measured v2 ranges into the final manifest.
- `scripts/isaac41_python.sh`: selects the existing EOS-managed Isaac Sim 4.1
  runtime in a clean process; it does not create or mutate an environment.

## Evidence

| Variant | Particles | Target | Three-run measured q95 |
| --- | ---: | ---: | --- |
| fill20 | 290 | 20% | 21.63–21.72% |
| fill40 | 580 | 40% | 38.90–38.95% |
| fill60 | 972 | 60% | 58.57–58.62% |
| fill80 | 1327 | 80% | 75.09–75.16% |

All twelve cold runs retained the full particle count, reported zero particles
outside the source, zero below the source floor, no hard runtime errors, and a
stable entry root. The selected prescribed-transfer candidates retained at
least 50% of particles in the target after the fixed trajectory.

## Verification

Focused pure tests:

```text
python -m pytest -q \
  tests/test_build_gpu_pbd_fill_sweep_states.py \
  tests/test_qualify_gpu_pbd_dynamic_loaded_start.py \
  tests/test_promote_gpu_pbd_dynamic_loaded_start.py
```

Result: 11 passed. Runtime evidence was produced with Isaac Sim 4.1 through the
managed wrapper and is retained below the output root named above.

## Claim boundary and open work

This delivery proves the four source-bound GPU-PBD loaded starts and the
recorded prescribed trajectory. It does not prove robot grasp/pour policy
success, downstream liquid metrics, benchmark success, general fluid fidelity,
or performance in another simulator version. fill80 is valid at the lower edge
of its ±5 percentage-point acceptance band; increasing it requires a new seed
and complete requalification, not a consumer-side edit.
