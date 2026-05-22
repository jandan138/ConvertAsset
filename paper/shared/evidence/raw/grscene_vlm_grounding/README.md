# GRScenes VLM Grounding Raw Outputs

This directory is reserved for the ACL-oriented VLM grounding pilot.

Expected files:

- `source_manifest.json`: selected source scenes and episode records with provenance, scratch paths, and current mapping status.
- `target_manifest.json`: resolved episode targets with USD prim paths, candidate prims, model provenance, and world-space bboxes for later camera placement.
- `render_manifest.json`: paired original/no-MDL render plan/jobs with planned output image paths, scene, camera, target, and prompt metadata.
- `scratch_materialization_report.json`: dry-run or execution report for mirroring selected benchmark scenes and split-level resources into the no-MDL scratch tree.
- `reference_closure_plan.json`: planner-only target/reference closure artifact that lists selected scene directories, selected model roots, and unresolved symlink/material dependency gaps.
- `material_dependency_closure_plan.json`: planner-only material subset artifact that lists the exact split-level `Materials` files and model-root `Materials` entry repairs needed by the selected targets.
- `targeted_materialization_report.json`: dry-run or execution report for the storage-safe target-object subset materializer.
- `full_nomdl_scratch_plan.json`: read-only whole-GRScenes scratch route planner for full no-MDL conversion preparation.
- `full_nomdl_multi_root_run_report.json`: full-route single-process no-MDL runner report; the current checked-in report is completed apply evidence.
- `full_nomdl_apply_verification_report.json`: post-apply verification report for completed full-route no-MDL evidence.
- `full_dependency_closure_report.json`: read-only whole-GRScenes authored USD dependency and recursive no-MDL output scan for the full scratch route.
- `camera_stage_authoring_report.json`: execution report for authoring paired
  render camera wrapper stages.
- `paired_render_smoke_report.json`: first paired Isaac viewport smoke summary
  for one original/converted render pair.
- `paired_render_visual_review.json`: independent visual QA summary for the
  smoke pair.
- `paired_render_reports/`: per-pair render smoke reports for centerline-AABB
  recommended pairs after the visibility preflight gate.
- `recommended_paired_render_summary.json`: aggregate smoke summary over the
  recommended paired renders.
- `target_projection_qa_report.json`: projected image-space target bboxes and
  scoring-record skeletons for the recommended render-smoke pairs.
- `projection_center_baseline_predictions.jsonl`: deterministic bbox-center
  scoring-smoke predictions generated from `target_projection_qa_report.json`;
  this is not a VLM output file.
- `projection_center_baseline_predictions.jsonl.metadata.json`: provenance and
  hashes for the deterministic baseline prediction file.
- `projection_center_baseline_score_summary.json`: scorer-smoke summary over
  the deterministic baseline predictions; this is not task-performance
  evidence.
- `render_logs/`: archived `.txt` stdout/stderr logs referenced by the smoke
  reports.
- `renders/`: thin camera wrapper USDs and smoke PNG outputs for GRScenes
  render jobs.
- `visibility_geometry_index.json`: scene-id keyed non-target obstacle bboxes
  for centerline-AABB visibility preflight.
- `visibility_preflight_report.json`: centerline-AABB preflight report used to
  pick first-pass render candidates before image-space QA.
- `predictions.jsonl`: model outputs using the schema documented by `score_grounding.py`.
- `predictions.jsonl.metadata.json`: provenance for model-generated
  predictions from `run_vlm_predictions.py`.
- `score_summary.json`: aggregate point-in-box, answer consistency, and original-vs-converted metrics.

Task/render planning manifests must record benchmark source provenance,
engineering mirror or scratch path, scene USD filename, material condition, and
generation command. At minimum, task/render planning manifests should include
`dataset_role`, `source_dataset_root`, `source_scene_id`,
`source_scene_split`, `source_usd`, `scratch_scene_root`, `converted_usd`,
`material_condition`, `conversion_command`, and `renderer_settings`.
Route-planner artifacts such as `reference_closure_plan.json`,
`material_dependency_closure_plan.json`, and `full_nomdl_scratch_plan.json`
use their own action-schema fields instead. `model_checkpoint` is required
later for `predictions.jsonl` and `score_summary.json`, not for source, target,
or render planning manifests.

