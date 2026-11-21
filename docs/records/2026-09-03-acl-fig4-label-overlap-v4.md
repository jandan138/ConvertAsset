# ACL Figure 4 Left-label Overlap Repair v4

Date: 2026-09-03

## Investigation

The active Figure 4 showed visible overlap between its left outcome labels and
the first image column. The defect was already present in the standalone source
figure and became easier to notice after paper-scale reduction, so LaTeX float
placement and caption wrapping were ruled out as causes.

The v3 generator placed each multiline label at normalized x-coordinate 0.048
without a right boundary. The first image column began at 0.145. Text such as
`both success · 1/1` exceeded that gutter and continued over the image.

A page-scale scan of the other active main visuals found no corresponding
blocking defect. Figure 1, the Table 1 companion, Figure 2, and Figure 3 remain
complete. The empty upper region on the Figure 3 page comes from LaTeX float
placement rather than missing or clipped figure content.

## Design and Implementation

`paper/shared/figures/gen_acl_internnav_rollout_v4.py` preserves all twelve
registered InternNav images, column order, trajectory colors, and evidence
semantics. It changes only layout and labels:

- outcomes use three lines: case id, outcome class, and `SR O/N` value;
- labels are right-aligned to x=0.138;
- the first image begins at x=0.150, leaving about 26 pixels at 300 dpi;
- four image columns are slightly narrowed and redistributed within the same
  7.2-by-2.75-inch canvas;
- a renderer-based preflight rejects label/image intersection, text outside
  the canvas, or axes outside normalized bounds.

The ACL wrapper now uses `fig_internnav_rollout_main_v4.pdf`. Its caption defines
O/N as original/noMDL success. The v3 bundle remains unchanged as historical
output.

## Verification

The initial v4/v3/layout/claim suite passes 109 tests. The standalone 300 dpi
render and the integrated ACL page 8 were inspected at normal and enlarged
scale. No label overlaps an image, and the legend, headers, twelve images,
caption, Limitations, Ethical Considerations, and References remain complete.

The clean main build remains 10 A4 pages, PDF 1.5. All twelve embedded Figure 4
rasters resolve at 343 ppi. No experimental result, image crop, trajectory, or
claim boundary changed. The complete pre-upload gate passes with 188 focused
ACL tests. The staged main PDF is byte-identical to the build output with
SHA-256 `da1e08e2bb0dd5f97b8696052bbc22b147a59a25a7dffe897f180d00b66b5e0b`.
The rebuilt 45-page supplement has SHA-256
`6d40ba373acc39496fae46c0fca02f59ad13aa129aed9a266ed17c4ab58f3898`.

## Open Issues

- The selected rollouts remain qualitative orientation evidence rather than a
  population rate estimate.
- Figure 3's page-level whitespace can be reconsidered separately, but changing
  float scheduling is not justified by this Figure 4 repair.
