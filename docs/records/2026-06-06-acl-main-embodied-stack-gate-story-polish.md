# 2026-06-06 ACL Main Embodied-Stack Gate Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on page 6 and the section
4.4 transition from material-effect boundaries into embodied-data sanity and
official-scene stability.

The fresh round-20 contact sheet showed no hard crop or float displacement. The
selected issue was local: section 4.4 had the correct numbers and scope, but it
began like a result list before explaining why the official InternNav run is the
paper's final executable-stack gate.

## Changes

- Rewrote the section 4.4 opener so the official KuJiaLe
  \texttt{val\_unseen} route is introduced as the move from static evidence to
  an executable embodied stack.
- Reframed Table 6 as an infrastructure gate for official-scene load/render
  stability.
- Preserved all InternNav/DualVLN metrics, paired-run counts, table references,
  figure references, and NVIDIA official-scene claim scope.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 6 now gives section 4.4 a clearer gate-sequence role before reporting
  the 99 paired episodes.
- The new page-6 text remains inside the ACL columns and does not crowd
  Figure 3.
- The page-6/page-7 focus sheet shows no downstream displacement of Figure 3,
  Table 1, or the evidence-gate registry companion.
- The after full contact sheet shows no visible displacement of Method, Results,
  figures, tables, Ethical Considerations, or References.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round20_current/contact_sheets/main_pages_01_11_current.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round20_current/pages_180/main-06.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round20_after/pages_180/main-06.png`
- Accepted page-6/page-7 focus sheet:
  `tmp/acl_main_visual_iter_20260606_round20_after/contact_sheets/main_pages_06_07_after_focus.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round20_after/contact_sheets/main_pages_01_11_after.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round20_embodied_stack_gate_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=548538fefb899e02a03480a91d44f40e7cb89b5bdae866bb4ae4e5446b565e87
pages=11
bytes=5189937
created=Sat Jun 6 10:59:19 2026 CST
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

This pass is a focused page-6 embodied-stack gate story polish. It is not a
complete final-upload audit, target-policy refresh, or integrity-fingerprint
refresh.
