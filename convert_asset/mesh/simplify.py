# -*- coding: utf-8 -*-
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
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Callable, Optional
import math
import heapq
import time

try:
    from pxr import Usd, UsdGeom  # type: ignore
except Exception:  # pragma: no cover
    Usd = None  # type: ignore[assignment]
    UsdGeom = None  # type: ignore[assignment]


@dataclass
class SimplifyStats:
    meshes_total: int = 0
    meshes_tri: int = 0
    faces_before: int = 0
    faces_after: int = 0
    verts_before: int = 0
    verts_after: int = 0
    skipped_non_tri: int = 0
def list_mesh_face_counts(stage_or_path: str | Any) -> list[tuple[str, int]]:
    """列出 Stage 中所有“活跃的、渲染用途的三角网格”的面数统计。

    返回：`[(prim_path, face_count), ...]`
    - 仅包含：`Imageable.purpose in {default, render}` 的 `UsdGeom.Mesh`；
    - 跳过：Inactive、Instance Proxy、`purpose in {proxy, guide}`。
    - 面数即 `faceVertexCounts` 的条目数（不验证是否为三角）。
    """
    if Usd is None or UsdGeom is None:
        raise RuntimeError("pxr.Usd not available; run inside Isaac/pxr environment")
    stage = stage_or_path if isinstance(stage_or_path, Usd.Stage) else Usd.Stage.Open(stage_or_path)  # type: ignore[name-defined]
    if stage is None:
        raise RuntimeError(f"Failed to open stage: {stage_or_path}")
    out: list[tuple[str, int]] = []
    for prim in stage.Traverse():
        if not prim.IsActive() or prim.IsInstanceProxy():
            continue
        if prim.GetTypeName() != "Mesh":
            continue
        img = UsdGeom.Imageable(prim)
        try:
            purpose = img.ComputePurpose()
            if purpose in (UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide):
                continue
        except Exception:
            pass
        mesh = UsdGeom.Mesh(prim)
        counts = mesh.GetFaceVertexCountsAttr().Get()
        if not counts:
            continue
        out.append((prim.GetPath().pathString, len(counts)))
    return out



