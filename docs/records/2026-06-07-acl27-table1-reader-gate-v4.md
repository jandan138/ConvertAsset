# 2026-06-07 ACL27 Table 1 Reader Gate v4

## Context

The ACL27 Table 1 evidence-gate companion still had two visual issues after the
layout fix: some registered evidence thumbnails were easier to read with
contain-style placement, and the Reader gate panel needed a more publication-like
schematic than a deterministic code-drawn flowchart.

## Change

- Added `paper/shared/figures/ai_slots/fig_supplement_evidence_gate_reader_v4_ai_slot.png`.
- Updated `paper/shared/figures/gen_supplement_task_media_atlases.py` to use the
  v4 AI Reader gate slot instead of a code-drawn flow diagram.
- Removed the temporary code-drawn Reader gate helper.
- Kept contain-style placement for the Table 1 companion evidence thumbnails so
  the registered images are not force-filled with center-crop behavior.
- Regenerated `paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png`.

## Verification

- `python -m py_compile paper/shared/figures/gen_supplement_task_media_atlases.py`
- Imported the figure script by path and ran `build_evidence_gate_registry_companion()`.
- `make -C paper acl27`
- Rendered ACL27 page 6 and reviewed:
  - `tmp/acl27_table1_reader_gate_v4/pdf_review/page06_table1_full.png`
  - `tmp/acl27_table1_reader_gate_v4/pdf_review/page06_reader_gate.png`
  - `tmp/acl27_table1_reader_gate_v4/pdf_review/page06_bottom_strip.png`

## Result

The Reader gate is now an AI-generated academic schematic showing evidence rows,
a scoped-claim gate, and blocked over-broad promotion. The lower evidence strip
remains complete in the rendered PDF.
