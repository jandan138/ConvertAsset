# Material-Effect Baseline Raw Outputs

This directory stores small, repo-resident metadata and summary artifacts for
the ConvertAsset vs NVIDIA material-effect baseline line.

Current files:

- `effect_sample_manifest.json`: links GRScenes expanded30 stress pairs to MDL
  material files, effect labels, and baseline execution planning metadata.
- `nvidia_baseline_smoke_manifest.json`: records the local Isaac Sim NVIDIA
  Asset Converter smoke over NVIDIA's own MDL fixture. The smoke passed two USD
  PreviewSurface baseline candidates and gates the next sample-level baseline.
- `nvidia_baseline_smoke/`: small repo-resident smoke outputs from the NVIDIA
  fixture conversion, kept with the manifest because the total footprint is
  small and directly auditable.

This directory should not store large raw render frames, uncompressed videos, or
full scratch USD trees. Large intermediate assets belong under the normalized
external research root and should be summarized here through manifests.
