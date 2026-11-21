# CVIU 自然场景实验基础与试验检查

按 grill-me 决策实施独立实验目录 12_cviu_diagnostics。保留旧实验与原始资产。
恢复完整转换入口：experiments/grscenes/nomdl_full/zzh-grscenes_nomdl_full_work_20260521。
新增确定性场景清点与分层划分、pilot USD 依赖检查、机器可读实验配置和 v2 协议。
99 个来源场景分为 pilot 3、train 15、validation 5、test 10、reserve 66。
固定 SHA256 顺序，与模型输出无关；入口缺失不会自动换场景。输出拒绝覆盖。

验证：python -m pytest -q tests/test_cviu_inventory.py，2 passed。
通过 scripts/isaac_python.sh 运行 check_stages.py：六入口有五个存在未解析依赖，
一个 commercial original 静态依赖检查通过。检查非零退出符合设计，不代表模型失败。
详细数据在 paper/shared/evidence/raw/cviu_diagnostics/v1/pilot_stage_check.json。

未完成：区分原始缺失与转换路径错误、修复独立实验副本、渲染可见性、标签、模型
checkpoint 固定、批量推理、分析、风险诊断、导航与完整稿件。没有新模型指标。
静态 dependency 检查不能替代 Isaac MDL resolver 与实际渲染，下一步要检查真实路径。
