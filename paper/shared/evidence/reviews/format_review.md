# Format Review: MDL-to-UsdPreviewSurface Material Simplification Paper
## Editor: Simulated CVPR Format Check

---

### 1. CVPR Template Compliance

**Page count:** 8 pages total (body text ends on page 7 with the conclusion; pages 7--8 are references). This is within the CVPR limit of 8 body pages with references excluded from the count. However, the body text actually overflows slightly onto page 7 where references begin. **Verdict: borderline -- body content ends mid-page-7, references start on page 7 and continue to page 8. Compliant.**

**Margins, column width, font sizes:**
- `\documentclass[10pt,twocolumn,letterpaper]{article}` -- correct.
- cvpr.sty sets `\textheight{8.875in}`, `\textwidth{6.875in}`, `\columnsep{0.3125in}` -- standard CVPR dimensions.
- Times font loaded via cvpr.sty -- correct.

**Double-blind compliance:**
- `main.tex:17`: `\def\cvprPaperID{****}` -- correct placeholder.
- `main.tex:25-26`: Author block reads "Anonymous CVPR 2026 Submission / Paper ID \cvprPaperID" -- **compliant**.
- No self-identifying author names, affiliations, or acknowledgments found.
- **Issue:** `main.tex:50` -- the toolkit name "ConvertAsset" is used throughout, and `introduction.tex:50` explicitly says "We release **ConvertAsset**". If the tool's GitHub repo is public and attributable, this could compromise double-blind review. **Recommendation:** Consider using a neutral placeholder name (e.g., "our toolkit") during review, or ensure the repo is not publicly linked to authors.

**Style option:** `\usepackage[pagenumbers]{cvpr}` -- The `pagenumbers` option enables page numbers but does not set review mode. For submission, this should likely be `\usepackage[review]{cvpr}` to enable line numbering and the confidential review watermark. **Severity: HIGH for submission.**

---

### 2. Abstract

**Word count:** ~154 words (target: 150--250). **Compliant**, though on the lower end.

**Structure check:**
- Problem statement: Present (MDL materials limit interoperability). **OK.**
- Method: Present (first systematic evaluation across four dimensions). **OK.**
- Results: Present (PSNR, SSIM, LPIPS, CLIP, detection-neutral). **OK.**
- Conclusion/implication: Present (release toolkit, provide guidelines). **OK.**

**Issues:**
- `main.tex:41`: "PSNR 35.52\,dB" -- The `\,` thin space before "dB" is good.
- The abstract is well-structured and self-contained.
- No issues found.

---

### 3. Figures

#### Figure 1: Matched Rendering Pairs (`fig_render_pairs`)
- **Placement:** `[t]` float spec -- correct (top of page). Appears on page 4.
- **Caption quality:** Self-contained, describes top/bottom row layout. **OK.**
- **Caption accuracy vs. actual figure:** The caption says "Top row: original MDL materials. Bottom row: converted UsdPreviewSurface materials." The actual figure shows a 2x2 grid with rows labeled #0011 and #0023, and columns labeled MDL and UsdPreviewSurface. **The caption says "four chest-of-drawers assets" but the figure only shows 2 of the 4 assets (#0011 and #0023; missing #0004 and #0029).** **Severity: HIGH -- caption/figure mismatch.**
- **Label readability:** Row/column headers in the PDF are large and clear.
- **Resolution:** Vector PDF, sharp at all zoom levels. **OK.**
- **Width:** `\linewidth` (single column) -- appropriate.
- **Overfull hbox:** The build log reports an overfull `\hbox` of 80.43pt at `results.tex` lines 37--50. This is the table immediately below the figure. **See Table 1 below.**

#### Figure 2: Per-Viewpoint Image Quality Metrics (`fig_image_quality`)
- **Placement:** `[t]` float spec -- correct.
- **Caption quality:** Self-contained, explains axes and identifies the outlier scene. **OK.**
- **Caption accuracy:** Caption says "PSNR and SSIM (higher is better) are shown on the left; LPIPS (lower is better) on the right." The actual figure shows three side-by-side bar charts (PSNR, SSIM, LPIPS), not a left/right split. **Minor caption inaccuracy** -- should say "left panel", "center panel", and "right panel" or similar.
- **Label readability:** Axis labels are readable. Tick labels are small but legible.
- **Resolution:** Vector PDF. **OK.**
- **Width:** `\linewidth` (single column). The figure's native aspect ratio is very wide (493pt x 168pt), and at column width it becomes quite short. Still readable.

