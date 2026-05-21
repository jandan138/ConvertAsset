# 2026-05-21 GRScenes Full Materialization And Closure Runner

## Summary

Added the next guarded step for the ACL/VLM GRScenes route: a full scratch
materializer dry-run and a closure-aware multi-root runner report.

Plain version: the full dependency scan is no longer the blocker. The current
blocker is now physical scratch materialization and scratch cleanliness. We can
plan exactly what would be hardlinked into scratch, and the runner can consume
the full closure report, but no full no-MDL conversion has run yet.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json`
- `tests/test_grscenes_vlm_full_scratch_materializer.py`
- `docs/superpowers/plans/2026-05-21-grscenes-full-materialization-and-closure-runner.md`

## Files Modified

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json`
- `tests/test_grscenes_vlm_full_nomdl_runner.py`
- experiment and raw README files for the paper evidence directory

## Materializer Behavior

The full materializer consumes `full_nomdl_scratch_plan.json`. Its default mode
is dry-run, so it writes only the JSON report and creates no asset files.

Current checked-in dry-run summary:

- `dry_run=true`.
- 103 planned tree actions.
- 138 planned scene-entry repairs.
- 99 ignored `convert_no_mdl` actions.
- 0 existing planned no-MDL outputs.
- 0 existing top-level scratch inputs.
- 99 missing top-level scratch inputs.

Safety behavior:

- rejects source/scratch nesting;
- rejects report output under source or scratch;
- validates tree action sources stay under source and destinations stay under
  scratch;
- validates projected symlink targets before copy/hardlink;
- repairs only scratch-side `models`/`Materials` pointer files into relative
  symlinks;
- rejects stale planned scratch `_noMDL` outputs before real materialization;
- rejects source-tree `_noMDL` sidecars before real materialization so stale
  converted outputs are not hardlinked into scratch;
- supports `hardlink` and `copy`, but the full route should use hardlinks under
  the current quota.

## Runner Closure Gate

`run_full_nomdl_multi_root.py` now accepts:

```bash
--closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json
--materialization-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json
```

The runner validates the closure report as pure JSON before any no-MDL import.
It requires matching roots, matching source plan status, matching selected jobs,
`scan_truncated=false`, no missing dependencies, no outside-source references,
and no recursive output collisions before it clears the dependency closure
blockers. It also validates materialization reports and clears
`scratch_cleanliness_not_verified` only when the report is non-dry-run, has zero
existing no-MDL outputs, and reports zero missing top-level scratch inputs.

Current checked-in runner report:

- `apply_ready=false`.
- Satisfied blockers:
  - `single_process_multi_root_runner_missing`;
  - `single_process_multi_root_runner_closure_report_not_consumed`;
  - `whole_scene_dependency_closure_not_scanned`;
  - `recursive_nomdl_output_collision_scan_missing`.
- Remaining blockers:
  - `scratch_cleanliness_not_verified`;
  - `scratch_inputs_missing`;
  - `scratch_root_missing`.

The current materialization report is consumed but remains `dry_run=true`, so
it intentionally does not clear scratch cleanliness.

## Storage Notes

Use `/cpfs/user/zhuzihou/assets/zzh-grscenes` as the clean source dataset and
`/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521` as the
operation scratch root. Keep the scratch root named like a work tree, not like a
clean dataset.

Hardlinks are acceptable because source and scratch are under the same
filesystem device and ConvertAsset no-MDL writes sibling sidecar outputs rather
than editing inputs in place. Hardlinks still share input inodes, so they are
not acceptable for any workflow that mutates input files in place. Copy mode is
not recommended without a fresh storage estimate under the 1.6 TiB quota.

## Next Gate

Before real no-MDL conversion:

1. Run quota/source preflight and a source `_noMDL` pollution scan.
2. Run real full scratch materialization with `--apply --copy-mode hardlink`.
3. Rerun the materializer to prove idempotency.
4. Rerun `plan_full_dependency_closure.py --max-usd-layers 0` after
   materialization and require `scratch_input_missing_count=0`.
5. Regenerate the closure-aware runner report and require `apply_ready=true`
   before using `--apply`.

## Verification

Fresh checks during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_scratch_materializer.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_runner.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json
```

The materializer tests report 13 passing tests. The runner tests report 19
passing tests.
