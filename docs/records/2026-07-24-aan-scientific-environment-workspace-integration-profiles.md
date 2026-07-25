# 2026-07-24 Scientific Environment Workspace Integration Profiles

## Why this record exists

Scenario Forge validated that 084's complete island (`/World/group_078`)
hosts the fixed eBench workbench naturally, and requested source-bound
workspace integration profiles for 066, 067, 081, 083, 085 (059 optional as
a bonus). This is analysis-only delivery: no LabUtopia USD/MDL/mesh was
modified, and no collider, rigid body, mass/inertia, or PhysX suppression
was authored.

## Method

1. Measured the validated 084 pattern: 12 identical islands, the replaced
   one being a complete 1.59 x 3.81 m assembly at a free aisle-adjacent
   spot; the eBench workbench footprint is 2.345 x 2.645 m (table package
   bbox, top 0.773 m).
2. Per candidate, computed composed world-frame bboxes from mesh points
   (Gf row-vector convention `p @ M`), identified counter-band assemblies,
   and ran a workspace overlap audit: the eBench-footprint clearance AABB at
   the proposed anchor must intersect only (a) the replaced assembly roots
   and (b) the room shell (floor/walls/ceiling, kept).
3. Candidates whose coverage would require ungrouped loose-mesh prims were
   returned as `not_applicable` per the request's no-guess-patching rule.

## Results (delivered to `scenario-forge/outputs/scientific_workbench_workspace_profiles_20260724/`)

| Candidate | Status | Assembly roots | Notes |
|---|---|---|---|
| 066 | profiled | `/World/group_111` | Zero non-shell intruders; 3 sibling islands stay |
| 067 | profiled | `/World/group_205` + `/World/group_206` | The two benches are contiguous at y=9658.94; single-group removal left the sibling crossing the workspace (the reported issue); both together pass the audit |
| 081 | **not_applicable** | — | Dense flat rows (1.19 x 8.31 m); clearance hits ungrouped cabinets/props (e.g. `mesh_046`) |
| 083 | profiled | `/World/group_025` + `026` + `027` | Contiguous three-bench row; two 0.58 m floor-drain decals (`mesh_164`, `mesh_167`) graze the clearance front edge and are listed as optional inactives |
| 085 | **not_applicable** | — | Single 1.50 x 0.90 m island smaller than the workbench; clearance hits ~48 ungrouped loose props |
| 059 | profiled (bonus) | `/World/group_063` + `064` + `073` + `241` | Island + interleaved bench unit + 2 aisle stools; all complete group roots |

Each profile YAML records source hash (request pins verified unchanged),
scope `/World`, producer revision, anchor prim + `anchor_xyz_m` (source
composed frame, `metersPerUnit=1.0`), inactive roots, clearance AABB, and
background keep rule. Before/after Isaac 4.1 source-side renders for the
four profiled candidates are under `evidence/` (inactivation verified by
pixel-diff: 066 78.7%, 067 24.4%, 083 21.4%, 059 23.2% changed pixels).

## Claim boundary

- Anchors/AABBs are in the source composed frame; Scenario Forge owns the
  scene-level pose/scale mapping (as in the validated 084 scenario).
- `not_applicable` results are honest negatives, not failed admissions:
  the geometry facts are recorded in the profiles.
- Evidence renders use the source USD directly (no package conversion);
  renders are visual evidence only and do not re-qualify the packages.

## Verification

- Overlap audit script: zero non-shell intruders for all profiled sets.
- Root .usd hashes re-verified against the batch admission request pins.
- `python -m pytest tests/ -q` -> `674 passed, 4 skipped` (no code changes).