#### Figure 3: Feature-Level Cosine Similarity (`fig_feature_similarity`)
- **Placement:** `[t]` -- correct.
- **Caption quality:** Self-contained. **OK.**
- **Label readability:** Legend text is legible. Axis labels clear.
- **Resolution:** Vector PDF. **OK.**
- **Width:** `\linewidth` (single column) -- appropriate.

#### Figure 4: t-SNE DINOv2 Embeddings (`fig_tsne_dino`)
- **Placement:** `[t]` -- correct.
- **Caption quality:** Self-contained, explains the 48-image composition and the clustering finding. **OK.**
- **Label readability:** Legend text is legible. Marker shapes (circle, square, triangle, diamond) provide redundant coding for scene identity beyond color -- **good for color accessibility**.
- **Resolution:** Vector PDF. **OK.**
- **Width:** `\linewidth` (single column) -- appropriate.
- **Color accessibility:** Both Figures 3 and 4 use blue/gold color scheme with shape markers. Distinguishable in grayscale. **OK.**

**General figure issues:**
- All figures use `[t]` placement -- consistent and correct.
- All captions are below figures -- correct per CVPR convention.
- No figure spans both columns (`figure*`), which is fine for this paper.

---

### 4. Tables

#### Table 1: Image Quality Metrics (`tab:image_quality`)
- **Booktabs:** Uses `\toprule`, `\midrule`, `\bottomrule` -- **correct**.
- **Alignment:** `{lccc}` -- scene names left-aligned, metrics centered. **OK.**
- **Caption placement:** Caption is BELOW the table (`\caption` after `\end{tabular}`). **CVPR convention requires captions ABOVE tables.** **Severity: MEDIUM -- fix for all 4 tables.**
- **Number formatting:** Consistent `mean \pm std` format. **OK.**
- **Overfull hbox:** Build log reports 80.43pt overfull at lines 37--50. Examining the PDF (page 4), the table and Table 3 are rendered overlapping/misaligned. The table is too wide for a single column. **Severity: HIGH -- table overflows column width.**
- **Fix:** Add `\small` or `\footnotesize` before `\begin{tabular}`, or use `\resizebox{\linewidth}{!}{...}`, or abbreviate column headers.

#### Table 2: Rendering Performance (`tab:performance`)
- **Booktabs:** Correct.
- **Alignment:** `{lccc}` -- **OK.**
- **Caption placement:** BELOW table. **Same issue -- move above.**
- **Overfull hbox:** Build log reports 107.81pt overfull at lines 92--101. This is the worst overflow in the paper. The "GPU Memory (MB)" and "FPS" columns push the table far beyond column width. **Clearly visible in the PDF on page 4 -- the FPS column is cut off at the right margin.**
- **Fix:** Shorten column headers (e.g., "Load (s)", "GPU Mem (MB)", "FPS") and/or reduce font size.

#### Table 3: Feature-Level Similarity (`tab:feature_sim`)
- **Booktabs:** Correct.
- **Alignment:** `{lcc}` -- **OK.**
- **Caption placement:** BELOW table. **Move above.**
- **Overfull hbox:** 22.84pt overfull at lines 127--140. Minor overflow but still visible in the PDF -- the table overlaps with Table 2 on page 4.

#### Table 4: Detection Results (`tab:detection`)
- **Booktabs:** Correct.
- **Alignment:** `{lccc}` -- **OK.**
- **Caption placement:** BELOW table. **Move above.**
- **Overfull hbox:** 54.70pt overfull at lines 194--204.
- **Number formatting:** Detection counts are integers, confidence is 3 decimal places. Consistent.

**Summary of table issues:**
1. **All four table captions are below the table; CVPR requires above.** Move `\caption{...}\label{...}` before `\begin{tabular}`.
2. **All four tables overflow column width.** Tables 1--4 produce overfull hbox warnings ranging from 22.8pt to 107.8pt. This is visible in the compiled PDF.

