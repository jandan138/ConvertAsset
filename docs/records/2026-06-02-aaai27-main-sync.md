# 2026-06-02 AAAI27 Main-Paper Sync

## Scope

The user redirected the target venue to AAAI. This pass converts the current
figure-driven ACL main-paper story into a buildable AAAI 2027 main-paper draft
and installs the official AAAI 2027 style files locally.

## What Changed

- Downloaded the official AAAI 2027 AuthorKit from
  `https://aaai.org/authorkit27/`.
- Installed `paper/venues/aaai27/aaai2027.sty` and
  `paper/venues/aaai27/aaai2027.bst`.
- Updated `paper/venues/aaai27/main.tex` to use
  `\usepackage[submission]{aaai2027}` and the current figure-driven title.
- Reworked `paper/venues/aaai27/preamble.tex` around the official AAAI package
  expectations.
- Copied the current ACL-local story sections into
  `paper/venues/aaai27/sections/`.
- Updated `paper/Makefile` and `paper/venues/aaai27/STATUS.md`.
- Added an AAAI-specific regression check in `tests/test_paper_layout.py`.
- Recorded visual/build evidence in
  `paper/shared/evidence/raw/acl27_visual_review/aaai27_main_sync_visual_review_20260602.json`.

## Current Output

The current AAAI main PDF is:

```text
paper/venues/aaai27/build/main.pdf
```

PDF profile:

- 9 pages
- letter paper
- SHA-256:
  `45befdd4648a9d524b56d4e388459822ad585152422d6081f6bff89315b53728`

The first three rendered pages were visually checked. They use the official
AAAI two-column layout and do not show the earlier large red-material fallback
artifact. Figure 1 currently starts on page 2 under the AAAI style, so a final
first-page polish pass may still be useful.

## Verification

- The AAAI-specific test failed before implementation and passed afterward with
  `1 passed, 48 deselected`.
- `make -C paper check-template-aaai27` passed.
- `make -C paper aaai27` passed.
- `python -m pytest -q tests/test_paper_layout.py` passed with `49 passed`.
- `pdftotext` found the new title and anonymous-submission marker and did not
  find the old title, old red-material caption tokens,
  `fig_vlm_grounding_cases`, or private local paths.

## Remaining AAAI Work

This is a candidate main-paper draft, not the final AAAI upload package. The
remaining AAAI-specific work is:

- Lock the exact AAAI 2027 page-limit, supplement, checklist, and disclosure
  rules when the final submission form is live.
- Flatten or package source files according to the official AuthorKit upload
  requirements.
- Run a full page-by-page AAAI visual/readability review.
- Decide whether to keep the main paper at 9 pages or compress it further after
  the official accepted page budget is confirmed.
