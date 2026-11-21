# ACL Main-Figure Visual-System Redesign

Date: 2026-08-30

## Investigation

The ACL candidate used five main-paper raster compositions: a generated
four-stage Figure 1, a dense visual companion below Table 1, paired render
evidence, a material-effect contact sheet, and an InternNav rollout grid. The
paper-level review found three recurring issues: Figure 1 encoded independent
checks as a visual sequence, Table 1 repeated the same scope information in
three layers, and the evidence figures did not share one condition-color or
typography system.

The EBench reconstruction case study was used in inspired mode. Only its visual
grammar was adopted: clear regions, a strong structural color, real evidence
slots, explicit connector topology, and compact labels. No EBench image,
scientific claim, task count, or spatial template was copied into the paper.

## Design Decisions

- Figure 1 now models `source -> conversion -> matched evidence` as the
  sequential path and fans matched evidence into four independent proxy, VLM,
  material, and stack gates.
- Main-paper condition colors are stable: Original MDL/structure blue, noMDL
  orange, pass/preserved green, InternNav trajectory purple, and NVIDIA grey.
- Table 1 retains searchable LaTeX rows. The ACL main wrapper selects a compact
  four-card evidence strip, while the supplement keeps its larger companion.
- Figures 2--4 keep the same registered evidence and claim boundaries. The
  redesign changes composition, crop presentation, labels, and spacing only.
- New ACL-only versioned files avoid changing the AAAI wrapper or historical
  supplement assets.

## Implementation

`paper/shared/figures/gen_acl_main_figures_v2.py` generates all five figures in
SVG, PDF, and PNG. Figure 1 also has a reviewed semantic specification at
`paper/shared/figures/specs/fig_acl_method_chain_v2.spec.json`. The source
registry, results manifest, ACL integrity fingerprint inputs, artifact
provenance, captions, and ethics wording were updated to match the active
assets. Historical figure candidates remain untouched.

## Verification

Commands executed:

```bash
python paper/shared/figures/gen_acl_main_figures_v2.py --figure all
python /root/.codex/skills/build-scientific-figures/scripts/validate_figure_spec.py \
  paper/shared/figures/specs/fig_acl_method_chain_v2.spec.json \
  --check-assets --require-approved --strict
python -m pytest -q \
  tests/test_acl_main_figures_v2.py \
  tests/test_render_scene_evidence_figure.py \
  tests/test_paper_layout.py \
  tests/test_acl_claim_boundaries.py
make -C paper clean-acl27 acl27
```

Results at the integrated-PDF checkpoint:

- semantic specification: pass with zero errors and zero warnings;
- focused tests: 109 passed;
- ACL build: 10 A4 pages, PDF 1.5;
- embedded raster evidence: approximately 343--365 ppi;
- page review: Figures 1--4 and Table 1 have no clipping, overlap, detached
  captions, missing glyphs, or broken assets.

Final checks after source freeze:

- final-integrity fingerprint: pass over 54 protected sources;
- extended standalone focused tests: 161 passed;
- consolidated pre-upload gate: pass with 168 focused tests, including claim, target-policy, metadata,
  checklist, citation, evidence-number, fingerprint, clean-build, staging,
  private-token, acknowledgment, PDF-profile, and ordered-section checks;
- staged main PDF: 10 A4 pages, PDF 1.5, 4,882,595 bytes.

The repository remains candidate-ready but human-blocked on route selection,
private author fields, OpenReview form copy, and final runtime/media approvals;
those pre-existing submission decisions are outside this figure task.

## Open Issues

- The final ACL-family route and OpenReview human fields remain outside this
  visual task.
- Figure 3 effect tags are compact at final width; Table 5 remains the
  authoritative material-effect scope artifact.
- InteriorAgent/KuJiaLe redistribution terms still govern any media distributed
  separately from the manuscript PDF.
