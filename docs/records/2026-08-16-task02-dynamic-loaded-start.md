# Task 02 dynamic-loaded-start qualification

Date: 2026-08-16

## Outcome

ConvertAsset now exports a source-bound `dynamic_loaded_start` contract for the
qualified Task 02 cylinder/beaker GPU-PBD pair. The producer settles the empty
dynamic cylinder on a 0.755 m support plane, records the stable entry-root pose,
expresses all 580 pre-settled particles in that root-local frame, and replays the
combined state in three independent Isaac Sim 4.1 cold starts.

```text
outputs/task02_gpu_pbd_dynamic_loaded_start_20260816_r59/
  final_package/task02_cylinder_to_beaker_gpu_pbd_transfer_pair_r5/
```

All three cold starts passed. Maximum entry-root tail drift was below
`2.3e-6 m`, maximum tilt was below `0.014 deg`, and every run retained all
`580/580` particles in the source. The measured entry root is
`[0.2499996126, 0.0000006202, 0.7481006980] m`; its support-relative vertical
offset is `-0.0068993020 m`.

## Implementation and validation

- `scripts/qualify_gpu_pbd_dynamic_loaded_start.py` performs dry settling and
  the three cold-start gates.
- `scripts/observe_gpu_pbd_dynamic_loaded_start.py` is the Isaac 4.1 worker.
- `scripts/promote_gpu_pbd_dynamic_loaded_start.py` hash-binds the contract,
  local particle state, and report into a new package; r4 remains unchanged.
- focused qualification and promotion tests pass.

No collider, rest/contact offset, friction, mass/inertia, particle-system, or
particle-material parameter changed. This proves the fixed loaded-start
protocol only; it does not prove robot grasp, pouring, policy or benchmark
success, or real-liquid calibration.

