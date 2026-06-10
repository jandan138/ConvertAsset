# 2026-06-07 ACL Main Page 8 Table Caption Linebreak Polish

## Summary

Round71 reviewed pages 6-11 of `paper/venues/acl27/build/main.pdf` after the
Round70 build and accepted one page-8 caption polish cluster. The rendered page
showed four distracting table-caption word splits across Tables 2, 3, 4, and 6:
`preser-`, `origi-`, `guaran-`, and `conver-`.

## Changes

- Compacted the Table 2 clean-pool caption while preserving the 15-pair control
  boundary below the 20-pair benchmark gate.
- Compacted the Table 3 frozen stress-set caption and replaced the
  linebreak-prone `point-in-bbox` phrase with point-hit wording.
- Compacted the Table 4 paired-CI caption while keeping the descriptive,
  non-population claim boundary.
- Compacted the Table 6 official-scene caption while keeping the NVIDIA row
  gated on matching converted scenes that pass smoke gates.
- Synced generated caption strings in the VLM stress, reviewer-closure, and
  official-scene package generators. The official-scene generator now emits a
  matching `table*` begin/end pair for the performance-summary table.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round71_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round71_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round71_after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round71_page8_table_caption_linebreak_polish_20260607.json`
- Final PDF hash:
  `3a9ce97bfb4ff02f9fabb55af5b20aca9e171e15c00c3bb5d6841c03ef23ea7e`

After rebuild, the targeted pages 7-9 had no text-extracted end-of-line hyphen
matches. Visual inspection confirmed that the table page remained stable and no
caption/table overlap was introduced.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed caption wording only. It did not change table values, labels,
evidence pool definitions, or supported/forbidden claim scopes. Pages 10-11
still contain normal bibliography hyphenation from narrow reference columns; the
round did not treat reference formatting as a body-text blocker.
