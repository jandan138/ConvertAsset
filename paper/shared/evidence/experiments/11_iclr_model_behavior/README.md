# ICLR model behavior experiments

## Research structure

Material intervention → query-conditioned localization → visual/readout mechanism → navigation.
The paper keeps downstream navigation in the main text. Implementation and detailed
source scope are in the appendix, rather than repeated as prose qualifiers.

## Recompute and build

From the repository root:

```bash
python -m pytest -q tests/test_iclr_model_behavior.py tests/test_grscenes_vlm_score_grounding.py tests/test_grscenes_vlm_prediction_runner.py
make -C paper iclr27
make -C paper iclr27-check
make -C paper iclr27-stage
```

`analyze.py` requires only Python's standard library. Image preparation needs Pillow;
figure generation needs NumPy/Matplotlib/Pillow. Heavy dependencies remain lazy in
the model engines. `models.json` maps model names to checkpoint and Python paths;
copy it to an experiment-specific config to run on another machine.

## Completed clean-image experiment

`interventions_clean_v2/manifest.json` uses exactly the four repaired source pairs
in `material_effect_baseline/qualitative_render_manifest.json`. It makes four
two-view boards, queries both targets, and swaps their positions. Sixteen paired
queries are evaluated per family: category, action, target-window crossover and
context-window crossover. Ground-truth boxes are transformed with the image but
never provided to the model. The neutral center gutter cannot hit a target.

Three models completed all 128 image queries each: Qwen3-VL-2B, Qwen3-VL-8B and
Gemma4-E4B. `runs_clean_v2/campaign.json` stores commands/return codes; per-model
directories contain raw JSONL, final metadata and frozen engine source.

To regenerate in a **new versioned output directory**:

```bash
python paper/shared/evidence/experiments/11_iclr_model_behavior/prepare_interventions.py \
  --out paper/shared/evidence/raw/iclr_model_behavior/interventions_clean_v3 \
  --verified-cases paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json
python paper/shared/evidence/experiments/11_iclr_model_behavior/campaign.py \
  --manifest paper/shared/evidence/raw/iclr_model_behavior/interventions_clean_v3/manifest.json \
  --out paper/shared/evidence/raw/iclr_model_behavior/runs_clean_v3
```

The larger `interventions_v1` development run uses twelve archive targets and
contains legacy render artifacts. It is not the clean material-mechanism result.

## Estimands

- Success: correct, in-image, parsed point / **all** requested queries.
- Coverage: numeric point present / all queries.
- Conditional accuracy: hits / numeric points, stored separately.
- Delta: paired success differences with the same denominator and query IDs.
- Distance: map requested coordinates to image pixels first, then compute L2.
- Repeated views: clustered by target; composite queries/positions clustered by board.
- View-set change: compare actual successful-view sets, not their counts.
- Image hashes: report changed/missing/unstamped images explicitly. Two old canonical
  files each refer to eight subsequently replaced images; current close-view table
  rows are ID-subsets of the later 80-pair runs.

## Fresh rendering and navigation follow-up

```bash
./scripts/isaac_python.sh paper/shared/evidence/experiments/11_iclr_model_behavior/rerender_views.py \
  --out paper/shared/evidence/raw/iclr_model_behavior/rtx_next --limit-targets 1
python paper/shared/evidence/experiments/11_iclr_model_behavior/prepare_navigation_followup.py
```

The RTX smoke attempted in this migration did not yield a usable pair: the
original capture timed out. Its report and logs remain under `rtx_smoke_v1/`.
The navigation command prepares a deterministic 12-episode selection and 72 jobs
for repeats and identical-state observations; it does not execute them. Full
navigation evaluation uses the existing `07_internnav_vln_downstream/` runtime.

## Next main-story experiments

1. Resolve source-MDL/viewport runtime behavior and produce off-axis views of new
   targets across additional scenes, fixed before model inference.
2. Extend from rectangular image-window crossovers to independently authored shader
   factors (base color, roughness and texture) at fixed cameras.
3. Execute same-condition navigation repeats, then matched-state observations and
   policy probes to connect perceptual changes to trajectory divergence.
4. Fix model-native output adapters on a separate calibration split and evaluate
   them on held-out scene/target inputs. The historical raw-vs-normalized rescoring
   is diagnostic, not a held-out calibration experiment.

Current output registry: `paper/shared/evidence/results_manifest.yaml`.
