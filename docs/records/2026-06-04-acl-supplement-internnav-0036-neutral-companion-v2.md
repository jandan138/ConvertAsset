# 2026-06-04 ACL Supplement InternNav 0036 Neutral Companion v2

## Scope

Round 18 ranked page 36 as the lowest non-reference supplement page. The page
held the third 0036/0066 selected neutral pair as two small horizontal strips,
leaving a large blank lower half. This pass replaced that pair with a denser
page-shaped companion built from registered navigation stills.

## Changes

- Added `fig_supplement_internnav_0036_neutral_companion.png` as a deterministic
  page-shaped evidence board.
- Reflowed case `891_891` and case `598_598` into start/mid/end grids with
  original and noMDL rows.
- Added a top context band from the registered 0036/0066 rollout sheet so the
  page carries more real navigation render material.
- Replaced the old third `\suppcasepair` page with one `figure*` include at
  `height=0.78\textheight`.
- Updated `sources.yaml` and layout tests to require the generated figure,
  registered sources, dense image statistics, and the new figure label.

## Claim Boundary

The companion remains selected qualitative navigation evidence. It does not add
a navigation metric, rerun, episode count, or media-package approval. The
compressed context band is a reading aid over already registered rollout rows.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_internnav_0036_neutral_companion_v2_20260604.json`

PDF review window:
`tmp/acl_supplement_page36_internnav_0036_neutral_v2_final_20260604/page-35.png`
through `tmp/acl_supplement_page36_internnav_0036_neutral_v2_final_20260604/page-37.png`

- Page 36 active245 at 90 dpi: `0.144668158` -> `0.310336080`
- Improvement from round 18 page 36: `+0.165667922`
- Intermediate horizontal companion active245: `0.191632727`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `e876bb5430ca86eb754badee537f4154b975f9d06e746da8884b676a314286e2`

Result: PASS by local `render-visual-reviewer` checklist. Page 36 is no longer
a sparse pair of horizontal strips; the registered rollout context band and both
neutral case grids are visible without clipping, and pages 35 and 37 keep their
expected content. Visual review was local rather than an independent subagent
review; the evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_internnav_0036_neutral_companion.png`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_internnav_0036_neutral_companion_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'internnav_0036_neutral_companion'`
  - RED first for the old `1800x1180` horizontal asset against the page-shaped
    companion requirement; GREEN after regenerating the `1500x1680` board.
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -f 35 -l 37 -png -r 144 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page36_internnav_0036_neutral_v2_final_20260604/page`
- `pdftoppm -f 36 -l 36 -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page36_internnav_0036_neutral_v2_final_90dpi_20260604/page`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
