# 2026-05-20 ACL GRScenes Dataset Role Correction

## Summary

The ACL/VLM experiment documentation now separates the original GRScenes benchmark source from local ConvertAsset engineering validation mirrors.

## Decision

- `/cpfs/user/zhuzihou/assets/zzh-grscenes` is the immutable benchmark source for ACL/VLM scene selection, episode metadata, and paper claims.
- `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset` is a restored clean engineering mirror for ConvertAsset smoke tests, runner debugging, and path validation.
- `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset_no_mdl_work_20260520` is a no-MDL work tree for engineering validation outputs.
- ACL/VLM no-MDL derivatives should be generated from scratch copies of selected benchmark scenes, not in the original GRScenes benchmark tree.

## Rationale

The processed `test0_transitive_apply_parallel` dataset is useful for validating ConvertAsset behavior, but it is not the right source for benchmark claims because it lacks the full original benchmark organization around scene metadata, `mm_episodes.json`, `sn_episodes.json`, robots, and task-specific USD scene variants.

The original `zzh-grscenes` package is better aligned with ACL/InternNav/VLM experiments because it contains the scene USDs, benchmark episodes, object metadata, and ecosystem structure expected by downstream embodied-language evaluations.

## Local Inventory Check

Checked locally on 2026-05-20:

- `zzh-grscenes` contains 69 home scenes and 30 commercial scenes, 99 total.
- Every checked scene directory contains `start_result_raw.usd`, `start_result_navigation.usd`, `start_result_interaction.usd`, `metadata.json`, and `interactive_obj_list.json`.
- `mm_episodes.json` covers 30 home scenes and 420 episodes: 291 test episodes and 129 validate episodes.
- `sn_episodes.json` covers the same 30 home scenes and 300 episodes: 200 test episodes and 100 validate episodes.
- All episode-covered scene IDs map to a local `GRScenes-100/*_scenes/scenes/<scene_id>/` directory.
- Commercial scenes have no local `mm_episodes.json` / `sn_episodes.json` coverage.
- Scene-local `Materials` and `models` entries are pointer files containing relative paths, not symlinks.
- The GRScenes README records the asset license as CC BY-NC-SA 4.0.

The first ACL/VLM episode-backed pilot should therefore use the 30 episode-covered home scenes as the primary pool. Commercial scenes can still be used for metadata-driven material-generalization stress tests, but not as official episode-backed benchmark results unless a future episode source is added. The full 99-scene pool can be used later for broader stress tests after target/metadata mapping is verified.

## Documentation Updated

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/protocol.yaml`
- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- `paper/shared/evidence/references/acl_vlm_benchmark_selection.md`
- `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- `paper/EXPERIMENT_CHECKLIST.md`
- `paper/venues/acl27/STATUS.md`
- `docs/records/2026-05-20-acl-vlm-benchmark-route.md`

## Open Work

- Add an explicit scratch-copy or output-root workflow before any full ACL/VLM conversion run.
- Make render manifests record `dataset_role`, `source_dataset_id`, `scene_provenance`, `source_usd`, `converted_usd`, and conversion command.
- Use the restored engineering mirror only for quick no-MDL smoke tests and runner integration checks.
- Open 2-3 `start_result_*` scene variants with Isaac Sim or `pxr` before declaring the source tree runner-ready.
- Verify that episode object IDs map cleanly through `metadata.json` to USD prim paths and projected image boxes or masks.
- Keep PIO wording as prompt/metric inspiration unless a future protocol explicitly evaluates on the PIO dataset.
