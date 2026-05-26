# 2026-05-26 Reviewer Closure Status And Next Goal

## Purpose

This record summarizes the current reviewer-response state after the
material-effect ConvertAsset-vs-NVIDIA baseline, the supplemental clearcoat and
procedural diagnostics, and the official InternNav / KuJiaLe downstream runs.

It is a claim-boundary ledger. It should be used to decide what can be written
in the paper now, what must stay in limitations, and what the next major goal
should be.

## Three-Condition Material Comparison

The material-effect experiment compares three conditions:

| Condition | Role | Plain meaning |
| --- | --- | --- |
| `original_MDL` | Reference condition | The source Isaac Sim material, treated as the visual/material reference. |
| `existing_noMDL` | ConvertAsset condition | Our composition-preserving MDL-to-UsdPreviewSurface conversion. |
| `nvidia_asset_converter_preview_or_bake` | NVIDIA baseline | NVIDIA `omni.kit.asset_converter`; the current GRScenes route uses the smoke-validated `usd_to_usd_preview` output, while `usd_to_usd_bake_flag` is a verified smoke candidate but not the main expanded sample route. |

### GRScenes-Covered Bins

The GRScenes expanded30 material-effect pool covers four effect bins:

- `opacity_transparency`
- `emission`
- `normal_bump`
- `displacement_height`

For these bins, all three conditions are available and pass the static gates.
The selected qualitative panel is also ready. The correct paper claim is:

```text
For the GRScenes-covered effect bins, both ConvertAsset and the NVIDIA
Asset Converter baseline have bounded static and selected qualitative evidence.
```

This should not be written as a final visual-quality win or as an all-assets
success rate. It is bounded evidence from the selected sample pool.

### Clearcoat

The clearcoat case comes from a supplemental official/sample wrapper because
GRScenes did not provide a clean clearcoat case in the selected pool.

Current interpretation:

- Original MDL: target exists and carries the clearcoat-style source material.
- ConvertAsset noMDL: target is retained, but clearcoat is reduced to a
  `UsdPreviewSurface` approximation.
- NVIDIA baseline: selected supplemental output loses the target in the PXR
  diagnostic, with zero shader records for the target condition.

The correct paper claim is:

```text
The supplemental clearcoat case is a selected NVIDIA failure case: ConvertAsset
retains the target as a PreviewSurface approximation, while the selected NVIDIA
output misses the target.
```

This must not be written as a population-level NVIDIA failure rate.

### Procedural Texture

The procedural-texture case also comes from a supplemental wrapper.

Current interpretation:

- Original MDL: has checker/procedural texture evidence.
- ConvertAsset noMDL: static conversion succeeds, but checker preservation is
  not supported by the diagnostic/visual review.
- NVIDIA baseline: static conversion succeeds, but checker preservation is also
  not supported.

The correct paper claim is:

```text
Procedural texture is a limitation/investigation case: both converted
conditions lose the checker-preservation evidence in the selected supplemental
case.
```

This must not be used as a success panel.

## Reviewer Concern Status

| Reviewer concern | Current status | What changed |
| --- | --- | --- |
| Experiment scope too small | Partially mitigated | GRScenes expanded30 VLM grounding adds target/category diversity, and official InternNav val-unseen now covers 99 paired episodes across three KuJiaLe scenes. This is still not a broad all-scene benchmark. |
| "AI task performance" was proxy-only | Partially fixed | The paper now has real VLM grounding evidence and real InternNav / InternVLA-N1 downstream metrics. Claims must stay scoped to these protocols. |
| Missing NVIDIA official-tool baseline | Partially fixed | NVIDIA Asset Converter is now compared through smoke-validated USD routes and the main `usd_to_usd_preview` route on GRScenes-selected samples. Full MDL distill/bake population statistics are still not claimed. |
| Missing per-material-effect analysis | Partially fixed | The risk matrix now separates GRScenes-covered bins from selected clearcoat failure and procedural-texture limitation cases. It is not a population error-rate distribution. |
| Overbroad guideline claims | Addressed in wording | Current manuscript language is claim-bounded and explicitly separates supported evidence from limitations. |
| Large-scene performance statistics too narrow | Partially fixed | The official-scene closure package now adds 18/18 successful fresh-process load/render runs across three official KuJiaLe scenes with bootstrap CIs and failure counts. It is original/noMDL only; NVIDIA official-scene baseline remains unavailable. |
| Missing safe-conversion recommender | Partially fixed | A rule-based safe-conversion table now maps the selected material-effect risk matrix to evidence-gated actions. A learned material-risk classifier remains open. |
| Weak statistical support | Partially fixed | The reviewer-closure package adds paired bootstrap confidence intervals for existing VLM/InternNav evidence and coordinate-only VLM baselines. |
| Title/abstract overpromise | Addressed for this closure pass | The official-scene audit decision records approved/disallowed language and keeps the claim at loadability/stability with overlapping ready-time intervals. |

