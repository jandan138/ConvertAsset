# 2026-05-23 InternNav VLN Downstream Prep

## Scope

This record documents the first concrete InternNav / VL-LN downstream bridge for
the ACL story. It prepares a paired GRScenes original vs no-MDL navigation input
for InternNav. The follow-up real runtime smoke is recorded in
`2026-05-23-internnav-vln-runtime-smoke.md`.

## Plain-Language Status

通俗版本：我们现在把“能不能跑 InternNav”拆成两层了。

第一层是数据输入层：InternNav 要 `json.gz` episodes 和每个 scene 的
`fixed.usd`。这一层已经打通。我们已经从 GRScenes 的 `sn_episodes.json`
生成了一个 mini VLN episode，并给同一个 scene 建了 original 和 no-MDL 两套
`fixed.usd` 入口。

第二层是真实仿真/模型层：这需要 InternUtopia、H1 robot、InternVLA checkpoint
和相关 Python 依赖。这个层已经通过外部 runtime 目录和 ConvertAsset wrapper
跑通了一个真实 smoke；这份记录保留输入准备过程，真实指标见 runtime smoke 记录。

## What Was Built

- Added `paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py`.
  It converts GRScenes SN episodes into InternNav's expected
  `<base>/<split>/<split>.json.gz` format and creates external work-root
  `fixed.usd` links.
- Added `paper/shared/evidence/experiments/07_internnav_vln_downstream/collect_results.py`.
  It will collect paired InternNav `result.json` files into
  `paper/shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json`
  once real runs exist. It rejects result paths that do not match the manifest's
  expected InternNav log suffixes and rejects metric `Count` values that do not
  match the prepared episode count.
- Added `tests/test_internnav_vln_downstream_prep.py` covering dataset prep,
  missing converted USD reporting, scene-id filtering, and result delta
  collection.
- Generated `paper/shared/evidence/raw/internnav_vln_downstream/prep_manifest.json`.
- Added `paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py`
  after runtime provisioning. The wrapper runs InternNav through ConvertAsset's
  Isaac Python entry, injects the external runtime dependency root, forces
  `HF_HUB_DISABLE_XET=1`, and applies compatibility patches recorded in the
  manifest.

## Prepared Smoke Pair

Scene:

```text
MV7J6NIKTKJZ2AABAAAAADY8_usd
```

Work root:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523
```

Prepared dataset:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523/datasets/grscene_sn_mini/mini/mini.json.gz
```

Original scene entry:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523/scene_data/original/MV7J6NIKTKJZ2AABAAAAADY8_usd/fixed.usd
```

Converted scene entry:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523/scene_data/converted/MV7J6NIKTKJZ2AABAAAAADY8_usd/fixed.usd
```

Both `fixed_docker.usd` aliases are also created because InternNav switches file
name inside containers.

## Source Safety

The clean source tree remains unmodified:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes
```

The no-MDL navigation USD was generated only in the scratch tree:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes/scenes/MV7J6NIKTKJZ2AABAAAAADY8_usd/start_result_navigation_noMDL.usd
```

Command used:

```bash
./scripts/isaac_python.sh ./main.py no-mdl --only-new-usd \
  /cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes/scenes/MV7J6NIKTKJZ2AABAAAAADY8_usd/start_result_navigation.usd
```

## Runtime Status

The generated manifest still says `ready_for_internnav_runtime`, which means the
asset/episode inputs are paired and present. It now also records the wrapper and
external runtime metadata used by the 2026-05-23 smoke run.

Runtime assets are external to git:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523
```

This directory supplies the local InternUtopia probe, Python target packages, HF
cache, H1 robot asset, depth checkpoint, and InternVLA-N1 checkpoint symlinks
used by `/cpfs/user/zhuzihou/dev/InternNav`.

## Verification

Focused tests:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

Result:

```text
13 passed
```

Smoke prep:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py \
  --max-episodes 1 \
  --scene-id MV7J6NIKTKJZ2AABAAAAADY8_usd
```

Result:

```json
{"blocked_by": [], "can_run_paired_eval": true, "status": "ready_for_internnav_runtime"}
```

Smoke result collection:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/collect_results.py \
  --prep-manifest paper/shared/evidence/raw/internnav_vln_downstream/prep_manifest.json \
  --original-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_mini/result.json \
  --converted-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json \
  --output paper/shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json
```

Result:

```text
TL delta +33.5054, NE delta +33.7468, SR/SPL unchanged at 0.0.
```

## Next Step

Scale beyond this one-episode smoke run: repeat over more GRScenes SN episodes,
record aggregate statistics, and keep the ACL claim bounded to embodied
downstream sensitivity unless success-rate differences emerge from a larger run.