def simplify_stage_meshes(
    stage_or_path: str | Any,
    ratio: float = 0.5,
    max_collapses: int | None = None,
    out_path: str | None = None,
    apply: bool = False,
    show_progress: bool = False,
    progress_interval_collapses: int = 5000,
    time_limit_seconds: Optional[float] = None,
) -> SimplifyStats:
    if Usd is None or UsdGeom is None:
        raise RuntimeError("pxr.Usd not available; run inside Isaac/pxr environment")

    stage = stage_or_path if isinstance(stage_or_path, Usd.Stage) else Usd.Stage.Open(stage_or_path)  # type: ignore[name-defined]
    if stage is None:
        raise RuntimeError(f"Failed to open stage: {stage_or_path}")

    # 汇总统计对象与“待写回编辑”列表（apply=True 时批量写回）
    stats = SimplifyStats()
    mesh_edits: list[tuple[Any, list[tuple[float, float, float]], list[tuple[int, int, int]]]] = []

    for prim in stage.Traverse():
        if not prim.IsActive() or prim.IsInstanceProxy():
            continue
        if prim.GetTypeName() != "Mesh":
            continue
        img = UsdGeom.Imageable(prim)
        try:
            purpose = img.ComputePurpose()
            if purpose in (UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide):
                continue
        except Exception:
            pass

        stats.meshes_total += 1
        mesh = UsdGeom.Mesh(prim)
        counts = mesh.GetFaceVertexCountsAttr().Get()
        indices = mesh.GetFaceVertexIndicesAttr().Get()
        if not counts or not indices:
            continue
        if not _all_triangles(counts):
            stats.skipped_non_tri += 1
            continue
        stats.meshes_tri += 1
    # 仅统计路径（dry-run 快速）：不构建逐面的 faces 列表，直接估算目标面数
        faces_n = len(counts)
        pts = mesh.GetPointsAttr().Get() or []
        stats.faces_before += faces_n
        stats.verts_before += len(pts)

        target_faces = max(0, int(faces_n * max(0.0, min(1.0, ratio))))
        if max_collapses is not None:
            target_faces = max(target_faces, faces_n - int(max_collapses))

        if apply and faces_n > target_faces:
            # Build full structures only when applying
            verts = [(float(p[0]), float(p[1]), float(p[2])) for p in pts]
            faces = _tri_faces_from_topology(counts, indices)
            # Prepare progress reporter per-mesh
            reporter: Optional[Callable[[int, int, int], bool]] = None
            start_t = time.time()
            last_emit = 0.0
            if show_progress:
                mesh_path = prim.GetPath().pathString
                faces_before_local = faces_n
                def _report(collapsed: int, faces_current: int, faces_target: int) -> bool:
                    nonlocal last_emit
                    now = time.time()
                    # Always print the very first progress (collapsed==0), then throttle to ~1s
                    if collapsed == 0 or (now - last_emit) >= 1.0:
                        total_need = max(1, faces_before_local - faces_target)
                        done = max(0, faces_before_local - faces_current)
                        frac = max(0.0, min(1.0, done / float(total_need)))
                        eta = (now - start_t) * (1.0 - frac) / max(1e-6, frac) if frac > 0 else float('inf')
                        print(f"[PROGRESS] {mesh_path} {done}/{total_need} ({frac*100:.1f}%) collapsed={collapsed} ETA≈{eta:.1f}s")
                        last_emit = now
                    if time_limit_seconds is not None and (now - start_t) >= time_limit_seconds:
                        print(f"[TIMEOUT] aborting mesh {mesh_path} after {time_limit_seconds}s")
                        return False
                    return True
                reporter = _report
            # START line
            if show_progress:
                print(f"[START] {mesh_path} faces {faces_before_local} -> target {target_faces}")
                # initial progress emit
                if reporter:
                    reporter(0, faces_before_local, target_faces)
            # 核心简化调用：返回新的顶点与三角面列表
            verts2, faces2 = qem_simplify(
                verts,
                faces,
                target_faces,
                progress_cb=reporter,
                interval=progress_interval_collapses,
                time_limit_seconds=time_limit_seconds,
            )
            stats.faces_after += len(faces2)
            stats.verts_after += len(verts2)
            mesh_edits.append((prim, verts2, faces2))
        else:
            # dry-run：仅估算面数（保持顶点数不变，作为保守估计；实际坍塌后顶点数会下降）
            stats.faces_after += target_faces if faces_n > target_faces else faces_n
            stats.verts_after += len(pts)  # rough estimate; exact vertex count depends on collapses

    if apply and mesh_edits:
        # Apply edits and export
        for prim, verts2, faces2 in mesh_edits:
            _write_mesh_triangles(UsdGeom.Mesh(prim), verts2, faces2)
        if out_path:
            stage.Export(out_path)

    return stats


