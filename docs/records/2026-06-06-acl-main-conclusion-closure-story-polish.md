# 2026-06-06 ACL Main Conclusion Closure Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on the page-9 Conclusion closure.

The fresh round-17 contact sheet showed no hard crop or float displacement. The
selected issue was local but high-value: Discussion, Limitations, and Conclusion
share the closing page, and the conclusion still ended like a compact checklist
rather than a reader-facing ACL takeaway.

## Changes

- Rewrote the first conclusion paragraph to say why material conversion matters
  for grounding evidence.
- Reframed the closing list as an auditable intervention: matched renders,
  projection QA, prompt/coordinate contracts, material-risk bins, and embodied
  smoke gates.
- Preserved the key claim boundary that portable assets are useful only for the
  gates they pass.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 9 uses existing vertical slack and keeps Conclusion entirely on the same
  closing page.
- The pre-edit checklist-style contribution sentence is replaced by a clearer
  two-paragraph closure.
- Page 10 Ethical Considerations and References remain visually stable on the
  after contact sheet.
- No figure, table, Discussion, Limitation, or reference displacement is visible
  in the accepted full contact sheet.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round17_current/contact_sheets/main_pages_01_11_current.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round17_current/pages_180/main-09.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round17_after/pages_180/main-09.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round17_after/contact_sheets/main_pages_01_11_after.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round17_conclusion_closure_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=67b0f4a73b362821adfdcd0630bd1005e0d11d1ad1ba70b63ea605f8c07d3d6a
pages=11
bytes=5189604
created=Sat Jun 6 10:31:42 2026 CST
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

This pass is a focused Conclusion closure and page-9 visual iteration. It is not
a complete final-upload audit, target-policy refresh, or integrity-fingerprint
refresh.
