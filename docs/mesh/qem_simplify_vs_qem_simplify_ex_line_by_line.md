# qem_simplify_ex vs qem_simplify 逐行详细对比（convert_asset/mesh/simplify.py）

本文对比 `convert_asset/mesh/simplify.py` 中两个核心函数：
- `qem_simplify(verts, faces, target_faces, progress_cb=None, interval=5000, time_limit_seconds=None)`
- `qem_simplify_ex(verts, faces, target_faces, face_uvs=None, progress_cb=None, interval=5000, time_limit_seconds=None)`

二者共享相同的 QEM（Quadric Error Metrics）折叠主流程，但 `qem_simplify_ex` 在“保持 face-varying UV（三角角点 UV）与拓扑同步”方面做了增强，返回值也多了 UV 输出。

---

## 1) 接口与契约（Inputs / Outputs）

- 共同点（两者均支持）：
  - `verts: list[tuple[float,float,float]]` 顶点坐标（x,y,z）
  - `faces: list[tuple[int,int,int]]` 三角面（顶点索引三元组）
  - `target_faces: int` 期望的三角面数（非严格，但尽力接近）
  - 可选 `progress_cb(collapsed, faces_current, faces_target) -> bool`：进度回调，返回 False 可中断
  - `interval: int`：按“坍塌次数”触发回调的步长
  - `time_limit_seconds: Optional[float]`：单个网格的时间上限（超时提前返回）

- 差异（ex 的增强）：
  - `qem_simplify_ex` 多了参数 `face_uvs: Optional[list[tuple[float,float,float,float,float,float]]]`
    - 与 `faces` 一一对应，每个三角提供 3 个 (u,v)，展平成 6 个 float：`(u0,v0,u1,v1,u2,v2)`
    - 若传入 None，表示不处理 UV；若传入列表，会在简化过程中同步过滤对应的 UV 三元组
  - 返回值：
    - `qem_simplify` 返回 `(new_verts, new_faces)`
    - `qem_simplify_ex` 返回 `(new_verts, new_faces, new_face_uvs | None)`

---

## 2) 数据结构初始化（逐行对照）

两者相同：
- 将 `verts`/`faces` 拷贝为可变列表 `V`/`F`
- 创建存活标记 `v_alive`/`f_alive`
- 为每个顶点准备 `v_quads`（4x4 Quadric，拉直为 16 浮点）
- 遍历每个三角：根据三点计算平面法线与 `d`，构造 `K=pp^T`，累加到三个顶点的 Quadric（退化面置 `f_alive=False`）
- 构建无向邻接 `v_adj`
- 定义最小堆（`heapq`）中元素：`(cost, eid, u, v, pos)`，并用 `push_edge(u,v)` 将所有无向边（u<v）入堆（`Quv=Qu[u]+Qu[v]`，`optimal_position_cost` 给出 `pos` 与 `cost`）
- 设定循环控制：`faces_target`、`faces_current`、`collapsed`、`last_emit_collapses`、`start_t`

`qem_simplify_ex` 的不同点：
- 在函数签名层面接受 `face_uvs`
- 在最终“压缩与输出”阶段会额外分配/填充 `new_face_uvs`

---

## 3) 主循环（候选边坍塌）对比

两者逻辑一致：
1. 超时提前返回（若设置了 `time_limit_seconds`）
2. 从堆中取代价最小的 `(u,v)`
3. 跳过已失效候选（端点已移除或不再相邻）
4. 执行坍塌：
   - 顶点 `u` 的位置设为 `pos`
   - `v_alive[v]=False`
   - 合并 Quadric：`Q[u]+=Q[v]`
   - 将 `v` 的邻居全部改连到 `u`（更新 `v_adj`）
5. 更新所有三角：把索引中的 `v` 改为 `u`，若出现重复顶点（三角退化）则 `f_alive[fi]=False`，并 `faces_current -= 1`
6. 重新将 `u` 的邻接边入堆（代价随位置与 Quadric 变化）
7. 计数 `collapsed += 1`，到达 `interval` 则触发 `progress_cb`，返回 False 则中断

UV 的同步策略（仅 `qem_simplify_ex`）：
- 在“坍塌”过程中并不直接写/改 UV 值
- 仅在“某个三角退化被删除”时，通过 `f_alive[fi]` 标记删除。最终输出阶段使用此掩码对 `face_uvs` 做一致的过滤

这种“延迟处理”的好处：
- 避免在每次坍塌时进行大量的 UV 拆分/重组，效率更可控
- 对于纯三角且 UV 为 face-varying 的常见场景，能稳定地与拓扑一一对应

---

