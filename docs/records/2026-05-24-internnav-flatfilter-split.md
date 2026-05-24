# 2026-05-24 InternNav Flat-Filter Split

## Purpose

This record closes the v2-v10 runtime-hang investigation with an executable
replacement protocol. Instead of excluding one hung episode at a time, the split
generator now filters candidate episodes whose generated `reference_path` has an
adjacent z jump above `0.3`, matching InternNav's official
`different_height()` z-jump branch used when `filter_stairs=True`.

## Implementation

Code and tests:

```text
paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py
tests/test_internnav_vln_downstream_prep.py
```

New CLI option:

```bash
--max-reference-z-delta 0.3
```

The manifest records the threshold, policy, skipped count, and skipped episode
records under `selection`. The generated runtime config still sets
`filter_stairs=False`; compatibility is enforced by ConvertAsset's preparation
step. Skipped-record `path_key` values are pre-filter source-selection keys, not
final runtime dataset keys.

`advance_split_from_triage.py` preserves `selection.max_reference_z_delta` from
the previous manifest, so any future triage-derived split from this flat-filter
candidate stays on the corrected protocol instead of silently returning to the
old high-target sampling rule.

## Generated Candidate

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_prep_manifest.json
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_height_audit.json
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523_pilot30_flatfilter
```

Statistics:

```text
requested max episodes = 30
selected episodes = 14
selected scenes = 6
height-filter skipped episodes = 48
dataset max adjacent z delta = 0.2501815125689813
height audit would_filter_stairs_count = 0
external work root size = 83K
```

The split is ready for an original/modified runtime smoke, but it is not a
paper-level 30-episode result. The 0.3m height gate collapses the current six
ready scene pairs from 62 ready episodes to 14 z-jump-compatible episodes.

## Paper Meaning

For the ACL story, this is a protocol correction:

- The prior v2-v10 hangs were invalid navigation episodes, not valid SR/SPL
  failures.
- The current flat-filter split is the right next smoke candidate for testing
  whether the runtime hang class has been removed.
- A main-result batch needs either more ready no-MDL scene pairs or a separate
  high-object stress benchmark that is labeled as nonstandard relative to
  InternNav's default height filter.

## Verification

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py tests/test_internnav_advance_split_from_triage.py -q
python paper/shared/evidence/experiments/07_internnav_vln_downstream/audit_episode_height_filter.py \
  --dataset /cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523_pilot30_flatfilter/datasets/grscene_sn_acl_main_pilot30_flatfilter/acl_main_pilot30_flatfilter/acl_main_pilot30_flatfilter.json.gz \
  --threshold 0.3 \
  --output paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_height_audit.json
```
