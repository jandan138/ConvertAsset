# 2026-06-02 ACL Supplement Theory Bridge Iteration

## Scope

This iteration continues the ACL supplement visual-density goal. The specific
problem was the theory appendix: the rendered PDF had sparse text-only pages
after the navigation media section, making the supplement feel visually
unfinished despite the available render evidence.

## Root Cause

`06_theory.tex` was pure text and had an internal `\clearpage` before the last
two subsections. In the rendered PDF this produced theory pages with large blank
regions and no visual connection to the material, VLM, or navigation evidence
shown earlier.

An image-generation pass was used only as a non-evidence layout reference:

```text
$CODEX_HOME/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_0b1fff5087d7da8c016a1e750dbe588198bd1b211d531362ec.png
```

The generated image was not copied into the paper and is not scientific
evidence.

## Changes

- Added `fig_supplement_theory_evidence_bridge.png`.
- Registered the bridge in `paper/shared/figures/sources.yaml`.
- Extended `paper/shared/figures/gen_supplement_task_media_atlases.py` with a
  bridge builder that composes tracked material, VLM target-view, and navigation
  still crops.
- Updated `paper/venues/acl27/sections/supplement/06_theory.tex` to show the
  bridge with non-floating `\captionof{figure}` before returning to two-column
  theory text.
- Removed the mid-section `\clearpage` that split the theory prose into sparse
  text-only pages.
- Added regression coverage in `tests/test_paper_layout.py`.

## Visual Review

The first bridge attempt failed local visual review because it used
`contain`-style scaling and left the real figures as tiny centered panels. The
second attempt was denser but still looked like cropped title blocks. The final
version uses direct render crops from tracked material, VLM, and navigation
figures.

Rendered-page stats:

- Before audit: theory page 37 active fraction `0.0578`; page 38 active
  fraction `0.0311`.
- After iteration: page 37 active fraction `0.12399`, with the bridge visible
  on the same page as the section heading.
- The bridge image itself is `1800 x 1420`, active fraction `0.3590`, SHA-256
  `6143cbbff7c9e98345890aa0991af27c8dcc256635aba708e55260f24ece8adf`.

The accepted visual review verdict is `PASS_WITH_REMAINING_GLOBAL_ITERATION`:
this fixes the theory-section sparse-page issue, but the broader supplement
polish goal remains active.

## Verification

Commands:

```bash
python paper/shared/figures/gen_supplement_task_media_atlases.py
python -m pytest -q tests/test_paper_layout.py -k 'theory_has_visual_evidence_bridge or theory_bridge_is_registered_and_dense'
make -C paper acl27-supplement
pdftoppm -f 36 -l 38 -r 150 -png paper/venues/acl27/build/supplement.pdf tmp/acl27_supplement_theory_bridge_review/page
```

Results:

- Targeted layout tests: `2 passed, 27 deselected`.
- `make -C paper acl27-supplement`: passed.
- Output PDF: `paper/venues/acl27/build/supplement.pdf`.
- Output PDF pages: `40`.
- Output PDF SHA-256:
  `b2e2716abe0ce66b8e5f256bd9c531a53c96c1aee653362a6ed607d158169a27`.

Structured evidence:

```text
paper/shared/evidence/raw/acl27_visual_review/supplement_theory_bridge_iteration_20260602.json
```

## Residual Work

This iteration does not claim the supplement is fully polished. Remaining
candidates for future passes are sparse table pages and any pages where render
panels are still too small after full-PDF review.
