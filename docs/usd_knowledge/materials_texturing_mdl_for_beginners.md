# MDL 材质贴图系统（小白完全指南）

> 目标读者：没有接触过 MDL / USD 贴图系统的初学者，希望弄清楚 `Materials` 目录里那些 `.mdl` 文件和一堆贴图是如何让模型“有颜色、有质感”的。
>
> 阅读结果：你能回答——纹理坐标来自哪里？材质里每张图起什么作用？为什么简化网格可能让贴图错位？如何检查 & 规避。

---
## 目录
1. 为什么需要材质与贴图
2. 整体资产目录结构回顾
3. 什么是 MDL（Material Definition Language）
4. 一个材质是怎么“引用”贴图的（数据流鸟瞰）
5. UV / 纹理坐标到底是什么？mapChannel 是什么？
6. `KooPbr_maps.mdl` 与核心函数拆解
7. 示例：从 `.mdl` 材质到最终渲染（逐行解释）
8. 常见贴图类型与用途（color / metallic / specular / gloss / normal / emission）
9. 贴图目录组织形式（`Textures/` vs `textures/` 分桶）
10. 网格简化为何会影响贴图（与 `simplify.py` 对照）
11. 如何验证贴图是否正确
12. 常见问题 FAQ
13. 后续扩展与优化建议

---
## 1. 为什么需要材质与贴图
一个裸的网格（只有顶点与三角面）只定义了“几何形状”。如果没有材质：
- 颜色统一（可能灰色）
- 无金属质感、无粗糙变化
- 没有法线细节（看上去平滑乏味）
- 无自发光效果

材质 + 多种贴图能让模型更加真实：木头、金属、塑料、布料、带凹凸的石头等都依赖材质参数和贴图驱动。

---
## 2. 整体资产目录结构回顾
在目标目录中我们看到：
```
instance.usd
instance_noMDL.usd
instance_simplified_50.usd
instance_simplified_95.usd
Materials/
  ├─ KooPbr.mdl
  ├─ KooPbr_maps.mdl
  ├─ MI_*.mdl （大量自动生成的具体材质实例）
  ├─ Textures/ （大量 png：color、metallic、specular、normal、gloss、emission 等）
  ├─ textures/ （分桶的 jpg，小写目录名，路径分层用于散列）
```
- `.usd` 文件：场景 / 模型容器，引用几何与材质。
- `.mdl` 文件：MDL 材质语言脚本，定义“如何根据纹理与参数计算外观”。
- `Textures/` / `textures/`：实际图片资源（PNG/JPG）。不同名字大小写与组织方式，功能上一致：提供纹理输入。

---
## 3. 什么是 MDL
MDL (Material Definition Language) 是 NVIDIA 提出的材质描述语言：
- 让材质逻辑（比如：采样贴图、混合颜色、应用法线）用可读的脚本描述。
- 渲染引擎（支持 MDL 的）会编译这些脚本，得到可执行着色程序。

对初学者简单理解：`.mdl` 就是“材质的公式文件”。你不需要写底层 GPU Shader；只要用 MDL 的函数组合贴图与参数。

---
## 4. 一个材质是怎么“引用”贴图的（数据流鸟瞰）
以典型流程总结：
```
Mesh -> 提供顶点坐标 + 三角面 + UV(纹理坐标)
UV(纹理坐标) + 贴图文件路径 -> 通过 MDL 函数采样得到颜色/高度/金属度等数值
MDL 材质主模块 -> 把这些数值组合成最终的物理属性 (漫反射、镜面反射、法线、自发光...) -> 交给渲染器
```
核心点：贴图文件本身只是“位图”，它必须通过“纹理坐标”索引才能被正确采样。纹理坐标来自 Mesh 的 UV 数据。

---
## 5. UV / 纹理坐标到底是什么？mapChannel 是什么？
- UV：每个网格顶点或面角关联的二维坐标 `(u,v)`，范围通常在 `[0,1]`。它是“把一个二维图片包裹到三维模型”的展开映射。
- 一个 Mesh 可以有多个 UV 集（比如 UV0, UV1 用于不同用途：底色、光照贴图等）。
- 在 MDL 中，`base::coordinate_source(texture_space: N)` 选择第 N 个 UV 集（从 0 开始计数）。
- `mapChannel` 参数常用来控制用哪一个 UV 集。看到：`mapChannel=1`，代码内部做 `texture_space: mapChannel-1`，则实际使用 `texture_space:0` → 即 UV0。

直观类比：
- 模型是一个 3D 橘子。
- UV 把橘子皮“剥开摊平”成二维图案坐标。
- 贴图是一张印在皮上的图；渲染时根据每个三角的 UV 坐标去取对应像素。

