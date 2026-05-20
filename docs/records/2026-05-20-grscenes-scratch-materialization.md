# 2026-05-20 GRScenes Scratch Materialization

## Summary

Added a pure-Python scratch materialization gate for the ACL/VLM GRScenes pilot.
The new script prepares selected benchmark scenes for no-MDL conversion outside
the immutable GRScenes source tree.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py`
- `tests/test_grscenes_vlm_materialize_scratch.py`
- `docs/superpowers/plans/2026-05-20-grscenes-scratch-materialization.md`

## Design Notes

- The script reads `source_manifest.json` and validates that the scratch root is
  outside `/cpfs/user/zhuzihou/assets/zzh-grscenes`.
- It mirrors selected scene directories plus split-level `Materials/` and
  `models/` resource trees, because scene-local entries are text pointer files
  containing `../../Materials` and `../../models`.
- The default copy mode is `hardlink` to avoid duplicating the shared material
  tree. Top-level resource destinations must be real scratch directories, not
  symlinks back into the source tree.
- GRScenes `models/` contains many internal relative symlinks such as
  per-model `Materials -> ../../../../../Materials`. The materializer preserves
  those asset-internal symlinks and validates that their scratch-side targets
  still resolve inside the scratch root.
- Hardlinked files share inodes with the benchmark source; this mode relies on
  ConvertAsset no-MDL writing sidecar outputs rather than editing existing input
  files in place. Use `--copy-mode copy` when physical isolation is required.
- Existing scratch destinations are treated as reusable only after relative
  path, entry type, file-size, symlink-text, and symlink-target validation. This
  prevents an interrupted or stale materialization from being silently accepted
  as complete.
- The script does not import `pxr`, `omni`, or Isaac Sim, and does not run
  no-MDL conversion by itself.
- The generated `scratch_materialization_report.json` is preparation provenance,
  not rendered image evidence and not a VLM result.

## Execution Result

One-scene materialization was executed after cleaning an earlier interrupted
scratch attempt:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py --limit-scenes 1
```

Result:

- Report: `paper/shared/evidence/raw/grscene_vlm_grounding/scratch_materialization_report.json`
- Summary: `scene_count=1`, `resource_tree_count=2`,
  `copy_mode=hardlink`, `created_count=3`, `exists_count=0`.
- Scratch scene USD exists and is a hardlink to the source scene USD
  (`same_inode=True`, link count 2).
- Sample internal `models/.../Materials` symlink is preserved and resolves to
  scratch `home_scenes/Materials`.
- `prepare_render_manifest.py --require-converted` still fails with
  `converted USD is missing for 92 render jobs`, which is expected until no-MDL
  derivatives are generated.

## Storage Guardrail

User-provided storage snapshot on 2026-05-20 18:55:02:

- Total storage: 1600.0 GiB
- Used storage: 1128.823 GiB
- File quota: 100,000,000
- Used files: 2,620,642

The one-scene scratch tree exposes about 104G of hardlinked data when measured
with `du`, plus 141,082 visible files, 27,819 internal symlinks, and 52,601
directories. This is acceptable only as a one-scene pilot. Do not run full-scene
or full-dataset materialization with the current split-level mirror approach.
The next implementation step must be a target/reference-closure materializer
that copies or hardlinks only assets needed by selected target prims.

## Current Command

Dry-run one selected scene:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py \
  --limit-scenes 1 \
  --dry-run
```

Execute one selected scene after reviewing the dry-run report:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py \
  --limit-scenes 1
```

Then run no-MDL on the scratch USD:

```bash
./scripts/isaac_python.sh ./main.py no-mdl \
  /cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520/scenes/GRScenes-100/home_scenes/scenes/<scene_id>/start_result_raw.usd
```

## Verification

Fresh checks run during implementation:

```bash
python -m pytest tests/test_grscenes_vlm_materialize_scratch.py -q
python -m pytest tests/test_grscenes_vlm_materialize_scratch.py tests/test_grscenes_vlm_render_manifest.py -q
python -m py_compile paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py --limit-scenes 1 --dry-run --out /tmp/grscenes_scratch_materialization_report.json
python -m pytest -q
```

## Open Work

- Replace split-level resource-tree mirroring with target/reference-closure
  materialization before scaling beyond this one-scene pilot.
- Run no-MDL conversion on scratch USDs and keep conversion logs.
- Add residual MDL, unresolved reference, and stage-open validation after
  conversion.
- Regenerate `render_manifest.json` with `--require-converted` after converted
  USDs exist.
