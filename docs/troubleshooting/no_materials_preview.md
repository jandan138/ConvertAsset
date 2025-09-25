# 场景打开后材质全灰 / 没有显示的排查与解决总结

> 适用范围：本项目 *_noMDL.usd 生成流程；针对“顶层文件打开后大面积灰、贴图/颜色缺失”问题的成因、定位方法与已实现的解决方案。

## 1. 现象回顾
- 打开顶层 `*_noMDL.usd`：几乎所有物体都是灰的 / 没贴图。
- 打开某个子级（例如 `.../bed/.../instance_noMDL.usd`）：材质正常，有颜色/贴图。
- Summary 中早期指标：
  - `Materials converted (preview/total)` 只有 2000 多（只覆盖顶层 root-owned 材质）。
  - `Materials without surface (after)` 高达 4000+（意味着很多 Material 在最终图里没有通用 `outputs:surface`）。

## 2. 根本原因拆解
| 问题 | 技术根因 | 直接后果 |
|------|----------|----------|
| 顶层灰 | 大量材质来自“外部引用”的 USD 文件（不是当前 root layer 拥有），初版逻辑只改当前文件 | 顶层看不到这些材质的 PreviewSurface 输出，只剩默认灰 |
| 贴图缺失 | 外部 MDL Shader 未被解析转接到 Preview，或贴图路径解析失败 | 即使有颜色逻辑，也只是灰底色 |
| 无 surface 输出 | 移除/Block MDL 输出后，没有创建通用 `outputs:surface` | 渲染器 fallback 到默认灰 |
| 统计有 MDL 残留 | 外部层 MDL Shader 还在（我们没改外部文件） | 严格验证失败（strict-fail） |

## 3. 早期“无材质”典型坑点
1. 只处理 root-owned 材质：外部引用材质完全没建 Preview → 大面积空 surface。
2. 删除 MDL 输出后忘了兜底：Material 没 `outputs:surface` → 渲染灰。
3. 外部引用路径层级（相对路径）解析错误，导致递归不到子文件，错失真正材质定义。
4. 实例 / 变体 中的属性 Block 失败：MDL 输出仍然存在 → 验证失败导致提前停止或误以为未处理。
5. 贴图路径锚点未使用属性真实 layer 目录，解析不到贴图。

## 4. 已实现的关键修复与增强
| 阶段 | 措施 | 作用 |
|------|------|------|
| 依赖收集 | 每条组合记录使用其 `layer_dir` 解析 + fallback raw Sdf PrimSpec 扫描 | 不遗漏子 USD，保障递归生成 *_noMDL |
| 本层替换 | `ensure_preview + copy_textures + connect_preview` | 将 root-owned MDL 转换成 UsdPreviewSurface |
| 外部材质 | 新增 **override 外部 Material 并建立 Preview 网络** | 顶层也能看到颜色/贴图（关键突破） |
| surface 兜底 | `post_process_material_surfaces` 自动补简易 PreviewSurface | 避免灰色空材质（即使 MDL 完全移除） |
| 强制 Block | 多层次策略：RemoveProperty → Block → break instance → overridePrim | 最大化屏蔽 MDL 输出 |
| 统计与 Summary | 输出：转换数量 / 无 surface / external vs root MDL / missing children | 快速诊断瓶颈 |

## 5. 外部材质可见性方案细节
流程（针对“外部 Material 有 MDL Shader”）：
1. `stage.OverridePrim(materialPath)`：在当前 *_noMDL 输出 layer 建立一个 override spec（不修改外部原文件）。
2. `ensure_preview()`：创建统一结构 `/<Material>/PreviewNetwork/...` 下的 PreviewSurface + UV + 四类纹理节点。
3. `copy_textures()`：从 MDL Shader pin 或解析 .mdl 文本提取 BaseColor / Roughness / Metallic / Normal 贴图与常量。
4. `connect_preview()`：将已抽取资源接入 PreviewSurface inputs。
5. （后续）统一清理 / Block 原 MDL 输出、删除本层可删的 MDL Shader（外部 MDL Shader 仍留在组合层）。

> 这样：即便外部文件没被修改，顶层组合时也“看见”一个有 `outputs:surface` 的 Preview 版本——材质不再灰。

## 5. 代码前后对比（可直接复制运行）

以下示例演示三类“从灰到可见”的最小化修复步骤，均基于项目内现成 API（`convert_asset.no_mdl.materials`）。

提示：将示例中的 `USD_PATH`/`MAT_PATH` 替换为你场景中的实际路径后运行即可。

