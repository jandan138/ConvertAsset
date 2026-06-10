# 2026-06-04 ACL Supplement GRScenes Failure-Taxonomy v4

## Scope

Round 35 still ranked page 22 among the lowest-density non-reference
supplement pages after the selected6 neutral companion pass. Page 22 already
had the v3 failure-taxonomy companion, but the visual support was still short:
it exposed the row cards and one audit strip, without enough focused render
crops to make the taxonomy rows feel inspectable.

## Changes

- Added
  `paper/shared/figures/ai_slots/fig_supplement_grscenes_failure_taxonomy_gate_v4_ai_slot.png`
  as a bounded failure-taxonomy gate schematic.
- Expanded
  `paper/shared/figures/fig_supplement_grscenes_failure_taxonomy_table_companion.png`
  from `1800 x 1260` to `1800 x 1640`.
- Added a two-row focused render matrix covering selected taxonomy edge cases
  across backpack, clock, bottle, cup, picture, and faucet rows.
- Updated the Figure S21 placement to `0.56\textheight` after testing a taller
  `0.62\textheight` placement that pushed the caption to a sparse page.
- Folded the standalone explanatory paragraph into the Figure S21 caption so
  page 23 starts with the PASS-only table companion rather than an orphan text
  paragraph.
- Registered the new AI slot in `sources.yaml`, the AI-slot manifest, and the
  layout tests.

## Claim Boundary

The added render matrix is table-reading support over registered GRScenes
render evidence. It does not add VLM predictions, benchmark rows, an exhaustive
taxonomy, taxonomy-frequency estimates, or a new model-performance claim. The
AI-generated gate is exposition only.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_failure_taxonomy_v4_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_grscenes_failure_taxonomy_table_companion.png`

- Size: `1800 x 1640`
- Layout-guard active238: `0.438528117`
- Layout-guard active245: `0.449656843`
- Red-pixel fraction: `0.009454607`
- SHA-256:
  `e6089fa12f74044f3c98700a57175e621738261ec090f2bb22d0174690cf504a`

Failure-taxonomy gate v4 slot:
`paper/shared/figures/ai_slots/fig_supplement_grscenes_failure_taxonomy_gate_v4_ai_slot.png`

- Size: `1536 x 1024`
- Layout-guard active238: `0.250704447`
- Layout-guard active245: `0.295733770`
- Red-pixel fraction: `0.005057017`
- SHA-256:
  `0a1c274d28cb97bc2b9894c4b3911815362ee58b8f0f12fce3ea4548701c978f`

PDF review window:
`tmp/acl_supplement_page22_grscenes_failure_taxonomy_v4_final_resolved_20260604/page-21.png`
through
`tmp/acl_supplement_page22_grscenes_failure_taxonomy_v4_final_resolved_20260604/page-24.png`

- Page 22 active245 at 90 dpi before round 35: `0.170561579`
- Page 22 active245 at 90 dpi after: `0.214127740`
- Improvement from round 35 page 22: `+0.043566161`
- Supplement PDF: 45 pages, A4, `50,412,965` bytes
- PDF SHA-256:
  `8a6b9a8a060706e85cef22e1353abdb18124cd3683fa5f3841a627630a0d909f`

Result: PASS by local `render-visual-reviewer` checklist. Page 22 now shows a
denser v4 companion and a same-page caption without clipping or overlap. Page
23 starts with the PASS-only table companion, so the iteration does not create
a new sparse page. Visual review was local rather than an independent subagent
review; the evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grscenes_failure_taxonomy_table_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_grscenes_failure_taxonomy_gate_v4_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_failure_taxonomy_table_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_failure_taxonomy_v4_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'grscenes_tables_have_render_companions or grscenes_table_companions_are_registered_and_dense'`
  - RED first for the old caption/slot expectation and then for the v3
    companion density under the new threshold; GREEN after adding the v4 slot,
    focused render matrix, and accepted PDF placement.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 21 -l 24 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page22_grscenes_failure_taxonomy_v4_final_resolved_20260604/page`
- `pdftoppm -r 90 -png -f 22 -l 22 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page22_grscenes_failure_taxonomy_v4_final_resolved_90dpi_20260604/page`
