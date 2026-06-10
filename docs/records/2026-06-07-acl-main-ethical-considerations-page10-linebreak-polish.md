# 2026-06-07 ACL Main Ethical Considerations Page 10 Linebreak Polish

## Summary

Round72 reviewed the closing pages of `paper/venues/acl27/build/main.pdf`,
focusing on pages 9-11 after the Round71 table-caption polish. Page 10 shared
the final body section with the start of References. The body text in Ethical
Considerations had several distracting splits, while References should remain a
normal bibliography column rather than a body-text blocker.

## Changes

- Rewrote the Ethical Considerations risk paragraph with shorter
  reviewer-facing language for synthetic-asset risks, license terms, intended
  use, and transfer limits.
- Rewrote the AI-tool disclosure to keep author control and claim scope clear:
  the Figure 1 schematic is not evidence, tool output is not treated as
  evidence, and claims remain tied to evidence tables, logs, figures, artifacts,
  and cited sources.
- Added a local `\hyphenpenalty`, `\exhyphenpenalty`, and `\sloppy` block around
  Ethical Considerations only. This avoids repeated body end-of-line splits in
  the narrow closing column without changing global paper layout.
- Added an explicit final sentence that the disclosure records tool use and does
  not widen the empirical claim scope.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round72_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round72_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round72_after/page-10.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round72_ethical_considerations_page10_linebreak_polish_20260607.json`
- Final PDF hash:
  `fcf4f1e4363ecbac03837effacf8d3d536562572c19b4f2f4318b29e6f5a1236`

The final targeted scan found no accepted body-column end-of-line split words
inside Ethical Considerations. Remaining hyphen matches on page 10 are
reference-column bibliography breaks or the literal in-line term
`manuscript-support`. Visual inspection confirmed that Figure 4 remains stable,
Ethical Considerations fills the left column, and References starts cleanly at
the top of the right column.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed disclosure prose and local linebreaking only. It did not
change empirical results, table values, figure evidence, citations, metadata, or
supported/forbidden claim scopes. References still contain normal bibliography
hyphenation in narrow columns; this round intentionally treated only the
Ethical Considerations body as the reader-facing defect.
