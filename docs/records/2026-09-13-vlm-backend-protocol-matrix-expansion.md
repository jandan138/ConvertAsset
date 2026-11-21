# 2026-09-13: VLM 后端 × 协议矩阵实验扩展（ARR 4 分主线实验）

> **2026-09-15 更正与接续：** 本记录是探索历史，不是当前 ICLR 的数值依据。后续检查发现
> 条件命中率使用不同解析子集、normalized 坐标误标为像素位移、部分旧图被替换，以及
> 未修复红色材质渲染混入输入池。原先的“−0.28~+0.28”与“主要方差来源”等总结不能
> 直接沿用。当前采用固定分母重算和干净四来源干预，详见
> [ICLR 迁移记录](2026-09-15-iclr-model-behavior-migration.md)。本地 99 个 episode 与本地
> split 文件相等，也不独立证明已下载所有公开 benchmark 数据。

## 目标

在 frozen expanded30 stress set 与新建 extended80 诊断池上，把"VLM grounding 协议可靠性"
故事从 2 个 backend 扩到 4+ 个 backend，并新增协议敏感性矩阵、s2 任务族、多视角一致性与
材质效应归因四组主线证据。不改论文正文，先出原始结果。

## 背景与假设

- 主线故事：材质转换是受控的 VLM-grounding 干预；测量接口（backend、坐标系、
  响应格式）本身是被 benchmark 当作固定的隐藏任务因子。
- 假设：同一冻结干预下，测得的 grounding 稳定性随 backend 与 prompt 协议显著变化。
- 环境：RTX 4090 46GB；`/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.venv_dlc`
  （transformers 5.2.0，Qwen/通用 HF）；`/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310`
  （unsloth，Gemma4 专用）。
- 模型下载走 `HF_ENDPOINT=https://hf-mirror.com`（huggingface.co 直连超时，镜像可用），
  缓存到 `/cpfs/user/zhuzihou/models/hf_cache`。

## 改动（脚本）

只改 `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/`：

1. `run_vlm_predictions.py`
   - 新增 `local_hf_generic` backend（AutoProcessor + AutoModelForImageTextToText，
     支持 `--model-class` 指定 `Qwen3VLForConditionalGeneration` 等），Qwen3-VL/InternVL
     等新一代 VLM 免专用引擎。
   - 新增 `--prompt-type {s1_point, s2_interaction}`；s2 为任务驱动 grounding
     （"The robot must {action}. Point to the object it should interact with."），
     内置 8 个 stress 类别的 action 映射，评分仍用同一 object bbox。
2. 新增 `analyze_material_effect_attribution.py`：预测 × effect_sample_manifest
   联结，输出 per-backend × per-effect 的点位移/翻转统计。
3. 新增 `aggregate_stress_backend_matrix.py`：扫描预测文件，输出
   backend × prompt_type × coord × fmt 大矩阵 CSV + 多视角一致性 JSON。
4. 新建 extended80 诊断池 `stress_extended80_projection_report.json`（160 条）：
   合并 retake/zoom/expansion/replacement 5 个 projection report，按 pair_id 去重，
   全部图片在盘；标记 `extended80_diagnostic_pool_not_frozen_canonical`，
   frozen expanded30 仍为 canonical。

## 运行与结果

### 新跑预测（全部 600×450、max_new_tokens=64、temperature=0）

- stress30（60 条/配置）：Gemma4/Qwen2.5-7B/Qwen3-VL-2B/Qwen3-VL-8B ×
  {normalized_1000, pixel} × {json, structured_text} + s2_interaction，共 20 配置。
- extended80（160 条/配置）：4 backend × structured+n1000 canonical + s2。
- clean_pool（30 条）：补 Qwen3-VL-2B/8B。
- 输出：`stress_expanded30_probes/`、`stress_extended80_probes/`、`clean_pool_probes/`，
  每个均有 `.metadata.json` provenance 与 `_score_summary.json`。

### 关键数字（stress30 canonical structured+n1000，n1k point hit O/C）

| backend | answer O/C | n1k hit O/C | 备注 |
|---|---|---|---|
| Gemma4-E4B-4bit | 1.00/1.00 | 0.90/0.97 | canonical 已有 |
| Qwen2.5-VL-7B | 0.93/0.92 | 0.10/0.10 | 契约破裂 |
| Qwen3-VL-2B | 1.00/1.00 | 0.87/0.87 | 稳定 |
| Qwen3-VL-8B | 1.00/1.00 | 0.93/0.97 | 最稳 |

