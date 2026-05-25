# 2026-05-25 InternNav Official noMDL Visual Assets

## Context

This note records the selected visual rerun assets produced after the official
KuJiaLe paired downstream result in
[2026-05-25-internnav-official-nomdl-pair-results.md](2026-05-25-internnav-official-nomdl-pair-results.md).

Update: the selected 0031 media has since been migrated into the repo-normalized
media package alongside the new 0036/0066 selected videos. See
[2026-05-25-internnav-official-selected-qualitative-videos.md](2026-05-25-internnav-official-selected-qualitative-videos.md).

The quantitative paper claim remains the full `33`-episode paired run. The
visual rerun assets here are qualitative evidence for the paper body and
supplement: selected rollout videos, extracted still frames, and figure
candidates that show original MDL and ConvertAsset noMDL scenes under the same
official InternNav-compatible KuJiaLe episode set.

## Selection

The selected cases were chosen from the full paired per-episode metrics, not
from the later visual rerun outcomes.

Case manifest:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/analysis/video_case_manifest_selected6.json
```

Selected episodes:

| Episode | Full-run transition | Selection type | Reason |
| --- | --- | --- | --- |
| `494_494` | `success -> fail` | `original_only_success` | show a sensitivity case from the full paired run |
| `479_479` | `fail -> success` | `modified_only_success` | show a noMDL-success transition from the full paired run |
| `464_464` | `fail -> fail` | `both_failure_divergent` | preserve the long/sensitive failure case for supplement context |
| `473_473` | `success -> success` | `both_success_divergent` | show both conditions succeeding with different trajectories |
| `493_493` | `fail -> fail` | `both_failure_neutral` | show a stable failure pair |
| `484_484` | `success -> success` | `both_success_neutral` | show a stable success pair suitable for the main figure |

## Rerun Inputs

Rerun workspace:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun
```

Selected-only split:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/raw_data/val_unseen_kujiale0031_video_selected6/val_unseen_kujiale0031_video_selected6.json.gz
```

Rerun manifest:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/video_rerun_manifest_selected6.json
```

Configs:

| Condition | Config | Task name |
| --- | --- | --- |
| original | `/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/configs/internvla_n1_kujiale0031_original_video_selected6_eval_cfg.py` | `official_kujiale0031_original_video_selected6_20260525` |
| noMDL | `/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/configs/internvla_n1_kujiale0031_nomdl_video_selected6_eval_cfg.py` | `official_kujiale0031_nomdl_video_selected6_20260525` |

Both configs set:

```text
eval_settings.vis_output = True
agent.model_settings.vis_debug = False
```

## Video Outputs

Original video root:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/official_kujiale0031_original_video_selected6_20260525/video
```

noMDL video root:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/official_kujiale0031_nomdl_video_selected6_20260525/video
```

Each selected episode has this output shape:

```text
<video-root>/<path_key>/<path_key>.mp4
<video-root>/<path_key>/frames/*.png
```

Observed visual-rerun results:

| Episode | Original rerun | noMDL rerun | Original frames | noMDL frames |
| --- | --- | --- | ---: | ---: |
| `494_494` | `success` | `success` | `81` | `77` |
| `479_479` | `not_reach_goal` | `success` | `60` | `80` |
| `464_464` | `not_reach_goal` | `success` | `208` | `214` |
| `473_473` | `success` | `success` | `124` | `112` |
| `493_493` | `not_reach_goal` | `not_reach_goal` | `62` | `64` |
| `484_484` | `success` | `success` | `45` | `43` |

The visual rerun outcome for `464_464` and `494_494` differs from the full
`33`-episode metric run. This is why the paper should use the full paired run
for quantitative metrics and use these selected videos only as qualitative
rollout assets.

## Figure and Still Assets

Asset manifest:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/video_asset_manifest_selected6.json
```

Extracted still frames:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/assets/stills
```

Figure candidates:

| Purpose | Path |
| --- | --- |
| Main-text paired rollout stills, 3 selected cases | `/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/assets/figures/official_kujiale_main_3case_paired_contact_sheet.png` |
| Supplement paired rollout stills, all 6 selected cases | `/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/assets/figures/official_kujiale_selected6_paired_contact_sheet.png` |
| Full-run metric and transition panel | `/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/assets/figures/official_kujiale_metrics_transition_panel.png` |

Repository-side figure copies:

```text
paper/shared/figures/fig_internnav_downstream_panel.png
paper/shared/figures/fig_internnav_rollout_stills.png
paper/shared/figures/fig_internnav_rollout_selected6_supp.png
```

The main-text contact sheet uses:

- `484_484`: stable `success -> success`
- `473_473`: `success -> success` with divergent trajectories
- `479_479`: full-run `fail -> success` representative case

## QA

Rerun status:

| Condition | Count | SR | SPL | OS | NE | TL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| selected original rerun | `6` | `0.5` | `0.3691` | `0.6667` | `3.2296` | `7.5388` |
| selected noMDL rerun | `6` | `0.8333` | `0.6364` | `1.0` | `1.7189` | `8.1195` |

Basic video QA:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/video_rerun/assets/qa/video_basic_qa_selected6.json
```

Checks performed:

- `12 / 12` expected videos exist
- every video is larger than `100000` bytes
- every video opens through OpenCV
- every video has non-zero frame count
- sampled first/mid/final frames pass a nonblank luma check
- stdout/stderr and common logs for both visual reruns were scanned for:
  - `Traceback`
  - `RuntimeError`
  - `Exception`
  - `CUDA out of memory`
  - `segmentation fault`
  - `Aborted`
  - `Killed`

No matching fatal-error signature was found. Local visual inspection of the two
contact sheets found the scenes, top-down paths, and condition labels visible
and usable for qualitative paper evidence.

## Claim Boundary

These assets support this paper use:

```text
Selected original/noMDL rollout videos and still frames illustrate that the
official KuJiaLe scene remains visually renderable and navigable in selected
InternNav episodes after noMDL conversion.
```

They do not support these stronger uses:

- replacing the full `33`-episode paired metrics
- claiming deterministic per-episode outcome preservation
- claiming GRScenes downstream validity
- claiming broad R2R / MP3D benchmark reproduction

For the manuscript, cite the full paired metrics for quantitative claims and
use the selected videos/stills as qualitative examples only.

## Residual Risks

- The visual rerun is selected-only and covers `6` episodes, not the full
  `33`-episode evaluation.
- The selected visual rerun outcomes are not identical to the full-run
  per-episode outcomes for every case.
- The generated contact sheets are figure candidates. Final paper styling may
  still need caption, crop, or typography adjustment in the camera-ready figure
  pipeline.
