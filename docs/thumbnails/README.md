# 缩略图渲染（thumbnails）

使用 Omniverse Isaac Sim 进行无头渲染，为场景中的实例 Mesh 生成带背景的多视角缩略图：

- 自动按实例 prim 名称创建文件夹并保存图片
- 上/下半球均匀取样视角（默认共 6 个视角，可配置）
- 基于 2D bbox 紧/松面积比阈值过滤不合格视角（默认阈值 0.8）
- 可选择是否在图片上叠加 2D bbox

快速开始、完整参数与范例见：`usage.md`
运行环境与依赖说明见：`environment.md`
常见问题见：`troubleshooting.md`
