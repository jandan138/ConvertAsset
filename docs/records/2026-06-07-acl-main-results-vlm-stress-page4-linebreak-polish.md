# 2026-06-07 ACL Main Results VLM Stress Page4 Linebreak Polish

## Scope

Round 63 of the ACL main-paper visual/prose review polished the page-4 Results
right column around the VLM stress result and material-boundary transition. The
source change is in:

- `paper/venues/acl27/sections/results.tex`

## Issue

The rendered page-4 right column contained a visible linebreak cluster in the
main result:

- `target- / category`
- `co- / ordinate`
- `ren- / ders`
- `agree- / ment`
- `con- / tract`
- `mea- / surement`
- `can- / not`
- `diag- / nostic`
- `mechanis- / tic`
- `Asset Con- / verter`

During iteration, shorter wording briefly introduced replacement splits such as
`differ- / ent`, `con- / ditions`, `au- / dited`, `fig- / ures`,
`prove- / nance`, `im- / age`, `nor- / malized`, `sur- / face`,
`Fig- / ure`, and `read- / ers`. The accepted version removes the target cluster
without changing the reported numbers or evidence boundary.

## Change

The VLM stress result now reads as a compact ACL result paragraph: Gemma4 keeps
all 30 target labels, scores 27/30 original and 29/30 converted point hits, and
keeps the same hit status for 28 pairs. Qwen2.5-VL is framed as a different
coordinate preference, with raw-pixel hits reported separately from the
normalized-1000 contract.

The interpretation sentence now states the boundary directly: the signal is not
a model ranking, and a close render alone is not enough for the VLM claim.

The bootstrap and qualitative-panel sentences were shortened so that the
contract, frozen tables, and overlay status remain separate evidence sources.

The material-boundary transition now uses the NVIDIA baseline wording and keeps
the comparison limited to bins with bounded provenance.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round63_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round63_after`
- Before PDF SHA-256:
  `b8b950c3b9a87357f6adc0a2d34d1282159793d1657112ea2f11dfb6207776c6`
- After PDF SHA-256:
  `524882046d1793d398c31a197c03122f5f85e0ca772798ca2397b7135b41f759`
- After page-4 right-column crop:
  `tmp/acl_main_visual_iter_20260607_round63_after/page4_right.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round63_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round63_results_vlm_stress_page4_linebreak_polish_20260607.json`

The final page-4 crop removes the targeted VLM stress split cluster and keeps
the Material Effects subsection heading on the same page. The full contact
sheet remains 11 pages with no obvious float, table, or blank-page regression.

## Verification

- `make -C paper acl27` exited 0.
- Log blocker scan for overfull boxes, undefined references, rerun warnings,
  multiply-defined labels, and `lineno` warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `"ok": true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `"ok": true` with a 168-word abstract.
