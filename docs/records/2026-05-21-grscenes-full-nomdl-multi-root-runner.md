# 2026-05-21 GRScenes Full no-MDL Multi-Root Runner

## Summary

Added a guarded single-process no-MDL runner shell for the full GRScenes scratch
route. It closes the "runner is missing" part of the previous full scratch plan
without converting any assets by default.

Plain version: this record captures the initial runner-shell checkpoint. It is
now superseded by `2026-05-21-grscenes-full-nomdl-apply.md`, where the 99-root
apply run is recorded as completed and verified.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json`
- `tests/test_grscenes_vlm_full_nomdl_runner.py`
- `docs/superpowers/plans/2026-05-21-grscenes-full-nomdl-multi-root-runner.md`

## Design Notes

- The dry-run/report path is pure Python and imports no `pxr` and no
  `convert_asset.no_mdl` modules.
- The report consumes `full_nomdl_scratch_plan.json`.
- It can also consume `full_dependency_closure_report.json` with
  `--closure-report` as a pure-JSON apply gate.
- It can consume `full_nomdl_scratch_materialization_report.json` with
  `--materialization-report` as scratch materialization/cleanliness evidence.
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
- It does not itself scan recursive dependency outputs. When
  `--closure-report` is supplied, it validates that the broader USD dependency
  closure has completed, has no missing/outside dependencies, and has no
  recursive no-MDL output collisions.
- The apply function is present but gated. It refuses to run while any blocker
  remains and also requires a closure report before importing no-MDL.
  `scratch_cleanliness_not_verified` is cleared only by a non-dry-run clean
  materialization report. Only after the report says `apply_ready=true` does it
  lazily import
  `convert_asset.no_mdl.processor`, set `RUNTIME_ONLY_NEW_USD=True`, create one
  `Processor`, and reuse that instance across all selected roots.

## Historical Dry-Run Output

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py \
  --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json \
  --materialization-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json
```

Historical dry-run summary at this checkpoint:

- 99 planned jobs.
- `dry_run=true`.
- `apply_ready=true`.
- `single_process_multi_root_runner_missing`,
  `single_process_multi_root_runner_closure_report_not_consumed`,
  `whole_scene_dependency_closure_not_scanned`, and
  `recursive_nomdl_output_collision_scan_missing`, and
  `scratch_cleanliness_not_verified` are listed under
  `satisfied_apply_blockers`.
- Remaining blockers: none.
- `source_usd_missing_count=0`.
- `scratch_input_missing_count=0`.
- `top_level_output_collision_count=0`.

## Important Limitation

This runner shell was the green button for the no-MDL conversion gate. The
full apply has since been run under Isaac Python and is tracked in
`2026-05-21-grscenes-full-nomdl-apply.md`.

## Verification

Fresh checks run during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_runner.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json --materialization-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json
```

The runner tests reported 19 passing tests at this checkpoint. Full-repo verification is tracked in
the final commit notes for this change.
