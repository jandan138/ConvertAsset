# 2026-06-02 ACL Supplement VLM Coordinate Protocol Atlas

This record documents one supplement visual-density iteration for the active
ACL supplement goal. The specific target was the VLM coordinate protocol pages,
which were previously mostly text and tables.

## Context

The rendered supplement audit showed that the VLM protocol and GRScenes
diagnostic region still had sparse pages. Before this pass, pages 14--16 were
mostly prose and coordinate tables, with active rendered-page density around
0.03--0.06. This made the supplement feel table-heavy even though the project
already had many real GRScenes render assets.

## Design

I used the image-generation skill once for a non-evidence layout reference:

- `/root/.codex/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_010add49e1a52a25016a1e9caa66d88195b33b4e12839692d0.png`

That generated image was not copied into the paper and is not evidence. It only
guided the composition: large render panels, compact legend, target box,
raw-center marker, normalized-1000 bbox-center marker, and small table-link
cards.

The tracked atlas uses real project evidence:

- original and converted GRScenes retake zoom render frames for backpack,
  clock, and bottle
- registered target boxes from
  `paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json`

The atlas intentionally does not add VLM point predictions. It explains the
coordinate protocol and baseline-scoring contract only.

## Changes

- Added `paper/shared/figures/fig_supplement_vlm_coordinate_protocol_atlas.png`.
- Extended `paper/shared/figures/gen_supplement_task_media_atlases.py` with a
  target-aware crop overlay helper and the new atlas builder.
- Registered the atlas and raw render/projection sources in
  `paper/shared/figures/sources.yaml`.
- Inserted the atlas into
  `paper/venues/acl27/sections/supplement/02_vlm_protocol.tex` before the
  coordinate-ablation tables.
- Added tests in `tests/test_paper_layout.py` for LaTeX inclusion, registry
  provenance, dimensions, and visual density.
- Stored visual-review evidence at
  `paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_protocol_atlas_20260602.json`.

## Visual Review

Local visual review was used; no independent subagent was spawned. The final
source figure and rendered PDF page were checked.

Findings:

- Source figure: PASS. The atlas is dense and coherent; target boxes and
  markers are visible; render panels fill the page without target clipping.
- Rendered PDF page 14: PASS. The page contains the VLM protocol introduction,
  the atlas, and a caption that states the figure is protocol guidance, not a
  new prediction result.
- No large red fallback-material artifact is visible.
- The adjacent coordinate-ablation and baseline table pages remain table-heavy;
  this pass improves the VLM protocol entry page but does not complete the
  broader supplement beautification goal.

## Verification

Commands run:

```bash
python paper/shared/figures/gen_supplement_task_media_atlases.py && python -m pytest -q tests/test_paper_layout.py -k "vlm_coordinate_protocol"
python -m pytest -q tests/test_paper_layout.py
make -C paper acl27-supplement
pdftotext paper/venues/acl27/build/supplement.pdf - | rg -n "VLM coordinate protocol visual atlas|Red material|registered diagnostic figure|fig_vlm_grounding_cases|/cpfs|zhuzihou|jandan138|github.com|ConvertAsset.git" -S
pdfimages -f 14 -l 14 -png paper/venues/acl27/build/supplement.pdf /tmp/pdfimg14/img
pdftoppm -f 14 -l 14 -singlefile -r 170 -png paper/venues/acl27/build/supplement.pdf /tmp/page14_single
```

Observed results:

- Targeted atlas test: `1 passed, 35 deselected`.
- Full layout test file: `36 passed`.
- Supplement build exited 0 and wrote
  `paper/venues/acl27/build/supplement.pdf`.
- Supplement PDF: 39 pages,
  SHA-256 `7e8cb929dfa204b777d942b6ca00380499fe67eaefc6c5b3fb96e0fce7bfb1d9`.
- Atlas figure SHA-256:
  `3db4308a8aa583a0b7fe05ff0de90afddd19954cafe921c04b85905cc0374013`.
- PDF text scan found the new caption and did not find old red-material
  diagnostic text, unsafe `fig_vlm_grounding_cases`, or local path leakage.

## Open Follow-Ups

The next useful visual-density pass is still the remaining table-heavy pages:
GRScenes failure taxonomy/PASS-only/zoom-stress tables and the material-effect
risk/recommender tables.