`source_manifest.json`, `target_manifest.json`, and `render_manifest.json` are generated provenance/planning artifacts, not VLM results, and should not be cited as task performance. The current `target_manifest.json` resolves 40/40 selected episode records across 5 home scenes to USD prim paths and world-space bboxes; those records correspond to 23 unique spatial targets after duplicate episode references are collapsed.

`target_manifest.json` uses the original GRScenes source tree read-only. The resolver opens source scene USDs with Isaac/pxr, matches target metadata paths to authored USD references, and computes bboxes from the absolute split-level model USD transformed by the scene prim transform. This avoids relying on composed scene bboxes when scene-local `models` and `Materials` entries are text pointer files rather than symlinks.

`scratch_materialization_report.json` is the next gate after `source_manifest.json`. The materializer mirrors selected scene folders and split-level `models` / `Materials` resource trees under `/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520`. The default copy mode is hardlink, not a top-level symlink to the source tree, so generated no-MDL sidecars can be written in scratch while avoiding a full duplicate of the shared material tree. GRScenes asset-internal relative symlinks under `models/` are preserved and checked so they resolve inside the scratch root. Hardlinked input files still share inodes with the source tree, so this mode relies on the invariant that no-MDL writes sidecar files and does not edit existing source files in place. One-scene materialization has been executed as a smoke gate only; do not scale the split-level mirror approach or use `--copy-mode copy` under the current storage budget. This report is still a filesystem-preparation artifact, not rendered image evidence and not a VLM result.

`reference_closure_plan.json` is the follow-up storage guardrail, currently generated at `2026-05-20T17:08:10.354908Z`.

It shows the selected model-root part is small: 40 resolved episode records collapse to 23 unique spatial targets, 5 scene-directory actions, 23 selected model-root actions, 51 model files, and 14 model symlinks.

It does not make conversion runnable. It reports `material_closure_status=requires_material_dependency_resolution` and `model_root_only_materialization_safe=false`: the 23 selected model roots contain 14 `Materials` symlinks, 5 ordinary `Materials` pointer files, and 4 missing `Materials` entries.

`material_dependency_closure_plan.json` is the follow-up material guardrail,
currently generated at `2026-05-20T18:03:34.938417Z`.

It scans only the 23 selected model roots with pxr/`UsdUtils.ComputeAllDependencies`. USD reports 70 resolved dependency paths and 61 unresolved dependency paths; the unresolved paths are recoverable because they are computed `model_root/Materials/...` paths whose tails exist under split-level `home_scenes/Materials`.

The checked-in plan resolves the material-file subset to 68 files, 56,405,072 bytes total: 20 `.mdl`, 42 `.png`, and 6 `.jpg`. It has `missing_material_asset_count=0` and `safe_to_materialize_selected_materials=true`, so a targeted materializer no longer needs the full split-level `Materials/` tree.

This still does not mean no-MDL can run after copying only those files. The plan has 9 `materials_entry_repair_actions`: 5 selected model roots have ordinary `Materials` pointer files, and 4 have no `Materials` entry. The scratch materializer must repair those roots to relative symlinks pointing at scratch split-level `Materials` before no-MDL conversion.

`targeted_materialization_report.json` is the storage-safe follow-up materializer
gate. The current checked-in report is a dry-run with 115 planned actions: 5
selected scene directories, 23 selected model roots, 68 material files, 10
scene-local `models`/`Materials` entry repairs, and 9 model-root `Materials`
entry repairs. It plans zero full resource-tree mirrors and records
`dry_run=true`, so no benchmark or scratch asset files were changed by the
checked-in run.

This still is not whole-scene conversion evidence. It is target-object closure.
Repairing scene-local `models` makes selected model roots addressable, but full
GRScenes scene USDs still author unselected `models/...` references. A read-only
probe also found scene-level material dependencies such as
`Materials/DayMaterial.mdl` and `Materials/Textures/Day.png`, outside the 68
model-root material files. Whole-scene no-MDL conversion needs a broader scene
dependency closure, or the render pipeline must intentionally crop/extract
target-object stages before conversion.