### 协议矩阵（同一批图片，测得的材质 delta 随协议变号）

- Gemma4：structured+n1000 +0.07；json+n1000 −0.03；json+pixel −0.07；s2 0.00。
- Qwen2.5-7B：json+n1000 0.44→0.17（−0.27）；pixel+json 原始像素命中 1.00/1.00；
  structured+pixel 0.92→0.80。同一模型同一批图，材质敏感度估计从 0 到 −0.27。
- Qwen3-VL-8B：四种协议全部 0.93/0.97（永远输出 normalized-1000，忽略 pixel 请求）。
- Qwen3-VL-2B：structured+pixel 时才部分遵守 pixel（0.50/0.53），其余全 normalized。
- 点位移 mean_prediction_point_delta_px：18.8（qwen3-2b structured+pixel）
  到 94.4（Qwen2.5 structured+n1000）px —— 敏感度估计本身依赖协议。

### extended80（更宽视角、更难；structured+n1000）

| backend | answer O/C | n1k O/C | hit agreement | d_px |
|---|---|---|---|---|
| Qwen3-VL-8B | 1.00/1.00 | 0.863/0.850 | 0.9125 | 55.9 |
| Gemma4 | 1.00/1.00 | 0.700/0.650 | 0.85 | 68.6 |
| Qwen3-VL-2B | 1.00/1.00 | 0.537/0.500 | 0.8375 | 70.3 |
| Qwen2.5-7B | 0.789/0.859 | 0.039/0.053 | 0.93 | 140.7 |

- Qwen2.5 在宽视角上首次出现 answer 级不稳定（0.79/0.86），27/80 对答案状态变化，
  含 parse 失败、placeholder 回显（'target category'）、截断（'fauc'）与真实语义翻转。
- 多视角一致性（14 个多视角 target）：Gemma4 跨视角一致率 0.50→0.29（转换降低一致性）；
  qwen3-2b 0.21/0.29、9/14 target 的命中视角集被转换改变；qwen3-8b 0.64/0.50。

### clean_pool（15 对，pilot）

Gemma4 0.533/0.400；Qwen2.5 0.0/0.0；Qwen3-VL-2B 0.200/0.200；Qwen3-VL-8B 0.800/0.867。

### 材质效应归因（6 backend × 30 对）

- 整体 hit flip：Gemma4=2、Qwen2.5=4、Qwen3-2B=2、Qwen3-8B=1、InternVL3=8、Molmo=2。
- 点位移：opacity_transparency 组反而更小（14-16px vs 26-62px）——该 bin 不扰动 grounding；
  normal_bump 覆盖全部 30 对（无法分离）；emission/displacement absent 组 n=4 偏小。
- 输出：`material_effect_attribution/material_effect_attribution.{csv,summary.json}`。

### Molmo-7B（native pointer，第 6 个 backend）

- stress30：structured+n1000 **0.90/0.97**；json+n1000 **0.13/0.03**（JSON 格式几乎摧毁
  pointing）；pixel 模式 0.00；s2 0.80/0.90。extended80：**0.925/0.938**，全部 backend 中最高。
- 行为机理：JSON/pixel 模式下 Molmo 回退到其训练期原生 0-100 坐标帧
  （如 `{"point_xy": [44.5, 60.0]}`），无视 prompt 的 normalized-1000/pixel 指令——
  响应格式对坐标帧合规的控制力强于坐标指令本身。

## 头条数字（供论文写作）

**同一冻结 30 对图片，材质 delta（converted−original n1k hit）跨 backend×协议从
−0.28（Qwen2.5 json+n1000）到 +0.28（InternVL3 s2），摆幅 0.56；协议内 spread：
Qwen2.5 0.278、InternVL3 0.19（含 s2 达 0.42）、Molmo 0.167、Gemma4 0.133、
Qwen3-8B 0.000。视角帧（zoom vs retake）可翻转符号（Gemma4 +0.05 → −0.15）。
答案标签几乎不动（多数 1.00/1.00），移动的是点。结论形状：材质转换的真实效应存在
但温和；测量接口（backend 契约 × 响应格式 × 视角 × 解码）才是 grounding 分数的主要
方差来源。**

## 验证命令

