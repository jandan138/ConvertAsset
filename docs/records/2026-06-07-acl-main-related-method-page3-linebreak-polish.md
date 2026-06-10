# 2026-06-07 ACL Main Related Method Page3 Linebreak Polish

## Scope

Round 61 of the ACL main-paper visual/prose review polished the page-3
Related Work to Method transition. The source changes are in:

- `paper/venues/acl27/sections/related.tex`
- `paper/venues/acl27/sections/method.tex`

## Issue

The rendered page-3 left column still had a reader-visible cluster around the
end of Related Work and the Method opener:

- `orig- / inal`
- `Inte- / riorNav`
- `Synthetic- / data`
- `Syn- / thetica`
- `representa- / tion`
- `inter- / vention`
- `ma- / terial`
- `usabil- / ity`

During iteration, shorter wording briefly introduced replacement splits such as
`Do- / main`, `ge- / ometry`, `Sys- / tems`, `UsdPreview- / Surface`,
`al- / lows`, and `compa- / rable`. The accepted version keeps the same
citations and evidence boundaries with shorter prose.

## Change

The embodied-simulation related-work paragraph now avoids the stale
`InteriorNav` wording and states the boundary as a scoped KuJiaLe sanity check,
not a broad navigation claim.

The synthetic-rendering paragraph now frames rendering as a task factor,
keeps the sim-to-real and synthetic-data citations, and presents the paper's
shift as an MDL-to-USD-PreviewSurface rewrite with scene content and task labels
fixed where the protocol allows.

The Method opener now reads as a gate bridge: conversion is the test step, each
evidence layer gets its own claim, and the method then asks task-proximal
questions about proxy match, VLM grounding, material mechanisms, and stack use.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round61_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round61_after`
- Before PDF SHA-256:
  `e33bd93d9dbed3c60a156eb2931cc24d048e0da7d1e05ed2a07198bbf38a7e82`
- After PDF SHA-256:
  `d7219ef76e9da3bd6956592b5d54f73798001ea44152ed870060a531f764a5d2`
- After page-3 left-column crop:
  `tmp/acl_main_visual_iter_20260607_round61_after/page3_left.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round61_related_method_page3_linebreak_polish_20260607.json`

The final page-3 crop removes the targeted Related Work split cluster and keeps
the Method opener readable. The full contact sheet remains 11 pages with no
obvious float, table, or blank-page regression.

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