`full_nomdl_scratch_plan.json` is the read-only full-dataset route planner. It
does not apply scratch actions and does not run no-MDL.

The current checked-in plan covers 99 scenes: 69 home and 30 commercial. It
defaults to 99 planned `start_result_raw.usd` inputs while recording that all
297 scene-entry USDs exist across raw, navigation, and interaction variants. It
plans 99 scene-directory actions, 4 split-level resource-tree actions, 138 home
scene pointer-file repairs, and 99 preview no-MDL jobs. Commercial scene
`models`/`Materials` entries are already relative symlinks, so 60 entries are
recorded as projectable.

This file intentionally records `safe_to_apply=false`. The preview no-MDL jobs
are blocked because no-MDL recursively writes dependency `*_noMDL.usd`
sidecars, and independent per-scene CLI runs do not share one `Processor.done`
map. Each job includes structured `argv` fields for a later runner, but the
runner should still use the structured `scratch_input_usd` list instead of
parsing the human-readable command string. The full scratch materialization and
post-materialization dependency closure report now exist. Do not treat this
planner JSON as evidence that full converted scenes exist.

`full_nomdl_scratch_materialization_report.json` is the materialization report
for the full scratch route. It consumes `full_nomdl_scratch_plan.json` and
applies/verifies scratch-side tree hardlinks plus scene-entry repairs; it does
not run no-MDL conversion.

The current checked-in report has `dry_run=false`, 103 existing tree actions,
138 existing scene-entry repairs, 99 ignored conversion actions, 0 existing
planned no-MDL outputs, and 0 missing top-level scratch inputs. It is
filesystem-preparation evidence, not converted-scene evidence.

`full_nomdl_multi_root_run_report.json` is the full-route runner report. It
consumes `full_nomdl_scratch_plan.json` and uses one Python process and one
`Processor` instance across the 99 planned raw-scene roots.

The current checked-in report has 99 planned jobs, `dry_run=false`,
`apply_ready=true`, 99 conversion results, and `processor_done_count=89583`.
It consumes `full_dependency_closure_report.json` and the non-dry-run
`full_nomdl_scratch_materialization_report.json`. It marks
these blockers as satisfied:

- `single_process_multi_root_runner_missing`
- `single_process_multi_root_runner_closure_report_not_consumed`
- `whole_scene_dependency_closure_not_scanned`
- `recursive_nomdl_output_collision_scan_missing`
- `scratch_cleanliness_not_verified`

It has no remaining apply blockers and is now conversion evidence, not merely a
dry-run readiness report.

It also records `source_usd_missing_count=0`, `scratch_input_missing_count=0`,
and `top_level_output_collision_count=0`. Recursive dependency outputs are
covered by `full_dependency_closure_report.json`.

For automation, read `jobs[*].blocked_by` as the current report-level blocker
list. The original plan's stale job blockers are retained separately in
`jobs[*].source_plan_blocked_by`.

For real apply runs, use `./scripts/isaac_python.sh` rather than plain Python.
The runner repairs `sys.path` before importing `convert_asset.no_mdl`, because
path-based Isaac wrapper execution otherwise starts from the experiment
directory and cannot import the repository package.

`full_nomdl_apply_verification_report.json` is the post-apply gate after a
real runner execution. It is generated by `verify_full_nomdl_apply.py` and is
pure Python: it checks that `full_nomdl_multi_root_run_report.json` is
non-dry-run evidence, every planned top-level no-MDL output exists under the
scratch root, result output paths match expected outputs, and the immutable
source tree contains no `_noMDL` USD sidecars. Treat converted scenes as ready
for the next render-manifest and USD/render smoke-validation gate only when
this report has `passed=true`.

`render_manifest.json` now consumes the completed full no-MDL report. Original
jobs retain immutable benchmark provenance in `source_usd`, but their actual
`usd_path` points at the scratch `scratch_input_usd` so the renderer uses the
same repaired pointer-file layout as converted jobs. The current manifest has
184 render jobs, 0 missing material inputs, 0 missing camera stages, and 184
ready-to-run jobs.

