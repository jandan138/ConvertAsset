# 2026-05-21 GRScenes Reference Closure Plan

## Summary

Added a pure-Python reference-closure planner for the ACL/VLM GRScenes pilot.
This is the storage-safe replacement for scaling the earlier one-scene
split-level scratch mirror.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_reference_closure.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/reference_closure_plan.json`
- `tests/test_grscenes_vlm_reference_closure.py`
- `docs/superpowers/plans/2026-05-21-grscenes-reference-closure-plan.md`

## Files Updated

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- `docs/index.md`
- `docs/records/README.md`
- `docs/superpowers/README.md`

## Design Notes

- The planner reads `source_manifest.json` and `target_manifest.json`.
- It does not import `pxr`, `omni`, or Isaac Sim, and it does not open USD
  stages.
- It does not copy, hardlink, convert, render, or mutate any asset tree.
- Unique spatial targets are deduplicated by
  `(source_scene_id, object_instance_id, target_prim_path)`.
- Unique model actions are deduplicated by the parent directory of
  `resolved_model_path`.
- All planned source paths must stay inside the manifest benchmark source root,
  and all planned destination paths must stay inside the scratch root.
- Scene `source_usd`, `source_usd_variant`, scratch input USD, and
  `converted_usd` are revalidated by the planner. no-MDL commands are derived
  from the checked scratch input path instead of trusting manifest-provided
  command strings.
- Target-manifest source roots are checked against the source manifest to avoid
  mixing stale target records with a different scene/source selection.
- Model-internal symlinks are scanned and any target not covered by the selected
  scene/model actions is reported as an uncovered dependency.
- Each selected model root's `Materials` entry is classified as `symlink`,
  `pointer_file`, `missing`, `dir`, or `file`, because model-root-only planning
  can otherwise miss ordinary text pointer files and absent entries.

## Current Output

Command:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_reference_closure.py
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/reference_closure_plan.json
```

Current summary from `reference_closure_plan.json`, generated at
`2026-05-20T17:08:10.354908Z` by the command above:

- 40 episode records.
- 40 resolved episode records.
- 23 unique spatial targets.
- 17 duplicate episode-target records.
- 5 unique scenes.
- 23 unique selected model roots.
- 28 planned actions: 5 scene directories and 23 target model roots.
- 51 selected model files.
- 14 selected model symlinks.
- `Materials` entry pattern: 14 symlinks, 5 ordinary pointer files, 4 missing
  entries.
- 23 model roots requiring external material resources.
- 1 deduplicated required external resource root: split-level
  `home_scenes/Materials`.
- 1 uncovered symlink target category: scratch split-level
  `home_scenes/Materials`.
- `model_root_only_materialization_safe=false`.
- `material_closure_status=requires_material_dependency_resolution`.

## Interpretation

Plain version: the target model part is small enough to plan safely. The old
one-scene mirror exposed about 104G and 141,082 visible files; the selected
model-root plan sees only 51 model files plus 14 model symlinks for the current
23 targets.

This does not yet mean no-MDL can run on the closure. At least one selected
model contains `Materials -> ../../../../../Materials`, other selected models
use ordinary text pointer files, and some selected roots have no `Materials`
entry even though the USDs may author `./Materials/...` paths. A follow-up
material-dependency planner must decide which split-level material files are
needed. The correct next step is not to copy all `home_scenes/Materials`; it is
to resolve the material files used by the selected model USDs and plan only
that dependency subset.

## Verification

Fresh checks run during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_reference_closure.py
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_reference_closure.py
```

Additional read-only review reported the same qualitative risk using
`UsdUtils.ComputeAllDependencies`: unresolved dependencies were material assets
that recover from split-level `home_scenes/Materials`. That diagnostic was not
committed as a standalone log in this change, so the committed evidence remains
the pure-Python `reference_closure_plan.json`; the USD dependency scan should be
formalized as the next material-dependency closure artifact.

Full-repo verification is tracked in the final commit notes for this change.

## Open Work

- The follow-up material dependency planner has been added in
  `2026-05-21-grscenes-material-dependency-closure-plan.md`.
- After the material dependency closure is planned, implement a
  materializer that hardlinks/copies the planned closure into scratch.
- Run no-MDL on scratch inputs and regenerate `render_manifest.json` with
  `--require-converted`.
