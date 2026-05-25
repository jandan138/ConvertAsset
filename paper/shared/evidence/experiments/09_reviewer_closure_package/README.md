# Reviewer-Closure Package

This experiment package turns existing evidence into reviewer-facing closure
artifacts without running new simulator or model jobs.

It produces three outputs:

1. paired bootstrap confidence intervals for the existing expanded30 VLM stress
   results and official KuJiaLe InternNav `val_unseen` results;
2. deterministic coordinate-only baselines for the expanded30 VLM scoring
   protocol;
3. a lightweight safe-conversion rule table derived from the material-effect
   risk matrix.

Run:

```bash
python paper/shared/evidence/experiments/09_reviewer_closure_package/build_reviewer_closure_package.py
```

Default raw outputs:

```text
paper/shared/evidence/raw/reviewer_closure_package/reviewer_closure_statistical_summary.json
paper/shared/evidence/raw/reviewer_closure_package/vlm_coordinate_baseline_summary.json
paper/shared/evidence/raw/reviewer_closure_package/material_safe_conversion_recommender.json
paper/shared/evidence/raw/reviewer_closure_package/vlm_coordinate_baselines/
```

Default table outputs:

```text
paper/shared/tables/reviewer_closure_paired_ci.csv
paper/shared/tables/tab_reviewer_closure_paired_ci.tex
paper/shared/tables/vlm_coordinate_baselines.csv
paper/shared/tables/tab_vlm_coordinate_baselines.tex
paper/shared/tables/material_safe_conversion_recommender.csv
paper/shared/tables/tab_material_safe_conversion_recommender.tex
```

## Claim Boundary

The paired intervals are descriptive bootstrap intervals over the frozen
evidence pools. They are not population-level significance claims.

The coordinate baselines are not VLM predictions. They calibrate scoring and
show that raw pixel point-in-box can be saturated by target-centered cameras.

The safe-conversion recommender is a rule table derived from selected
material-effect evidence. It is not a learned classifier and should not be
presented as an automatic material-risk predictor.
