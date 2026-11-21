# ACL Story-first Figure v3 and Supplement Atlas Refresh

Date: 2026-09-03

## Investigation

The v2 ACL visual system corrected the evidence topology, but the first figure
still needed a stronger first-glance story and the supplement retained several
dense, locally styled atlases. The latest scientific-figure workflow was
applied to the five main-paper visuals and four high-priority supplement
figures. Review covered standalone PNGs and their integrated ACL pages.

The earlier Figure 1 concept included four material examples. The v3 audit
therefore restored wood, stone, ceramic, and metal as paired source/simplified
spheres while preserving the real matched-render pair at the center of the
scientific argument.

## Design Decisions

- Figure 1 uses one story-first hero path: material intervention leads to
  matched evidence, then fans out to four parallel proxy, VLM, material, and
  embodied-stack checks.
- The eight material-sphere slots are generated raster components. They are
  replaceable explanatory cues and are explicitly excluded from experimental
  evidence and quantitative claims.
- Scientific text, arrows, grouping, labels, and layout remain deterministic
  Python/Matplotlib output. Real render, grounding, material, and navigation
  evidence remains sourced from registered experiment artifacts.
- Table 1 retains searchable LaTeX content and receives a compact visual strip.
  Figures 2--4 and the four supplement atlases use the same condition colors,
  typography, headers, and evidence-boundary language.
- ACL-only versioned assets are used so historical and other-venue figures stay
  intact.

## Implementation

`paper/shared/figures/gen_acl_paper_figures_v3.py` generates nine figure bundles
in SVG, PDF, and 300 dpi PNG. The Figure 1 semantic graph is recorded in
`paper/shared/figures/specs/fig_acl_method_chain_v3.spec.json`. Generated sphere
provenance, the source atlas, prompt, slot manifest, extracted RGBA components,
and optical measurements live under
`paper/shared/figures/generated_components/fig1_material_pairs_v1/`.

Three visual iterations were completed. The first exposed label collisions and
generated shadow artifacts. The second corrected typography and panel geometry.
The third retained the largest connected alpha component for each sphere slot,
removing detached shadows without modifying the sphere body. Figure 1 finishes
at 70 shapes, 27 text nodes, 45 words, and four font sizes; its minimum font
size is 6 pt.

The ACL main and supplement wrappers now point to the new versioned assets.
Source registries, the evidence results manifest, artifact provenance,
responsible-AI disclosure, claim checks, layout tests, and integrity inputs were
updated with them. The machine-readable review is
`paper/shared/figures/acl_paper_visual_v3.qa.json`.

## Verification

Commands used during the final pass include:

```bash
python paper/shared/figures/gen_acl_paper_figures_v3.py --target all \
  --output-dir paper/shared/figures
python /root/.codex/skills/build-scientific-figures/scripts/validate_figure_spec.py \
  paper/shared/figures/specs/fig_acl_method_chain_v3.spec.json \
  --check-assets --require-approved --strict
python -m pytest -q \
  tests/test_acl_paper_figures_v3.py \
  tests/test_paper_layout.py \
  tests/test_acl_claim_boundaries.py
make -C paper clean-acl27 acl27 acl27-supplement
python paper/venues/acl27/scripts/run_preupload_gate.py
```

The focused v3/layout/claim suite passed 104 tests. The semantic specification
passed strict validation with zero errors and zero warnings. The integrated
main paper remains 10 A4 pages and the supplement remains 45 A4 pages. Page
review covered main pages 2, 4, 5, 6, and 8 and supplement pages 1, 15, 25, and
29; no clipping, overlap, detached captions, missing glyphs, or broken assets
were observed. The consolidated pre-upload gate passed with 176 focused ACL
tests. Embedded main-paper rasters resolve at 343--365 ppi. The final main build
and staged submission PDF are byte-identical with SHA-256
`ef2e589a7244f639ba65f82eb22b634308ed6c2300ef8af6ecce9425ba70a51e`; the
supplement SHA-256 is
`d37d4e691d33f17de68808155c70ff57573f52cd1ae4f4779ed27ec999ab39f3`.

## Open Issues

- The material spheres must not be described as measured render evidence. Their
  manifest and the manuscript caption preserve this boundary.
- Figure 3 retains the brightness of its registered source evidence rather than
  cosmetically changing experimental pixels.
- The final submission route, private author fields, OpenReview form copy, and
  runtime/media approvals remain human-owned submission tasks outside this
  figure refresh.
