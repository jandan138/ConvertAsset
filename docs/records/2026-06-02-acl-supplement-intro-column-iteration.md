# 2026-06-02 ACL Supplement Intro Column Iteration

## Scope

This record documents the next visual-density iteration for the ACL supplement.
The immediate problem was that the material and navigation intro pages still
looked sparse after the previous strip pass: the preview image was constrained
to one ACL column, leaving the right column visually empty.

## Design Decision

A generated image was used only as a non-evidence layout reference for a denser
academic supplement page. The actual paper artifacts remain fully repo-native
and evidence-bound.

The implemented design uses two real-image vertical preview panels:

- `paper/shared/figures/fig_supplement_material_intro_column.png`
- `paper/shared/figures/fig_supplement_navigation_intro_column.png`

Each panel is built from tracked figures and selected still panels. The
material preview stacks covered-bin render rows, the selected clearcoat
diagnostic, and the procedural-texture limitation. The navigation preview
stacks paired-run metrics, selected rollout stills, 0036/0066 route context,
and selected case panels.

The corresponding supplement sections now briefly switch to `\onecolumn` for
the intro visual page and return to `\twocolumn` before the rest of the
appendix. This avoids a half-empty two-column page while preserving the normal
ACL-style layout for tables, atlases, and selected case pages.

## Files Changed

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
  - added `fig_supplement_material_intro_column.png`;
  - added `fig_supplement_navigation_intro_column.png`;
  - kept the older horizontal strip outputs available but no longer referenced
    by the supplement intro pages.
- `paper/shared/figures/sources.yaml`
  - registered both new column-preview figures and their tracked sources.
- `paper/venues/acl27/sections/supplement/04_material_effects.tex`
  - switched the intro preview to the material column figure;
  - used a local one-column page for the preview.
- `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
  - switched the intro preview to the navigation column figure;
  - used a local one-column page for the preview.
- `tests/test_paper_layout.py`
  - updated the regression tests so the supplement uses the new vertical
    column previews instead of the earlier horizontal strips.

## Visual Review

Local visual review of the rendered PDF pages:

- Page 23: PASS. The material page is now centered and dense enough to read as a
  visual page instead of a small left-column strip.
- Page 28: PASS. The navigation page now shows metric, still, route, and case
  evidence in one centered preview panel, with no clipped metric-axis fragments.

Quantitative page-render checks:

| Page | Previous nonwhite fraction | Current nonwhite fraction | Red fallback fraction |
| --- | ---: | ---: | ---: |
| Material intro page | about `0.03` | `0.1416` | `0.00001` |
| Navigation intro page | about `0.03` | `0.1411` | `0.00042` |

Structured visual-review evidence:

```text
paper/shared/evidence/raw/acl27_visual_review/supplement_intro_column_iteration_20260602.json
```

## Verification

Commands:

```bash
python paper/shared/figures/gen_supplement_task_media_atlases.py
python -m pytest -q tests/test_paper_layout.py
make -C paper acl27-supplement
pdftoppm -f 23 -l 23 -r 170 -png paper/venues/acl27/build/supplement.pdf tmp/acl27_supplement_onecolumn_iteration/page
pdftoppm -f 28 -l 28 -r 170 -png paper/venues/acl27/build/supplement.pdf tmp/acl27_supplement_onecolumn_iteration/page
pdftotext -layout paper/venues/acl27/build/supplement.pdf /tmp/acl27_supplement_column_iteration.txt
rg -n "/cpfs|/home/|/root/|zhuzihou|jandan138|github.com/jandan138|ConvertAsset.git" /tmp/acl27_supplement_column_iteration.txt
```

Results:

- `tests/test_paper_layout.py`: `27 passed`.
- `make -C paper acl27-supplement`: passed; output PDF has 40 pages.
- Privacy scan: no matches.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `144d70b8ee89302103506c9dcb316689dfc648a8177873a4de8aff8f9e753023`.

## Remaining Work

The supplement is no longer dominated by text-only pages in the material and
navigation intro positions, but the overall goal remains active. The next
iteration should review the full 40-page PDF page-by-page and identify any
remaining pages whose figures are too small, whose captions are too dense, or
whose visual evidence can be replaced by stronger tracked render panels.
