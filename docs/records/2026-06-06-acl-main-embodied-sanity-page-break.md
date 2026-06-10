# 2026-06-06 ACL Main Embodied Sanity Page Break

## Scope

Continued the ACL main-paper visual and language review on
`paper/venues/acl27/build/main.pdf`, focusing on the page-5/page-6 transition
where Results moves from the material-effect boundary into embodied-data sanity.

The rendered PDF had a small but reader-visible page-break weakness: page 5
ended the Embodied-Data Sanity opener with `Combined orig-`, and page 6 resumed
with `inal/noMDL`. This split a key condition label across pages immediately
before Figure 3.

## Changes

- Shortened the embodied-data opener from "For downstream embodied-data sanity"
  to "For embodied-data sanity".
- Changed "three local official scenes" to "three local scenes" because the
  section header and route name already establish the official-scene context.
- Replaced "Combined original/noMDL means are" with "Means are" so the page
  break no longer splits `original/noMDL`.
- Preserved all reported values: SR 0.5253/0.4848, SPL 0.4739/0.4298, NE
  3.6798/3.6306, and TL 6.9754/7.0598.

## Visual Finding

The accepted render keeps the same page count and local float structure:

- Page 5 no longer ends with a cross-page word split.
- Page 5 now carries the route coverage sentence and starts the means sentence
  through the SR value.
- Page 6 begins with the next metric, SPL, without the stretched first-line
  spacing introduced by an intermediate rejected paragraph-break variant.
- Figure 3 remains stable at the bottom of page 6 with no crop, caption
  collision, or overlap.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round11_current/contact_sheets/main_pages_01_11_current.png`
- Before page renders:
  - `tmp/acl_main_visual_iter_20260606_round11_current/pages_180/main-05.png`
  - `tmp/acl_main_visual_iter_20260606_round11_current/pages_180/main-06.png`
- Accepted page renders:
  - `tmp/acl_main_visual_iter_20260606_round11_after4/pages_180/main-05.png`
  - `tmp/acl_main_visual_iter_20260606_round11_after4/pages_180/main-06.png`
- Accepted contact sheet:
  `tmp/acl_main_visual_iter_20260606_round11_after4/contact_sheets/main_pages_05_06_after4.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round11_embodied_sanity_page_break_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=13afc6f46049898600e24a50375021b9f8158ded223be32a57f47652445a7847
pages=11
bytes=5189290
created=Sat Jun 6 09:33:08 2026 CST
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

This pass is a focused p5/p6 Results page-break iteration. It is not a complete
final-upload audit, broad full-PDF completion proof, or integrity-fingerprint
refresh.
