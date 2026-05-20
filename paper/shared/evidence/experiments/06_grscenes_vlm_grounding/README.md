# GRScenes VLM Grounding Experiment

This experiment is the ACL-oriented material-generalization study. It measures whether ConvertAsset's MDL-to-UsdPreviewSurface conversion changes VLM grounding behavior on realistic USD indoor scenes.

## Benchmark Basis

- Benchmark source: GRScenes-100 original benchmark package under
  `/cpfs/user/zhuzihou/assets/zzh-grscenes`.
- Intervention: ConvertAsset no-MDL conversion.
- Protocol: PIO-style precise visual grounding prompts.
- Downstream extension: InternNav / VL-LN navigation after the grounding pilot is stable.

The benchmark source provides scene USDs, metadata, and episodes:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes/scenes/GRScenes-100
/cpfs/user/zhuzihou/assets/zzh-grscenes/benchmark/mm_episodes.json
/cpfs/user/zhuzihou/assets/zzh-grscenes/benchmark/sn_episodes.json
```

Local inventory checked on 2026-05-20:

- 69 home scenes and 30 commercial scenes, 99 total.
- Each scene has `start_result_raw.usd`, `start_result_navigation.usd`, `start_result_interaction.usd`, `metadata.json`, and `interactive_obj_list.json`.
- `mm_episodes.json` covers 30 home scenes and 420 episodes.
- `sn_episodes.json` covers the same 30 home scenes and 300 episodes.
- Commercial scenes have no local `mm_episodes.json` / `sn_episodes.json` coverage, so they should be treated as metadata-driven material stress tests unless a future episode source is added.
- The first ACL/VLM episode-backed pilot should select from the 30 episode-covered home scenes before claiming broader 99-scene coverage.

Treat this tree as immutable. It is the source for scene selection and paper claims, not a place to write generated sidecars.

Two source-tree details matter for runners:

- Scene-local `Materials` and `models` entries are pointer files containing relative paths, not symlinks.
- Scene USDs use `.usd` names but may contain binary USDC data, so validation should open them through `pxr` or Isaac Sim.

## Engineering Validation Data

The restored test0 mirror is only for ConvertAsset smoke tests, runner debugging, and path validation. Do not cite it as the benchmark source.

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100
```

First smoke-test scene:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100/home/MV7J6NIKTKJZ2AABAAAAADQ8_usd/layout.usd
```

The existing no-MDL work tree for this mirror is:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset_no_mdl_work_20260520/GRScenes100
```

Convert command template:

```bash
./scripts/isaac_python.sh ./main.py no-mdl /path/to/scratch-copy/start_result_raw.usd
```

Conversion outputs for the ACL/VLM benchmark must be generated from a scratch copy of selected benchmark scenes, for example under:

```text
/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520
```

The paired material conditions are:

- Original benchmark USD: `start_result_raw.usd`, `start_result_navigation.usd`, or `start_result_interaction.usd`, depending on the task.
- Converted scratch derivative: the no-MDL USD generated outside the immutable benchmark source tree.

PIO is a prompt and metric inspiration here. Do not write that this experiment evaluates on PIO unless a later protocol actually imports the PIO dataset.

## Source Manifest

Before rendering, generate the source/episode manifest:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_source_manifest.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/source_manifest.json
```

This manifest is not a VLM result. It fixes provenance and selection for the first pilot:

- 5 episode-backed home scenes.
- 5 metadata-driven commercial stress scenes.
- 8 uniquely metadata-mapped episode targets per home scene, 40 episode records total.
- Scratch paths mirror the original GRScenes layout under `/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520`.
- `excluded_episode_records` captures episode records that fail the current source-mapping gate.

The current no-MDL CLI writes `*_noMDL.usd` beside the input USD. Until an explicit `--out-root` path exists, never run it directly on `/cpfs/user/zhuzihou/assets/zzh-grscenes`; copy selected scenes into the scratch tree first.

## Task Families

| Task | Prompt shape | Metric |
|---|---|---|
| S1 referred object localization | "Point to the {attribute} {category}." | point-in-box or point-in-mask accuracy |
| S2 task-driven grounding | "Where should the robot interact to {action}?" | part/object region hit rate |
| S3 navigation proxy | "Which object should the robot move toward to {goal}?" | target-region accuracy and answer consistency |

## Planned Outputs

Do not cite these files in the paper until they exist and are registered in `paper/shared/evidence/results_manifest.yaml`.

```text
paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json
paper/shared/evidence/raw/grscene_vlm_grounding/predictions.jsonl
paper/shared/evidence/raw/grscene_vlm_grounding/score_summary.json
```

Scoring command:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/score_summary.json
```
