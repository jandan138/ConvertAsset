# 2026-05-20 GRScenes VLM Target Resolver

## Summary

Added the read-only target-localization gate for the ACL/VLM GRScenes pilot. The new resolver turns selected `source_manifest.json` episode records into concrete USD prim paths and world-space bboxes, which are required before paired original/no-MDL rendering.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/target_manifest.json`
- `tests/test_grscenes_vlm_target_resolver.py`
- `docs/superpowers/plans/2026-05-20-grscenes-target-resolver.md`

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
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/target_manifest.json
```

The generated manifest currently contains:

- 5 attempted episode-backed home scenes.
- 40 attempted episode records.
- 40 records resolved to USD prim paths.
- 40 records resolved to world-space bboxes.
- 23 unique `(scene, object_instance_id, target_prim_path)` targets after duplicate episode records are collapsed.
- 17 duplicate episode-record targets, with at most 2 episode records mapped to the same unique target.
- No unresolved selected episode records.

## Design Notes

- The resolver is read-only against `/cpfs/user/zhuzihou/assets/zzh-grscenes`.
- It opens original scene USDs through Isaac/pxr and does not run no-MDL conversion, rendering, copying, or in-place asset mutation.
- It first matches episode targets through authored USD reference paths against `metadata_model_paths`.
- It includes exact prim-suffix fallback for valid targets that are absent from `interactive_obj_list.json`.
- It computes bbox via `model_local_bbox_x_scene_xform`: open the absolute split-level model USD, compute model local bbox, then transform bbox corners with the source scene prim transform.
- This bbox strategy is necessary because GRScenes scene-local `models` and `Materials` entries are regular text pointer files, so composed scene bboxes can emit broken relative-reference warnings in the immutable source layout.
- The manifest records exact generator command, resolver script hash, and git status in `generator_provenance` so the artifact is auditable even before a follow-up commit makes the generator path immutable.
- The CLI refuses `--out` paths under the benchmark source root to avoid accidental JSON sidecars inside `/cpfs/user/zhuzihou/assets/zzh-grscenes`.

## Review Findings Integrated

- `interactive_obj_list.json` is incomplete for static or non-pickable targets; it cannot be the only mapping source.
- Duplicate model hashes require matching the full `model_<hash>_<instance_index>` suffix or reference path, not hash alone.
- Direct composed bbox on the scene prim is unreliable for this local source layout; the model bbox plus scene transform is the stable first gate.
- Existing `convert_asset/camera/orbit.py` has the strongest bbox defensive pattern, but it imports `pxr` at module import time, so the experiment resolver keeps all `pxr` imports lazy.
- Review flagged that 40 episode records are not 40 unique spatial targets; docs and manifest summary now report 23 unique targets and 17 duplicate episode-record targets.

## Verification

Fresh checks run after implementation:

```bash
python -m pytest tests/test_grscenes_vlm_target_resolver.py -q
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py \
  --limit-scenes 1 \
  --out /tmp/grscene_target_manifest_smoke.json
./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py \
  2>/tmp/grscene_target_resolver_usd_warnings.log
```

The full run wrote `target_manifest.json` with 40 records across 5 scenes. USD emitted relative-reference warnings into `/tmp/grscene_target_resolver_usd_warnings.log`; these are expected for the original source layout and are not committed.

## Open Work

- Generate paired camera/view plans from `target_manifest.json`.
- Materialize safe scratch scenes or add no-MDL `--out-root` before conversion.
- Render original/no-MDL paired images with identical target, camera, and prompt metadata.
- Run coordinate-capable VLM inference and scoring only after render provenance is registered.
