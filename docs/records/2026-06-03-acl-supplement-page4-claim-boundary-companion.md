# 2026-06-03 ACL Supplement Page-4 Claim-Boundary Companion

## Scope

Improved the formerly sparse page 4 of the ACL supplement by adding
`fig_supplement_page4_claim_boundary_companion.png` under the overview's
``What This Supplement Does Not Prove'' discussion.

The companion ties the text-only exclusions to visible evidence categories:

- proxy render score: matched original/noMDL render views
- VLM target box: clean GRScenes target crops with projected boxes
- material cases: selected clearcoat and procedural-texture limits
- navigation media: selected rollout/case stills
- boundary marker: an imagegen-created schematic slot for exposition only

## Claim Boundary

The `boundary_marker` slot is AI-generated and exposition only. It is not a
render result, metric, VLM prediction, navigation run, benchmark row, or
evidence source.

The evidence-bearing thumbnails are copied from registered render/media figures.
The companion does not introduce a new experiment or result; it only makes the
overview's negative-claim boundary visually inspectable.

## Layout Outcome

The first placement used a floating column figure and created an unwanted sparse
page. The final placement uses an inline `\captionof{figure}` block after the
``What This Supplement Does Not Prove'' paragraph, so the companion lands in the
page-4 right column and the supplement remains 44 pages.

Measured rendered-page active fractions:

- page 4: `0.127577`, from prior sparse reference `0.074102`
- page 3: `0.132858`
- page 5: `0.232060`
- page 6: `0.261243`

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_page4_claim_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_page4_boundary_marker_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_page4_claim_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_page4_claim_boundary_companion_20260603.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py -k "page4_claim_boundary_companion"`
- `make -C paper acl27-supplement`
- Rendered PDF pages 3-6 with `pdftoppm`.
- PDF text positive scan for the page-4 companion and AI-exposition boundary.
- PDF text negative scan for stale red-material diagnostic wording, local paths,
  and author-profile leakage.

Visual review was local rather than an independent subagent review; the evidence
JSON records `independent_subagent: false`.
