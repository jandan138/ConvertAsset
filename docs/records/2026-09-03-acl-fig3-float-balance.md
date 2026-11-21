# ACL Fig.3 Float Balance And Nine-page Layout

Date: 2026-09-03

Superseded on 2026-09-04 for ARR compliance: Figure 4 was moved from the
post-Limitations float queue into the counted Results section. The nine-page
balance remains, but the current anchors are Figure 4/Discussion/Conclusion on
page 7 and Limitations/Ethical Considerations/References on page 8. See
`2026-09-04-acl-arr-figure4-counted-content.md`.

## Investigation

The apparent defect around Figure 3 was not missing image content. The active
`fig_material_effect_baseline_qualitative_v3.pdf` rendered correctly at its
existing `0.94\textwidth` size, but the late Results section queued two wide
tables and a bottom double-column figure. The default two-float top limit, a
forced `\clearpage` before Limitations, and the early Figure 4 declaration
prevented LaTeX from balancing the remaining text and floats efficiently.

Temporary builds tested top placement, a smaller Figure 3, moving the Results
float barrier, a single-column Figure 3, `cuted`/`strip`, and moving Discussion
text. Those variants either grew the paper to 11 pages, shifted the blank area,
reduced Figure 3 readability, or produced caption/line-number problems.

## Design

The accepted route keeps Figure 3 unchanged and fixes only float scheduling:

- allow up to three top double-column floats;
- set `\dbltopfraction` to `0.78`;
- remove the forced page break between Conclusion and Limitations;
- declare the Figure 4 top float after the Limitations prose.

This preserves the evidence hierarchy and caption order while giving LaTeX
enough freedom to fill pages 5--8 naturally.

## Implementation

- `paper/venues/acl27/preamble.tex` defines the reviewed double-column float
  limits.
- `paper/venues/acl27/main.tex` no longer forces a new page before Limitations.
- `paper/venues/acl27/sections/limitations.tex` keeps the v4 InternNav figure
  and caption unchanged but declares the float after the section prose.
- The OpenReview checklist and its checker now anchor Limitations to page 7.
- The pre-upload gate locks the reviewed nine-page count and the page 5--8
  marker distribution; source-level layout tests protect the scheduling rules.

## Verification

- `make -C paper clean-acl27 acl27`: pass; 9 A4 pages, PDF 1.5.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_openreview_checklist.py tests/test_acl_preupload_gate.py`:
  111 passed.
- `pdftotext -layout` confirms Figure 2 and Tables 2--3 on page 5; Tables 4--5
  and Figure 3 on page 6; Table 6, Discussion, Conclusion, and Limitations on
  page 7; and Figure 4, Ethical Considerations, and References on page 8.
- Pages 5--9 were rendered at 160 dpi and reviewed locally. No clipped text,
  incomplete panel, detached caption, overlap, or new excessive whitespace was
  found. Figure 3 remains readable and Figure 4 retains its repaired left gutter.
- The final LaTeX log contains no unresolved citation/reference or PDF-inclusion
  warning. It retains the pre-existing 2.07956 pt Table 1 overfull warning.
- `python paper/venues/acl27/scripts/run_preupload_gate.py`: pass, including 190
  focused tests, a clean rebuild, packet scans, the exact nine-page profile, and
  page-distribution checks.
- The final build and staged main PDFs are byte-identical with SHA-256
  `2ebc15136b2592e35404ef2e66536311c37fe615be0b9428713144065149b810`;
  embedded main-paper raster evidence has a minimum effective resolution of
  341 x 340 ppi.
- `make -C paper acl27-supplement`: pass; the supplement remains 45 A4 pages
  with SHA-256
  `30e333c6bee27276664ddfe2e3e2d10719f68981b1da0c4377c4dd5c25a62a0d`.

## Open Issues

- The small Table 1 overfull warning predates this layout repair and remains a
  separate typography cleanup candidate.
- Final venue routing, private author checks, approvals, and upload remain human
  decisions tracked by the existing ACL readiness workflow.
