# GRScenes VLM Grounding Experiment

This experiment is the ACL-oriented material-generalization study. It measures whether ConvertAsset's MDL-to-UsdPreviewSurface conversion changes VLM grounding behavior on realistic USD indoor scenes.

## Benchmark Basis

- Dataset: GRScenes-100 USD scenes.
- Intervention: ConvertAsset no-MDL conversion.
- Protocol: PIO-style precise visual grounding prompts.
- Downstream extension: InternNav / VL-LN navigation after the grounding pilot is stable.

## Local Pilot Data

Dataset root:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100
```

First smoke-test scene:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100/home/MV7J6NIKTKJZ2AABAAAAADQ8_usd/layout.usd
```

Convert command template:

```bash
./scripts/isaac_python.sh ./main.py no-mdl /path/to/layout.usd
```

The paired material conditions are:

- `layout.usd`
- `layout_noMDL.usd`

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
