# -*- coding: utf-8 -*-  # 指定源码文件使用 UTF-8 编码，避免中文注释乱码
"""
QEM（Quadric Error Metrics）三角网格简化（Python 参考实现）。

目标与范围：
- 面向 `UsdGeom.Mesh`，且仅在“全部为三角面”的网格上运行（`faceVertexCounts == 3`）。
- 跳过不活跃（Inactive）、Instance Proxy，以及 `purpose` 为 `proxy/guide` 的网格。
- 纯 Python 实现，不依赖外部三方库，便于理解与验证；适合小中型网格或在有 `max_collapses/时间限制` 保护的场景。

输出行为：
- `apply=True`：对每个符合条件的网格进行实际拓扑更新（点位与三角面索引），并在调用侧导出到指定 `out_path`。
- `apply=False`（dry-run）：仅估算前后面数，不修改原始 USD。

实现要点（简述）：
1. QEM 基本思想：为每个三角面构建一个“平面二次误差矩阵”（quadric），并累加到该面的三个顶点上；
     边坍塌时，选取能最小化误差的合并位置（解线性方程或使用端点中点作为回退），以代价最小的边优先坍塌。
2. 本实现的“代价”与“最优位置”来自 4x4 Quadric 的 `v^T Q v`；当矩阵不可解时使用端点中点作为降级策略。
3. 为保证稳健性与易读性：
     - 省略了很多网格鲁棒性细节（例如拓扑约束、法线/UV 保留、边界保持、折叠翻转检测），
         但保留了核心数据流：构建 Quadric → 堆选边 → 坍塌 → 重建邻接与候选边 → 直到达到目标面数/时间上限。
4. 进度与时限：
     - 允许通过 `progress_cb` 回调报告进度（避免“无输出”观感），并支持 `time_limit_seconds` 对单网格限时，
         到时会提前终止该网格的简化（不中断整个 Stage）。
"""
from __future__ import annotations  # 允许在类型注解中使用前向引用（Python 3.7+ 风格）

from dataclasses import dataclass  # 引入 dataclass 简化数据类定义
from typing import Any, Iterable, Callable, Optional  # 类型注解：任意类型、可迭代、回调、可选
import math  # 数学函数库（如 sqrt）
import heapq  # 最小堆（优先队列）实现，用于边候选的“代价最小先出”
import time  # 时间相关工具，用于限时和进度 ETA 计算

try:
    from pxr import Usd, UsdGeom, Gf, Sdf  # type: ignore  # USD 的 Python 绑定（Isaac/pxr 环境提供）
except Exception:  # pragma: no cover  # 无法导入 pxr 时不中断（便于静态检查/文档生成）
    Usd = None  # type: ignore[assignment]  # 占位：标记当前环境不可用 USD
    UsdGeom = None  # type: ignore[assignment]  # 占位：同上
    Gf = None  # type: ignore[assignment]
    Sdf = None  # type: ignore[assignment]


@dataclass  # 使用数据类自动生成初始化与repr，便于汇总统计输出
class SimplifyStats:
    meshes_total: int = 0  # 遍历到的 Mesh 总数（符合 Active+purpose 过滤）
    meshes_tri: int = 0  # 其中完全为三角网格的数量
    faces_before: int = 0  # 所有三角网格的总面数（处理前）
    faces_after: int = 0  # 所有三角网格的总面数（处理后，或dry-run估算）
    verts_before: int = 0  # 所有三角网格的顶点总数（处理前）
    verts_after: int = 0  # 所有三角网格的顶点总数（处理后，或dry-run保守估计）
    skipped_non_tri: int = 0  # 被跳过的非三角网格数量
def list_mesh_face_counts(stage_or_path: str | Any) -> list[tuple[str, int]]:  # 返回 (Prim路径, 面数) 列表
    """列出 Stage 中所有“活跃的、渲染用途的三角网格”的面数统计。

    返回：`[(prim_path, face_count), ...]`
    - 仅包含：`Imageable.purpose in {default, render}` 的 `UsdGeom.Mesh`；
    - 跳过：Inactive、Instance Proxy、`purpose in {proxy, guide}`。
    - 面数即 `faceVertexCounts` 的条目数（不验证是否为三角）。
    """
    if Usd is None or UsdGeom is None:  # 若当前环境无 USD 绑定，则报错提示需在 Isaac/pxr 环境运行
        raise RuntimeError("pxr.Usd not available; run inside Isaac/pxr environment")
    stage = stage_or_path if isinstance(stage_or_path, Usd.Stage) else Usd.Stage.Open(stage_or_path)  # type: ignore[name-defined]  # 支持传入已开的Stage或路径
    if stage is None:  # 打不开则报错（路径错误或权限不足等）
        raise RuntimeError(f"Failed to open stage: {stage_or_path}")
    out: list[tuple[str, int]] = []  # 结果列表
    for prim in stage.Traverse():  # 深度优先遍历整个 Stage（保持组合结构，不打平）
        if not prim.IsActive() or prim.IsInstanceProxy():  # 跳过非激活和实例代理（避免重复统计）
            continue
        if prim.GetTypeName() != "Mesh":  # 仅处理 Mesh 类型的 Prim
            continue
        img = UsdGeom.Imageable(prim)  # 转为 Imageable 以便获取 purpose
        try:
            purpose = img.ComputePurpose()  # 计算有效的 purpose（考虑继承与强弱）
            if purpose in (UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide):  # 忽略 proxy/guide 用途
                continue
        except Exception:
            pass  # 某些 Prim 可能不支持，忽略异常继续
        mesh = UsdGeom.Mesh(prim)  # 构造 Mesh 句柄
        counts = mesh.GetFaceVertexCountsAttr().Get()  # 读取每个面的顶点数数组
        if not counts:  # 无拓扑则跳过
            continue
        out.append((prim.GetPath().pathString, len(counts)))  # 面数等于条目数
    return out  # 返回 (路径, 面数) 列表