---

### 5. References

**Format consistency:**
- All 16 cited entries use the `ieeenat_fullname` bibliography style. Formatting appears consistent.
- Journal/conference names are properly italicized in the compiled output.

**Missing fields:**
- `Mittal2025Isaac`: Uses `author = {Mayank Mittal and others}`. The `and others` is informal; BibTeX/natbib will not render this as "et al." correctly. Should use the full author list or `and others` should be verified to produce proper output. In the compiled PDF (page 8, ref [6]), it renders as "Mayank Mittal et al." -- **acceptable but unconventional**.

**Uncited entries (6 of 22 bib entries are never cited):**
- `Park2024Benchmark`
- `Kolbeinsson2024DDOS`
- `Alcorn2024Paved2Paradise`
- `Singh2024IsSynthetic`
- `Chen2024Instance`
- `Caron2021Emerging`

These entries are in `references.bib` but never `\cite`-d. They do not appear in the compiled PDF (BibTeX only includes cited entries), so this is not a formatting error, but the bib file should be cleaned up.

**note field cleanup:**
- Several entries have `note` fields containing `\url{...}` and descriptive text (e.g., "Introduces LPIPS.", "Published at SynData4CV Workshop, CVPR 2025.", "Version 8.0.0"). These are rendered in the bibliography output. For CVPR camera-ready, URLs in the `note` field are acceptable but some style guides prefer them only when no DOI is available.
- `Jocher2023YOLO` uses `@misc` with `howpublished = {\url{...}}` -- this is the correct pattern for software references.

**URL formatting:**
- All URLs use `\url{...}` -- correct. The `url` package (loaded by cvpr.sty) handles line breaking.
- In the compiled PDF, URLs are rendered in cyan/teal monospace and break across lines correctly.

---

### 6. Build Warnings

All warnings from `main.log`:

| # | Warning | File:Lines | Severity | Description |
|---|---------|-----------|----------|-------------|
| 1 | Overfull `\hbox` (80.43pt) | `results.tex:37--50` | **HIGH** | Table 1 (image quality) overflows column |
| 2 | Overfull `\hbox` (107.81pt) | `results.tex:92--101` | **HIGH** | Table 2 (performance) overflows column -- worst offender |
| 3 | Overfull `\hbox` (22.84pt) | `results.tex:127--140` | **MEDIUM** | Table 3 (feature similarity) slight overflow |
| 4 | Overfull `\hbox` (54.70pt) | `results.tex:194--204` | **HIGH** | Table 4 (detection) overflows column |

No underfull box warnings. No undefined reference warnings. No missing citation warnings. The `silence` package in cvpr.sty suppresses some font-related warnings.

**Note:** The cvpr.sty file sets `\hbadness=10000` and `\hfuzz=30pt`, which suppresses many overfull/underfull warnings. Only overflows exceeding 30pt are reported. The actual number of overflowing elements may be higher.

---

### 7. Writing Style

**Grammar/spelling:**
- No spelling errors detected in the body text.
- Consistent American English spelling throughout.

**Passive voice:**
- The paper uses a good mix of active ("We present", "We evaluate", "We release") and passive voice. Not excessive.

**Terminology consistency:**
- "UsdPreviewSurface" is used consistently (not "USD Preview Surface" or other variants). **OK.**
- "MDL" is always expanded on first use ("Material Definition Language") in the abstract and introduction. **OK.**
- "chest-of-drawers" is hyphenated consistently. **OK.**
- "sim-to-real" is hyphenated consistently. **OK.**
- "zero-shot" is hyphenated consistently. **OK.**
- Minor: "glTF" vs "GLB" -- both are used appropriately (glTF is the format family, GLB is the binary container). **OK.**

**Sentence length:**
- Generally well-controlled. A few long sentences in the methodology section but nothing excessive.

