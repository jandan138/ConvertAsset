# 2026-06-07 ACL Main Discussion Page8 Contract Evidence Prose Polish

## Summary

Round83 reviewed the current ACL main PDF after the Round82 Ethical
Considerations boundary polish. The page-8 Discussion paragraph still described
the GRScenes stress result as `the clearest warning` and said
`Qwen2.5-VL is stronger in raw pixels`. Both statements were bounded by the
surrounding text, but the wording was more editorial and ranking-like than the
paper's contract-evidence story.

## Changes

- Rewrote the Discussion sentence in
  `paper/venues/acl27/sections/discussion.tex` to say the stress result `shows
  why proxy similarity is not enough`.
- Replaced `a different scoring contract` with `a contract mismatch` to keep
  the rendered line compact.
- Replaced `Qwen2.5-VL is stronger in raw pixels` with
  `Qwen2.5-VL shows a raw-pixel preference`, preserving the model-behavior
  boundary without a ranking tone.
- Kept the edit local to Discussion prose. No metrics, evidence pools, figures,
  tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The first rewrite removed `clearest warning` but introduced a visible page-8
  model-name split: `Qwen2.5-` / `VL`.
- The second rewrite protected the model name and neutralized `stronger in raw
  pixels`, but introduced visible page-8 linebreak hyphenation:
  `dif-` / `ferent`.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round83_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round83_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round83_after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round83_discussion_page8_contract_evidence_prose_polish_20260607.json`
- Final PDF hash:
  `a0fc5f85e0fbe300f3102837d9ed168ea2862bfd462229a9dd2159ea91a0f001`

The accepted after scan shows the revised page-8 Discussion text without
body-text linebreak hyphenation. The PDF remains 10 pages. The strict
hyphenation scan reports only the existing explicit `human-subject` wording and
normal reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.23s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Discussion prose on page 8. It did not change metrics,
evidence pools, figures, tables, citations, metadata, or supported/forbidden
claim scopes.
