# 2026-05-20 ACL VLM Benchmark Route

## Summary

The ACL route should use GRScenes-100 USD scenes as the asset substrate and evaluate VLM grounding under ConvertAsset's MDL-to-UsdPreviewSurface intervention. The primary benchmark direction is a PIO-style precise visual grounding pilot. InternNav / VL-LN should be treated as the downstream navigation extension after the grounding pilot is reproducible.

## Investigation

Sources checked on 2026-05-20:

- GRScenes-100 dataset card: https://huggingface.co/datasets/InternRobotics/GRScenes
- InternNav repository: https://github.com/InternRobotics/InternNav
- InternNav VL-LN benchmark docs: https://internrobotics.github.io/user_guide/internnav/projects/benchmark.html
- PIO project page: https://research.nvidia.com/labs/cosmos-lab/pio/
- PIO dataset card: https://huggingface.co/datasets/pio-benchmark/PIO
- BEHAVIOR-1K overview: https://behavior.stanford.edu/

## Decision

Use **GRScenes-100 + PIO-style VLM grounding** as the first reproducible ACL experiment.

Reasons:

- The local dataset is already available under `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100`.
- GRScenes is USD-native and uses MDL materials, so ConvertAsset creates a clean paired intervention.
- PIO-style object localization and task-driven grounding align with ACL/VLM embodied language evaluation.
- The pilot can be scored without committing to a full navigation training stack.

InternNav / VL-LN remains valuable, but it should follow the grounding pilot because it introduces more simulator, policy, and evaluation dependencies.

## Files Added

- `paper/shared/evidence/references/acl_vlm_benchmark_selection.md`
- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/protocol.yaml`
- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`

## Verification

Planned verification for this documentation/scaffold change:

- Python syntax check for `score_grounding.py`.
- Unit-like scorer smoke test with synthetic prediction records.
- `tests/test_paper_layout.py` for paper tree consistency.
- `git diff --check`.

## Open Work

- Implement the render manifest generator for selected GRScenes scenes.
- Add an Isaac Sim runner that renders paired original/no-MDL views around semantic target prims.
- Add a VLM inference runner for coordinate-capable open models.
- Register real raw outputs in `paper/shared/evidence/results_manifest.yaml` only after the pilot produces checked files.
