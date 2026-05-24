# 2026-05-25 InternNav Expanded30 And Video Rerun Prep

## Context

The flat-filter InternNav route had two separate findings:

- v2-v10 repeatedly selected high-z target episodes that InternNav's
  `different_height()` filter would remove. This was a sampling protocol issue.
- The corrected flat-filter split removed that high-z class. Original completed
  14/14 episodes, while modified completed 12/14 and then hung after reset on a
  tvstand episode. That is a modified scene reset / first-step simulation hang,
  not a target-subtree static USD failure.

After the 0.3m z-jump gate, the original ready scene-pair pool only supplied 14
usable flat episodes. This was too small for the ACL pilot-main threshold.

## What Changed

Ten additional GRScenes home navigation scenes were converted to no-MDL in the
scratch tree:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521
```

The clean GRScenes source tree remains unchanged:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes
```

The conversion evidence is recorded in:

```text
paper/shared/evidence/raw/internnav_vln_downstream/navigation_nomdl_expand_20260525_report.json
```

Post-expansion inventory:

| item | value |
| --- | ---: |
| newly converted navigation scenes | 10 |
| failed conversions | 0 |
| ready original/no-MDL navigation scenes | 16 |
| ready episodes before height filter | 162 |
| ready flat episodes at `max_reference_z_delta=0.3` | 38 |
| skipped high-z ready episodes | 124 |

This enabled a 30-episode / 16-scene flat-filter candidate:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_expanded30_prep_manifest.json
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_expanded30_height_audit.json
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260525_pilot30_flatfilter_expanded30
```

The split excludes the known modified tvstand reset-hang path:

```text
MV7J6NIKTKJZ2AABAAAAADY8_usd_tvstand_model_0b7e2a91f26da6b0f1f83c1c7d824399_0_0_6
```

The final numeric suffix in that display key is tied to the dataset order. The
expanded30 manifest can therefore show the same trajectory/base target identity
as an excluded record with a different suffix, such as `_92`. The stable part is
the trajectory and target identity before the suffix, not the suffix itself.

Height audit result:

| item | value |
| --- | ---: |
| episode count | 30 |
| `would_filter_stairs_count` | 0 |
| known hang count | 0 |
| known hang unmatched count | 0 |

## Video Rerun Prep

`generate_video_rerun_configs.py` was added under:

```text
paper/shared/evidence/experiments/07_internnav_vln_downstream/
```

It converts a prep manifest plus a selected video-case manifest into a
selected-only InternNav dataset and paired original/modified configs with
`vis_output=True`.

Current generated video rerun manifest:

```text
paper/shared/evidence/raw/internnav_vln_downstream/video_rerun_manifest_flatfilter_partial.json
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260525_flatfilter_video_selected_partial
```

It selects six diagnostic episodes across three scenes and records expected mp4
paths. It is not video evidence until the selected-only InternNav jobs finish.

## Interpretation For The Paper Story

This round moves InternNav from "real route exists but input pool is too small"
to "a 30-episode, 16-scene paired runtime split is ready to run."

It does not produce new SR/SPL/NE/TL metrics. The ACL story can now say the
embodied downstream experiment has a prepared pilot-main input gate, but it
cannot claim an expanded30 embodied result until both original and modified
runtime jobs complete and the paired analysis is regenerated.

## Verification

Commands run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py tests/test_internnav_advance_split_from_triage.py -q
python -m json.tool paper/shared/evidence/raw/internnav_vln_downstream/navigation_nomdl_expand_20260525_report.json >/dev/null
python -m json.tool paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_expanded30_prep_manifest.json >/dev/null
python -m json.tool paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_expanded30_height_audit.json >/dev/null
python -m json.tool paper/shared/evidence/raw/internnav_vln_downstream/video_rerun_manifest_flatfilter_partial.json >/dev/null
```

Result:

```text
38 passed
```
