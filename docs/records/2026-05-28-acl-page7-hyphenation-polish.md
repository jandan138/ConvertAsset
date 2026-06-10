# 2026-05-28 ACL Page 7 Hyphenation Polish

## Scope

This record documents a small visual-layout fix found during a full-PDF visual
review of the ACL candidate.

## Finding

Page 7 started with the fragment `nal/noMDL` because the phrase
`original/noMDL fresh-process runs` was split across the page boundary after
Table 6. This did not change any evidence, but it made a dense table page look
less polished.

## Change

`paper/venues/acl27/sections/results.tex` now says:

```text
All 18 required paired runs complete successfully in fresh processes across
original and noMDL conditions on the same three official scenes
```

The evidence and claim boundary are unchanged: the result remains an 18/18
official-scene load/render stability check, not a speedup result or broad
navigation robustness claim.

## Visual Review

Current local check:

```text
paper/venues/acl27/build/main.pdf
sha256=36b2f0fae8ead9955016466227ef9936fa0f454427577aefb48b53c523116711
pages=11
bytes=3991259
created=Thu May 28 19:33:56 2026 CST

/tmp/convertasset_acl27_page7_hyphen_final/page-06.png
sha256=cc2aa4ed487c62e21da0e97b0bcb915f09e2faa9c3991930bfc09a4b02605e8f

/tmp/convertasset_acl27_page7_hyphen_final/page-07.png
sha256=ee985d9cfbda18949177eeee4cb6b2119fd97d8c79b0e45ed1dab4785813f8b8
```

The rendered page 7 now starts with `complete successfully in fresh
processes...`, not the old `nal/noMDL`, `process official-scene`, or
`scene runs` fragments.

Durable review summary:

```text
paper/shared/evidence/raw/acl27_visual_review/page7_official_scene_hyphenation_review_20260528.json
```

## Verification

Commands run:

```bash
python -m pytest -q tests/test_paper_layout.py -k original_nomdl_phrase
make -C paper acl27
pdftotext -f 6 -l 7 -layout paper/venues/acl27/build/main.pdf -
pdftoppm -f 6 -l 7 -png -r 160 paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_page7_hyphen_final/page
```

Focused result: `1 passed, 12 deselected`.
The follow-up consolidated pre-upload gate reports `ok=true` with 91 focused
tests and a staged PDF hash matching the build PDF.
