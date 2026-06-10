# 2026-06-04 ACL Supplement First-Page Evidence Quickstart v4

## Scope

Round 32 ranked page 1 as the next practical sparse non-reference and
non-formula page. The first-page quickstart already carried four evidence
lanes, but the lower ladder was visually small and the reader-compass slot was
less dense than the newer supplement figures.

## Changes

- Replaced the reader-compass slot with
  `paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v4_ai_slot.png`.
- Expanded the opening render ladder from six small anchors to eight anchors,
  including the extended render-scene view, VLM coordinate atlas, GRScenes VLM
  visual guide, material, navigation atlas, route stills, and case frames.
- Reworked the VLM target lane to use raw target renders with deterministic
  bounding-box overlays instead of secondary crops from the clean-rerender
  composite.
- Kept the quickstart on page 1 with a compact `920 x 1800` standalone image
  and a `0.60\textheight` include height.

## Claim Boundary

The v4 reader compass is exposition only. It is not a new evidence source, a
new metric, a VLM run, or a navigation run. The evidence-bearing content is the
registered render media reused by the deterministic composition.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_first_page_evidence_quickstart_v4_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_first_page_evidence_quickstart.png`

- Size: `920 x 1800`
- Layout-guard active238: `0.500644928`
- Layout-guard active245: `0.519396739`
- Red-pixel fraction: `0.000299517`
- SHA-256:
  `43f624153953e73ced1990915b2ca6c8396c5a6eb0ff107fe3860a25042cd675`

Reader-compass v4 slot:
`paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v4_ai_slot.png`

- Size: `1602 x 982`
- Layout-guard active238: `0.453412359`
- Layout-guard active245: `0.482971260`
- Red-pixel fraction: `0.000448141`
- SHA-256:
  `6869bb2dd07b3526f62af440616da5e5ea3359da57a106e45694e10b760d9d30`

PDF review window:
`tmp/acl_supplement_page01_quickstart_v4_compact_final_20260604/page-01.png`
and
`tmp/acl_supplement_page01_quickstart_v4_compact_final_20260604/page-02.png`

- Page 1 active245 at 90 dpi before round 32: `0.165193726`
- Page 1 active245 at 90 dpi after: `0.172578188`
- Improvement from round 32 page 1: `+0.007384462`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `0bbe611f2ebe8cf16cbbd89a78eb2c725652e333842b654c71e10f79de76a671`

Result: PASS by local `render-visual-reviewer` checklist. The quickstart and
caption remain on page 1, page 2 remains the visual roadmap, and the build does
not spill to 46 pages.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_first_page_evidence_quickstart.png`
- `paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v4_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_first_page_evidence_quickstart.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_first_page_evidence_quickstart_v4_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'first_page_evidence_quickstart'`
  - RED first for v4 caption/source/slot/height expectations; GREEN after
    implementation with `2 passed, 74 deselected`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 1 -l 2 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page01_quickstart_v4_compact_final_20260604/page`
- `pdftoppm -r 90 -png -f 1 -l 1 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page01_quickstart_v4_compact_final_90dpi_20260604/page`
