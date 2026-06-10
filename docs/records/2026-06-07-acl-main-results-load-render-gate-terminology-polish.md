# 2026-06-07 ACL Main Results Load/Render Gate Terminology Polish

## Summary

Round79 reviewed the current ACL main PDF after the Round78 Discussion
terminology polish. Two remaining Results/Table-6 locations still used
`smoke gate(s)`: the page-5 embodied-data Results paragraph and the page-7
Table 6 caption. The rest of the paper now frames this evidence as a
load/render or stack-entry gate, so the residual wording was less formal and
less consistent with the ACL claim-boundary story.

## Changes

- Replaced `run through a smoke gate` in
  `paper/venues/acl27/sections/results.tex` with `pass this load/render gate`.
- Replaced `pass smoke gates` in
  `paper/shared/tables/tab_official_scene_performance_summary.tex` with `pass
  the same load/render gate`.
- Kept the edit local to Results prose and Table 6 caption terminology. No
  table values, evidence pools, figures, citations, metadata, or claim scopes
  were changed.
- Rejected the first Results rewrite because it introduced page-5 line-end
  breaks `match-` and `gener-`.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round79_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round79_after/`
- Rendered after screenshots:
  `tmp/acl_main_visual_iter_20260607_round79_after/page-05.png` and
  `tmp/acl_main_visual_iter_20260607_round79_after/page-07.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round79_results_load_render_gate_terminology_polish_20260607.json`
- Final PDF hash:
  `fec589080615dbd9bfa322f17af85ffa416f704b09d9df5781126eff3665afc0`

The accepted after scan shows no page-5 or page-7 body/caption line-end
hyphenation. The full after scan reports only normal bibliography-column
hyphenation on pages 9-10, and `smoke gate` no longer appears in ACL main
Results/table text.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Results prose and Table 6 caption terminology. It did
not change metric values, evidence pools, figures, citations, metadata, or
supported/forbidden claim scopes.
