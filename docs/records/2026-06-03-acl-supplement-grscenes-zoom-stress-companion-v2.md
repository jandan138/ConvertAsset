# 2026-06-03 ACL Supplement GRScenes Zoom-Stress Companion V2

## Scope

Reworked the ACL supplement GRScenes zoom-stress table companion after the user
allowed imagegen assets inside the paper, provided they are composed through the
project AI-slot figure workflow and kept distinct from experimental evidence.

The v2 companion is a hybrid figure:

- registered GRScenes original/noMDL render pairs remain the evidence-bearing
  panels;
- a new `zoom_stress_gate` imagegen slot explains how to read the stress table;
- an added registered render audit strip fills the previously sparse lower part
  of page 24 with real render anchors;
- deterministic code owns layout, labels, captions, and claim-boundary text.

## Claim Boundary

The `zoom_stress_gate` slot is AI-generated and exposition only. It is not a VLM
prediction, benchmark row, render result, material-preservation result, or
additional experiment.

The evidence for this page remains the zoom-stress table and registered
original/noMDL render pairs. The AI slot only illustrates the table-reading
gate, and the caption explicitly says the panels are not additional VLM
predictions or benchmark rows.

## Layout Outcome

Before this pass, the page-24 audit identified the GRScenes zoom-stress table
page as one of the sparsest supplement pages, with active fraction `0.086817`
in the page-density audit reference.

The revised page keeps Table S6, Figure S23, its caption, and the boundary
paragraph together. The final `pdftoppm -r 140` page review recorded page 24 at
active fraction `0.117216`, with no red fallback pixels under the recorded
threshold. The supplement remains 44 pages.

Local visual review result:

- standalone figure: readable render-pair cards, separated AI gate card, and
  bottom registered render audit strip;
- rendered PDF page 24: no caption-only spill, no obvious clipping, and reduced
  blank area below the table;
- page 25 material-effect opener remains normal after the expansion.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grscenes_zoom_stress_table_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_grscenes_zoom_stress_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_zoom_stress_table_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_zoom_stress_companion_v2_20260603.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py -k "grscenes_tables_have_render_companions or grscenes_table_companions_are_registered_and_dense"`
- `python -m pytest -q tests/test_paper_layout.py` (`73 passed`)
- `make -C paper acl27-supplement`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_zoom_stress_companion_v2_20260603.json >/dev/null`
- `pdftotext paper/venues/acl27/build/supplement.pdf -` positive/negative claim-boundary scan
- Rendered PDF pages 23-25 with `pdftoppm -f 23 -l 25 -r 140 -png`.
- Visual review was local rather than an independent subagent review; the
  evidence JSON records `independent_subagent: false`.
