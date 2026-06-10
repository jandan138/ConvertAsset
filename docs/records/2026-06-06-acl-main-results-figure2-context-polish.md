# 2026-06-06 ACL Main Results Figure 2 Context Polish

## Scope

Round 45 continued the ACL main-paper visual review on
`paper/venues/acl27/build/main.pdf`. The target was the page 4 Results handoff
from proxy similarity to Figure 2, where extracted text showed:

- `the downstream-reliability claim. Figure 2 an-`
- `chors the gate visually; the panels are orienta-`
- `tion evidence, not VLM-equivalence evidence.`

## Change

Updated `paper/venues/acl27/sections/results.tex` to keep the same evidentiary
boundary while removing the visible split:

```tex
Figure~\ref{fig:render_scene_evidence_acl} gives visual context; metric and
task claims stay in the frozen tables.
```

The edit does not change any metric, table, evidence source, or claim scope. It
turns Figure 2 into reader orientation and keeps metric/task claims tied to the
frozen tables.

## Visual Review

Artifacts:

- Before render directory:
  `tmp/acl_main_visual_iter_20260606_round45_current`
- After render directory:
  `tmp/acl_main_visual_iter_20260606_round45_after`
- Before/after page 4 comparison:
  `tmp/acl_main_visual_iter_20260606_round45_after/focus_before_after_p4.png`
- Page 4/5 after spread:
  `tmp/acl_main_visual_iter_20260606_round45_after/focus_p4_p5.png`

After extraction, page 4 reads:

- `as the downstream-reliability claim. Figure 2`
- `gives visual context; metric and task claims`
- `stay in the frozen tables.`

The PDF remained 11 pages. Figure 2 stayed on page 5, and the page 4/5 spread
kept the same float structure.

## Verification

Commands run from the repository root:

- `make -C paper acl27` - exit 0
- `rg` blocker scan over `paper/venues/acl27/build/main.log` - `no blocker matches`
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py` -
  `102 passed in 15.66s`
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` - `ok: true`
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` - `ok: true`,
  abstract word count 169

## Evidence

Evidence manifest:
`paper/shared/evidence/raw/acl27_visual_review/main_round45_results_figure2_context_polish_20260606.json`

Final PDF:

- Path: `paper/venues/acl27/build/main.pdf`
- SHA256:
  `27ac5e0c3714de620638348893d4ad30e174564c918f3182fdbd6939ae82c9b3`
- Pages: 11
- Size: 5,188,362 bytes