**Specific issues:**
- `introduction.tex:29-30`: "The sim-to-real gap literature focuses on the boundary between simulated and real images~\cite{Tobin2017Domain, Tremblay2018Training,Zakharov2022Photo}" -- there is a line break inside the `\cite` command between `Tobin2017Domain,` and `Tremblay2018Training`. While LaTeX handles this correctly, it is better practice to keep multi-key citations on one line or ensure no space after the line break.
- `discussion.tex:69`: "image--text retrieval" uses an em-dash; should be an en-dash for compound adjectives: "image--text" is correct (en-dash in LaTeX is `--`). **OK.**

---

### 8. LaTeX Best Practices

**Non-breaking spaces before `\cite` and `\ref`:**
- All `\cite` calls are preceded by `~` (non-breaking space). **Excellent -- fully compliant.**
- All `\ref` calls are preceded by `~`. **Excellent.**
- Example: `Figure~\ref{fig:render_pairs}`, `Table~\ref{tab:image_quality}`, `Section~\ref{sec:pixel_quality}`.

**Thin spaces (`\,`):**
- Used correctly before units: `35.52\,dB`, `1024 \times 1024`, `0.508 \pm 0.024\,s`.
- `methodology.tex:65`: "RTX 4090 (48\,GB VRAM)" -- consistent.

**Math mode usage:**
- All mathematical expressions are properly in math mode.
- `$\pm$` used consistently in tables for standard deviations.
- `$\uparrow$` and `$\downarrow$` used in table headers for metric direction indicators.
- `$[0,1]$` interval notation is in math mode. **OK.**
- `$4 \times 6 \times 2 = 48$` -- correct. **OK.**

**Underscore escaping:**
- All underscores in text mode are within `\texttt{...}` blocks (e.g., `\texttt{chestofdrawers\_0004}`), where `\_` is properly escaped. **OK.**
- Table body uses `chestofdrawers\_0004` etc. directly in text mode within tables -- since these are escaped, **OK**.

**Other LaTeX issues:**
- `main.tex:6`: `\usepackage[pagenumbers]{cvpr}` -- packages `graphicx`, `amsmath`, `amssymb`, `booktabs` are loaded both in `main.tex` and inside `cvpr.sty`. LaTeX silently ignores duplicate `\usepackage` calls for these packages, but it is slightly messy. **Low priority.**
- `main.tex:14`: Comment says "cleveref is loaded by cvpr.sty with [capitalize]" -- correct, no duplicate load.

---

### 9. Specific Fixes (file:line format)

#### CRITICAL (must fix before submission)

1. **`main.tex:6` -- Switch to review mode for submission**
   - Current: `\usepackage[pagenumbers]{cvpr}`
   - Fix: `\usepackage[review]{cvpr}` (enables line numbering, confidential watermark, and page numbers)

2. **`results.tex:35-52` -- Table 1 overflows column (80pt)**
   - Fix: Wrap table content in `\resizebox{\linewidth}{!}{...}` or add `\small` before `\begin{tabular}`
   - Move `\caption` and `\label` ABOVE `\begin{tabular}` (CVPR convention)

3. **`results.tex:90-103` -- Table 2 overflows column (108pt, worst)**
   - Fix: Shorten headers: "Load (s)" instead of "Load Time (s)", "GPU Mem. (MB)" instead of "GPU Memory (MB)"
   - Alternatively: `\resizebox{\linewidth}{!}{...}`
   - Move `\caption` and `\label` ABOVE `\begin{tabular}`

4. **`results.tex:125-142` -- Table 3 overflows column (23pt)**
   - Fix: Use `\small` or abbreviate "cos sim" to "cos." in headers
   - Move `\caption` and `\label` ABOVE `\begin{tabular}`

5. **`results.tex:192-206` -- Table 4 overflows column (55pt)**
   - Fix: `\resizebox{\linewidth}{!}{...}` or `\small`
   - Move `\caption` and `\label` ABOVE `\begin{tabular}`

