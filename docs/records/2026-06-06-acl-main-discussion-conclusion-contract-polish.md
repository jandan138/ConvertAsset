# 2026-06-06 ACL Main Discussion/Conclusion Contract Polish

## Scope

Continued the ACL main-paper visual and language review on
`paper/venues/acl27/build/main.pdf`, focusing on the page-9 close across
Discussion, Conclusion, and Limitations.

The current PDF had no black images, crop failures, overfull warnings, or
missing-reference warnings. The higher-impact issue was rhetorical: the close
was technically bounded but still read more like a defensive disclaimer than an
ACL-style reusable contribution.

## Changes

- Reframed the Discussion lead so noMDL conversion is a visible intervention,
  not a converter-quality claim.
- Tightened the material-effect discussion around auditable claims: portable
  scene workflows may carry evidence only when the relevant gate is checked.
- Rewrote the Conclusion around a reusable evidence contract: matched renders,
  projection QA, prompt/coordinate contracts, material-risk bins, and embodied
  smoke gates.
- Preserved the existing claim boundary: no converter ranking, no speedup
  claim, no broad robustness claim, and no broad benchmark-distribution claim.

## Visual Finding

The first rewrite was too long and spilled the Conclusion into the top of the
Limitations column. It was shortened and rebuilt. The accepted render restores
the intended page-9 rhythm:

- Left column: Discussion plus the complete Conclusion.
- Right column: Limitations starts cleanly at the top.
- Page 10: Figure 4, Ethical Considerations, and References remain readable and
  non-overlapping.

## Visual Evidence

- Before late-page contact sheet:
  `tmp/acl_main_visual_iter_20260606_round8/contact_sheets/main_pages_07_11.png`
- Rejected spill render:
  `tmp/acl_main_visual_iter_20260606_round8_after/pages_180/main-09.png`
- Accepted page renders:
  - `tmp/acl_main_visual_iter_20260606_round8_after2/pages_180/main-09.png`
  - `tmp/acl_main_visual_iter_20260606_round8_after2/pages_180/main-10.png`
- Accepted contact sheet:
  `tmp/acl_main_visual_iter_20260606_round8_after2/contact_sheets/main_pages_08_10_after2.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round8_discussion_conclusion_contract_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=44be014aab9b2530eca69eb2da4bb77737ef408cb045a7443eaf4a8f5ae74344
pages=11
bytes=5193049
created=Sat Jun 6 09:03:32 2026 CST
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
ACL claim-boundary and metadata-consistency checks passed.

## Residual Risk

This pass is a focused main-paper prose and p9-p10 visual iteration. It is not a
final upload gate, broad visual audit, or integrity-fingerprint refresh.
