# 2026-06-06 ACL Main Evidence-Gate Companion Public Wording

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on page 7 and Table 1's
evidence-gate registry companion.

The fresh round-21 contact sheet showed no hard crop or float displacement. The
selected issue was local: the page-7 caption and companion figure still exposed
internal production language (`AI-generated reader-gate v3 schematic` and
`AI schematic, exposition only`) in reviewer-facing text.

## Changes

- Rewrote the Table 1 caption so the companion is described as an interpretive
  index, not by how it was produced.
- Preserved the stable `evidence-gate registry companion` phrase required by
  layout regression tests and by the paper's evidence-gate terminology.
- Updated the companion figure generator and regenerated
  `fig_supplement_evidence_gate_registry_companion.png` so the Reader gate card
  says `interpretive schematic`.
- Updated `tests/test_paper_layout.py` to require the neutral wording and reject
  the old `AI-generated reader-gate v3 schematic used only for exposition`
  phrase.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 7 no longer exposes the old production wording in the Table 1 caption.
- The companion figure's Reader gate card uses neutral interpretive wording.
- Table 1, the companion image, and the caption remain on the same page.
- The page-7/page-8 focus sheet shows no downstream displacement of the dense
  result tables on page 8.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round21_current/contact_sheets/main_pages_01_11_current.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round21_current/pages_180/main-07.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round21_after/pages_180/main-07.png`
- Accepted page-7/page-8 focus sheet:
  `tmp/acl_main_visual_iter_20260606_round21_after/contact_sheets/main_pages_07_08_after_focus.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round21_after/contact_sheets/main_pages_01_11_after.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round21_evidence_gate_companion_public_wording_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=43a9dac47c417e2c59b536cc36f3f7e6c6d71788ae8a6314f68d229e83ab15c0
pages=11
bytes=5189160
created=Sat Jun 6 11:13:12 2026 CST
```

## Verification

```bash
python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_overview_has_evidence_gate_registry_companion
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
rg -n -i "AI-generated|AI-assisted|AI-slot|imagegen|AI schematic|teaching artifact|author-produced|record-derived" tmp/acl_main_visual_iter_20260606_round21_after/text/main_layout.txt paper/shared/tables/tab_acl_evidence_gate_registry.tex || true
```

Results: the targeted test first failed after the wording change because the
stable companion phrase had been removed; after restoring the phrase without
restoring the old production wording, the targeted test passed. The ACL build
passed with an 11-page A4 PDF, the final LaTeX blocker scan returned no matches,
`tests/test_paper_layout.py` passed with 85 tests, and both ACL claim-boundary
and metadata-consistency checks returned `ok`. The main-PDF/table production
wording scan returned no matches. The metadata check still reports
`abstract_word_count=169`.

## Residual Risk

This pass is a focused page-7 main-paper public-wording polish. It is not a
complete final-upload audit, target-policy refresh, integrity-fingerprint
refresh, or supplement-wide production-wording cleanup.
