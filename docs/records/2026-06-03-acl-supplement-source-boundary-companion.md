# 2026-06-03 ACL Supplement Source Boundary Companion

## Scope

Improved the ACL supplement reproducibility/source-boundary material by adding
`fig_supplement_source_boundary_companion.png` as a full-width companion page
after the reproducibility text and before references.

The companion makes the source boundary more visual and less scattered by
combining:

- registered packet, render-atlas, material, VLM, and navigation source panels
- registered 0036/0066 route stills and selected route case media
- a render source tray with proxy, scene, target-view, material, and route panels
- paired original/noMDL target-view closeups for backpack, clock, bottle, and cup cases
- an imagegen-created `source_boundary_gate` schematic slot

## Claim Boundary

The AI-generated `source_boundary_gate` slot is exposition only. It is not a
render result, evidence source, experiment, metric, VLM run, navigation run, or
benchmark row.

The evidence-bearing content remains the registered source figures and selected
target-view renders. The AI slot is replaceable and only explains the review
packet boundary: readable sources enter the PDF, while raw/private frame
directories and local artifacts remain outside the review packet.

## Layout Outcome

The first inserted version was rejected in visual review because a column-width
image in the two-column reproducibility section split the image and caption
across columns. The second version used a full-width float but mixed the figure
with bibliography text and left the preceding page sparse.

The final version:

- uses a taller `1320x1380` deterministic composition with additional render closeups
- places the `figure*` after the reproducibility text and before bibliography
- keeps page 43 as filled two-column text
- places the companion and caption together on page 44
- starts references normally on page 45

Measured rendered-page active fractions:

- page 43: `0.053412`
- page 44: `0.242364`
- page 45: `0.050105`

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_source_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_source_boundary_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_source_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/07_reproducibility.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_source_boundary_companion_v1_20260603.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_reproducibility_has_visual_media_manifest tests/test_paper_layout.py::test_supplement_source_boundary_companion_is_registered_and_dense`
- `python -m pytest -q tests/test_paper_layout.py::test_figure_sources_outputs_and_generators_are_consistent tests/test_paper_layout.py::test_acl_supplement_reproducibility_has_visual_media_manifest tests/test_paper_layout.py::test_supplement_source_boundary_companion_is_registered_and_dense`
- `make -C paper acl27-supplement`
- Rendered PDF pages 43-45 with `pdftoppm`.
- Pure visual review checked standalone figure density, page 43 text flow, page 44 figure/caption placement, and page 45 bibliography flow.

Visual review was local rather than an independent subagent review; the evidence
JSON records `independent_subagent: false`.
