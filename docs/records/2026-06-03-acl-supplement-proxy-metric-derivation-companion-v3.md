# 2026-06-03 ACL Supplement Proxy Metric Derivation Companion v3

## Scope

This pass revisits page 12 of the ACL supplement after the round-10 density
audit made it the lowest non-reference page. The goal was to make the
proxy-metric derivation spread more render-backed while preserving the
metric-vs-task claim boundary.

## Changes

- Rebuilt `fig_supplement_proxy_metric_derivation_companion.png` at
  `1800x1260`.
- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_proxy_metric_axis_v2_ai_slot.png`.
- Enlarged the registered object and scene render-pair cards.
- Replaced the audit strip title with `registered proxy render ladder` and
  expanded it with zoom-019 backpack and clock render pairs.
- Increased the page-12 include cap from `0.34\textheight` to
  `0.40\textheight`.
- Updated `tests/test_paper_layout.py` to require the v2 slot, zoom-019 source
  registration, taller figure, denser active fraction, and caption ladder phrase.

## Claim Boundary

The v2 proxy-axis AI slot remains exposition only. It is not a metric, model
prediction, benchmark row, render result, VLM output, navigation run, or task
result. Evidence-bearing content remains the registered render pairs, render
ladder, formulas, and existing evidence manifests.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_proxy_metric_derivation_companion_v3_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_proxy_metric_derivation_companion.png`

- Size: `1800x1260`
- Layout-guard active fraction: `0.381409171`
- Red-pixel fraction: `0.007043210`
- SHA-256:
  `e0a7abf5af7d692a4d420d772658ec8788f3a8dac9e6af025e20a0d442e609a0`

PDF review window:
`tmp/acl_supplement_page12_proxy_derivation_v2_20260603/page-12.png` through
`tmp/acl_supplement_page12_proxy_derivation_v2_20260603/page-15.png`

- Page 12 active245 at 90 dpi before: `0.133667310`
- Page 12 active245 at 90 dpi after: `0.157892120`
- Page 13 active245 at 90 dpi after: `0.134736802`
- Page 14 active245 at 90 dpi after: `0.135478690`
- Page 15 active245 at 90 dpi after: `0.136022996`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 12 keeps the
larger proxy companion and caption on the page, starts PSNR below it, and does
not shift the page-13 to page-15 derivation companions.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_proxy_metric_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_proxy_metric_axis_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_proxy_metric_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_proxy_metric_derivation_companion_v3_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'proxy_metric_derivation_companion or derivations_have_render_companions'` (RED before implementation, GREEN after)
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py`
- `make -C paper acl27-supplement`
- `pdftoppm -f 12 -l 15 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page12_proxy_derivation_v2_20260603/page`
- `pdftoppm -f 12 -l 15 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page12_proxy_derivation_v2_20260603/page90`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_proxy_metric_derivation_companion_v3_20260603.json`
- `pdftotext -f 12 -l 12 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page12_proxy_derivation_v3_final_20260603/page12.txt`
- `pdfinfo paper/venues/acl27/build/supplement.pdf` (`45` A4 pages)
- `git diff --check` on touched tracked files, plus a direct trailing-whitespace
  scan over the new doc and evidence JSON
