# Approved ICLR system hero

Permanent editable glass-core composition promoted from the user-selected A
reconstruction. The trial bundle under `../tmp/hero_A_structured/` is unchanged.

## Rebuild

From the repository root:

```bash
python paper/venues/iclr27/scripts/figure_hero.py
```

The `render_hero(output_dir=None)` API rebuilds and exports
`paper/venues/iclr27/figures/system_hero.{svg,pptx,pdf,png}` and returns the list of
source `Path` objects for the parent build's source-hash manifest. Optional
`output_dir` selects another export directory. `source_paths()` returns inputs
without rendering.

Dependencies: Python, Pillow, NumPy, python-pptx, installed Liberation Sans/Serif,
LibreOffice (`soffice`), Ghostscript (`gs`) and Poppler (`pdftocairo`).

`build_hero.py` controls all editable text, connectors, boxes and point markers.
`hero_A_glass.layout.json` and `hero_A_glass.spec.json` record the rebuilt layout
and semantic graph. `prepare_evidence.py` can recreate the evidence copies from
repository-relative source records; ordinary figure builds verify and use the
stored copies. `measure_hub.py` is the optional glass-face typography diagnostic.
The SVG embeds its images and retains native text; the PPTX retains native text,
connectors, boxes and point markers, with independently replaceable raster assets.

## Evidence

`evidence_manifest.json` records SHA256, exact source IDs and source paths,
full-image coordinate conversion, target boxes, and map extraction rectangles.
Generated material balls and the glass device are conceptual illustrations.
Grounding observations and crossover inputs are recorded 1216×450 images.
Navigation maps are lossless right-half crops from episode 898_898 qualitative
recordings; red executed and green reference paths remain unaltered. These maps
must not be assigned primary-run quantitative scores.

Source data and saved prediction hashes are checked at build time. The prior
`overview.png` and the bundled original A reference remain protected; manuscript and compiled
paper hashes are intentionally excluded so paper integration can proceed.

## Validation on promotion

- Regenerated PNG and SVG are byte-identical to the approved trial exports.
- Regenerated native layout JSON exactly matches the approved composition.
- The 12×6-inch canvas gives 7.104-pt minimum type at 5.5-inch paper width.
- Actual serialized PPTX point positions match saved normalized predictions.
- Strict figure-spec validation: zero errors/warnings.
- Native PPTX audit: one slide, 118 shapes, 33 text shapes, 15 images,
  52 words, four font sizes, no machine paths, external links or theme effects.

The trial versions, experiments, raw images, prior overview and manuscript are
not modified by this promotion. Layout geometry checks and source integrity
results are stored in `validation.json`; native PPTX audit is retained separately.

The layout reference is retained at `assets/reference_A.png`; rebuilding does not depend on the temporary candidate directory.

## Integration refinement

The promoted layout initially reproduced the approved PNG/SVG exactly. Final paper-scale review darkened only the native `Material conversion` subtitle from muted gray to the existing ink color. Geometry, source pixels, and the selected glass composition remain unchanged; final export hashes are in `validation.json`.
