# QEM 网格简化（Python实现增强版）超详细新手指南

> 本文面向**第一次接触网格简化与 UV 同步**的开发者，解释 `qem_simplify_ex` 函数的设计、输入输出、执行流程、以及为什么在简化时需要同时处理 face-varying UV。
>
> 对应源文件：`convert_asset/mesh/simplify.py`
>
> 函数位置：`qem_simplify_ex(...)`
>
> 推荐先阅读：`materials_texturing_mdl_for_beginners.md` 了解贴图与 UV 的关系。

---
## 1. 背景：为什么需要“增强版”简化函数
原始 `qem_simplify` 只负责几何（顶点 + 三角拓扑）简化，不处理任何 UV 数据。对于使用 **faceVarying** UV 的资产（即每个三角的每个角有独立 (u,v)），如果仅删除或重排面而不同步 UV：
- UV 数组长度与新三角数量乘以 3 不匹配 → 渲染器可能报错或贴图错位。
- 退化被删除的面仍保留其 UV（孤立数据） → 无意义且污染数据结构。

增强版 `qem_simplify_ex` 在保持原始 QEM 核心逻辑的基础上，添加了对 **面级 UV triplets** 的携带与过滤：
- 输入可选 `face_uvs`: 每面三个 UV `(u0,v0,u1,v1,u2,v2)`。
- 在边坍塌时只更新索引，不改 UV 值（保持原有纹理映射的局部形变）。
- 面退化被删除时同步丢弃对应 UV triplet。
- 最终输出新的面与对应的新 UV triplets，保证一一对应。

---
## 2. 函数签名与参数说明
```python
qem_simplify_ex(
    verts: list[tuple[float, float, float]],    # 输入顶点坐标 (x,y,z)
    faces: list[tuple[int, int, int]],          # 输入三角面 (i,j,k) 顶点索引
    target_faces: int,                          # 期望简化后面数的近似目标（非强制）
    face_uvs: Optional[list[tuple[float, float, float, float, float, float]]] = None,
        # 可选：每个面三对 (u,v) 展平成 6 个 float，与 faces 一一对应
    progress_cb: Optional[Callable[[int, int, int], bool]] = None,
        # 进度回调：参数 (collapsed_count, faces_current, faces_target)，返回 False 可中断
    interval: int = 5000,                       # 进度回调的坍塌间隔（节流）
    time_limit_seconds: Optional[float] = None, # 单次简化的时间上限（超时提前结束）
) -> (
    new_verts: list[tuple[float, float, float]],
    new_faces: list[tuple[int, int, int]],
    new_face_uvs: Optional[list[tuple[float, float, float, float, float, float]]]
)
```
### 输入约束
- `faces` 必须全部是三角（仓库中已在外层过滤非三角）。
- 若提供 `face_uvs`，长度必须与 `faces` 相同。
- 每个 `face_uvs[i]` 包含该面三个角的 UV：`(u0,v0,u1,v1,u2,v2)`。

### 输出保证
- `new_faces` 与 `new_face_uvs` 长度一致（若 `face_uvs` 输入为 None，则输出也为 None）。
- UV 顺序保持与面一致，不做重排（除去删除的退化面）。

---
## 3. 算法流程总览
| 步骤 | 说明 | 本实现做法 |
|------|------|-----------|
| 1. 初始化 | 拷贝顶点与面，创建存活标记与 Quadric | `V`, `F`, `v_alive`, `f_alive`, `v_quads` |
| 2. 构建 Quadric | 对每个三角建立平面 Quadric 累加到三顶点 | 法线归一化 + `plane_quadric` + `add_inplace` |
| 3. 邻接构建 | 为每个顶点列出相邻顶点 | 无向集合 `v_adj` |
| 4. 建候选边堆 | 每条边计算合并最优位置与误差压入最小堆 | `push_edge` + `optimal_position_cost` |
| 5. 主循环坍塌 | 弹出最小代价边 → 合并 → 更新面/邻接/Quadric | 跟踪 `faces_current` / 时间限制 / 回调 |
| 6. 面退化处理 | 合并后导致顶点重复的面标记删除 | `f_alive[fi]=False` |
| 7. 重新入堆 | u 的邻接边误差重新计算入堆 | 保持堆与当前几何一致 |
| 8. 进度回调 | 按坍塌间隔调用，可中断 | `progress_cb` 返回 False 直接 break |
| 9. 压缩输出 | 建立旧→新索引映射，过滤存活面 | 构造 `new_verts`, `new_faces` |
| 10. UV 同步 | 若提供 face_uvs，则同步保留未删除面的对应 triplet | 构造 `new_face_uvs` |

---
## 4. 核心数据结构解释
- `V: list[list[float]]` 顶点坐标可变副本；每次坍塌更新合并点位置。
- `F: list[list[int]]` 面索引可变副本；边坍塌后替换 v→u，并处理退化删除。
- `v_quads: list[list[float]]` 每顶点的 4x4 Quadric（二次误差矩阵），用 16 个 float 存储。
- `heap: list[tuple[cost,eid,u,v,pos]]` Python 最小堆，按误差 cost 取出最优边。`eid` 用于避免当 cost 相等时 Python 比较元组发生类型错误。
- `v_adj: list[set[int]]` 顶点邻接（无向），用于判断边是否仍有效及重建候选。
- `face_uvs` 与 `new_face_uvs`：输入与输出的面级 UV triplets 列表。仅在压缩阶段处理删除。

---
## 5. UV 处理策略（为什么这么简单）
### 不在坍塌中修改 UV 的原因
处理正确的面角 UV 需要复杂的选择：
- 理论上，合并后顶点位置改变可能需要重新投影或重采样 UV —— 这是高阶功能。
- 这里选择最稳妥最简单策略：只要面仍然存活，就保留其原始 3 个角的 UV；删除面则丢弃对应 UV。

