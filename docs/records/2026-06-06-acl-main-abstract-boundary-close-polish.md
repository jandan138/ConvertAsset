# 2026-06-06 ACL Main Abstract Boundary Close Polish

## Scope

Round 48 of the ACL main-paper visual/prose review polished the page-1
abstract close and one adjacent page-1 introduction phrase. The source changes
are in `paper/venues/acl27/sections/abstract.tex`,
`paper/venues/acl27/sections/intro.tex`,
`paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md`, and
`tests/test_acl_metadata_consistency.py`.

## Issue

The page-1 abstract still had two reader-visible `downstream` splits:

- `proxy fidelity does not certify down- / stream grounding`
- `converted synthetic scenes support down- / stream robustness claims`

After the abstract rewrite removed those splits, the same page exposed an
adjacent introduction split:

- `where down- / stream experiments may combine`

These were not correctness bugs, but they weakened the first-page story at the
exact place where the paper frames its claim boundary.

## Change

The abstract now says that proxy fidelity does not certify `grounding behavior`
and closes with:

`Together, these gates keep visual similarity, grounding, material effects, and stack usability from merging into one task claim.`

The adjacent introduction phrase now uses `evaluation runs may combine` instead
of `downstream experiments may combine`. The OpenReview metadata packet mirrors
the refreshed 168-word abstract, and the metadata consistency unit test now
checks the new boundary wording.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260606_round48_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260606_round48_after`
- Before PDF SHA-256:
  `2220f78d266b1c2c9a406c56c3ee33dc5dcccc03e6b0c7980286b1b6f6d020d3`
- After PDF SHA-256:
  `c63a33f973d20a3e5fb60b0a114e8c7dfb875e36e4ee4d4e82c489b2ab257766`
- After page-1 comparison:
  `tmp/acl_main_visual_iter_20260606_round48_after/focus_before_after_p1.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round48_abstract_boundary_close_polish_20260606.json`

The final page-1 render removes the targeted `downstream` splits, keeps the
abstract under 200 words, and preserves the 11-page layout.

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