### 5.1 给只有 MDL 的本地材质补建 PreviewSurface 并接管 outputs:surface

- Before（典型症状）
  - 该 Material 只有 `outputs:surface:mdl` 连接，缺少通用 `outputs:surface` 或未连接。

```python
from pxr import Usd, UsdShade

stage = Usd.Stage.Open(USD_PATH)
mat   = UsdShade.Material(stage.GetPrimAtPath(MAT_PATH))

print('has mdl out?', bool(mat.GetSurfaceOutput('mdl')))
out_def = mat.GetSurfaceOutput()
print('def surface connected?', bool(out_def and out_def.HasConnectedSource()))
# 输出通常为: True / False  —— 即只有 MDL，没有通用 surface
```

- After（修复：创建 Preview 网络 + 改接线）

```python
from pxr import Usd, UsdShade, Sdf
from convert_asset.no_mdl.materials import ensure_preview

stage = Usd.Stage.Open(USD_PATH)
mat   = UsdShade.Material(stage.GetPrimAtPath(MAT_PATH))

prev = ensure_preview(stage, mat)  # 创建 PreviewSurface/UV/纹理骨架
# 将通用 outputs:surface 指向 PreviewSurface
mat.CreateSurfaceOutput().ConnectToSource(prev.CreateOutput('surface', Sdf.ValueTypeNames.Token))

stage.GetRootLayer().Save()
```

运行后再次检查 `mat.GetSurfaceOutput().HasConnectedSource()` 应为 True，渲染不再灰。

### 5.2 对“外部引用材质”在当前层 override 并构建可见 Preview（不改外部文件）

- Before（典型症状）
  - 材质来自 referenced/payload/sublayer/variant 的外部文件；顶层看不到它的 Preview，呈灰色。

```python
from pxr import Usd, UsdShade

stage = Usd.Stage.Open(USD_PATH)
mat   = UsdShade.Material(stage.GetPrimAtPath(MAT_PATH))

print('owned by root layer?', stage.GetEditTarget().GetLayer().GetPrimAtPath(mat.GetPath()) is not None)
# 通常为 False，说明该 prim 的定义不在当前 root layer
```

- After（修复：override + 复制贴图 + 接线）

```python
from pxr import Usd, UsdShade
from convert_asset.no_mdl.materials import ensure_preview, find_mdl_shader, copy_textures, connect_preview

stage = Usd.Stage.Open(USD_PATH)

# 1) 在当前输出层对该材质建立 override（不会修改外部原文件）
stage.OverridePrim(MAT_PATH)
mat = UsdShade.Material(stage.GetPrimAtPath(MAT_PATH))

# 2) 定位外部材质上挂的 MDL Shader（若有）
mdl = find_mdl_shader(mat)

# 3) 构建 Preview 网络骨架
prev = ensure_preview(stage, mat)

# 4) 从 MDL pin 或 .mdl 文本复制/解析贴图与常量
filled, has_c, c_rgb, bc_tex = copy_textures(stage, mdl, mat)

# 5) 将已抽取的信息接线到 PreviewSurface
connect_preview(stage, mat, filled, has_c, c_rgb, bc_tex)

stage.GetRootLayer().Save()
```

完成后，即使外部文件未改，当前 *_noMDL.usd 层也提供了一个可渲染的 `outputs:surface`，顶层不再是灰色。

### 5.3 移除/屏蔽 MDL 输出并兜底创建最小 PreviewSurface

- Before（典型症状）
  - 我们已经断开/删除了 MDL，但该材质仍没有任何通用 `outputs:surface`，渲染器回退到灰色。

```python
from pxr import Usd, UsdShade

stage = Usd.Stage.Open(USD_PATH)
mat   = UsdShade.Material(stage.GetPrimAtPath(MAT_PATH))

print('has mdl out?', bool(mat.GetSurfaceOutput('mdl')))
out_def = mat.GetSurfaceOutput()
print('def surface connected?', bool(out_def and out_def.HasConnectedSource()))
# 通常: has mdl out? False 但 def surface connected? 也 False
```

- After（修复：清理 MDL 输出 + 确保最小可渲染 surface）

```python
from pxr import Usd, UsdShade
from convert_asset.no_mdl.materials import remove_material_mdl_outputs, ensure_surface_output

stage = Usd.Stage.Open(USD_PATH)

# 1) 尽可能移除/Block 所有 MDL 输出属性与连接（包含实例/变体下的处理与 override 兜底）
remove_material_mdl_outputs(stage)

# 2) 若该材质缺少通用 surface，则自动补一个最小 PreviewSurface（可配置基础色）
mat = UsdShade.Material(stage.GetPrimAtPath(MAT_PATH))
ensure_surface_output(stage, mat, base_color=(0.18, 0.18, 0.18))

stage.GetRootLayer().Save()
```

