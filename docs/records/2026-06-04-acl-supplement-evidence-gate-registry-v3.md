# 2026-06-04 ACL Supplement Evidence-Gate Registry V3

## Scope

Round 27 ranked page 3 as the lowest-density non-reference, non-formula page
that had not just been revisited. This pass updates the evidence-gate registry
companion under Table S1 so the page reads less like a sparse table page and
more like the opening claim-boundary map.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_evidence_gate_reader_v3_ai_slot.png`.
- Rebuilt `fig_supplement_evidence_gate_registry_companion.png` from
  `1800 x 1160` to `1800 x 1240`.
- Replaced the sparse v2 reader-gate slot with a denser v3 gate schematic.
- Enlarged the registered cross-evidence render strip, preserving proxy,
  GRScenes VLM, material, and InternNav evidence anchors.
- Increased Table S1's companion allocation from `0.40\textheight` to
  `0.50\textheight`.
- Updated source registration, AI-slot manifest provenance, caption wording,
  and layout tests to require the v3 slot and denser companion.

## Claim Boundary

The v3 AI-generated reader-gate schematic is exposition only. It is not a new
experiment, metric, VLM run, navigation run, benchmark row, or evidence source.
The evidence-bearing content remains the registered proxy, GRScenes VLM,
material-effect, and InternNav render crops composed by deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_evidence_gate_registry_companion_v3_20260604.json`

Generated v3 slot:
`paper/shared/figures/ai_slots/fig_supplement_evidence_gate_reader_v3_ai_slot.png`

- Size: `1672 x 941`
- Layout-guard active238: `0.224063020`
- Layout-guard active245: `0.237228541`
- Red-pixel fraction: `0.002965007`
- SHA-256:
  `20c064b30b0b433c4c9eb403621ff895dc4c330515766035261a206d28bb5b86`

Standalone figure:
`paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png`

- Size: `1800 x 1160` -> `1800 x 1240`
- Standalone layout-guard active238: `0.391122126` -> `0.461080197`
- Standalone layout-guard active245: `0.401445402` -> `0.472991935`
- Red-pixel fraction: `0.000287634`
- SHA-256:
  `911601c8483a21d9c1692819881ab35e368192b806c92712b8474f8a824e41f2`

PDF review window:
`tmp/acl_supplement_page03_evidence_gate_registry_v3_final_20260604/page-02.png`
through `tmp/acl_supplement_page03_evidence_gate_registry_v3_final_20260604/page-04.png`

- Page 3 active245 at 90 dpi before round 27: `0.156829002`
- Page 3 active245 at 90 dpi after: `0.194022830`
- Improvement from round 27 page 3: `+0.037193828`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `918241613327bf06b6377d29b7bb72467a69c2ea397d8ebdd9fbc522f3f6b531`

Result: PASS by local `render-visual-reviewer` checklist. Page 3 remains a
table page, but the companion now carries the visual center of gravity, the
render strip is inspectable at page scale, and neighboring pages 2 and 4 remain
intact.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_evidence_gate_reader_v3_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_evidence_gate_registry_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/shared/tables/tab_acl_evidence_gate_registry.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_evidence_gate_registry_companion_v3_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'overview_has_evidence_gate_registry_companion or evidence_gate_registry_companion_is_registered_and_dense'`
  - RED first for the missing v3 slot, larger include allocation, and taller
    companion; GREEN after implementation with `2 passed, 73 deselected`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 2 -l 4 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page03_evidence_gate_registry_v3_final_20260604/page`
- `pdftoppm -r 90 -png -f 3 -l 3 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page03_evidence_gate_registry_v3_final_90dpi_20260604/page`
