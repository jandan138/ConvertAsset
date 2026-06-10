# 2026-06-06 ACL Supplement Round 7 Review-Packet Contact Sheet

## Scope

This pass continued the ACL supplement crop/scale/incomplete-display scan. The
reviewed artifact was:

- `paper/venues/acl27/build/supplement.pdf`
- before SHA256:
  `4c5295b7306453238cfa9a2a14e8cbaea56c16ffec0b22d63b88c6d7a836cb0d`
- after SHA256:
  `5c4b86a78ae91f257f77c74c17cd6a17de45626b78f99542128c166db80f4237`
- 46 pages, A4

## Finding

The user-flagged Fig. S25 bottom claim-boundary gate was rechecked first. In the
current PDF page 27 and standalone
`fig_supplement_material_claim_boundary_atlas.png`, the gate is fully visible:
all three input rows, the center lock, all three output rows, and the right-side
boundary cards remain inside the figure frame. No S25 source or LaTeX change was
needed in this pass.

The new blocking visual issue was on Fig. S40 / PDF page 43, the
review-packet media manifest:

- the contact-sheet label lane was too narrow for labels such as
  `Material diagnostics`, putting labels too close to the first thumbnail;
- `_draw_contact_row` used fit/cover-style crop placement, which is wrong for a
  source-index contact sheet whose purpose is to show complete source snippets;
- the VLM target-view row still used crop coordinates that assumed a wider
  source image. The actual clean-rerender panel is `1602 x 1672`, so coordinates
  reaching `1720` or `1782` could introduce black out-of-bounds padding.

## Changes

- Updated `_draw_contact_row` in
  `paper/shared/figures/gen_supplement_task_media_atlases.py`:
  - label lane: `225` px -> `280` px;
  - source-index thumbnail placement: `_crop_fit(...)` -> `_crop_contain(...)`.
- Replaced the VLM target-view contact-sheet crops with card-bounded source
  coordinates inside the `1602 x 1672` source image.
- Regenerated:
  - `paper/shared/figures/fig_supplement_review_packet_contact_sheet.png`
  - `paper/shared/figures/fig_supplement_source_boundary_companion.png`
- Added regression assertions to
  `tests/test_paper_layout.py::test_supplement_review_packet_contact_sheet_is_registered_and_dense`
  for contain scaling, the wider label lane, and the source-bounded VLM crop.

## Visual Review

Reviewed artifacts:

- Before/full scan contact sheets:
  `tmp/acl_supp_visual_iter_20260606_round7/contact_sheets/`
- After page renders:
  `tmp/acl_supp_visual_iter_20260606_round7_after/pages_160/`
- Durable evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_round7_review_packet_contact_sheet_20260606.json`

Results:

- Standalone Fig. S40 PNG: PASS. Row labels no longer collide with thumbnails,
  and the VLM row shows four bounded target-view cards without black
  out-of-bounds padding.
- PDF page 43: PASS. The review-packet contact sheet is contained; the caption
  remains below the figure; no label/thumbnail occlusion is visible at page
  scale.
- PDF page 45: PASS. The source-boundary companion embeds the updated packet
  index cleanly and remains contained with its caption.
- PDF page 27 / Fig. S25: PASS. The bottom claim-boundary gate remains complete.

## Verification

- PASS: `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- PASS: `make -C paper acl27-supplement`
  - output: `build/supplement.pdf`
  - 46 pages, `48662958` bytes
- PASS: rendered page 27 and pages 43-45 at 160 dpi with `pdftoppm`
- PASS: supplement log scan found no `Overfull`, float-size, rerun, label, or
  undefined-reference warnings
- PASS:
  `python -m pytest -q tests/test_paper_layout.py -k 'review_packet_contact_sheet or reproducibility_has_visual_media_manifest or source_boundary_companion_is_registered_and_dense'`
  - `3 passed, 82 deselected`
- PASS: `python -m pytest -q tests/test_paper_layout.py`
  - `85 passed`

## Residual Risk

This was a visual containment, crop, occlusion, and scaling pass. Some atlas and
contact-sheet pages remain intentionally dense, but the final reviewed pages did
not show an obvious incomplete-display blocker.
