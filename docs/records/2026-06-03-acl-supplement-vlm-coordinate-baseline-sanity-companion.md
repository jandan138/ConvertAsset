# 2026-06-03 ACL Supplement VLM Coordinate Baseline Sanity Companion

## Scope

Improved the previously sparse coordinate-baseline page in the ACL supplement
by adding `fig_supplement_vlm_coordinate_baseline_sanity_companion.png` after
Table S3.

The companion uses real GRScenes target-view renders to make the deterministic
baseline rows visually inspectable:

- image-center pixel: raw center can be easy under target-centered cameras
- bbox-center pixel: oracle target center checks box geometry and scoring
- bbox-center normalized-1000: normalized center checks the prompt coordinate
  contract

It also includes an imagegen-created `baseline_gate` schematic slot.

## Claim Boundary

The AI-generated `baseline_gate` slot is exposition only. It is not a VLM
prediction, metric, benchmark row, or new experiment.

The evidence-bearing content remains Table S3 plus the registered GRScenes
target-view renders with deterministic overlay marks.

## Layout Outcome

The first standalone version had bottom labels too close to card edges. The
final version moves the right-side bullet list and bottom labels so the panel is
contained at paper scale.

Measured rendered-page active fractions:

- page 18: `0.116327`, from prior sparse reference `0.0469`
- page 17: `0.088220`
- page 19: `0.149193`
- page 20: `0.222769`

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_vlm_coordinate_baseline_sanity_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_baseline_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_baseline_sanity_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/02_vlm_protocol.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_baseline_sanity_companion_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k "coordinate_baseline_sanity_companion"`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- Rendered PDF pages 17-20 with `pdftoppm`.
- PDF text positive scan for the coordinate-baseline companion and AI-exposition boundary.
- PDF text negative scan for stale red-material diagnostic wording, absolute local paths, and author-profile leakage.

Visual review was local rather than an independent subagent review; the evidence
JSON records `independent_subagent: false`.
