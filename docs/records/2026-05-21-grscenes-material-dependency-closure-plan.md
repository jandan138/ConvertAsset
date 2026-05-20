# 2026-05-21 GRScenes Material Dependency Closure Plan

## Summary

Added a read-only material dependency closure planner for the ACL/VLM GRScenes
pilot. It turns the previous reference-closure model-root plan into a concrete
file-level `Materials` subset and records the remaining scratch-side entry
repairs needed before no-MDL can run.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_material_dependency_closure.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/material_dependency_closure_plan.json`
- `tests/test_grscenes_vlm_material_dependency_closure.py`
- `docs/superpowers/plans/2026-05-21-grscenes-material-dependency-closure-plan.md`

## Files Updated

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- `docs/records/2026-05-21-grscenes-reference-closure-plan.md`
- `docs/records/README.md`
- `docs/superpowers/README.md`

## Design Notes

- The planner consumes `reference_closure_plan.json`.
- It defaults to pxr/`UsdUtils.ComputeAllDependencies`, but keeps `pxr` imports
  lazy so normal unit tests can import the module without Isaac startup.
- A text backend exists for unit tests and small fake USD/MDL fixtures.
- It does not copy, hardlink, convert, render, or mutate any asset tree.
- Resolved paths from symlinked `model_root/Materials` entries are realpath
  normalized back to split-level `home_scenes/Materials`.
- Unresolved paths are recoverable only by taking the lexical tail under
  `model_root/Materials/<tail>` and checking `split_root/Materials/<tail>`.
- Material source files must resolve inside split-level `Materials`, and all
  planned destinations must stay inside the scratch root.
- Pointer-file and missing model-root `Materials` entries are represented as
  explicit scratch-side symlink repair actions.

## Current Output

Command:

```bash
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_material_dependency_closure.py \
  --dependency-backend pxr
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/material_dependency_closure_plan.json
```

Current summary from `material_dependency_closure_plan.json`, generated at
`2026-05-20T18:03:34.938417Z`:

- 23 selected model roots scanned.
- 70 resolved dependency paths from USD.
- 61 unresolved dependency paths from USD, all recovered from split-level
  `home_scenes/Materials`.
- 68 deduplicated material file actions.
- 56,405,072 total source bytes.
- File types: 20 `.mdl`, 42 `.png`, 6 `.jpg`.
- 0 missing material assets.
- 0 unresolved non-material assets.
- 9 model-root `Materials` entry repair actions: 5 pointer files and 4 missing
  entries.
- `safe_to_materialize_selected_materials=true`.
- `ready_for_nomdl_after_material_file_actions=false`.
- `material_closure_status=selected_material_dependencies_resolved_with_entry_repairs_required`.

## Interpretation

Plain version: the big `home_scenes/Materials` directory no longer needs to be
mirrored. For the current 23 targets, the material file payload is 68 files
instead of the full split-level tree.

The remaining trap is not file size; it is path shape. Five selected model
roots store `Materials` as an ordinary pointer file and four have no
`Materials` entry. After material files are placed in scratch, the materializer
must repair those nine roots so `./Materials/...` resolves to scratch
split-level `Materials`. Running no-MDL after only materializing the 68 files
would still fail for those roots.

## Verification

Fresh checks run during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_material_dependency_closure.py
./scripts/isaac_python.sh paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_material_dependency_closure.py --dependency-backend pxr
python -m json.tool paper/shared/evidence/raw/grscene_vlm_grounding/material_dependency_closure_plan.json >/tmp/material_dependency_json_check.out
```

The pxr run emitted 287 USD resolver warning lines to stderr for unresolved
`model_root/Materials/...` paths. These warnings are expected and now reflected
structurally in the JSON summary as `usd_dependency_unresolved=9` and
`scratch_materials_entry_repair_required=9`.

Full-repo verification is tracked in the final commit notes for this change.

## Open Work

- Implement the targeted scratch materializer using the reference-closure scene
  and model actions, the 68 material file actions, and the 9 entry repair
  actions.
- Run no-MDL on scratch scene USDs only.
- Regenerate `render_manifest.json --require-converted`, then run the paired
  render and visual QA gates.
