# 2026-06-06 ACL Main Contribution Claim Gate Polish

## Scope

Round 44 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The accepted target was page 2, contribution
4 in the Introduction. The current render split `selected NVIDIA-` /
`baseline` and `99-episode offi-` / `cial` inside the contribution list, a
high-visibility location just before `Related Work`.

## Change

- Recast contribution 4 as a claim-gate sentence:
  `We anchor material-effect and embodied-stack sanity checks in the same claim
  gate`.
- Replaced `selected NVIDIA-baseline material audit` with `a selected material
  audit against the NVIDIA baseline`.
- Replaced `a 99-episode official KuJiaLe InternNav run` in the contribution
  item with `a 99-episode VLN run on official KuJiaLe scenes`. The preceding
  introduction paragraph already names the official KuJiaLe InternNav run.
- Kept the bounded-claim close: these checks support bounded reliability
  claims, not broad embodied-benchmark or speedup claims.

Rejected intermediate routes:

- `same claim registry: ... a 99-episode InternNav run ...` removed the original
  target splits but introduced `claim reg-` / `istry` and `In-` / `ternNav`.
- `99-episode official navigation run` removed those splits but introduced
  `nav-` / `igation`.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round44_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round44_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round44_after/focus_before_after_p2.png`
- Pages 1-2 focus sheet: `tmp/acl_main_visual_iter_20260606_round44_after/focus_p1_p2.png`
- Pages 2-3 focus sheet: `tmp/acl_main_visual_iter_20260606_round44_after/focus_p2_p3.png`

Observed result: page 2 no longer renders `selected NVIDIA-` / `baseline` or
`99-episode offi-` / `cial` in contribution 4. The final contribution text
renders as `the NVIDIA baseline, a 99-episode VLN run` / `on official KuJiaLe
scenes, and repeated`, with `Related Work` still starting at line 127 in the
right column. Page 1 and page 3 text extraction hashes are unchanged, and the
PDF remains 11 pages.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, label warnings, undefined references,
  multiply defined labels, rerun-to-cross-reference warnings, and lineno
  warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 16.07s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.

Final PDF identity:

- SHA256: `646dd6d838c9f75186a3d456876c7b0ca9d06a987ac8cf4d5805d09a1edbae2b`
- Pages: 11
- Size: 5,188,392 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round44_contribution_claim_gate_polish_20260606.json`
