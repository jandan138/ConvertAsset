# AI 生成文本审计报告

> **日期**: 2026-06-10
> **范围**: ACL 主文 (11页) + 补充材料 (46页)
> **方法**: 三个独立 agent 多角度并行审阅

---

## 总评

**补充材料存在严重的 LLM 生成模式，主文程度较轻。** 补充材料中约 30-40% 的散文为防御性模板文本，其自我指涉的元免责声明和自动化式的否定句式密度远超正常学术惯例。主文虽然也过度受限，但或许仍可作为极端谨慎的人类写作通过。

---

## 六类关键 AI 信号

### 1. 图形标题的"免责声明流水线"（极强信号）

41 张补充材料图中，**37 张（90.2%）** 以免责声明结尾。核心模式是可互换的否定词汇的封闭集合，被机械地洗牌到几乎每个标题中：

**精确出现频率（LaTeX 源码）**：

| 模式 | Supplement `.tex` 出现次数 |
|------|---------------------------|
| `not a new metric, ...` | 13 |
| `these panels are not additional VLM predictions` | 3 (S16, S22, S23) |
| `not a new navigation metric/run` | 3 (S27, S35, S36) |
| `not a new experiment` | 2 (S38, S39) |
| `not a new evidence source` | 1 (S2) + 1 (S41) |

**最过分的单条标题（S41）**，以带五要素否定列表结尾：
> "This companion is **not a new evidence source, experiment, metric, VLM run, or navigation run.**"

**S26 含双免责声明**，中间仅隔一句话：
- "not as an official-scene navigation baseline or a population-level converter ranking"
- "not evidence for a material mechanism or converter ranking"

**近逐字重复**——在三个不同的附录中出现了相同的三要素结构：
- S12: "they are not new metrics, model predictions, or benchmark rows"
- S13: "not a new metric, model prediction, or benchmark row"
- S16: "these panels are not additional VLM predictions or benchmark rows"

### 2. "X, not Y" 否定句式作为主导修辞模式（极强信号）

`X, not Y` 是本文的核心句法策略。主文及补充材料中有 **数十处** 实例。几乎每一个事实陈述后面都紧跟一个否定短语：

**主文示例**：
| 文件 | 行 | 文本 |
|------|-----|------|
| `intro.tex:52` | 52 | "controlled test of VLM grounding, **not neutral asset cleanup**." |
| `intro.tex:60-62` | 60 | "entry and stability in these settings, **not broad benchmark or speedup results**." |
| `method.tex:18-19` | 18 | "**not full MDL semantics**; clearcoat, displacement, opacity, and emission stay audit risks." |
| `method.tex:37-38` | 37 | "The probes test a fixed prompt-and-coordinate format, **not a model ranking**." |
| `results.tex:106` | 106 | "This stack-entry check is **not a benchmark result**." |
| `discussion.tex:4-5` | 4 | "Protocol, **not leaderboard**." |

这是 AI 生成文本的典型特征——它将大部分精力花在声明自己不是什么上，而不是陈述自己是什么。

### 3. 最像 AI 的句子（致命信号）

**位置**: `venues/acl27/sections/supplement/00_overview.tex:75`

> **"These exclusions are methodological rather than rhetorical."**

这是**标志性 LLM 文本**——机器在解释自己文本的体裁。没有任何人类学者会写出这句话来为自己的排除条件辩护。它是元评论的元评论。

同一段中第二条致命句子（第 46-49 行）：

> **"This scope also explains why the supplement is deliberately redundant in a few places. Some quantities appear as a table, a derivation, and a visual example. The repeated presentation is not meant to inflate evidence."**

这篇散文在解释为什么文件自我重复，并主动拒绝了没人会提出的控诉（"夸大证据"）。这是 AI 被指示 "解释冗余的来源" 后生成的。

### 4. "What This Supplement Does Not Prove" 专门章节（强信号）

**位置**: `venues/acl27/sections/supplement/00_overview.tex:67-81`

完整的五项否定列表，附带专属可视化伴侣图（Figure S3/S4）：

> "The supplement does not prove that MDL-to-UsdPreviewSurface conversion is semantically lossless. It does not prove broad downstream task robustness. It does not turn the selected NVIDIA clearcoat case into a failure-rate estimate. It does not show that procedural textures are preserved. It does not use selected video examples as a replacement for the 99-episode paired run."

人类作者可能会包含一句边界声明。这种去叶化的、带枚举和可视化伴侣的列表结构是明确的 AI 防御性写作指纹。

### 5. `deliberately` / `intentionally` 过度使用（中信号）