def simplify_stage_meshes(
    stage_or_path: str | Any,  # USD 路径或已打开的 Stage
    ratio: float = 0.5,  # 目标面数比例（0..1]，最终目标=faces_n*ratio
    max_collapses: int | None = None,  # 最大允许坍塌次数（安全上限）
    out_path: str | None = None,  # 导出路径（当 apply=True 时可用）
    apply: bool = False,  # 是否实际应用（写回拓扑）
    show_progress: bool = False,  # 是否打印每网格的进度
    progress_interval_collapses: int = 5000,  # 进度回调的坍塌间隔
    time_limit_seconds: Optional[float] = None,  # 单网格的时间上限（秒）
) -> SimplifyStats:  # 返回全场统计信息
    if Usd is None or UsdGeom is None:  # 无 USD 环境时报错
        raise RuntimeError("pxr.Usd not available; run inside Isaac/pxr environment")
    stage = stage_or_path if isinstance(stage_or_path, Usd.Stage) else Usd.Stage.Open(stage_or_path)  # type: ignore[name-defined]  # 打开或复用 Stage
    if stage is None:  # 打不开则报错
        raise RuntimeError(f"Failed to open stage: {stage_or_path}")
    # 汇总统计对象与“待写回编辑”列表（apply=True 时批量写回）
    stats = SimplifyStats()  # 初始化统计累加器
    # 收集每个网格的新几何 (prim, verts, faces, optional face_varying_uv_triplets)
    mesh_edits: list[tuple[Any, list[tuple[float, float, float]], list[tuple[int, int, int]], Optional[list[tuple[float, float, float, float, float, float]]]]] = []

    for prim in stage.Traverse():  # 遍历所有 Prim
        if not prim.IsActive() or prim.IsInstanceProxy():  # 跳过非激活/实例代理
            continue
        if prim.GetTypeName() != "Mesh":  # 仅 Mesh
            continue
        img = UsdGeom.Imageable(prim)  # 获取 purpose
        try:
            purpose = img.ComputePurpose()  # 计算 purpose
            if purpose in (UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide):  # 过滤 proxy/guide
                continue
        except Exception:
            pass  # 忽略异常
        stats.meshes_total += 1  # Mesh 总数 +1
        mesh = UsdGeom.Mesh(prim)  # Mesh 句柄
        counts = mesh.GetFaceVertexCountsAttr().Get()  # 每面顶点数数组
        indices = mesh.GetFaceVertexIndicesAttr().Get()  # 全部面的顶点索引串
        if not counts or not indices:  # 缺少拓扑信息则跳过
            continue
        if not _all_triangles(counts):  # 存在非三角面则跳过（Python 后端仅支持三角）
            stats.skipped_non_tri += 1  # 记录跳过数量
            continue
        stats.meshes_tri += 1  # 确认是三角网格
    # 仅统计路径（dry-run 快速）：不构建逐面的 faces 列表，直接估算目标面数
        faces_n = len(counts)  # 当前网格的面数
        pts = mesh.GetPointsAttr().Get() or []  # 顶点坐标数组
        stats.faces_before += faces_n  # 累加全场“处理前”面数
        stats.verts_before += len(pts)  # 累加全场“处理前”顶点数
        # 计算目标面数：比率裁剪至[0,1]后乘以 faces_n，向下取整；再考虑最大坍塌上限
        target_faces = max(0, int(faces_n * max(0.0, min(1.0, ratio))))  # 基于比率
        if max_collapses is not None:  # 若设置了最大坍塌数，则不能少于 faces_n - max_collapses
            target_faces = max(target_faces, faces_n - int(max_collapses))

        if apply and faces_n > target_faces:  # 仅当实际应用且确需减少面数时才构建完整数据并执行
            # Build full structures only when applying
            verts = [(float(p[0]), float(p[1]), float(p[2])) for p in pts]  # 顶点三元组列表
            faces = _tri_faces_from_topology(counts, indices)  # 将拓扑展开为 (i,j,k) 面列表
            # 若存在 faceVarying UV，则构建每面三个UV的triplet列表 (u0,v0,u1,v1,u2,v2)
            face_uv_triplets: Optional[list[tuple[float, float, float, float, float, float]]] = None
            try:
                st_pv = UsdGeom.PrimvarsAPI(mesh).GetPrimvar("st")  # 常见UV名称：st
                if st_pv and st_pv.HasValue():
                    interp = st_pv.GetInterpolation()
                    if interp == UsdGeom.Tokens.faceVarying:
                        uv_vals = st_pv.Get() or []
                        total_corners = sum(int(c) for c in counts)
                        if uv_vals and len(uv_vals) == total_corners:
                            face_uv_triplets = []
                            it_idx = 0
                            for c in counts:
                                c = int(c)
                                if c != 3:
                                    # 仅支持三角；理论上不会到这里，因为上游已过滤
                                    it_idx += c
                                    continue
                                uv0 = uv_vals[it_idx]
                                uv1 = uv_vals[it_idx + 1]
                                uv2 = uv_vals[it_idx + 2]
                                # 统一转为 float
                                u0, v0 = float(uv0[0]), float(uv0[1])
                                u1, v1 = float(uv1[0]), float(uv1[1])
                                u2, v2 = float(uv2[0]), float(uv2[1])
                                face_uv_triplets.append((u0, v0, u1, v1, u2, v2))
                                it_idx += 3
            except Exception:
                # 如果任何一步失败，则忽略 UV（不致命）
                face_uv_triplets = None
            # Prepare progress reporter per-mesh
            reporter: Optional[Callable[[int, int, int], bool]] = None  # 进度回调（可中断）
            start_t = time.time()  # 网格级起始时间
            last_emit = 0.0  # 上次进度打印时间戳
            if show_progress:
                mesh_path = prim.GetPath().pathString  # 便于日志标识
                faces_before_local = faces_n  # 该网格最初面数
                def _report(collapsed: int, faces_current: int, faces_target: int) -> bool:
                    nonlocal last_emit  # 引用外部变量
                    now = time.time()  # 当前时间
                    # Always print the very first progress (collapsed==0), then throttle to ~1s
                    if collapsed == 0 or (now - last_emit) >= 1.0:  # 首次或每~1秒打印一次进度
                        total_need = max(1, faces_before_local - faces_target)  # 需要减少的总面数
                        done = max(0, faces_before_local - faces_current)  # 已减少的面数
                        frac = max(0.0, min(1.0, done / float(total_need)))  # 完成比例
                        eta = (now - start_t) * (1.0 - frac) / max(1e-6, frac) if frac > 0 else float('inf')  # 粗略 ETA
                        print(f"[PROGRESS] {mesh_path} {done}/{total_need} ({frac*100:.1f}%) collapsed={collapsed} ETA≈{eta:.1f}s")  # 进度行
                        last_emit = now  # 更新上次打印时间
                    if time_limit_seconds is not None and (now - start_t) >= time_limit_seconds:  # 命中单网格时限
                        print(f"[TIMEOUT] aborting mesh {mesh_path} after {time_limit_seconds}s")  # 打印超时
                        return False  # 通过回调返回 False 让算法中断该网格
                    return True  # 继续
                reporter = _report  # 赋值回调
            # START line
            if show_progress:
                print(f"[START] {mesh_path} faces {faces_before_local} -> target {target_faces}")  # 打印网格开始信息
                # initial progress emit
                if reporter:  # 触发一次初始进度（collapsed==0）
                    reporter(0, faces_before_local, target_faces)
            # 核心简化调用（增强版）：返回新的顶点、三角面与（可选）新的UV triplets
            verts2, faces2, face_uvs2 = qem_simplify_ex(
                verts,  # 输入顶点
                faces,  # 输入三角
                target_faces,  # 目标面数
                face_uvs=face_uv_triplets,  # 面角UV（可选）
                progress_cb=reporter,  # 进度回调（可中断）
                interval=progress_interval_collapses,  # 回调间隔（按坍塌次数）
                time_limit_seconds=time_limit_seconds,  # 单网格时限
            )
            stats.faces_after += len(faces2)  # 累加“处理后”的总面数
            stats.verts_after += len(verts2)  # 累加“处理后”的总顶点数
            mesh_edits.append((prim, verts2, faces2, face_uvs2))  # 记录该网格的写回数据
        else:
            # dry-run：仅估算面数（保持顶点数不变，作为保守估计；实际坍塌后顶点数会下降）
            stats.faces_after += target_faces if faces_n > target_faces else faces_n  # 面数估算
            stats.verts_after += len(pts)  # 顶点估算（保守：不变）

    if apply and mesh_edits:  # 仅当实际应用且有网格变更时才写回/导出
        # Apply edits and export
        for prim, verts2, faces2, face_uvs2 in mesh_edits:  # 逐网格写回点与拓扑
            _write_mesh_triangles(UsdGeom.Mesh(prim), verts2, faces2)  # 设置 points/topology 属性
            # 若有新的 face-varying UV，则写回到 primvars:st
            if face_uvs2:
                _write_facevarying_uv(UsdGeom.Mesh(prim), face_uvs2, name="st")
        if out_path:  # 若提供输出路径，则导出新的 USD 文件
            stage.Export(out_path)
    return stats  # 返回全场统计


