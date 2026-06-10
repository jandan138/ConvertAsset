# ACL Clean-Pool Table Readability Polish

Date: 2026-05-30.

## Context

A page-scale visual review of the current ACL candidate found that the GRScenes
clean-pool pilot table was present but hard to inspect because the whole table
was scaled through `\resizebox`. The table supports the core VLM-grounding
evidence chain, so it should be readable without asking reviewers to infer the
numbers from surrounding prose.

## Changes

- Reworked `paper/shared/tables/tab_grscenes_vlm_clean_pool_pass15.tex` to use
  fixed-width text columns instead of whole-table image-style scaling.
- Removed the repeated `Format` column and moved the shared structured-text
  prompt detail into the caption.
- Preserved all metric values and boundary semantics.
- Added a layout regression test in `tests/test_paper_layout.py` so this table
  does not return to `\resizebox` downscaling.
- Recorded the page-scale visual review at
  `paper/shared/evidence/raw/acl27_visual_review/clean_pool_table2_visual_review_20260530.json`.

## Verification

```bash
python -m pytest -q tests/test_paper_layout.py
make -C paper acl27
pdftoppm -png -r 150 -f 6 -singlefile paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_table_review_20260530_b/page-06
```

The focused layout test passed. The ACL build stayed at 11 A4 pages, LaTeX log
search found no `Overfull`, `undefined`, or warning lines after the final build,
and the rendered page-6 visual review passed.
