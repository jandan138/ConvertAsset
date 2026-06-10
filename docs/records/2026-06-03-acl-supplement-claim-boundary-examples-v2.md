# 2026-06-03 ACL Supplement Claim-Boundary Examples V2

## Scope

The first claim-boundary examples pass improved the page, but page 5 still read
as a small centered visual with too much unused lower-page area. This iteration
keeps the same conservative evidence boundary and makes the page more
render-heavy by expanding the figure with a cross-gate audit strip.

## Changes

- Rebuilt `paper/shared/figures/fig_supplement_claim_boundary_examples.png`
  from `1800 x 1620` to `1800 x 2070`.
- Added the AI-slot asset
  `paper/shared/figures/ai_slots/fig_supplement_claim_boundary_examples_gate_ai_slot.png`.
- Added the AI-slot manifest
  `paper/shared/figures/ai_slot_manifests/fig_supplement_claim_boundary_examples.yaml`.
- Added more registered real-render sources to
  `paper/shared/figures/sources.yaml`: VLM zoom renders and InternNav case
  panels.
- Updated `paper/venues/acl27/sections/supplement/00_overview.tex` so the
  claim-boundary examples figure uses the taller v2 asset and discloses that
  the generated gate schematic is used only for exposition.
- Hardened `tests/test_paper_layout.py` so the figure must include the new
  disclosure, manifest, registered sources, and a dense portrait output.

## AI Slot Boundary

The AI-generated gate is only an explanatory schematic. It is not an
experimental result, metric, VLM run, material experiment, navigation run, or
benchmark output. Evidence-bearing content in the figure remains tracked proxy,
VLM, material-effect, and InternNav render/still material registered in
`paper/shared/figures/sources.yaml`.

Critical labels and claim-boundary statements are drawn by deterministic code
or LaTeX, not trusted from generated pseudo-text.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_claim_boundary_examples_v2_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_claim_boundary_examples.png`

- Size: `1800 x 2070`
- Active fraction: `0.264567096`
- SHA-256:
  `84bd07e27c2a9920dca6b88d009803a38daed19d7b1895e7f54c670c83fe78cf`

Page 5 raster:
`tmp/acl_supplement_claim_boundary_examples_v2_review_20260603/page-05.png`

Final PDF:
`paper/venues/acl27/build/supplement.pdf`

- SHA-256:
  `8ad3be3856ab0eca98598ccda4be71bc70a8fce25f80f94d6711b4f8144e6a54`

Result: PASS by local `render-visual-reviewer` checklist. The page now uses
most of the available area for the larger claim-boundary figure, including a
bottom audit strip with proxy, VLM, material, and navigation render evidence.
The figure is not clipped and the caption does not collide with it.

At the same 90 dpi thresholded density used for the sparse-page audit, page 5
increased from `0.112731282` to `0.153370683`. Some bottom whitespace remains
after the caption, but the page no longer presents as a detached small visual.

Visual review was local rather than an independent subagent review because the
available subagent tool requires explicit delegation permission.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_claim_boundary_examples.png`
- `paper/shared/figures/ai_slots/fig_supplement_claim_boundary_examples_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_claim_boundary_examples.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_claim_boundary_examples_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k "claim_boundary_examples"`
  passed after the implementation with `2 passed`.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
  completed and regenerated the supplement task/media figures.
- `python -m pytest -q tests/test_paper_layout.py`
  passed with `74 passed`.
- `make -C paper acl27-supplement`
  exited 0; `build/supplement.pdf` was up-to-date and contains 45 pages.
- `pdftoppm -f 5 -l 5 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_claim_boundary_examples_v2_review_20260603/page`
  regenerated `page-05.png`.
- `pdftoppm -f 5 -l 5 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_claim_boundary_examples_v2_review_20260603/page90`
  regenerated `page90-05.png`.
- `pdftotext -f 5 -l 5 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_claim_boundary_examples_v2_review_20260603/page-05.txt`
  found the claim-boundary disclosure and no private local-path tokens.
- `git diff --check -- docs/records/README.md paper/shared/figures/gen_supplement_task_media_atlases.py paper/shared/figures/sources.yaml paper/venues/acl27/sections/supplement/00_overview.tex tests/test_paper_layout.py`
  exited 0 with no whitespace errors.