def qem_simplify(
    verts: list[tuple[float, float, float]],  # 输入顶点坐标列表
    faces: list[tuple[int, int, int]],  # 输入三角面索引列表
    target_faces: int,  # 目标面数（非严格，但尽力接近）
    progress_cb: Optional[Callable[[int, int, int], bool]] = None,  # 进度回调（返回 False 可中断）
    interval: int = 5000,  # 回调间隔（按坍塌次数）
    time_limit_seconds: Optional[float] = None,  # 单网格时限（秒）
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:  # 返回新的 (顶点, 三角)
    """Simplify a triangle mesh to approximately target_faces using QEM.

    Pure Python reference implementation. Suitable for small meshes or capped collapses.
    """
    # ========== 构建简化所需的基础结构 ==========
    # 可变拷贝：V=顶点坐标，F=三角面索引；alive 标记分别表示顶点/面是否仍然“存活”。
    V = [list(v) for v in verts]  # 顶点坐标的可变副本
    F = [list(f) for f in faces]  # 三角索引的可变副本
    v_alive = [True] * len(V)  # 顶点是否“存活”（未被合并）
    f_alive = [True] * len(F)  # 面是否“存活”（未退化/被删除）
    v_quads = [mat4_zero() for _ in V]  # 每个顶点对应的 Quadric（4x4，拉直存储）

    # 1) 计算初始顶点 Quadric：对每个三角面，求面法线 n 与平面 d，形成 4x4 矩阵 K，并累加到三个顶点上。
    for fi, f in enumerate(F):  # 遍历每个三角面，构建并累加 Quadric
        if not f_alive[fi]:  # 已经被判退化的面跳过
            continue
        i, j, k = f  # 三角的三个顶点索引
        p = V[i]  # 顶点 i 的坐标
        q = V[j]  # 顶点 j 的坐标
        r = V[k]  # 顶点 k 的坐标
        n = cross(sub(q, p), sub(r, p))  # 面法线（未归一化）= (q-p)×(r-p)
        norm = length(n)  # 法线长度
        if norm <= 1e-12:  # 面积近零则视为退化面
            f_alive[fi] = False  # 标记该面无效
            continue
        n = [n[0] / norm, n[1] / norm, n[2] / norm]  # 归一化法线
        d = -dot(n, p)  # 平面常数项 d = -n·p
        K = plane_quadric(n[0], n[1], n[2], d)  # 构建该面的 4x4 二次型矩阵
        add_inplace(v_quads[i], K)  # 累加到三个顶点的 Quadric
        add_inplace(v_quads[j], K)
        add_inplace(v_quads[k], K)

    # 2) 构建顶点邻接（无向图）：每个顶点记录与其相邻的顶点集合
    v_adj: list[set[int]] = [set() for _ in V]  # 顶点的邻接集合（无向）
    for f in F:  # 根据每个三角的三个边，填充邻接
        a, b, c = f
        v_adj[a].update((b, c))
        v_adj[b].update((a, c))
        v_adj[c].update((a, b))

    # 3) 初始化边堆（最小堆）：元素为 (cost, eid, u, v, pos)
    #    - cost：合并误差；eid：入堆序号避免比较歧义；u,v：边两个顶点；pos：合并后位置
    heap: list[tuple[float, int, int, int, tuple[float, float, float]]] = []  # 最小堆：按代价排序
    eid = 0  # 入堆序号，避免比较歧义
    def push_edge(u: int, v: int):  # 将边(u,v)作为候选压入堆
        nonlocal eid
        if u == v:  # 自环忽略
            return
        if v not in v_adj[u]:  # 非邻接忽略（可能因拓扑更新导致）
            return
        Quv = add(v_quads[u], v_quads[v])  # 合并端点的 Quadric
        pos, cost = optimal_position_cost(Quv, V[u], V[v])  # 计算最佳合并位置与代价
        heapq.heappush(heap, (cost, eid, u, v, pos))  # 压入堆（代价最小优先）
        eid += 1  # 自增序号

    for u in range(len(V)):  # 初始化阶段：将每条无向边入堆一次
        for v in v_adj[u]:
            if u < v:  # 用 u<v 保证每条边只入堆一次
                push_edge(u, v)

    faces_target = max(target_faces, 0)  # 目标面数下界为 0
    faces_current = sum(1 for x in f_alive if x)  # 当前存活面的数量
    collapsed = 0  # 已执行的坍塌次数

    last_emit_collapses = 0  # 距离上次触发回调的坍塌增量
    start_t = time.time()  # 计时起点（用于时限控制）
    
    # 4) 主循环：持续从堆中弹出“代价最小的边”进行坍塌，直到达到目标面数/时间限制或候选边耗尽
    while faces_current > faces_target and heap:  # 只要需要继续减少面且仍有候选边
        if time_limit_seconds is not None and (time.time() - start_t) >= time_limit_seconds:  # 命中时间上限
            # Abort early due to time limit  # 提前结束，返回部分简化结果
            break
        cost, _, u, v, pos = heapq.heappop(heap)  # 弹出当前代价最小的候选边
        if (not v_alive[u]) or (not v_alive[v]):  # 端点若已被移除则跳过
            continue
        if v not in v_adj[u]:  # 不是当前邻接（可能被拓扑更新改变）则跳过
            continue
        # 4.1) 边坍塌 v -> u：将 v 合并到 u，且把 u 的位置设为 pos（最优或回退的中点）
        V[u] = [pos[0], pos[1], pos[2]]  # 更新 u 的位置为合并位置
        v_alive[v] = False  # 顶点 v 被移除
        v_adj[u].discard(v)  # 去掉 u-v 邻接
        v_adj[v].discard(u)  # 去掉 v-u 邻接

        # 4.2) 合并 Quadric：u <- u + v
        add_inplace(v_quads[u], v_quads[v])  # 合并 Quadric：Q[u]+=Q[v]

        # 4.3) 重连邻接：v 的所有邻居改连 u，保持图连通信息更新
        for w in list(v_adj[v]):  # 遍历 v 的邻居，将其改连到 u
            v_adj[w].discard(v)  # 去除 w-v
            if w != u:  # 避免自环
                v_adj[w].add(u)  # 增加 w-u
                v_adj[u].add(w)  # 增加 u-w
        v_adj[v].clear()  # 清空 v 的邻接

        # 4.4) 更新三角面：将面中的 v 替换成 u；若三顶点出现重复则该面退化，标记删除
        for fi, f in enumerate(F):  # 更新所有三角的顶点索引，把 v 替换为 u
            if not f_alive[fi]:  # 已无效的面跳过
                continue
            a, b, c = f
            if a == v:
                a = u
            if b == v:
                b = u
            if c == v:
                c = u
            if len({a, b, c}) < 3:  # 若出现重复顶点，面退化，标记删除
                f_alive[fi] = False
                faces_current -= 1  # 当前面数-1
                continue
            # Optional: prevent flips via area check (skip for simplicity)  # 可选：面积/法线检查（此处省略）
            F[fi] = [a, b, c]  # 写回更新后的三角

        # 4.5) 重新评估与 u 相邻的候选边（其代价随顶点位置与 Quadric 更新变化）
        for w in list(v_adj[u]):  # u 的邻居边重新入堆（代价已改变）
            push_edge(min(u, w), max(u, w))  # 规范顺序避免重复

        collapsed += 1  # 坍塌计数+1
        # 4.6) 按间隔调用进度回调，可用于打印 ETA、节流输出；回调返回 False 则中断当前网格
        if progress_cb is not None and collapsed - last_emit_collapses >= max(1, interval):  # 到达报告间隔
            last_emit_collapses = collapsed  # 记录本次坍塌数
            if not progress_cb(collapsed, faces_current, faces_target):  # 回调要求中断
                break  # 终止该网格

    # ========== 压缩与重建拓扑 ==========
    # 将“仍存活”的顶点顺序压紧，建立旧索引→新索引的映射；按映射重建三角面索引。
    index_map = {}  # 旧顶点索引 -> 新索引 的映射
    new_verts: list[tuple[float, float, float]] = []  # 压缩后的顶点数组
    for i, alive in enumerate(v_alive):  # 遍历所有顶点
        if alive:  # 仅保留仍存活的顶点
            index_map[i] = len(new_verts)  # 分配新索引
            new_verts.append((V[i][0], V[i][1], V[i][2]))  # 写入坐标
    new_faces: list[tuple[int, int, int]] = []  # 压缩后的三角面
    for fi, alive in enumerate(f_alive):  # 遍历所有面
        if not alive:  # 跳过已删除的
            continue
        a, b, c = F[fi]
        if a in index_map and b in index_map and c in index_map:  # 三个端点都仍然存活
            new_faces.append((index_map[a], index_map[b], index_map[c]))  # 写入重映射后的面

    return new_verts, new_faces  # 返回新的几何


def qem_simplify_ex(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    target_faces: int,
    face_uvs: Optional[list[tuple[float, float, float, float, float, float]]] = None,
    progress_cb: Optional[Callable[[int, int, int], bool]] = None,
    interval: int = 5000,
    time_limit_seconds: Optional[float] = None,
) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[int, int, int]],
    Optional[list[tuple[float, float, float, float, float, float]]],
]:
    """QEM 简化的增强版：在几何拓扑简化的同时，携带并过滤 face-varying UV（按面三元组）。

    说明：
    - face_uvs 为可选，长度应与输入 faces 一致；每个元素包含该三角的三个 (u,v)，展平成 6 个浮点数。
    - 本实现不在坍塌时修改 UV 值，仅在面退化/删除时同步丢弃对应 triplet，最后与存活面一同压缩输出。
    - 若未提供 face_uvs，则返回的第三项为 None。
    """
    # 将不可变的元组列表拷贝为可变列表，便于更新顶点坐标
    V = [list(v) for v in verts]  # V[i] = [x, y, z]
    # 拷贝三角面索引，后续会原位更新顶点索引（替换 v -> u）
    F = [list(f) for f in faces]  # F[fi] = [a, b, c]
    # 顶点/面存活标记：坍塌后，v 会被标记为不存活；退化三角会被标记为不存活
    v_alive = [True] * len(V)
    f_alive = [True] * len(F)
    # 为每个顶点准备一个 4x4 Quadric（拉直成 16 个浮点），用于误差评估
    v_quads = [mat4_zero() for _ in V]

    # 遍历每个三角面，计算其平面 Quadric，并累加到三个顶点
    for fi, f in enumerate(F):
        if not f_alive[fi]:  # 已经无效的面直接跳过（初始阶段一般不会命中）
            continue
        i, j, k = f  # 三角的三个顶点索引
        p = V[i]; q = V[j]; r = V[k]  # 对应三顶点的坐标
        n = cross(sub(q, p), sub(r, p))  # 未归一化法线 = (q-p) x (r-p)
        norm = length(n)  # 法线长度 ~ 面积的两倍
        if norm <= 1e-12:  # 面积近零，认为退化
            f_alive[fi] = False  # 标记该面无效
            continue
        n = [n[0]/norm, n[1]/norm, n[2]/norm]  # 归一化法线
        d = -dot(n, p)  # 平面常数项 d = -n·p
        K = plane_quadric(n[0], n[1], n[2], d)  # 构建该面的 Quadric 矩阵
        add_inplace(v_quads[i], K)  # 累加到三个顶点
        add_inplace(v_quads[j], K)
        add_inplace(v_quads[k], K)

    # 构建顶点邻接：每个顶点记录它相邻的顶点集合（无向图）
    v_adj: list[set[int]] = [set() for _ in V]
    for f in F:
        a, b, c = f
        v_adj[a].update((b, c))  # a 邻接 b、c
        v_adj[b].update((a, c))  # b 邻接 a、c
        v_adj[c].update((a, b))  # c 邻接 a、b

    # 最小堆存放候选边：(cost, eid, u, v, pos)
    heap: list[tuple[float, int, int, int, tuple[float, float, float]]] = []
    eid = 0  # 自增 id，避免堆中比较元组时同 cost 冲突

    def push_edge(u: int, v: int):
        nonlocal eid
        if u == v:  # 自环忽略
            return
        if v not in v_adj[u]:  # 已不相邻则忽略（拓扑变化后可能发生）
            return
        Quv = add(v_quads[u], v_quads[v])  # 合并端点的 Quadric
        pos, cost = optimal_position_cost(Quv, V[u], V[v])  # 计算最优合并位置与误差
        heapq.heappush(heap, (cost, eid, u, v, pos))  # 压入候选
        eid += 1  # 自增 id

    # 初始化：把每条无向边（u<v）入堆一次
    for u in range(len(V)):
        for v in v_adj[u]:
            if u < v:
                push_edge(u, v)

    # 目标面数取下界 0；faces_current 为当前存活面数
    faces_target = max(target_faces, 0)
    faces_current = sum(1 for x in f_alive if x)
    collapsed = 0  # 已坍塌次数
    last_emit_collapses = 0  # 上次进度回调时的坍塌计数
    start_t = time.time()  # 用于限时

    # 主循环：每次弹出代价最小的边进行坍塌，直到达标或无候选
    while faces_current > faces_target and heap:
        # 命中时间上限则提前退出，返回部分结果
        if time_limit_seconds is not None and (time.time() - start_t) >= time_limit_seconds:
            break
        cost, _, u, v, pos = heapq.heappop(heap)  # 取出当前最优候选边
        if (not v_alive[u]) or (not v_alive[v]):  # 任一端点已经被移除，跳过
            continue
        if v not in v_adj[u]:  # 不再相邻（期间拓扑变化），跳过
            continue
        # 执行坍塌：把 v 合并到 u，u 的位置更新为最优 pos
        V[u] = [pos[0], pos[1], pos[2]]  # 更新 u 的坐标
        v_alive[v] = False  # 顶点 v 被移除
        v_adj[u].discard(v)  # 移除 u-v 邻接
        v_adj[v].discard(u)  # 移除 v-u 邻接
        add_inplace(v_quads[u], v_quads[v])  # 合并 Quadric：Q[u]+=Q[v]
        # 把 v 的邻居改连 u（重建邻接）
        for w in list(v_adj[v]):
            v_adj[w].discard(v)
            if w != u:
                v_adj[w].add(u)
                v_adj[u].add(w)
        v_adj[v].clear()  # v 的邻接清空

        # 更新所有三角的顶点索引：出现重复顶点则该面退化并删除
        for fi, f in enumerate(F):
            if not f_alive[fi]:  # 已无效面跳过
                continue
            a, b, c = f
            if a == v:
                a = u
            if b == v:
                b = u
            if c == v:
                c = u
            if len({a, b, c}) < 3:  # 顶点重复 → 退化，删除该面
                f_alive[fi] = False
                faces_current -= 1
                continue
            F[fi] = [a, b, c]  # 写回更新后的三角

        # u 的相邻边误差已变化，重新入堆
        for w in list(v_adj[u]):
            push_edge(min(u, w), max(u, w))

        collapsed += 1  # 计数
        # 达到回调间隔则触发进度回调；若回调返回 False 则中断
        if progress_cb is not None and collapsed - last_emit_collapses >= max(1, interval):
            last_emit_collapses = collapsed
            if not progress_cb(collapsed, faces_current, faces_target):
                break

    # 压缩存活顶点：建立旧索引 -> 新索引映射，并构建新顶点数组
    index_map: dict[int, int] = {}
    new_verts: list[tuple[float, float, float]] = []
    for i, alive in enumerate(v_alive):
        if alive:
            index_map[i] = len(new_verts)  # 为旧索引 i 分配新索引
            new_verts.append((V[i][0], V[i][1], V[i][2]))  # 写入坐标
    # 根据存活面与索引映射，构建新的三角面列表
    new_faces: list[tuple[int, int, int]] = []
    # 若传入了 face_uvs，则准备一个输出列表与 new_faces 对齐
    new_face_uvs: Optional[list[tuple[float, float, float, float, float, float]]] = [] if face_uvs is not None else None
    for fi, alive in enumerate(f_alive):
        if not alive:
            continue  # 跳过被删除的面
        a, b, c = F[fi]
        if a in index_map and b in index_map and c in index_map:
            # 三个端点均存活：重映射到新索引
            new_faces.append((index_map[a], index_map[b], index_map[c]))
            if new_face_uvs is not None and face_uvs is not None:
                # 同步保留该面的 UV triplet（与面一一对应）
                new_face_uvs.append(face_uvs[fi])

    # 返回新顶点、新三角与（可选）新 UV triplets
    return new_verts, new_faces, new_face_uvs


