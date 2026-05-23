# 2026-05-23 InternNav VLN Downstream Prep

## Scope

This record documents the first concrete InternNav / VL-LN downstream bridge for
the ACL story. It prepares a paired GRScenes original vs no-MDL navigation input
for InternNav, but it does not claim SR/SPL results yet.

## Plain-Language Status

通俗版本：我们现在把“能不能跑 InternNav”拆成两层了。

第一层是数据输入层：InternNav 要 `json.gz` episodes 和每个 scene 的
`fixed.usd`。这一层已经打通。我们已经从 GRScenes 的 `sn_episodes.json`
生成了一个 mini VLN episode，并给同一个 scene 建了 original 和 no-MDL 两套
`fixed.usd` 入口。

第二层是真实仿真/模型层：这需要 InternUtopia、H1 robot、InternVLA checkpoint
和相关 Python 依赖。当前机器还没准备好这一层，所以还没有 SR/SPL/goal success
真实指标。

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

## Current Runtime Blockers

The generated manifest says `ready_for_internnav_runtime`, which means the
asset/episode inputs are paired and present. It does not mean the real model run
has happened.

Observed blockers:

- InternNav official eval shell expects `/root/miniconda3`, but the available
  conda install is under `/cpfs/user/zhuzihou/conda-managed/miniforge3`.
- There is no `internutopia` conda environment in that install.
- Normal Python misses `internutopia`, `internutopia_extension`, `lmdb`,
  `msgpack_numpy`, `torch`, `transformers`, and `omni`.
- ConvertAsset Isaac Python has `torch` and `omni`, but still misses
  `internutopia`, `internutopia_extension`, `lmdb`, `msgpack_numpy`, and
  `transformers`.
- `/cpfs/user/zhuzihou/dev/InternNav/data/Embodiments/vln-pe/h1/h1_internvla.usd`
  is missing.
- `/cpfs/user/zhuzihou/dev/InternNav/checkpoints/InternVLA-N1-DualVLN` is missing.

## Verification

Focused tests:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

Result:

```text
4 passed
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

## Next Step

The next real unblock is not more ConvertAsset code. It is provisioning an
InternNav runtime with InternUtopia, robot assets, and a real VLN model
checkpoint. Once that exists, run the two generated eval configs and feed both
`result.json` files to `collect_results.py`.
