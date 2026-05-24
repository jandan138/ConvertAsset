# 2026-05-24 InternNav Runtime Hang Root Cause

## Summary

`acl_main_pilot30_v2` through `v10` did not fail because the navigation agent
merely chose bad actions. They repeatedly hit the same simulator boundary:

```text
start sampling -> WARM UP / Env Reset -> agent step time: 0.0s -> no action -> no finish
```

That means the hung episode produced no terminal metric and must not be counted
as `SR=0`, `SPL=0`, or `not_reach_goal`.

The strongest root cause is protocol mismatch: our GRScenes SN-to-InternNav
bridge kept high-target object episodes that InternNav's `different_height()`
z-jump rule would remove when `filter_stairs=True`. `prepare_minipair.py`
appends the object `target_point` to `reference_path`; for tabletop/high objects
this creates a final z jump from floor level to object height. InternNav's
`different_height()` rule filters any adjacent z jump greater than `0.3`, but
our generated configs set `filter_stairs=False`.

## Evidence

Machine-readable audit:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_runtime_hang_height_filter_audit.json
```

The audit covers nine v2-v10 known hang path keys across the generated v2-v10
datasets:

```text
known_hang_count = 9
known_hang_covered_count = 9
known_hang_would_filter_stairs_covered_count = 9
known_hang_unmatched_count = 0
```

Representative z jumps:

```text
refrigerator b408...  max_adjacent_z_delta = 0.9237
microwave 699b...     max_adjacent_z_delta = 1.3330
oven 9506...          max_adjacent_z_delta = 0.9821
pan dd34...           max_adjacent_z_delta = 0.9471
faucet 350e...        max_adjacent_z_delta = 1.0029
sofa_chair d5f1...    max_adjacent_z_delta = 0.3237
washingmachine 1d30... max_adjacent_z_delta = 0.4268
clock 65d...          max_adjacent_z_delta = 0.5022
bottle cbb224...      max_adjacent_z_delta = 0.8906
```

This explains why official InternNav-style runs are less likely to show this
failure: the paper/example path keeps `filter_stairs=True`, while our custom
GRScenes SN split explicitly disabled it to preserve paired selection.

## Asset Layer

This is not the original broken-sidecar problem. Opening the prepared runtime
`fixed_docker.usd` under the InternNav work root resolves `models` and
`Materials` sidecars; direct-opening the raw source USD can still show missing
references because raw per-scene `models`/`Materials` entries are text pointers,
not symlinks.

The raw GRScenes scenes do have physics risk:

- v6-v10 logs contain thousands of `Fail to create IRigidBody`,
  `Non-positive determinant`, `negative mass`, and invalid inertia warnings.
- Static USD inspection found many scene-level physics prims with non-positive
  determinants.
- The v10 `bottle cbb224` target itself did not show authored negative mass,
  authored invalid inertia, unresolved reference, or negative determinant under
  the prepared runtime USD.
- The ACA8 refrigerator `b408...` target did show negative-determinant mesh
  descendants inside the target subtree.

So the asset layer is a real robustness risk, but it is not the clean single
root cause for every v2-v10 hang. The common denominator across all known hangs
is the high-target / non-flat reference-path pattern.

## Classification

- `invalid_broken_sidecars`: input packaging failure; not paper evidence.
- `invalid_resumed_lmdb`: stale InternNav sample LMDB/resume state; not paper
  evidence and not the same hang class.
- `acl_main_pilot30_v2` through `v10`: true runtime-incompatible episodes,
  consistently reset/warm-up without a first action or terminal metric.
- `acl_main_pilot30_v11`: manually stopped partial run; it is not hang
  evidence and must be cleaned or archived before any rerun with the same task
  name.

## Decision

Stop advancing by one exclusion at a time. That creates `v9`, `v10`, and `v11`
churn without changing the underlying sampling rule.

Next valid experiment split should be a new protocol, not `v12`:

1. Apply an InternNav-compatible height gate before split selection:
   `max_adjacent_z_delta <= 0.3`, matching `different_height()`.
2. Keep the paired original/converted split deterministic after filtering.
3. Prefer at least 30 episodes across at least five scenes for the next pilot;
   for ACL main evidence, scale to 100+ episodes across 10+ scenes after the
   protocol is stable.
4. Add a static scene health report, but do not let scene-level PhysX warnings
   replace the height-gate fix.

This preserves the paper story: ConvertAsset can still test whether material
conversion changes embodied behavior, but the benchmark input must use
InternNav-valid navigation episodes rather than high-object target points that
the official pipeline would filter away.

## Follow-Up Split

`prepare_minipair.py` now accepts `--max-reference-z-delta 0.3` and applies the
`different_height()` z-jump gate before selecting the final paired split. The
generated runtime config still sets `filter_stairs=False`; compatibility is
enforced in the preparation step. The first follow-up split is:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_prep_manifest.json
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_height_audit.json
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523_pilot30_flatfilter
```

Outcome:

```text
requested max episodes = 30
selected episodes = 14
selected scenes = 6
height-filter skipped episodes = 48
height audit would_filter_stairs_count = 0
max remaining adjacent z delta = 0.2502
claim_gate.status = ready_for_internnav_runtime
```

This is the correct next smoke candidate, not a finished ACL main-result batch.
The result also explains why repeated v8/v9/v10-style fixes kept failing: the
current six ready scene pairs contain only 14 InternNav-compatible flat
episodes after applying the 0.3m `different_height()` z-jump rule. A larger paper batch
requires more ready no-MDL scene pairs, or a clearly separated high-object stress
protocol that is not presented as official InternNav-compatible VLN.

## Later Flat-Filter Runtime Note

The flat-filter split removed the v2-v10 high-z hang class, but it did not make
the modified condition fully complete. Original finished all 14 flat-filter
episodes; modified finished 12 and then hung after `Env Reset` on the tvstand
path recorded in:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_modified_runtime_hang_triage.json
```

That later hang is a different class: its height audit reports
`would_filter_stairs=false`, and target-subtree inspection does not support a
broken-target-asset explanation. See
`2026-05-24-internnav-flatfilter-runtime-result.md` for the current
classification and diagnostic metrics.
