# docs-writer Memory

只记录稳定的、项目级的、跨会话仍有价值的文档经验。

- 记录文档目录习惯、命名规则、常见章节结构
- 不记录一次性的草稿细节
- 新增一等 docs/records 论文记录时，同步更新 `docs/records/README.md`；如果是论文主线入口，也同步更新 `docs/index.md` 的“论文修订入口”。
- AAN 文档惯例：`docs/design/asset-application-normalizer.md` 以中文说明架构和 gate，consumer handoff 以英文给 ABI/命令；动态 interaction 的 cooked/proxy probe、post-reset render 与真实机器人 close/lift/hold 必须明确分开表述，避免把前者写成 grasp success。
- 论文图表字体记录应区分系统已安装与 Matplotlib 缓存可发现；ICLR 绘图使用 `font_manager.fontManager.addfont` 显式注册 Liberation Sans 并保留 DejaVu Sans 后备，避免缓存导致静默字体替换。