# --- QEM 相关的 4x4 矩阵与线性代数小工具 ---

def mat4_zero():  # 生成一个 4x4 全零矩阵（按行主序一维列表存储）
    return [0.0] * 16


def add(A, B):  # 返回两个 4x4 矩阵（列表）的逐元素和
    return [A[i] + B[i] for i in range(16)]


def add_inplace(A, B):  # 将 B 原地加到 A 上（节省临时内存）
    for i in range(16):
        A[i] += B[i]


def plane_quadric(a: float, b: float, c: float, d: float):  # 由平面方程参数 p=[a,b,c,d] 构建 K=pp^T
    """由平面参数 [a,b,c,d] 构建 4x4 Quadric 矩阵（K = p p^T）。"""
    return [
        a * a, a * b, a * c, a * d,  # 第一行
        b * a, b * b, b * c, b * d,  # 第二行
        c * a, c * b, c * c, c * d,  # 第三行
        d * a, d * b, d * c, d * d,  # 第四行
    ]


def optimal_position_cost(Q: list[float], pu: list[float], pv: list[float]) -> tuple[tuple[float, float, float], float]:  # 计算最优合并位置与代价
    """求解最优合并位置与代价。

    目标：最小化 v'^T Q v'（v'=[x,y,z,1]）。
    做法：解 3x3 线性方程组 A x = b，其中 A=Q[0:3,0:3]，b=-Q[0:3,3]；
    若不可解（病态），则退化为端点中点以保证稳健。
    """
    A = [  # 取 Q 的左上 3x3 作为系数矩阵 A
        [Q[0], Q[1], Q[2]],
        [Q[4], Q[5], Q[6]],
        [Q[8], Q[9], Q[10]],
    ]
    b = [-Q[3], -Q[7], -Q[11]]  # 右侧项 b = -Q[0:3,3]
    x = solve3(A, b)  # 解 A x = b
    if x is None:  # 奇异或病态：退化为端点中点
        x = [(pu[0] + pv[0]) * 0.5, (pu[1] + pv[1]) * 0.5, (pu[2] + pv[2]) * 0.5]
    vx, vy, vz = x  # 拆解最优位置坐标
    v4 = [vx, vy, vz, 1.0]  # 齐次坐标形式
    cost = quadric_eval(Q, v4)  # 代价 = v'^T Q v'
    return (vx, vy, vz), float(cost)  # 返回位置与代价值


