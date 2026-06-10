# 2026-06-10 ACL27 Table 1 Reader Gate v5 AI Schematic

## Context

The ACL27 Table 1 Reader gate v4 schematic communicated the broad idea of
evidence rows, scoped claims, and blocked promotion, but it read as a generic
funnel/gate. The requested revision was to use a pure AI-generated academic
schematic whose own text, arrows, labels, and layout explain how to read a Table
1 row.

## Change

- Added `paper/shared/figures/ai_slots/fig_supplement_evidence_gate_reader_v5_table_reading_ai_slot.png`.
- Updated `paper/shared/figures/gen_supplement_task_media_atlases.py` to use the
  v5 slot in the Table 1 companion Reader gate card.
- Removed the code-drawn text inside the Reader gate card, leaving only the
  existing card frame and the AI-generated schematic.
- Regenerated `paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png`.

## Prompt Boundary

The v5 slot is a publication-style AI infographic with the title
`Evidence-bound reading` and three large columns: `Evidence used`,
`Scoped claim`, and `Blocked promotion`. It is an interpretive schematic for
reading the table, not experimental evidence.

## Verification

- `python -m py_compile paper/shared/figures/gen_supplement_task_media_atlases.py`
- Imported the figure script by path and ran `build_evidence_gate_registry_companion()`.
- `make -C paper acl27`
- `pdfinfo paper/venues/acl27/build/main.pdf`
- Rendered ACL27 page 6 and reviewed:
  - `tmp/acl27_table1_reader_gate_v5/pdf_review/page-06.png`
  - `tmp/acl27_table1_reader_gate_v5/pdf_review/page06_table1_companion.png`
  - `tmp/acl27_table1_reader_gate_v5/pdf_review/page06_reader_gate_wide_right_full_tall.png`
  - `tmp/acl27_table1_reader_gate_v5/pdf_review/page06_bottom_strip_full.png`

## Result

The rendered PDF keeps Table 1 on page 6 with the updated Reader gate visible
and contained. The right-side schematic now directly maps Table 1's row logic:
evidence used supports one scoped claim, while broader promotion remains blocked
without new evidence. The lower registered evidence strip remains complete.
