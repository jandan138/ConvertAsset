# 2026-06-04 ACL Supplement GRScenes Failure-Taxonomy v3

## Scope

Round 19 ranked page 22 as the lowest non-reference supplement page after the
page36 InternNav companion pass. Page 22 already had a v2 failure-taxonomy
companion, but the left companion area still left an unused third row while the
right table-reading gate occupied three rows. This pass fills that row with
registered render evidence.

## Changes

- Added `picture | zoom stress` and `faucet | PASS-only` original/noMDL render
  pair cards to the failure-taxonomy companion.
- Kept the standalone companion size at `1800 x 1260` and kept the existing
  v2 AI table-reading gate.
- Raised the failure-taxonomy companion density guard in
  `tests/test_paper_layout.py` from `0.28` to `0.34` active238.
- Kept Table S4, the caption, the explanatory paragraph, and page flow
  unchanged.

## Claim Boundary

The new picture and faucet cards are table-reading anchors over already
registered GRScenes render evidence. They do not add VLM predictions, benchmark
rows, taxonomy frequencies, or a new model-performance claim.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_failure_taxonomy_v3_20260604.json`

PDF review window:
`tmp/acl_supplement_page22_grscenes_failure_v3_final_20260604/page-21.png`
through `tmp/acl_supplement_page22_grscenes_failure_v3_final_20260604/page-23.png`

- Standalone companion active238: `0.281968254` -> `0.361131393`
- Page 22 active245 at 90 dpi: `0.144728070` -> `0.170570502`
- Improvement from round 19 page 22: `+0.025842432`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `5a206468cc3e73180828c64317d643b12ac66cdfd7e5321d799640a519b003b7`

Result: PASS by local `render-visual-reviewer` checklist. Page 22 shows the
filled third render-pair row without caption or paragraph overlap, and page 23
still starts with the PASS-only table and companion. Visual review was local
rather than an independent subagent review; the evidence JSON records
`independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grscenes_failure_taxonomy_table_companion.png`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_failure_taxonomy_v3_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'grscenes_table_companions_are_registered_and_dense'`
  - RED first for the old companion active238 `0.281968254` against the new
    `0.34` threshold; GREEN after adding the third-row render pairs.
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -f 21 -l 23 -png -r 144 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page22_grscenes_failure_v3_final_20260604/page`
- `pdftoppm -f 22 -l 22 -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page22_grscenes_failure_v3_final_90dpi_20260604/page`
- `pdftotext -f 21 -l 23 paper/venues/acl27/build/supplement.pdf -`
