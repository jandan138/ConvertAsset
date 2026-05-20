# GRScenes VLM Grounding Raw Outputs

This directory is reserved for the ACL-oriented VLM grounding pilot.

Expected files:

- `source_manifest.json`: selected source scenes and episode records with provenance, scratch paths, and current mapping status.
- `render_manifest.json`: paired original/no-MDL renders with scene, camera, target, and prompt metadata.
- `predictions.jsonl`: model outputs using the schema documented by `score_grounding.py`.
- `score_summary.json`: aggregate point-in-box, answer consistency, and original-vs-converted metrics.

Each raw output must record benchmark source provenance, engineering mirror or scratch path, scene USD filename, material condition, and generation command. At minimum, manifests should include `dataset_role`, `source_dataset_root`, `source_scene_id`, `source_scene_split`, `source_usd`, `scratch_scene_root`, `converted_usd`, `material_condition`, `conversion_command`, `renderer_settings`, and `model_checkpoint`.

`source_manifest.json` is the only generated file currently present. It is a source-selection artifact, not a VLM result, and should not be cited as task performance.

Do not cite generated results unless the provenance shows that benchmark scenes came from `/cpfs/user/zhuzihou/assets/zzh-grscenes` and no in-place conversion was run there. PIO should be treated as prompt/metric inspiration unless a future run explicitly imports PIO data.

Do not register or cite result files until they exist and have been checked.
