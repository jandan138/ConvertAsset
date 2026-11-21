# 2026-09-15：ICLR 模型行为主线迁移与实验重算

## 目标与架构选择

用户确认以模型行为与机制为核心，并要求保留导航等下游实验。新增独立
`paper/venues/iclr27/`，将 ICLR 设为默认构建；共享数据/转换工具保持现有边界。
正文按材质输入、目标定位、图像区域机制和导航结果推进。旧 ACL 词汇门禁不进入
ICLR；新校验只管数字、来源、生成资产、引用、PDF 格式和匿名信息。

## 调查与纠正

读取了论文 Makefile、共享 registries、ACL 章节、scorer、runner、历史扩样脚本、
paired navigation JSON/CSV、官方 ICLR 作者页与模板。关键发现：

1. Qwen JSON/n1000 的旧“下降 27.8pp”是 4/9 与 2/12 可解析子集比较；固定全部查询
   分母为 4/30 与 2/30，下降 6.7pp。不存在“把同一个指标写得更保守”的决定。
2. normalized 数值原始距离被误称像素；新版先按图像宽高变换，再测距离和真正的中位数。
3. 同一目标多视角重复，旧 pair bootstrap 没有保留簇结构；新版以 target cluster 重采样。
4. 旧多视角代码比较命中数量，漏掉同数但不同视角集合的变化；新增回归覆盖。
5. 两个旧 canonical 文件各有 8 张输入图被后续重渲染替换。ICLR close-view 表从后来
   80-pair 推理的精确 ID 子集生成，避免图片/预测混用。
6. 全图中心在旧 stress30 上命中 30/30。新任务通过双视图、查询互换和左右互换检验
   视觉与语言绑定，中心 gutter 命中 0。
7. 扩样档案仍含红色材质异常。开发双视图集也继承了这个问题；正文机制实验改用已修复、
   逐日志核验的四个来源，开发集保留为历史。

## 已实现及运行

`experiments/11_iclr_model_behavior/`：
- `analyze.py`：fixed-denominator、coverage、requested-frame、实际像素位移、簇区间、hash inventory。
- `prepare_interventions.py`：双视图查询/位置互换及 target/context 窗口交叉替换。
- `run_interventions.py`：模型只加载一次、逐条 flush、冻结引擎源码与环境 metadata。
- `models.json`、`campaign.py`：六模型配置入口和串行调度。
- `rerender_views.py`：新目录 camera overlay、偏轴 aperture、带超时回收的真实 RTX 捕获。
- `prepare_navigation_followup.py`：按 episode ID hash、独立于结果选择 12 个 paired cases。

干净来源实验 `interventions_clean_v2`：4 sources / 4 boards，每族 16 pairs；
Qwen3-VL-2B、Qwen3-VL-8B、Gemma4 各完成 128 条推理，共 **384 条**。
所有 campaign return code 为 0。每个输出对应原始文本、图片 SHA-256、checkpoint、
temperature/seed、token budget、Python/Torch/Transformers 版本和冻结引擎源码。

实际发现（干净来源窗口干预）：
- Gemma4 原始 12/16，target-window 11/16，context-window 14/16，全转换 13/16。
- Qwen3-8B 原始 16/16，target-window 15/16，context-window 16/16。
- Qwen3-2B 全转换保持 14/16，但 2 个 paired queries 改变 hit status。

导航正文保留 **99 paired episodes / 198 rollouts**。CSV 重算的转移矩阵为
fail/fail 34、fail/success 13、success/fail 17、success/success 35，30/99 转移。
每场景 SR/SPL 与真实轨迹案例均进入正文，而不是只保留“stack entry”措辞。

## 实际阻塞与未执行项

新偏轴 RTX smoke 在当前自动检测到的 Isaac 4.5 下运行：原始图在 camera binding
后超时，未生成 usable pair；日志保存在 `raw/iclr_model_behavior/rtx_smoke_v1/`。
不将失败捕获并入机制数据。未来扩到新场景需先解决 runtime/rendering 问题。

导航 follow-up 准备了 12 paired cases / 72 repeat jobs；尚未生成新的重复轨迹或
匹配状态模型探针。也尚未完成独立新场景模型验证或 shader 参数单因素消融。
当前窗口实验是明确的图像区域干预，不冒充物理材质参数干预。

## 论文、图表与文档

- `paper/venues/iclr27/`：官方模板、独立 main/sections/appendix、局部补充 bibliography、
  机器生成 tables/figures、OpenReview 复制文案、artifact checker 和本地 staging。
- 主叙事：Same Scene, Different Decisions；模型行为、机制、导航均有正文小节。
- 正文移除旧的 allowed/forbidden claims 表和反复防御语句；定义写进方法，来源细节进附录。
- root/paper README、CLAUDE、EXPERIMENT_CHECKLIST、results/claims/figure registries、
  docs 导航同步切换 ICLR。
- 2026-09-13 探索记录顶部加更正入口，保留原历史数据，不复用有歧义的头条数字。

## 验证证据

已执行：
```bash
python -m pytest -q tests/test_iclr_model_behavior.py tests/test_grscenes_vlm_score_grounding.py tests/test_grscenes_vlm_prediction_runner.py
python paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py
python paper/shared/evidence/experiments/11_iclr_model_behavior/prepare_navigation_followup.py
make -C paper iclr27-check
git diff --check
```

针对性测试 **43 passed**；四来源 provenance 检查通过（4 logs、0 MDL error signals）。
首次构建发现 BibTeX build 子目录路径和小型大写 PDF 文本识别问题，均修复。
最新 PDF/page-scale review 及 check_report 随 `paper/venues/iclr27/build/` 构建生成。
本次没有执行 git commit 或 OpenReview 上传。

## 最终构建与页面检查

- 组合测试命令增加 `tests/test_paper_layout.py` 后：**131 passed**。
- `make -C paper iclr27-stage` 成功；`check_report.json` 无失败项。
- PDF 共 **13 页**，正文及正文图表结束于第 **8 页**；符合 9 页初稿正文上限。
- 原始图表 standalone 与最终 PDF 逐页做了本地视觉复查（非独立审阅）。修复协议图
  横轴文字拥挤，重排导航 ending frames，消除段落纵向强行撑满的空隙。
- 精确 PDF SHA-256：`e043bc5b12f07c570fdecec4d8a302285ad83fcfbcd63e65991158cace7e9e47`。
- 审阅记录：`paper/venues/iclr27/VISUAL_REVIEW.json`。
- 本地包：`paper/submissions/iclr27_candidate/`，含 `main.pdf`、`metadata.md`、
  `experiment_results.csv` 与校验和清单。
