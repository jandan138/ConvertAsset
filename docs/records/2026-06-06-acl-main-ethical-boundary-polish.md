# 2026-06-06 ACL Main Ethical Boundary Polish

## Scope

Round 41 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The accepted target was page 10,
`Ethical Considerations`, where the current render split `intended ren-` /
`der use`, `object af-` / `fordances`, and `synthetic-scene suc-` / `cess`
inside the same risk-reporting paragraph.

## Change

- Replaced `intended render use` with `intended use` to remove a distracting
  line-end split without changing the reporting obligation.
- Replaced the long `vision-language models` / `material-change failures`
  phrase with `VLMs` and `failures that alter task cues`, keeping the same
  ethical caution while avoiding the old `object af-` split.
- Replaced `synthetic-scene success as real-world transfer` with `success in
  synthetic scenes as transfer to real settings`.
- Added `They mark the evidence boundary` so the paragraph keeps the References
  heading at the top of the right column and states the disclosure rule as an
  evidence-boundary requirement.

Rejected intermediate routes: shorter variants removed the target splits but
either moved the `References` heading to the bottom of the left column or
introduced new `con-` / `real-`, `ac-`, `dis-`, `ev-`, and `ma-` line-end
splits. Those variants were rebuilt and rejected before the accepted wording.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round41_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round41_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round41_after/focus_before_after_p10.png`
- Pages 9-10 focus sheet: `tmp/acl_main_visual_iter_20260606_round41_after/focus_p9_p10.png`

Observed result: the accepted page 10 paragraph removes the targeted
`intended ren-`, `object af-`, and `synthetic-scene suc-` splits. The
`References` section still starts at the top of the right column, Figure 4
stays above the ethics block, page 9 retains its Discussion / Limitations /
Conclusion structure, and the PDF remains 11 pages.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, label warnings, undefined references,
  multiply defined labels, rerun-to-cross-reference warnings, and lineno
  warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 15.19s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.

Final PDF identity:

- SHA256: `96497cb37b19807d5bf88727679a0611239246523074b9aea992f685ce7e9ca1`
- Pages: 11
- Size: 5,188,355 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round41_ethical_boundary_polish_20260606.json`
