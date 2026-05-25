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
- `supplemental_fixtures/`: small repo-resident wrapper USD stages,
  ConvertAsset no-MDL outputs, and ConvertAsset audit/summary sidecars for the
  supplemental material-effect cases.
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
  one after supplemental clearcoat exposes a NVIDIA static-gate failure.
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
