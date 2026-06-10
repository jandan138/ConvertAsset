# 2026-06-07 ACL Main Related Page3 Stack Checks Polish

## Summary

Round104 reviewed the current ACL main PDF after the Round103 Discussion
stack-entry terminology polish. Page 3 Related Work still said
`embodied stack checks remain separate claim gates`. The phrase was bounded,
but it lagged the now-consistent main-paper wording that treats the final
navigation layer as a stack-entry/stack check rather than as a broad embodied
benchmark.

## Changes

- Rewrote the page-3 Related Work sentence in
  `paper/venues/acl27/sections/related.tex`.
- Final accepted wording:
  `Proxy match is only a first claim gate. Answer stability, point hits, frame checks, material-risk bins, and stack checks stay separate.`
- Rejected two intermediate candidates after rebuild:
  `stack-entry checks` split as `stack-` / `entry`, and
  `stack checks remain` split as `re-` / `main`.
- Kept metrics, evidence pools, figures, tables, citations, metadata, and claim
  scopes unchanged.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round104_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round104_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round104_current/after/page-03.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round104_related_page3_stack_checks_polish_20260607.json`
- Baseline PDF hash:
  `24ffc5dc1cf846a1abd061d06544e9480297fc93fa6a596e044b0ea9c77b4b35`
- Final PDF hash:
  `88fb7ee3e0addda66ba89ff140d1de57f9a0f7113736a5400a456c9c963de922`

The accepted after screenshot shows the Related Work paragraph reading
`Proxy match is only a first claim gate. Answer stability, point hits, frame
checks, material-risk bins, and stack checks stay separate.` The replacement
removes the residual `embodied stack checks` wording and wraps without the
rejected hyphenation artifacts. The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.18s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed one Related Work boundary sentence on page 3. It did not
change measured values, evidence pools, figures, tables, citations, metadata,
or supported/forbidden claim scopes.
