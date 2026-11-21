# ACL/ARR Figure 4 Counted-content Compliance

Date: 2026-09-04

## Investigation

The nine-page ACL candidate was visually balanced, but Figure 4 was declared
after the Limitations prose and rendered on page 8. ARR and ACLPUB require all
main-text figures and tables to remain inside the long-paper content limit;
Limitations and Ethical Considerations cannot introduce figures, experiments,
or analysis. The previous layout therefore carried a desk-rejection risk even
though its total page count was small.

A temporary clean build tested the narrow correction: move the unchanged v4
InternNav float to the end of Results, after the official-scene table and
interpretation, while retaining the existing Results `\FloatBarrier`. It
produced the desired page order without changing any figure asset.

## Design And Implementation

- Figure 4 is now owned by the Results stack-entry subsection and is flushed
  before Discussion and Conclusion.
- Limitations contains only scope limitations; Ethical Considerations remains
  prose-only.
- The pre-upload gate rejects figure/table source in either non-counted section
  and requires Figure 4, Discussion, and Conclusion to precede Limitations.
- The reviewed layout remains nine pages: page 7 carries Table 6, Figure 4,
  Discussion, and most of Conclusion; page 8 starts with the Conclusion tail,
  then Limitations, Ethical Considerations, and References.
- OpenReview anchors and regression tests now point to Figure 4 on page 7 and
  Limitations on page 8.

## Verification

- `python -m pytest -q tests/test_acl_preupload_gate.py tests/test_paper_layout.py tests/test_acl_openreview_checklist.py tests/test_acl_internnav_rollout_v4.py tests/test_acl_paper_figures_v3.py`:
  118 passed.
- `make -C paper clean-acl27 acl27`: pass; 9 A4 pages, PDF 1.5.
- The strengthened source and PDF layout checks pass on the clean build.
- Pages 5--9 were rendered at 160 dpi and reviewed locally. Figure 4 is complete
  and readable on page 7; its label gutter remains clear. Figure 3 remains on
  page 6. No clipping, overlap, detached caption, incomplete panel, or new
  excessive whitespace was found.
- Main-paper raster evidence remains at approximately 340 ppi or higher.
- `python paper/venues/acl27/scripts/run_preupload_gate.py`: pass, including the
  new non-counted-source scan, 185 focused tests, clean rebuild, staging,
  privacy/acknowledgment scans, PDF profile, and exact page-marker checks.
- All main-PDF fonts are embedded, and the minimum effective embedded-image
  resolution is 341 x 340 ppi.
- The final build and staged main PDFs are byte-identical with SHA-256
  `7a9d73ccb9c42dcd8e2f005bdc0801baa61a195256cd0cb2a0421cfd24ce5a51`.
- `make -C paper acl27-supplement`: pass; the supplement remains 45 A4 pages
  with SHA-256
  `7f1e5c0386a1280bccd57ba251558828f2cdbb2dac1badd1b4c0092ad312de7c`.

## Open Issues

- The existing 2.07956 pt Table 1 overfull warning is unchanged and unrelated
  to this compliance repair.
- Author identity/profile, reviewer registration, route selection, disclosure
  approvals, OpenReview form copy, and final upload remain human decisions.
