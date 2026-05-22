# GRScenes VLM Grounding Experiment

This experiment is the ACL-oriented material-generalization study. It measures whether ConvertAsset's MDL-to-UsdPreviewSurface conversion changes VLM grounding behavior on realistic USD indoor scenes.

## Read This First: 1-Scene Pilot Lessons

Plain version: this run only prepared one scene so no-MDL can be run safely
outside the benchmark source tree. It did not produce converted USDs, rendered
images, VLM predictions, or paper-ready scores.

The important traps:

- Never run no-MDL directly on `/cpfs/user/zhuzihou/assets/zzh-grscenes`.
  ConvertAsset writes `*_noMDL.usd` beside the input USD, so source inputs must
  first be materialized into scratch.
- Scene-local `models` and `Materials` entries are small pointer files, not the
  real resource trees. The real resources live at the split level under
  `home_scenes/models` and `home_scenes/Materials`.
- GRScenes `models/` contains many internal relative symlinks. A naive copy
  with `symlinks=False` expands those links into hundreds of thousands of real
  files and is slow to clean up. The current materializer preserves internal
  symlinks and checks that they resolve inside scratch.
- Hardlink mode is space-saving but not a physical copy. `du` can report a
  large logical size because the files are visible from scratch, but the input
  files share inodes with the source tree. This relies on no-MDL writing
  sidecars and never editing existing inputs in place.
- Do not scale the current split-level mirror beyond `--limit-scenes 1`. The
  one-scene scratch tree already exposes about 104G through `du` and creates
  141,082 visible files, 27,819 symlinks, and 52,601 directories.
- Use the target/reference closure planner before any further materialization.
  The current plan sees 23 selected model roots with 51 model files and 14 model
  symlinks, but all 23 selected roots still require split-level `Materials`
  dependency resolution.
- This one-scene pilot predates the full scratch route. For the current full
  route, pass `--nomdl-run-report` when regenerating `render_manifest.json` so
  converted paths are taken from the completed full no-MDL apply report.

Safe status after the 2026-05-20 pilot:

```text
source tree: /cpfs/user/zhuzihou/assets/zzh-grscenes
scratch tree: /cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520
report: paper/shared/evidence/raw/grscene_vlm_grounding/scratch_materialization_report.json
result: one scene materialized, converted USDs still missing
```

## Benchmark Basis

- Benchmark source: GRScenes-100 original benchmark package under
  `/cpfs/user/zhuzihou/assets/zzh-grscenes`.
- Intervention: ConvertAsset no-MDL conversion.
- Protocol: PIO-style precise visual grounding prompts.
- Downstream extension: InternNav / VL-LN navigation after the grounding pilot is stable.

The benchmark source provides scene USDs, metadata, and episodes:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes/scenes/GRScenes-100
/cpfs/user/zhuzihou/assets/zzh-grscenes/benchmark/mm_episodes.json
/cpfs/user/zhuzihou/assets/zzh-grscenes/benchmark/sn_episodes.json
```

Local inventory checked on 2026-05-20:

- 69 home scenes and 30 commercial scenes, 99 total.
- Each scene has `start_result_raw.usd`, `start_result_navigation.usd`, `start_result_interaction.usd`, `metadata.json`, and `interactive_obj_list.json`.
- `mm_episodes.json` covers 30 home scenes and 420 episodes.
- `sn_episodes.json` covers the same 30 home scenes and 300 episodes.
- Commercial scenes have no local `mm_episodes.json` / `sn_episodes.json` coverage, so they should be treated as metadata-driven material stress tests unless a future episode source is added.
- The first ACL/VLM episode-backed pilot should select from the 30 episode-covered home scenes before claiming broader 99-scene coverage.

Treat this tree as immutable. It is the source for scene selection and paper claims, not a place to write generated sidecars.

Two source-tree details matter for runners:

- Scene-local `Materials` and `models` entries are pointer files containing relative paths, not symlinks.
- Scene USDs use `.usd` names but may contain binary USDC data, so validation should open them through `pxr` or Isaac Sim.

## Engineering Validation Data

The restored test0 mirror is only for ConvertAsset smoke tests, runner debugging, and path validation. Do not cite it as the benchmark source.

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100
```

