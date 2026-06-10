# 2026-06-03 ACL Supplement Navigation Intro Opener V2

## Scope

The InternNav / DualVLN supplement opener on page 29 still read as a small,
centered preview with too much unused page area. This pass rebuilds
`fig_supplement_navigation_intro_column.png` as a denser evidence opener with
more registered navigation render/still material and a clearly bounded
AI-generated review-gate schematic.

## Changes

- Rebuilt the opener from `1700 x 1320` to `1700 x 1540`.
- Tightened the official paired-run metric crop to the actual lower-is-better
  chart instead of pulling in neighboring chart labels.
- Enlarged the selected case and 0036/0066 case crops.
- Added a neutral case closure row using the remaining selected examples:
  selected6 cases 05-06 and 0036/0066 cases 05-06.
- Registered those additional real case sources in
  `paper/shared/figures/sources.yaml`.
- Added/updated layout tests so the navigation opener must include the AI-slot
  manifest, the review-gate disclosure caption, the richer case-source set, and
  a dense output image.

## AI Slot Policy

The navigation-review gate slot remains exposition only. It is not navigation
evidence, not a route-success metric, not a benchmark run, and not a
video-package approval. Critical labels and claim-boundary text are drawn by
deterministic code or LaTeX.

The evidence-bearing content in the opener remains registered metrics, rollout
stills, route overlays, media atlas context, media-boundary context, and selected
case panels.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_intro_opener_v2_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_navigation_intro_column.png`

- Size: `1700 x 1540`
- Active fraction: `0.400294118`
- SHA-256:
  `449c2236f00159b1efa0c7e1d04be2ba068d4a8754ed6c19b6e22783fdef3416`

Page 29 raster:
`tmp/acl_supplement_navigation_intro_review_20260603/page-29.png`

Result: PASS by local `render-visual-reviewer` checklist. Page 29 now shows the
navigation opener immediately after the section introduction with no clipping
or caption collision. The page active fraction increased from `0.149580030` to
`0.174102332`; the added content is real registered case material rather than a
larger empty canvas.

Visual review was local rather than an independent subagent review because the
available subagent tool requires explicit delegation permission.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_navigation_intro_column.png`
- `paper/shared/figures/ai_slots/fig_supplement_navigation_review_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_intro_column.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_intro_opener_v2_20260603.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_intro_pages_have_real_visual_strips tests/test_paper_layout.py::test_supplement_intro_strips_are_registered_and_dense`
- `python -m pytest -q tests/test_paper_layout.py`
- `make -C paper acl27-supplement`
- `pdftoppm -f 29 -l 30 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_navigation_intro_review_20260603/page`
- `pdftotext -f 29 -l 29 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_navigation_intro_review_20260603/page-29.txt`
- `git diff --check -- docs/records/README.md paper/shared/figures/gen_supplement_task_media_atlases.py paper/shared/figures/sources.yaml paper/venues/acl27/sections/supplement/05_internnav_visuals.tex tests/test_paper_layout.py`

Final PDF:
`paper/venues/acl27/build/supplement.pdf`
