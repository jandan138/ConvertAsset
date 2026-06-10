# 2026-06-03 ACL Supplement Navigation Media Boundary V2

## Scope

Page 37 still looked sparse after the first navigation media-boundary pass. This
iteration keeps the media-inventory claim boundary unchanged but rebuilds
`fig_supplement_navigation_media_boundary_strip.png` as a taller render-forward
figure with more registered selected-case and route-case panels.

## Changes

- Added `fig_supplement_navigation_media_package_v2_ai_slot.png` as the
  selected exposition-only media-package gate schematic.
- Updated
  `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_media_boundary_strip.yaml`
  to point at the v2 AI slot and source generated image.
- Rebuilt the navigation media-boundary figure at 1800 x 2120 as a 12-panel
  registered selected-media wall plus deterministic boundary cards.
- Expanded `sources.yaml` and the density guard to include selected cases 03-06,
  0036/0066 route cases 04-06, and the v2 AI slot.
- Raised the ACL supplement include cap for this figure to `0.66\textheight`
  while keeping the caption and next page intact.

## Claim Boundary

The AI slot is exposition only. It is not a navigation metric, route-success
statistic, video-upload approval, or replacement for the 99-episode paired run.
The evidence-bearing content remains the registered selected stills, route
overlays, media atlas, and readable route panels.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_media_boundary_v2_20260603.json`

Page 37 raster:
`tmp/acl_supplement_navigation_media_boundary_v2_review_20260603/page-37.png`

Result: PASS. Page 37 keeps the media-inventory text, taller figure, and
caption on one page. Page 38 still starts with the official-scene upload-gate
closure card. Page 37 active245 fraction increased from `0.115970607` to
`0.170340214`.

## Files

- `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png`
- `paper/shared/figures/ai_slots/fig_supplement_navigation_media_package_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_media_boundary_strip.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_media_boundary_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 140 -f 37 -l 38 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_navigation_media_boundary_v2_review_20260603/page`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`228107b97ddd91aab7adad900b3799629b00eda9cce348e119516937f7c66ae1`
