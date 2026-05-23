# InternNav VLN Downstream Bridge

This directory prepares ConvertAsset-controlled GRScenes original vs no-MDL
inputs for InternNav / VL-LN evaluation.

## What Is Ready

`prepare_minipair.py` converts GRScenes `benchmark/sn_episodes.json` records into
InternNav's expected dataset layout:

```text
<work_root>/datasets/grscene_sn_mini/mini/mini.json.gz
<work_root>/scene_data/original/<scene_id>/fixed.usd
<work_root>/scene_data/converted/<scene_id>/fixed.usd
<work_root>/configs/original_eval_cfg.py
<work_root>/configs/converted_eval_cfg.py
```

The default work root is outside git:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523
```

The repo evidence manifest is:

```text
paper/shared/evidence/raw/internnav_vln_downstream/prep_manifest.json
```

## Current Smoke Pair

The first prepared pair uses:

```text
MV7J6NIKTKJZ2AABAAAAADY8_usd
```

Original `fixed.usd` links to the clean GRScenes source tree. Converted
`fixed.usd` links to `start_result_navigation_noMDL.usd` generated only in the
scratch tree:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521
```

Do not run no-MDL conversion inside `/cpfs/user/zhuzihou/assets/zzh-grscenes`.

## Commands

Prepare or refresh the smoke pair:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py \
  --max-episodes 1 \
  --scene-id MV7J6NIKTKJZ2AABAAAAADY8_usd
```

If the converted navigation USD is missing, generate it from the scratch copy:

```bash
./scripts/isaac_python.sh ./main.py no-mdl --only-new-usd \
  /cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes/scenes/MV7J6NIKTKJZ2AABAAAAADY8_usd/start_result_navigation.usd
```

After InternNav produces both `result.json` files, collect paired metrics:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/collect_results.py \
  --original-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_mini/result.json \
  --converted-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json
```

`collect_results.py` is intentionally strict: each result path must end with the
expected log suffix recorded in `prep_manifest.json`, and each result split's
`Count` must match the prepared episode count. This prevents stale or unrelated
InternNav runs from becoming paper evidence by accident.

## Current Runtime Blockers

The input pair is ready for an InternNav runtime, but SR/SPL metrics have not
been produced yet. Current blockers are:

- no `internutopia` conda environment in the local conda-managed install;
- missing `internutopia`, `internutopia_extension`, `lmdb`, `msgpack_numpy`,
  and `transformers`;
- missing `data/Embodiments/vln-pe/h1/h1_internvla.usd`;
- missing `checkpoints/InternVLA-N1-DualVLN`.

Isaac Python has `torch` and `omni`, but not the InternNav/InternUtopia stack.
