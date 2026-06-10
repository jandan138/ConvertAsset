# 2026-06-07 ACL Main Results Page4 Proxy/VLM Linebreak Polish

## Scope

Round 69 of the ACL main-paper visual/prose review polished the page-4 Results
opening around the proxy-similarity and clean-pool VLM grounding paragraphs.
The final source change is in:

- `paper/venues/acl27/sections/results.tex`

## Issue

The rendered page-4 Results opening contained a visible linebreak cluster:

- `visual- / QA`
- `nu- / meric`
- `ren- / ders`
- `co- / sine`
- `vi- / sually`

Several intermediate rewrites were rejected because they removed the original
cluster but introduced replacement splits: `QA- / clean`, `stan- / dard`,
`evi- / dence`, `screen- / ing`, `similar- / ity`, `Fig- / ure`,
`origi- / nal`, `ob- / ject`, `there- / fore`, `task- / proximal`,
`down- / stream`, `ta- / bles`, and `fi- / nal`.

## Change

The accepted Results opener keeps all evidence values unchanged while using
shorter ACL-style prose. The proxy paragraph now says the four Isaac Sim assets
stay close by proxy metrics and reports the same PSNR, SSIM, LPIPS, CLIP,
DINOv2, and 24-pair values. It then states the boundary directly: proxy match
is a gate for later task checks, not the task claim.

The clean-pool paragraph now uses `source/noMDL pairs that pass QA` and ties
claim numbers to frozen pair tables. This keeps the clean-pool role clear
without using the hyphen-heavy `visual-QA` phrase at the page break.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round69_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round69_after`
- Before PDF SHA-256:
  `60abce690523873e3a3ef86e9ff1898ff9788c715e8288cb2cc192a76d959766`
- After PDF SHA-256:
  `ab72227c64e4b8a0ecf51a4dda990640c8598cb531ff6ead788d6cf56e3fe0d5`
- After page-4 top crop:
  `tmp/acl_main_visual_iter_20260607_round69_after/page4_top.png`
- After page-4 right-middle crop:
  `tmp/acl_main_visual_iter_20260607_round69_after/page4_right_mid.png`
- After page-5 top crop:
  `tmp/acl_main_visual_iter_20260607_round69_after/page5_top.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round69_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round69_results_page4_proxy_vlm_linebreak_polish_20260607.json`

The accepted page-4 text scan has no remaining target-region hyphen splits.
Page 5 was checked for reflow; remaining splits there are inherited/non-target
items, including `expanded 30- / pair` and the Figure 3 caption's
`original- / MDL`.

## Verification

- `make -C paper acl27` exited 0.
- Log blocker scan for overfull boxes, undefined references, rerun warnings,
  multiply-defined labels, and `lineno` warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `"ok": true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `"ok": true` with a 168-word abstract.
