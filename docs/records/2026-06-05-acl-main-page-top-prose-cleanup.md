# 2026-06-05 ACL Main Page-Top Prose Cleanup

## Scope

Continued the ACL main-paper visual and prose iteration on:

- `paper/venues/acl27/build/main.pdf`
- Final SHA256:
  `fcb67ada780a1b053e05ea991d197258b36349babc9601725b2a4c850824122a`
- 11 pages, A4

This round targeted reader-visible page-top fragments that remained after the
previous front-story and figure-placement polish.

## Findings

The current rendered PDF before this pass still had two disruptive page-top
continuations:

- Page 3 opened with the tail of "infrastructure" and "intervention" from the
  Related Work opener.
- Page 5 opened with the tail of the clean-pool table interpretation sentence,
  and the first rewrite briefly exposed a `Qwen2.5-VL` page-break split.

## Changes

- Rewrote the Related Work opener so the conversion-step motivation closes on
  page 2 and page 3 now starts with the complete paragraph heading
  "Vision-language grounding and navigation."
- Rewrote the clean-pool interpretation sentence in Results:
  - "separates answer stability from point-grounding stability" replaces the
    longer "answer-level recognition..." sentence.
  - The Qwen paragraph now starts naturally on page 5 with a complete sentence:
    "Qwen2.5-VL shows weaker parser stability..."
- Kept all numeric claims, tables, figure references, and claim boundaries
  unchanged.

## Visual Evidence

Rendered evidence is under:

- `tmp/acl_main_visual_iter_20260605_round11_page_tops/pages_180_after5/`
- `tmp/acl_main_visual_iter_20260605_round11_page_tops/text/after5_layout.txt`
- `tmp/acl_main_visual_iter_20260605_round11_page_tops/contact_sheets_after5/main_pages_01_04_after5.png`
- `tmp/acl_main_visual_iter_20260605_round11_page_tops/contact_sheets_after5/main_pages_05_08_after5.png`
- `tmp/acl_main_visual_iter_20260605_round11_page_tops/contact_sheets_after5/main_pages_09_11_after5.png`

After the final rebuild:

- Page 3 starts with a complete Related Work paragraph heading and no longer
  starts with "ture..." or "tion."
- Page 5 starts with a complete Qwen2.5-VL sentence and no longer starts with
  "ing", "VL", or "parser-stable" fragments.
- Figures 1-4 remain fully visible with captions separated from image content.
- The table page and references pages were unchanged in page count and did not
  gain a new visible collision or crop.

## Verification

- PASS: `make -C paper acl27`
- PASS: `python paper/venues/acl27/scripts/check_claim_boundaries.py`
- PASS: `python paper/venues/acl27/scripts/check_metadata_consistency.py`
- PASS: `python -m pytest -q tests/test_acl_claim_boundaries.py tests/test_acl_preupload_gate.py`
  - Result: `26 passed`
- PASS: `python -m pytest -q tests/test_paper_layout.py -k 'acl_intro or acl_method or acl_main or results'`
  - Result: `5 passed, 80 deselected`
- PASS: `rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|lineno Warning" paper/venues/acl27/build/main.log`
  - Result: no matches

## Residual Risk

This round was a targeted rendered-PDF cleanup. It does not claim that the full
main-paper objective is complete. Further iterations can still improve global
ACL-style prose, table density, and final-read polish.
