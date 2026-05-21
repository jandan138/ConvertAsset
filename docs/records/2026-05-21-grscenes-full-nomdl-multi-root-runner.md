# 2026-05-21 GRScenes Full no-MDL Multi-Root Runner

## Summary

Added a guarded single-process no-MDL runner shell for the full GRScenes scratch
route. It closes the "runner is missing" part of the previous full scratch plan
without converting any assets by default.

Plain version: we now have the code shape needed to run 99 scratch roots through
one Python process and one `Processor` instance later. The current checked-in
run is still a dry-run report, not converted-scene evidence.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json`
- `tests/test_grscenes_vlm_full_nomdl_runner.py`
- `docs/superpowers/plans/2026-05-21-grscenes-full-nomdl-multi-root-runner.md`

## Design Notes

- The dry-run/report path is pure Python and imports no `pxr` and no
  `convert_asset.no_mdl` modules.
- The report consumes `full_nomdl_scratch_plan.json`.
- It validates:
  - source/scratch root nesting;
  - `source_usd` paths stay inside source root;
  - `scratch_input_usd` and `expected_top_output_usd` stay inside scratch root;
  - report `--out` is not written into source or scratch asset trees.
- It scans only planned top-level no-MDL outputs:
  - existing expected outputs;
  - timestamped siblings such as `<stem>_noMDL_*.usd`;
  - duplicate planned outputs.
- It recomputes each job's current `blocked_by` list from the run report and
  preserves the source plan's older blockers as `source_plan_blocked_by`.
- It does not scan recursive dependency outputs, because those require the
  broader USD dependency closure that is still a separate gate.
- The apply function is present but gated. It refuses to run while any blocker
  remains. Only after the report says `apply_ready=true` does it lazily import
  `convert_asset.no_mdl.processor`, set `RUNTIME_ONLY_NEW_USD=True`, create one
  `Processor`, and reuse that instance across all selected roots.

## Current Output

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json
```

Current checked-in summary:

- 99 planned jobs.
- `dry_run=true`.
- `apply_ready=false`.
- `single_process_multi_root_runner_missing` is listed under
  `satisfied_apply_blockers`.
- Remaining blockers:
  - `whole_scene_dependency_closure_not_scanned`
  - `recursive_nomdl_output_collision_scan_missing`
  - `scratch_cleanliness_not_verified`
  - `scratch_root_missing`
  - `scratch_inputs_missing`
- `source_usd_missing_count=0`.
- `scratch_input_missing_count=99`.
- `top_level_output_collision_count=0`.

## Important Limitation

This runner shell is deliberately not a green button. It exists so the future
conversion step can deduplicate recursive dependencies through one shared
`Processor.done` map. The current scratch root has not been materialized, so all
99 planned scratch inputs are missing. Whole-scene dependency closure and
recursive no-MDL output collision scanning are also still missing.

Do not run `--apply` for paper evidence until:

- scratch scene/resource materialization exists for the full route;
- USD dependency closure proves no missing or outside-source references;
- recursive no-MDL output collisions are known;
- the dry-run report says `apply_ready=true`.

## Verification

Fresh checks run during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_runner.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py
```

The runner tests report 10 passing tests. Full-repo verification is tracked in
the final commit notes for this change.
