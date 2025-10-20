# 导出 MDL 材质球：踩坑点与排错

本文汇总常见问题与解决策略。

## 1. 打不开或找不到 _ball.usda
- 现象：filepicker 提示 not found，或路径复制有误。
- 排查：确认导出目录与文件名（`<MatName>_ball.usda`）是否存在；路径中有无中文或空格；确保挂载/权限可读。

## 2. MDL 模块加载失败（Find module / MdlModuleId Invalid）
- 原因：导出材质球里的 `info:mdl:sourceAsset` 未能被解析。
- 解决：
  - 已在导出时重写为“相对导出文件目录”或“绝对路径”；优先尝试 `--assets-path-mode absolute`；
  - 若依赖 Omniverse 的库索引，需在 omniverse.toml 配置 `library_root` 指向 mdl 库；
  - 确认 `.mdl` 文件真实存在并可读。

## 3. 贴图找不到（References an asset that can not be found）
- 原因：MDL 输入中的 AssetPath 指向的贴图文件不在该相对位置。
- 解决：
  - A) 在对应目录放置贴图文件；
  - B) 使用 `--assets-path-mode absolute` 重导出；
  - C) 若是公共“白图/黑图”，可统一指向公共贴图目录（绝对路径）。

## 4. 路径分隔与跨平台
- 相对路径统一写为 POSIX 风格（`/`）；Windows 环境建议优先绝对路径模式，或保证驱动器/共享盘挂载一致。

## 5. 作者层判断不符合预期
- 如果某材质的“首次定义”不在你想要的子文件，可改用 `--placement root` 统一输出到顶层目录；或后续增强提供自定义映射表。

## 6. 仍需深拷连接子图
- 当前 MDL 模式复制输入值，不深拷 connected source 网络。如需完整图克隆，可在 `_export_mdl_material` 里遍历下游 Shader 并复制属性/连接（后续增强项）。

## 7. 性能与批量
- 大场景导出耗时与材质数量/IO 相关；建议先用小样本确认路径策略，再批量跑。

---

## 快速自检清单
- [ ] `_ball.usda` 是否存在且可打开？
- [ ] `info:mdl:sourceAsset` 是不是你期望的相对/绝对路径？
- [ ] 关键贴图（base/metal/normal/spec/gloss/emissive）是否能在磁盘上找到？
- [ ] inspect（mdl 模式）是否能列出 shader 与输入？
