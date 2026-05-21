# 2026-05-21 GRScenes Full Dependency Closure

## Summary

Added a read-only authored USD composition dependency and recursive no-MDL
output closure planner for the full GRScenes scratch route. It answers the next
engineering question after the multi-root runner: if the 99 planned raw scene
roots are converted through one shared `Processor`, what dependency USDs and
`_noMDL` sidecars will be involved, and are there obvious missing refs or
output collisions before any asset writes?

Plain version: this is still not a conversion run. It is a safety scan for the
full-route conversion story.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_dependency_closure.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json`
- `tests/test_grscenes_vlm_full_dependency_closure.py`
- `docs/superpowers/plans/2026-05-21-grscenes-full-dependency-closure.md`

## Design Notes

- The module imports no `pxr` at import time. The Sdf backend is loaded lazily
  only when the CLI scans real USD layers.
- The default report consumes
  `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_plan.json`.
- The scan is read-only: it does not copy, hardlink, convert, render, or write
  under the immutable source root or the planned scratch root.
- Authored `models/...` and `Materials/...` paths from scene-local USDs are
  recovered to split-level GRScenes resource roots before scratch mapping when
  they appear as USD composition dependencies.
- Every reachable source USD in the scanned closure is mapped to the planned
  scratch tree, then its expected `*_noMDL.usd` output is checked for:
  existing base sidecars, timestamped sidecars, and duplicate planned outputs.
- Missing scratch inputs are counted across both top-level roots and recursive
  dependency USDs, so a partial scratch tree cannot clear the apply blocker by
  materializing only the 99 root scenes.
- The output JSON caps large lists by `max_report_records` while preserving
  complete counts in `summary` and `report_limits`.

## Current Output

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_dependency_closure.py
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json
```

Current checked-in summary:

- 99 planned jobs.
- 85,705 reachable source USD layers scanned.
- 89,484 resolved USD dependency records.
- 0 missing dependencies.
- 0 outside-source references.
- 85,705 expected no-MDL outputs: 99 top-level outputs and 85,606 recursive
  dependency outputs.
- 0 existing expected outputs, 0 timestamped output siblings, and 0 duplicate
  planned outputs.
- `unique_usd_enqueue_count=85705`.
- `duplicate_usd_dependency_enqueue_count=3878`.
- `max_usd_queue_depth=85606`.
- `scratch_root_exists=false`.
- `top_level_scratch_input_missing_count=99`.
- `recursive_scratch_input_missing_count=85606`.
- `scratch_input_missing_count=85705`.
- `scan_truncated=false`.
- `unscanned_usd_queue_count=0`.
- `safe_to_run_multi_root_nomdl=false`.

## Important Limitation

The dependency/output scan is now complete for USD composition arcs. It marks
`whole_scene_dependency_closure_not_scanned` and
`recursive_nomdl_output_collision_scan_missing` as satisfied. This still does
not make conversion runnable, because the full scratch tree has not been
materialized and scratch cleanliness has not been verified.

The Sdf backend scans authored composition dependencies. It is enough for the
recursive USD sidecar-output gate, but it is not a standalone proof that all
shader, material, or texture asset attributes are closed. Those remain covered
by the separate material-dependency closure route unless they appear as
composition arcs in this report.

Timestamped `_noMDL_*` siblings are intentionally treated as conservative
collision signals. This may over-block later apply attempts, but it is safer
than ignoring stale generated sidecars.

The remaining blockers are:

- `single_process_multi_root_runner_closure_report_not_consumed`, because the
  multi-root runner has not yet consumed this closure report as an apply gate;
- `scratch_cleanliness_not_verified`;
- `scratch_root_missing`;
- `scratch_inputs_missing`.

## Pitfall Recorded

An earlier uncapped diagnostic report was too large because GRScenes produces
tens of thousands of dependency and queue records. The production report keeps
the complete counts but caps long record arrays. Use `summary` and
`report_limits` for paper/engineering decisions, and use the capped arrays only
as debugging samples.

## Next Gate

To advance the ACL material-generalization experiment, the full route now needs
these engineering moves:

- materialize the full scratch root and verify scratch cleanliness;
- teach the multi-root runner to consume the dependency closure report rather
  than only the original scratch plan.

Only after those gates are closed should a guarded `--apply` no-MDL conversion
run be used as paper evidence.

## Verification

Fresh checks run during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_dependency_closure.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_dependency_closure.py
```

The closure tests report 8 passing tests. Full-repo verification is tracked in
the final commit notes for this change.
