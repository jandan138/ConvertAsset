# ACL → ICLR appendix figure migration

Audited 34 active TeX files and 49 figure occurrences (49 distinct figure references), recursively including `suppcasepair`.

Each distinct real case is retained in the canonical plates below. Repeated schematics move to concise metric/protocol definitions. Numeric results use corrected fixed-denominator analyses; qualitative reruns remain separate from the 99-episode metrics.

## New plates

- **appendix_render_pairs_01**: 0004/front, 0004/top_front_left, 0004/top_front_right, 0011/front, 0011/top_front_left.
- **appendix_render_pairs_02**: 0011/top_front_right, 0023/front, 0023/top_front_right, 0029/front, 0029/top_front_right.
- **appendix_scene_pairs**: orbit_01, orbit_03, orbit_05, orbit_07.
- **appendix_clean_grounding**: 47aa36277a54f6ca90cc.zoom_018, f35ef3d86c42446b7ddf.zoom_018, c27086f557d316584264.zoom_018, e2ec085d524d5df4455d.zoom_020.
- **appendix_grounding_diagnostics_01**: bb985fd4504a1afe8516.zoom_017, c8ee4b66274b05d242c2.zoom_017, ef6a4fe9448f672c2ecc.zoom_017.
- **appendix_grounding_diagnostics_02**: 47aa36277a54f6ca90cc.zoom_019, f35ef3d86c42446b7ddf.zoom_019.
- **appendix_material_comparison**: c27086f557d316584264.zoom_018, f35ef3d86c42446b7ddf.zoom_018, e2ec085d524d5df4455d.zoom_020, 47aa36277a54f6ca90cc.zoom_018.
- **appendix_material_failures**: supplemental_clearcoat_omnipbr, supplemental_procedural_checker.
- **appendix_navigation_cases_01**: kujiale0031/494_494, kujiale0031/479_479.
- **appendix_navigation_cases_02**: kujiale0031/464_464, kujiale0031/473_473.
- **appendix_navigation_cases_03**: kujiale0031/493_493, kujiale0031/484_484.
- **appendix_navigation_cases_04**: kujiale0036_0066/898_898, kujiale0036_0066/919_919.
- **appendix_navigation_cases_05**: kujiale0036_0066/895_895, kujiale0036_0066/597_597.
- **appendix_navigation_cases_06**: kujiale0036_0066/891_891, kujiale0036_0066/598_598.
- **appendix_readout**: board02.q0.side0.two_view_category.

## Source figure disposition

| Previous figure | Replacement |
|---|---|
| figures/fig_acl_method_chain_v4.pdf | main overview |
| \aclEvidenceGateCompanion | appendix metric definitions, appendix_render_pairs_01, appendix_material_comparison, appendix_clean_grounding |
| figures/fig_render_scene_evidence_wide_v3.pdf | appendix_render_pairs_01, appendix_render_pairs_02, appendix_scene_pairs |
| figures/fig_material_effect_baseline_qualitative_v3.pdf | appendix_material_comparison, appendix_material_failures, appendix material inventory |
| figures/fig_internnav_rollout_main_v4.pdf | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/fig_supplement_first_page_evidence_quickstart_v2.pdf | appendix metric definitions, appendix_render_pairs_01, appendix_material_comparison, appendix_clean_grounding |
| figures/fig_supplement_visual_evidence_roadmap.png | appendix metric definitions, appendix_render_pairs_01, appendix_material_comparison, appendix_clean_grounding |
| figures/fig_supplement_render_atlas_opener.png | appendix_render_pairs_01, appendix_render_pairs_02, appendix_scene_pairs |
| figures/fig_supplement_render_atlas.png | appendix_render_pairs_01, appendix_render_pairs_02, appendix_scene_pairs |
| figures/fig_supplement_render_scene_evidence_extended.png | appendix_render_pairs_01, appendix_render_pairs_02, appendix_scene_pairs |
| figures/fig_grscene_qualitative.png | appendix_render_pairs_01, appendix_render_pairs_02, appendix_scene_pairs |
| figures/fig_supplement_vlm_clean_rerender_panel.png | appendix_clean_grounding |
| figures/fig_material_effect_baseline_qualitative.png | appendix_material_comparison, appendix_material_failures, appendix material inventory |
| figures/fig_supplement_proxy_metric_derivation_companion.png | appendix metric definitions, appendix_render_pairs_01, appendix_material_comparison, appendix_clean_grounding |
| figures/fig_supplement_grounding_derivation_companion.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_navigation_derivation_companion.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/fig_supplement_metric_boundary_bridge.png | appendix metric definitions, appendix_render_pairs_01, appendix_material_comparison, appendix_clean_grounding |
| figures/fig_supplement_vlm_coordinate_protocol_atlas_v2.pdf | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_vlm_coordinate_table_companion.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_vlm_coordinate_baseline_sanity_companion.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_grscenes_vlm_visual_guide.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_grscenes_diagnostic_case_atlas.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_grscenes_vlm_stress_render_strip.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_grscenes_failure_taxonomy_table_companion.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_grscenes_pass_only_table_companion.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_grscenes_zoom_stress_table_companion.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_material_intro_column.png | appendix_material_comparison, appendix_material_failures, appendix material inventory |
| figures/fig_supplement_material_diagnostic_atlas_v2.pdf | appendix_material_comparison, appendix_material_failures, appendix material inventory |
| figures/fig_supplement_material_claim_boundary_atlas.png | appendix_material_comparison, appendix_material_failures, appendix material inventory |
| figures/fig_supplement_material_decision_map.png | appendix_material_comparison, appendix_material_failures, appendix material inventory |
| figures/fig_supplement_navigation_intro_column.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/fig_supplement_navigation_media_atlas_v2.pdf | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/supplement/internnav_selected6_case01.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/supplement/internnav_selected6_case02.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/supplement/internnav_selected6_case03.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/supplement/internnav_selected6_case04.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/fig_supplement_internnav_selected6_neutral_companion.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/supplement/internnav_0036_0066_case01.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/supplement/internnav_0036_0066_case02.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/supplement/internnav_0036_0066_case03.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/supplement/internnav_0036_0066_case04.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/fig_supplement_internnav_0036_neutral_companion.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/fig_supplement_navigation_media_boundary_strip.png | appendix_navigation_cases_01, appendix_navigation_cases_02, appendix_navigation_cases_03, appendix_navigation_cases_04, appendix_navigation_cases_05, appendix_navigation_cases_06, appendix full paired navigation metrics |
| figures/fig_supplement_internnav_upload_gate_closure_card.png | appendix reproducibility text |
| figures/fig_supplement_theory_evidence_bridge.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_theory_failure_mode_map.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_theory_hypothesis_boundary_companion.png | appendix_clean_grounding, appendix_grounding_diagnostics_01, appendix_grounding_diagnostics_02, appendix corrected protocol/tables |
| figures/fig_supplement_review_packet_contact_sheet.png | appendix reproducibility text |
| figures/fig_supplement_source_boundary_companion.png | appendix reproducibility text |

## Validation and handoff

Python/Matplotlib exports SVG, PDF and 360-dpi PNG. Every source raster and any explicit crop is hash-recorded in `figures/supplement/figure-spec.json`. All text uses at least 7 pt. Final manuscript-scale visual inspection remains required after integration.
