# 导出 MDL 材质球：使用说明（User Guide）

本文面向使用者，介绍如何运行与验证。

## 基本命令（Isaac-Sim 环境）

```bash
# 默认导出为“MDL 模式”，按作者层目录放置，并生成预览球
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py export-mdl-materials \
  /abs/path/to/scene.usd \
  --placement authoring \
  --out-dir-name mdl_materials \
  --mode mdl \
  --emit-ball
```

可选：写绝对路径（更稳妥）
```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py export-mdl-materials \
  /abs/path/to/scene.usd \
  --placement authoring \
  --out-dir-name mdl_materials \
  --mode mdl \
  --emit-ball \
  --assets-path-mode absolute
```

统一放到顶层目录（而非作者层）：
```bash
... --placement root
```

仅导出根层作者的材质（忽略外部）：
```bash
... --no-external
```

## 打开哪个文件看球？
- 输出目录：`/<作者层目录或顶层目录>/<out-dir-name>/`
- 直接打开：`<MaterialName>_ball.usda`（内含球体与材质绑定）
- 材质球本体：`<MaterialName>.usda`（位于 `/Looks/<MaterialName>`）

## 如何核对导出结果
- 用 inspect 检查 MDL 材质：
```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect \
  /path/to/mdl_materials/MatA.usda mdl /Looks/MatA
```
- 预览模式核查（如导出 preview 模式）：
```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect \
  /path/to/mdl_materials/MatA.usda usdpreview /Looks/MatA
```

## 与 no-MDL 流程并用
- no-MDL 生成的是 *_noMDL.usd（预览材质），用于场景“去 MDL”；
- export-mdl-materials 拆出“原始 MDL 材质球”，用于资产沉淀与复用；
- 两者互补：先去 MDL 保持渲染稳定，再把原始 MDL 材质异地归档。