## 4) 压缩与输出（最核心差异）

共同：
- 重建“旧顶点索引 → 新顶点索引”的 `index_map`
- 输出 `new_verts`
- 遍历 `f_alive`，对仍存活的三角 `(a,b,c)` 做索引映射，得到 `new_faces`

差异（ex 特有）：
- 若 `face_uvs is not None`，则分配 `new_face_uvs: list[uv_triplet]`（初始空列表）
- 在写入 `new_faces` 的同时，同步 `new_face_uvs.append(face_uvs[fi])`
  - 注意：`fi` 是旧三角的索引，只有当该旧三角仍“存活并被映射”时，才拷贝对应的 UV triplet
- 最终返回 `(new_verts, new_faces, new_face_uvs)`；若未提供 `face_uvs` 则返回第三项 `None`

---

## 5) 误差评估与最优位置（一致）

二者共享同一套线性代数工具：
- `plane_quadric(a,b,c,d)` 生成 4x4 Quadric（`pp^T`）
- `optimal_position_cost(Q, pu, pv)`：优先解 `A x = b`（`A=Q[0:3,0:3]`, `b=-Q[0:3,3]`），失败则退化为端点中点；代价 `v'^T Q v'`
- `solve3(A,b)`：3x3 高斯消元（部分选主元）返回解或 `None`

---

## 6) 关键差异速览（表格）

| 方面 | qem_simplify | qem_simplify_ex |
|---|---|---|
| UV 支持 | 不处理 | 支持输入 `face_uvs`，输出 `new_face_uvs`（与 `new_faces` 一一对应） |
| 函数返回 | `(new_verts, new_faces)` | `(new_verts, new_faces, new_face_uvs or None)` |
| 坍塌过程中 UV 处理 | 无 | 不改动数值，仅在删除三角时同步丢弃对应 triplet，输出阶段再过滤 |
| 额外开销 | 无 | 仅在输出阶段根据 `f_alive` 做一次线性过滤（O(#faces)) |

---

## 7) 边界与鲁棒性说明

- 两者：
  - 退化面（法线近零）会被标记删除
  - `time_limit_seconds` 超时提前返回（返回部分结果）
  - `progress_cb` 可中断（返回 False）
- `qem_simplify_ex`：
  - 若未传入 `face_uvs`（`None`），则等价于 `qem_simplify` 的 UV 行为（返回第三项 `None`）
  - 仅支持“每个三角对应 3 个角点 UV（face-varying）”的常见情形；不在折叠时重构/重采样 UV

---

## 8) 何时使用哪个函数？

- 需要保持 MDL/纹理不花（face-varying `st`）→ 用 `qem_simplify_ex`
- 只做几何粗化、没有 UV 约束 → 用 `qem_simplify`（更轻量些）

---

## 9) 最小使用示例

- 仅几何简化：

```python
new_verts, new_faces = qem_simplify(verts, faces, target_faces=10000,
                                    progress_cb=None, interval=5000, time_limit_seconds=5.0)
```

- 携带 face-varying UV（每面三元组）：

```python
new_verts, new_faces, new_face_uvs = qem_simplify_ex(
    verts,
    faces,
    target_faces=10000,
    face_uvs=face_uv_triplets,  # [(u0,v0,u1,v1,u2,v2), ...] 与 faces 对齐
    progress_cb=None,
    interval=5000,
    time_limit_seconds=5.0,
)
```

- 将 `new_face_uvs` 写回 USD `primvars:st`（示意，同文件中的 `_write_facevarying_uv`）：

```python
# face_uvs -> TexCoord2f[] (faceVarying)
_write_facevarying_uv(mesh, new_face_uvs, name="st")
```

---

## 10) 性能与内存

- 两者的核心复杂度由候选边堆与拓扑更新主导；`qem_simplify_ex` 只在末尾增加一次线性过滤 `face_uvs` 的步骤
- 若网格超大，建议：
  - 设置 `time_limit_seconds`，避免在单个网格上超时
  - 通过 `interval` 和 `progress_cb` 监控进度
  - 预先保证输入是“纯三角”（避免频繁退化）

---

## 11) 小结

- 代码主体（构建 Quadric → 入堆 → 坍塌 → 重建索引）的行序与逻辑在两个函数中基本一致
- `qem_simplify_ex` 在“输出阶段”多出一个 `new_face_uvs` 的分支，按照 `f_alive` 对 `face_uvs` 做同步筛选，实现“几何拓扑变化与面角 UV 的一致保留”
- 对于使用 MDL 且依赖 `primvars:st`（face-varying）的资产，建议优先采用 `qem_simplify_ex`
