# Reagent-bottle 45/40 plug original-SimReady admission

Date: 2026-09-19.

## Outcome

ConvertAsset admitted the matched `manual_glassware_v1` reagent-bottle plug as
a source-bound original-SimReady dynamic package. The vessel itself was already
admitted on 2026-08-19; this run does not rebuild that package.

Output root:
`outputs/scientific_workbench_reagent_bottle_pair_20260919/`

- Asset id: `scientific_workbench_reagent_bottle_plug_45_40_original_simready`
- Package:
  `packages/reagent_bottle_plug_45_40_original_simready`
- Source: hash-locked `manual_glassware_v1/simready/reagent_bottle_plug_45_40.usdc`
  SHA-256 `ea6f4b5f13f7f55c6c8bb53073f9afde8e6a6f1131afffffda462d1e8b3ce612`
- Archive SHA-256
  `731eb7eb539377b7c1fec015065c256d932e13b548d39f8697ec9b1444074afd`
- `normalize-asset` `overall_status: pass` (static + Isaac 4.1 runtime smoke)
- Observed kit: `4.1.0-rc.7+4.1.14801.71533b68.gl`
- Visual policy: `preserve_original_simready` (no webpage glass override)

The producer pair-fit evidence remains Isaac Sim 4.5 only. This package does
not inherit plug-seat, pull/insert, liquid, or robot-policy success.

Matched vessel package (unchanged):
`outputs/scientific_workbench_glass_web_standard_20260819/packages/reagent_bottle_90x55_original_simready`

Purchase-view copies of the producer assembled/exploded renders and the
reference photograph are under `purchase_views/`.
