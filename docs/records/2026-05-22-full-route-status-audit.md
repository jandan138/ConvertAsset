# 2026-05-22 Full-route status audit

## Scope

This audit checks the first three full-route gates in the ACL/VLM plan:

1. full dependency scan;
2. full scratch materialization;
3. full no-MDL conversion and source-cleanliness verification.

## Current evidence

The current repository evidence shows these gates are already complete for the planned 99 `start_result_raw.usd` roots.

### Full dependency scan

`paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json` records:

- `reachable_source_usd_count=85705`;
- `resolved_usd_dependency_count=89484`;
- `usd_layer_scan_limit=null`;
- `scan_truncated=false`;
- `unscanned_usd_queue_count=0`;
- `missing_dependency_count=0`;
- `outside_source_root_ref_count=0`;
- `output_collision_count=0`;
- `scratch_input_missing_count=0`.

The scan CLI now defaults to `--max-usd-layers 0`, so the documented no-argument command is a full no-cap scan. Positive layer limits are diagnostic-only.

### Full scratch materialization

`paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json` records:

- `dry_run=false`;
- `existing_tree_count=103`;
- `existing_scene_entry_count=138`;
- `top_level_scratch_input_exists_count=99`;
- `top_level_scratch_input_missing_count=0`.

### Full no-MDL conversion

`paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json` records:

- `status=completed_full_grscenes_nomdl_multi_root_run`;
- `dry_run=false`;
- `apply_ready=true`;
- `processor_done_count=89583`;
- `safety.remaining_apply_blockers=[]`.

`paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_apply_verification_report.json` records:

- `passed=true`;
- `existing_top_output_count=99`;
- `missing_top_output_count=0`;
- `source_pollution_count=0`;
- `source_pollution_scan_truncated=false`;
- `blockers=[]`.

## Boundary

This audit proves the full route for the planned 99 raw-scene roots, not every possible GRScenes USD variant. It does not prove rendered visual quality or VLM behavior. Those remain the next gates.

## Next gate

Continue with paired rendering:

- render original/no-MDL pairs for the selected targets and stress expansion candidates;
- run projection QA and independent visual review;
- rebuild the stress manifest only after render/projection/review pass;
- then run canonical VLM predictions and scoring.

Plain version: the old "5000 scanned, 80705 left" state is no longer current. The route is ready to spend effort on images and VLM evaluation.
