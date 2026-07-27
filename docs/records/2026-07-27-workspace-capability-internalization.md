# 2026-07-27 Workspace Capability Internalization

## Why this record exists

The 2026-07 deliveries (batch admission, workspace profiles, 067
re-profiles, external-room facade) produced capability that lived in
`/tmp` probe scripts and one-off YAML assembly. This change internalizes
that capability as regression-locked repo modules so future rooms skip the
same pitfalls.

## New/changed modules

| Module | Content | Tests |
|---|---|---|
| `convert_asset/workspace/geometry.py` | Composed world bbox from mesh points (Gf row-vector convention documented; the M.T pitfall that once landed bboxes at wrong coordinates), counter-band estimation | `tests/test_workspace_geometry.py` |
| `convert_asset/workspace/audit.py` | Clearance overlap audit with three-way intruder classification (`loose_prop` / `flat_item` / room shell), verdict contract | `tests/test_workspace_audit.py` |
| `convert_asset/workspace/profiles.py` | v0.1 integration profile, v0.2 zone profile/manifest writers with exact `coordinate_mapping` and unit clarification | `tests/test_workspace_profiles.py` |
| `convert_asset/workspace/render.py` | Isaac before/after inactivation evidence renders + labeled compose (reuses `render/single.py` flow) | compose smoke |
| `convert_asset/asset_application_normalizer/facade.py` | Generic multi-root consumer facade: namespace mounts + prefix-rule `material:binding` retarget overlay + provenance | `tests/test_aan_facade.py` |
| `convert_asset/asset_application_normalizer/batch.py` | Hash-bound batch admission driver (verify-before-run, per-candidate summary) | `tests/test_aan_batch.py` |
| `convert_asset/cli.py` | New `build-facade` and `workspace-profile` subcommands | end-to-end smoke verified |
| `docs/operations/workspace-profiling.md` | Runbook with the placement checklist (table depth vs row depth, aisle width, robot landing spot, interior embedding, exact scale publication, yaw by row orientation, not_applicable contract, facade pattern) | linked from operations README |

## Architecture notes

- `workspace/` sits beside AAN and reuses its conventions; AAN does not
  import it (one-way dependency), and `normalize-asset`'s main flow is
  unchanged.
- Facade/batch live inside AAN because they are admission-supporting
  producer tools; facade takes namespace mounts as parameters, no hardcoded
  `/world`/`/Root`/`/Render`.
- Heavy Isaac imports stay inside functions (repo lazy-import rule);
  `render.py` compose path stays PIL-only and import-clean.

## Verification

- `python -m pytest tests/ -q` -> all green (new workspace/facade/batch
  tests included).
- End-to-end CLI smoke: `build-facade` retargets and composes;
  `workspace-profile` emits a clean-verdict v0.1 profile.
