# 2026-05-20 GRScenes VLM Source Manifest

## Summary

Added a pure-Python source manifest generator for the ACL/VLM GRScenes pilot. It prepares the scene and episode selection before any Isaac Sim rendering, VLM inference, or no-MDL conversion.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_source_manifest.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/source_manifest.json`
- `tests/test_grscenes_vlm_manifest.py`

## Current Output

Command:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_source_manifest.py
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/source_manifest.json
```

The generated manifest currently contains:

- 5 episode-backed home scenes.
- 5 metadata-driven commercial stress scenes.
- 40 selected episode records: 8 per selected home scene.
- 7 excluded episode records whose metadata model path did not match uniquely under the current source-only mapping gate.
- Scratch scene roots under `/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520/scenes/GRScenes-100/...`.

## Design Notes

- The generator does not copy files, open USD stages, run Isaac Sim, or execute ConvertAsset.
- The manifest records source hashes, protocol hash, Git commit, source USD paths, scratch USD paths, stable episode IDs, JSON pointers, episode hashes, object category, model hash, instance index, and metadata match counts.
- `mapping_status` remains `pending_metadata_to_prim` because final instance-level target localization should be verified against USD prim paths through `pxr` or Isaac Sim.
- Commercial scenes are marked `metadata_driven_commercial_stress` and are not paper-claim eligible as episode-backed results.

## Review Findings Integrated

- Current `no-mdl` writes sibling `*_noMDL.usd` files beside the input USD and has no `--out-root`; never run it directly in `/cpfs/user/zhuzihou/assets/zzh-grscenes`.
- Scratch paths mirror the original GRScenes layout so scene-local `Materials` and `models` pointer files can keep their relative meaning after a future copy step.
- Episode keys can be parsed into `object_category`, `model_hash`, and `instance_index`; metadata confirms asset identity but final per-instance localization needs USD prim-path matching.

## Verification

Fresh checks run after implementation:

```bash
python -m pytest tests/test_grscenes_vlm_manifest.py -q
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_source_manifest.py
```

## Open Work

- Implement a scratch-copy materializer that copies selected scene directories plus required split-level `Materials` and `models` directories.
- Add a `pxr` or Isaac Sim target mapper that resolves episode object IDs to USD prim paths and world bounds.
- Add an explicit no-MDL `--out-root` mode or keep conversion restricted to copied scratch scenes.
- Generate paired render records only after the source manifest, scratch copy, target mapping, and no-MDL conversion gates pass.
