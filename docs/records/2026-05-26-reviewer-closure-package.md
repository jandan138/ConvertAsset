# 2026-05-26 Reviewer Closure Package

## Scope

Implemented the reviewer-closure package requested after the material-effect
baseline and official InternNav evidence runs.

The package does not run new simulator, VLM, or InternNav jobs. It converts the
existing evidence into paper-ready closure artifacts:

- paired bootstrap confidence intervals for VLM and InternNav evidence;
- deterministic coordinate-only point baselines for the expanded30 VLM stress
  set;
- a lightweight safe-conversion rule table derived from the material-effect
  risk matrix.

## Generated Evidence

Raw package outputs:

```text
paper/shared/evidence/raw/reviewer_closure_package/reviewer_closure_statistical_summary.json
paper/shared/evidence/raw/reviewer_closure_package/vlm_coordinate_baseline_summary.json
paper/shared/evidence/raw/reviewer_closure_package/material_safe_conversion_recommender.json
paper/shared/evidence/raw/reviewer_closure_package/vlm_coordinate_baselines/
```

Table outputs:

```text
paper/shared/tables/reviewer_closure_paired_ci.csv
paper/shared/tables/tab_reviewer_closure_paired_ci.tex
paper/shared/tables/vlm_coordinate_baselines.csv
paper/shared/tables/tab_vlm_coordinate_baselines.tex
paper/shared/tables/material_safe_conversion_recommender.csv
paper/shared/tables/tab_material_safe_conversion_recommender.tex
```

Generator:

```text
paper/shared/evidence/experiments/09_reviewer_closure_package/build_reviewer_closure_package.py
```

## Main Numbers

VLM expanded30 paired bootstrap deltas:

| Evidence | Metric | Delta | 95% CI |
| --- | --- | ---: | --- |
| Gemma4 | normalized-1000 point | `+0.0667` | `[0.0000, 0.1667]` |
| Qwen2.5-VL | raw point diagnostic | `-0.1429` | `[-0.3214, 0.0000]` |

Official KuJiaLe InternNav `val_unseen` paired bootstrap deltas:

| Metric | Delta noMDL - original | 95% CI |
| --- | ---: | --- |
| `SR` | `-0.0404` | `[-0.1515, 0.0707]` |
| `SPL` | `-0.0441` | `[-0.1417, 0.0514]` |
| `NE` | `-0.0492` | `[-0.6464, 0.5386]` |
| `TL` | `+0.0844` | `[-0.7366, 0.9304]` |

Coordinate-only baseline finding:

- `image_center_pixel` and `bbox_center_pixel` both score `30/30` under raw
  pixel point-in-box because the stress cameras are target-centered.
- `bbox_center_normalized_1000` scores `30/30` under the normalized-1000 metric.
- These are scoring/camera sanity baselines, not model evidence.

Safe-conversion rule table:

- `opacity_transparency`, `emission`, `normal_bump`, and
  `displacement_height`: bounded-low risk with static and selected visual gates.
- `clearcoat`: manual-review high risk; ConvertAsset approximation needs visual
  review and NVIDIA output needs target-retention gating.
- `procedural_texture`: high risk; keep MDL or bake/investigate before claiming
  preservation.

## Paper Integration

Updated:

- `paper/shared/sections/experiments.tex`
- `paper/shared/sections/appendix.tex`
- `paper/shared/sections/discussion.tex`
- `paper/shared/evidence/claims.yaml`
- `paper/shared/evidence/results_manifest.yaml`
- `paper/shared/tables/README.md`

## Verification

Executed verification:

```bash
python paper/shared/evidence/experiments/09_reviewer_closure_package/build_reviewer_closure_package.py
python -m pytest -q tests/test_reviewer_closure_package.py tests/test_paper_layout.py tests/test_paper_vlm_coordinate_ablation.py tests/test_material_effect_baseline_risk_matrix.py
python -m py_compile paper/shared/evidence/experiments/09_reviewer_closure_package/build_reviewer_closure_package.py
python - <<'PY'
import json
from pathlib import Path
import yaml

root = Path('.')
for rel in [
    'paper/shared/evidence/raw/reviewer_closure_package/reviewer_closure_statistical_summary.json',
    'paper/shared/evidence/raw/reviewer_closure_package/vlm_coordinate_baseline_summary.json',
    'paper/shared/evidence/raw/reviewer_closure_package/material_safe_conversion_recommender.json',
]:
    json.loads((root / rel).read_text())
for rel in [
    'paper/shared/evidence/results_manifest.yaml',
    'paper/shared/evidence/claims.yaml',
]:
    yaml.safe_load((root / rel).read_text())
PY
git diff --check
make -C paper acl27
```

Results: `19 passed`; structured data parsed successfully; `git diff --check`
returned clean; `make -C paper acl27` produced
`paper/venues/acl27/build/main.pdf`.
