# 2026-05-25 InternNav Official Sanity Check

## Context

This note records a sanity check run performed before using InternNav as
downstream evidence for ConvertAsset paper claims.

The purpose was intentionally narrow: verify that the local InternNav runtime,
checkpoint, Isaac Sim wrapper, and official public navigation data path can
produce a non-zero success signal without hanging. This is not a GRScenes
original-vs-noMDL result and should not be cited as evidence that ConvertAsset
preserves or improves downstream navigation performance.

At the start of the run, the reported storage state was:

- total capacity: `1600.0 GiB`
- used capacity: `1122.6920623779297 GiB`
- estimated free capacity: `477.31 GiB`

Storage capacity was therefore not the limiting factor for this sanity check.

## Research / Investigation

The preferred official R2R / MP3D-PE route was checked first because it matches
the standard InternVLA-N1 evaluation configuration more closely. The local
InternNav tree had the R2R evaluation config and the `InternVLA-N1-DualVLN`
checkpoint, but the required MP3D-PE scene package was not locally available.
The scene download route required gated access, so that path was not used for
this reproducibility check.

The run instead used public official InteriorAgent data:

- scene repository: `spatialverse/InteriorAgent`
- navigation repository: `spatialverse/InteriorAgent_Nav`
- source split: `val_unseen`
- scene: `kujiale_0031`
- episode count: `33`

The selected subset is still an official public InternNav-compatible input, but
it is a KuJiaLe / InteriorAgent sanity subset rather than an R2R / MP3D paper
benchmark.

## Prepared Inputs

Prepared workspace:

```text
/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525
```

Generated subset:

```text
/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525/interiornav_data/raw_data/val_unseen_kujiale0031_33/val_unseen_kujiale0031_33.json.gz
```

Downloaded scene directory:

```text
/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525/interiornav_data/scene_data/kujiale_0031
```

Generated InternNav config:

```text
/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525/configs/internvla_n1_kujiale0031_33_eval_cfg.py
```

Input manifest:

```text
/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525/official_kujiale0031_33_manifest.json
```

Important config choices:

| Field | Value |
| --- | --- |
| `model_name` | `internvla_n1` |
| `model_path` | `/cpfs/user/zhuzihou/dev/InternNav/checkpoints/InternVLA-N1-DualVLN` |
| `scene_type` | `kujiale` |
| `dataset_type` | `kujiale` |
| `split_data_types` | `['val_unseen_kujiale0031_33']` |
| `task_name` | `official_kujiale0031_33` |
| `env_num` | `1` |
| `vis_output` | `False` |

## Runtime Command

The run used the ConvertAsset Isaac wrapper and the external InternNav runtime
dependency root:

```bash
PYTHONPATH=/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523/python_target:/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523/internutopia_probe:/cpfs/user/zhuzihou/dev/InternNav \
HF_HOME=/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523/hf_cache \
HF_HUB_DISABLE_XET=1 \
/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/scripts/isaac_python.sh \
  /cpfs/user/zhuzihou/dev/ConvertAsset/paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py \
  --config /cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525/configs/internvla_n1_kujiale0031_33_eval_cfg.py \
  --internnav-root /cpfs/user/zhuzihou/dev/InternNav \
  --runtime-deps-root /cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523
```

Captured stdout/stderr:

```text
/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525/logs/official_kujiale0031_33_stdout_stderr.log
```

The first attempted full-run launch used `./scripts/isaac_python.sh` from the
InternNav root and failed before evaluation because that wrapper does not exist
there. The successful run used the absolute ConvertAsset wrapper path shown
above.

## Results

Final result file:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/official_kujiale0031_33/result.json
```

Final aggregate metrics:

| Metric | Value |
| --- | ---: |
| `Count` | `33` |
| `SR` | `0.5152` |
| `SPL` | `0.4793` |
| `OS` | `0.8182` |
| `TL` | `6.097` |
| `NE` | `3.0653` |
| `FR` | `0.0` |
| `StR` | `0.0` |

Progress log:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/official_kujiale0031_33/progress/official_kujiale0031_33.log
```

The progress log recorded `33` finished episodes:

| Episode result | Count |
| --- | ---: |
| `success` | `17` |
| `not_reach_goal` | `16` |

The first completion was:

```text
[2026-05-25 10:43:03,172][INFO] [1/33][step_index:286] finish: [trajectory_id:494_494][duration:121.81 s][step_count:286][fps:2.35][result:success]
```

The final completion was:

```text
[2026-05-25 11:06:16,813][INFO] [33/33][step_index:150] finish: [trajectory_id:462_462][duration:29.57 s][step_count:150][fps:5.07][result:not_reach_goal]
```

## Verification

Verification checks performed after the run:

