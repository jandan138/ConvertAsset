# 2026-06-02 ACL Supplement Visual Atlas Iteration

## Context

The ACL supplement was visually stronger after the InternNav grouping pass, but
the user still found it ugly, scattered, and too light on rendered evidence. The
goal of this iteration was to add more real render material near the front of
the supplement without treating generated imagery as experiment evidence.

## Changes

- Added `paper/shared/figures/gen_supplement_render_atlas.py`.
- Generated `paper/shared/figures/fig_supplement_render_atlas.png`.
- Registered the new figure in `paper/shared/figures/sources.yaml`.
- Added `paper/venues/acl27/sections/supplement/01a_render_atlas.tex`.
- Inserted the render-atlas section immediately after the supplement overview.
- Updated the overview reading order and reproducibility source list.
- Added layout tests for the new section, registered figure, and atlas density.

The new atlas uses only tracked real render sources:

- proxy object renders under `paper/shared/evidence/raw/renders/`;
- GRScenes render views under `paper/shared/figures/out_tmp/`.

The image-generation skill was used only for non-evidence layout ideation. No
image-generated bitmap was inserted as render, VLM, material, or navigation
evidence.

## Visual Review

Local render-visual review found that the first atlas draft was landscape and
left too much empty space on an A4 portrait page. The generator was revised to
produce a portrait, eight-row MDL/noMDL atlas. The focused rendered page is now
usable as a dense front-loaded evidence page.

Recorded review:

- `paper/shared/evidence/raw/acl27_visual_review/supplement_visual_atlas_iteration_20260602.json`

Known residual issue:

- page 4 remains a text-only introduction page for the atlas section; the next
  iteration should either merge that introduction with a visual page or add a
  small real-render strip.

## Verification

Commands:

```bash
python paper/shared/figures/gen_supplement_render_atlas.py
python -m pytest -q tests/test_paper_layout.py -k 'supplement_has_render_evidence_atlas or supplement_render_atlas_figure_is_registered_and_dense or supplement_has_appendix_sections'
make -C paper acl27-supplement
python -m pytest -q tests/test_paper_layout.py
pdftotext paper/venues/acl27/build/supplement.pdf - | rg -n '/cpfs|/home/|/root/|zhuzihou|jandan138|github\.com/jandan138|ConvertAsset\.git' || true
```

Results:

- targeted supplement tests: `3 passed, 18 deselected`;
- full layout tests: `21 passed`;
- supplement build: `paper/venues/acl27/build/supplement.pdf`;
- PDF page count: 40 A4 pages;
- PDF SHA-256: `8296854178441d86fc426dd18aedf00ae626d86683bf91b48fb2c9121210ce8e`;
- privacy scan: no forbidden author/path tokens found in extracted PDF text.
