# Material-Effect Baseline Raw Outputs

This directory stores small, repo-resident metadata and summary artifacts for
the ConvertAsset vs NVIDIA material-effect baseline line.

Current files:

- `effect_sample_manifest.json`: links GRScenes expanded30 stress pairs to MDL
  material files, effect labels, and baseline execution planning metadata.
- `supplemental_effect_candidate_manifest.json`: records bounded local
  official/sample candidates for the missing `clearcoat` and
  `procedural_texture` bins.
- `supplemental_wrapper_stage_manifest.json`: records the two repo-resident
  wrapper stages that bind the selected official/sample MDL sources to small
  renderable targets.
- `supplemental_conversion_manifest.json`: records original / ConvertAsset
  no-MDL / NVIDIA condition availability for the supplemental clearcoat and
  procedural texture wrappers. Current static gates show ConvertAsset passing
  both, NVIDIA passing procedural texture, and NVIDIA dropping clearcoat
  material output.
- `supplemental_qualitative_render_manifest.json`: records the two
  supplemental wrapper cases across original MDL, ConvertAsset no-MDL, and
  NVIDIA render conditions. Current state is 2/2 ready cases and 6/6 ready
  images.
- `supplemental_qualitative_render_run_manifest.json`: records the Isaac Sim
  viewport-capture run for those six supplemental stills; the current run has
  `attempted=6`, `ready=6`, and `failed=0`.
- `supplemental_qualitative_visual_qa.json`: records machine visual QA over
  the supplemental stills. It flags one rendered failure candidate:
  NVIDIA clearcoat is near-black after the static-gate-failed conversion.
- `supplemental_clean_room_visual_review.json`: records the clean-room
  human-style visual QA pass over the six supplemental stills. The overall
  verdict is `FAIL`, so these stills are failure/retake evidence rather than a
  success-style qualitative panel.
- `supplemental_material_preservation_diagnostic.json`: records the PXR static
  USD-network diagnosis for the two supplemental cases. It confirms NVIDIA
  clearcoat is missing the target prim and both converted procedural conditions
  lack checker/base-color texture preservation evidence.
- `supplemental_fixtures/`: small repo-resident wrapper USD stages,
  ConvertAsset no-MDL outputs, and ConvertAsset audit/summary sidecars for the
  supplemental material-effect cases.
- `supplemental_qualitative_renders/`: repo-resident supplemental stills for
  the clearcoat and procedural texture wrappers.
- `supplemental_qualitative_render_logs/`: stdout/stderr logs from the
  supplemental viewport-capture commands.
- `nvidia_baseline_smoke_manifest.json`: records the local Isaac Sim NVIDIA
  Asset Converter smoke over NVIDIA's own MDL fixture. The smoke passed two USD
  PreviewSurface baseline candidates and gates the next sample-level baseline.
- `nvidia_sample_conversion_manifest.json`: records the sample-level NVIDIA
  Asset Converter run over five unique selected source scenes. Large converted
  USD outputs stay under the external normalized research root.
- `baseline_conversion_manifest.json`: records sample-level condition
  availability and static gates for 30 selected samples. Original MDL and
  ConvertAsset no-MDL rows are available; NVIDIA sample rows are available after
  the sample conversion runner.
- `effect_failure_case_manifest.json`: records effect-labeled follow-up cases
  from non-available or static-gate-failed condition rows. Current case count is
  one after supplemental clearcoat exposes a NVIDIA static-gate failure; the
  same row now links to the near-black rendered failure image through
  `rendered_failure_*` fields.
- `qualitative_render_manifest.json`: selects four representative expanded30
  cases and records matched original / ConvertAsset / NVIDIA render records for
  the covered effect bins.
- `qualitative_camera_stage_authoring_report.json`: records the selected NVIDIA
  camera-stage authoring run; all four camera stages were authored under
  `qualitative_renders/`.
- `qualitative_nvidia_render_run_manifest.json`: records the selected-only
  NVIDIA render run; all four NVIDIA qualitative PNG outputs are ready.
- `qualitative_renders/`: small repo-resident NVIDIA stills and camera stages
  for the selected qualitative comparison cases.
- `qualitative_render_logs/`: stdout/stderr logs from the selected-only NVIDIA
  qualitative render commands.
- `nvidia_baseline_smoke/`: small repo-resident smoke outputs from the NVIDIA
  fixture conversion, kept with the manifest because the total footprint is
  small and directly auditable.

This directory should not store large raw render frames, uncompressed videos, or
full scratch USD trees. Large NVIDIA supplemental conversion outputs remain
under the normalized external research root and are summarized here through
manifests.
