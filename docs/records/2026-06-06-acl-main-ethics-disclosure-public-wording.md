# 2026-06-06 ACL Main Ethics Disclosure Public Wording

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on page 10 where Figure 4,
Ethical Considerations, and the first References column share the final body
page.

The fresh round-22 contact sheet showed no hard crop or float displacement. The
selected issue was local: the AI-tool disclosure in Ethical Considerations still
read like a production-process note (`AI coding, writing, and image-generation
assistants` and `generated schematic`) rather than a polished responsibility and
claim-boundary disclosure.

## Changes

- Rewrote the disclosure paragraph in
  `paper/venues/acl27/sections/ethical-considerations.tex`.
- Retained the required AI-tool disclosure while replacing process-heavy wording
  with `AI-based development and manuscript-support tools`.
- Recast Figure 1 as an explanatory roadmap, not as generated evidence.
- Preserved the author-responsibility statement and the repository-artifact
  evidence check for quantitative and empirical visual claims.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 10 keeps Figure 4 at the top and the Ethical Considerations paragraph in
  the left column.
- References continue to begin in the right column without collision or visible
  displacement.
- The disclosure rewrite affects only the page-10 ethical paragraph; the figure,
  caption, references, and page count remain stable.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round22_current/contact_sheet.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round22_current/page-10.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round22_after/page-10.png`
- Accepted before/after comparison:
  `tmp/acl_main_visual_iter_20260606_round22_after/page10_before_after.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round22_after/contact_sheet.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round22_ethics_disclosure_public_wording_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=408e089cd1b848ecf423ae84c774c061a635616003e35329cc25f345787bba8f
pages=11
bytes=5189156
created=Sat Jun 6 11:22:06 2026 CST
```

## Verification

```bash
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
pdftotext paper/venues/acl27/build/main.pdf tmp/acl_main_visual_iter_20260606_round22_after/main.txt && rg -n -i "AI coding|coding, writing|image-generation|generated schematic|schematic method-chain|teaching artifact|author-produced|record-derived" tmp/acl_main_visual_iter_20260606_round22_after/main.txt paper/venues/acl27/sections/ethical-considerations.tex || true
```

Results: the ACL build passed with an 11-page A4 PDF, the final LaTeX blocker
scan returned no matches, `tests/test_paper_layout.py` passed with 85 tests, and
both ACL claim-boundary and metadata-consistency checks returned `ok`. The
targeted production-process wording scan returned no matches. The metadata check
still reports `abstract_word_count=169`.

## Residual Risk

This pass is a focused page-10 main-paper public-wording polish. It is not a
supplement-wide production-wording cleanup, full final-upload audit,
target-policy refresh, or integrity-fingerprint refresh.
