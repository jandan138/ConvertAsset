# 2026-05-21 GRScenes Full Materialization And Closure Runner

## Summary

Added the next guarded step for the ACL/VLM GRScenes route: full scratch
materialization, post-materialization dependency closure, and a closure-aware
multi-root runner report.

Plain version: this record captures the pre-apply gate that made the full
conversion safe to start. It is now superseded by
`docs/records/2026-05-21-grscenes-full-nomdl-apply.md`, where the full no-MDL
apply is recorded as completed and verified.

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
is dry-run, but the current report records the real hardlink materialization and
an idempotency rerun.

Current checked-in summary:

- `dry_run=false`.
- 103 existing tree actions on the idempotency rerun.
- 138 existing scene-entry repairs on the idempotency rerun.
- 99 ignored `convert_no_mdl` actions.
- 0 existing planned no-MDL outputs.
- 99 existing top-level scratch inputs.
- 0 missing top-level scratch inputs.

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

Pre-apply runner report at this checkpoint:

- `apply_ready=true`.
- Satisfied blockers:
  - `single_process_multi_root_runner_missing`;
  - `single_process_multi_root_runner_closure_report_not_consumed`;
  - `whole_scene_dependency_closure_not_scanned`;
  - `recursive_nomdl_output_collision_scan_missing`;
  - `scratch_cleanliness_not_verified`.
- Remaining blockers: none.

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

## Superseded Next Gate

At this checkpoint, the next gate was the guarded no-MDL conversion:

```bash
PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py \
  --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json \
  --materialization-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json \
  --apply
```

That command has now completed successfully. Current apply evidence lives in
`paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json`
with `status=completed_full_grscenes_nomdl_multi_root_run` and in
`paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_apply_verification_report.json`
with `passed=true`.

Use the Isaac Python wrapper for apply commands, because they import
`convert_asset.no_mdl` and `pxr` after the readiness gate.

Operational pitfall: when the wrapper executes a script by path,
`sys.path[0]` is the experiment script directory, not the repository root. The
runner therefore adds the project root to `sys.path` immediately before the
lazy no-MDL import. Without that guard, the gated apply command fails before
conversion with `ModuleNotFoundError: No module named 'convert_asset'`.

After the apply command finishes, run the pure-Python post-apply verifier:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/verify_full_nomdl_apply.py
```

It writes
`paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_apply_verification_report.json`
and checks that the runner report is non-dry-run evidence, top-level outputs
exist under scratch, result paths match expected outputs, and the immutable
source tree has no `_noMDL` USD sidecars.

## Verification

Fresh checks during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_scratch_materializer.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_runner.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_apply_verifier.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json --materialization-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json
```

The materializer tests report 14 passing tests. The runner tests report 21
passing tests. The post-apply verifier tests report 11 passing tests.
