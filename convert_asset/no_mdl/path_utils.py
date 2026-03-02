# -*- coding: utf-8 -*-
import os
import time
from .config import SUFFIX, ALLOW_OVERWRITE


# _to_posix = None  # avoid lint complaining before function declared

def _to_posix(p: str) -> str:
    return p.replace("\\", "/") if isinstance(p, str) else p


def _relpath(from_dir: str, to_path: str) -> str:
    return _to_posix(os.path.relpath(to_path, start=from_dir))


def _resolve(layer_dir: str, asset_path: str) -> str | None:
    if not asset_path:
        return None
    ap = str(asset_path)
    if os.path.isabs(ap):
        return _to_posix(os.path.normpath(ap))
    return _to_posix(os.path.normpath(os.path.join(layer_dir, ap)))


def _sibling_noMDL_path(src_usd: str) -> str:
    d, b = os.path.split(src_usd)
    stem, ext = os.path.splitext(b)
    out = os.path.join(d, f"{stem}{SUFFIX}{ext or '.usd'}")
    if (not ALLOW_OVERWRITE) and os.path.exists(out):
        ts = time.strftime("%Y%m%d_%H%M%S")
        out = os.path.join(d, f"{stem}{SUFFIX}_{ts}{ext or '.usd'}")
    return _to_posix(out)


def _resolve_abs_path(anchor_dir: str | None, pth: str | None) -> str | None:
    if not pth:
        return None
    if os.path.isabs(pth):
        return _to_posix(os.path.normpath(pth))
    if not anchor_dir:
        return _to_posix(pth)
    return _to_posix(os.path.normpath(os.path.join(anchor_dir, pth)))


def _rebase_tex_path(
    src_path: str | None,
    src_anchor_dir: str | None,
    dst_layer_dir: str | None,
    resolve_to_absolute: bool = False,
) -> str | None:
    """纹理路径重算：根据策略决定写入 USD 的路径形式。

    - resolve_to_absolute=True：总是写绝对路径（旧行为）。
    - resolve_to_absolute=False（默认）：
        - 若源路径已是绝对 → 保持绝对路径。
        - 若源路径是相对 → 以 src_anchor_dir 解析为绝对，
          再转换为相对于 dst_layer_dir 的相对路径。
    - 若 dst_layer_dir 为 None 时无法转相对 → 退回绝对路径。

    参数：
    - src_path: 原始路径字符串（可为相对或绝对）。
    - src_anchor_dir: 原始路径的锚点目录（MDL 属性所在 layer 的目录）。
    - dst_layer_dir: 输出 *_noMDL.usd 文件所在目录。
    - resolve_to_absolute: True → 总是绝对化（向后兼容/强制模式）。

    返回：
    - 处理后的路径字符串（POSIX 风格）；None 表示输入无效。
    """
    if not src_path:
        return None
    is_abs = os.path.isabs(src_path)
    if resolve_to_absolute:
        # 旧行为：绝对化
        return _resolve_abs_path(src_anchor_dir, src_path)
    if is_abs:
        # 源路径已是绝对 → 保持绝对
        return _to_posix(os.path.normpath(src_path))
    # 源路径是相对 → 先解析为绝对，再转为相对于 dst
    abs_path = _resolve_abs_path(src_anchor_dir, src_path)
    if not abs_path:
        return _to_posix(src_path)  # 无法解析则原样返回
    if not os.path.isabs(abs_path):
        # anchor_dir 为 None 时 _resolve_abs_path 返回原相对路径；无法重算，原样返回
        return _to_posix(src_path)
    if not dst_layer_dir:
        return abs_path  # 无目标目录信息则退回绝对
    return _to_posix(os.path.relpath(abs_path, start=dst_layer_dir))
