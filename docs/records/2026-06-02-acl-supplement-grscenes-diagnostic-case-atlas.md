# 2026-06-02 ACL Supplement GRScenes Diagnostic Case Atlas

This record documents a second GRScenes/VLM supplement visual-density pass. The
goal was to make the selected failure taxonomy, PASS-only pilot, and zoom-stress
tables less visually isolated by adding a real-render case atlas.

## Context

After adding the VLM coordinate protocol atlas, the GRScenes diagnostic section
still had table-heavy pages. The section already had a general VLM visual guide,
but Tables S4--S6 were still difficult to read as concrete scene evidence.

## Design

I used the image-generation skill once for a non-evidence layout reference:

- `/root/.codex/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_010add49e1a52a25016a1ea4fe05848195acb737ae5d5c25ff.png`

That generated image was not copied into the paper. It only suggested the
three-band layout: failure taxonomy, PASS-only pilot, and zoom stress.

The tracked atlas uses real GRScenes renders from the clean-rerender subset and
registered projection boxes:

- backpack `47aa36277a54f6ca90cc.zoom_018`
- clock `f35ef3d86c42446b7ddf.zoom_018`
- bottle `c27086f557d316584264.zoom_018`
- cup `e2ec085d524d5df4455d.zoom_020`

Each case shows original and converted target-view frames with the target box
and point-contract marker overlay. The figure is table-reading support, not a
new VLM prediction run.

## Visual QA Decision

An initial version tried to use faucet, picture, and zoom-019 rows to match more
table entries. Local visual review rejected that version because several
original-condition panels had large red material regions, which would
reintroduce the same visual risk previously removed from S4. The final version
therefore uses the clean-rerender case pool even though it covers fewer table
row categories.

## Changes

- Added `paper/shared/figures/fig_supplement_grscenes_diagnostic_case_atlas.png`.
- Extended `paper/shared/figures/gen_supplement_task_media_atlases.py` with a
  three-band GRScenes diagnostic case atlas builder.
- Registered the new figure, clean rerender reports, projection report, and
  source render frames in `paper/shared/figures/sources.yaml`.
- Inserted the atlas into
  `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`.
- Added layout/provenance/density/red-fallback tests in
  `tests/test_paper_layout.py`.
- Stored visual-review evidence at
  `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_diagnostic_case_atlas_20260602.json`.

## Visual Review

Local visual review was used; no independent subagent was spawned.

Findings:

- Source figure: PASS. It is dense, coherent, and uses clean original/converted
  render pairs without visible large red fallback material.
- Rendered PDF page 18: PASS. The atlas page is legible and its caption keeps
  the evidence boundary clear.
- Remaining limitation: the adjacent Table S4--S6 pages are still table-heavy.

## Verification

Commands run:

```bash
python paper/shared/figures/gen_supplement_task_media_atlases.py && python -m pytest -q tests/test_paper_layout.py -k "grscenes_diagnostic_case_atlas"
python -m pytest -q tests/test_paper_layout.py
make -C paper acl27-supplement
pdftotext paper/venues/acl27/build/supplement.pdf - | rg -n "GRScenes diagnostic case atlas|Red material|registered diagnostic figure|fig_vlm_grounding_cases|/cpfs|zhuzihou|jandan138|github.com|ConvertAsset.git" -S
pdftoppm -f 17 -l 20 -r 170 -png paper/venues/acl27/build/supplement.pdf /tmp/acl27_grscenes_case_atlas_check/page
```

Observed results:

- Targeted atlas test: `1 passed, 37 deselected`.
- Full layout test file: `38 passed`.
- Supplement build exited 0 and wrote a 40-page PDF.
- Supplement PDF SHA-256:
  `9c208abb588496d413ed4d5d341b7be2d1d384f35d7d558b7b69be37f03066cb`.
- Atlas figure SHA-256:
  `63edbd19c0f241141f113543bcc45519b706b4a61468f92062d6c7d657a4eaa6`.
- Source figure active fraction: `0.5005`; red-fallback fraction: `0.00000`.
- Rendered PDF page 18 active fraction: `0.2202`; red-fallback fraction:
  `0.00000`.
- PDF text scan found the new caption and did not find old red-material text,
  unsafe `fig_vlm_grounding_cases`, or local path leakage.

## Open Follow-Ups

The next useful pass is to rework the remaining material-effect risk and
safe-conversion recommender table pages, which still read as table-first rather
than render-first.
