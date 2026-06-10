# 2026-06-06 ACL Main Related/Method Transition Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on the page-3 transition from
Related Work into Method.

The fresh round-18 contact sheet showed no hard crop or float displacement. The
selected issue was local: the proxy-metric paragraph had the correct boundary
but still read like a diagnostic list before Method began. This pass turns that
paragraph into a story handoff.

## Changes

- Rewrote the final Related Work paragraph so proxy metrics become the first
  evidence layer rather than a standalone diagnostic list.
- Rewrote the Method opener to connect the Related Work distinction to the
  evidence-gate sequence.
- Preserved all citations, evidence gates, claim boundaries, and reported
  counts.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 3 now states the key handoff clearly: proxy metrics show pixel/feature
  closeness, while grounding systems expose a different contract.
- The Method opener now begins from that distinction and introduces the gate
  sequence without adding a new claim.
- The after full contact sheet shows no visible displacement of Method, Results,
  figures, tables, Ethical Considerations, or References.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round18_current/contact_sheets/main_pages_01_11_current.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round18_current/pages_180/main-03.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round18_after/pages_180/main-03.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round18_after/contact_sheets/main_pages_01_11_after.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round18_related_method_transition_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=89ce4ab1c6211c81a6456882405919a862e10d75e5f803f652d989dfd2b6a5a6
pages=11
bytes=5189623
created=Sat Jun 6 10:39:30 2026 CST
```

## Verification

```bash
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
```

Results: ACL build passed with an 11-page A4 PDF, the final LaTeX blocker scan
returned no matches, `tests/test_paper_layout.py` passed with 85 tests, and both
ACL claim-boundary and metadata-consistency checks returned `ok`. The metadata
check still reports `abstract_word_count=169`.

## Residual Risk

This pass is a focused page-3 Related Work to Method transition polish. It is
not a complete final-upload audit, target-policy refresh, or
integrity-fingerprint refresh.