def qem_simplify(
    verts: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    target_faces: int,
    progress_cb: Optional[Callable[[int, int, int], bool]] = None,
    interval: int = 5000,
    time_limit_seconds: Optional[float] = None,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Simplify a triangle mesh to approximately target_faces using QEM.

    Pure Python reference implementation. Suitable for small meshes or capped collapses.
    """
    # ========== 构建简化所需的基础结构 ==========
    # 可变拷贝：V=顶点坐标，F=三角面索引；alive 标记分别表示顶点/面是否仍然“存活”。
    V = [list(v) for v in verts]
    F = [list(f) for f in faces]
    v_alive = [True] * len(V)
    f_alive = [True] * len(F)
    v_quads = [mat4_zero() for _ in V]

    # 1) 计算初始顶点 Quadric：对每个三角面，求面法线 n 与平面 d，形成 4x4 矩阵 K，并累加到三个顶点上。
    for fi, f in enumerate(F):
        if not f_alive[fi]:
            continue
        i, j, k = f
        p = V[i]
        q = V[j]
        r = V[k]
        n = cross(sub(q, p), sub(r, p))
        norm = length(n)
        if norm <= 1e-12:
            f_alive[fi] = False
            continue
        n = [n[0] / norm, n[1] / norm, n[2] / norm]
        d = -dot(n, p)
        K = plane_quadric(n[0], n[1], n[2], d)
        add_inplace(v_quads[i], K)
        add_inplace(v_quads[j], K)
        add_inplace(v_quads[k], K)

    # 2) 构建顶点邻接（无向图）：每个顶点记录与其相邻的顶点集合
    v_adj: list[set[int]] = [set() for _ in V]
    for f in F:
        a, b, c = f
        v_adj[a].update((b, c))
        v_adj[b].update((a, c))
        v_adj[c].update((a, b))

    # 3) 初始化边堆（最小堆）：元素为 (cost, eid, u, v, pos)
    #    - cost：合并误差；eid：入堆序号避免比较歧义；u,v：边两个顶点；pos：合并后位置
    heap: list[tuple[float, int, int, int, tuple[float, float, float]]] = []
    eid = 0
    def push_edge(u: int, v: int):
        nonlocal eid
        if u == v:
            return
        if v not in v_adj[u]:
            return
        Quv = add(v_quads[u], v_quads[v])
        pos, cost = optimal_position_cost(Quv, V[u], V[v])
        heapq.heappush(heap, (cost, eid, u, v, pos))
        eid += 1

    for u in range(len(V)):
        for v in v_adj[u]:
            if u < v:
                push_edge(u, v)

    faces_target = max(target_faces, 0)
    faces_current = sum(1 for x in f_alive if x)
    collapsed = 0

    last_emit_collapses = 0  # 距离上次进度回调的坍塌计数
    start_t = time.time()
    # 4) 主循环：持续从堆中弹出“代价最小的边”进行坍塌，直到达到目标面数/时间限制或候选边耗尽
    while faces_current > faces_target and heap:
        if time_limit_seconds is not None and (time.time() - start_t) >= time_limit_seconds:
            # Abort early due to time limit
            break
        cost, _, u, v, pos = heapq.heappop(heap)
        if (not v_alive[u]) or (not v_alive[v]):
            continue
        if v not in v_adj[u]:
            continue
        # 4.1) 边坍塌 v -> u：将 v 合并到 u，且把 u 的位置设为 pos（最优或回退的中点）
        V[u] = [pos[0], pos[1], pos[2]]
        v_alive[v] = False
        v_adj[u].discard(v)
        v_adj[v].discard(u)

    # 4.2) 合并 Quadric：u <- u + v
        add_inplace(v_quads[u], v_quads[v])

        # 4.3) 重连邻接：v 的所有邻居改连 u，保持图连通信息更新
        for w in list(v_adj[v]):
            v_adj[w].discard(v)
            if w != u:
                v_adj[w].add(u)
                v_adj[u].add(w)
        v_adj[v].clear()

        # 4.4) 更新三角面：将面中的 v 替换成 u；若三顶点出现重复则该面退化，标记删除
        for fi, f in enumerate(F):
            if not f_alive[fi]:
                continue
            a, b, c = f
            if a == v:
                a = u
            if b == v:
                b = u
            if c == v:
                c = u
            if len({a, b, c}) < 3:
                f_alive[fi] = False
                faces_current -= 1
                continue
            # Optional: prevent flips via area check (skip for simplicity)
            F[fi] = [a, b, c]

        # 4.5) 重新评估与 u 相邻的候选边（其代价随顶点位置与 Quadric 更新变化）
        for w in list(v_adj[u]):
            push_edge(min(u, w), max(u, w))

        collapsed += 1
        # 4.6) 按间隔调用进度回调，可用于打印 ETA、节流输出；回调返回 False 则中断当前网格
        if progress_cb is not None and collapsed - last_emit_collapses >= max(1, interval):
            last_emit_collapses = collapsed
            if not progress_cb(collapsed, faces_current, faces_target):
                break

    # ========== 压缩与重建拓扑 ==========
    # 将“仍存活”的顶点顺序压紧，建立旧索引→新索引的映射；按映射重建三角面索引。
    index_map = {}
    new_verts: list[tuple[float, float, float]] = []
    for i, alive in enumerate(v_alive):
        if alive:
            index_map[i] = len(new_verts)
            new_verts.append((V[i][0], V[i][1], V[i][2]))
    new_faces: list[tuple[int, int, int]] = []
    for fi, alive in enumerate(f_alive):
        if not alive:
            continue
        a, b, c = F[fi]
        if a in index_map and b in index_map and c in index_map:
            new_faces.append((index_map[a], index_map[b], index_map[c]))

    return new_verts, new_faces


# --- QEM 相关的 4x4 矩阵与线性代数小工具 ---

def mat4_zero():
    return [0.0] * 16


def add(A, B):
    return [A[i] + B[i] for i in range(16)]


def add_inplace(A, B):
    for i in range(16):
        A[i] += B[i]


def plane_quadric(a: float, b: float, c: float, d: float):
    """由平面参数 [a,b,c,d] 构建 4x4 Quadric 矩阵（K = p p^T）。"""
    return [
        a * a, a * b, a * c, a * d,
        b * a, b * b, b * c, b * d,
        c * a, c * b, c * c, c * d,
        d * a, d * b, d * c, d * d,
    ]


def optimal_position_cost(Q: list[float], pu: list[float], pv: list[float]) -> tuple[tuple[float, float, float], float]:
    """求解最优合并位置与代价。

    目标：最小化 v'^T Q v'（v'=[x,y,z,1]）。
    做法：解 3x3 线性方程组 A x = b，其中 A=Q[0:3,0:3]，b=-Q[0:3,3]；
    若不可解（病态），则退化为端点中点以保证稳健。
    """
    A = [
        [Q[0], Q[1], Q[2]],
        [Q[4], Q[5], Q[6]],
        [Q[8], Q[9], Q[10]],
    ]
    b = [-Q[3], -Q[7], -Q[11]]
    x = solve3(A, b)
    if x is None:
        x = [(pu[0] + pv[0]) * 0.5, (pu[1] + pv[1]) * 0.5, (pu[2] + pv[2]) * 0.5]
    vx, vy, vz = x
    v4 = [vx, vy, vz, 1.0]
    cost = quadric_eval(Q, v4)
    return (vx, vy, vz), float(cost)


def quadric_eval(Q: list[float], v4: list[float]) -> float:
    # v^T Q v for 4x4 Q and 4-vector v
    # Compute Qv first
    Qv0 = Q[0]*v4[0] + Q[1]*v4[1] + Q[2]*v4[2] + Q[3]*v4[3]
    Qv1 = Q[4]*v4[0] + Q[5]*v4[1] + Q[6]*v4[2] + Q[7]*v4[3]
    Qv2 = Q[8]*v4[0] + Q[9]*v4[1] + Q[10]*v4[2] + Q[11]*v4[3]
    Qv3 = Q[12]*v4[0] + Q[13]*v4[1] + Q[14]*v4[2] + Q[15]*v4[3]
    return v4[0]*Qv0 + v4[1]*Qv1 + v4[2]*Qv2 + v4[3]*Qv3


def solve3(A: list[list[float]], b: list[float]) -> list[float] | None:
    """解 3x3 线性方程组（带部分选主元的高斯消元）。

    返回 None 表示矩阵病态/不可解（此时建议使用中点作为回退）。
    """
    M = [A[0][:] + [b[0]], A[1][:] + [b[1]], A[2][:] + [b[2]]]
    n = 3
    # Forward elimination
    for i in range(n):
        # Pivot
        piv = i
        piv_val = abs(M[i][i])
        for r in range(i+1, n):
            if abs(M[r][i]) > piv_val:
                piv, piv_val = r, abs(M[r][i])
        if piv_val < 1e-12:
            return None
        if piv != i:
            M[i], M[piv] = M[piv], M[i]
        # Normalize row
        div = M[i][i]
        for c in range(i, n+1):
            M[i][c] /= div
        # Eliminate below
        for r in range(i+1, n):
            factor = M[r][i]
            for c in range(i, n+1):
                M[r][c] -= factor * M[i][c]
    # Back substitution
    x = [0.0, 0.0, 0.0]
    for i in reversed(range(n)):
        s = M[i][n]
        for c in range(i+1, n):
            s -= M[i][c] * x[c]
        x[i] = s
    return x


# --- geometry helpers ---

def sub(a: list[float], b: list[float]):
    return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]


def dot(a: list[float], b: list[float]) -> float:
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def cross(a: list[float], b: list[float]):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def length(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def _all_triangles(counts: Iterable[int]) -> bool:
    try:
        return all(int(c) == 3 for c in counts)
    except Exception:
        return False


def _tri_faces_from_topology(counts: Iterable[int], indices: Iterable[int]) -> list[tuple[int, int, int]]:
    faces: list[tuple[int, int, int]] = []
    it = iter(indices)
    for c in counts:
        c = int(c)
        if c != 3:
            raise ValueError("Non-triangle face encountered")
        a = int(next(it))
        b = int(next(it))
        cidx = int(next(it))
        faces.append((a, b, cidx))
    return faces


def _write_mesh_triangles(mesh: Any, verts: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]):
    """将三角网格写回到 USD Mesh（点坐标 + 三角面拓扑）。"""
    # points
    mesh.GetPointsAttr().Set([(v[0], v[1], v[2]) for v in verts])
    # topology
    counts = [3] * len(faces)
    indices: list[int] = []
    for a, b, c in faces:
        indices.extend([int(a), int(b), int(c)])
    mesh.GetFaceVertexCountsAttr().Set(counts)
    mesh.GetFaceVertexIndicesAttr().Set(indices)
