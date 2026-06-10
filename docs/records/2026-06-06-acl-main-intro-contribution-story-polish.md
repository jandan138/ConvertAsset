# 2026-06-06 ACL Main Intro Contribution Story Polish

## Scope

Round 26 continued the ACL main-paper visual polish loop on `paper/venues/acl27/build/main.pdf`.
The localized target was the page 2 Introduction contribution list immediately before
the Related Work handoff.

## Change

- Reframed the lead sentence so the contribution list turns a hidden preprocessing
  step into an auditable grounding measurement protocol.
- Rewrote the four contribution bullets as a contribution contract:
  define the perturbation, specify the claim-bounded protocol, instantiate it on
  GRScenes, and connect material-effect plus embodied-stack sanity checks to the
  same claim registry.
- Preserved the evidence boundary: the text still supports bounded reliability
  claims, not broad embodied-benchmark or speedup claims.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round26_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round26_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round26_after/focus_before_after_p2_p3.png`

Observed result: page 2 keeps the same broad figure/caption/protocol/contribution/Related
Work flow, page 3 remains stable, and the final contribution item 2 avoids the
visibly stretched justified line seen during the first draft of this round.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 13.96s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- PDF text extraction confirmed the new contribution wording.

Final PDF identity:

- SHA256: `542c9fd36dd054f453282cd18d86e755ba98f4c0ea61b0f257ad08793be1e749`
- Pages: 11
- Size: 5,189,026 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round26_intro_contribution_story_polish_20260606.json`