First smoke-test scene:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100/home/MV7J6NIKTKJZ2AABAAAAADQ8_usd/layout.usd
```

The existing no-MDL work tree for this mirror is:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset_no_mdl_work_20260520/GRScenes100
```

Convert command template:

```bash
./scripts/isaac_python.sh ./main.py no-mdl /path/to/scratch-copy/start_result_raw.usd
```

Conversion outputs for the ACL/VLM benchmark must be generated from a scratch copy of selected benchmark scenes, for example under:

```text
/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520
```

The paired material conditions are:

- Original benchmark USD: `start_result_raw.usd`, `start_result_navigation.usd`, or `start_result_interaction.usd`, depending on the task.
- Converted scratch derivative: the no-MDL USD generated outside the immutable benchmark source tree.

PIO is a prompt and metric inspiration here. Do not write that this experiment evaluates on PIO unless a later protocol actually imports the PIO dataset.

## Source Manifest

Before rendering, generate the source/episode manifest:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_source_manifest.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/source_manifest.json
```

This manifest is not a VLM result. It fixes provenance and selection for the first pilot:

- 5 episode-backed home scenes.
- 5 metadata-driven commercial stress scenes.
- 8 metadata-mapped episode records per home scene, 40 episode records total. These are not guaranteed to be 40 unique spatial targets because `mm` and `sn` episodes can repeat the same object.
- Scratch paths mirror the original GRScenes layout under `/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520`.
- `excluded_episode_records` captures episode records that fail the current source-mapping gate.

The current no-MDL CLI writes `*_noMDL.usd` beside the input USD. Until an explicit `--out-root` path exists, never run it directly on `/cpfs/user/zhuzihou/assets/zzh-grscenes`; copy selected scenes into the scratch tree first.

## Scratch Materialization

Before running no-MDL conversion, materialize the selected benchmark scenes into
the scratch tree:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py \
  --limit-scenes 1 \
  --dry-run
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/scratch_materialization_report.json
```

The materializer reads `source_manifest.json`, validates that the scratch root is
outside the manifest-declared benchmark source root, and mirrors each selected
scene directory plus the split-level `models/` and `Materials/` resource trees.
It uses hardlinks by default so the first pilot does not duplicate the shared
material tree. Hardlinked files are not independent physical copies: this mode
assumes the no-MDL pipeline writes new `*_noMDL.usd` sidecars and does not edit
existing input USD/MDL/texture files in place.

Storage guardrail: keep this command to `--limit-scenes 1` for smoke
preparation. A completed one-scene scratch tree exposes about 104G of
hardlinked data through `du` and creates 27,819 internal symlinks plus 52,601
directories. Do not scale this split-level mirror approach or use
`--copy-mode copy` until the experiment has a target/reference-closure
materializer.

Do not replace the scratch resource roots with symlinks to the source tree:
no-MDL sidecars must be created in scratch, never inside the immutable benchmark
source. Asset-internal GRScenes relative symlinks under `models/` are different:
the materializer preserves them and validates that their scratch-side targets
resolve inside the scratch root.

Current hard stop: do not use this split-level materializer for more scenes or
as the next ACL evidence step. The next step is the reference-closure and
material-dependency closure plan below, because all 23 selected model roots
still need split-level `Materials` resolution.

To materialize one scene after reviewing the dry-run report:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py \
  --limit-scenes 1
```

Then run conversion on the scratch input USD, not on `source_usd`:

```bash
./scripts/isaac_python.sh ./main.py no-mdl \
  /cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520/scenes/GRScenes-100/home_scenes/scenes/<scene_id>/start_result_raw.usd
```

After conversion, regenerate the render manifest with the converted-input gate:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py \
  --nomdl-run-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json \
  --require-converted
```