---
## 6. `KooPbr_maps.mdl` 与核心函数拆解
在 `KooPbr_maps.mdl` 里有几个重要函数：
### 6.1 `KooPbr_bitmap`
作用：载入一张 2D 贴图，将其根据 UV 做采样，并允许：
- 平移 (U_Offset, V_Offset)
- 缩放 (U_Tiling, V_Tiling)
- 旋转 (U_angle, V_angle, W_angle)
- 镜像 (U_Mirror, V_Mirror)
- 裁剪 (clipu, clipw, clipv, cliph)
还可选“反转颜色”、“输出单通道强度”等。
内部关键调用：
```mdl
base::file_texture(texture: filename, uvw: base::transform_coordinate(...))
```
### 6.2 `rotation_translation_scale_2_matrix`
生成一个 4x4 变换矩阵，用于把基本 UV 坐标做缩放、旋转、平移、镜像处理。
### 6.3 `KooPbr_bitmap_bump`
和 `KooPbr_bitmap` 类似，但用于法线/凹凸贴图（bump/normal），输出空间法线扰动。
### 6.4 `NormalMap_bump`
对法线贴图的 RGB 做翻转/交换、缩放，然后与原有法线混合得到最终法线方向。
### 6.5 Mix / Falloff
`KooPbr_mix` / `KooPbr_falloff` 提供两个贴图结果的混合（线性插值 / 基于 smoothstep）。

---
## 7. 示例：逐行理解一个材质实例
摘自 `MI_6543a8c6aaed890001b11ba0.mdl`：
```mdl
material MI_6543a8c6aaed890001b11ba0 = KooPbr::KooMtl(
    diffuse: color(0.9158, 0.9158, 0.9158),
    reflect: color(0.8885, 0.8885, 0.8885),
    reflect_glossiness: KooPbr_maps::KooPbr_bitmap(...).mono,
    texmap_bump: KooPbr_maps::KooPbr_bitmap_bump(...),
    ...
);
```
拆解：
1. 使用 `KooPbr::KooMtl`（主 PBR 材质模块）。
2. `diffuse` 与 `reflect` 是基础颜色与反射颜色的常量（有时也可用贴图，这里是固定值）。
3. `reflect_glossiness`：来自某张贴图的灰度输出 `.mono`（表示把贴图采样结果转换为单通道强度，用于控制粗糙/光泽）。
4. `texmap_bump`：一张法线或凹凸贴图经过 `KooPbr_bitmap_bump` 计算后的结果，用于添加表面细节。参数里包含：
   - `texture_2d("./textures/958/4c1/xxx.jpg", gamma_srgb, "")` 指向实际图片。
   - UV 控制参数（平移、缩放等）。
5. 其他如 `fresnel_ior`、`reflection_metalness` 是物理参数控制金属/折射/菲涅尔效果。

一个贴图采样调用示例（简化）：
```mdl
KooPbr_maps::KooPbr_bitmap(
  mapChannel=1,              // 使用 UV0
  U_Offset=0, V_Offset=0,
  U_Tiling=1, V_Tiling=1,
  filename=texture_2d("./Textures/5b1dded852b6140cb402dd7f_color.png", tex::gamma_srgb, "")
).tint  // 得到 RGB 颜色
```

---
## 8. 常见贴图类型与用途
| 类型 | 文件名常见后缀 | 作用 | 在材质里可能的用法 |
|------|----------------|------|------------------|
| Color / Albedo | `_color.png/.jpg` | 基础表面颜色 | 直接赋给 `diffuse` 或混合出最终基色 |
| Metallic | `_metallic.png` | 指示金属区域（影响反射模型） | 控制 `reflection_metalness` 或金属权重 |
| Specular | `_specular.png` | 镜面高光强度/颜色 | 控制高光、反射强度 |
| Gloss / Roughness | `_gloss.png` / 有时 `_roughness` | 表面粗糙度（影响高光大小） | 驱动 `reflect_glossiness` 等 |
| Normal | `_normal.png` | 法线扰动，增加细节 | 用在 `KooPbr_bitmap_bump` / `NormalMap_bump` |
| Bump / Height | 有时和 normal 合并 | 表面高度变化 | 叠加到法线结果中 |
| Emission | `_emission.png` | 自发光 | 驱动发光颜色或强度 |

实际材质可能只使用其中一部分；未使用的贴图会被忽略。

---
## 9. 贴图目录组织（`Textures/` vs `textures/`）
- `Textures/`：直接平铺大量 PNG 文件，命名里含用途后缀（`_color`, `_metallic`, `_specular`, `_normal`, `_gloss`, `_emission` 等）。
- `textures/`：按哈希 / 前缀分桶（例如 `./textures/05e/1dd/xxxx.jpg`），目的是避免单目录中文件过多影响加载或文件系统性能。
两者功能上无差别。材质里只要引用正确相对路径即可。

---
## 10. 网格简化为何会影响贴图（与 `simplify.py` 对照）
`simplify.py` 做的事情：
- 仅修改 Mesh 的 `points`（顶点坐标）与三角拓扑（删除/重排面）。
- 没有同步 UV primvar（`primvars:st` 或其他名字）。

