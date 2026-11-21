# ICLR 23337 → CVIU 逐条评审修改跟踪

更新时间：**2026-11-18**（已完成同机 RTX 4090 `transformers 5.23.0` 全四家族 / 六模型 / `14,016` 条零错误 `torch.bfloat16` 预测、WET-OP 风格全套 6 张高密矢量图 + 可编辑 `Figure1_ConvertAsset_Overview.pptx`、Elsevier `[5p,times,authoryear]` 双栏 CVIU 全稿重构及编译/视觉验收）。依据：用户提供的[三份评审全文](../iclr27/reviews/official_reviews_user_supplied_2026-11-14.md)。本表用于 CVIU 转投改稿，不代表审稿人已重新审阅。

## 当前结论

- **CVIU v3 扩展实证与全稿改写已全面收官**：
  - 正式 30 场景（240 目标、480 对自然视角、1,440 张掩码反事实 + $\mathrm{CIE}~L^*a^*b^*$ 光度对照、3 场景光追重渲染与 $T{=}0.2$ 随机解码控制）共覆盖 **4 个独立开源 VLM 家族、6 个无量化 `bfloat16` 模型**（`Qwen3-VL-2B/8B/32B`、`InternVL3.5-8B-HF`、`Molmo2-8B`、`LLaVA-NeXT-Mistral-7B`），在同卡同版本下累计 **`14,016`** 条零错误预测（不含 24-input pilot 门控为 `13,920` 条）并由 10,000 次场景簇 Bootstrap 检验（`E10`–`E11`）。
  - 全稿版式已转为 Elsevier CVIU 官方双栏 `\documentclass[5p,times,authoryear]{elsarticle}`（含 5 条 Highlights 与 CRediT 作者贡献声明），全部 6 张主文图按照 WET-OP CVPR 2027 学术视觉标杆重绘并经渲染像素验收。
- **P1/P2 问题关闭情况**：25 项中有 **20 项已验证完成**（原 H06 进一步从 2 家族升级为 **4 独立 VLM 家族 / 6 检查点闭环**）、**3 项为明确边界/范围决定**（`G05` 人类基线、`H07` 闭源商业 API、`Z03/G02` 导航与静态定位关系界定）、**2 项为 3D 导航多重复保留作用域**（`Z05/H03` 3D 仿真器 5 次重跑留待 `navigation_followup.json` 执行，正文严格降格为观察性下游案例）。

## 状态与关闭规则

- **已验证完成**：有对应结果、正文/图表位置和编译验证记录（更新日期 `2026-11-18`）。
- **部分完成 / 范围决定**：保留在各自对应边界说明与局限性章节中。

## 证据索引

| 代号 | 已存在文件 | 能证明什么 / 边界说明 |
|---|---|---|
| E1 | [CVIU 协议](PROTOCOL.md)、[机器配置](experiment_plan.json) | `v3` 实验协议（`schema_version=3`）与统计规范 |
| E2–E7 | [旧诊断](../../shared/evidence/raw/iclr_model_behavior/analysis_v1/results.json)、[导航清单](navigation_followup.json) | 旧版 ICLR 数据、接口格网对比与 `99` 条 KuJiaLe 导航批次 + `990` 次待执行仿真重跑计划 |
| E8–E9 | [pilot 记录](../../../docs/records/2026-11-14-cviu-three-scene-pilot-results.md)、[正式冻结输入](../../shared/evidence/raw/cviu_formal/v1/manifest.json)、[正式 VLM 分析](../../shared/evidence/raw/cviu_formal/v1/analysis_v1/primary/results.json) | 30 场景 480 对冻结输入、`Qwen3-VL-8B/32B` 三次贪心复跑及 3 场景重复渲染基线（`5,952` 条预测） |
| E10 | [Colab 阶段记录](../../../docs/records/2026-11-17-cviu-v3-colab-campaign-results.md)、[文献核验记录](../../../docs/records/2026-11-17-cviu-reference-verification.md) | 早期方案与 12 篇以上参考文献一手核验元数据 |
| **E11** | [CVIU v3 结果目录](../../shared/evidence/raw/cviu_v3/)、[四家族同卡闭环与版式升级记录](../../../docs/records/2026-11-18-cviu-v3-four-family-and-wetop-overhaul.md) | **最终定稿实证（`14,016` 总预测，`0` 错误）**：本地 RTX 4090 (`transformers 5.23.0`) 完成 19/19 组 `v3` 评测（4 独立家族 `Qwen3-VL-2B`, `InternVL3.5-8B-HF`, `Molmo2-8B`, `LLaVA-NeXT-Mistral-7B` 完整 960 主评测 + L1/L3 控制 + 24-input pilot；2 独立 8B 家族共 `2,880` 路掩码反事实评测、`T=0.2` 随机控制、`family_overlap_4x8b` 85.7% 单模型失效分析、WET-OP 6 图 + `Figure1_ConvertAsset_Overview.pptx` 与 Elsevier 5p 双栏完稿） |

