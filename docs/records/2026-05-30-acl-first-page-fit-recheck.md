# 2026-05-30 ACL First-Page Fit Recheck

## Scope

This record refreshes the first-page ACL fit audit after the current v18
figure-forward PDF, latest reviewer-risk refresh, conclusion takeaway polish,
manual Introduction page-break removal, and final pre-upload-gate restaging.

## Findings

The current PDF first two pages were rechecked as part of the post-gate
full-PDF 150-DPI render and reviewed locally with the paper-figure visual
rubric:

```text
paper/venues/acl27/build/main.pdf
sha256=177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356
pages=11
bytes=4066770
created=Sat May 30 20:25:01 2026 CST
```

Rendered page hashes:

```text
page 1: 811e00d49062b29a37e823b0752332e92abd13a31fb6aa69ad37474dbd1be237
page 2: 980f7931c141e6ae389421da30d5196f2e96a6f28f9b1d06e3c9b1f2bab05874
```

Verdict: pass with human route caveat. Page 1 foregrounds
vision-language grounding, embodied-data reliability, and controlled material
perturbation rather than a standalone conversion-tool story. Page 2 keeps the
accepted Figure 1 imagegen v18 schematic, the four-gate paragraph, and the
contribution list readable at page scale. The contribution list now follows
Figure 1 without a manual `\newpage`, and the Related Work heading remains
visible on the same page without overlap.

No new imagegen iteration was run. The accepted v18 Figure 1 still passes this
first-page visual-fit check, and regenerating without a specific defect would
risk introducing in-image text errors.

## Changes

Updated:

- `paper/venues/acl27/FIRST_PAGE_ACL_FIT_AUDIT.md`
- `paper/shared/evidence/raw/acl27_visual_review/first_page_acl_fit_review_20260530.json`
- `paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_20260530.json`
- `docs/records/2026-05-30-acl-full-pdf-visual-recheck.md`

Manuscript source edit: removed the manual `\newpage` before the contribution
list in `paper/venues/acl27/sections/intro.tex`.

## Verification

Commands:

```bash
python -m json.tool paper/shared/evidence/raw/acl27_visual_review/first_page_acl_fit_review_20260530.json
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
git diff --check -- paper/venues/acl27/FIRST_PAGE_ACL_FIT_AUDIT.md paper/shared/evidence/raw/acl27_visual_review/first_page_acl_fit_review_20260530.json docs/records/2026-05-30-acl-first-page-fit-recheck.md docs/records/README.md
```

Results:

- JSON parse: pass;
- claim-boundary check: pass;
- metadata consistency check: pass;
- whitespace diff check: pass.

## Remaining Risk

The first-page story is ready for author review, but the submission is still not
upload-ready until the human route lock and private OpenReview author gate are
complete.
