# 2026-06-06 ACL Main Proxy Gate Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on page 4 where the paper moves
from Method into Results.

The fresh round-24 render showed no hard layout defect. The selected issue was
story clarity: Section 4.1 reported proxy similarity and then stated the
boundary, but the narrative could make the gate logic sharper for ACL readers.

## Changes

- Rewrote the first paragraph of Section 4.1 in
  `paper/venues/acl27/sections/results.tex`.
- Preserved all proxy metric values: PSNR 35.52 dB, SSIM 0.990, LPIPS 0.020,
  CLIP 0.925, DINOv2 0.872, and 24 matched render pairs.
- Reframed proxy similarity as a deliberately narrow screening gate: it permits
  task-proximal checks but does not close the grounding question.
- Preserved Figure 2's evidence boundary as orientation evidence, not
  VLM-equivalence evidence.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Section 4.1 remains on page 4 and now leads more directly into Section 4.2.
- Section 4.2 still starts on page 4.
- Figure 2 remains at the top of page 5.
- Page 5 text flow and page number placement remain visually stable.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round24_current/contact_sheet.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round24_current/page-04.png`
- Accepted page-4 render:
  `tmp/acl_main_visual_iter_20260606_round24_after/page-04.png`
- Accepted page-5 render:
  `tmp/acl_main_visual_iter_20260606_round24_after/page-05.png`
- Accepted page-4/page-5 before-after comparison:
  `tmp/acl_main_visual_iter_20260606_round24_after/pages04_05_before_after.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round24_after/contact_sheet.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round24_proxy_gate_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=e9523fa1433e7ff2e1fc5613c5e992dc8375815e777406f764a82b6305157484
pages=11
bytes=5188951
created=Sat Jun 6 11:38:41 2026 CST
```

## Verification

```bash
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
pdftotext paper/venues/acl27/build/main.pdf tmp/acl_main_visual_iter_20260606_round24_after/main.txt && rg -n "The first result is deliberately narrow|This clears the screening gate|permission to run task-proximal checks" tmp/acl_main_visual_iter_20260606_round24_after/main.txt
```

Results: the ACL build passed with an 11-page A4 PDF, the final LaTeX blocker
scan returned no matches, and `tests/test_paper_layout.py` plus
`tests/test_acl_preupload_gate.py` passed with 102 tests. Both ACL
claim-boundary and metadata-consistency checks returned `ok`; the metadata check
still reports `abstract_word_count=169`. The extracted-PDF scan found the new
proxy-gate story phrases.

## Residual Risk

This pass is a focused page-4 main-paper story polish. It is not a
supplement-wide wording cleanup, full final-upload audit, target-policy refresh,
or title/metadata change.
