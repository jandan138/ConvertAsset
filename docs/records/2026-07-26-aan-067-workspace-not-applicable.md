# 2026-07-26 067 Workspace not_applicable (Geometric Incompatibility)

## Why this record exists

Scenario Forge validated profile-3 (north hood pair) in Isaac 4.1: package
check, GenManip visual_ready_gate, and workbench closeup passed, but the
overall scene_overview failed — remaining north-wall/fume-hood foreground
geometry occluded the eBench table, Lift2 robot, and both containers. They
asked for either `not_applicable` or a corrected profile, with no
consumer-side changes.

## Root-cause analysis (from their own scenario.yaml)

Their composer mapping is `task = source x scene_scale + scene_pose`
(scene_scale = 2.67626e-05 = 1/37365.6, identity rotation); the robot
spawns at a fixed -x offset of 1.26 m from the table in source frame.

1. **Profile-3 anchor error**: the anchor was the north hood pair center
   (y=372220), but the hood row is only 0.45 m deep (y 363812-380628)
   while the fixed eBench table is 2.645 m deep. Centered there, the
   table's back penetrated 1.09 m through the north wall face (y=380836).
   The robot camera sat 0.33 m from the wall, so the wall filled the
   overview frame — the reported occlusion.
2. **Wall-flush shift fails on aisle width**: placing the table back flush
   with the wall face pushes the table 2.2 m south, but the north aisle is
   only 1.88 m (interior island row at y 241927-293574). The table bites
   the island row and would need 6+ additional island groups inactivated
   (group_110/116/117/118/142/144...), destroying retained background.
3. **West wall fails identically**: the west aisle is 2.21 m < 2.345 m
   table width (west hood row x[-647364,-617866], nearest island column at
   x -535366).
4. **Interior islands remain unusable**: ~175 ungrouped loose counter-prop
   meshes; coverage would require anonymous mesh masks.

Conclusion: no rule-compliant 2.345 x 2.645 m placement exists in lab_067
without gutting retained background. The honest outcome is
`not_applicable`, which Scenario Forge explicitly offered as option 1.

## Delivered updates (`scenario-forge/outputs/scientific_workbench_workspace_profiles_20260724/`)

- `scientific_environment_067_workspace_profile.yaml` -> profile-4:
  `status: not_applicable` with the full four-point geometric evidence;
  previous assembly/anchor/clearance marked superseded.
- `workspace_profiles_manifest.json` -> profile-4 revision note; 067 entry
  records the aisle-width and penetration measurements.

## Claim boundary

- No USD, physics, robot, tabletop, or task-object pose changes anywhere;
  this is analysis-only.
- The profile-2 coordinate mapping (37365.6 units/m) remains valid and was
  the basis of all measurements here.
- 066/083/059 profiles are unaffected (their overviews passed).

## Verification

- Measurements computed from the composed source frame and verified
  against the delivered profile-3 scenario.yaml mapping.
- `python -m pytest tests/ -q` -> `674 passed, 4 skipped` (no code changes).
