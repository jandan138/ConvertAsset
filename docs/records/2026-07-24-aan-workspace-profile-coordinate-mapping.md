# 2026-07-24 Workspace Profile Coordinate Mapping (profile-2)

## Why this record exists

Scenario Forge reproduced a consumption failure for the profiled rooms:
anchor/clearance values are `source_composed` coordinates, but
`metersPerUnit=1.0` in the package USD does not explain the audited eBench
clearance (their 066 reproduction shrank the intended 2.45 x 2.75 x 3.06 m
clearance to ~0.210 x 0.235 x 0.262 m). They requested a sidecar-only fix:
an exact `coordinate_mapping` per profiled candidate, unit clarification,
and producer revision/git_commit sync. No LabUtopia USD/MDL/mesh, physics,
or packages were touched.

## Changes (delivery dir `scenario-forge/outputs/scientific_workbench_workspace_profiles_20260724/`)

| Candidate | `source_composed_units_per_meter` | Note |
|---|---|---|
| 066 | 19.146 | Audit-true value; consistent with the SF 2.45 x 2.75 x 3.06 m reproduction |
| 067 | **37365.6** (supersedes 31417) | Bench-local re-derivation: the profile-1 value mixed global room furniture into the counter band; bench vertices concentrate at 5.87k-6.67k above floor -27526.46 (25% of bench vertices), giving 37365.6 units/m. Anchor (`5873.05` counter band) and clearance AABB regenerated and re-audited: still zero non-shell intruders |
| 083 | 1.0 | Source composed frame is metric |
| 059 | 11.057 | Audit-true value; bench-local re-derivation within 3 percent |

Each profile YAML gains `coordinate_mapping` (`frame: source_composed`,
both `source_composed_meters_per_unit` and the reciprocal
`source_composed_units_per_meter`, plus `derivation`) and a
`unit_clarification` note: anchor/clearance values are source_composed
units, the legacy `*_m` names stay for schema compatibility and are
candidates for a future `*_su` rename.

The batch manifest gains `coordinate_mappings`, a `revision_note`, and its
producer revision/git_commit is synced to the delivery commit.

## Claim boundary

- Sidecar-only change: profiles, manifest, and this record; the four
  packages, sources, and evidence images from profile-1 are unchanged
  (067's evidence image still shows the same prims; only numbers were
  re-derived).
- 067's scale correction changes its anchor/clearance numbers; all other
  candidates' numbers are untouched.
- The mapping values are the exact scales the (re-)audits consumed, not
  the rounded prose approximations.

## Verification

- 067 coverage re-audit at 37365.6 units/m: only the room shell intersects
  the enlarged clearance AABB.
- `python -m pytest tests/ -q` -> `674 passed, 4 skipped` (no code changes).
