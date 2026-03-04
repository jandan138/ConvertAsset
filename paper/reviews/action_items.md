# Paper Review Action Items
## Synthesized from Content Review + Format Review
## Date: 2026-03-04

### Overall Assessment

The paper is **not ready for submission** in its current state. It has visible layout corruption (table overflows), factual data errors in the detection results, and a hardware specification mistake. The writing quality and LaTeX practices are strong, and the conceptual contribution (within-simulation rendering gap) is valuable. With 8 days until the March 12 deadline, all CRITICAL and IMPORTANT items below are achievable.

**Top 3 priorities:**
1. Fix factual errors in the detection results (data-text discrepancies that undermine credibility)
2. Fix table formatting (overflow + caption placement -- visible corruption in the PDF)
3. Correct the viewpoint naming mismatch and GPU specification error

---

### CRITICAL (Must Fix Before Submission)
Issues that would likely cause desk rejection or strong negative reviewer response.

| # | Issue | Source | File | Fix |
|---|-------|--------|------|-----|
| C1 | Detection results: paper claims 5/24 UsdPreviewSurface images with detections, raw data shows 7/24 | Content | `results.tex` (Sec 4.4, Table 4) | Recount from raw JSON; update Table 4 and body text to 7/24 |
| C2 | Detection results: mean confidence reported as 0.527, actual is 0.513 | Content | `results.tex` (Sec 4.4, Table 4) | Recompute from raw JSON; update Table 4 and text |
| C3 | Viewpoint naming mismatch: text says "top-front, top-back" but data uses "top_front_left, top_front_right" | Content | `methodology.tex:~line 52` | Change to "front, back, left, right, top-front-left, and top-front-right" |
| C4 | GPU spec error: RTX 4090 listed as 48 GB VRAM (actually 24 GB) | Content + Format | `methodology.tex:65` | Either change to "24 GB" or change GPU model to the actual card used |
| C5 | All 4 tables overflow column width (22-108pt overfull hbox) -- visible corruption in PDF | Format | `results.tex:35-52, 90-103, 125-142, 192-206` | Wrap each table in `\resizebox{\linewidth}{!}{...}` or use `\small`/`\footnotesize` + abbreviate headers |
| C6 | All 4 table captions are BELOW the table; CVPR requires ABOVE | Format | `results.tex:49,100,139,202` | Move `\caption{...}\label{...}` to immediately after `\centering`, before `\begin{tabular}` |
| C7 | Must use `\usepackage[review]{cvpr}` for submission (enables line numbers + confidential watermark) | Format | `main.tex:6` | Change `[pagenumbers]` to `[review]` |
| C8 | Figure 1 caption says "four chest-of-drawers assets" but figure only shows 2 (#0011, #0023) | Format | `results.tex:21-25` | Either regenerate figure with all 4 assets, or change caption to "two representative assets (#0011 and #0023)" |
| C9 | PSNR count error: paper says "22 of 24 pairs exceeding 30 dB", data shows 23/24 | Content | `results.tex` (Sec 4.1) | Change "22" to "23" |

### IMPORTANT (Strongly Recommended)
Issues that significantly weaken the paper but may not cause rejection at a workshop.

| # | Issue | Source | File | Fix |
|---|-------|--------|------|-----|
| I1 | Detection claim "concentrated in elevated viewpoints" is partially wrong (front-view detections exist) | Content | `results.tex` (Sec 4.4) | Revise to acknowledge front-view detections; soften the viewpoint-concentration claim |
| I2 | "Detection-neutral" claim is unsupported with only 6-9 detections and no statistical test | Content | `results.tex` + `discussion.tex` | Reframe as "preliminary observation"; suggest McNemar test if more data were available |
| I3 | No statistical significance tests for any metrics | Content | `results.tex` (all subsections) | Add paired Wilcoxon signed-rank tests or paired t-tests for PSNR/SSIM/LPIPS/CLIP/DINOv2 (n=24 pairs) |
| I4 | CLIP threshold 0.85 is below worst observed value (0.808); DINOv2 threshold 0.80 has 3 violations not discussed | Content | `discussion.tex` (Sec 5) | Either remove specific thresholds or justify them with external evidence; discuss the DINOv2 violations |
| I5 | DINOv2 std for chestofdrawers_0004: paper says 0.156, data computes to 0.171 | Content | `results.tex` Table 3 | Recompute and correct |
| I6 | "First systematic quantification" novelty claim is strong for a 4-object study | Content | `introduction.tex` | Soften to "an initial multi-level quantification" or "a systematic quantification on representative assets" |
| I7 | Scope limitations insufficiently acknowledged -- guidelines presented as general but based on 1 category | Content | `discussion.tex` | Add explicit caveat that guidelines are preliminary and derived from furniture assets only |
| I8 | Residual TODO comment in source: `% TODO: Add Figure 1 (pipeline architecture diagram)` | Format | `methodology.tex:10` | Remove the TODO comment (or add the pipeline diagram if available) |
| I9 | Figure 2 caption inaccuracy: says "left/right" but figure has 3 panels | Format | `results.tex:73-77` | Change to "PSNR (left) and SSIM (center) are higher-is-better; LPIPS (right) is lower-is-better" |
| I10 | "ConvertAsset" toolkit name may compromise double-blind if repo is public | Format | `introduction.tex:50` + throughout | If GitHub repo is public and attributable, replace with "our toolkit" during review |
| I11 | Missing details: which LPIPS backbone (VGG vs AlexNet), anti-aliasing/sample settings | Content | `methodology.tex` | Add 1-2 sentences specifying LPIPS backbone and render settings (AA, samples, denoiser) |
| I12 | Missing related work: material LOD/simplification (Wang et al.), BRDF simplification, other sim platforms | Content | `related_work.tex` | Add 1 paragraph covering material simplification literature and other simulation platforms |
| I13 | FID mentioned in related work but never used; either justify omission or remove mention | Content | `related_work.tex` | Add sentence: "We omit FID/KID due to the small sample size (n=24) which makes distributional metrics unreliable." |
| I14 | Dropped MDL features not explicitly listed (subsurface scattering, clearcoat, anisotropy, emission, opacity, displacement) | Content | `methodology.tex` (Sec 3.1) | Add 1 sentence listing which MDL features are not mapped |
| I15 | t-SNE hyperparameters (perplexity, learning rate) not reported | Content | `results.tex` or `methodology.tex` | Add parenthetical: "(perplexity=X, learning rate=Y)" |

### MINOR (Nice to Have)
Polish items if time allows before March 12 deadline.

| # | Issue | Source | File | Fix |
|---|-------|--------|------|-----|
| M1 | 6 uncited bib entries cluttering `references.bib` | Format | `references.bib` | Remove `Park2024Benchmark`, `Kolbeinsson2024DDOS`, `Alcorn2024Paved2Paradise`, `Singh2024IsSynthetic`, `Chen2024Instance`, `Caron2021Emerging` |
| M2 | Duplicate package loading (`graphicx`, `amsmath`, `amssymb`, `booktabs`) in main.tex and cvpr.sty | Format | `main.tex:8-13` | Remove duplicates from main.tex (cvpr.sty handles them) |
| M3 | Multi-line `\cite` key in introduction | Format | `introduction.tex:29-30` | Put all keys on one line |
| M4 | Figure color palette inconsistency across Figs 2-4 | Format | Figure generation scripts | Unify color scheme if regenerating figures |
| M5 | Abstract and conclusion both list all major numbers (redundant) | Content | `conclusion.tex` or abstract | Trim numbers from one location to save space |
| M6 | Performance benchmarking uses only 3 runs (10+ is more standard) | Content | N/A (experiment design) | Acknowledge in limitations; could rerun if time permits |
| M7 | Cold-start run included in mean load time -- questionable fairness | Content | `results.tex` (Sec 4.2) | Report both with and without first run, or add footnote |
| M8 | "Within-simulation gap is negligible compared to sim-to-real gap" stated without evidence | Content | `discussion.tex` | Soften to "we hypothesize" or remove the comparison |
| M9 | YOLOv8n (nano) choice not motivated; larger model might produce more detections | Content | `methodology.tex` | Add brief justification (e.g., "nano variant chosen to match edge-deployment scenario") |
| M10 | `Mittal2025Isaac` uses informal `and others` instead of full author list | Format | `references.bib` | Replace with full author list or verify output renders correctly |

---

### Section-by-Section Fix Guide

#### Abstract
- Update PSNR count if it appears here (currently says "22 of 24" -- change to "23 of 24" if present)
- Update detection mean confidence from 0.527 to 0.513 if mentioned
- Trim numbers if conclusion also lists them all (M5)

#### Introduction
- Soften "first systematic quantification" to "an initial multi-level quantification" (I6)
- Evaluate whether "ConvertAsset" name compromises double-blind (I10)
- Fix multi-line `\cite` key (M3)

#### Related Work
- Add material simplification / material LOD literature (I12)
- Add brief mention of other simulation platforms (Habitat, AI2-THOR, ThreeDWorld) (I12)
- Justify omission of FID or remove its mention (I13)

#### Methodology (Sec 3)
- Fix viewpoint names: "top-front, top-back" --> "top-front-left, top-front-right" (C3)
- Fix GPU VRAM: 48 GB --> 24 GB (or correct GPU model) (C4)
- Remove or replace TODO comment about pipeline figure (I8)
- Add LPIPS backbone specification and render settings (I11)
- List dropped MDL features explicitly (I14)
- Motivate YOLOv8n choice (M9)

#### Results (Sec 4)
- **Table 1-4:** Fix all overflows with `\resizebox` or `\small` (C5); move all captions above tables (C6)
- **Sec 4.1:** Change "22 of 24" to "23 of 24" (C9)
- **Sec 4.3, Table 3:** Fix chestofdrawers_0004 DINOv2 std from 0.156 to correct value (I5)
- **Sec 4.4, Table 4:** Fix image count 5 --> 7, mean confidence 0.527 --> 0.513 (C1, C2)
- **Sec 4.4:** Correct viewpoint-concentration claim (I1)
- **Fig 1:** Fix caption or regenerate to show all 4 assets (C8)
- **Fig 2:** Fix caption "left/right" to "left/center/right" (I9)
- Add t-SNE hyperparameters (I15)
- Add statistical significance tests (I3)

#### Discussion (Sec 5)
- Reframe detection-neutral claim as preliminary (I2)
- Fix or remove CLIP 0.85 threshold; discuss DINOv2 0.80 violations (I4)
- Add explicit caveat that guidelines are category-specific (I7)
- Soften sim-to-real gap comparison (M8)

#### Conclusion (Sec 6)
- Update any repeated numbers that are corrected above
- Consider trimming redundant number listing (M5)

#### LaTeX / Build
- Switch to `\usepackage[review]{cvpr}` (C7)
- Clean up uncited bib entries (M1)
- Remove duplicate package loads (M2)

---

### Estimated Effort

**CRITICAL fixes (C1-C9):** ~3-4 hours
- Data corrections (C1, C2, C9): 1 hour (recompute from raw JSON, update text + tables)
- Table formatting (C5, C6): 1 hour (mechanical LaTeX edits)
- Text corrections (C3, C4, C7, C8): 1 hour (straightforward text edits)

**IMPORTANT fixes (I1-I15):** ~6-8 hours
- Statistical tests (I3): 2 hours (run tests, write up results, add to tables/text)
- Threshold discussion + scope caveats (I4, I7): 1 hour
- Related work additions (I12, I13): 1.5 hours
- All other text edits (I1, I2, I5, I6, I8-I11, I14, I15): 2 hours

**MINOR fixes (M1-M10):** ~2 hours if time allows

**Total for CRITICAL + IMPORTANT: ~10-12 hours of focused work, achievable within the 8-day window.**

Recommended order: C1-C9 first (day 1-2), then I3 + I12 (day 3-4), then remaining IMPORTANT items (day 5-6), then MINOR if time allows (day 7-8).
