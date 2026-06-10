# 2026-06-07 ACL Main Evidence Registry Stack-Entry Terminology Polish

## Summary

Round98 reviewed the current ACL main PDF after the Round97 ethics disclosure
polish. Page 6 still used `Embodied-data sanity` in Table 1, and the companion
image card used `Embodied sanity`. The surrounding main text had already moved
to the narrower `stack-entry` wording, so the table and image introduced a
visible terminology mismatch.

## Changes

- Rewrote the Table 1 gate label in
  `paper/shared/tables/tab_acl_evidence_gate_registry.tex` from
  `Embodied-data sanity` to `Stack entry`.
- Updated `paper/shared/figures/gen_supplement_task_media_atlases.py` so the
  evidence-gate companion card title uses `Stack entry`.
- Regenerated
  `paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png`
  from the project figure script.
- Kept the evidence, claim-supported, and forbidden-promotion cells unchanged:
  99 paired InternNav episodes, three scenes, repeated load-render checks,
  selected-stack entry, and no broad navigation robustness/speedup promotion.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round98_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round98_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round98_current/after/page-06.png`
- Regenerated companion PNG hash:
  `99b41149da111f2bb232caead897d117cbc4c1c806f0f2811e31e9a1afac177b`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round98_evidence_registry_stack_entry_terminology_polish_20260607.json`
- Final PDF hash:
  `0a167be408b2b8a2c37284372ea07d66ed954623c000b60bcb0eb016e75bfdae`

The accepted after screenshot shows `Stack entry` in both Table 1 and the
evidence-gate registry companion card. The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.03s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only visible terminology for the embodied stack-entry row
and its companion card. It did not change metrics, evidence pools, figures'
underlying evidence, citations, metadata, or supported/forbidden claim scopes.