## Reference Closure Plan

Before scaling scratch materialization, plan the target/reference closure:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_reference_closure.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/reference_closure_plan.json
```

The current checked-in plan was generated at `2026-05-20T17:08:10.354908Z`.

This planner is intentionally read-only. It does not copy, hardlink, convert,
render, or open USD stages. It consumes the resolved targets from
`target_manifest.json`, deduplicates them by
`(source_scene_id, object_instance_id, target_prim_path)`, and plans one model
root action per unique `resolved_model_path` parent directory.

Current result:

- 40 resolved episode records collapse to 23 unique spatial targets.
- Those targets reference 23 unique model roots across 5 scenes.
- The selected model roots contain 51 files and 14 symlinks.
- `Materials` entry pattern: 14 symlinks, 5 ordinary pointer files, and 4
  missing entries.
- All 23 selected model roots require external split-level material resolution.

Plain version: this shows the model part can be made much smaller than the
one-scene split-level mirror, but the closure is not runnable yet. The next
implementation should resolve only the material files used by these selected
model USDs, not copy the entire split-level `Materials/` tree.

## Material Dependency Closure Plan

Before writing a new scratch materializer, plan the exact split-level material
files needed by the selected model USDs:

```bash
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_material_dependency_closure.py \
  --dependency-backend pxr
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/material_dependency_closure_plan.json
```

The current checked-in plan was generated at
`2026-05-20T18:03:34.938417Z`.

This planner is also read-only. It opens only the 23 selected `instance.usd`
roots with `UsdUtils.ComputeAllDependencies`, recovers unresolved
`./Materials/...` paths against split-level `home_scenes/Materials`, and emits
file-level hardlink actions. It does not copy files or mutate either asset
tree.

Current result:

- 23 selected model roots scanned.
- USD reports 70 resolved dependency paths and 61 unresolved dependency paths.
- All unresolved paths recover to split-level `home_scenes/Materials`.
- The deduplicated material subset is 68 files, 56,405,072 bytes total:
  20 `.mdl`, 42 `.png`, and 6 `.jpg`.
- 9 selected model roots still need a scratch-side `Materials` entry repair:
  5 pointer files should be replaced with relative symlinks, and 4 missing
  entries should be created as relative symlinks.
- `safe_to_materialize_selected_materials=true`, but
  `ready_for_nomdl_after_material_file_actions=false` until those entry repairs
  are executed in scratch.

Plain version: the material files are now small enough to materialize safely,
but they are not sufficient by themselves. Do not run no-MDL after only copying
the 68 files; pointer-file and missing-entry model roots will still fail to
resolve `./Materials/...`.

## Targeted Materialization Plan

Use the targeted materializer instead of scaling the old split-level mirror:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_targeted_closure.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/targeted_materialization_report.json
```

The command defaults to dry-run. It writes only the report unless `--apply` is
passed.

Current dry-run result:

- 115 planned actions, 0 writes.
- 5 selected scene directories.
- 23 selected model roots.
- 68 selected material files.
- 10 scene-local entry repairs: each selected scene's `models` and
  `Materials` pointer files become scratch-side relative symlinks.
- 9 model-root `Materials` entry repairs from the material dependency closure.
- `resource_tree_count=0`, so it does not mirror full split-level `models/` or
  `Materials/`.

Important limitation: this closes the target-object storage subset, not the
whole-scene conversion problem. A read-only probe found that the selected
scenes still author many unselected `models/...` references, and scene-level
materials such as `Materials/DayMaterial.mdl` and `Materials/Textures/Day.png`
are outside the 68 model-root material files. Before citing converted whole
scenes, either implement broader scene dependency closure or intentionally move
to target-object/cropped render stages.

## Full no-MDL Scratch Plan

