# GRScenes VLM Grounding Raw Outputs

This directory is reserved for the ACL-oriented VLM grounding pilot.

Expected files:

- `render_manifest.json`: paired original/no-MDL renders with scene, camera, target, and prompt metadata.
- `predictions.jsonl`: model outputs using the schema documented by `score_grounding.py`.
- `score_summary.json`: aggregate point-in-box, answer consistency, and original-vs-converted metrics.

Do not register or cite result files until they exist and have been checked.
