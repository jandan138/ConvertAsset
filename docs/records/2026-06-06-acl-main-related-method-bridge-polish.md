# 2026-06-06 ACL Main Related/Method Bridge Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on page 3 where Related Work turns
into Method.

The fresh round-25 render showed no hard layout defect. The selected issue was
story continuity: the final Related Work paragraph correctly separated proxy
metrics from task evidence, but it could set up the Method gates more directly.

## Changes

- Rewrote the `Proxy metrics versus task evidence` paragraph in
  `paper/venues/acl27/sections/related.tex`.
- Rewrote the Method opener in `paper/venues/acl27/sections/method.tex`.
- Preserved all citations and section structure.
- Made the bridge explicit: proxy metrics answer a preservation question, while
  grounding evaluation asks a stricter evidence-contract question.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Related Work still ends on page 3.
- Method still starts on page 3.
- `Material Conversion as the Intervention` still remains on page 3.
- `Evidence Gates` still starts on page 4.
- No figure, table, page number, or section-heading placement changed
  materially.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round25_current/contact_sheet.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round25_current/page-03.png`
- Accepted page-3 render:
  `tmp/acl_main_visual_iter_20260606_round25_after/page-03.png`
- Accepted page-4 render:
  `tmp/acl_main_visual_iter_20260606_round25_after/page-04.png`
- Accepted page-3/page-4 before-after comparison:
  `tmp/acl_main_visual_iter_20260606_round25_after/pages03_04_before_after.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round25_after/contact_sheet.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round25_related_method_bridge_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=710d1aad5282b82a987b61e2fe39d7e5c63107e17efd71caf1a12c0437267fd9
pages=11
bytes=5188991
created=Sat Jun 6 11:45:57 2026 CST
```

## Verification

```bash
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
pdftotext paper/venues/acl27/build/main.pdf tmp/acl_main_visual_iter_20260606_round25_after/main.txt && rg -n "stricter question|entry gate|operationalizes that distinction" tmp/acl_main_visual_iter_20260606_round25_after/main.txt paper/venues/acl27/sections/related.tex paper/venues/acl27/sections/method.tex
```

Results: the ACL build passed with an 11-page A4 PDF, the final LaTeX blocker
scan returned no matches, and `tests/test_paper_layout.py` plus
`tests/test_acl_preupload_gate.py` passed with 102 tests. Both ACL
claim-boundary and metadata-consistency checks returned `ok`; the metadata check
still reports `abstract_word_count=169`. The extracted-PDF/source phrase scan
found the new bridge wording.

## Residual Risk

This pass is a focused page-3 main-paper story polish. It is not a
supplement-wide wording cleanup, full final-upload audit, target-policy refresh,
or citation refresh.