For the "convert the whole `zzh-grscenes` benchmark into no-MDL scratch first"
route, use the read-only full planner:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_nomdl_scratch.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_plan.json
```

Current checked-in result:

- 99 scenes: 69 home and 30 commercial.
- 99 planned `start_result_raw.usd` no-MDL inputs by default.
- All 297 scene-entry USDs exist in inventory: 99 raw, 99 navigation, and 99
  interaction.
- 99 scene-directory materialization actions.
- 4 split-level resource-tree actions: home/commercial `models` and
  `Materials`.
- 138 home scene pointer-file repairs for `models` and `Materials`.
- 60 commercial scene symlink entries are already projectable into scratch.
- 0 existing source-side raw `_noMDL` sidecars were found at the scene-entry
  layer.
- `planner_only=true` and `safe_to_apply=false`.

Plain version: full scratch conversion is possible as a staged route, but this
planner is not permission to run no-MDL. ConvertAsset recursively writes
`*_noMDL.usd` beside every reachable USD. `--only-new-usd` suppresses
summary/audit files, but it still writes recursive dependency USD sidecars.
Running 99 scene roots as 99 separate CLI commands would not share
`Processor.done`, so shared dependencies can be converted repeatedly and may
produce timestamped outputs when `ALLOW_OVERWRITE=False`.

The dedicated single-process multi-root runner, full scratch materialization,
and post-materialization dependency/output collision scan now exist. The next
safe step is the guarded no-MDL `--apply` conversion.

## Full no-MDL Scratch Materialization Report

For the full scratch route, the guarded materializer is:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json
```

Current checked-in result:

- `dry_run=false`; the full scratch tree has been materialized.
- 103 tree actions verified as existing on the idempotency rerun: 99 scene
  directories and 4 split-level
  `models`/`Materials` resource roots.
- 138 scratch scene-entry repairs verified as existing for pointer-file `models` and
  `Materials` entries.
- 99 `convert_no_mdl` actions are intentionally ignored by the materializer.
- 0 existing planned no-MDL outputs detected in the scratch root.
- 99 top-level scratch inputs exist and 0 are missing.

Plain version: the full input scratch dataset exists now. It was materialized
with hardlinks, not full physical copies. The materializer rejects
source/scratch nesting, refuses report writes inside asset roots, validates
projected symlink targets, and blocks stale scratch/source no-MDL outputs before
real materialization.

## Full no-MDL Multi-Root Runner Report

For a dry-run readiness check, use:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py \
  --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json \
  --materialization-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json
```

Current checked-in result:

- 99 planned raw-scene jobs.
- `dry_run=false`.
- `apply_ready=true`.
- `single_process_multi_root_runner_missing`,
  `single_process_multi_root_runner_closure_report_not_consumed`,
  `whole_scene_dependency_closure_not_scanned`, and
  `recursive_nomdl_output_collision_scan_missing` are satisfied by the runner
  shell plus `full_dependency_closure_report.json`.
- `scratch_cleanliness_not_verified` is satisfied by the non-dry-run
  materialization report.
- Remaining blockers: none.
- Top-level expected-output collision count is 0.
- 99 conversion results were written.
- `processor_done_count=89583`.
- Each job's current `blocked_by` is recomputed from this report; the older
  plan-level blockers are preserved separately as `source_plan_blocked_by`.

Plain version: the full scratch no-MDL apply has run successfully. It reused
one `Processor` instance and one `Processor.done` map across all 99 roots. The
default dry-run path still imports no `pxr` and no no-MDL modules.

The real apply command must use Isaac Python and `--apply`:

```bash
PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py \
  --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json \
  --materialization-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json \
  --apply
```

The runner explicitly adds the repository root to `sys.path` before importing
`convert_asset.no_mdl`; this is needed because Isaac's wrapper runs path-based
scripts with the experiment directory, not the repository root, as
`sys.path[0]`.

After a real apply finishes, verify it before using the converted scenes:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/verify_full_nomdl_apply.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_apply_verification_report.json
```

The verifier is pure Python. It checks that the runner report is non-dry-run
evidence, all planned top-level no-MDL outputs exist under scratch, result
paths match expected outputs, and the immutable source tree has no `_noMDL`
USD sidecars.