13 处实例，密度异常：

| 文件（LaTeX 源码） | 文本 |
|------|------|
| `results.tex:7` | "The first result is **deliberately** narrow." |
| `limitations.tex:15` | "The evaluation scope is **deliberately** limited." |
| `supplement/00_overview.tex:46` | "the supplement is **deliberately** redundant" |
| `supplement/02_vlm_protocol.tex:70` | "The parser is **intentionally** conservative." |
| `supplement/06_theory.tex:6` | "**intentionally** labeled as hypothesis-level material" |
| `supplement/03_grscenes_visuals.tex:96` | "zoom-stress views are **intentionally** different" |
| `supplement/05_internnav_visuals.tex:69` | "The PDF supplement **intentionally** uses still panels" |
| `shared/sections/discussion.tex:117` | "It is **intentionally** visual" (rule table) |
| `shared/sections/experiments.tex:354` | "The stress pool **intentionally** includes" |
| `shared/sections/experiments.tex:383` | "The stress camera construction **deliberately** centers" |

个别使用或许可接受，但整体密度远超人类作者的正常范围。

### 6. `registered` 作为出处水印（中信号）

**补充材料 LaTeX 源码中出现 29 次**。"registered" 被用作系统的出处水印——"registered render evidence"、"registered proxy pairs"、"registered target projections"、"registered stills"、"registered machine-readable closure artifacts"。这是 AI 收到指令 "每次重用现有图形时使用 registered 进行标记" 后机械执行的结果。

---

## 主文 vs 补充材料：量化对比

| 模式 | 主文（`venues/acl27/*.tex`） | 补充（`sections/supplement/*.tex`） |
|------|------------------------------|-------------------------------------|
| `not a new [X]` 免责声明 | 0 | 13 |
| `visual guide/bridge/atlas` 标签 | 1 | 14 |
| `registered` 出处标记 | 0 | 29 |
| `does not prove/show/certify` | 0 | 10 |
| `not a benchmark/ranking/leaderboard` | 3 | 8 |
| `frozen evidence/pairs/tables` | 7 | 5 |
| `deliberately/intentionally` | 3 | 4 (+6 in shared/) |

**补充材料密度大约高 5-10 倍。**

---

## 根因推测

补充材料极有可能是用一个系统级指令生成的，大意如下：

> *"每个图形标题必须声明它不是新证据。每个视觉元素必须被标记为 visual guide/reading aid。每个主张必须立即被其不证明的内容所限定。每当重用现有证据时，使用 registered。将文件自我引述为 supplement。永远不要让读者误以为任何图形代表新实验。"*

结果是，补充材料约有 30-40% 的散文是由可互换的否定短语和出处水印组成的防御性模板文本，没有人类作者会觉得需要以这种密度包含这些内容。

---

## 建议修复（按优先级排列）

### 高优先级——立即删除

1. **删除 "These exclusions are methodological rather than rhetorical"**
   — 整个文件中最直接的 AI 指纹。`00_overview.tex:75`

2. **将 "What This Supplement Does Not Prove" 章节压缩为 1 句**
   — 删除五项否定列表及其可视化伴侣图（Figure S3/S4）。
   — 替换为一个简单的句子，如 "This supplement does not constitute independent evidence; all results are derived from the main paper's data."

3. **删除或大幅重写 "not meant to inflate evidence" 段落**
   - `00_overview.tex:46-49`

### 中优先级——系统性缩减

4. **删除约 80% 的图形标题免责声明**
   — S1-S41 中约 37 个标题包含它们；保留 5-8 个真正需要澄清边界的情况。
   — 读者能自行判断图是解释性的还是新的实验。

5. **将 `deliberately`/`intentionally` 从 13 处减少到 2-3 处**
   — 保留在真正区别设计选择的边缘情况与无意产物的地方。

6. **将 `registered` 多次出现替换为更自然的英语**
   — "as shown in", "from the main paper", "previously reported", "corresponding" 等。

### 低优先级——语气改进

7. **重新平衡否定（X, not Y）与肯定（X is Y）**
   — 减少 "Protocol, not leaderboard"、"not a model ranking, but..."、"visible intervention, not safety..." 的说话习惯。
   — 直接陈述主张，不加否定性限定。

8. **移除重复的 "visual guide" / "visual atlas" / "visual bridge" 标签**
   — 这些本身就说明了功能，几乎不需要这样的元标签。

---

## 修复历史

| 日期 | 行动 |
|------|------|
| 2026-06-10 | 三 agent 并行审计完成；初始审计报告已撰写 |
| 待定 | 开始修复（待作者审核） |