可能的问题：
1. 如果 UV 插值是 `vertex`：顶点被合并 → 新顶点数变少 → 原 UV 数组长度不匹配；或不同 UV 合并成一个顶点导致拉伸/错色。
2. 如果 UV 插值是 `faceVarying`：删除/改面后，原有按面角展开的 UV 序列顺序错乱或长度不符。
3. 法线贴图的方向也会被破坏（若法线数据依赖旧拓扑）。

结果：渲染时贴图可能跳、糊、错位、全部黑或报错。需要在简化后重建或重新采样 UV（参见后续扩展建议）。

---
## 11. 如何验证贴图是否正确
手动 & 自动两种：
### 手动检查
1. 用支持 MDL 的查看器（例如 Omniverse）打开简化前后 USD。比较同一个材质的外观是否保持。
2. 检查 Mesh 的 primvars：数量是否与顶点或面角数一致。
3. 随机点选几个顶点的 UV，确认没有跑到极端值（比如全变成 0,0）。
### 简易脚本（伪代码）
```python
mesh = UsdGeom.Mesh(prim)
uv = mesh.GetPrimvar('st')
vals = uv.Get()
print('UV count:', len(vals), 'points:', len(mesh.GetPointsAttr().Get()))
# 如果插值是 vertex：len(vals) 应与 points 一致
# 如果 faceVarying：len(vals) 应与 sum(faceVertexCounts)
```
### 视觉差分
- 渲染同角度截图（前后）做像素差异热力图；差异剧烈说明映射失真。

---
## 12. 常见问题 FAQ
Q1：为什么材质里有那么多 `.mdl` 文件？
> 很多是自动生成的材质实例（不同参数/贴图组合），每个 MI_ 开头的文件代表一个独立材质。

Q2：为什么有的贴图只用灰度（`.mono`）？
> 粗糙度、金属度等参数只需要单通道；对彩色纹理取平均或指定 alpha 可得到强度。

Q3：我能直接删除 `textures/` 目录只留 `Textures/` 吗？
> 不行，材质可能引用了 `./textures/...` 路径；删除会导致找不到贴图。

Q4：简化后贴图错位如何快速“补救”？
> 若只是 vertex UV：用旧→新索引映射拷贝保留；若是 faceVarying：提前缓存三角的 3 个 UV，并同步更新再重建。

Q5：如何判断是 vertex 还是 faceVarying UV？
> `uvPrimvar.GetInterpolation()` 返回字符串：`"vertex"` 或 `"faceVarying"`。

Q6：MDL 与普通 `UsdPreviewSurface` 有什么区别？
> MDL 更强大（支持更多控制），但需要支持 MDL 的渲染环境；`UsdPreviewSurface` 是通用最低公分母。

Q7：贴图的 gamma 模式 `tex::gamma_srgb` 是做什么的？
> 指示采样时按 sRGB→线性空间转换，保证物理着色计算正确。

Q8：法线贴图为什么看起来“偏蓝”？
> 标准切线空间法线贴图的默认背景是 (0.5, 0.5, 1.0)，表示“指向 z 轴”。

---
## 13. 后续扩展与优化建议
- 在简化代码里添加对 UV 的同步（vertex 与 faceVarying 两种分支）。
- 对法线贴图做切线重建（坍塌后法线可能失真）。
- 引入边折叠约束：禁止跨“UV 缝”或法线角度差大于阈值的边坍塌，减少视觉破坏。
- 建立材质使用统计：哪些贴图实际被使用，未引用的贴图可归档或删减。
- 做纹理打包：将多个小贴图合并成图集（Atlas）以减少加载调用。

---
## 术语速查
| 术语 | 解释 |
|------|------|
| UV | 展开二维纹理的坐标；U 横向，V 纵向。 |
| mapChannel | 指选择哪一组 UV（从 1 开始写，内部减一变成 0 基）。 |
| Albedo | 基础反照颜色，不含光照信息。 |
| Metallic | 金属度，区分金属与非金属反射模型。 |
| Specular | 镜面反射强度或颜色。 |
| Gloss / Roughness | 表面微观粗糙度，影响高光范围。 |
| Normal Map | 法线扰动贴图，为平面增加细节感。 |
| Bump | 灰度高度 → 近似法线或位移。 |
| Emission | 自发光颜色。 |
| MDL | 材质描述语言，脚本化定义材质行为。 |
| Primvar | USD 中的自定义几何属性（如 UV、颜色、权重）。 |

---
## 最后总结（一句话版）
材质里的每张贴图都通过 MDL 函数依赖 Mesh 的 UV0 来采样；网格简化如果不同时更新 UV，就会让贴图从正确位置“滑掉”。

如果你需要，我可以下一步帮你在 `simplify.py` 里加一个最基础的 vertex UV 保留补丁（或 faceVarying 缓存方案），告诉我你的资产主要是哪种 UV 插值即可。