Current checked-in verification result:

- `passed=true`.
- `blockers=[]`.
- 99 expected top-level no-MDL outputs exist.
- 0 source `_noMDL` USD sidecars were found under
  `/cpfs/user/zhuzihou/assets/zzh-grscenes`.

This verifier is not a residual-MDL, USD-open, or visual render validation.
The next gate is render-manifest regeneration plus USD/render smoke validation.

## Full Dependency Closure Report

Before materializing or converting the full scratch route, scan the authored USD
composition dependency closure and recursive no-MDL sidecar write set:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_dependency_closure.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json
```

This report is read-only. It consumes `full_nomdl_scratch_plan.json`, lazily
uses `pxr.Sdf` for authored composition dependency scanning, recovers
scene-local `models/...` and `Materials/...` references when they appear as USD
composition dependencies, maps reachable source USDs into the planned scratch
tree, and computes the recursive `*_noMDL.usd` sidecars that ConvertAsset would
write later. It does not copy, hardlink, convert, render, or write inside the
source/scratch asset roots.

Current checked-in result:

- 99 planned raw-scene jobs.
- 85,705 reachable source USD layers scanned with no layer cap.
- 89,484 resolved USD composition dependency records.
- 0 missing dependencies.
- 0 outside-source references.
- 85,705 expected no-MDL sidecar outputs: 99 top-level roots and 85,606
  recursive dependency outputs.
- 0 existing base sidecars, 0 timestamped sidecars, and 0 duplicate planned
  outputs.
- 0 missing scratch inputs: 99 top-level inputs and 85,606 recursive dependency
  inputs all exist under the scratch root.
- `scan_truncated=false` and `unscanned_usd_queue_count=0`.
- The post-materialization no-cap scan took 702 seconds in the local Isaac/PXR
  environment.
- `safe_to_run_multi_root_nomdl=false`.

Plain version: the full USD composition graph now looks structurally clean for
the recursive no-MDL sidecar gate, and the scan-missing blockers are satisfied.
This closure report alone still records runner/cleanliness blockers because it
does not consume runner/materialization evidence. The downstream
`full_nomdl_multi_root_run_report.json` consumes both and reports
`apply_ready=true`.

The JSON intentionally caps large record lists at 2,000 items so the evidence
file stays reviewable. Use `summary` and `report_limits` for complete counts;
the long arrays are samples for debugging.

This report should not be read as material-file or texture-file closure. The
Sdf backend scans USD composition asset dependencies; shader inputs and texture
asset attributes remain covered by separate material-dependency evidence unless
they are surfaced through composition arcs.

Timestamped `_noMDL_*` siblings are treated as conservative collision signals.
That can over-block a future run, but it avoids silently stepping past stale
sidecars.

## Target Manifest

Before rendering, resolve the selected episode targets to USD prims and world-space bboxes:

```bash
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/target_manifest.json
```

This manifest is also not a VLM result. It is the camera-target localization gate for paired rendering:

- 5 episode-backed home scenes attempted.
- 40 episode records attempted.
- 40 episode records resolved to USD prim paths and world-space bboxes.
- 23 unique `(scene, object_instance_id, target_prim_path)` targets after duplicate episode records are collapsed.
- 17 duplicate episode-record targets, with at most 2 episode records mapped to the same unique target.
- Resolution uses authored USD reference paths first, with exact prim-suffix fallback for objects whose `interactive_obj_list.json` coverage is incomplete.
- Bboxes use the absolute split-level model USD bbox transformed by the scene prim transform (`model_local_bbox_x_scene_xform`), because scene-local `models` pointer files are regular text files rather than symlinks and composed scene bbox warnings are expected.

For command-line smoke tests, use:

```bash
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py \
  --limit-scenes 1 \
  --out /tmp/grscene_target_manifest_smoke.json
```

USD may emit broken relative-reference warnings when opening the original scene USDs. Those warnings are expected for the immutable source layout and do not imply that the resolver modified the source dataset.

## Render Manifest

Before rendering images, generate the paired view/job plan:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py \
  --nomdl-run-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json \
  --require-converted
```