- parsed `result.json` and confirmed:
  - `Count >= 30`
  - `SR > 0`
  - `SPL > 0`
- confirmed the progress log had `33` finished episodes
- confirmed the evaluation process exited normally with exit code `0`
- checked there was no remaining `official_kujiale0031_33` /
  `run_internnav_eval.py` / Isaac Python eval process
- searched stdout/stderr and the InternNav common log for:
  - `Traceback`
  - `RuntimeError`
  - `Exception`
  - `CUDA out of memory`
  - `segmentation fault`
  - `Aborted`
  - `Killed`

No matching crash or fatal-error signature was found in those logs.

## Claim Boundary

This run supports the following claim:

```text
The local InternNav installation can complete an official public InteriorAgent
evaluation subset with at least 30 completed episodes, non-zero SR, non-zero
SPL, and no observed runtime hang.
```

This run does not support the following stronger claims:

- that the local setup reproduces the official R2R / MP3D paper numbers
- that ConvertAsset noMDL conversion preserves InternNav navigation behavior
- that GRScenes original and noMDL variants are ready for paper-facing paired
  downstream metrics

Those claims still require a separate paired GRScenes experiment with matching
original and noMDL inputs, per-episode provenance, and a complete aggregate
analysis.

## ACL Downstream Evidence Strategy

After this sanity check, the downstream evidence path should shift away from
the previously attempted unverified GRScenes InternNav runs.

The reason is attribution. In the GRScenes attempts, the original baseline did
not produce a reliable non-zero SR/SPL signal and several custom episodes had
reset or warm-up compatibility problems. That makes the result hard to
interpret: a failure could come from the GRScenes episode construction,
coordinate or height discontinuities, InternNav scene compatibility, or the
asset conversion itself.

For ACL paper evidence, the stronger next experiment is therefore a controlled
paired run on the official KuJiaLe scene that already succeeded:

```text
official InteriorAgent / KuJiaLe `kujiale_0031`
same `val_unseen_kujiale0031_33` 33-episode subset
original scene baseline: Count=33, SR=0.5152, SPL=0.4793
noMDL converted scene: Count=33, SR=0.5758, SPL=0.4955
```

The noMDL preparation and final paired result are recorded in
[2026-05-25-internnav-official-nomdl-pair-preparation.md](2026-05-25-internnav-official-nomdl-pair-preparation.md)
and
[2026-05-25-internnav-official-nomdl-pair-results.md](2026-05-25-internnav-official-nomdl-pair-results.md).

The completed paired run supports this narrow claim:

```text
On an official public InternNav-compatible InteriorAgent scene where the
baseline model obtains non-zero performance, the noMDL-converted scene still
supports downstream VLN evaluation with non-zero SR/SPL.
```

This is a defensible ACL downstream sanity check. It should not be written as a
general claim that ConvertAsset preserves navigation performance across all
GRScenes assets.

### Paper-Use Gate

The completed result satisfies the original paper-use gate for a controlled
downstream sanity table:

- the noMDL scene loads in Isaac Sim and reaches InternNav action execution
- the noMDL run completes at least `30 / 33` episodes
- the noMDL aggregate has `SR > 0` and `SPL > 0`
- there is no runtime hang or fatal error signature
- paired per-episode outcomes are reported:
  - `success -> success`
  - `success -> fail`
  - `fail -> success`
  - `fail -> fail`
- the text clearly labels the result as an official KuJiaLe controlled sanity
  check, not a GRScenes benchmark

If noMDL SR/SPL are close to the original baseline, the manuscript can describe
the downstream signal as largely preserved for this controlled scene. If SR/SPL
drop substantially, the result should be framed as downstream sensitivity or a
limitation rather than as preservation evidence.

As of the paired result note, the noMDL smoke and full `33`-episode paired run
have completed. The result is paper-facing only as a controlled single-scene
KuJiaLe downstream sanity check, not as a broad navigation benchmark.

### Role of GRScenes After This Decision

GRScenes should remain useful for the paper's existing evidence types:

- visual fidelity comparisons
- feature-similarity metrics
- startup and warm-up performance measurements
- qualitative full-scene examples

Until a GRScenes original InternNav baseline produces a reliable non-zero
signal, GRScenes should not be used as the main InternNav downstream evidence.

## Residual Risks

- The official R2R / MP3D-PE path remains blocked locally unless the gated scene
  package is made available.
- The evaluated subset is one KuJiaLe scene with 33 episodes, so it is a runtime
  sanity check rather than a broad benchmark.
- The helper wrapper used for the run lives in the `/cpfs/user/zhuzihou/dev`
  ConvertAsset copy, while this documentation is stored in the active
  `/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset` repository. Treat the
  absolute paths above as run provenance, not as portable repository-relative
  instructions.
