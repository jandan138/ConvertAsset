# 2026-06-02 ACL Supplement Review-Packet Contact Sheet

## Scope

This iteration continues the supplement visual-density goal by improving the
ending of the supplement. Before this pass, the reproducibility appendix was a
mostly text-only page that shared space with the references. That made the
supplement end feel detached from the render-heavy evidence shown earlier.

## Design

The new Figure S15 is a review-packet media manifest: a dense contact sheet
grouping tracked visual artifacts into four bands:

- render atlas;
- material diagnostics;
- VLM target views;
- navigation videos.

Image generation was used only as a non-evidence layout reference:

```text
$CODEX_HOME/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_0b1fff5087d7da8c016a1e7d83fa1081988f27e64e6131e589.png
```

The generated image was not copied into the paper and is not evidence.

## Changes

- Added `paper/shared/figures/fig_supplement_review_packet_contact_sheet.png`.
- Extended `paper/shared/figures/gen_supplement_task_media_atlases.py` with a
  review-packet contact-sheet builder.
- Registered the new figure in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/07_reproducibility.tex` so the
  reproducibility appendix opens with the visual manifest before returning to
  two-column reproducibility text.
- Added layout/provenance tests in `tests/test_paper_layout.py`.

## Visual Review

The first implementation was rejected locally because the render-atlas band was
too washed out and the contact sheet active fraction was only `0.3576`. The
accepted version uses denser render-pair and GRScenes crops for the first band.

Accepted figure stats:

- `fig_supplement_review_packet_contact_sheet.png`: `1800 x 1700`.
- Active fraction: `0.3854`.
- SHA-256: `a98e1a08bb676942222ec3214486706937d4f85c3f9d94b3bb9b327cd5ea4f98`.

Rendered page stats:

- Before audit: page 39 active fraction `0.1107`.
- After iteration: page 39 active fraction `0.1580`.

Local visual review verdict: `PASS_WITH_REMAINING_GLOBAL_ITERATION`. The contact
sheet improves the ending, but the broader goal remains active because sparse
table pages can still be inspected and polished.

## Verification

Commands:

```bash
python paper/shared/figures/gen_supplement_task_media_atlases.py
python -m pytest -q tests/test_paper_layout.py -k 'reproducibility_has_visual_media_manifest or review_packet_contact_sheet_is_registered_and_dense'
make -C paper acl27-supplement
pdftoppm -f 38 -l 41 -r 150 -png paper/venues/acl27/build/supplement.pdf tmp/acl27_supplement_contact_sheet_review/page
```

Results:

- Targeted layout tests: `2 passed, 29 deselected`.
- `make -C paper acl27-supplement`: passed.
- Output PDF: `paper/venues/acl27/build/supplement.pdf`.
- Output PDF pages: `41`.
- Output PDF SHA-256:
  `7f81bbe1fc23c4b0f0716b5ecc87d3f7378b8828e1befba33d02d1016a5114d1`.

Structured evidence:

```text
paper/shared/evidence/raw/acl27_visual_review/supplement_review_packet_contact_sheet_20260602.json
```
