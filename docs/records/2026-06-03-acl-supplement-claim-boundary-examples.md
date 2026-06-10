# 2026-06-03 ACL Supplement Claim-Boundary Examples

## Scope

The supplement still had a sparse overview page at the end of Appendix A. The
page contained only the "What This Supplement Does Not Prove" text block, so it
looked disconnected from the render-heavy evidence pages that follow. This pass
adds a render-first claim-boundary examples figure to that page.

## What Changed

- Added `paper/shared/figures/fig_supplement_claim_boundary_examples.png`.
- Added `build_claim_boundary_examples()` to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered the figure in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/00_overview.tex` so the
  "What This Supplement Does Not Prove" page includes the new figure.
- Added layout/source-density tests in `tests/test_paper_layout.py`.
- Recorded structured evidence in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_claim_boundary_examples_20260603.json`.

## Imagegen Role

The generated bitmap below was used only as a layout reference:

```text
/root/.codex/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_01032ee89cab32b6016a1f031415fc819ba9a0213aed5d1c50.png
```

The final paper figure is deterministic and uses tracked render images from the
proxy, VLM, material-effect, and InternNav evidence pools.

## Visual Review

The page now combines the conservative "not proved" wording with a real-render
strip showing four bounded evidence families: proxy render pairs, VLM target
boxes, material mechanism examples, and navigation media. The rendered page is
not clipped and the caption does not overlap the figure.

Residual risk: some in-figure text is still small. The figure is acceptable as
a reading guide, but a future pass could simplify the card labels further.

## Verification

- Targeted claim-boundary tests failed before implementation with `2 failed, 49
  deselected`.
- Targeted claim-boundary tests passed after implementation with `2 passed, 49
  deselected`.
- `python -m pytest -q tests/test_paper_layout.py` passed with `51 passed`.
- `make -C paper acl27-supplement` passed and produced a 42-page A4 supplement.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `19b042d78c4bd3fe1f5f9e5c95f6ffcf0b61ea21d792d8b527796a19858d4cd6`.
- `fig_supplement_claim_boundary_examples.png` SHA-256:
  `8443b3b3ab0714d22331f01b7faffb58b0f65a3c128aef1f4d38138cfe483114`.
- Page 5 active fraction at 120 dpi increased from `0.0254` to `0.130543`.
- `pdftotext` found the new Figure S2 caption and did not find the old
  red-material caption tokens, `fig_vlm_grounding_cases`, author-identifying
  tokens, or local path tokens.
