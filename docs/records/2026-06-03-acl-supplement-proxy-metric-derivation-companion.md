# 2026-06-03 ACL Supplement Proxy Metric Derivation Companion

Superseded by
[2026-06-03 ACL Supplement Proxy Metric Derivation Companion V2](2026-06-03-acl-supplement-proxy-metric-derivation-companion-v2.md),
which replaces the `proxy_metric_lens` slot with `proxy_metric_axis`, adds a
registered render audit strip, and fixes the final derivation-section page flow.

## Scope

Improved the formerly sparse proxy-metric derivation page in the ACL supplement
by adding `fig_supplement_proxy_metric_derivation_companion.png` under the
paired-render, PSNR, and SSIM definitions.

The companion uses registered original/noMDL render pairs to make the equations
visually grounded:

- object render pair: paired render notation, MSE, PSNR, and SSIM are computed
  under matched camera and lighting
- scene render pair: feature-similarity proxies are read against broader scene
  context
- proxy-metric lens: an imagegen-created schematic explains the reading rule
  for pixel, structure, and feature proxies

## Claim Boundary

The `proxy_metric_lens` slot is AI-generated and exposition only. It is not a
render result, metric, model prediction, benchmark row, or evidence source.

The evidence-bearing content remains the registered original/noMDL render pairs
and the metric definitions in the text. The first imagegen candidate was
rejected because it looked too much like realistic evidence imagery; the final
slot is abstract and separated in the right-side card.

## Layout Outcome

The first LaTeX placement moved the figure to a mostly empty new page. The final
placement keeps the companion on page 12 as a compact page-bottom visual, so the
page is no longer pure formulas while the derivation text remains readable.

Measured rendered-page active fractions:

- page 12: `0.098933`, from prior sparse reference `0.0455`
- page 13: `0.152343`
- page 14: `0.139624`

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_proxy_metric_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_proxy_metric_lens_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_proxy_metric_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_proxy_metric_derivation_companion_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k "proxy_metric_derivation_companion or derivations_have_render_companions"`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- Rendered PDF pages 12-14 with `pdftoppm`.
- PDF text positive scan for the proxy companion and AI-exposition boundary.
- PDF text negative scan for stale red-material diagnostic wording, local paths,
  and author-profile leakage.

Visual review was local rather than an independent subagent review; the evidence
JSON records `independent_subagent: false`.
