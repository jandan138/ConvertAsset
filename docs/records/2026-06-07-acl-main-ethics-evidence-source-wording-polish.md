# 2026-06-07 ACL Main Ethics Evidence-Source Wording Polish

## Summary

Round109 reviewed the ACL main PDF after the Round108 Figure 1 caption
claim-boundary polish. The first target was the remaining page-5
`result.    The official KuJiaLe val unseen` spacing, but three source-level
candidates made the line flow worse by introducing visible proper-noun or
common-word hyphenation. Those candidates were rejected and the page-5 source
was restored.

The accepted change is a safer page-9 Ethical Considerations wording cleanup:
the disclosure now names the evidence surfaces directly instead of using the
reader-facing production phrase `project artifacts`.

## Changes

- Rewrote one sentence in
  `paper/venues/acl27/sections/ethical-considerations.tex`.
- Final accepted wording:
  `Evidence comes from cited sources, logs, tables, and figures; no tool output is treated as evidence.`
- Removed the reader-facing phrase `project artifacts` from the main PDF.
- Kept the tool-use disclosure, evidence boundary, metrics, evidence pools,
  citations, metadata, and claim scopes unchanged.
- Restored the page-5 Stack-Entry paragraph after rejected line-flow
  candidates.

## Rejected Candidates

- Shortening the stack-entry opener to `It is not a benchmark result...`
  removed the old wide gap but introduced `Ku-` / `JiaLe`, `In-` /
  `ternNav`, and `lo-` / `cal` splits.
- Changing `benchmark result. The official...` to
  `benchmark result; the official...` introduced `benchmark re-` / `sult` and
  moved a wide gap to `scenes.       Means`.
- Marking the period space as a TeX control space with `result.\ The official`
  still produced `benchmark re-` / `sult` and the same `scenes.       Means`
  gap.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round109_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round109_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round109_current/after/page-09.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round109_ethics_evidence_source_wording_polish_20260607.json`
- Baseline PDF hash:
  `ea46134a76a8dfa7c94bf73f79da848c7b5f858d1d419b8b5234c4d2f0f1b406`
- Final PDF hash:
  `51b1866799b5224e2e9e091a69e58196e1a98234bc65e243f575b13223a62575`

The accepted after screenshot shows the page-9 disclosure reading through lines
420-424 without overlap. Page 5 is byte-identical at the rendered page and
extracted-text level to the Round109 baseline after the rejected candidates were
restored. The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.12s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed one Ethical Considerations disclosure sentence on page 9. It
does not alter measured values, evidence pools, figures, tables, citations,
metadata, or supported/forbidden claim scopes. The sentence still states that
tool output is not evidence.

## Residual Risk

The page-5 `result.    The official KuJiaLe val unseen` spacing remains
unchanged. Three Round109 source-level candidates made that region worse, so it
is now treated as a known local layout residual rather than an active target.
