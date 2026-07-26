# 2026-07-26 067 Workspace Re-Profile (North Hood Pair)

## Why this record exists

Scenario Forge consumed the profile-2 067 placement (west-wall pair
`/World/group_205 + /World/group_206`): package/runtime gates and the
workspace closeup passed, but the Isaac 4.1 overview failed — the fixed
eBench workspace sat at the equipment-row edge, so the robot faced a blank
white wall and target vessels were unreadable. They asked for a re-profiled
assembly/anchor/clearance or an honest `not_applicable`, with no
consumer-side hiding/collider/camera workarounds and no USD/pose changes.

The request was assessed as reasonable: profile-1/2 optimized coverage
completeness but never verified embedding quality (what the robot/camera
faces). This is the fix.

## Analysis

1. Floor-plan mapping of lab_067: every tall fume-hood row is wall-adjacent
   (west wall x=-646k or north wall y=380k); the failed pair sits at the
   south-west corner area, blank walls behind.
2. Interior island rows (20/21/22-mesh groups, y 190k-293k) were rejected:
   their counters are covered by ~175 ungrouped loose prop meshes, so
   coverage would require the forbidden anonymous mesh masks.
3. The north fume-hood pair `/World/group_223 + /World/group_225`
   (contiguous at x=-303100, 2.7 m clear of neighboring pairs) passes the
   overlap audit: no furniture intruders; only flat floor-level items
   intersect the clearance — two 1.85 x 4.0 m floor mats, nine paper-thin
   decals, and one 0.5 x 0.5 m tray group — all listed as optional
   inactives with full prim paths (same class as the 083 floor drains).
4. Source-side Isaac 4.1 render of the cleared spot confirms the
   background: windowed north wall (two daylight windows), green storage
   cabinet, and lab counters on both sides — no blank wall.

## Delivered updates (`scenario-forge/outputs/scientific_workbench_workspace_profiles_20260724/`)

- `scientific_environment_067_workspace_profile.yaml` -> profile-3:
  assembly `[/World/group_223, /World/group_225]`, anchor
  `(-144132.29, 372220.08, 272.66)` (source_composed, 37365.6 units/m),
  clearance AABB `[-189905.15, 320842.38, -27526.46]` ..
  `[-98359.43, 423597.78, 82476.98]`, 12 optional inactive paths, and a
  background note documenting the verified windowed-wall embedding.
- Evidence image `evidence/scientific_environment_067_workspace.png`
  replaced with the north-pair before/after render.
- `workspace_profiles_manifest.json` -> profile-3 revision note and
  assembly roots for 067.

## Claim boundary

- Numbers are source_composed coordinates at the profile-2 mapping
  (37365.6 units/m); no asset, package, robot, table, or task-object pose
  changes were made anywhere.
- The optional inactives are flat floor/counter items that may also stay
  active under the workbench base; they are explicit paths, not masks.
- The overview composition is evidenced by a source render from the
  south of the pair; Scenario Forge owns the final GenManip camera QA.

## Verification

- Overlap audit at the north pair: zero furniture intruders.
- Pixel-level before/after render difference confirms inactivation.
- `python -m pytest tests/ -q` -> `674 passed, 4 skipped` (no code changes).
