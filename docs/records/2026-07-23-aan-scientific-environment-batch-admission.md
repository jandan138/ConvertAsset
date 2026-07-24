# 2026-07-23 Scientific Environment Batch Admission (7 Candidates)

## Why this record exists

Scenario Forge screened 92 scene USDs by thumbnails, re-shot the top 10 in
EOS Isaac Sim 4.1, and sent 7 candidates for batch admission via the
hash-bound request
`scenario-forge/outputs/scientific_environment_background_screening_20260723/convertasset_batch_admission.yaml`
(`request_id: scientific_environment_visual_static_d60b1a9e87b3`). All seven
source SHA-256 values matched the pinned catalog hashes before admission ran.

The request role `visual_static_environment` (scope `/World`) was new, and
the batch surfaced three producer-side closure gaps plus five genuine
source-data defects. This record documents the ConvertAsset changes and the
per-candidate outcomes.

Note: the consumer's chat message mentioned scope `/World_走廊`; the
hash-bound YAML declares `source_scope: /World` and `/World_走廊` does not
exist in the sources, so `/World` was used.

## ConvertAsset changes (commit `61c924f`)

| Change | Files | Effect |
|---|---|---|
| `visual_static_environment` role with `visual_static` semantics, recorded verbatim in manifests | `model.py`, `cli.py`, `pipeline.py`, `physics_checks.py`, `role_normalization.py`, `runtime_smoke.py`, `usd_closure.py` | New role admitted; scope extraction, scope-first closure, rigid-reset `not_applicable`, and role claims all apply |
| Remote-URI local mirror resolution (AAN-03R "prefer local mirror" for legally synchronized content) | `usd_closure.py` | Remote deps resolve from mirror roots by URL-path suffix with `resolution: mirrored_remote` provenance; unmirrored remote URIs still block |
| Scanner collects asset paths nested in property `customData` (NVIDIA materials keep original CDN URLs there; binary layers have no text-regex fallback) | `usd_closure.py` | Hidden customData deps become visible to closure; fail-closed snapshot rewrite no longer trips on unscanned strings |
| Scope-first filter keeps deps whose holder prim is under scope/bound-material subtrees | `usd_closure.py` | Bound-material customData deps stay in scope; unselected siblings stay out |
| AAN-06 render gate retries enclosed scopes from interior look-out probes (blank exterior orbit, or fragment ratio <= 0.35); best probe wins, non-blank still required | `runtime_smoke.py` | Interior environments produce honest non-blank Isaac 4.1 renders instead of exterior-wall blanks |

Producer-side mirror cache created (legally synchronized NVIDIA Slate
content, copied from `Labs/lab_083/Materials/Base/Stone/`):
`_datasets/LabUtopia-Dataset/Materials/Base/Stone/Slate.mdl` and
`Slate/Slate_Tile_{BaseColor,N,ORM}.png` (SHA-256 identical to source
copies). This unblocked remote `Slate.mdl` (081) and remote Slate texture
URLs (083).

## Per-candidate results (single revision, all gates static,runtime on Isaac 4.1)

| Candidate | Result | Evidence |
|---|---|---|
| 066 | **pass** | Render upgraded exterior fragment (0.14) -> interior probe (0.999) |
| 067 | **pass** | Was blank exterior orbit; interior probe 0.94 -> pass |
| 081 | blocked `aan11_block_required_mdl_runtime_dependency` | 2 MDL-internal textures genuinely absent from the entire dataset: `./a________1/原图222.jpg` (diffuse), `./vm_v1_005_Radial_button/3d66Model-1416944-files-26.jpg` |
| 083 | blocked `aan11_block_required_mdl_runtime_dependency` | 1 MDL-internal texture genuinely absent: `./a________3/原图222.jpg` (diffuse) |
| 084 | blocked `aan11_block_runtime_material_compiler` | Source MDL defect `mdl_0067.mdl(171,8): C104 redeclaration of 'material Material__38'` (duplicate export + self-referential blend) |
| 085 | blocked `aan11_block_runtime_material_compiler` | Source MDL defect `mdl_0012.mdl(55,7): C111 type 'float3' has no member 'tint'` |
| 059 | blocked `aan11_block_runtime_material_compiler` | Source MDL defect `mdl_0066.mdl(118,32): C111 type 'material' has no member 'mono'` |

Packages and `evidence/manifest.json`:
`scenario-forge/outputs/scientific_environment_background_screening_20260723/packages/scientific_environment_0XX/`
(blocked candidates keep sidecar `scientific_environment_0XX.manifest.json`).
Batch summary: `../convertasset_batch_admission_summary.json`.

All seven sources remained hash-unchanged during processing
(`source_integrity.unchanged: true`); USD-level remote/missing dependency
counts are 0/0 for every candidate after closure.

## Claim boundary

- The five blocked candidates are **source-data defects**, not ConvertAsset
  gate bugs: missing texture files absent from the dataset, and MDL modules
  that fail MDLC compilation in the raw Isaac preview as well. Admission
  stays blocked per AAN fail-closed policy; no waiver or preview-fallback
  was synthesized because the consumer must first decide between upstream
  source repair, a scoped waiver policy, or candidate replacement.
- 084/085/059 runtime load/render/step/reset passed with interior probes
  (0.96-1.0); the block is the AAN-11 runtime MDL compiler gate, so their
  renders are retained as evidence but the packages are not admitted.
- Interior probes are recorded per-view in `render_readback.retry_attempts`;
  the strategy (`interior_center_look_out`) is explicit in every manifest.

## Verification

- `python -m pytest tests/ -q` -> `674 passed, 4 skipped` (14 new AAN tests:
  role, customData scan, remote mirror, holder-in-scope, interior retry).
- `python -m ruff check` on touched files -> clean (2 pre-existing errors in
  untouched files remain).
