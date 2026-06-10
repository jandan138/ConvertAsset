# 2026-06-03 ACL Supplement Proxy Metric Derivation Companion V2

## Scope

Reworked `fig_supplement_proxy_metric_derivation_companion.png` for the ACL
supplement derivation section after the user explicitly allowed imagegen assets
inside the paper.

The v2 companion keeps the figure as a hybrid composition:

- registered object render pair: original MDL and noMDL views for paired proxy
  notation, MSE, PSNR, and SSIM
- registered scene render pair: broader context for feature-similarity proxy
  interpretation
- registered proxy render audit strip: additional real render thumbnails from
  existing evidence figures
- `proxy_metric_axis`: an imagegen-created abstract schematic slot for
  exposition only

## Claim Boundary

The `proxy_metric_axis` slot is AI-generated and exposition only. It is not a
render result, metric, model prediction, benchmark row, evidence source, or task
result.

Evidence-bearing content remains the registered render pairs, registered render
audit strip, metric definitions, and existing evidence manifests. The generated
slot is deliberately abstract and kept in a separate card so it can be replaced
later by a deterministic or real-render schematic if needed.

## Layout Outcome

The first v2 placement made the figure denser but pushed captions onto
caption-only pages. The final layout:

- moves the proxy companion directly after paired-render notation so the figure
  is large enough to read;
- replaces the post-SSIM forced page break with ordinary spacing so feature and
  grounding definitions continue naturally;
- shortens and shrinks the grounding companion caption;
- reduces the grounding companion height enough to keep its caption on the same
  page;
- keeps the supplement at 44 pages.

Rendered-page active fractions from the final `pdftoppm -r 140` review:

- page 12: `0.120017`, proxy companion readable and no isolated caption
- page 13: `0.098968`, grounding definitions, figure, and caption on one page
- page 14: `0.087270`, navigation companion page, not caption-only
- page 15: `0.149848`, metric-boundary bridge page

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_proxy_metric_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_proxy_metric_axis_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_proxy_metric_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_proxy_metric_derivation_companion_v2_20260603.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py -k "proxy_metric_derivation_companion"`
- `make -C paper acl27-supplement`
- Rendered PDF pages 12-15 with `pdftoppm -r 140`.
- Visual review was local rather than an independent subagent review; the
  evidence JSON records `independent_subagent: false`.