```bash
PY=/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.venv_dlc/bin/python
$PY paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions <jsonl> --out <summary.json>
$PY paper/shared/evidence/experiments/06_grscenes_vlm_grounding/aggregate_stress_backend_matrix.py \
  --predictions ... --out-csv ... --out-multiview ...
$PY paper/shared/evidence/experiments/06_grscenes_vlm_grounding/analyze_material_effect_attribution.py \
  --predictions ... --out-csv ... --out-summary ...
```

## 遗留问题

- Molmo-7B-D-0924 下载完成（断点续传成功）。transformers 5.2 已彻底移除 legacy cache
  （无 `to_legacy_cache`/`from_legacy_cache`），Molmo 2024-09 remote code 与 5.x generate
  不兼容，因此为其建专用 venv `/cpfs/user/zhuzihou/dev/molmo_venv`（py3.10 + torch 2.5.1
  + transformers 4.46.3）。pip 走 aliyun 镜像大文件频繁断流，最终方案：curl -C 断点续传
  预下载全部 wheel 到 `/cpfs/user/zhuzihou/dev/molmo_wheels/`（含 torch 906MB、cudnn 665MB
  等 14 个 nvidia/torch 大包 + 全部小依赖），然后 `pip install --no-index --find-links`。
  注意避开 musllinux 变体、预发布版（rc/a/b）、以及 hf 三方库版本区间
  （huggingface-hub 0.36.2、tokenizers 0.20.4、requests 2.34.2、networkx 3.4.2 配 py3.10）。
  Molmo remote code 在 4.46 下仍需两个小兼容：snapshot blob 的 `image_preprocessing_molmo.py`
  tensorflow 分支改 lazy-import（该分支永不用），runner 侧包 `all_tied_weights_keys` 不需要
  （4.46 无此属性），只需 `use_cache=True` 与图像 dtype 转 bf16。smoke 通过：
  输出 `Point: 450, 600 / Answer: backpack`，符合 structured_text + normalized-1000 契约。
- InternVL3-8B 点输出存在坐标量化（{400,500,600,330,650} 粗网格）与偶发 10× 越界
  （y=3300），导致 mean displacement 被 outliers 拉大（677px）——写作时位移指标应报
  median 或 winsorized，hit-rate 指标不受影响（越界=miss 已正确计入）。
- InternVL3-8B 已跑通：transformers 5.2 原生 InternVL 类与官方 checkpoint config 不匹配
  （hidden 3584 vs 4096），改用 `local_internvl_chat` backend（trust_remote_code
  InternVLChatModel）；需要对 hf_cache blob 打 numpy linspace 补丁（meta-tensor 兼容），
  并对 remote class 做 `all_tied_weights_keys` 兼容包装。venv_dlc 补装了 einops/timm
  （aliyun pypi 镜像；tsinghua 403）。
- extended80 池未做逐张人工视觉复核（沿用原 report 的 projection QA + 图片存在性）；
  其中 retake 宽视角 target 较小，答案级指标对 parse 质量更敏感。
- Qwen2.5 的 'fauc' 截断与 max_new_tokens=64 的关系未排查；paper 中应把 parse 失败
  与语义翻转分开报告。
- 多视角一致性目前只对 normalized-1000 契约合规的 backend 有意义（Qwen2.5 全 miss 造成
  "虚假一致"），写作时需按契约合规性分层。
- 文档 handoff（docs-writer）：本记录已含数字；若进入论文，推荐更新
  `docs/design/` 下 VLM grounding 协议设计页 + `paper/shared/evidence/results_manifest.yaml`。

## 追加结果（当日后续批次）

### 协议矩阵扩展到 5 backend（含 InternVL3-8B）

InternVL3-8B stress30：structured+n1000 0.72/0.77；json+n1000 **1.00/0.86**
（最强 pointer 但材质 delta −0.14）；s2 0.33/0.61（+0.28，最大正 delta）。
结论：grounding 准确率排名不预测稳定性排名；5 个 backend 的材质 delta 分布
−0.28 到 +0.28，同一干预的结论完全取决于 backend × 协议组合。

### extended80 视角分解（view-type 是第三个隐藏因子）

| backend | zoom O/C | retake O/C |
|---|---|---|
| Qwen3-VL-8B | 0.902/0.927 | 0.821/0.769 |
| Gemma4 | 0.878/0.927 | **0.513/0.359** |
| Qwen3-VL-2B | 0.780/0.732 | 0.282/0.256 |
| InternVL3-8B | 0.697/0.781 | 0.200/0.250 |

