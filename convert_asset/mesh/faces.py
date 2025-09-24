# -*- coding: utf-8 -*-
"""
统计 USD Mesh 的面数（面片数量）— Python 实现。

计数口径（与 CLI `mesh-faces` 一致）：
- 遍历 Stage 中所有活跃（Active）的 `UsdGeom.Mesh`；
- 跳过 Instance Proxy（避免对原型与实例双重计数）；
- 可选地按 `Imageable.purpose` 过滤：忽略 `proxy/guide`，仅统计 `default/render`；
- 面数 = `faceVertexCounts` 的条目数（不展开/打平，不验证是否三角）。

注意事项：
- USD 的遍历会访问实例视图（Instance Proxy）。为避免对同一原型/实例重复统计，我们显式跳过 `prim.IsInstanceProxy()`。
- 该实现不做“去重”或“合并原型”的复杂逻辑，只是严格按照遍历遇到的有效 Mesh（非 Proxy/Guide）累加其 `faceVertexCounts` 的长度。
- 需要在含有 `pxr` 的环境下运行（例如 Isaac Sim）。
"""
from __future__ import annotations

from typing import Optional  # 预留：未来如需口径参数（例如是否统计 proxy/guide），可扩展使用

try:
    from pxr import Usd, UsdGeom  # type: ignore
except Exception:  # pragma: no cover - allow type checkers without pxr
    Usd = None  # type: ignore[assignment]  # 兜底占位，便于类型检查
    UsdGeom = None  # type: ignore[assignment]


from typing import Any  # 允许传入 Stage 或 路径字符串


def count_mesh_faces(stage_or_path: str | Any) -> int:
    """统计 Stage 中有效 Mesh 的面片总数。

    合同（Contract）：
    - 输入：USD 路径或 `Usd.Stage` 实例；
    - 输出：`int`，为所有符合条件 Mesh 的 `len(faceVertexCounts)` 之和；
    - 忽略：Inactive、Instance Proxy、`purpose in {proxy, guide}`。

    边界情况：
    - 无法导入 `pxr`：抛出 RuntimeError（请在 USD 运行时环境中运行，如 Isaac Sim）。
    - 无法打开 Stage：抛出 RuntimeError（路径错误或无权限等）。
    """
    if Usd is None or UsdGeom is None:
        # 当前环境不可用 pxr（USD）库：提示需要在带 USD 的运行时执行
        raise RuntimeError("pxr.Usd not available in this environment; please run inside USD runtime (e.g., Isaac Sim)")

    # 路径或已有 Stage：若为路径，则尝试打开；打开失败时 Usd.Stage.Open 返回 None
    stage = stage_or_path if isinstance(stage_or_path, Usd.Stage) else Usd.Stage.Open(stage_or_path)  # type: ignore[name-defined]
    if stage is None:
        raise RuntimeError(f"Failed to open USD stage: {stage_or_path}")

    total = 0  # 面数累计
    for prim in stage.Traverse():  # 深度优先遍历组合层次；不打平、不过滤变体等
        if not prim.IsActive():
            continue
        if prim.IsInstanceProxy():
            # 避免对原型与实例的双重计数（Instance Proxy 是原型的实例视图）
            continue
        if prim.GetTypeName() != "Mesh":
            continue
        # purpose 过滤（可选）：proxy/guide 通常不参与渲染统计
        try:
            img = UsdGeom.Imageable(prim)
            purpose = img.ComputePurpose()
            if purpose in (UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide):
                continue
        except Exception:
            pass  # 某些 Prim 不支持 Imageable 或其他异常：忽略异常，继续统计
        mesh = UsdGeom.Mesh(prim)  # 以当前 Prim 构造 Mesh 句柄
        counts_attr = mesh.GetFaceVertexCountsAttr()  # 面顶点计数数组属性（IntArray）
        counts = counts_attr.Get()  # 读取当前时间码下的值（通常与时间无关；为 None 表示无拓扑）
        if counts is None:  # 若无面信息，跳过该 Mesh
            continue
        # 面数累加：面数 = faceVertexCounts 的条目数；不限定每面顶点数
        total += len(counts)
    return total


def _looks_like_tris(counts: list[int]) -> bool:
    # 预留辅助：判断是否“看起来像三角网格”（未在计数逻辑中使用）
    try:
        return all(int(c) == 3 for c in counts)
    except Exception:
        return False
