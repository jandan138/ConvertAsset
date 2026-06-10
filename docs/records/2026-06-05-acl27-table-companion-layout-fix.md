# 2026-06-05 ACL27 Table Companion Layout Fix

## Context

The ACL27 main PDF had a visual readability issue on the Table 1 evidence-gate
registry companion. The lower "Registered cross-evidence render strip" used six
small columns in a single row, so the proxy-scene and InternNav thumbnails looked
like narrow partial cuts after the companion image was scaled into the main paper.

## Change

- Updated `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Added optional multi-row and contain placement support to `_draw_opener_band`
  while preserving its default single-row cover behavior for existing callers.
- Rebuilt only `fig_supplement_evidence_gate_registry_companion.png`.
- Changed the evidence-gate companion strip to use a 3-column by 2-row layout
  and contain-mode tiles for the lower registered evidence thumbnails.

## Verification

- `python -m py_compile paper/shared/figures/gen_supplement_task_media_atlases.py`
- Imported the figure script by path and ran `build_evidence_gate_registry_companion()`.
- `make -C paper acl27`
- Exported ACL27 PDF page 8 with `pdftoppm` and reviewed:
  - `tmp/acl27_table_companion_fix/pdf_review/page08_full_visible.png`
  - `tmp/acl27_table_companion_fix/pdf_review/page08_companion_full_deep.png`
  - `tmp/acl27_table_companion_fix/pdf_review/page08_companion_bottom_deep.png`

## Result

The Table 1 companion now shows the lower evidence thumbnails as complete,
larger 3x2 tiles. The main PDF still keeps the companion as a compact visual
registry under Table 1, but the previous narrow-column partial-image failure is
removed.
