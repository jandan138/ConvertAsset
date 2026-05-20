# GRScenes VLM Grounding Raw Outputs

This directory is reserved for the ACL-oriented VLM grounding pilot.

Expected files:

- `source_manifest.json`: selected source scenes and episode records with provenance, scratch paths, and current mapping status.
- `target_manifest.json`: resolved episode targets with USD prim paths, candidate prims, model provenance, and world-space bboxes for later camera placement.
- `render_manifest.json`: paired original/no-MDL render plan/jobs with planned output image paths, scene, camera, target, and prompt metadata.
- `predictions.jsonl`: model outputs using the schema documented by `score_grounding.py`.
- `score_summary.json`: aggregate point-in-box, answer consistency, and original-vs-converted metrics.

Planning manifests must record benchmark source provenance, engineering mirror or scratch path, scene USD filename, material condition, and generation command. At minimum, planning manifests should include `dataset_role`, `source_dataset_root`, `source_scene_id`, `source_scene_split`, `source_usd`, `scratch_scene_root`, `converted_usd`, `material_condition`, `conversion_command`, and `renderer_settings`. `model_checkpoint` is required later for `predictions.jsonl` and `score_summary.json`, not for source, target, or render planning manifests.

`source_manifest.json`, `target_manifest.json`, and `render_manifest.json` are generated provenance/planning artifacts, not VLM results, and should not be cited as task performance. The current `target_manifest.json` resolves 40/40 selected episode records across 5 home scenes to USD prim paths and world-space bboxes; those records correspond to 23 unique spatial targets after duplicate episode references are collapsed.

`target_manifest.json` uses the original GRScenes source tree read-only. The resolver opens source scene USDs with Isaac/pxr, matches target metadata paths to authored USD references, and computes bboxes from the absolute split-level model USD transformed by the scene prim transform. This avoids relying on composed scene bboxes when scene-local `models` and `Materials` entries are text pointer files rather than symlinks.

`render_manifest.json` currently plans 23 unique targets x 4 target-centered views = 92 original/converted pairs and 184 material-condition jobs. Original material inputs exist under the immutable benchmark source, but camera-stage authoring is still pending; converted material inputs are marked `blocked_missing_material_input` until no-MDL scratch derivatives are generated outside the source tree. Image-space boxes are explicitly pending projection and must be filled by the render/projection stage before VLM scoring. The manifest normalizes current VLM prompts to S1 category-pointing prompts and keeps source episode instructions/prompts separately as provenance; some source SN episode records do not carry instruction text and must not be treated as ready-made VLM prompts.

Do not cite generated results unless the provenance shows that benchmark scenes came from `/cpfs/user/zhuzihou/assets/zzh-grscenes` and no in-place conversion was run there. PIO should be treated as prompt/metric inspiration unless a future run explicitly imports PIO data.

Do not cite result files until rendered images, image hashes, image-space target boxes, predictions, and score summaries exist and have been checked.