Gemma4 在 zoom 视角材质 delta 为 +0.05，retake 宽视角为 **−0.15**——同一模型同一干预，
视角切换翻转结论符号。产物：`backend_protocol_matrix/paper_tables/extended80_view_breakdown.csv`。

### s2 任务族（任务驱动 grounding）

extended80 s2 vs s1：qwen3-2b 从 0.537/0.500 升到 **0.750/0.637**（动作语境帮助小模型
grounding，但转换损失更大）；qwen3-8b 0.850/0.850 完全稳定；gemma4 0.688/0.637。

### 采样方差 vs 材质位移（temp=0.7 × 3 seeds，stress30 canonical）

| backend | seed spread(px) | hit 不稳定率 | 采样下材质位移(px) |
|---|---|---|---|
| Qwen3-VL-8B | 7.66 | 0.0% | 14.56 |
| Qwen3-VL-2B | 24.34 | 16.7% | 25.12 |
| Gemma4 | 27.07 | 10.0% | 29.24 |

强 backend 的材质位移（2×）显著大于解码噪声；小 backend 两者相当——小模型材质 delta
部分淹没在采样噪声里。产物：`sampling_variance_probes/sampling_variance_summary.json`。
该结果同时反向支持 canonical 评测采用 temperature=0。

### clean-pool 五 backend 补齐（n1k O/C）

Gemma4 0.533/0.400；Qwen2.5 0.0/0.0；Qwen3-VL-2B 0.200/0.200；Qwen3-VL-8B 0.800/0.867；
InternVL3-8B 0.231/0.273。backend 排序与 stress30 一致。

### 配对 bootstrap CI（6 backend × 2 pool，2000 rounds）

`backend_protocol_matrix/paper_tables/canonical_paired_cis.{csv,json}`：

- stress30 各 backend 的 n1k hit delta CI 都跨零（n=30 功效有限）；材质效应的
  系统发现是**跨仪器方差**而非单仪器显著性——同一冻结干预下 measured delta
  由 backend/协议选择决定（−0.28 ~ +0.28）。
- median displacement：Molmo 0px、Qwen3-8B 13.5px、Gemma4 18px、InternVL3 64px
  （其 mean 309px 由坐标量化 outlier 拉大，median 已纠正）。

### InternNav 方向评估结论（E6）

- 官方 InteriorAgent/InternNav **val_unseen split 全集 = 3 scenes / 99 episodes**
  （kujiale_0031/0036/0066 各 33 条）；已验证现有 99-episode paired run 的 episode ID
  与官方 split **完全一致**——论文措辞可从 "99 episodes across three local scenes"
  升级为 "the complete official val_unseen split"。扩展到 5+ 官方场景不可行
  （官方 split 本身只有 3 个场景）。
- GRScenes InternNav 路线本地有 8 次 invalid 运行记录（v2-v9 均 warmup hang），
  继续扩场景风险高、价值低，本轮不再投入。

## 产物清单（最终）

- 预测：stress30 29 个配置 JSONL + extended80 11 个 + clean_pool 补 3 个 +
  sampling_variance 9 个，均带 `.metadata.json` provenance。
- 分析产物（均在 `paper/shared/evidence/raw/grscene_vlm_grounding/`）：
  - `backend_protocol_matrix/backend_protocol_matrix.csv`（41 配置大矩阵）
  - `backend_protocol_matrix/multiview_consistency.json`
  - `backend_protocol_matrix/paper_tables/`（canonical_backend_table、
    protocol_sensitivity_table、task_family_table、extended80_view_breakdown、
    canonical_paired_cis、headline_digest）
  - `backend_protocol_matrix/consensus_analysis.json`
  - `material_effect_attribution/`（6 backend 归因）
  - `sampling_variance_probes/sampling_variance_summary.json`
  - `stress_extended80_projection_report.json`（extended80 诊断池清单）
- 分析脚本：`aggregate_stress_backend_matrix.py`、`analyze_material_effect_attribution.py`、
  `analyze_sampling_variance.py`、`compute_canonical_paired_cis.py`、`distill_paper_tables.py`
  （均在 `experiments/06_grscenes_vlm_grounding/`）。
