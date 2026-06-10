# 2026-06-02 ACL Supplement Visual Evidence Roadmap

## Scope

The supplement still looked too text-heavy near the front. This pass added a
render-first roadmap page immediately after the claim-boundary opening so that
reviewers see the four evidence lanes before entering the longer tables and
derivations.

## What Changed

- Added `paper/shared/figures/fig_supplement_visual_evidence_roadmap.png`.
- Added the roadmap to
  `paper/venues/acl27/sections/supplement/00_overview.tex`.
- Registered the figure in `paper/shared/figures/sources.yaml`.
- Extended `paper/shared/figures/gen_supplement_task_media_atlases.py` with a
  deterministic compositor for the roadmap.
- Added layout-source tests in `tests/test_paper_layout.py`.
- Recorded reproducible visual-review evidence in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_visual_evidence_roadmap_20260602.json`.

## Imagegen Role

The image-generation output was used only as a non-evidence layout reference:

`/root/.codex/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_08c9b2592dc8c59e016a1ec4d2f8a88194a44e3521b2cfd409.png`

The paper figure itself is deterministic and composed from registered repo
figures or raw render stills. It does not introduce a new metric, VLM run, or
navigation claim.

## Visual Review

Local render review found the roadmap readable as an index page. Page 2 in the
rendered supplement has active fraction 0.1888 at 120 dpi and a red fraction of
0.000099. The figure has four lanes: proxy render pairs, GRScenes target views,
material diagnostics, and InternNav media.

The remaining layout risk is not solved by this page. Low-density pages remain:
p15, p36, p23, p6, p22, p17, p5, p4, p21, p13, p14, and p3, plus the references
tail on p41. These should be the next targets for additional render-heavy
iteration.

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k "visual_evidence_roadmap"`
  first failed two tests before implementation, then passed with `2 passed, 40
  deselected`.
- `python -m pytest -q tests/test_paper_layout.py` passed with `42 passed`.
- `make -C paper acl27-supplement` passed and produced a 41-page A4
  `paper/venues/acl27/build/supplement.pdf`.
- A `pdftotext` scan matched only the roadmap caption among the checked tokens;
  no private path, author token, or old red-material caption token was observed.
