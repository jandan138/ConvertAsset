# ACL Figure 1 Material-sphere Crop Repair

Date: 2026-09-04

## Investigation

Both metal spheres in Figure 1 had a visible horizontal cap. The PPTX image
boxes, arrows, and labels did not overlap them; the defect was already present
in `metal_source.png` and `metal_simplified.png`. The original 1024-by-1536
atlas contains eight complete, independent alpha components. Fixed four-row
slicing began the metal row at y=1152 even though both metal components begin
at y=1129, discarding 23 source pixels before padding and composition. Ceramic
components crossed their row boundary by two pixels as well.

## Design And Implementation

The source atlas and generated material appearance remain unchanged. Component
preparation now labels the full atlas at alpha greater than 12, filters
significant components, requires exactly eight, groups them into four centroid
rows, and orders each row from left to right. Each complete component is then
cropped, padded by 16 percent, and resized to the existing 512-by-512 contract.

`optics.json` now records the extraction method, global atlas bounds and
centroids, grid position, output bounds, visible fraction, and silhouette edge
widths. Generation fails when the first or last active scanline exceeds 15
percent of the maximum silhouette width, directly guarding against another
flat crop edge.

All eight component PNGs, the historical v3 Figure 1 bundle, and the active v4
PPTX/SVG/PDF/PNG bundle are regenerated. Figure geometry, labels, arrows,
evidence thumbnails, caption, and scientific semantics are unchanged.

## Verification

- The atlas yields exactly eight significant alpha components.
- Strict v3 and v4 figure-spec validation reports zero errors and warnings.
- The focused v3/v4 figure suite passes 15 tests before integrated-paper QA.
- The PPTX audit reports one slide, 73 shapes, 19 pictures, 20 text shapes, four
  font sizes, no external relationships, machine paths, nonzero theme effects,
  outer shadows, or violations.
- Local visual review confirms complete round metal and ceramic silhouettes in
  the component PNGs and standalone v4 figure.
- `make -C paper clean-acl27 acl27`: pass; the main paper remains 9 A4 pages,
  Figure 1 remains on page 2, and the minimum effective raster resolution is
  341 x 340 ppi.
- The final main log has no unresolved citation, reference, or PDF-inclusion
  warning. The pre-existing 2.07956 pt Table 1 overfull warning is unchanged.
- `python paper/venues/acl27/scripts/run_preupload_gate.py`: pass with 185
  focused tests, clean compilation, packet staging, privacy/acknowledgment
  scans, and exact PDF profile/page-order checks.
- The final build and staged main PDFs are byte-identical with SHA-256
  `057489562f928c5c3ec74a58b678e275ab4f54f64bcfbcac59815f310b16a68c`.
  The 45-page supplement SHA-256 is
  `7d9de4066e5ab5c864955a5028def0d62008a7fe4fbbc9e6b5676906c07a018b`.
- The repaired editable Figure 1 PPTX SHA-256 is
  `3aa0233b648c9fc7ff15b78a621d24c67faa3c7828f840f6d27db8950316b56b`;
  its paper PDF SHA-256 is
  `2ef8a9a82760b796251749d5cdba0ae9eac69bfa41c903f259d29d0ffc144cec`.

## Open Issues

- The spheres remain generated explanatory cues, not experimental evidence.
- Microsoft PowerPoint rendering is unavailable in this Linux environment;
  LibreOffice remains the reviewed office-rendering authority.
- Final author route and upload decisions remain outside this visual repair.
