# 2026-06-02 ACL Supplement Material Decision Map

## Scope

This pass replaced the sparse material risk/recommender table presentation in
the ACL supplement with a render-supported decision map. It also rechecked the
user-reported Figure S4 red-material concern against the current rebuilt
supplement.

## S4 Recheck

The current supplement no longer contains the old caption:

```text
Selected VLM grounding cases ... Red material in these diagnostic cases ...
```

The rebuilt PDF uses Figure S4 as a post-repair GRScenes target-view render
panel:

```text
Figure S4: Post-repair GRScenes target-view render panel for the VLM evidence chain.
```

The legacy `fig_vlm_grounding_cases.png` still exists as historical generated
material and has a measured saturated-red fraction of `0.051321`, so it remains
unsafe as a clean qualitative showcase. The current S4 replacement figure has
red fraction `0.0`, and rendered supplement page 8 also has red fraction `0.0`.

## Material Layout Fix

The material section previously had table/prose-heavy pages after the material
claim-boundary atlas. The new Figure S11,
`fig_supplement_material_decision_map.png`, organizes the same policy into
three render-first lanes:

- covered material bins: bounded evidence claims are allowed;
- clearcoat: manual review and selected NVIDIA failure case only;
- procedural texture: limitation/investigation case unless MDL is kept or the
  procedural signal is baked before claiming preservation.

The raw risk matrix and recommender remain registered in shared evidence and
table files, but the supplement now shows the reviewer the visual basis before
the policy summary. A short trailing paragraph after Figure S11 was removed
because it created an almost blank page; its content is already carried by the
caption and the shared table registry.

## Files

- Updated `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Added `paper/shared/figures/fig_supplement_material_decision_map.png`.
- Updated `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/04_material_effects.tex`.
- Updated `tests/test_paper_layout.py`.
- Added structured evidence:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_material_decision_map_20260602.json`.

## Verification

Commands:

```bash
python paper/shared/figures/gen_supplement_task_media_atlases.py
make -C paper acl27-supplement
python -m pytest -q tests/test_paper_layout.py
pdftotext paper/venues/acl27/build/supplement.pdf - | rg -n "Post-repair GRScenes target-view render panel|Material safe-conversion decision map|Red material|Selected VLM grounding cases|registered diagnostic figure|fig_vlm_grounding_cases|/cpfs|zhuzihou|jandan138|github.com|ConvertAsset.git" -S || true
```

Results:

- `tests/test_paper_layout.py`: `40 passed in 5.80s`.
- `make -C paper acl27-supplement`: passed; output PDF has 39 pages.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `a7cb640814ab086dd5f0e3810a741367bc2f166d92d7c39151dd737541718fbb`.
- `fig_supplement_material_decision_map.png` SHA-256:
  `7c6ab95a376c34b2b6d4f9c13c2de7e12a55ef56da756214e71880e6078f6bb1`.
- Current S4 page red fraction: `0.0`.
- Figure S11 rendered page red fraction: `0.0`.
- Text scan finds the current S4 and S11 captions and does not find the old
  red-material caption, unsafe figure id, or local path leakage.

## Remaining Risk

Figure S11 is readable as a page-level decision map and is no longer scattered,
but some in-figure microcopy is small. If this supplement becomes the final
camera-ready artifact, the next polish pass should either enlarge the S11
microcopy or split it into two figure pages.