def quadric_eval(Q: list[float], v4: list[float]) -> float:  # 计算 v^T Q v（先算 Qv 再内积）
    # v^T Q v for 4x4 Q and 4-vector v  # 说明：按行主序展开计算，避免构造矩阵
    # Compute Qv first  # 先计算 Q 与 v 的乘积，得到 Qv
    Qv0 = Q[0]*v4[0] + Q[1]*v4[1] + Q[2]*v4[2] + Q[3]*v4[3]
    Qv1 = Q[4]*v4[0] + Q[5]*v4[1] + Q[6]*v4[2] + Q[7]*v4[3]
    Qv2 = Q[8]*v4[0] + Q[9]*v4[1] + Q[10]*v4[2] + Q[11]*v4[3]
    Qv3 = Q[12]*v4[0] + Q[13]*v4[1] + Q[14]*v4[2] + Q[15]*v4[3]
    return v4[0]*Qv0 + v4[1]*Qv1 + v4[2]*Qv2 + v4[3]*Qv3  # 再与 v 点乘得到标量


def solve3(A: list[list[float]], b: list[float]) -> list[float] | None:  # 解 3x3 线性方程组，失败返回 None
    """解 3x3 线性方程组（带部分选主元的高斯消元）。

    返回 None 表示矩阵病态/不可解（此时建议使用中点作为回退）。
    """
    M = [A[0][:] + [b[0]], A[1][:] + [b[1]], A[2][:] + [b[2]]]  # 扩展成增广矩阵 [A|b]
    n = 3  # 阶数
    # Forward elimination
    for i in range(n):  # 消元主循环
        # Pivot
        piv = i  # 初始主元行为 i
        piv_val = abs(M[i][i])  # 当前主元绝对值
        for r in range(i+1, n):  # 在下方行中找更大的主元（部分选主元）
            if abs(M[r][i]) > piv_val:
                piv, piv_val = r, abs(M[r][i])
        if piv_val < 1e-12:  # 主元过小视为奇异
            return None  # 放弃求解
        if piv != i:
            M[i], M[piv] = M[piv], M[i]  # 交换到当前行
        # Normalize row
        div = M[i][i]  # 主元值
        for c in range(i, n+1):  # 归一化该行，使主元=1
            M[i][c] /= div
        # Eliminate below
        for r in range(i+1, n):  # 对下面的行做消元
            factor = M[r][i]
            for c in range(i, n+1):
                M[r][c] -= factor * M[i][c]
    # Back substitution
    x = [0.0, 0.0, 0.0]  # 解向量
    for i in reversed(range(n)):  # 回代求解
        s = M[i][n]  # 右侧常数项
        for c in range(i+1, n):  # 减去已知部分
            s -= M[i][c] * x[c]
        x[i] = s  # 得到当前未知数
    return x  # 返回解


