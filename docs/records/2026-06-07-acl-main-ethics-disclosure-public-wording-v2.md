# 2026-06-07 ACL Main Ethics Disclosure Public Wording v2

## Summary

Round97 reviewed the current ACL main PDF after the Round96 Limitations lineflow
polish. The first candidate target was the page-5 embodied-stack opener, but
three wording attempts either kept the stretched spacing or introduced worse
linebreak hyphenation. That target was reverted.

The accepted target is page 9. The Ethical Considerations disclosure still used
internal production wording (`AI-based development and manuscript-support
tools`) and the phrase `The roadmap is explanatory, not evidence`. This round
rewrote that disclosure into public-facing tool-use and evidence-boundary prose
while preserving the References heading placement in the right column.

## Changes

- Rewrote the second paragraph of
  `paper/venues/acl27/sections/ethical-considerations.tex`.
- Replaced `AI-based development and manuscript-support tools` with
  `automated development and manuscript-support tools`.
- Replaced `The roadmap is explanatory, not evidence` with a direct
  Figure 1 boundary: the figure orients the evidence chain and does not add a
  new measurement, experiment, or claim.
- Kept the author-control, cited-source, no-tool-output-as-evidence, and
  evidence-table/log/figure boundaries intact.

## Rejected Iterations

- Page-5 target attempt 1 moved `val_unseen` but introduced `cov-` / `ers` and
  retained stretched `result. The official` spacing.
- Page-5 target attempt 2 removed `covers` but introduced `benchmark re-` /
  `sult:` and stretched spacing after `sult:`.
- Page-5 target attempt 3 removed the local defect but shifted the right column
  and introduced multiple worse hyphenations: `inter-` / `vals`, `se-` /
  `lected`, `eval-` / `uate`, and `Roll-` / `out`.
- The first ethics rewrite removed the internal wording but shortened the left
  column enough to move `References` to the left-column bottom. The accepted
  version adds a natural evidence-boundary sentence so `References` stays at the
  top of the right column.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round97_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round97_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round97_current/after/page-09.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round97_ethics_disclosure_public_wording_v2_20260607.json`
- Final PDF hash:
  `40ce1f80bf45c07c4832c7574662de6c96e8881bd3fda7324d55137b60f49b70`

The accepted after screenshot shows the Ethical Considerations disclosure in the
left column and the References heading still at the top of the right column. The
PDF-visible public wording scan no longer finds `AI-based` or `roadmap is
explanatory`.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.35s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Ethical Considerations disclosure prose on page 9. It
did not change metrics, evidence pools, figures, tables, citations, metadata,
or supported/forbidden claim scopes.
