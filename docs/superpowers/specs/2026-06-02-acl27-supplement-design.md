# ACL27 Supplement Design

Date: 2026-06-02.

## Goal

Build a standalone ACL-style supplement for the current ACL/ARR candidate. The
target first version is 32-36 pages, with room to expand toward 40 pages if the
extra material remains evidence-bearing and anonymous.

## Venue Boundary

The main paper remains self-contained. The supplement may contain derivations,
diagnostics, sample outputs, extra visual evidence, media inventories, and
replication notes, but it must not carry claims that are essential for
understanding the main paper. Appendix text and any media inventory must stay
anonymous and must not point to private paths, non-anonymous repositories, or
raw source locations.

The readable supplement PDF follows the ACL review layout. Most sections use
the same double-column format as the main paper. Math-heavy derivations may use
brief single-column blocks for readability, then return to the normal style.
Video clips and raw frame directories are not embedded directly in the PDF;
the PDF shows selected still panels and references an anonymized media manifest.

## Structure

The supplement is organized as eight appendices:

- Appendix A: claim-boundary map and evidence registry.
- Appendix B: mathematical definitions and metric derivations.
- Appendix C: VLM prompt, parser, and coordinate protocol.
- Appendix D: additional GRScenes visual and diagnostic evidence.
- Appendix E: material-effect and NVIDIA baseline diagnostic panels.
- Appendix F: InternNav / DualVLN navigation stills and media inventory.
- Appendix G: hypotheses and failure-mode interpretation.
- Appendix H: reproducibility, artifact, and media manifest.

The desired page budget is:

- A: 2 pages.
- B: 5-6 pages.
- C: 4 pages.
- D: 4-5 pages.
- E: 5-6 pages.
- F: 10-12 pages.
- G: 4-5 pages.
- H: 3 pages.

## File Design

Create `paper/venues/acl27/supplement.tex` as the standalone entry point. Place
ACL-specific supplement sections under `paper/venues/acl27/sections/supplement/`
so the main paper sections stay stable. Reuse shared figures and tables through
the existing ACL preamble path setup. Add `make -C paper acl27-supplement` and
`make -C paper clean-acl27-supplement` targets without changing the existing
`acl27` main-paper target.

The supplement should initially reuse current project artifacts:

- `paper/shared/tables/tab_acl_evidence_gate_registry.tex`
- `paper/shared/tables/tab_grscenes_vlm_coordinate_ablation.tex`
- `paper/shared/tables/tab_vlm_coordinate_baselines.tex`
- `paper/shared/tables/tab_grscenes_vlm_failure_taxonomy.tex`
- `paper/shared/tables/tab_material_effect_risk_matrix.tex`
- `paper/shared/tables/tab_material_safe_conversion_recommender.tex`
- `paper/shared/tables/tab_official_scene_submission_closure_status.tex`
- `paper/shared/figures/fig_material_effect_supplemental_qualitative.png`
- `paper/shared/figures/fig_internnav_rollout_selected6_supp.png`
- `paper/shared/figures/fig_internnav_rollout_0036_0066_selected6_supp.png`
- `paper/shared/evidence/raw/internnav_vln_downstream/video_case_manifest*.json`

## Guardrails

- Do not broaden claims beyond the main paper's evidence gates.
- Label selected screenshots and videos as qualitative evidence.
- Label theory-heavy text as interpretation or hypothesis unless it is directly
  derived from measured artifacts.
- Keep raw videos and raw frames outside the safe default review packet until
  the author approves the media-upload path.
- Do not add author names, local absolute paths, usernames, private links, or
  acknowledgments to the supplement PDF.

## Acceptance Criteria

- `make -C paper acl27-supplement` builds
  `paper/venues/acl27/build/supplement.pdf`.
- `pdfinfo` reports A4 and at least 20 pages; the v0 target is 32 or more pages.
- The supplement contains the eight appendices listed above.
- The PDF text contains no private path or author-identifying tokens from the
  current packet scan list.
- A dated record under `docs/records/` explains the scaffold and verification.