### 潜在失真
- 当边两端顶点的空间位置发生较大变化而 UV 未变，可能造成轻微拉伸。
- 若需要更高质量，可在未来加入：
  - 限制跨“UV 缝”或 UV 差异过大的边坍塌。
  - 基于局部参数化重新估算合并点周围的 UV。

---
## 6. 与原始 `qem_simplify` 的差异
| 项目 | 原始版 | 增强版 |
|------|--------|--------|
| 函数名 | `qem_simplify` | `qem_simplify_ex` |
| UV 支持 | 无 | 可选 `face_uvs`，输出同步过滤 |
| 返回值 | (verts, faces) | (verts, faces, face_uvs?) |
| 侵入性 | 仅几何 | 几何 + 易于扩展到其他面级属性 |
| 后续扩展 | 需修改原函数 | 已预留可选参数模式 |

---
## 7. 进度与中断机制
- 通过 `progress_cb(collapsed, faces_current, faces_target)` 实现：
  - 定期回调（按 `interval` 坍塌数）
  - 可用于打印日志/ETA
  - 回调返回 False 时立即中断循环（常用于时间/用户取消）

- 时间上限：`time_limit_seconds` 在每轮循环开头判断是否超时，超时提前结束，保留当前部分结果。

---
## 8. 关键函数回顾
| 函数 | 作用 |
|------|------|
| `plane_quadric(a,b,c,d)` | 从平面方程参数构建 4x4 Quadric 矩阵 |
| `optimal_position_cost(Q, pu, pv)` | 对合并后顶点位置求解误差最小点，失败回退中点 |
| `solve3(A,b)` | 3x3 线性方程组求解（部分选主元） |
| `add_inplace(A,B)` | 矩阵元素级累加（降低临时分配） |
| `cross/dot/length/sub` | 基础向量运算 |

---
## 9. 复杂度与性能注意
- 每次边坍塌目前遍历所有面更新索引，复杂度较高 O(F * collapses)。适合中等规模或有坍塌上限/时间上限的场景。
- 优化方向：
  - 为顶点维护面邻接列表，从而只更新受影响的少量面。
  - 使用更高效的 C++/numba 加速（仓库已有 `backend_cpp.py` 可探索）。

---
## 10. 示例：调用增强版函数
假设你已经在外层提取了 face-varying UV：
```python
verts = [(0,0,0),(1,0,0),(0,1,0),(1,1,0)]
faces = [(0,1,2),(1,3,2)]  # 两个三角
face_uvs = [
    (0.0,0.0, 1.0,0.0, 0.0,1.0),  # 面0 三角三个角的 UV
    (1.0,0.0, 1.0,1.0, 0.0,1.0),  # 面1
]
new_verts, new_faces, new_face_uvs = qem_simplify_ex(
    verts, faces, target_faces=1, face_uvs=face_uvs
)
print(len(new_faces), len(new_face_uvs))  # 应为 1 1
```

---
## 11. 验证输出正确性的要点
- 简化前：`len(face_uvs) == len(faces)`。
- 简化后：`len(new_face_uvs) == len(new_faces)`。
- 对所有 `new_faces[i] = (a,b,c)`，不应出现重复索引（否则表示退化过滤失败）。
- `new_face_uvs[i]` 应该仍是 6 个 float，未出现 None 或长度不等。

---
## 12. 常见问题 FAQ
**Q: 为什么不在坍塌时重新计算 UV？**  
A: 简化实现保持最小侵入，避免引入 UV 参数化复杂度；重采样属于进阶功能。后续可在 push_edge 阶段判定边两端 UV 差异过大则跳过。

**Q: 如果我有 vertex 插值的 UV 怎么办？**  
A: 当前增强版只处理 faceVarying；vertex 插值可以在压缩阶段根据 `index_map` 重建新 UV 数组（后续可加）。

**Q: 为什么有 time limit？**  
A: 避免超大网格在纯 Python 环境耗时过长导致运行失控，便于中途终止仍得到部分结果。

**Q: 会不会出现 UV 与实际面不匹配的情况？**  
A: 只要传入的 `face_uvs` 与初始 `faces` 一一对应，且面退化被正确删除，就不会。

**Q: 如何进一步减少视觉失真？**  
A: 引入边折叠约束（跨缝/高差过滤）、法线翻转检测、局部曲率阈值、基于误差分布的多策略选择点位置。

---
## 13. 后续可扩展点（Roadmap）
1. Vertex UV 支持：增加 `vertex_uvs` 参数，坍塌后挑选或插值端点 UV。
2. 多属性同步：颜色、法线、切线、权重等面级/顶点级属性与几何同步。
3. 约束折叠：防止跨材质/跨 UV 缝折叠；维护边分类。
4. 法线更新：简化后重建顶点法线（面法线加权平均）。
5. 质量度量：输出误差统计（总 QEM 误差变化、边界面占比）。

---
## 14. 一句话总结
`qem_simplify_ex` 在原有 QEM 几何简化的基础上安全携带 face-varying UV，保证简化后贴图坐标仍与剩余三角一一对应。

---
## 15. 参考
- Quadric Error Metrics 原始论文：*Surface Simplification Using Quadric Error Metrics* （Garland & Heckbert, 1997）
- USD Primvars 与插值规范：USD 官方文档中 Geometry & Primvars 部分
- MDL 材质与纹理：NVIDIA MDL 手册

若你还有具体行级实现疑问，可直接查阅源码中每行注释（已全面标注）。
