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
- 8 metadata-mapped episode records per home scene, 40 episode records total. These are not guaranteed to be 40 unique spatial targets because `mm` and `sn` episodes can repeat the same object.
- Scratch paths mirror the original GRScenes layout under `/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520`.
- `excluded_episode_records` captures episode records that fail the current source-mapping gate.

The current no-MDL CLI writes `*_noMDL.usd` beside the input USD. Until an explicit `--out-root` path exists, never run it directly on `/cpfs/user/zhuzihou/assets/zzh-grscenes`; copy selected scenes into the scratch tree first.

## Target Manifest

Before rendering, resolve the selected episode targets to USD prims and world-space bboxes:

```bash
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/target_manifest.json
```

This manifest is also not a VLM result. It is the camera-target localization gate for paired rendering:

- 5 episode-backed home scenes attempted.
- 40 episode records attempted.
- 40 episode records resolved to USD prim paths and world-space bboxes.
- 23 unique `(scene, object_instance_id, target_prim_path)` targets after duplicate episode records are collapsed.
- 17 duplicate episode-record targets, with at most 2 episode records mapped to the same unique target.
- Resolution uses authored USD reference paths first, with exact prim-suffix fallback for objects whose `interactive_obj_list.json` coverage is incomplete.
- Bboxes use the absolute split-level model USD bbox transformed by the scene prim transform (`model_local_bbox_x_scene_xform`), because scene-local `models` pointer files are regular text files rather than symlinks and composed scene bbox warnings are expected.

For command-line smoke tests, use:

```bash
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py \
  --limit-scenes 1 \
  --out /tmp/grscene_target_manifest_smoke.json
```

USD may emit broken relative-reference warnings when opening the original scene USDs. Those warnings are expected for the immutable source layout and do not imply that the resolver modified the source dataset.

## Render Manifest

Before rendering images, generate the paired view/job plan:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json
```

This manifest is a render plan and provenance bridge, not rendered image evidence and not a VLM result:

- 40 resolved episode records are collapsed into 23 unique spatial render targets.
- Four target-centered static orbit views are planned per unique target.
- The current pilot therefore has 92 original/converted render pairs and 184 material-condition render jobs.
- Original jobs point at immutable benchmark source USDs and have material inputs available, but camera-stage authoring is still pending.
- Converted jobs point at scratch no-MDL USDs and are currently `blocked_missing_material_input` until selected scenes are copied and converted outside `/cpfs/user/zhuzihou/assets/zzh-grscenes`.
- Each pair stores one shared camera plan so original and converted renders differ only by material condition once the scratch derivative exists.
- No job is `render_jobs_ready_to_run` yet because camera USD stages have not been authored.
- Image-space target bboxes remain `pending_projection_from_world_bbox`; scoring must not run until the renderer projects bboxes or masks into image coordinates.
- Each planned image record includes a `visual_review` packet marker for the clean-room `render-visual-reviewer` skill.

Use `--require-converted` after scratch conversion to fail fast if any converted USD is still missing.

## Task Families

| Task | Prompt shape | Metric |
|---|---|---|
| S1 referred object localization | "Point to the {category}." for the current render-plan gate; attribute-augmented prompts are a later extension after image-space labels exist. | point-in-box or point-in-mask accuracy |
| S2 task-driven grounding | "Where should the robot interact to {action}?" | part/object region hit rate |
| S3 navigation proxy | "Which object should the robot move toward to {goal}?" | target-region accuracy and answer consistency |

## Planned Outputs

Do not cite these files as task-performance evidence until the corresponding rendered images, image-space labels, predictions, and score summaries exist and are registered in `paper/shared/evidence/results_manifest.yaml`.

```text
paper/shared/evidence/raw/grscene_vlm_grounding/target_manifest.json
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