Default output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json
```

This manifest is a render plan and provenance bridge, not rendered image evidence and not a VLM result:

- 40 resolved episode records are collapsed into 23 unique spatial render targets.
- Four target-centered static orbit views are planned per unique target.
- The current pilot therefore has 92 original/converted render pairs and 184 material-condition render jobs.
- Original jobs keep immutable benchmark source provenance in `source_usd`, but
  render from the full scratch `scratch_input_usd`. The scratch route repairs
  scene-local `models` / `Materials` pointer entries without writing back to the
  benchmark source tree, so original and converted renders share the same
  addressable dependency layout.
- Converted jobs point at the full no-MDL scratch outputs recorded by
  `full_nomdl_multi_root_run_report.json`; `converted_jobs_missing_input_count=0`.
- Camera-stage authoring has been executed with
  `author_render_camera_stages.py`; `camera_stage_missing_count=0` and
  `render_jobs_ready_to_run=184`.
- Each pair stores one shared camera plan so original and converted renders differ only by material condition.
- Image-space target bboxes remain `pending_projection_from_world_bbox`; scoring must not run until the renderer projects bboxes or masks into image coordinates.
- Each planned image record includes a `visual_review` packet marker for the clean-room `render-visual-reviewer` skill.

Use `--require-converted` after scratch conversion to fail fast if any converted USD is still missing.

Author camera wrapper stages:

```bash
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/author_render_camera_stages.py \
  --include-existing \
  --overwrite \
  --apply
```

The camera wrappers are thin USD files in the render output tree. Each wrapper
opens the condition-specific scratch USD as a sublayer, adds the planned camera
prim, and adds identical auto-light anchors for both material conditions.

The current paired render smoke is recorded in:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/paired_render_smoke_report.json
paper/shared/evidence/raw/grscene_vlm_grounding/render_logs/
```

Run it with:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_paired_render_smoke.py \
  --pair-id c27086f557d316584264.view_001
```

The current smoke shows that both original and converted view-001 renders
produce visible pixels under the local Isaac viewport path. The original render
still reports many MDL/KooPbr failures; the converted render reports no KooPbr
signal. The report stores image hashes, stdout/stderr log hashes, and the
executed renderer script hash for `scripts/render_with_viewport_capture.py`.
Independent visual review marked the pair `WARN`: the bottle is visible, but
the converted material/color shift is large enough that this is not yet a fair
final grounding comparison. Treat this as render-stack smoke evidence only; it
is not VLM metric evidence. The next render gate is visibility-aware view
selection before batch rendering.

Start visibility-aware view selection with the pure geometry preflight:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_visibility_aware_views.py \
  --render-manifest paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json \
  --geometry-index paper/shared/evidence/raw/grscene_vlm_grounding/visibility_geometry_index.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/visibility_preflight_report.json
```

`visibility_geometry_index.json` and `visibility_preflight_report.json` now
exist as generated preflight artifacts. Treat them as candidate-selection
helpers only: they use a single camera-to-target centerline against filtered
non-target AABBs, not rendered image visibility, depth, mask, or model evidence.

## Task Families

| Task | Prompt shape | Metric |
|---|---|---|
| S1 referred object localization | "Point to the {category}." for the current render-plan gate; attribute-augmented prompts are a later extension after image-space labels exist. | point-in-box or point-in-mask accuracy |
| S2 task-driven grounding | "Where should the robot interact to {action}?" | part/object region hit rate |
| S3 navigation proxy | "Which object should the robot move toward to {goal}?" | target-region accuracy and answer consistency |

## Planned Outputs

Do not cite these files as task-performance evidence until the corresponding rendered images, image-space labels, model-generated predictions, and real score summaries exist and are registered in `paper/shared/evidence/results_manifest.yaml`.

