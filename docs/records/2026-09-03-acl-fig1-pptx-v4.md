# ACL Figure 1 PPTX-native v4

Date: 2026-09-03

Component-crop follow-up on 2026-09-04: the original atlas contained complete
metal spheres, but fixed-row extraction removed their top 23 pixels. The active
v4 bundle now uses whole-atlas connected-component extraction; see
`2026-09-04-acl-fig1-sphere-crop-repair.md`.

## Investigation

The v3 method figure had correct scientific topology and acceptable raster
assets, but its three section headers, rounded evidence cards, badges, and
vertical distribution bus made it read like a dashboard. A comparison against
image-led overview figures in recent CVPR, ICCV, and NeurIPS papers showed a
more suitable pattern: real images carry the hierarchy, while labels, arrows,
and grouping remain visually light.

The runtime probe confirmed an editable Linux workflow with `python-pptx`,
LibreOffice Impress, and Poppler. Microsoft PowerPoint automation is not
available in this environment, so the reviewed LibreOffice PDF is the paper
rendering authority.

## Design Decisions

- The v4 figure uses one continuous white canvas with no rounded cards, title
  bars, number badges, or outer panel frames.
- Four existing material-sphere pairs remain in a compact 2-by-2 rewrite area.
  The registered original/noMDL scene pair is the dominant visual element.
- Four registered evidence-thumbnail groups form an unboxed lower strip. One
  explicit distribution rail preserves the approved parallel-check topology.
- Original MDL remains blue, noMDL remains orange, and structural separators
  use neutral grey. Four font sizes cover the complete figure.
- The spheres remain explanatory rather than experimental evidence; the
  caption and provenance record preserve this boundary.

## Implementation

`paper/shared/figures/gen_acl_method_chain_v4_pptx.py` creates a one-slide,
fully editable PPTX and a self-contained SVG from shared geometry. LibreOffice
exports the slide, Ghostscript normalizes it to PDF 1.5 for pdfTeX, and
`pdftocairo` produces the 2160-by-990 PNG.
The generator measures every text string with the installed Liberation Sans
font before writing the slide and rejects text overflow, image overflow,
unexpected text/image intersections, or fewer than 6 points.

The approved graph is stored in
`paper/shared/figures/specs/fig_acl_method_chain_v4.spec.json`. The ACL
Introduction, source registry, result manifest, artifact provenance, tests, and
integrity inputs now reference the versioned v4 assets. The v3 assets remain
available as history.

## Verification

The strict semantic-spec validator reports zero errors and zero warnings. The
PPTX audit reports one slide, 73 shapes, 20 text shapes, 19 pictures, 54 words,
four font sizes, no external relationships, no machine paths, no shadows, no
nonzero theme effects, no rounded cards, and no violations.

The focused v4/v3/layout/claim suite passes 111 tests. A clean ACL build remains
10 A4 pages. Embedded Figure 1 rasters resolve at 340--346 ppi. The standalone
round trip and integrated page 2 were reviewed; no clipped title, incomplete
thumbnail, detached arrow, text overflow, missing glyph, or unintended overlap
was observed. The consolidated pre-upload gate passes with 183 focused ACL
tests. The staged main PDF is byte-identical to the build output; their SHA-256
is `9bddb9a8be94a37f537703e582f63be9ce4f57172adeb5569fff5c8b8a063774`.
The 45-page supplement SHA-256 is
`8eb007d264073a9644d8c99e4fa1911717eae4c8786020dc746965d6f49f058d`.

## Open Issues

- Evidence-strip notes sit at the approved 6-point minimum and should not be
  reduced further.
- Microsoft PowerPoint may apply small renderer-specific differences. The
  manuscript uses the reviewed LibreOffice PDF, not a live office rendering.
- Submission-route and private author-form decisions remain outside this figure
  change.
