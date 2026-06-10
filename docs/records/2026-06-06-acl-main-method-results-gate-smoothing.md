# 2026-06-06 ACL Main Method/Results Gate Smoothing

## Scope

Continued the ACL main-paper visual and language review on
`paper/venues/acl27/build/main.pdf`, focusing on the page-4 transition from
Method evidence gates into Results.

The full-PDF contact sheet showed no broken figures or float failures, but page
4 still had a visible prose/spacing weakness: the Method Gate 2 paragraph
carried long inline backend identifiers, which created jagged monospaced line
breaks and made the protocol harder to scan.

## Changes

- Replaced the inline full Gemma4 and Qwen checkpoint identifiers in the main
  Method prose with the roles the paper actually needs at that point:
  canonical backend and second-model diagnostic.
- Kept public checkpoint identity in the repository provenance/audit records
  rather than forcing those long identifiers into the main-paper method column.
- Changed Gate 1 wording from "obvious visual structure" to "first-order visual
  structure" for a more ACL-style protocol register.
- Reworded the Results opener so Figure 2 is described as orientation evidence,
  not VLM-equivalence evidence.

## Visual Finding

The accepted render keeps the same page count and local layout:

- Page 3 remains stable; the Method section still starts in the right column.
- Page 4 reads more smoothly in the Gate 2 method block without the long
  monospaced identifier run.
- Results still starts on page 4.
- Figure 2 remains on page 5, with no caption collision or follow-on text
  overlap.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round9_current/contact_sheets/main_pages_01_all_current.png`
- Before page 4:
  `tmp/acl_main_visual_iter_20260606_round9_current/pages_180/main-04.png`
- Accepted page renders:
  - `tmp/acl_main_visual_iter_20260606_round9_after2/pages_180/main-03.png`
  - `tmp/acl_main_visual_iter_20260606_round9_after2/pages_180/main-04.png`
  - `tmp/acl_main_visual_iter_20260606_round9_after2/pages_180/main-05.png`
- Accepted contact sheet:
  `tmp/acl_main_visual_iter_20260606_round9_after2/contact_sheets/main_pages_03_05_after2.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round9_method_results_gate_smoothing_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=18c9199b53b4036b783f0ee848d84bbaf22886648fa7a47acda761fe974e7d6f
pages=11
bytes=5189433
created=Sat Jun 6 09:13:39 2026 CST
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

This pass is a focused p3-p5 readability and local visual iteration. It is not a
complete final-upload audit, broad full-PDF completion proof, or
integrity-fingerprint refresh.
