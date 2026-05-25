# 2026-05-25 InternNav Official noMDL Pair Results

## Context

This note records the completed controlled paired InternNav downstream
experiment prepared in
[2026-05-25-internnav-official-nomdl-pair-preparation.md](2026-05-25-internnav-official-nomdl-pair-preparation.md).

The experiment uses the official public InteriorAgent / KuJiaLe
`kujiale_0031` scene and the same `33`
`val_unseen_kujiale0031_33` episodes for both conditions:

- original official scene
- scratch noMDL-converted scene produced by ConvertAsset

This result intentionally replaces the earlier unverified GRScenes InternNav
attempts as the downstream navigation sanity evidence. It is still a controlled
single-scene sanity check, not a broad GRScenes or R2R / MP3D benchmark.

## Inputs

Original result:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/official_kujiale0031_33/result.json
```

noMDL result:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/official_kujiale0031_nomdl_33/result.json
```

noMDL scene entrypoint:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl/kujiale_0031/kujiale_0031.usda
```

noMDL evaluation config:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/configs/internvla_n1_kujiale0031_nomdl_33_eval_cfg.py
```

The noMDL scene was statically verified before evaluation:

| Check | Value |
| --- | ---: |
| Stage opened | `True` |
| Prim count | `23899` |
| Shader count | `14403` |
| `UsdPreviewSurface` shader count | `2062` |
| Active MDL shader ID count | `0` |
| Active MDL source asset count | `0` |
| MDL-named placeholder properties | `2124` |

The MDL-named placeholder properties are blocked
`"__noMDL_placeholder__"` outputs and should not be counted as active MDL
materials.

## noMDL Runtime Result

The noMDL full run completed all `33` episodes with exit code `0`.

Progress log:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/official_kujiale0031_nomdl_33/progress/official_kujiale0031_nomdl_33.log
```

Final result:

| Metric | noMDL value |
| --- | ---: |
| `Count` | `33` |
| `SR` | `0.5758` |
| `SPL` | `0.4955` |
| `OS` | `0.7879` |
| `NE` | `3.1024` |
| `TL` | `5.805` |
| `FR` | `0.0` |
| `StR` | `0.0` |

Episode finish counts from the noMDL progress log:

| noMDL episode result | Count |
| --- | ---: |
| `success` | `19` |
| `not_reach_goal` | `13` |
| `exceed_total_max_step` | `1` |

The one `exceed_total_max_step` episode was `464_464`; it terminated normally
after `1100` steps and did not hang the run.

## Paired Aggregate Comparison

Paired analysis output:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/analysis/paired_33_summary.json
```

Repository-side copies:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_kujiale0031_33/
```

Aggregate comparison:

| Metric | Original | noMDL | noMDL - original | Direction |
| --- | ---: | ---: | ---: | --- |
| `Count` | `33` | `33` | `0` | same |
| `SR` | `0.5152` | `0.5758` | `+0.0606` | higher is better |
| `SPL` | `0.4793` | `0.4955` | `+0.0163` | higher is better |
| `OS` | `0.8182` | `0.7879` | `-0.0303` | higher is better |
| `NE` | `3.0653` | `3.1024` | `+0.0371` | lower is better |
| `TL` | `6.097` | `5.805` | `-0.2920` | lower is better |
| `steps` | `172.0606` | `210.6667` | `+38.6061` | lower is better |

The paired analyzer also recorded:

| Metric | noMDL better | original better | tie |
| --- | ---: | ---: | ---: |
| `SR` | `5` | `3` | `25` |
| `SPL` | `9` | `9` | `15` |
| `OS` | `2` | `3` | `28` |
| `NE` | `18` | `15` | `0` |
| `TL` | `19` | `14` | `0` |
| `steps` | `15` | `15` | `3` |

## Per-Episode Outcome Transitions

Transition artifacts:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/analysis/paired_episode_transitions.json
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/analysis/paired_episode_transitions.csv
```

Outcome transitions:

| Transition | Count | Episodes |
| --- | ---: | --- |
| `success -> success` | `14` | `465_465`, `467_467`, `471_471`, `473_473`, `474_474`, `476_476`, `477_477`, `481_481`, `482_482`, `484_484`, `486_486`, `487_487`, `488_488`, `490_490` |
| `success -> fail` | `3` | `485_485`, `491_491`, `494_494` |
| `fail -> success` | `5` | `470_470`, `472_472`, `478_478`, `479_479`, `492_492` |
| `fail -> fail` | `11` | `462_462`, `463_463`, `464_464`, `466_466`, `468_468`, `469_469`, `475_475`, `480_480`, `483_483`, `489_489`, `493_493` |

