# 2026-06-06 ACL Main Embodied Sanity Gate Story Polish

## Scope

Round 27 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 6 Section 4.4
handoff from material-effect evidence into official-scene embodied-stack sanity.

## Change

- Reframed the final gate as a sanity gate, not a benchmark result.
- Made the supported conclusion more explicit: the selected official stack can
  load, render, and evaluate converted scenes end-to-end, but current evidence
  does not show broad embodied-navigation robustness.
- Kept the infrastructure paragraph inside the established guardrails:
  `18 required paired runs` remains present for the layout guard, and the NVIDIA
  official-scene sentence uses `do not report` so the claim-boundary checker
  recognizes it as scoped.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round27_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round27_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round27_after/focus_before_after_p6_p7.png`

Observed result: page 6 keeps the same broad section/table/Figure 3 flow, the
previous `benchmark up-grade` visual break is gone, and page 7 remains stable.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 14.05s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- PDF text extraction confirmed the new sanity-gate wording and the guardrailed
  NVIDIA official-scene performance omission.

During verification, an intermediate wording draft broke two guardrails: it
removed the exact `18 required paired runs` phrase and changed `do not report`
to `omit`. Both were restored before final verification.

Final PDF identity:

- SHA256: `4564f0eb59b4301e3fb6d0423e529544566179d842fe3b1dabd76d4df175a7f1`
- Pages: 11
- Size: 5,188,947 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round27_embodied_sanity_gate_story_polish_20260606.json`
