# 2026-07-24 Scientific Environment Source-Fix Round (7/7 Pass)

## Why this record exists

Follow-up to [2026-07-23 batch admission](2026-07-23-aan-scientific-environment-batch-admission.md):
5 candidates were blocked by genuine source-data defects. Scenario Forge
instructed producer-side source repair (no package-only injection, no fake
waivers, Isaac 4.1 MDLC compilation and runtime evidence as the bar), then
rerun AAN under the updated hash-bound request. Result: **all 7 candidates
now pass** (066/067 untouched from the previous round).

## Binding investigation before repair

- 081 `mdl_0005.mdl` -> `/World/Looks/material_002`: **no bound prims**
  (raw `material:binding` rel scan confirmed).
- 083 `mdl_0006.mdl` -> `/World/Looks/material_003`: **no bound prims**.
- 081 `mdl_0040.mdl` -> `/World/Looks/material_037`: bound to 6
  `geomsubset_03` prims across small-prop meshes.

## Source repairs (all inside LabUtopia-Dataset source trees)

Root `.usd` hashes are unchanged (verified after edits); only MDL/texture
sidecars were added or repaired. The hash-bound request
`convertasset_batch_admission.yaml` now carries a
`producer_source_updates` section (`2026-07-24-producer-source-fix-2`)
listing every sidecar file with its new SHA-256.

| Candidate | Repair |
|---|---|
| 081 | Placeholder neutral-gray 64x64 JPEGs for the two dataset-absent textures (`a________1/原图222.jpg`, `vm_v1_005_Radial_button/3d66Model-1416944-files-26.jpg`); `mdl_0059.mdl` Material__38 redeclaration fixed (rename first export -> `Material__38_base`, blend references base); `mdl_0040.mdl` `ad_3dsmax_gradient_ramp` restored to template default arrays (caller array literals were non-uniform and redundant with defaults) |
| 083 | Placeholder gray JPEG for `a________3/原图222.jpg`; `mdl_0066.mdl` Material__38 redeclaration fixed (same pattern) |
| 084 | `mdl_0067.mdl` Material__38 redeclaration fixed (same pattern; USD `subIdentifier: Material__38` preserved on the blend) |
| 085 | `mdl_0012.mdl`: dropped invalid `.tint` on `float3`-returning `ad_3dsmax_noise_bump`; explicit `color(...)` conversions at `Diffuse` and `Reflection` (MDL C302 requires explicit float3 -> color) |
| 059 | `mdl_0066.mdl`: `mixAmount : Material__58().mono` (illegal member access on a material) replaced with constant `1.0f` (full light material for the ceiling fixture; documented judgment call since the original mask texture is unknown) |

MDL style follows the instruction: MDL 1.6, conservative constructs only
(rename, drop invalid member access, explicit conversions, constant blend,
template defaults) — no 5.1-only APIs such as `base::texture_return` member
tricks beyond what the source already used.

## Results (same revision `main@61c924f`, gates static,runtime, Isaac 4.1 worker)

All five: `overall_status: pass`, every stage gate pass, AAN-11 runtime MDL
compiler gate **pass**, interior render probes 0.969-1.0, source integrity
locks intact.

Packages: `scenario-forge/outputs/scientific_environment_background_screening_20260723/packages/scientific_environment_{081,083,084,085,059}/`
with `evidence/manifest.json`; batch summary at
`../convertasset_batch_admission_summary.json`.

## Claim boundary and follow-ups

- The 4.1 evidence is complete (compile + runtime). A 5.1 regression pass
  still needs an Isaac 5.1 runtime, which is not available on this machine
  (`/isaac-sim` is 4.5.0, the AAN worker env is 4.1); the repairs were
  deliberately restricted to portable MDL 1.6 constructs to minimize 5.1
  risk, but that is a risk assessment, not 5.1 evidence.
- Placeholder textures are visibly neutral gray: honest stand-ins recorded
  in the manifests, not reconstructions of the lost originals.
- 059's `mixAmount: 1.0f` chooses full-light for the ceiling fixture; if
  Scenario Forge later recovers the intended mask texture, the constant can
  be replaced with the textured mask.

## Verification

- Per-candidate manifests: all gates pass, `blocked_reasons: []`,
  `runtime_compiler.status: pass` for 081/083/084/085/059.
- `python -m pytest tests/ -q` -> `674 passed, 4 skipped` (unchanged; no
  code changes in this round, source-data only).
