# 2026-05-24 InternNav Flat-Filter Runtime Result

## Summary

The InternNav flat-filter protocol advanced from input preparation to real
runtime evidence.

Original completed all 14 selected episodes:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_acl_main_pilot30_flatfilter/result.json
```

Aggregate:

```text
TL = 80.5189
NE = 34.2730
OS = 0.3571
SR = 0.0
SPL = 0.0
Count = 14
```

Modified completed 12 episodes, then hung after reset on:

```text
MV7J6NIKTKJZ2AABAAAAADY8_usd_tvstand_model_0b7e2a91f26da6b0f1f83c1c7d824399_0_0_6
```

The watchdog classification is:

```text
status = runtime_hang
reason = reset_without_first_action_or_terminal_metric
```

This means the hung episode reached `Env Reset` but produced no first
navigation action, no `Env Step`, no `finish`, and no terminal metric. It must
not be counted as a normal `SR=0` / `SPL=0` navigation failure.

## What This Rules Out

This is not the same issue as the earlier broken-sidecar packaging failure. The
prepared scene directories expose the GRScenes `models` and `Materials`
sidecars.

This is not the v2-v10 high-target sampling problem. The specific hang path
passes the flat z-jump audit:

```text
would_filter_stairs = false
max_adjacent_z_delta = 0.231996
```

This is not supported as a broken-target-asset case. Independent static USD
inspection found:

- the tvstand target exists in both original and modified scenes;
- target geometry is identical: 7 meshes, 7070 points, 13656 faces;
- target world bbox is identical across original and modified;
- modified target has UsdPreviewSurface shader graphs and no residual target
  MDL;
- no unresolved target references were found;
- no target-local negative determinant, negative mass, or invalid inertia issue
  was found.

The remaining classification is a modified-scene reset / first-step simulation
hang that is target/scene-state sensitive. Scene-level PhysX warnings still
matter as robustness risk, but the current evidence does not isolate a broken
target model as the cause.

## Diagnostic Pair Metrics

The completed rows were extracted into:

```text
paper/shared/evidence/raw/internnav_vln_downstream/original_flatfilter_episode_metrics.jsonl
paper/shared/evidence/raw/internnav_vln_downstream/modified_flatfilter_partial_episode_metrics.jsonl
paper/shared/evidence/raw/internnav_vln_downstream/paired_flatfilter_partial_episode_analysis.json
```

The 12 paired diagnostic rows show behavior changes:

| metric | original mean | modified mean | modified - original |
| --- | ---: | ---: | ---: |
| TL | 87.4767 | 48.3071 | -39.1696 |
| NE | 36.0452 | 32.5808 | -3.4644 |
| OS | 0.4167 | 0.1667 | -0.2500 |
| SR | 0.0 | 0.0 | 0.0 |
| SPL | 0.0 | 0.0 | 0.0 |

Failure-pair distribution:

```text
original_exceed_total_max_step__modified_exceed_total_max_step = 1
original_exceed_total_max_step__modified_not_reach_goal = 2
original_not_reach_goal__modified_exceed_total_max_step = 2
original_not_reach_goal__modified_not_reach_goal = 7
```

The selected qualitative rerun candidates are recorded at:

```text
paper/shared/evidence/raw/internnav_vln_downstream/video_case_manifest_flatfilter_partial.json
```

No mp4 evidence has been produced yet.

## Paper Meaning

This result strengthens the ACL story only in a limited way:

- It proves the InternNav route is now running real multi-episode episodes, not
  only a one-episode smoke.
- It shows original and modified conditions can produce different embodied
  behavior under matched instructions and scene ids.
- It exposes a new runtime robustness risk introduced by the modified scene
  condition.

It does not yet support a main-result SR/SPL claim:

- modified aggregate runtime is incomplete;
- only 12 paired rows are available;
- `paired_flatfilter_partial_episode_analysis.json` reports
  `acl_main_result_ready=false`;
- no selected side-by-side videos exist yet.

The correct paper wording is "diagnostic embodied downstream evidence and
runtime failure case", not "completed InternNav benchmark result".

## Follow-Up State

A deterministic continuation split excluding the hung path has been generated:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_v2_prep_manifest.json
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523_pilot30_flatfilter_v2
```

It contains 13 episodes across six scenes. This is a valid continuation
candidate, but it still cannot satisfy the 30-episode pilot gate. Reaching a
paper-level batch requires expanding the ready original/no-MDL scene-pair
inventory, or explicitly defining a separate high-object stress protocol that is
not presented as standard InternNav-compatible VLN.

## Verification Commands

Runtime/evidence commands used for this record:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/runtime_watchdog.py \
  --log-dir /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_modified_acl_main_pilot30_flatfilter \
  --result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_modified_acl_main_pilot30_flatfilter/result.json \
  --split-name acl_main_pilot30_flatfilter \
  --output paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_modified_runtime_hang_triage.json

python paper/shared/evidence/experiments/07_internnav_vln_downstream/audit_episode_height_filter.py \
  --dataset /cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523_pilot30_flatfilter/datasets/grscene_sn_acl_main_pilot30_flatfilter/acl_main_pilot30_flatfilter/acl_main_pilot30_flatfilter.json.gz \
  --threshold 0.3 \
  --hang-path-key MV7J6NIKTKJZ2AABAAAAADY8_usd_tvstand_model_0b7e2a91f26da6b0f1f83c1c7d824399_0_0_6 \
  --output paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_modified_runtime_hang_height_audit.json

python paper/shared/evidence/experiments/07_internnav_vln_downstream/analyze_paired_metrics.py \
  --input-jsonl paper/shared/evidence/raw/internnav_vln_downstream/original_flatfilter_episode_metrics.jsonl \
  --input-jsonl paper/shared/evidence/raw/internnav_vln_downstream/modified_flatfilter_partial_episode_metrics.jsonl \
  --output paper/shared/evidence/raw/internnav_vln_downstream/paired_flatfilter_partial_episode_analysis.json
```
