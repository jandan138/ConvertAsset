# 2026-05-21 GRScenes Targeted Materialization

## Summary

Added a storage-safe targeted materializer for the ACL/VLM GRScenes pilot. It
turns the reference closure plus material dependency closure into a dry-run/apply
plan without mirroring full split-level `models/` or `Materials/` trees.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_targeted_closure.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/targeted_materialization_report.json`
- `tests/test_grscenes_vlm_targeted_materialization.py`
- `docs/superpowers/plans/2026-05-21-grscenes-targeted-materialization.md`

## Design Notes

- The script is pure Python and imports no `pxr`.
- The default CLI mode is dry-run. The only write mode is explicit `--apply`.
- It consumes:
  - `reference_closure_plan.json`
  - `material_dependency_closure_plan.json`
- It plans only:
  - 5 selected scene directories.
  - 23 selected model roots.
  - 68 selected material files.
  - 10 scene-local `models`/`Materials` entry repairs.
  - 9 model-root `Materials` entry repairs.
- Scene-local `models` and `Materials` entries are ordinary pointer files in
  the source tree. The materializer replaces only scratch-side copies with
  relative symlinks so USD resolution can cross into scratch split-level
  resources.
- Model-root `Materials` pointer/missing entries are also repaired only in
  scratch.
- Source and destination paths are checked against source/scratch roots, and
  relative symlink targets must resolve inside the scratch root.
- Before `--apply` copies a selected scene/model tree, all internal symlinks
  are projected to their scratch destination and rejected if they would resolve
  outside scratch.
- Existing scratch tree destinations are not trusted by name alone: their
  structure, symlink text, file sizes, and file contents must match the source
  tree, except for explicitly repairable scratch-side entries.
- Existing material files are content-compared with `filecmp.cmp(...,
  shallow=False)` so same-size stale files are rejected.

## Current Output

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_targeted_closure.py
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/targeted_materialization_report.json
```

Current dry-run summary:

- `dry_run=true`
- 115 planned actions.
- 5 scene directory actions.
- 23 model-root actions.
- 68 material file actions.
- 10 scene entry repairs.
- 9 model-root material entry repairs.
- 0 created actions.
- 0 existing actions.
- `resource_tree_count=0`
- `known_scene_dependency_gap=true`
- `reported_at_utc` records when the dry-run report was produced. The report
  intentionally does not use `materialized_at_utc` when `dry_run=true`.

## Important Limitation

Plain version: this is the correct next storage-safe step, but it is not a
claim that whole-scene no-MDL conversion is ready.

The closure is target-object focused. A read-only USD probe found that repairing
scene-local `models` makes selected model roots resolvable, but the full scene
still authors many unselected `models/...` references. The same probe also saw
scene-level material references such as `Materials/DayMaterial.mdl` and
`Materials/Textures/Day.png`, which are outside the 68 model-root material
files.

Therefore the next experiment decision is:

- either build a broader scene dependency closure for whole-scene conversion;
- or build target-object/cropped render stages where unresolved unselected scene
  references are intentionally excluded.

Do not run no-MDL on the scratch scene and cite it as whole-scene evidence until
that decision is implemented and documented.

## Verification

Fresh checks run during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_targeted_materialization.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_targeted_closure.py
```

Initial review found two apply-mode guardrail gaps: copied tree symlink targets
were not projected/validated before copy, and existing scratch destinations were
accepted too loosely. The tests now cover symlink escape, incomplete existing
trees, same-size stale material files, destination escape, repair target escape,
and dry-run timestamp naming. The targeted test file currently reports 11
passing tests.

Full-repo verification is tracked in the final commit notes for this change.
