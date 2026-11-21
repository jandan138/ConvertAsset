# fig1-0922 exact reconstruction (rebuild)

Pixel-locked reconstruction of `../convert-from-draw.png` (1672×941), built in
`exact` mode following the build-scientific-figures skill. The same locked
layout drives three projections: PNG (PIL), SVG (native text + embedded
rasters), and PPTX (native shapes/text + named picture slots).

## Rebuild

```bash
cd paper/shared/figures/fig1-0922/rebuild
python3 build_fig.py --out rounds/roundXX/fig1.png --svg rounds/roundXX/fig1.svg --pptx rounds/roundXX/fig1.pptx
```

- `layout.py` — single source of truth: canvas, palette, 20 frames, 4 header
  bands, 4 legend swatches, 64 native text elements (ink boxes), raster order.
- `build_fig.py` — renderer. Native layer at 3× supersample → Lanczos; raster
  slots pasted 1:1 at source coordinates. Text size is calibrated per element
  through the real pipeline (3× render → downscale → ink measure with the
  source color mask) so rendered ink width matches the measured source ink
  box; ink top-left is pinned.
- `assets/` — 47 raster slots cropped from the author-owned source PNG
  (`crops.json` records each locked box). All slots diff 0.000 vs source.
- `work/font_sizes.json` — cached per-element calibration `[size3, cx, cy]`;
  delete to recalibrate.
- `rounds/` — archived iteration rounds (never overwritten).

## Key decisions

- **Font**: source type is a narrow grotesque. Liberation Sans Narrow
  (Regular/Bold) matches ink width and cap height simultaneously; plain
  Liberation Sans could match width only at ~21% short cap height.
- **PPTX text anchoring**: `spAutoFit` must be disabled
  (`MSO_AUTO_SIZE.NONE`); otherwise LibreOffice recenters text horizontally.
  Global ink offset correction `PPTX_TEXT_DY=-1.5` aligns first-line ascent
  with LibreOffice's line box. Slide size = 1672×941 px (×9525 EMU).
- **Baked vs native**: photos, icons, arrows, number circles, check/cross
  badges, the VLM chip, speech bubble, code block, map annotations and the
  `(pᵢ)` caption (U+1D62 missing from Liberation) are raster slots; every
  other label is native, editable text.
- **Source noise**: the source PNG carries resampling noise inside stroke
  interiors (mean ink lum ≈118 vs 85–92 for any clean FreeType render).
  Residual text diff is this noise floor, not a position/size error.

## Verification (round13)

| render | mean abs diff | pct>30 | pct>90 |
|---|---|---|---|
| PNG (PIL) | 18.42 | 7.28 | 4.32 |
| PPTX (LibreOffice→PDF→PNG) | 21.17 | 9.18 | 4.38 |
| SVG (sharp) | 20.54 | 9.41 | 4.39 |

- All 47 raster slots: exact (diff 0.000).
- Text ink top-left: x exact, y within ±1 px in the PPTX render.
- Non-text, non-raster chrome: mean 5.72 (PNG), 6.47 (PPTX).
- `compare_reference.py` on PNG: mae 0.0241, passed.
- PPTX audit: 1 slide, 144 shapes, 62 text shapes, 47 pictures, 17 font
  sizes, no violations, no machine paths, no external links, no theme
  effects (`fig1_rebuild.pptx.audit.json`).

## Real-evidence assets (assets/real/)

`build_real_assets.py` replaces the 15 photo slots (mock crops) with real
library evidence; `build_fig.py --assets-dir assets/real` renders the
evidence-backed figure (missing slots fall back to `assets/`):

- Panel A: paired `zoom_018` single-view renders (original/converted, 600x450).
- Panel B grounding: `two_view_category_original.png` (recorded model input);
  Swapped thumb = the real `board02.q0.side1` recording (target in right view);
  prediction dot at the recorded Qwen3-VL-2B hit (304,180); target box =
  projected bbox [230.4,89.1,369.4,372.7] from `iclr_system_hero/evidence_manifest.json`.
- Parse code block is native text with the real coordinate `[304, 180]`.
- Region probes: two_view / target_window / context_window / full conversion,
  all recorded model inputs of pair `board02.q0.side0`.
- Panel C: end views = left halves of episode 898_898 end composites; maps =
  `original_map.png` / `nomdl_map.png` (habitat-baked red/green trajectories),
  Start pill / Goal star drawn at green-path endpoints.
- `assets/real/provenance.json`: per-slot source path, crop rect, overlay
  params, SHA256.

Rounds: real_r1 (focus bug fixes) -> real_r2 (bbox-centered crops) ->
real_r3 (real side1 swap thumb, map reframing, Goal text flip) ->
real_r4 (final). Chrome drift vs round13 replica: 0.000 outside replaced
slots + code block. PPTX audit: 147 shapes / 65 text / 46 pictures,
0 violations, 0 theme effects, 0 machine paths.

## Provenance

Every raster slot is a lossless crop of the author-owned
`../convert-from-draw.png`; coordinates in `assets/crops.json`. No external
or third-party imagery is used. Reconstruction is authorized exact-mode
replication of the repository's own figure.
