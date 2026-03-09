# 2026-03-09 AutoFigure Methodology Pipeline Integration

## Context

This change turns a real `AutoFigure-Edit` run into the paper's official
methodology figure asset and records the later candidate comparison used to
pick the final paper-facing version.

The upstream run artifacts were provided under:

- `paper/writing/figures/final_run/`

That directory is kept as provenance and includes the full generation bundle:

- `figure.png`
- `samed.png`
- `boxlib.json`
- `template.svg`
- `optimized_template.svg`
- `final.svg`
- `icons/`

The paper itself does **not** reference those intermediate files directly.
Instead, this change promotes a selected final figure into the stable
`paper/writing/figures/` path already wired into LaTeX.

## Design Decision

The integration follows the previously established placement rule:

- keep methodology figures under `paper/writing/figures/`
- preserve the raw AutoFigure run separately
- commit only the curated final assets used by LaTeX

The source of truth for the final paper figure is now:

- `paper/writing/figures/fig_method_pipeline.svg`

This file was created from:

- `paper/writing/figures/final_run/figure.png`

and, after comparing heavier curated variants, was finalized by keeping the
original AutoFigure layout rather than retaining overlay-heavy edits.

## Candidate Comparison

Two alternate curated variants were tried in addition to the raw AutoFigure
layout:

- candidate A: minimal semantic edits aimed at preserving the original look
- candidate B: stronger terminology overlays and stage subtitles

Independent review split the outcome:

- the raw AutoFigure layout was clearly the most visually regular
- candidate B was the most semantically explicit
- candidate A underperformed on both readability and finish quality

The final paper asset therefore prioritizes visual coherence and keeps the
original AutoFigure structure. Methodology-specific precision remains anchored
in the body text and caption rather than being forced through visible overlay
patches.

## Final Selection

The final stable asset intentionally keeps the cleaner original AutoFigure
layout from `final_run/figure.png`.

This means the paper-facing figure now favors:

- better alignment and spacing consistency
- fewer visible manual repair marks
- a more believable single-pass generated appearance

while accepting that some terminology is slightly less explicit than the
overlay-heavy candidates.

## Stable Assets

The final paper assets are:

- `paper/writing/figures/fig_method_pipeline.svg`
- `paper/writing/figures/fig_method_pipeline.pdf`
- `paper/writing/figures/fig_method_pipeline.png`

The LaTeX figure reference remains:

- `paper/writing/sections/methodology.tex`

with:

- `\includegraphics[width=\textwidth]{figures/fig_method_pipeline.pdf}`
- label `fig:method_pipeline`

## Text Update

The figure caption in `paper/writing/sections/methodology.tex` remains the
paper-level explanation layer for the selected AutoFigure-derived diagram.

Specifically, the old wording about optional downstream `GLB` / evaluation
branches was removed because the finalized figure stops at the converted USD
hierarchy rather than showing those downstream branches explicitly.

## Validation

The following commands were used:

```bash
cp paper/writing/figures/final_run/figure.png \
  paper/writing/figures/fig_method_pipeline.png

python - <<'PY'
from PIL import Image
src='/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/paper/writing/figures/final_run/figure.png'
pdf='/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/paper/writing/figures/fig_method_pipeline.pdf'
with Image.open(src) as im:
    im.convert('RGB').save(pdf, 'PDF', resolution=300.0)
PY

pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Final verification was performed against:

- `paper/writing/main.pdf`

Results:

- the paper compiles successfully
- the methodology figure renders on the page without missing assets
- the final figure now comes directly from the supplied AutoFigure run rather
  than the older hand-drawn draft path
- the selected stable asset is cleaner than the heavier curated overlays tried
  during comparison
- the exported PDF now matches the unclipped original AutoFigure raster rather
  than the slightly cropped `final.svg` export

## Residual Notes

- `paper/writing/figures/final_run/` remains the archival provenance directory
  for this specific AutoFigure generation run
- the legacy script-generated methodology figure path is no longer the source
  of truth, even if some older historical files remain in the workspace
- future refinement should start from the raw AutoFigure layout and avoid dense
  overlay patches unless the whole stage is re-laid out cleanly
