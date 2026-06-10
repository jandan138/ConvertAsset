# 2026-06-03 ACL Supplement Theory Hypothesis Boundary Companion

## Scope

Improved the previously text-only theory hypothesis page in the ACL supplement
by adding `fig_supplement_theory_hypothesis_boundary_companion.png` inside the
two-column hypothesis section.

The companion keeps the theory page visually tied to existing evidence:

- material salience: covered cue, clearcoat limit, and procedural-texture limit
- coordinate contract: clean GRScenes target-view render rows with target boxes
- embodied stack: selected InternNav rollout and route media
- hypothesis boundary: an imagegen-created schematic slot that explains the
  interpretation boundary

## Claim Boundary

The `hypothesis_boundary` slot is AI-generated and exposition only. It is not a
render result, model output, experiment, causal proof, population rate, or
benchmark row.

The evidence-bearing content remains the registered material, VLM target-view,
and navigation render rows. The AI slot is replaceable and only helps the reader
understand how the supplement separates evidence from hypothesis-level
interpretation.

## Layout Outcome

The new companion is a column-width figure placed on page 41. It improves the
former pure-text hypothesis page without adding pages or breaking the following
reproducibility/media-manifest page.

Measured rendered-page active fractions:

- page 41: `0.141167`, from prior sparse reference `0.079269`
- page 39: `0.216856`
- page 40: `0.273115`
- page 42: `0.256477`
- page 43: `0.102503`

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_hypothesis_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/06_theory.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k "hypothesis_boundary_companion"`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- Rendered PDF pages 39-43 with `pdftoppm`.
- PDF text positive scan for the hypothesis companion and AI-exposition boundary.
- PDF text negative scan for stale red-material diagnostic wording, local paths,
  and author-profile leakage.

Visual review was local rather than an independent subagent review; the evidence
JSON records `independent_subagent: false`.
