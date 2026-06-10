# 2026-06-03 ACL Supplement InternNav Upload-Gate V2

## Scope

Page 38 still read as a sparse upload/status page after the first closure-card
pass. This iteration rebuilds
`fig_supplement_internnav_upload_gate_closure_card.png` as a taller
render-forward card with more registered navigation media and a replacement
AI-generated upload-gate schematic.

## Changes

- Added `fig_supplement_internnav_upload_gate_v2_ai_slot.png` as the selected
  exposition-only upload-gate schematic.
- Updated
  `paper/shared/figures/ai_slot_manifests/fig_supplement_internnav_upload_gate_closure_card.yaml`
  to point at the v2 AI slot and source generated image.
- Rebuilt the upload-gate closure card at 1800 x 2200 with a 3 x 3 registered
  navigation media wall, deterministic closure cards, and a paper claim-boundary
  strip.
- Expanded `sources.yaml` and the density guard to include selected case 02/03
  and 0036/0066 case 02/03 render panels.
- Raised the ACL supplement include cap for this figure to `0.80\textheight`
  while keeping the caption and next page intact.

## Claim Boundary

The AI slot is exposition only. It is not route-success evidence, an
official-scene statistic, a navigation metric, or a replacement for the
registered closure artifacts. The evidence-bearing material in the page remains
the registered navigation stills, route overlays, selected qualitative package,
and official-scene closure files.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_internnav_upload_gate_v2_20260603.json`

Page 38 raster:
`tmp/acl_supplement_upload_gate_v2_review_20260603/page-38.png`

Result: PASS. Page 38 keeps the taller card and caption on one page, page 39
begins the next theory section normally, and page 38 active245 fraction
increased from `0.103449` to `0.216744060`.

## Files

- `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_internnav_upload_gate_closure_card.png`
- `paper/shared/figures/ai_slots/fig_supplement_internnav_upload_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_internnav_upload_gate_closure_card.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_internnav_upload_gate_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 140 -f 38 -l 39 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_upload_gate_v2_review_20260603/page`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`7156fbec266a1228f831ffc8c52d107ad8807387ccd26933c2d25c6ac9558595`