## What Can Be Written Now

The manuscript can now say:

- ConvertAsset noMDL and NVIDIA Asset Converter can both be compared against
  original MDL on selected GRScenes-covered material-effect bins.
- For `opacity_transparency`, `emission`, `normal_bump`, and
  `displacement_height`, the evidence supports bounded static plus selected
  qualitative comparison across all three conditions.
- The supplemental clearcoat case is a selected NVIDIA target-loss failure,
  while ConvertAsset retains the target as an approximation.
- The supplemental procedural-texture case is a limitation for both converted
  conditions.
- ConvertAsset noMDL has been evaluated in a real official InternNav /
  InteriorNav route over 99 paired `val_unseen` episodes, with small aggregate
  differences but scene-dependent behavior.
- Official KuJiaLe scene-load/render timing now has repeated original/noMDL
  measurements across `0031`, `0036`, and `0066`: 18/18 required runs succeeded,
  and ready-time intervals overlap.

The manuscript should not say:

- ConvertAsset is universally visually better than NVIDIA.
- NVIDIA bake/distill is broadly worse than ConvertAsset.
- Procedural textures are preserved.
- The material-effect table is a population-level error-rate estimate.
- The official InternNav 99-episode result proves all-scene downstream
  robustness.
- ConvertAsset is faster on official KuJiaLe scene-load/render performance.
- NVIDIA official-scene performance has been compared.

## Recommended Next Goal

The previous recommended goal, the reviewer-closure package, is now complete.
The next major goal should be:

```text
Build a submission-readiness closure pass: add multi-scene, multi-run
scene-load/render-performance statistics with variance or confidence intervals
on official or releaseable scenes, then run a final claim-language and citation
audit for the target paper route.
```

Why this is now the right next step:

1. The reviewer-closure package already added paired CIs, coordinate baselines,
   and the rule-based material-risk table.
2. The largest remaining concrete reviewer gap is performance breadth: current
   scene-load/render timing evidence is narrower than the downstream InternNav
   and VLM evidence and lacks multi-scene variance.
3. This is lower risk than forcing a broad GRScenes embodied-navigation claim:
   official KuJiaLe / InteriorAgent scenes can support a cleaner, releaseable
   performance protocol.
4. A learned material-risk classifier remains future work; it is not required
   before submission unless the paper claims automatic risk prediction.

Suggested concrete success criteria:

- Select three to five official or releaseable scenes that already have clean
  original/noMDL pairs; prefer official KuJiaLe / InteriorAgent routes over
  ad-hoc GRScenes embodied-navigation claims.
- For each scene, run repeated scene-load and render timing measurements for
  original MDL, ConvertAsset noMDL, and the NVIDIA baseline where available.
- Report means, standard deviations, confidence intervals, failure counts, and
  any unsupported material-effect bins.
- Add the resulting table, manifest entries, and claim-boundary notes to the
  shared paper evidence package.
- Run a final paper audit that removes unsupported broad claims and checks
  citations/provenance for ACL/ARR or the chosen target venue.

## Completion Update

This goal was implemented in
`docs/records/2026-05-26-reviewer-closure-package.md`.

The completed package adds:

- `paper/shared/evidence/raw/reviewer_closure_package/reviewer_closure_statistical_summary.json`
- `paper/shared/evidence/raw/reviewer_closure_package/vlm_coordinate_baseline_summary.json`
- `paper/shared/evidence/raw/reviewer_closure_package/material_safe_conversion_recommender.json`
- `paper/shared/tables/reviewer_closure_paired_ci.csv`
- `paper/shared/tables/vlm_coordinate_baselines.csv`
- `paper/shared/tables/material_safe_conversion_recommender.csv`

The remaining gap is not the rule-table recommender requested here; it is a
future learned or automatic material-risk classifier that generalizes beyond
the selected material-effect evidence.

## Next Goal Completion Update

The follow-up official-scene submission-closure package is recorded in
`docs/records/2026-05-26-official-scene-submission-closure-package.md`.

Current gate status:

- official KuJiaLe / InteriorAgent scene scope: ready for `0031`, `0036`, and
  `0066`;
- selected qualitative videos/stills/contact sheets: ready;
- multi-run load/render performance statistics: ready for required
  original/noMDL conditions with 18/18 successful rows;
- final claim-language and citation/provenance audit: ready via
  `official_scene_claim_audit_decision.json`;
- NVIDIA official-scene baseline: not available until matching NVIDIA converted
  official scenes are generated and smoke-gated.

## Verification

This is a docs-only status update. The expected verification is:

```bash
rg -n "Reviewer Closure Status|Build a paper-ready reviewer-closure package|selected NVIDIA failure|procedural texture is a limitation" docs
git diff --check
```
