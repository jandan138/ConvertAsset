# 2026-06-05 ACL Main Related/Method Transition Polish

## Scope

Continued the ACL main-paper visual and prose iteration for
`paper/venues/acl27/build/main.pdf`. This pass focused on the page-3/page-4
transition from Related Work into Method, where the earlier render placed the
Method heading low in the right column and made the first method subsection feel
compressed.

## Changes

- Tightened `Related Work` so it spends fewer lines recapping adjacent
  benchmarks and more directly frames the measurement-reliability gap.
- Added a short Method framing paragraph that separates the conversion
  intervention from the evidence gates allowed to support downstream claims.
- Rewrote the Method gate descriptions as `Gate 1` through `Gate 4` for a
  cleaner ACL-style protocol narrative.
- Preserved the claim boundaries: the edit does not expand any material-effect,
  VLM, or navigation robustness claim.

## Visual Evidence

Before render:

- `tmp/acl_main_visual_iter_20260605_round7_related_method_before/contact_sheets/main_pages_03_04_09_10_before.png`
- `tmp/acl_main_visual_iter_20260605_round7_related_method_before/pages_180/page-03.png`
- `tmp/acl_main_visual_iter_20260605_round7_related_method_before/pages_180/page-04.png`

Final render:

- `tmp/acl_main_visual_iter_20260605_round7_related_method_after/contact_sheets/main_pages_03_04_09_10_after.png`
- `tmp/acl_main_visual_iter_20260605_round7_related_method_after/contact_sheets/main_pages_01_11_after.png`
- `tmp/acl_main_visual_iter_20260605_round7_related_method_after/pages_180/page-03.png`
- `tmp/acl_main_visual_iter_20260605_round7_related_method_after/pages_180/page-04.png`
- `tmp/acl_main_visual_iter_20260605_round7_related_method_after/pages_180/page-09.png`
- `tmp/acl_main_visual_iter_20260605_round7_related_method_after/pages_180/page-10.png`

Visual result: page 3 now introduces Method with a brief framing paragraph and
3.1 content in the right column rather than dropping straight into a squeezed
subsection. Page 4 still carries the remaining Evidence Gates, Claim Registry,
and Results opening without a float collision. Page 10 still keeps Figure 4,
caption, Ethical Considerations, and References separated.

## Verification

- `make -C paper acl27` passed and produced an 11-page A4 PDF.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.
- `python -m pytest -q tests/test_paper_layout.py -k 'acl_method_avoids_narrow_column_monospace_evidence_path or acl_main_forces_results_floats_before_discussion or acl_results_avoids_page_break_prone_original_nomdl_phrase or acl_intro_uses_latest_low_text_method_chain_schematic'`
  passed: 4 passed, 81 deselected.
- LaTeX log scan for overfull boxes, float sizing warnings, undefined
  references, rerun warnings, label warnings, and lineno warnings returned no
  matches.

Final PDF:

- Path: `paper/venues/acl27/build/main.pdf`
- Pages: 11
- Size: 5,194,349 bytes
- SHA-256:
  `20ac19cc7fd2559727f4f292c2f072dedd506afdcd5dd767d25467a2f0e1a8d4`

## Residual Risk

The paper remains under active iterative polish. Page 9 still starts Conclusion
near the lower part of the left column, but the final render shows enough body
text before the page turn and page 10 remains collision-free. Future passes can
continue with global cadence and late-page balancing rather than treating this
transition as a blocker.
