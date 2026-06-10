# 2026-06-06 ACL Main Conclusion Punchline Polish

## Scope

Continued the ACL main-paper visual and language review on
`paper/venues/acl27/build/main.pdf`, focusing on the page-9 close where
Discussion, Limitations, and Conclusion share the final text page before
Ethical Considerations and References.

The rendered Conclusion was complete and did not spill, but its first sentence
opened with a weak visual break: `synthetic-scene mate-` followed by
`rial conversion`. That made the final claim boundary read less like an ACL
closing punchline.

## Changes

- Replaced the Conclusion opener with a shorter claim-boundary sentence:
  "USD material conversion is not neutral."
- Recast the negative boundary as "not a ranking, speedup claim, or broad
  robustness result," preserving the no-ranking/no-speedup/no-broad-robustness
  claim boundary.
- Shortened "reusable evidence contract" to "reusable contract" because the
  following clause still names the evidence gates and avoids a disruptive
  `con-`/`tract` split in the rendered close.

## Visual Finding

The accepted render keeps the same page count and late-page structure:

- Page 9 left column still contains Discussion plus the complete Conclusion.
- Page 9 right column still contains Limitations without overlap.
- The Conclusion opener no longer starts with a split `material` word.
- Page 10 remains stable: Figure 4, Ethical Considerations, and References are
  unchanged in local structure and do not overlap.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round12_current/contact_sheets/main_pages_01_11_current.png`
- Before page renders:
  - `tmp/acl_main_visual_iter_20260606_round12_current/pages_180/main-09.png`
  - `tmp/acl_main_visual_iter_20260606_round12_current/pages_180/main-10.png`
- Accepted page renders:
  - `tmp/acl_main_visual_iter_20260606_round12_after5/pages_180/main-09.png`
  - `tmp/acl_main_visual_iter_20260606_round12_after5/pages_180/main-10.png`
- Accepted contact sheet:
  `tmp/acl_main_visual_iter_20260606_round12_after5/contact_sheets/main_pages_09_10_after5.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round12_conclusion_punchline_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=740a7677a2321c5ca3d5a92ea94611cbaeda946bf82fc6dadf5524b848322c8f
pages=11
bytes=5189207
created=Sat Jun 6 09:41:36 2026 CST
```

## Verification

```bash
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
```

Results: ACL build passed with an 11-page A4 PDF, the final LaTeX blocker scan
returned no matches, `tests/test_paper_layout.py` passed with 85 tests, and both
ACL claim-boundary and metadata-consistency checks returned `ok`.

## Residual Risk

This pass is a focused p9 Conclusion punchline iteration. It is not a complete
final-upload audit, broad full-PDF completion proof, or integrity-fingerprint
refresh.
