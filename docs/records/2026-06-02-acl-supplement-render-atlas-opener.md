# 2026-06-02 ACL Supplement Render Atlas Opener

## Scope

The Render Evidence Atlas opener page was still sparse: page 6 introduced a
render-heavy appendix but initially contained only explanatory text. This pass
added a real-render section opener so the appendix starts with visual evidence
rather than a blank-looking text page.

## What Changed

- Added `paper/shared/figures/fig_supplement_render_atlas_opener.png`.
- Added a deterministic compositor to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered the opener in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/01a_render_atlas.tex` to use
  a controlled one-column opener block before returning to the two-column
  supplement layout.
- Added opener layout and density tests in `tests/test_paper_layout.py`.
- Recorded visual-review provenance in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_render_atlas_opener_20260602.json`.

## Imagegen Role

The generated image
`/root/.codex/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_0ef86247e532efe7016a1ee615583c8195bebad2fbd94c89fd.png`
was used only as a layout reference. The final opener is deterministic and uses
registered real render crops.

## Visual Review

Three layouts were tried. The first portrait single-column block put a small
image on page 6 but still looked too empty. The second wide `figure*` float
looked better as a source image but drifted to page 7. The final controlled
one-column block keeps the opener on page 6 and raises the page active fraction
from 0.0218 to 0.199897 at 120 dpi.

The page still has some lower whitespace, and the navigation thumbnails can be
cleaned further in a later pass. For this iteration, the page is no longer a
text-only opener and the figure remains evidence-bounded.

## Verification

- Targeted opener tests first failed before implementation.
- The final targeted opener tests passed with `2 passed, 42 deselected`.
- `python -m pytest -q tests/test_paper_layout.py` passed with `44 passed`.
- `make -C paper acl27-supplement` passed and produced a 41-page A4
  `paper/venues/acl27/build/supplement.pdf`.
- A `pdftotext` scan for private paths, author tokens, old red-material caption
  tokens, and `fig_vlm_grounding_cases` returned no matches.
- The final opener image has active fraction 0.536169 and red fraction 0.000312.
- The next low-density targets are p15, p36, p23, p22, p17, p5, p4, p21, p13,
  p14, and p3, plus the references tail on p41.
