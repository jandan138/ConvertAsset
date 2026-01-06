# 材质检查 (inspect) 子命令

该功能用于**只读**分析某个 Material Prim 在两种渲染语义下的着色网络：

- `mdl`：MDL 渲染上下文 (Material 输出 `outputs:surface:mdl` 及其连接的 MDL Shader)
- `usdpreview`：UsdPreviewSurface 网络 (典型的 `UsdPreviewSurface` + 纹理 / 常量输入)

适用场景：
1. 验证 no-MDL 转换后某个材质是否仍残留 MDL Shader。
2. 排查为什么某个材质没有按预期出现贴图或参数。
3. 对比转换前（原始 MDL）与转换后（UsdPreviewSurface）材质结构。

---
## 基本用法

```
python -m convert_asset.cli inspect <usd文件路径> <mdl|usdpreview> <Material Prim 路径> [--json]
```

参数说明：
- `<usd文件路径>`：Stage 根层文件路径（.usd / .usda / .usdc）。
- `<mdl|usdpreview>`：检查模式。
- `<Material Prim 路径>`：目标材质 Prim 的 Sdf Path，例如：`/Root/Looks/Mat001` 或本示例中的 `/Looks_PreviewMat`。
- `--json`：当前为占位，将来可输出 JSON（目前只打印文本格式）。

退出码（Exit Code）：
- `0` 成功并找到/解析到对应网络（即 ok=True）。
- `2` USD 文件不存在。
- `3` 打开 Stage 失败或运行期异常。
- `4` 成功执行但未找到指定模式对应的网络（例如要求 `mdl` 但该材质已无 MDL Shader）。

---
## 输出结构说明（文本）
示例：
```
Mode: usdpreview
Material: /Looks_PreviewMat
OK: True (PreviewSurface analyzed)
Has PreviewSurface: True
  Shader Path : /Looks_PreviewMat/Preview
  Channels:
    - diffuseColor: const=(0.8, 0.2, 0.2)
    - roughness: const=0.4
    - metallic: const=0.0
    - normal: const=None
  Missing channels: normal
```

各字段解释：
- `Mode`：当前检查模式。
- `Material`：材质 Prim 路径。
- `OK`：是否成功解析到期望网络；括号内为摘要消息。
- `Has PreviewSurface` / `Has MDL Shader`：是否存在对应核心 Shader。
- `Shader Path`：核心 Shader prim 的 Sdf Path。
- `Channels`（usdpreview 模式）：列出关心的几个输入（diffuseColor / roughness / metallic / normal），会显示常量或纹理来源。
- `Missing channels`：既没有常量值也没有贴图连接的输入名字。
- MDL 模式下还会列出：
  - `sourceAsset`：`info:mdl:sourceAsset` 的 AssetPath。
  - `subIdentifier`：子标识（若存在）。
  - `Inputs`：遍历 MDL Shader 的所有输入，显示连接或常量。

---
## 示例 USD（内置演示文件）
仓库新增文件：`examples/inspect_demo.usda`，包含两个材质：
- `/Looks_PreviewMat`：UsdPreviewSurface 材质
- `/Looks_Mat`：模拟一个 MDL 材质（含 `outputs:surface:mdl`）

片段（简化）：
```
#usda 1.0

def Material "Looks_PreviewMat" {
    token outputs:surface.connect = </Looks_PreviewMat/Preview.outputs:surface>
    def Shader "Preview" {
        uniform token info:id = "UsdPreviewSurface"
        token outputs:surface
        color3f inputs:diffuseColor = (0.8, 0.2, 0.2)
        float inputs:roughness = 0.4
        float inputs:metallic = 0.0
    }
}

def Material "Looks_Mat" {
    token outputs:surface:mdl.connect = </Looks_Mat/mdlShader.outputs:surface>
    def Shader "mdlShader" {
        uniform token info:id = "mdlMaterial"
        asset info:mdl:sourceAsset = @MyFake.mdl@
        string info:mdl:sourceAsset:subIdentifier = "main"
        token outputs:surface
        color3f inputs:base_color = (0.1, 0.2, 0.3)
    }
}
```

---
## 运行示例
(假设当前工作目录位于仓库根)

1. 检查预览材质：
```
python -m convert_asset.cli inspect examples/inspect_demo.usda usdpreview /Looks_PreviewMat
```

2. 检查 MDL 材质：
```
python -m convert_asset.cli inspect examples/inspect_demo.usda mdl /Looks_Mat
```

若第二步返回 `No MDL shader found`，说明运行环境 / USD 解析正常，但该材质未匹配模式；否则会列出 MDL Shader 信息。

---
## 典型排查流程建议
1. 先用 `usdpreview` 模式看转换后材质是否存在缺失通道；若缺失贴图，检查生成的 *_noMDL.usd 是否包含对应 UsdUVTexture。
2. 再用 `mdl` 模式确认是否仍残留 MDL（严格模式下应该无）。
3. 若某些通道常量异常为 0 或 None，回到转换日志 / 审计 JSON 查看对应贴图是否被忽略或路径无法解析。

---
## 后续可扩展点 (TODO)
- 支持直接输入“几何 Prim 路径”自动解析其绑定材质。
- 增加更多通道：emissiveColor / opacity / displacement。
- `--json` 输出结构化 JSON。
- 批量模式：对一个 Stage 中所有 Material 生成报告。

---
## 与 no-MDL 流程的结合
在完成 no-MDL 转换后：
1. 对原文件（含 MDL）运行 `mdl` 模式 → 应能看到 MDL Shader。
2. 对 *_noMDL.usd 运行 `mdl` 模式 → 期望返回未找到 (Exit Code 4)。
3. 再对 *_noMDL.usd 运行 `usdpreview` → 验证预览网络是否完整（贴图/常量）。

这样可实现快速点检：
- “是否完全移除 MDL”
- “预览材质是否参数完整”

---
## 常见问题
| 问题 | 可能原因 | 建议 |
|------|----------|------|
| 预览模式缺少 diffuseColor | 转换时未找到贴图或未写常量 | 查看审计 JSON 中该材质的贴图拷贝记录 |
| MDL 模式仍找到 shader | 转换未针对该文件执行 / 使用了错误的 USD | 确认是否针对该文件运行过 no-MDL 子命令 |
| normal 通道总是 Missing | 原 MDL 无法可靠解析法线贴图 | 后续可增强：在转换阶段补充 normal 纹理推断 |
| 纹理 exists=False | 相对路径未落地或复制失败 | 检查纹理复制目录及路径映射逻辑 |

---
## 版本
初始版本：inspect 子命令 v1（纯读取，无写操作）。
