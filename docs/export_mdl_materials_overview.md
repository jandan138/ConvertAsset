# 导出 MDL 材质球：功能解析（Feature）

本功能的目标：从一个 USD 文件中，自动遍历“MDL 材质”（UsdShade.Material 上存在 MDL 语义），并为每个材质生成一个独立的“材质球 USD”。

核心特点：
- 保留 MDL：默认模式导出为“原始 MDL 材质”（保留 info:mdl:* 与输入值），不做 UsdPreviewSurface 转换。
- 目录放置可控：
  - authoring（默认）：将材质球写到“材质作者层（通常是最小子 USD）”的同级目录下的子文件夹；
  - root：统一写到顶层 USD 的同级目录。
- 预览小场景：可选生成一个“绑定球体”的小场景（*_ball.usda）用于快速查看材质效果。
- 资产路径重写：将 MDL 模块与贴图等 AssetPath 重写为“相对导出文件目录”或“绝对路径”，避免分发后路径失效。
- 只读：不修改原始 USD、不 flatten、不改外部文件。

输入/输出（简要）
- 输入：任意 USD（顶层或子层）。
- 输出：
  - /<out-dir-name>/<MaterialName>.usda：独立材质球文件（/Looks/<MaterialName>）。
  - 可选：/<out-dir-name>/<MaterialName>_ball.usda：包含球体与材质绑定的小场景。

与现有能力的关系
- 与 no-MDL 转换并行：no-MDL 生成 *_noMDL.usd（预览材质），而本功能导出 MDL 材质球，二者用途不同但相互补充。
- 与 inspect 联动：inspect 可对导出的材质球检查 MDL/UsdPreview 网络结构与链接情况。

典型使用场景
- 资产沉淀：把场景里的 MDL 材质批量拆出为独立可复用的材质资产。
- 快速评估：用 *_ball.usda 快速预览材质效果，不依赖原场景。
- 跨项目共享：通过“绝对路径输出”便于在不同机器/环境直接打开材质球。

---

## 设计取舍
- 不深拷连接子图：导出 MDL 模式下，复制 MDL Shader 的元数据与输入值（常量与 AssetPath）；对于连接源网络（connected source）做保守处理（优先落地为值）。如确需完整图克隆，可作为后续增强。
- 不复制贴图文件：仅重写路径，不做文件拷贝；保持导出轻量与可控。若需要复制贴图，请结合 no-MDL 流程或独立脚本补全。
