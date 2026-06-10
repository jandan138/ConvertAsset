# 2026-06-06 ACL Main Ethics Disclosure Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on the page-10 Ethical
Considerations block and its disclosure boundary.

The fresh round-16 contact sheet showed stable figures and tables with no new
hard crop. The selected issue was local but reviewer-facing: Ethical
Considerations sat beside the start of References and still read partly like a
checklist rather than a polished ACL disclosure.

## Changes

- Reframed the ethical risks as indirect synthetic-scene risks: bias, license
  restrictions, unsafe deployment assumptions, and inflated robustness claims.
- Recast reuse guidance as a general submission responsibility for asset
  provenance, license compatibility, filtering criteria, and intended render
  use.
- Added concise author-responsibility language for AI-assisted implementation,
  editing, audit drafting, and schematic generation.
- Preserved the boundary that the generated schematic is illustrative only and
  that quantitative results and empirical visual panels were checked against
  repository artifacts and cited sources.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 10 still contains Ethical Considerations in the left column and
  References in the right column.
- The final disclosure paragraph avoids the loose full-justified line introduced
  by the first intermediate rewrite.
- References start cleanly, and no downstream reference-page displacement is
  visible on the after contact sheet.
- Figures, tables, Discussion, Conclusion, and Limitations remain visually
  stable across the full contact sheet.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round16_current/contact_sheets/main_pages_01_11_current.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round16_current/pages_180/main-10.png`
- Intermediate page render:
  `tmp/acl_main_visual_iter_20260606_round16_after/pages_180/main-10.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round16_after_final/pages_180/main-10.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round16_after_final/contact_sheets/main_pages_01_11_after_final.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round16_ethics_disclosure_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=75f0bf954fc1357118c91f2c3c56455f484a3b05c95d1f87b3e50f6db1db0296
pages=11
bytes=5189504
created=Sat Jun 6 10:23:56 2026 CST
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
ACL claim-boundary and metadata-consistency checks returned `ok`. The metadata
check still reports `abstract_word_count=169`.

## Residual Risk

This pass is a focused Ethical Considerations and disclosure story polish. It is
not a complete final-upload audit, target-policy refresh, or
integrity-fingerprint refresh.