# --- geometry helpers ---

def sub(a: list[float], b: list[float]):  # 向量减法 a-b
    return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]


def dot(a: list[float], b: list[float]) -> float:  # 向量点积
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def cross(a: list[float], b: list[float]):  # 向量叉积
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def length(a: list[float]) -> float:  # 向量长度
    return math.sqrt(dot(a, a))


def _all_triangles(counts: Iterable[int]) -> bool:  # 判断是否全部为三角面（每面顶点数=3）
    try:
        return all(int(c) == 3 for c in counts)
    except Exception:
        return False  # 任何异常都视作“不是纯三角”


def _tri_faces_from_topology(counts: Iterable[int], indices: Iterable[int]) -> list[tuple[int, int, int]]:  # 将拓扑展开为三角面列表
    faces: list[tuple[int, int, int]] = []  # 结果列表
    it = iter(indices)  # 顺序迭代所有面顶点索引
    for c in counts:  # 遍历每个面的顶点个数
        c = int(c)
        if c != 3:  # 若出现非三角，直接报错（调用方已筛掉，这里是防御）
            raise ValueError("Non-triangle face encountered")
        a = int(next(it))  # 读取该面的三个顶点索引
        b = int(next(it))
        cidx = int(next(it))
        faces.append((a, b, cidx))  # 写入一个三角
    return faces  # 返回三角列表


