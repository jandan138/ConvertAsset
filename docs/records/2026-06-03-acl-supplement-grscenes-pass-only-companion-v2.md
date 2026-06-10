# 2026-06-03 ACL Supplement GRScenes PASS-Only Companion V2

## Scope

Page 23 of the ACL supplement looked sparse and the PASS-only table companion
still reused zoom-stress backpack/clock rows. This iteration makes the page
match Table S5 more directly: one bottle pair, two cup views, and one faucet
view.

## Changes

- Replaced the PASS-only companion layout with a taller 1800 x 1040 deterministic
  composition.
- Added registered real-render anchors for the second cup view
  (`bb985fd4504a1afe8516.zoom_017`) and faucet
  (`c8ee4b66274b05d242c2.zoom_017`).
- Added a larger registered PASS-only pilot render audit strip with six real
  render tiles.
- Added `fig_supplement_grscenes_pass_only_gate_ai_slot.png` as an exposition-only
  gate slot and updated the slot manifest.
- Updated the ACL supplement caption and include height to keep the AI slot
  clearly outside experimental evidence.

## Imagegen Note

A fresh nested Codex imagegen bridge attempt could not access the built-in
`image_gen` tool in that session, so no new bitmap was generated. The v2 slot
uses an unused prior imagegen candidate and records that limitation in the
manifest and raw review record.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_pass_only_companion_v2_20260603.json`

Page 23 raster:
`tmp/acl_supplement_grscenes_pass_only_v2_review_20260603/page-23.png`

Result: PASS. The page has no clipping or caption spill, and page 24 remains
intact. Page 23 active-pixel density at 140 dpi increased from the earlier audit
baseline of `0.089843` to `0.14255663737529023`.

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_grscenes_tables_have_render_companions tests/test_paper_layout.py::test_supplement_grscenes_table_companions_are_registered_and_dense`
- `make -C paper acl27-supplement`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`c79701b4fd77d87a7e3c9e29e385c7c53ff1dbb9bf0631721a6f3eedba8a9a2b`
