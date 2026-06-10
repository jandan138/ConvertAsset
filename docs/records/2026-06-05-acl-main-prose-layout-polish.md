# 2026-06-05 ACL Main Prose Layout Polish

## Scope

Continued the ACL27 main-paper iteration for rendered-PDF visual review,
layout polish, and ACL-style manuscript language. The target artifact was:

- `paper/venues/acl27/build/main.pdf`
- 11 pages, A4
- PDF creation timestamp: Fri Jun 5 09:42:06 2026 CST

This was a prose/layout polish pass only. It did not change experimental
numbers, figure sources, tables, citations, or claim boundaries.

## Findings

The current main PDF had no obvious figure clipping, occlusion, page-edge crop,
or broken float. Figure 3 remained at the bottom of page 6 and Figure 4 remained
contained on page 10.

The higher-impact issues were manuscript-level:

- `sections/abstract.tex` did not match the already-polished OpenReview metadata
  abstract, so the metadata-consistency gate failed.
- The opening prose still read partly like an internal audit of claim ledgers
  rather than an ACL-style evaluation story.
- Page 9 put the `Conclusion` heading low in the left column; it was not a
  blocking orphan, but it looked tighter than necessary.

## Changes

Updated main-paper prose:

- `paper/venues/acl27/sections/abstract.tex`
  - Synchronized the PDF abstract with the 183-word OpenReview metadata abstract.
- `paper/venues/acl27/sections/intro.tex`
  - Reframed the hook around the rendered scene as the measurement interface.
  - Tightened the evidence-gate paragraph while preserving the explicit boundary
    that the gates do not establish broad downstream robustness.
- `paper/venues/acl27/sections/results.tex`
  - Tightened figure/table transition sentences so visual panels orient readers
    while frozen tables remain the source of quantitative claims.
- `paper/venues/acl27/sections/discussion.tex`
  - Compressed repeated audit phrasing and improved the page-9 section flow into
    Conclusion.
- `paper/venues/acl27/sections/conclusion.tex`
  - Recast the conclusion around synthetic-scene material conversion as an
    observable intervention in language-grounding evidence.

## Evidence

Raw evidence:

- `paper/shared/evidence/raw/acl27_visual_review/main_prose_layout_polish_20260605.json`

Rendered review artifacts:

- Baseline contact sheet:
  `tmp/acl_main_visual_iter_20260605_round4/contact_sheets/main_pages_01_11_180.png`
- First prose pass contact sheet:
  `tmp/acl_main_visual_iter_20260605_round5_prose_after/contact_sheets/main_pages_01_11_round5_prose_after.png`
- Final contact sheet:
  `tmp/acl_main_visual_iter_20260605_round6_discussion_compact/contact_sheets/main_pages_01_11_round6_discussion_compact.png`
- Focus pages:
  `tmp/acl_main_visual_iter_20260605_round6_discussion_compact/pages_180/page-09.png`
  `tmp/acl_main_visual_iter_20260605_round6_discussion_compact/pages_180/page-10.png`

Final artifact fingerprint:

- `paper/venues/acl27/build/main.pdf`
  - SHA-256:
    `711191e54b0b0e72c44dd60adc8717a4e5d91d8c19266349a7f25e5de822c07c`
  - Pages: 11
  - Bytes: 5,194,558

## Verification

- PASS: `python paper/venues/acl27/scripts/check_metadata_consistency.py`
  - Abstract matches metadata and remains under 200 words.
- PASS: `python paper/venues/acl27/scripts/check_claim_boundaries.py`
  - No claim-boundary, unsafe-figure, or venue-wrapper violations.
- PASS: `make -C paper acl27`
  - Built `build/main.pdf` as an 11-page PDF.
- PASS: final log scan found no overfull boxes, float-too-large warnings,
  undefined labels, rerun warnings, or lineno warnings under the blocker pattern.
- PASS: rendered all 11 pages at 180 dpi and manually reviewed the final contact
  sheet plus page 9 and page 10 at full scale.
- PASS: targeted layout tests:
  `python -m pytest -q tests/test_paper_layout.py -k 'acl_intro_uses_latest_low_text_method_chain_schematic or acl_main_forces_results_floats_before_discussion or acl_results_avoids_page_break_prone_original_nomdl_phrase'`
- PASS: JSON syntax and whitespace checks for touched tracked files and new
  record/evidence files.

## Residual Risk

This pass improves one prose/layout layer. It does not prove that the full main
paper is final: a later iteration can still tune the page-9 Conclusion break,
compress references, or run a broader ACL-style peer-review pass over every
section.