6. **`results.tex:21-25` -- Figure 1 caption/content mismatch**
   - Caption says "four chest-of-drawers assets" but figure only shows 2 (scenes #0011 and #0023; missing #0004 and #0029).
   - Fix: Either regenerate the figure to include all 4 assets, or update the caption to say "two representative chest-of-drawers assets (#0011 and #0023)".

#### HIGH PRIORITY

7. **`results.tex:49,100,139,202` -- All table captions below tables**
   - CVPR convention: table captions go ABOVE the table, figure captions go BELOW the figure.
   - For each table environment, move `\caption{...}\label{...}` to immediately after `\centering` and before `\begin{tabular}`.
   - Example fix for Table 1:
     ```latex
     \begin{table}[t]
     \centering
     \caption{Pixel-level image quality metrics ...}
     \label{tab:image_quality}
     \begin{tabular}{lccc}
     ...
     ```

8. **`methodology.tex:10` -- Residual TODO comment**
   - `% TODO: Add Figure 1 (pipeline architecture diagram) here once created.`
   - Either add the pipeline figure or remove the TODO before submission. Reviewers may see comments in source if submitted.

#### MEDIUM PRIORITY

9. **`results.tex:73-77` -- Figure 2 caption inaccuracy**
   - Caption says "PSNR and SSIM (higher is better) are shown on the left; LPIPS (lower is better) on the right."
   - The figure has three panels (left: PSNR, center: SSIM, right: LPIPS).
   - Fix: "PSNR (left) and SSIM (center) are higher-is-better; LPIPS (right) is lower-is-better."

10. **`references.bib` -- 6 uncited entries**
    - `Park2024Benchmark`, `Kolbeinsson2024DDOS`, `Alcorn2024Paved2Paradise`, `Singh2024IsSynthetic`, `Chen2024Instance`, `Caron2021Emerging` are defined but never cited.
    - These do not appear in the compiled PDF, but the bib file should be cleaned up to avoid confusion.

11. **`methodology.tex:65` -- Hardware description inconsistency**
    - States "NVIDIA GeForce RTX 4090 (48\,GB VRAM)" -- the RTX 4090 has 24 GB VRAM, not 48 GB. The 48 GB variant is the RTX 6000 Ada Generation or L40. **Verify and correct the GPU model or VRAM amount.**

#### LOW PRIORITY

12. **`main.tex:8-13` -- Duplicate package loading**
    - `graphicx`, `amsmath`, `amssymb`, `booktabs` are loaded by both `main.tex` and `cvpr.sty`. LaTeX handles this silently, but removing the duplicates from `main.tex` would be cleaner.

13. **`introduction.tex:29-30` -- Multi-line cite key**
    - `\cite{Tobin2017Domain,\n Tremblay2018Training,Zakharov2022Photo}` has a line break and leading spaces inside the cite. Works correctly but is slightly fragile. Keep on one line.

14. **Figure color palette consistency**
    - Figures 2, 3, and 4 use different color palettes (blue/green/orange bar charts vs. blue/gold grouped bars vs. blue/gold scatter). Consider unifying the color scheme across all figures for visual coherence.

---

### Summary

| Category | Issues Found | Critical | High | Medium | Low |
|----------|-------------|----------|------|--------|-----|
| Template compliance | 2 | 1 | 0 | 0 | 0 |
| Abstract | 0 | 0 | 0 | 0 | 0 |
| Figures | 2 | 1 | 0 | 1 | 1 |
| Tables | 5 | 4 | 1 | 0 | 0 |
| References | 2 | 0 | 0 | 2 | 0 |
| Build warnings | 4 | 3 | 0 | 1 | 0 |
| Writing style | 0 | 0 | 0 | 0 | 0 |
| LaTeX practices | 2 | 0 | 1 | 0 | 1 |
| **Total** | **17** | **9** | **2** | **4** | **2** |

**Top 3 action items:**
1. Fix all four table overflows (resize or abbreviate headers) -- visible corruption in compiled PDF.
2. Move all table captions above the tables per CVPR convention.
3. Fix Figure 1 caption/content mismatch (claims 4 assets, shows 2).

**Overall assessment:** The paper is well-written with good LaTeX practices (non-breaking spaces, proper booktabs, thin spaces for units). The main formatting issues are: (a) table overflow causing visible layout corruption in the PDF, (b) table captions in the wrong position, and (c) a figure-caption discrepancy. All are straightforward to fix. The writing quality is high with consistent terminology and minimal stylistic issues.
