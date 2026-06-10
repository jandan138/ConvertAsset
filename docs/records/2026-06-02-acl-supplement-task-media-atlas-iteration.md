# 2026-06-02 ACL Supplement Task Media Atlas Iteration

## Context

After the first render-atlas pass, the front of the supplement became more
visual, but the material-effect and InternNav blocks still looked like separate
tables, isolated screenshots, and index sheets. This iteration targeted pages
21--35 of the ACL supplement.

## Changes

- Added `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Generated:
  - `paper/shared/figures/fig_supplement_material_diagnostic_atlas.png`;
  - `paper/shared/figures/fig_supplement_navigation_media_atlas.png`.
- Registered both figures in `paper/shared/figures/sources.yaml`.
- Replaced the standalone supplemental material figure in
  `paper/venues/acl27/sections/supplement/04_material_effects.tex` with the
  material diagnostic atlas.
- Replaced two standalone InternNav index-sheet figures in
  `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex` with the
  navigation media atlas.
- Added layout tests requiring both atlas figures to be registered, referenced,
  and visually dense.

The image-generation skill was used only for a non-evidence layout reference.
No generated bitmap was included in the paper or treated as experiment
evidence.

## Visual Review

Local render-visual review over pages 21--35 found:

- page 24 is now a stronger material evidence page because covered bins and
  limitation cases are visible together;
- page 29 is now a stronger navigation overview page because metrics, selected
  stills, readable 0036/0066 route context, and compact index context are
  combined;
- pages 23 and 28 remain mostly text-only section-introduction pages and should
  be the next polish targets.

Recorded review:

- `paper/shared/evidence/raw/acl27_visual_review/supplement_task_media_atlas_iteration_20260602.json`

## Verification

Commands:

```bash
python paper/shared/figures/gen_supplement_task_media_atlases.py
python -m pytest -q tests/test_paper_layout.py -k 'task_media_atlases'
make -C paper acl27-supplement
python -m pytest -q tests/test_paper_layout.py
pdftotext paper/venues/acl27/build/supplement.pdf - | rg -n '/cpfs|/home/|/root/|zhuzihou|jandan138|github\.com/jandan138|ConvertAsset\.git' || true
```

Results:

- targeted atlas tests: `2 passed, 21 deselected`;
- full layout tests: `23 passed`;
- supplement build: `paper/venues/acl27/build/supplement.pdf`;
- PDF page count: 40 A4 pages;
- PDF SHA-256: `f99460b5780e8db37515ed5b1900d0c02e4a5a38654a651c6531b10c2fc99c75`;
- privacy scan: no forbidden author/path tokens found in extracted PDF text.