若你的场景存在“只读层/实例化”导致的 Block 失败，本项目已内置多层次重试策略：
- Break instance（`prim.SetInstanceable(False)`）再 Block；
- 建立 override spec 后在本层 Block；
- 最后兜底强制写入一个可 Block 的 attr 并打上 `customData.noMDL_forced_block=True` 标记。

## 6. 指标演进示例
| 指标 | 灰问题前 | 解决后 | 说明 |
|------|----------|--------|------|
| Materials converted (preview/total) | ~2313 | 6773 | 加入外部 override 后全部可见材质都建了 Preview |
| Materials without surface (after) | 4838 | 378 | 大部分缺失 surface 的材质被补齐 |
| External materials overridden with preview | 0 | 4460 | 新增指标，验证 override 覆盖范围 |
| External MDL shaders | 6771 | 6771 | 仍存在：外部文件里的 Shader 未被删除（保留参考） |

## 7. 仍存在的（设计内）现象
- External MDL shaders 数量不变：我们只是在当前 layer 提供替代渲染网络，并未失活原 Shader（可回溯）。
- Forced blocked outputs 多：统计是按属性/实例累积（包括外部） → 并不影响“视觉正确”，只影响严格 PASS 判定。
- 仍有少量 `auto_created`：这些材质没有 MDL Shader（或在未遍历 variant 内），故只补一个简易 PreviewSurface（颜色可能偏灰）。

## 8. 相关配置说明（与材质显示直接相关）
| 配置 | 作用 | 默认 |
|------|------|------|
| `OVERRIDE_EXTERNAL_MDL_PREVIEW` | 为外部材质建立本层 Preview 网络 | True |
| `CREATE_PREVIEW_FOR_EXTERNAL_MDL` | 对仍缺 surface 的材质自动补简易 Preview | True |
| `AUTO_PREVIEW_BASECOLOR` | 自动补的 PreviewSurface 基础色（无贴图时） | (0.18,0.18,0.18) |
| `ALLOW_EXTERNAL_ONLY_PASS` | 若仅剩外部 MDL，允许整体判 PASS | True |
| `REQUIRE_NO_MISSING_FOR_EXTERNAL_PASS` | external-only-pass 是否要求 missing child=0 | False |

## 9. 如何验证“材质显示链路”是否正常
1. 打开顶层 `_noMDL.usd`，随便点一个之前灰的对象。  
2. 找到它绑定的 `Material` prim：
   - 是否有子路径 `Material/PreviewNetwork/PreviewSurface`？
   - `Material.outputs:surface` 是否连接到 `PreviewSurface.outputs:surface`？
3. 展开 `PreviewNetwork/Tex_BaseColor`：是否有 `inputs:file` 且路径存在？
4. 如果仍灰：检查 BaseColor 纹理是否缺失 / 贴图路径是否相对错误。

## 10. 常见再发问题与排查
| 现象 | 可能原因 | 排查建议 |
|------|----------|----------|
| 少数材质仍灰 | 没有贴图信息且常量色为 0.18 默认 | 采样其 MDL Shader 看是否无有效 baseColor 定义 |
| 贴图不生效 | 路径解析失败（相对锚点错误） | 打印 `PRINT_DIAGNOSTICS` 查看解析日志；确认 .mdl 所在层目录 |
| external-only 仍 FAIL | root 层仍存在 blocked 输出统计 | 放宽判定或失活这些 blocked 属性 |

## 11. 后续可选优化（尚未实现）
- 失活 external MDL Shader (`SetActive(False)`) 彻底清空统计。
- JSON summary 输出给自动化管线。
- 贴图命中率统计：区分有贴图 vs 纯常量的 override 材质。
- 去重：对重复贴图/参数的外部材质合并共享 Preview Material，减小 layer 体积。
- 变体笛卡尔积遍历，覆盖在多个 VariantSet 特定组合里才出现的材质/MDL。

## 12. TL;DR（一句话总结）
通过“对外部引用材质在当前 *_noMDL.usd 层建立 PreviewSurface override + 自动补 surface 输出”两步，顶层文件获得了可渲染的通用着色网络，从而摆脱了原先的大面积灰色显示。

---
更新日期：2025-09-23
