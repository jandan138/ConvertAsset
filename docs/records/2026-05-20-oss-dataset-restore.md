# 2026-05-20 OSS Dataset Restore For GRScenes Test0 Parallel

## Summary

Restored a clean sibling copy of the GRScenes test0 parallel dataset from the
existing Alibaba OSS release prefix after a local no-MDL experiment wrote
`*_noMDL.usd` sidecar files into the working dataset tree, then promoted the
clean copy back to the canonical `dataset/` path.

Current clean reference tree:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset
```

Current no-MDL experiment working tree:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset_no_mdl_work_20260520
```

The initial restore target was
`dataset_oss_restored_20260520`; after verification it was renamed to
`dataset/`. The polluted working tree remains available for experiments that
intentionally use generated no-MDL outputs.

## Source

The OSS source was identified from the upload records in:

```text
/cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep
```

Remote release prefix:

```text
aliyun-beijing-internal:pjlab-bjpai-zhuzihou-assets/GRScenes-test1-parallel-dedup-20260506
```

Relevant external records:

- `docs/operations/grscenes_oss_rclone_runbook.md`
- `docs/records/changes/2026-05-14_invalid_asset_shell_cleanup.md`
- `docs/records/changes/2026-05-16_test0_parallel_glb_generation.md`

## Restore Procedure

The OpenCode `oss-rclone-ops` skill was used from:

```text
/root/.config/opencode/skills/oss-rclone-ops/SKILL.md
```

The active machine only had the `aliyun-beijing-internal:` rclone remote, so the
restore used that configured remote instead of the older documented
`aliyun-a-oss-demo:` alias.

Transfer command:

```bash
REMOTE='aliyun-beijing-internal:pjlab-bjpai-zhuzihou-assets/GRScenes-test1-parallel-dedup-20260506'
DEST='/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset_oss_restored_20260520'

env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy \
  rclone copy "$REMOTE" "$DEST" \
  --transfers 32 \
  --checkers 64 \
  --stats 30s \
  --stats-one-line \
  --log-file /tmp/convertasset_oss_restore_20260520.log \
  --log-level INFO
```

After verification, the directories were renamed in the same parent directory:

```bash
BASE='/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel'
mv "$BASE/dataset" "$BASE/dataset_no_mdl_work_20260520"
mv "$BASE/dataset_oss_restored_20260520" "$BASE/dataset"
```

## Verification

Remote preflight:

- Bucket root listed `GRScenes-test1-parallel-dedup-20260506/`.
- Release prefix top level listed `GRScenes100/`, `GRScenes_assets/`, and
  `Material/`.
- Remote sample scene directory
  `GRScenes100/home/MV7J6NIKTKJZ2AABAAAAADQ8_usd/` listed only `layout.usd`.
- `rclone size` reported `394474` objects and `271.059 GBytes`.
- A recursive remote include probe for `*_noMDL.usd` returned no objects.

Local restore checks:

```text
top_level:
GRScenes100
GRScenes_assets
Material
layout_count=99
home_layout_count=69
commercial_layout_count=30
sample_layout_files:
layout.usd
```

Known local pollution candidates:

```text
candidate_count=452
restored_candidate_exists=0
```

Post-rename checks:

```text
clean=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset
work=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset_no_mdl_work_20260520
clean_candidate_exists=0
work_candidate_exists=452
clean_sample_files=layout.usd
work_sample_files=layout.usd, layout_noMDL.usd, layout_noMDL_audit.json, layout_noMDL_summary.txt
```

Full remote-to-local check:

```text
rclone check: 0 differences found
rclone check: 394474 matching files
```

An additional `rg --files "$DEST" -g '*_noMDL.usd'` scan returned no paths.

## Operational Decision

Do not delete files from the original `dataset/` directory as part of this
restore record. The known sidecar candidates are still tracked at:

```text
/tmp/convertasset_no_mdl_pollution_candidates.txt
```

Future ConvertAsset experiments should prefer one of these two modes:

- Read-only experiments against the canonical clean `dataset/`.
- Write-producing conversion experiments against an explicit scratch/output
  directory or `dataset_no_mdl_work_20260520/`, never against the clean
  reference tree.
