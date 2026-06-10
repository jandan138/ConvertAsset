# 2026-06-07 ACL Main Related Proxy Page 3 Linebreak Polish

## Summary

Round73 reviewed the full 11-page ACL main PDF after the Round72 ethics polish.
The full text scan found a real body-text cluster on page 3 in the Related Work
paragraph that bridges proxy metrics to task evidence. The paragraph was
semantically correct, but the rendered page split several words in a short span:
`use-`, `ob-`, `similar-`, `consis-`, and `abla-`.

## Changes

- Rewrote the `Proxy metrics versus task evidence` paragraph in
  `paper/venues/acl27/sections/related.tex` with shorter ACL-style sentences.
- Preserved the same claim boundary: SSIM, LPIPS, CLIP, and DINOv2 remain proxy
  checks, while answer stability, point hits, frame checks, material-risk bins,
  and embodied stack checks remain separate claim gates.
- Kept the edit local to Related Work. No tables, citations, figures, evidence
  values, or Method gate definitions were changed.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round73_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round73_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round73_after/page-03.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round73_related_proxy_page3_linebreak_polish_20260607.json`
- Final PDF hash:
  `e73eca612d34dc4bee9436565ce528e1849ea80105561f7dd92c81363726cc8a`

The after scan of pages 2-4 removed the page-3 proxy-paragraph split cluster.
Page 2 still has unrelated literal compound breaks from earlier content, and
the bibliography retains normal reference-column hyphenation.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Related Work prose and linebreak behavior. It did not
change metric values, evidence pools, figures, citations, metadata, or
supported/forbidden claim scopes.
