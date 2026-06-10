# 2026-06-02 ACL Supplement Material Claim-Boundary Atlas

This record documents a material-effect supplement visual-density pass. The
goal was to make the material risk matrix and NVIDIA-baseline interpretation
less table-first by adding a render-driven claim-boundary atlas.

## Context

After the GRScenes diagnostic atlas pass, the material-effect section still had
a sparse page where the risk matrix, recommender prose, and NVIDIA-baseline
interpretation sat mostly in one narrow column. That page was technically
correct but visually weak for a supplement that is supposed to carry the paper's
large render evidence package.

## Design

I used the image-generation skill once for a non-evidence layout reference:

- `/root/.codex/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_035a3f5d5aac6898016a1eb0bbb4548199b957c19f3269b5d1.png`

The generated image was not copied into the paper and is not evidence. It only
informed the layout direction: a compact page where real render thumbnails sit
next to the risk-matrix interpretation.

The tracked paper figure uses existing material-effect render evidence:

- covered bins from `fig_material_effect_baseline_qualitative.png`;
- selected clearcoat diagnostic from
  `fig_material_effect_supplemental_qualitative.png`;
- procedural-texture limitation diagnostic from the same supplemental figure.

The atlas is table-reading support. It does not add a new material benchmark,
rerun the NVIDIA baseline, or change the paper's claim boundary.

## Changes

- Added `paper/shared/figures/fig_supplement_material_claim_boundary_atlas.png`.
- Extended `paper/shared/figures/gen_supplement_task_media_atlases.py` with a
  material claim-boundary atlas builder.
- Registered the figure and sources in `paper/shared/figures/sources.yaml`.
- Inserted the atlas into
  `paper/venues/acl27/sections/supplement/04_material_effects.tex`.
- Added `\FloatBarrier` after the figure so it appears before the material risk
  matrix instead of floating past the sparse table page.
- Added layout/provenance/density/red-fallback tests in
  `tests/test_paper_layout.py`.
- Stored visual-review evidence at
  `paper/shared/evidence/raw/acl27_visual_review/supplement_material_claim_boundary_atlas_20260602.json`.

## Visual Review

Local visual review was used; no independent subagent was spawned.

Findings:

- Source figure: PASS. The three rows are visually separated, labels are not
  clipped, and the clearcoat/procedural rows no longer expose unrelated adjacent
  row labels.
- Rendered PDF page 24: PASS. The previous material table-first page is replaced
  by a render-first visual page with Figure S10.
- Red-material risk: PASS. No large red fallback-material artifact is visible.
- Remaining limitation: pages 25--26 remain table/text heavy. This goal remains
  active; the next pass should reflow or visually support those remaining pages.

## Verification

Commands run:

```bash
python paper/shared/figures/gen_supplement_task_media_atlases.py && python -m pytest -q tests/test_paper_layout.py -k "material_claim_boundary_atlas or has_task_media_atlases"
python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_material_claim_boundary_atlas_20260602.json >/tmp/supp_material_claim_boundary_json.out && python -m pytest -q tests/test_paper_layout.py
make -C paper acl27-supplement
pdftoppm -f 24 -l 26 -png -r 150 paper/venues/acl27/build/supplement.pdf /tmp/acl27_material_final/page
pdftotext paper/venues/acl27/build/supplement.pdf - | rg -n "Figure S10|Material claim-boundary visual atlas|Red material|registered diagnostic figure|fig_vlm_grounding_cases|/cpfs|zhuzihou|jandan138|github.com|ConvertAsset.git" -S
```

Observed results:

- Targeted layout tests: `2 passed, 37 deselected`.
- Full layout test file: `39 passed`.
- Supplement build exited 0 and wrote a 40-page PDF.
- Supplement PDF SHA-256:
  `b248a4b11cceabe0acfa7ab4acabe28539e41523d22829ed1c37cd1e1aad9705`.
- Atlas figure SHA-256:
  `e86e0e1861df1365d4c58e508209b96f1d95fa181c4f5201f5549019d2595c06`.
- Source figure active fraction: `0.2254`; red-fallback fraction: `0.00003`.
- Rendered PDF page 24 active fraction: `0.0986`; red-fallback fraction:
  `0.00000`.
- PDF text scan found the Figure S10 caption and did not find old red-material
  text, unsafe `fig_vlm_grounding_cases`, or local path leakage.

## Open Follow-Ups

The remaining material-effect table/recommender pages should still be reflowed.
The best next local target is to replace the page-25/page-26 table/prose split
with either a compact one-column table layout or another small render-supported
summary panel.