`camera_stage_authoring_report.json` records the camera-wrapper authoring pass.
The current report selected 184 records, authored 184 camera stages, and has 0
blocked or failed jobs. Auto-light anchors are enabled in the wrappers so
original and converted conditions share identical supplemental lighting.

`paired_render_smoke_report.json` records the first usable paired render smoke:
`c27086f557d316584264.view_001.original` and
`c27086f557d316584264.view_001.converted`. Both commands exited 0 and produced
PNG files. Both images contain visible pixels for this view, but the original
render log still contains MDL/KooPbr failures while the converted render has no
KooPbr signal in stderr. This is render-stack smoke evidence only. The
associated `render_logs/` files are archived as `.txt` artifacts so the report
hashes point at files that can be committed. The report also hashes the
executed renderer script, `scripts/render_with_viewport_capture.py`. VLM
scoring still requires visibility-aware view selection, image-space boxes or
masks, predictions, and a score summary.

`paired_render_visual_review.json` records the independent clean-room visual
review for the same smoke pair. The verdict is `WARN`: the bottle is visible in
both images, but the converted material/color shift is large enough that this
pair should not be used as final VLM grounding evidence.

`paired_render_visual_review_batch.json` records the follow-up blind visual QA
over all 10 recommended render-smoke pairs. The batch-level verdict is `FAIL`
because 4/10 pairs have task-breaking visibility or framing problems. The useful
split is: one primary probe pair (`c27086f557d316584264.view_001`), five
WARN/caution candidates that need caveated or retaken use, and four excluded
pairs that should not enter VLM metrics without rerendering. This file is a
candidate filter only, not a model metric.

`visibility_geometry_index.json` and `visibility_preflight_report.json` are now
generated artifacts, not planned placeholders. The current geometry index covers
5 scenes, 19,435 filtered obstacle AABBs, 0 failures, `min_diagonal=5.0`,
`max_diagonal=1000.0`, and `max_abs_coordinate=1000000.0`. These filters remove
USD extreme bounds and overlarge scene components that otherwise make every
camera appear to sit inside an obstacle.

The current visibility preflight has 92 render pairs, 21
`centerline_clear` pairs, 71 blocked/ambiguous pairs, and 10 recommended target
pairs. Its method is `single_centerline_vs_non_target_aabb_preflight`; it is a
render-candidate filter only. It does not prove target visibility, image-space
coverage, depth visibility, material fidelity, or VLM readiness.

`paired_render_reports/` and `recommended_paired_render_summary.json` record the
recommended-pair render smoke follow-up after the preflight repair. The
aggregate summary covers 10 recommended pairs: 9 reports from
`paired_render_reports/` plus the earlier `paired_render_smoke_report.json`
fallback. All 10 commands exited 0, and every original/converted image has
non-dark pixels and image hashes. This advances the render evidence beyond a
single smoke pair, but the claim boundary remains render-smoke only: VLM
scoring still needs image-space target boxes or masks, visual QA over the
candidates, predictions, and `score_summary.json`.

`target_projection_qa_report.json` projects the world-space target bboxes for
the 10 recommended render-smoke pairs into image coordinates using the manifest
camera fields. The current report has 10 `projection_ok` pairs, 0 projection
blockers, and 20 scoring-record skeletons across original/converted conditions.
These projected boxes are the first point-in-box labels for VLM scoring, but
they are still geometric labels only. Final claims still need visual or depth QA,
VLM predictions, and `score_summary.json`.

`projection_center_baseline_predictions.jsonl` and
`projection_center_baseline_score_summary.json` are deterministic scoring-smoke
artifacts. They use the projected bbox center as the predicted point and the
target category as the predicted answer for all 20 scoring records. The current
score summary uses `schema_version=3` and records
`prediction_backends=["projection_center_smoke_baseline"]`,
`model_checkpoints=["projection_center_smoke_baseline_no_vlm"]`, and
`claim_boundary="scoring_smoke_only_not_vlm_evidence"`. It also includes
`score_provenance` with the input prediction hash and scorer script hash. The
1.0 point and answer scores only prove that the scorer, paired sample ids,
labels, and original/converted aggregation are wired correctly. They must not
be cited as VLM accuracy, model robustness, or downstream task performance.
Mixed baseline/model prediction files are also guarded: the scorer reports
`mixed_projection_baseline_and_model_predictions_not_claimable` if deterministic
baseline rows appear beside real model rows.
Duplicate rows for the same `pair_id/task/version` are counted in
`pair_consistency.duplicate_pair_version_count`.
Malformed coordinate fields, string-valued coordinate arrays, and non-dict
`target` or `prediction` objects are treated as unscored rows rather than
scorer crashes.

