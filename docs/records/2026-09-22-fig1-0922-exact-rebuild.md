# 2026-09-22 — fig1-0922 (ICLR hero) exact reconstruction: PNG/SVG/PPTX

## Task

Replicate `paper/shared/figures/fig1-0922/convert-from-draw.png` (1672×941)
pixel-exactly in exact mode, iterating versions, with the editable PPTX
required to align. Prior replication experience from
`scenario-forge/paper/venues/iclr2027/figures/lab2sim/` (spec+SVG+PPTX
projection) and this repo's `paper/shared/figures/iclr_system_hero/`
(locked-layout PIL/PPTX renderer) was used as the starting pattern.

## What was built

`paper/shared/figures/fig1-0922/rebuild/`:

- `layout.py` — locked layout: 3 panels, 20 rounded frames, 4 header bands,
  4 legend swatches, 64 native text elements with measured ink boxes,
  47 raster slots (photos, icons, arrows, badges, composites).
- `build_fig.py` — one builder → PNG (PIL 3× supersample), SVG (native text,
  embedded rasters), PPTX (python-pptx native shapes/text + named picture
  slots at identical EMU boxes). Per-element text calibration through the
  real render pipeline locks ink width and ink top-left.
- `assets/` + `assets/crops.json` — all raster slots are lossless crops of
  the author-owned source PNG; every slot diffs 0.000.
- `rounds/round01..round13` — archived iterations (never overwritten).
- Deliverables at `paper/shared/figures/fig1-0922/fig1_rebuild.{png,svg,pptx}`
  (+ `fig1_rebuild_pptx_render.pdf`, `fig1_rebuild.pptx.audit.json`).

## Findings / decisions

1. **Measurement**: panel borders located by light-blue border runs; photo
   slots snapped via adjacent-pixel difference spikes; one slot (probe3) had
   to be re-snapped after the detector locked onto the orange dashed overlay
   edge instead of the photo edge (x 854 → 841). Text ink boxes measured per
   color-class mask; two boxes were contaminated (icon overlap, region clip)
   and re-measured.
2. **Font**: the source face is narrow — Liberation Sans Narrow matches ink
   width and cap height together; Liberation Sans matched width only with a
   21% cap-height deficit. Narrow is used for all three projections.
3. **Source noise floor**: stroke interiors in the source contain resampling
   noise (mean ink lum ≈118 vs ≈85–92 for any clean render). Pixel-identical
   text is unreachable; sizes/positions are locked instead, and the residual
   diff is noise, not layout error.
4. **PPTX anchoring traps**: (a) `spAutoFit` must be removed or LibreOffice
   recenters text; (b) first-line ascent needs a global `DY=-1.5 px` ink
   correction; (c) font name must be exactly "Liberation Sans Narrow";
   (d) stripping `<p:style>` from autoshapes removes theme effect refs
   (audit count 35 → 0).
5. **Crop audit**: after round 12 found the crosshair icon clipped (crop too
   narrow), all non-photo crops were audited for ink touching crop borders;
   14 crops were re-measured to full ink extent.

## Verification

- PNG: mean abs diff 18.42, pct>30 7.28, pct>90 4.32; `compare_reference.py`
  mae 0.0241 (passed).
- PPTX via LibreOffice→PDF→PNG: mean 21.17, pct>30 9.18, pct>90 4.38; text
  ink x exact, y within ±1 px; all 47 raster slots exact in both renders.
- SVG (sharp): mean 20.54, pct>90 4.39.
- PPTX audit: 144 shapes / 62 text / 47 pictures, no violations, no machine
  paths, no external links, no theme effects.

## Open issues / follow-ups

- Text antialiasing differs at sub-stroke level (source noise + rasterizer
  AA); invisible at normal zoom, visible only in amplified diff maps.
- The three A-pipeline chip icons bake the top ~8 px of their titles inside
  the icon rasters (exact pixels, but those pixels are not text-editable).
- 17 PPTX font sizes result from per-element calibration; acceptable in
  exact mode but worth knowing before hand-editing the deck.
