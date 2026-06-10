# 2026-06-04 ACL Supplement Render Visibility p7/p8

## Context

The global ACL supplement visual audit found that pages 7 and 8 did not have a
LaTeX clipping problem. The rendered PDF pages showed complete figure boxes, but
the proxy object evidence inside those boxes was composed as wide cover-style
tiles from 4:3 source renders. At paper scale, the proxy rows read as cropped
close-ups rather than complete object evidence.

## Changes

- Added a regression test,
  `test_supplement_render_evidence_preserves_proxy_object_context`, requiring
  proxy object context views and preventing the render-atlas generator from
  reintroducing `cover=True`.
- Reworked `paper/shared/figures/gen_supplement_render_atlas.py` so each proxy
  row shows four contained views: `MDL front`, `noMDL front`, `MDL detail`, and
  `noMDL detail`.
- Reworked
  `paper/shared/figures/gen_supplement_task_media_atlases.py` so
  `fig_supplement_render_scene_evidence_extended.png` pairs full proxy-object
  context with contained material-detail views instead of direct crop-fit
  close-ups.
- Updated `paper/shared/figures/sources.yaml` for the new front-context render
  sources and refreshed the ACL supplement captions in
  `paper/venues/acl27/sections/supplement/01a_render_atlas.tex`.

## Visual Review

Local paper-scale visual review used the render visual reviewer protocol. No
independent subagent was spawned because this environment only permits
`spawn_agent` when explicitly requested.

- Page 7: figure and caption are contained; proxy object front/context and
  detail tiles are visible inside their frames.
- Page 8: full-context and material-detail proxy views are both visible; the
  figure does not collide with the caption.
- Residual caveat: proxy objects are inherently low contrast because the source
  renders are white furniture on light backgrounds, but the composer no longer
  crops them into wide horizontal strips.

## Evidence

- Review JSON:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_render_visibility_p7_p8_20260604.json`
- Rendered page evidence:
  `tmp/acl_render_visibility_fix_20260604/supplement_pages/page-07.png`
  and `tmp/acl_render_visibility_fix_20260604/supplement_pages/page-08.png`
- Supplement contact sheet:
  `tmp/acl_render_visibility_fix_20260604/supplement_110/contact_sheet.png`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'preserves_proxy_object_context'`
- `python paper/shared/figures/gen_supplement_render_atlas.py`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py -k 'render_atlas or render_scene_evidence_extended or preserves_proxy_object_context or review_packet_contact_sheet'`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 160 -f 7 -l 8 paper/venues/acl27/build/supplement.pdf tmp/acl_render_visibility_fix_20260604/supplement_pages/page`

## Follow-Up

The broader supplement polish goal remains active. The next global visual-review
risks are pages 22 and 23, which have the highest red-pixel ratios in the latest
110 dpi supplement audit, followed by the dense navigation pages around pages
33-38.