`run_vlm_predictions.py` is the real-model prediction runner for future
`predictions.jsonl` files. It supports `local_hf_qwen`,
`local_gemma4_multimodal`, and `openai_compatible` backends with lazy imports
so tests do not load VLM weights. The first checked-in real-model probe is under
`probes/gemma4_p01_predictions.jsonl`: local Gemma4 generated two predictions
for the visually accepted bottle pair `c27086f557d316584264.view_001`. This is
still a probe, not canonical `predictions.jsonl`. Its paired score summary is
`probes/gemma4_p01_score_summary.json`: answer accuracy is 1.0 for
original/converted, but point-in-bbox is 0.0 and the new point-in-image
diagnostic is also 0.0 because both predicted points are outside the 600x450
image. The runner blocks limited runs to canonical `predictions.jsonl` unless
`--force` is explicitly supplied, rejects empty record selections, and checks
image files before loading a local model.

The current checked-in verification report has `passed=true`, `blockers=[]`,
99 existing top-level outputs, and 0 source `_noMDL` USD sidecars.

`full_dependency_closure_report.json` is the next read-only gate for the full
scratch route. It consumes `full_nomdl_scratch_plan.json`, uses lazy `pxr.Sdf`
composition dependency scanning, maps reachable source USDs into the planned
scratch tree, and computes recursive `_noMDL` sidecar output paths.

The current checked-in report was generated at
`2026-05-21T09:05:33.920851Z`. It scanned the full 85,705 reachable USD
composition layers with no cap, resolved 89,484 USD dependency records, found 0
missing dependencies, found 0 outside-source references, and found 0 recursive
output collisions. It also records 0 missing top-level scratch inputs and 0
missing recursive scratch inputs, so `scan_truncated=false` and
`scratch_input_missing_count=0`.

Do not treat this JSON as converted-scene evidence, render evidence, or
permission to run `--apply`. Its large arrays are capped at 2,000 records;
complete totals live under `summary` and `report_limits`. It is not
material-file or texture-file closure evidence; shader and texture asset
attributes remain separate material-dependency gates unless surfaced as USD
composition arcs.

The runner consumes this report as an apply gate together with the
materialization report.

Timestamped `_noMDL_*` siblings are conservative collision signals in this
report, not a precise overwrite model.

`render_manifest.json` currently plans 23 unique targets x 4 target-centered
views = 92 original/converted pairs and 184 material-condition jobs. Original
render inputs use scratch `scratch_input_usd` files while retaining immutable
benchmark provenance in `source_usd`; converted material inputs point at the
completed full no-MDL scratch outputs via
`full_nomdl_multi_root_run_report.json`; `converted_jobs_missing_input_count=0`.
Camera-stage authoring has been completed, so `camera_stage_missing_count=0`
and `render_jobs_ready_to_run=184`. The first 10 recommended pairs now have
image-space projected boxes and deterministic scorer-smoke outputs, but real
paper claims still require visual/depth QA and model-generated VLM predictions.
The manifest normalizes current VLM prompts to S1 category-pointing prompts and
keeps source episode instructions/prompts separately as provenance; some source
SN episode records do not carry instruction text and must not be treated as
ready-made VLM prompts. Rendered image hashes live in smoke/result reports, not
in this planned manifest.

Do not cite generated results unless the provenance shows that benchmark scenes came from `/cpfs/user/zhuzihou/assets/zzh-grscenes` and no in-place conversion was run there. PIO should be treated as prompt/metric inspiration unless a future run explicitly imports PIO data.

Do not cite result files until rendered images, image hashes, image-space
target boxes, model-generated predictions, and real `score_summary.json` files
exist and have been checked.