```text
paper/shared/evidence/raw/grscene_vlm_grounding/target_manifest.json
paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json
paper/shared/evidence/raw/grscene_vlm_grounding/target_projection_qa_report.json
paper/shared/evidence/raw/grscene_vlm_grounding/projection_center_baseline_predictions.jsonl
paper/shared/evidence/raw/grscene_vlm_grounding/projection_center_baseline_score_summary.json
paper/shared/evidence/raw/grscene_vlm_grounding/predictions.jsonl
paper/shared/evidence/raw/grscene_vlm_grounding/score_summary.json
```

The `projection_center_baseline_*` files are scorer-smoke artifacts only. They
are intentionally generated from projected bbox centers and carry
`claim_boundary="scoring_smoke_only_not_vlm_evidence"`. They prove that the
JSONL schema, point-in-box scoring, answer matching, score provenance, and
original/converted pair aggregation are wired, not that any VLM succeeded.
The current answer metric uses simple case-insensitive substring matching and
is acceptable for this category-echo smoke gate only; final model claims need a
stricter category normalizer, ontology mapping, or adjudicated semantic match.

## Real VLM Backend Route

The read-only reference project
`/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator` has already solved
the practical model-backend split that this experiment should reuse
conceptually:

- `local_hf`: local Hugging Face/Qwen-VL inference, with
  `/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct` available on
  this machine.
- `local_gemma4_multimodal`: local Gemma4 image-text inference in
  `/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python`,
  using the immutable Gemma4 release path under
  `/cpfs/user/zhuzihou/models/gemma4/releases/`.
- `openai_compatible`: remote multimodal Chat Completions-compatible API,
  requiring both an API base URL and an API key environment variable.

For this paper repo, do not run the Auto-Asset-Annotator asset annotation CLI
against GRScenes images. Instead, implement a small prediction runner that
reuses the same backend ideas but writes this experiment's `predictions.jsonl`
schema: one record per rendered image, preserving `sample_id`, `pair_id`,
`version`, `task`, `target`, prompt text, image hash, model backend, model
checkpoint, decoding settings, raw model text, parsed point or answer, and
failure status. Real VLM claims start only after that file is generated by an
actual model backend and scored into `score_summary.json`.

The prediction runner now exists:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/target_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/probes/qwen_limit1_predictions.jsonl \
  --model-backend local_hf_qwen \
  --model-path /cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct \
  --limit 1
```

Use `--limit 1` for the first live probe and write to an isolated probe output,
not canonical `predictions.jsonl`. The runner blocks limited runs to canonical
`predictions.jsonl` unless `--force` is explicitly supplied, refuses empty
record selections, and checks image files before loading a local model. It also supports
`local_gemma4_multimodal` under the Genesis-LLM QLoRA Python environment and
`openai_compatible` when a real API base URL plus key environment variable are
available. The script uses lazy imports for local model backends, so importing
or testing it does not load heavy VLM weights.

The first live probe has now been run with `local_gemma4_multimodal` on the
visually accepted P01 bottle pair:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 \
  /cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/target_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_p01_predictions.jsonl \
  --model-backend local_gemma4_multimodal \
  --model-path /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 \
  --sample-id c27086f557d316584264.view_001.original \
  --sample-id c27086f557d316584264.view_001.converted \
  --max-new-tokens 64 \
  --force
```

The Qwen route is not yet the first choice in this repo because the currently
checked Python environments do not provide `qwen_vl_utils`. The Gemma4 route
loads successfully on the local RTX 4090. Unsloth may create
`unsloth_compiled_cache/` under the repo root; it is ignored and should be
treated as disposable runtime cache.

Scoring command:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/score_summary.json
```

For the Gemma4 P01 probe, score the isolated probe output instead:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_p01_predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_p01_score_summary.json
```

The P01 probe result is intentionally negative for localization: both model
points are outside the 600x450 image and outside the target bbox, while the
answer text matches `bottle`. This makes the next experiment step clear: scale
from one probe to visually accepted pairs only, and report coordinate failures
separately from category-answer matches.
