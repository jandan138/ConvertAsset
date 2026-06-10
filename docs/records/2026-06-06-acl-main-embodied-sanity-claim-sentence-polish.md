# 2026-06-06 ACL Main Embodied Sanity Claim Sentence Polish

## Scope

Round 35 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 6 Results Section
4.4 claim-boundary paragraph immediately before Table 6 and Figure 3.

## Change

- Replaced the comma-spliced conclusion sentence with a shorter scoped claim:
  the selected official stack can load, render, and evaluate converted scenes
  end-to-end.
- Recast the boundary as `a sanity result, not a broad navigation claim`.
- Replaced the rollout-evidence sentence with a shorter qualitative-check
  sentence tied to the 99-episode paired run.

The edit preserves the embodied-data claim boundary: the InternNav evidence is
an official-stack sanity check, not a broad navigation or robustness result.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round35_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round35_after/contact_sheet.png`
- After focus sheet: `tmp/acl_main_visual_iter_20260606_round35_after/focus_p6_after.png`
- Pages 6-7 focus sheet: `tmp/acl_main_visual_iter_20260606_round35_after/focus_p6_p7_after.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round35_after/focus_before_after_p6.png`

Observed result: the page 6 paragraph no longer renders the old `conclu-` /
`sion` split or the `substi-` / `tute` split. Intermediate phrasings that
introduced `sup-` / `ported`, `con-` / `text`, or `robust-` / `ness` splits
were rejected before this final wording. The page 6 Figure 3 placement and the
page 7 evidence-gate companion spread remain visually stable.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 13.97s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- Page-6 text extraction confirms the old split in the current render and the
  final `sanity result, not a broad navigation claim` wording in the after
  render.

Final PDF identity:

- SHA256: `54acf980380eb24eb818e61c72988e7d15d973153447005191d462bc346efb9e`
- Pages: 11
- Size: 5,188,647 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round35_embodied_sanity_claim_sentence_polish_20260606.json`