Failure-pair counts from the paired analyzer:

| Failure pair | Count |
| --- | ---: |
| `original_not_reach_goal__modified_success` | `5` |
| `original_success__modified_not_reach_goal` | `3` |
| `original_success__modified_success` | `14` |
| `original_not_reach_goal__modified_not_reach_goal` | `10` |
| `original_not_reach_goal__modified_exceed_total_max_step` | `1` |

## Verification

Post-run checks:

- parsed the noMDL `result.json` and confirmed `Count=33`
- confirmed the noMDL progress log reached `[33/33]`
- confirmed no remaining `official_kujiale0031_nomdl_33` /
  `run_internnav_eval.py` / Isaac Python eval process
- searched noMDL stdout/stderr and common logs for:
  - `Traceback`
  - `RuntimeError`
  - `Exception`
  - `CUDA out of memory`
  - `segmentation fault`
  - `Aborted`
  - `Killed`

No matching crash or fatal-error signature was found.

The per-episode metrics were extracted with:

```bash
PYTHONPATH=/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523/python_target:/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523/internutopia_probe:/cpfs/user/zhuzihou/dev/InternNav \
python /cpfs/user/zhuzihou/dev/ConvertAsset/paper/shared/evidence/experiments/07_internnav_vln_downstream/extract_episode_metrics.py \
  --condition nomdl \
  --lmdb-dir /cpfs/user/zhuzihou/dev/InternNav/data/sample_episodes/official_kujiale0031_nomdl_33/sample_data0.lmdb \
  --output /cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/analysis/nomdl_episodes.jsonl
```

The paired summary was produced with:

```bash
PYTHONPATH=/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523/python_target:/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523/internutopia_probe:/cpfs/user/zhuzihou/dev/InternNav \
python /cpfs/user/zhuzihou/dev/ConvertAsset/paper/shared/evidence/experiments/07_internnav_vln_downstream/analyze_paired_metrics.py \
  --input-jsonl /cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/analysis/original_episodes.jsonl \
  --input-jsonl /cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/analysis/nomdl_episodes.jsonl \
  --output /cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/analysis/paired_33_summary.json \
  --has-aggregate-result-json
```

## Claim Boundary

This completed pair supports the following paper-facing statement:

```text
On an official public InternNav-compatible InteriorAgent / KuJiaLe scene where
the original MDL scene already obtains non-zero VLN performance, the
ConvertAsset noMDL-converted scene completes the same 33-episode evaluation and
retains non-zero downstream SR/SPL with comparable aggregate performance.
```

This is suitable as a controlled downstream sanity result or ablation row when
the manuscript clearly labels it as one official KuJiaLe scene with `33`
episodes.

This result should not be framed as:

- a broad GRScenes downstream navigation benchmark
- a reproduction of official R2R / MP3D numbers
- proof that noMDL preserves navigation behavior across all scenes
- proof that the earlier unverified GRScenes InternNav runs are valid

The paired analysis helper reports `acl_main_result_ready=false` because its
automated gate expects at least `100` paired episodes, at least `10` scenes, and
a video manifest. That gate is stricter than this controlled sanity experiment.
For an ACL manuscript, this result can be cited only with the narrow scope
above unless additional scenes or a larger official benchmark are run.

## Visual Assets

Selected video reruns, still frames, figure candidates, QA evidence, and their
qualitative claim boundary are recorded in
[2026-05-25-internnav-official-visual-assets.md](2026-05-25-internnav-official-visual-assets.md).

Those visual assets are for paper-body and supplement illustration only. The
full `33`-episode paired metrics in this note remain the authoritative
quantitative downstream result.

## Residual Risks

- The experiment covers one official KuJiaLe scene and `33` episodes.
- The noMDL run has one long terminating episode
  (`464_464`, `exceed_total_max_step`), so per-episode transitions should be
  reported instead of only aggregate means.
- Rendering-level visual equivalence was not re-audited in this result note;
  this document only records static noMDL USD verification and InternNav
  downstream behavior.
- The official R2R / MP3D-PE path remains blocked locally unless the gated scene
  package is made available.
