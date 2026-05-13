# QEM 算法（Python 参考实现）

输入：
- V：三维点列表 `(x, y, z)`；
- F：三角面索引 `(i, j, k)`；
- 目标面数 T：由 `--ratio` 或规划阶段的 `--target-faces` 推导。

步骤：
1. 面二次型累加（见 `plane_quadric()` 与 `add_inplace()`）：
   ```python
   n = normalize(cross(q - p, r - p))
   d = -dot(n, p)
   K = plane_quadric(n.x, n.y, n.z, d)
   Q[i] += K; Q[j] += K; Q[k] += K
   ```
2. 构建顶点无向邻接并初始化边最小堆（见 `push_edge()`）：
   ```python
   Quv = add(Q[u], Q[v])
   pos, cost = optimal_position_cost(Quv, V[u], V[v])
   heapq.heappush(heap, (cost, eid, u, v, pos))
   ```
3. 主循环（从堆中取代价最低的边进行坍塌）：
   ```python
   while faces_current > faces_target and heap:
       cost, _, u, v, pos = heapq.heappop(heap)
       if not v_alive[u] or not v_alive[v]:
           continue
       if v not in v_adj[u]:
           continue
       # v -> u，位置设为 pos
       V[u] = [pos[0], pos[1], pos[2]]
       v_alive[v] = False
       add_inplace(Q[u], Q[v])
       # 重连邻接、更新三角、推新边...
   ```
4. 终止条件：达到目标面数 T、堆空或命中 `time_limit_seconds`；
5. 压缩顶点与重建三角索引映射（compaction）。

位置求解与代价：
```python
A = Q[:3,:3]; b = -Q[:3,3]
x = solve3(A, b)
if x is None: x = midpoint(u, v)
cost = v'^T Q v'  # v' = [x, y, z, 1]
```

边界与保护：
- 面法线近零（零面积面）直接丢弃；
- 线性系统奇异时回退到端点中点，保证稳健；
- 单网格时间上限触发时提前结束，返回“部分简化”的合法结果；
- v1 不做法线/UV 保留、不做翻面检测，仅几何/拓扑层面的减面。

源码参见：`convert_asset/mesh/simplify.py::qem_simplify()`，并配合其下方的 `solve3/quadric_eval` 等小工具函数。
