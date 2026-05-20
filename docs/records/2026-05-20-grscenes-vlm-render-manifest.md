# 2026-05-20 GRScenes VLM Render Manifest

## Summary

Added the render-planning gate for the ACL/VLM GRScenes pilot. The new generator consumes `target_manifest.json`, collapses duplicate episode records into unique spatial targets, and writes paired original/no-MDL render jobs with shared camera metadata.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json`
- `tests/test_grscenes_vlm_render_manifest.py`
- `docs/superpowers/plans/2026-05-20-grscenes-render-manifest.md`

## Files Updated

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- `paper/shared/evidence/results_manifest.yaml`
- `paper/venues/acl27/STATUS.md`
- `docs/records/README.md`
- `docs/superpowers/README.md`

## Current Output

Command:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json
```

The generated manifest currently contains:

- 40 resolved episode records as input.
- 23 unique spatial render targets after duplicate episode references are collapsed.
- 4 target-centered views per unique target.
- 92 original/converted view pairs.
- 184 material-condition render jobs.
- 92 original jobs with material inputs available but `planned_camera_stage_pending`.
- 92 converted jobs marked `blocked_missing_material_input` because scratch no-MDL USDs have not yet been generated.
- 184 jobs with camera USD stages still pending.
- 0 jobs ready to run directly through the viewport capture script.

## Design Notes

- The generator is pure Python and imports no `pxr`, `omni`, or Isaac Sim modules.
- It does not open USD stages, render images, copy scenes, run no-MDL conversion, or mutate `/cpfs/user/zhuzihou/assets/zzh-grscenes`.
- Duplicate `mm` / `sn` episode records are preserved as `linked_episode_ids` and `linked_episodes` on the unique render target.
- Duplicate episode records for the same spatial target are rejected if their category, world bbox, bbox method, or resolved model path diverges.
- Each original/converted pair stores a single shared camera plan, so later rendering can keep target, view, resolution, intrinsics, and renderer settings fixed across material conditions.
- The flat `records` list is shaped for future VLM input and independent visual review. It includes `sample_id`, `pair_id`, material condition, target category, world bbox, planned image path, render command template, normalized S1 category-pointing prompt, source episode instructions/prompts for provenance, and `visual_review` metadata.
- Image-space target boxes are intentionally `pending_projection_from_world_bbox`; VLM scoring must wait until rendered images and image-space boxes or masks exist.
- The manifest records the target manifest hash and script provenance so the render plan can be audited before image generation.

## Review Findings Integrated

- The manifest keeps both target-level grouping and flat records so duplicate episode prompts are not lost.
- Original and converted conditions share identical camera metadata.
- Converted inputs are not assumed to exist; missing scratch derivatives become blocking status fields.
- Existing material inputs and missing camera stages are represented separately so a planned command is not mistaken for a runnable render.
- S1 VLM prompt text is normalized to `Point to the {category}.`; original episode instructions and prompts remain provenance fields.
- The clean-room `render-visual-reviewer` skill was added globally and referenced from each planned visual-review packet.

## Verification

Fresh checks run during implementation:

```bash
python -m pytest tests/test_grscenes_vlm_render_manifest.py -q
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py
python -m py_compile paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py
```

## Open Work

- Materialize scratch copies of selected GRScenes scenes with
  `materialize_scratch.py`, then run no-MDL conversion on scratch USDs.
- Add the runner that authors camera USDs and renders the planned original/no-MDL image pairs.
- Project world bboxes or masks into image-space boxes for VLM scoring.
- Use the clean-room visual reviewer on render samples before treating image outputs as paper evidence.