## Reviewer zAz6

| ID | 原文定位与问题 | 优先级 | 修改动作与当前证据 | 当前状态（`2026-11-18`） |
|---|---|---|---|---|
| Z01 | W1：仅观察决策变化，缺少解释与解决方案 | P1 | `E11` 完成双家族 `2,880` 次反事实光学机制归因（两条独立架构均现 **`+3.54%`** 非光度残差、`Reflective/Metallic` $+4.43\%$ 眩光消除增益 vs.\ 结构平坦退化）并提出家庭校准零 VLM 风险门控（`0.743` 测试集 / `0.732` LOSO）；见 `sections/mechanisms.tex`、Figure 5 | **已验证完成** |
| Z02 | W2：实验不连贯、在材料/坐标/格式间跳转 | P1 | 按 `RQ1 (方差+尺度/四家族) → RQ2 (双家族反事实) → RQ3 (家族校准 vs 混合风险门控) → RQ4 (下游导航)` 重组全文；接口诊断与四解析器门控归入 Appendix A–B | **已验证完成** |
| Z03 | W2：grounding 与导航联系不足 | P1 | 重写 `sections/navigation.tex`（`RQ4`），明确两者分属"单帧精确感知诊断 vs.\ 闭环序贯观察案例"，删去未经同状态 `usd` 证实的强因果外推 | **范围决定（已透明界定）** |
| Z04 | W3；Q1：仅四对来源，能否推广 | P1 | 扩展至 **30 个独立场景（20 住宅 + 10 商业）/ 240 目标 / 480 对自然视角** 并报告 10,000 次场景簇 Bootstrap 区间；见 `sections/method.tex`、`grounding.tex`、Table 3 | **已验证完成** |
| Z05 | W3；Q2：导航无同条件重复，难分随机性 | P1 | 静态 grounding 已通过 6 检查点 4 层方差（全部 `0.00%` 贪心 vs.\ `2.0x–6.0x` 超光追噪底）彻底关闭；3D 导航 5 次重跑保留 `navigation_followup.json` 并在正文透明界定边界 | **部分完成（正文已如实降格边界）** |

## Reviewer GRGE

| ID | 原文定位与问题 | 优先级 | 修改动作与当前证据 | 当前状态（`2026-11-18`） |
|---|---|---|---|---|
| G01 | W1；Q3：缩写未定义、动机弱、可读性差 | P1 | 全文首次出现均严格展开全称（`USD`, `MDL`, `VLM`, `BSDF`, `MAE`, `SSIM`, `SR`, `SPL`, `NE`, `TL`, `AUROC`, `AUPRC`, `LOSO`），重写 `introduction.tex` 确立工程资产转换动机 | **已验证完成** |
| G02 | W1：静态场景和导航关系不清 | P1 | 同 Z03；在 `introduction.tex` 与 `navigation.tex` 中将导航明确为下游观察性案例研究 | **已验证完成** |
| G03 | W2；Q3：导航设置与指标解释不足 | P1 | 完整重写 `sections/navigation.tex` 与重绘 WET-OP 风格 `fig6_navigation_vln.pdf`：详述任务输入、`STOP` 规则、`SR/SPL/NE/TL` 与 30/99 (30.3%) 翻转分布 | **已验证完成** |
| G04 | W3；Q2；Q3：缺乏规模理由与样本分母 | P1 | 明确报告 30 场景、240 目标、480 对自然视角及各子层分母与 10,000 次场景簇 CI；见 `sections/method.tex` | **已验证完成** |
| G05 | W4：没有与人类表现比较 | P3 | 在 `sections/conclusion.tex` 明确不做正式人类心理物理基线，说明仿真掩码真值与本地视觉抽检校验边界 | **范围决定（正文已写明）** |
| G06 | W4：表现变异与噪声鲁棒性未充分处理 | P1 | `E11` 完成全部 6 检查点 4 层方差分解（`variance_hierarchy.tex`、Figure 4a）：证明同卡同版本贪心 `T=0` 严格零方差（全部 `0.00%`），而 `T=0.2` 触发 `8.96%` 成对翻转（`16.67%` 任一翻转），材质转换达光追基线 `2.00x–6.00x` | **已验证完成** |
| G07 | W5；Q1：颜色/对比度/纹理 salience 替代解释 | P1 | `E11` 对 `Qwen3-VL-8B` 与 `InternVL3.5-8B-HF` 双家族均完成掩码级 `I^T/I^B/I^{\text{photo}}` 反事实（累计 `2,880` 预测）；两者出现完全一致的 **`+3.54%`** 非光度材质残差（473 同掩码子集均 **`+3.38%`**）；见 `sections/mechanisms.tex`、Table 4、Figure 5 | **已验证完成** |

