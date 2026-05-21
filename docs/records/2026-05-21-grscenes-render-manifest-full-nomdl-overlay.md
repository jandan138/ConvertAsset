# 2026-05-21 GRScenes Render Manifest Full no-MDL Overlay

## Summary

Updated the GRScenes render-manifest generator so the selected ACL/VLM targets
can use the completed full no-MDL apply report instead of the older one-scene
pilot scratch paths.

Plain version: the second paper gate has started. The manifest can now find the
original and converted USD inputs for all planned pairs, but no camera stages
or images have been rendered yet.

## Change

`prepare_render_manifest.py` now accepts:

```bash
--nomdl-run-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json
```

When supplied, it overlays each scene's `converted_usd` and
`scratch_scene_root` from the completed full no-MDL runner report. The overlay
requires:

- `status=completed_full_grscenes_nomdl_multi_root_run`;
- `dry_run=false`;
- matching scene split, scene id, and source USD variant.

## Current Evidence

Command:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py \
  --nomdl-run-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json \
  --require-converted
```

Result:

- Output report:
  `paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json`.
- 23 unique targets.
- 92 original/converted render pairs.
- 184 material-condition jobs.
- `converted_jobs_missing_input_count=0`.
- `render_jobs_missing_input_count=0`.
- `camera_stage_missing_count=184`.
- `render_jobs_ready_to_run=0`.

## Next Gate

Author camera stages and run a small USD/render smoke validation before the
full paired render batch. This manifest is still planning evidence, not image
evidence and not VLM score evidence.
