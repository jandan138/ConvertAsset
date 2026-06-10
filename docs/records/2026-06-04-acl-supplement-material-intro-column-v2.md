# 2026-06-04 ACL Supplement Material Intro Column v2

## Scope

Round 23 identified page 25 as a low-density non-reference page. The page was
conceptually useful as the material-effect section opener, but the figure was a
narrow `900 x 1500` column placed at only `0.72\textwidth`, leaving substantial
empty page area.

## Changes

- Rebuilt `fig_supplement_material_intro_column.png` as a wider page-shaped
  `1600 x 1700` material evidence board.
- Enlarged the registered material renders for covered bins: opacity/emission,
  scene object surfaces, cup target, and backpack target.
- Enlarged the selected clearcoat and procedural-texture limitation diagnostics.
- Added a registered material comparison wall and a compact reading-boundary
  footer for covered bins, clearcoat, and procedural texture.
- Updated the material section include size from `0.72\textwidth` /
  `0.70\textheight` to `0.96\textwidth` / `0.78\textheight`.
- Updated layout tests to require the wider page-shaped material opener.

## Claim Boundary

The opener still reuses registered material figures only. It is not a converter
ranking, population rate, material-mechanism proof, or new experiment. Covered
bins support bounded qualitative inspection; clearcoat remains a selected
NVIDIA failure diagnostic; procedural texture remains a limitation case unless
it is preserved or baked.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_material_intro_column_v2_20260604.json`

PDF review window:
`tmp/acl_supplement_page25_material_intro_v2_final_20260604/page-24.png`
through `tmp/acl_supplement_page25_material_intro_v2_final_20260604/page-26.png`

- Standalone figure size: `900 x 1500` -> `1600 x 1700`
- Standalone figure active238: `0.441958519` -> `0.506519485`
- Page 25 active245 at 90 dpi: `0.150664449` -> `0.233414278`
- Improvement from round 23 page 25: `+0.082749829`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `eccefbc90c345ff18e7f78192300ad5d90876f4a8ccee433bb62382386decf01`

Result: PASS by local `render-visual-reviewer` checklist. Page 25 now has a
larger material evidence opener without clipping or neighbor-page float
displacement. Visual review was local rather than an independent subagent
review; the evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_material_intro_column.png`
- `paper/venues/acl27/sections/supplement/04_material_effects.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_material_intro_column_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'intro_pages_have_real_visual_strips or intro_strips_are_registered_and_dense'`
  - RED first for the old `900 x 1500` figure and narrow LaTeX include;
    GREEN after rebuilding the `1600 x 1700` opener and widening the include.
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -r 144 -png -f 24 -l 26 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page25_material_intro_v2_final_20260604/page`
- `pdftoppm -r 90 -png -f 25 -l 25 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page25_material_intro_v2_final_90dpi_20260604/page`