def _write_mesh_triangles(mesh: Any, verts: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]):  # 将三角网格写回 USD 属性
    """将三角网格写回到 USD Mesh（点坐标 + 三角面拓扑）。"""
    # points
    mesh.GetPointsAttr().Set([(v[0], v[1], v[2]) for v in verts])  # 写回点坐标（Vec3f[]）
    # topology
    counts = [3] * len(faces)  # 每个面都是三角
    indices: list[int] = []  # 展平的顶点索引数组
    for a, b, c in faces:
        indices.extend([int(a), int(b), int(c)])  # 追加一个面的三个索引
    mesh.GetFaceVertexCountsAttr().Set(counts)  # 写回 FaceVertexCounts
    mesh.GetFaceVertexIndicesAttr().Set(indices)  # 写回 FaceVertexIndices


def _write_facevarying_uv(mesh: Any, face_uvs: list[tuple[float, float, float, float, float, float]], name: str = "st"):  # 写回 faceVarying UV primvar
    """写回 face-varying UV 数据。

    参数：
        mesh: UsdGeom.Mesh
        face_uvs: 每个三角的 (u0,v0,u1,v1,u2,v2) 列表
        name: primvar 名称（默认 'st'）
    行为：
        - 展平为 float2 数组并设置插值为 faceVarying。
        - 若 primvar 不存在则创建；存在则覆写。
    """
    if UsdGeom is None:
        return
    api = UsdGeom.PrimvarsAPI(mesh)
    pv = api.GetPrimvar(name)
    if not pv:
        # 创建新的 face-varying UV primvar (texCoord2f[])；role 'textureCoordinate'
        type_name = Sdf.ValueTypeNames.TexCoord2fArray if Sdf is not None else None
        if type_name is not None:
            pv = api.CreatePrimvar(name, type_name, UsdGeom.Tokens.faceVarying)
        else:
            # 回退：尝试直接创建 float2[] 类型（不一定可用）
            pv = api.CreatePrimvar(name, Sdf.ValueTypeNames.Float2Array if Sdf else None, UsdGeom.Tokens.faceVarying)  # type: ignore[arg-type]
        try:
            pv.SetRole(UsdGeom.Tokens.textureCoordinate)
        except Exception:
            pass
    # 展平
    flat: list[tuple[float, float]] = []
    for (u0, v0, u1, v1, u2, v2) in face_uvs:
        flat.append((u0, v0))
        flat.append((u1, v1))
        flat.append((u2, v2))
    pv.Set(flat)
    # 确保插值正确
    try:
        pv.SetInterpolation(UsdGeom.Tokens.faceVarying)
    except Exception:
        pass
