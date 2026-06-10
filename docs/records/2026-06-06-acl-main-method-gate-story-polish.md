# 2026-06-06 ACL Main Method Gate Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on the Method 3.2 evidence-gate
transition on page 4.

The fresh round-15 contact sheet did not show a new hard crop or table cutoff.
The selected issue was local but visible: the Gate 3/Gate 4 method text still
read like a checklist, and the rendered Gate 3 line around "the NVIDIA
baseline. For the selected" had an awkward full-justified stretch.

## Changes

- Reframed Gate 3 as a selected-baseline evidence gate that links visible shifts
  to material mechanisms.
- Reframed Gate 4 as an embodied-stack entry check rather than a generic
  usability checklist.
- Removed the slash-heavy `InteriorAgent / KuJiaLe` construction from the
  rendered method paragraph while preserving the official KuJiaLe
  `val_unseen`, InternNav/DualVLN, and load/render stability evidence boundary.
- Preserved the four-gate structure, claim boundaries, evidence counts, and all
  table references.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 4 still ends with the start of Results 4.2 and does not displace the
  clean-pool table flow.
- Gate 3 no longer renders as the original stretched `baseline. For the
  selected` sentence break.
- Gate 4 reads as stack-entry evidence and avoids the worst slash-heavy
  justification from the first intermediate rewrite.
- The after full contact sheet shows no large downstream figure, table, or
  reference movement.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round15_current/contact_sheets/main_pages_01_11_current.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round15_current/pages_180/main-04.png`
- Intermediate page renders:
  - `tmp/acl_main_visual_iter_20260606_round15_after1/pages_180/main-04.png`
  - `tmp/acl_main_visual_iter_20260606_round15_after2/pages_180/main-04.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round15_after3/pages_180/main-04.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round15_after3/contact_sheets/main_pages_01_11_after3.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round15_method_gate_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=04b194cc5bbf9228623e9672576ea061667c63c3d66771b46ff1b1222c8cefbc
pages=11
bytes=5189527
created=Sat Jun 6 10:12:25 2026 CST
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

This pass is a focused Method 3.2 Gate 3/Gate 4 story and page-4 visual
iteration. It is not a complete final-upload audit, broad full-PDF completion
proof, or integrity-fingerprint refresh.
