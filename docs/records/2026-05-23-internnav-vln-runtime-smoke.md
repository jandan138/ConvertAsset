# 2026-05-23 InternNav VLN Runtime Smoke

## Scope

This record documents the first real InternNav / InternVLA-N1 downstream smoke
run over a ConvertAsset-controlled GRScenes original vs no-MDL pair. It upgrades
the ACL downstream story from "prepared input bridge" to "real embodied protocol
evidence", but only for one episode.

## Plain-Language Status

通俗版本：我们已经不只是准备好了 InternNav 的输入，而是真的把 InternNav
模型和 Isaac 仿真跑起来了。它跑了同一个导航任务两次：一次用原始 GRScenes
USD，一次用 no-MDL 后的 USD。

两个版本都没有成功到达目标，所以这不是“方法提升导航成功率”的证据。真正有
价值的是：同一个任务在 no-MDL 版本里走得更远、最后离目标更远，说明材质/纹理
转换会影响真实 embodied agent 的行为。这可以作为 ACL story 里的 downstream
sensitivity smoke，但还不能作为大规模 benchmark 结论。

## Runtime Route

The run uses the ConvertAsset wrapper:

```text
paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py
```

The wrapper runs through:

```bash
./scripts/isaac_python.sh paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py \
  --config /cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523/configs/original_eval_cfg.py
```

and the converted config swaps the scene-data root:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523/configs/converted_eval_cfg.py
```

External runtime dependency root:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523
```

This root is intentionally outside git and was about 17 GiB during the run.

## Compatibility Fixes

The wrapper records and applies these practical fixes:

- prepend external `python_target`, `internutopia_probe`, and InternNav to `PYTHONPATH`;
- set `HF_HOME` to the external runtime cache;
- force `HF_HUB_DISABLE_XET=1` so parent shell settings cannot re-enable Xet;
- alias `pkg_resources.packaging` for LongCLIP compatibility;
- disable the transformers sklearn probe to avoid Isaac/NumPy/SciPy conflicts;
- fall back from `flash_attention_2` to `sdpa` when `flash_attn` is unavailable;
- patch Lumina gradient-checkpointing signature compatibility;
- set NextDiT checkpoint `ffn_dim_multiplier` default to `2/3`;
- disable InternNav debug videos to avoid extra `imageio`/`ffmpeg` dependencies and large artifacts.

## Results

Canonical paired summary:

```text
paper/shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json
```

InternNav result files:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_mini/result.json
/cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json
```

Metrics:

| condition | TL | NE | SR | SPL | Count | result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| original | 64.7729 | 8.3585 | 0.0 | 0.0 | 1 | `exceed_total_max_step` |
| no-MDL | 98.2783 | 42.1053 | 0.0 | 0.0 | 1 | `exceed_total_max_step` |
| no-MDL minus original | +33.5054 | +33.7468 | 0.0 | 0.0 | 0 | longer path, larger final error |

The original run lasted `721.31 s` with `step_count=1100`. The no-MDL run lasted
`1156.79 s` with `step_count=1100`.

## Claim Boundary

This smoke result supports:

- the real InternNav / VL-LN bridge is executable from ConvertAsset;
- original vs no-MDL paired scene inputs can produce real SR/SPL/TL/NE metrics;
- material conversion can change the embodied action trajectory and final error.

It does not support:

- a success-rate improvement claim;
- a broad InternNav benchmark claim;
- a statistically stable ACL-main conclusion by itself.

## Verification

Commands run:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py \
  --max-episodes 1 \
  --scene-id MV7J6NIKTKJZ2AABAAAAADY8_usd

./scripts/isaac_python.sh paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py \
  --config /cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523/configs/original_eval_cfg.py

./scripts/isaac_python.sh paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py \
  --config /cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523/configs/converted_eval_cfg.py

python paper/shared/evidence/experiments/07_internnav_vln_downstream/collect_results.py \
  --prep-manifest paper/shared/evidence/raw/internnav_vln_downstream/prep_manifest.json \
  --original-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_mini/result.json \
  --converted-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json \
  --output paper/shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json
```

Expected collector output:

```text
{"metric_deltas": {"Count": 0.0, "FR": 0.0, "NE": 33.7468, "OS": 0.0, "SPL": 0.0, "SR": 0.0, "StR": 0.0, "TL": 33.5054}, "split": "mini"}
```

## Next Step

Run a small multi-episode batch before paper-level claims: keep the same wrapper,
sample more GRScenes SN episodes, collect aggregate means and failure cases, and
separate "both failed but trajectory changed" from "success metrics changed".