## Reviewer 51hM

| ID | 原文定位与问题 | 优先级 | 修改动作与当前证据 | 当前状态（`2026-11-18`） |
|---|---|---|---|---|
| H01 | W1；Q1：缺少相关工作比较与文献核验 | P1 | 逐条联网核验 `[1]`–`[10]` 及 `Bai2025Qwen3` / `Wang2025InternVL35` / `Clark2026Molmo2` / `Liu2024LLaVANeXT`，更新 Table 1 (`related_work_comparison.tex`) 与 `sections/related_work.tex` | **已验证完成** |
| H02 | W1：与 adversarial perturbations 关系 | P2 | `sections/related_work.tex` 与 `sections/method.tex` 对照 \citet{Chaubey2020UAP} 明确区别确定性双向工程降级与梯度对抗攻击 | **已验证完成** |
| H03 | W2.1：样本太少 | P1 | grounding 扩展至 30 场景 480 对 × 6 模型 + `2,880` 反事实（合计 `14,016` 预测）；99 集 3D 导航多重复留待 `E5` 协议 | **部分完成（grounding 已彻底关闭；导航同 Z05）** |
| H04 | W2.2；W3.4；Q2：零假设与 16.7% 波动关系不清 | P1 | 以 6 检查点 4 层方差实测彻底关闭：全部 6 检查点 `T=0` 均为 `0.00%`，`T=0.2` 复现 `16.67%` 任一采样翻转；相对光追基线产生 `2.00x–6.00x`（`Molmo2-8B` `4.17%` vs.\ `0.00%`）翻转 | **已验证完成** |
| H05 | W2.3；Q2：颜色/背景替代解释未检验 | P1 | 同 G07：双独立 8B 家族 `2,880` 反事实均检出 `+3.54%` 非光度残差 | **已验证完成** |
| H06 | W2.4；Q3：模型偏小/旧，缺强模型及跨家族 | P1 | 在同卡 RTX 4090 (`transformers 5.23.0`) 完成 **4 独立开源 VLM 家族、6 无量化 `bfloat16` 模型**：**`Qwen3-VL` 全尺度 (`2B → 8B → 32B`)** + **`InternVL3.5-8B-HF`** (`10.63%`) + **SigLIP-2 指向专精模型 `Molmo2-8B`** (`93.96%` 基准 / `4.58%` 翻转) + **非 Qwen 纯 Mistral-CLIP `LLaVA-NeXT-Mistral-7B`** (`16.67%` 翻转)，并发现 `85.7%` (`66/77`) 单模型回归分化（见 `scaling_and_families.json` 与 Table 3） | **已验证完成（4 独立家族 6 检查点全面闭环）** |
| H07 | W2.4：缺闭源 SoTA（GPT/Gemini/Claude） | P2 | 坚持全开源可锁权重/锁解码实验边界，在 `sections/conclusion.tex` 透明说明不外推至闭源黑盒 API | **范围决定（正文已写明）** |
| H08 | W2.5；Q4：无清晰 takeaway | P1 | 全文收敛为三项可操作结论 + 5 条 CVIU Highlights + 家族校准风险门控优于跨家族混合门控（`0.743` vs.\ `0.582` AUROC） | **已验证完成** |
| H09 | W3.1：摘要缺乏意义 | P1 | 完全重写 `sections/abstract.tex`，报告四家族范围、`14,016` 总预测、双家族 `+3.54%` 残差与家庭校准门控结论 | **已验证完成** |
| H10 | W3.2；Q1：引言动机与贡献不清 | P1 | 重写 `sections/introduction.tex`，配全新 WET-OP 风格横跨双栏主图 `fig1_overview.pdf` 与四项可验证贡献 | **已验证完成** |
| H11 | W3.3：Figure 1 混淆且看似换场景 | P1 | 按 `wet-op-cvpr2027` 结构重绘全部 6 张专业图表（`fig1_overview.pdf` 居中全景标图 + 四角 8 张光学/对照样例，另附可编辑 `Figure1_ConvertAsset_Overview.pptx`） | **已验证完成** |
| H12 | W3.4 L212–237：16 样本个位数翻转含义不清 | P1 | 扩展至 30 场景 480 对主试验（Table 3、`sections/grounding.tex`），将旧 4 对构造降为 Appendix~\ref{app:construction} 辅助例证 | **已验证完成** |
| H13 | Q4：整体写作质量需全面重构 | P1 | 全文转为 Elsevier `\documentclass[5p,times,authoryear]{elsarticle}` 双栏刊物排版（含 Highlights 与 CRediT 声明），重写全部 7 节正文章节与附录并通过 `latexmk` + 逐页渲染像素核验 | **已验证完成** |
