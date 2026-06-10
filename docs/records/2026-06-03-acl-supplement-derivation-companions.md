# 2026-06-03 ACL Supplement Derivation Companions

## Scope

Added two supplement companion figures for the math-heavy derivation pages:

- `fig_supplement_grounding_derivation_companion.png`
- `fig_supplement_navigation_derivation_companion.png`

Both figures use deterministic composition over registered paper evidence. The only AI-generated image is the reusable `metric_contract_gate` slot, stored at `paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_ai_slot.png`.

## Claim Boundary

The imagegen slot is allowed in the paper as exposition only. It summarizes metric-contract structure and does not serve as experimental evidence, a model prediction, a benchmark row, or a baseline result.

Evidence-bearing panels remain the registered original/noMDL render pairs, metric charts, route strips, rollout stills, and selected navigation cases.

## Layout Outcome

The first build exposed a caption-only page after the navigation companion. The final layout keeps the navigation figure readable at full width and replaces the hard post-figure page break with a soft separation, so the caption is followed by the metric-boundary summary and bridge figure.

Measured rendered-page active fractions:

- page 13: `0.101992` after adding the grounding companion, from prior sparse-page reference `0.0338`
- page 14: `0.087321` after adding the navigation companion, from prior sparse-page reference `0.0375`
- page 15: `0.149727` after removing the caption-only page pattern

## Files

- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grounding_derivation_companion.png`
- `paper/shared/figures/fig_supplement_navigation_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grounding_derivation_companion.yaml`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_derivation_companions_20260603.json`

## Verification

- `make -C paper acl27-supplement`
- `python -m pytest -q tests/test_paper_layout.py -k "derivations_have_render_companions or derivation_companions"`
- `python -m pytest -q tests/test_paper_layout.py`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_derivation_companions_20260603.json`
- PDF text positive scan for the two new captions and AI-exposition boundary.
- PDF text negative scan for stale red-material diagnostic wording, absolute local paths, and author-profile leakage.

Visual review was local rather than an independent subagent review; the evidence JSON records `independent_subagent: false`.
