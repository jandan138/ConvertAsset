# GRScenes VLM Grounding Raw Outputs

This directory is reserved for the ACL-oriented VLM grounding pilot.

Expected files:

- `source_manifest.json`: selected source scenes and episode records with provenance, scratch paths, and current mapping status.
- `target_manifest.json`: resolved episode targets with USD prim paths, candidate prims, model provenance, and world-space bboxes for later camera placement.
- `render_manifest.json`: paired original/no-MDL renders with scene, camera, target, and prompt metadata.
- `predictions.jsonl`: model outputs using the schema documented by `score_grounding.py`.
- `score_summary.json`: aggregate point-in-box, answer consistency, and original-vs-converted metrics.

Each raw output must record benchmark source provenance, engineering mirror or scratch path, scene USD filename, material condition, and generation command. At minimum, manifests should include `dataset_role`, `source_dataset_root`, `source_scene_id`, `source_scene_split`, `source_usd`, `scratch_scene_root`, `converted_usd`, `material_condition`, `conversion_command`, `renderer_settings`, and `model_checkpoint`.

`source_manifest.json` and `target_manifest.json` are generated provenance artifacts, not VLM results, and should not be cited as task performance. The current `target_manifest.json` resolves 40/40 selected episode records across 5 home scenes to USD prim paths and world-space bboxes; those records correspond to 23 unique spatial targets after duplicate episode references are collapsed.

`target_manifest.json` uses the original GRScenes source tree read-only. The resolver opens source scene USDs with Isaac/pxr, matches target metadata paths to authored USD references, and computes bboxes from the absolute split-level model USD transformed by the scene prim transform. This avoids relying on composed scene bboxes when scene-local `models` and `Materials` entries are text pointer files rather than symlinks.

Do not cite generated results unless the provenance shows that benchmark scenes came from `/cpfs/user/zhuzihou/assets/zzh-grscenes` and no in-place conversion was run there. PIO should be treated as prompt/metric inspiration unless a future run explicitly imports PIO data.

Do not register or cite result files until they exist and have been checked.
