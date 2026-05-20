# GRScenes VLM Grounding Raw Outputs

This directory is reserved for the ACL-oriented VLM grounding pilot.

Expected files:

- `source_manifest.json`: selected source scenes and episode records with provenance, scratch paths, and current mapping status.
- `target_manifest.json`: resolved episode targets with USD prim paths, candidate prims, model provenance, and world-space bboxes for later camera placement.
- `render_manifest.json`: paired original/no-MDL render plan/jobs with planned output image paths, scene, camera, target, and prompt metadata.
- `scratch_materialization_report.json`: dry-run or execution report for mirroring selected benchmark scenes and split-level resources into the no-MDL scratch tree.
- `reference_closure_plan.json`: planner-only target/reference closure artifact that lists selected scene directories, selected model roots, and unresolved symlink/material dependency gaps.
- `material_dependency_closure_plan.json`: planner-only material subset artifact that lists the exact split-level `Materials` files and model-root `Materials` entry repairs needed by the selected targets.
- `predictions.jsonl`: model outputs using the schema documented by `score_grounding.py`.
- `score_summary.json`: aggregate point-in-box, answer consistency, and original-vs-converted metrics.

Planning manifests must record benchmark source provenance, engineering mirror or scratch path, scene USD filename, material condition, and generation command. At minimum, planning manifests should include `dataset_role`, `source_dataset_root`, `source_scene_id`, `source_scene_split`, `source_usd`, `scratch_scene_root`, `converted_usd`, `material_condition`, `conversion_command`, and `renderer_settings`. `model_checkpoint` is required later for `predictions.jsonl` and `score_summary.json`, not for source, target, or render planning manifests.

`source_manifest.json`, `target_manifest.json`, and `render_manifest.json` are generated provenance/planning artifacts, not VLM results, and should not be cited as task performance. The current `target_manifest.json` resolves 40/40 selected episode records across 5 home scenes to USD prim paths and world-space bboxes; those records correspond to 23 unique spatial targets after duplicate episode references are collapsed.

`target_manifest.json` uses the original GRScenes source tree read-only. The resolver opens source scene USDs with Isaac/pxr, matches target metadata paths to authored USD references, and computes bboxes from the absolute split-level model USD transformed by the scene prim transform. This avoids relying on composed scene bboxes when scene-local `models` and `Materials` entries are text pointer files rather than symlinks.

`scratch_materialization_report.json` is the next gate after `source_manifest.json`. The materializer mirrors selected scene folders and split-level `models` / `Materials` resource trees under `/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520`. The default copy mode is hardlink, not a top-level symlink to the source tree, so generated no-MDL sidecars can be written in scratch while avoiding a full duplicate of the shared material tree. GRScenes asset-internal relative symlinks under `models/` are preserved and checked so they resolve inside the scratch root. Hardlinked input files still share inodes with the source tree, so this mode relies on the invariant that no-MDL writes sidecar files and does not edit existing source files in place. One-scene materialization has been executed as a smoke gate only; do not scale the split-level mirror approach or use `--copy-mode copy` under the current storage budget. This report is still a filesystem-preparation artifact, not rendered image evidence and not a VLM result.

`reference_closure_plan.json` is the follow-up storage guardrail, currently generated at `2026-05-20T17:08:10.354908Z`.

It proves the selected model-root part is small: 40 resolved episode records collapse to 23 unique spatial targets, 5 scene-directory actions, 23 selected model-root actions, 51 model files, and 14 model symlinks.

It does not make conversion runnable. It reports `material_closure_status=requires_material_dependency_resolution` and `model_root_only_materialization_safe=false`: the 23 selected model roots contain 14 `Materials` symlinks, 5 ordinary `Materials` pointer files, and 4 missing `Materials` entries.

`material_dependency_closure_plan.json` is the follow-up material guardrail,
currently generated at `2026-05-20T18:03:34.938417Z`.

It scans only the 23 selected model roots with pxr/`UsdUtils.ComputeAllDependencies`. USD reports 70 resolved dependency paths and 61 unresolved dependency paths; the unresolved paths are recoverable because they are computed `model_root/Materials/...` paths whose tails exist under split-level `home_scenes/Materials`.

The checked-in plan resolves the material-file subset to 68 files, 56,405,072 bytes total: 20 `.mdl`, 42 `.png`, and 6 `.jpg`. It has `missing_material_asset_count=0` and `safe_to_materialize_selected_materials=true`, so a targeted materializer no longer needs the full split-level `Materials/` tree.

This still does not mean no-MDL can run after copying only those files. The plan has 9 `materials_entry_repair_actions`: 5 selected model roots have ordinary `Materials` pointer files, and 4 have no `Materials` entry. The scratch materializer must repair those roots to relative symlinks pointing at scratch split-level `Materials` before no-MDL conversion.

`render_manifest.json` currently plans 23 unique targets x 4 target-centered views = 92 original/converted pairs and 184 material-condition jobs. Original material inputs exist under the immutable benchmark source, but camera-stage authoring is still pending; converted material inputs are marked `blocked_missing_material_input` until no-MDL scratch derivatives are generated outside the source tree. Image-space boxes are explicitly pending projection and must be filled by the render/projection stage before VLM scoring. The manifest normalizes current VLM prompts to S1 category-pointing prompts and keeps source episode instructions/prompts separately as provenance; some source SN episode records do not carry instruction text and must not be treated as ready-made VLM prompts.

Do not cite generated results unless the provenance shows that benchmark scenes came from `/cpfs/user/zhuzihou/assets/zzh-grscenes` and no in-place conversion was run there. PIO should be treated as prompt/metric inspiration unless a future run explicitly imports PIO data.

Do not cite result files until rendered images, image hashes, image-space target boxes, predictions, and score summaries exist and have been checked.
