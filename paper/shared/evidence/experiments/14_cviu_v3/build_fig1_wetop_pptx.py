#!/usr/bin/env python3
"""Build editable 1:1 WET-OP-styled Figure 1 PPTX + PDF for ConvertAsset CVIU v3.

Design contract:
- Starts directly from WET-OP's Figure1_WET-OP_Bench_Overview.pptx template.
- Preserves exact native OOXML layout, gradients, drop shadows, line weights, and typography (<a:rPr>/<a:pPr>).
- Clears <a:srcRect> on all replaced photo slots so pre-framed high-DPI crops never clip.
- Keeps the 14 corner/gallery thumbnails 100% clean (zero contours, zero scatter markers),
  adds refined circular check/cross pins only to the 4 Audit Progression frames,
  and embeds studio RGBA cutouts of the Arched Desk Clock in Shader2Sim Assets.
- Replaces all 16 vector/SVG slots with aspect-matched, domain-authentic multi-layer SVGs + crisp PNG fallbacks.
- Renders a 3-cluster grouped nested bar chart (Home 20 | Commercial 10 | All Scenes 30) alongside the 4-quadrant Rose.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle, Wedge
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[4]
sys.path.insert(0, str(THIS_DIR))

V3_RAW_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_v3"
V1_META_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_formal/v1"
WETOP_ROOT = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\wetop_inspect\wet-op-cvpr2027-full-package"
)
WETOP_PPTX = WETOP_ROOT / "3_editable_figures_pptx/Figure1_WET-OP_Bench_Overview.pptx"
WETOP_HELPER = WETOP_ROOT / "4_scripts_and_data/update_fig1_pptx.py"
VLN_STILLS = REPO_ROOT / "paper/shared/figures/fig_internnav_rollout_stills.png"

OUT_PPTX = REPO_ROOT / "paper/venues/cviu/figures/Figure1_ConvertAsset_Overview.pptx"
OUT_PDF = REPO_ROOT / "paper/venues/cviu/figures/fig1_overview.pdf"
PREVIEW_PNG = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\fig_previews\fig1_overview.png"
)

EMU_PER_PT = 12700
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ASVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

ET.register_namespace("p", P_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("asvg", ASVG_NS)


def pt(val: float) -> str:
    return str(int(round(val * EMU_PER_PT)))


def _pct1(val_pct: float) -> str:
    q = Decimal(f"{val_pct:.6f}").quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{q}%"


def _pct2(val_pct: float, signed: bool = False) -> str:
    q = Decimal(f"{val_pct:.6f}").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if signed and q > 0:
        return f"+{q}%"
    if signed and q == 0:
        return "+0.00%"
    return f"{q}%"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _index_oc(path: Path) -> dict[tuple[str, str], dict]:
    return {
        (str(r["pair_id"]), str(r["condition"])): r
        for r in _read_jsonl(path)
        if r.get("status") == "ok"
    }


def _resolve_asset(rel_or_abs: str, assets_root: Path) -> Path:
    s = rel_or_abs.replace("\\", "/")
    marker = "/experiments/cviu/"
    if marker in s:
        return assets_root / s.split(marker, 1)[1]
    p = Path(rel_or_abs)
    return p if p.is_file() else assets_root / rel_or_abs


def _pure_scene_crop(
    im_rgb: np.ndarray,
    mask: np.ndarray,
    target_w_px: int,
    target_h_px: int,
    *,
    pad_frac: float = 1.60,
    shift_x_frac: float = 0.0,
) -> bytes:
    """Clean high-res LANCZOS crop centered on target mask without contours or markers."""
    H, W = im_rgb.shape[:2]
    ys, xs = np.where(mask)
    if len(xs) == 0:
        cx, cy, bw, bh = W * 0.5, H * 0.5, W * 0.5, H * 0.5
    else:
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        cx = 0.5 * (x0 + x1)
        cy = 0.5 * (y0 + y1)
        bw = max(x1 - x0, 150)
        bh = max(y1 - y0, 150)

    aspect = target_w_px / float(target_h_px)
    box_w = max(bw * pad_frac, bh * pad_frac * aspect, 300.0)
    box_h = box_w / aspect
    if box_h > H:
        box_h = float(H)
        box_w = box_h * aspect
    if box_w > W:
        box_w = float(W)
        box_h = box_w / aspect

    cx += shift_x_frac * box_w
    cx0 = int(round(min(max(cx - box_w * 0.5, 0.0), W - box_w)))
    cy0 = int(round(min(max(cy - box_h * 0.5, 0.0), H - box_h)))
    cx1 = min(W, cx0 + int(round(box_w)))
    cy1 = min(H, cy0 + int(round(box_h)))

    pil = Image.fromarray(im_rgb[cy0:cy1, cx0:cx1]).resize(
        (target_w_px, target_h_px), Image.Resampling.LANCZOS
    )
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return buf.getvalue()


def _audit_pin_crop(
    im_rgb: np.ndarray,
    mask: np.ndarray,
    target_w_px: int,
    target_h_px: int,
    *,
    point_norm: list[float] | None,
    hit: bool,
    pad_frac: float = 1.95,
) -> bytes:
    """High-res crop for top-right 4 audit progression slots with a crisp circular pin (no neon contours)."""
    H, W = im_rgb.shape[:2]
    ys, xs = np.where(mask)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    bw, bh = max(x1 - x0, 160), max(y1 - y0, 160)

    aspect = target_w_px / float(target_h_px)
    box_w = max(bw * pad_frac, bh * pad_frac * aspect, 400.0)
    box_h = box_w / aspect
    if box_h > H:
        box_h = float(H)
        box_w = box_h * aspect
    if box_w > W:
        box_w = float(W)
        box_h = box_w / aspect

    cx0 = int(round(min(max(cx - box_w * 0.5, 0.0), W - box_w)))
    cy0 = int(round(min(max(cy - box_h * 0.5, 0.0), H - box_h)))
    cx1 = min(W, cx0 + int(round(box_w)))
    cy1 = min(H, cy0 + int(round(box_h)))

    crop = Image.fromarray(im_rgb[cy0:cy1, cx0:cx1]).resize(
        (target_w_px, target_h_px), Image.Resampling.LANCZOS
    ).convert("RGBA")

    if point_norm is not None:
        sx = target_w_px / float(cx1 - cx0)
        sy = target_h_px / float(cy1 - cy0)
        px = (float(point_norm[0]) * W / 1000.0 - cx0) * sx
        py = (float(point_norm[1]) * H / 1000.0 - cy0) * sy
        px = min(max(px, 28.0), target_w_px - 28.0)
        py = min(max(py, 28.0), target_h_px - 28.0)

        overlay = Image.new("RGBA", (target_w_px, target_h_px), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        r = 18.0
        # Soft drop shadow
        d.ellipse([px - r - 2, py - r, px + r + 2, py + r + 4], fill=(15, 23, 42, 95))
        fill_col = (16, 185, 129, 255) if hit else (225, 29, 72, 255)
        d.ellipse([px - r, py - r, px + r, py + r], fill=fill_col, outline=(255, 255, 255, 255), width=4)
        if hit:
            d.line(
                [(px - 7.5, py + 0.5), (px - 2.0, py + 6.5), (px + 8.5, py - 6.0)],
                fill=(255, 255, 255, 255), width=4, joint="curve",
            )
        else:
            d.line([(px - 6.5, py - 6.5), (px + 6.5, py + 6.5)], fill=(255, 255, 255, 255), width=4)
            d.line([(px + 6.5, py - 6.5), (px - 6.5, py + 6.5)], fill=(255, 255, 255, 255), width=4)
        crop = Image.alpha_composite(crop, overlay)

    buf = io.BytesIO()
    crop.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def _crop_vln_rollout(target_w_px: int, target_h_px: int) -> bytes:
    """Crop clean KuJiaLe DualVLN hallway + floorplan trajectory panel without headers/footers."""
    im = Image.open(VLN_STILLS).convert("RGB")
    # In fig_internnav_rollout_stills.png (1106x1324), row 3 right half sits y=958..1185, x=562..1080
    sub = im.crop((675, 958, 1020, 1185))  # shows doorway corridor + full floorplan with red & green trajectories
    # Target ratio = 1.459 (matches 920x630 nicely with tiny center crop)
    w, h = sub.size
    desired_w = int(round(h * (target_w_px / float(target_h_px))))
    if desired_w <= w:
        dx = (w - desired_w) // 2
        sub = sub.crop((dx, 0, dx + desired_w, h))
    else:
        desired_h = int(round(w / (target_w_px / float(target_h_px))))
        dy = (h - desired_h) // 2
        sub = sub.crop((0, dy, w, dy + desired_h))
    out = sub.resize((target_w_px, target_h_px), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


def _cutout_rgba_asset(im_rgb: np.ndarray, mask: np.ndarray, out_w: int = 460, out_h: int = 432) -> bytes:
    """Extract target mask object onto clean transparent studio canvas with soft feathered edge & drop shadow."""
    ys, xs = np.where(mask)
    y0, y1 = max(0, int(ys.min()) - 6), min(im_rgb.shape[0], int(ys.max()) + 6)
    x0, x1 = max(0, int(xs.min()) - 6), min(im_rgb.shape[1], int(xs.max()) + 6)
    crop_rgb = im_rgb[y0:y1, x0:x1]
    crop_m = (mask[y0:y1, x0:x1].astype(np.uint8) * 255)
    m_img = Image.fromarray(crop_m).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.4))

    rgba = Image.fromarray(crop_rgb).convert("RGBA")
    rgba.putalpha(m_img)

    # Fit inside (out_w - 40) x (out_h - 46) centered slightly above bottom shadow
    cw, ch = rgba.size
    scale = min((out_w - 36) / cw, (out_h - 48) / ch)
    nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
    rgba = rgba.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    # Soft studio contact shadow underneath
    sh = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    oy = (out_h - nh) // 2 - 4
    ox = (out_w - nw) // 2
    sd.ellipse([ox + nw * 0.14, oy + nh - 14, ox + nw * 0.86, oy + nh + 12], fill=(15, 23, 42, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(8.0))
    canvas = Image.alpha_composite(canvas, sh)
    canvas.paste(rgba, (ox, oy), rgba)
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


def _craft_svgs_and_pngs() -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Create all 16 aspect-matched multi-layer vector SVGs and crisp RGBA PNG fallbacks."""
    def _svg(w: float, h: float, body: str) -> bytes:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" '
            f'viewBox="0 0 {w:g} {h:g}" fill="none" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
        ).encode("utf-8")

    svgs: dict[str, bytes] = {}
    pngs: dict[str, bytes] = {}

    def _new_fig(w_px: int, h_px: int, xlim: float, ylim: float):
        dpi = 100.0
        fig = plt.figure(figsize=(w_px / dpi, h_px / dpi), dpi=dpi, facecolor="none")
        ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], facecolor="none")
        ax.set_xlim(0, xlim)
        ax.set_ylim(ylim, 0)
        ax.axis("off")
        return fig, ax

    def _finish_fig(fig: plt.Figure) -> bytes:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, transparent=True)
        plt.close(fig)
        return buf.getvalue()

    # 1. Center Hub Emblem: White split 3D Shader Sphere (no text), viewBox 96x96 -> 72x72 pt
    svgs["ppt/media/ca_hub_sphere.svg"] = _svg(
        96, 96,
        '<defs>'
        '<clipPath id="leftHalf"><rect x="0" y="0" width="48" height="96"/></clipPath>'
        '<clipPath id="rightHalf"><rect x="48" y="0" width="48" height="96"/></clipPath>'
        '</defs>'
        '<circle cx="48" cy="48" r="35" fill="#FFFFFF" fill-opacity="0.14" stroke="#FFFFFF" stroke-width="4.4"/>'
        '<line x1="48" y1="13" x2="48" y2="83" stroke="#FFFFFF" stroke-width="3.2"/>'
        # Right hemisphere: isometric UV wireframe arcs (preview mesh/roughness)
        '<g clip-path="url(#rightHalf)" stroke="#CCFBF1" stroke-width="2.4">'
        '<ellipse cx="48" cy="48" rx="18" ry="35"/>'
        '<path d="M48,30 Q68,30 80,36"/>'
        '<path d="M48,48 Q70,48 83,48"/>'
        '<path d="M48,66 Q68,66 80,60"/>'
        '</g>'
        # Left hemisphere: glossy specular crescent + incident/reflected beam + glint star
        '<g clip-path="url(#leftHalf)">'
        '<path d="M48,13 A35,35 0 0,0 48,83 Z" fill="#FFFFFF" fill-opacity="0.22"/>'
        '<path d="M23,36 A26,26 0 0,1 40,20" stroke="#FFFFFF" stroke-width="4.2"/>'
        '</g>'
        '<polygon points="32,33 34.4,39.6 41,42 34.4,44.4 32,51 29.6,44.4 23,42 29.6,39.6" fill="#FFFFFF"/>'
    )
    fig, ax = _new_fig(288, 288, 96, 96)
    ax.add_patch(Circle((48, 48), 35, facecolor=(1, 1, 1, 0.14), edgecolor="white", lw=4.4))
    ax.plot([48, 48], [13, 83], color="white", lw=3.2)
    ax.add_patch(Wedge((48, 48), 35, 90, 270, facecolor=(1, 1, 1, 0.22), edgecolor="none"))
    ax.add_patch(Arc((48, 48), 36, 70, angle=0, theta1=270, theta2=90, color="#CCFBF1", lw=2.4))
    for yy in (31, 48, 65):
        ax.plot([48, 80 if yy != 48 else 83], [yy, yy + (4 if yy == 31 else -4 if yy == 65 else 0)], color="#CCFBF1", lw=2.3)
    ax.add_patch(Arc((48, 48), 52, 52, angle=0, theta1=115, theta2=168, color="white", lw=4.2))
    ax.add_patch(Polygon([(32, 33), (34.4, 39.6), (41, 42), (34.4, 44.4), (32, 51), (29.6, 44.4), (23, 42), (29.6, 39.6)], facecolor="white"))
    pngs["ppt/media/ca_hub_sphere.png"] = _finish_fig(fig)

    # 2. Top 4 Card Header Icons (32x32 viewBox -> 26x26 pt)
    # 2a. RM: Glossy Specular Sphere (#28609F + #DCE8F8)
    svgs["ppt/media/ca_icon_rm.svg"] = _svg(
        32, 32,
        '<circle cx="15" cy="17" r="10.5" fill="#DCE8F8" stroke="#28609F" stroke-width="2.1"/>'
        '<path d="M9.5,14.5 A6.8,6.8 0 0,1 16,10" stroke="#FFFFFF" stroke-width="2.4"/>'
        '<path d="M12,24 A9,9 0 0,0 24,18" stroke="#28609F" stroke-width="1.3" stroke-opacity="0.45"/>'
        '<polygon points="24,4 25.4,7.6 29,9 25.4,10.4 24,14 22.6,10.4 19,9 22.6,7.6" fill="#28609F"/>'
    )
    fig, ax = _new_fig(128, 128, 32, 32)
    ax.add_patch(Circle((15, 17), 10.5, facecolor="#DCE8F8", edgecolor="#28609F", lw=2.3))
    ax.add_patch(Arc((15, 17), 13.5, 13.5, theta1=130, theta2=195, color="white", lw=2.6))
    ax.add_patch(Polygon([(24, 4), (25.4, 7.6), (29, 9), (25.4, 10.4), (24, 14), (22.6, 10.4), (19, 9), (22.6, 7.6)], facecolor="#28609F"))
    pngs["ppt/media/ca_icon_rm.png"] = _finish_fig(fig)

    # 2b. TG: Glass Prism + Refracted Beams (#10756D + #D5F2EE)
    svgs["ppt/media/ca_icon_tg.svg"] = _svg(
        32, 32,
        '<polygon points="16,5 26.5,24.5 5.5,24.5" fill="#D5F2EE" stroke="#10756D" stroke-width="2.1"/>'
        '<line x1="2" y1="17" x2="10.5" y2="15" stroke="#10756D" stroke-width="1.9"/>'
        '<line x1="10.5" y1="15" x2="21.5" y2="17" stroke="#0F8B8D" stroke-width="1.8"/>'
        '<line x1="21.5" y1="17" x2="30" y2="13.5" stroke="#10756D" stroke-width="1.8"/>'
        '<line x1="21.5" y1="17" x2="30" y2="21" stroke="#10756D" stroke-width="1.8"/>'
    )
    fig, ax = _new_fig(128, 128, 32, 32)
    ax.add_patch(Polygon([(16, 5), (26.5, 24.5), (5.5, 24.5)], facecolor="#D5F2EE", edgecolor="#10756D", lw=2.3))
    ax.plot([2, 10.5, 21.5, 30], [17, 15, 17, 13.5], color="#10756D", lw=2.0)
    ax.plot([21.5, 30], [17, 21], color="#10756D", lw=2.0)
    pngs["ppt/media/ca_icon_tg.png"] = _finish_fig(fig)

    # 2c. MD: Micro-facet Rough Surface + Diffuse Scatter Rays (#B1691B + #F7E8D4)
    svgs["ppt/media/ca_icon_md.svg"] = _svg(
        32, 32,
        '<polygon points="4,22 8.5,17.5 12.5,21.5 16.5,17 20.5,21.5 24.5,17.5 28,22 28,26.5 4,26.5" fill="#F7E8D4" stroke="#B1691B" stroke-width="2.0"/>'
        '<path d="M16,16 V6 M16,6 L13.5,9 M16,6 L18.5,9" stroke="#B1691B" stroke-width="1.9"/>'
        '<path d="M10.5,16 L6,8.5 M6,8.5 L9,9 M6,8.5 L5.8,11.5" stroke="#B1691B" stroke-width="1.7"/>'
        '<path d="M21.5,16 L26,8.5 M26,8.5 L23,9 M26,8.5 L26.2,11.5" stroke="#B1691B" stroke-width="1.7"/>'
    )
    fig, ax = _new_fig(128, 128, 32, 32)
    ax.add_patch(Polygon([(4, 22), (8.5, 17.5), (12.5, 21.5), (16.5, 17), (20.5, 21.5), (24.5, 17.5), (28, 22), (28, 26.5), (4, 26.5)], facecolor="#F7E8D4", edgecolor="#B1691B", lw=2.1))
    for (x0, y0, x1, y1) in [(16, 16, 16, 6), (10.5, 16, 6, 8.5), (21.5, 16, 26, 8.5)]:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=2.0, color="#B1691B"))
    pngs["ppt/media/ca_icon_md.png"] = _finish_fig(fig)

    # 2d. ES: Emissive Screen + Radiance Waves (#9E3065 + #F9DFEC)
    svgs["ppt/media/ca_icon_es.svg"] = _svg(
        32, 32,
        '<rect x="5" y="7" width="22" height="15" rx="3" fill="#F9DFEC" stroke="#9E3065" stroke-width="2.1"/>'
        '<path d="M12,18 A4,4 0 0,1 20,18" stroke="#9E3065" stroke-width="1.8"/>'
        '<path d="M9.5,16.5 A7,7 0 0,1 22.5,16.5" stroke="#9E3065" stroke-width="1.6"/>'
        '<circle cx="16" cy="18" r="1.5" fill="#9E3065"/>'
        '<line x1="16" y1="22" x2="16" y2="26.5" stroke="#9E3065" stroke-width="2.1"/>'
        '<line x1="11" y1="26.5" x2="21" y2="26.5" stroke="#9E3065" stroke-width="2.1"/>'
    )
    fig, ax = _new_fig(128, 128, 32, 32)
    ax.add_patch(FancyBboxPatch((5, 7), 22, 15, boxstyle="round,pad=0,rounding_size=3", facecolor="#F9DFEC", edgecolor="#9E3065", lw=2.3))
    ax.add_patch(Circle((16, 18), 1.6, facecolor="#9E3065"))
    ax.add_patch(Arc((16, 18), 8, 8, theta1=15, theta2=165, color="#9E3065", lw=1.9))
    ax.add_patch(Arc((16, 18), 14, 14, theta1=15, theta2=165, color="#9E3065", lw=1.7))
    ax.plot([16, 16], [22, 26.5], color="#9E3065", lw=2.3)
    ax.plot([11, 21], [26.5, 26.5], color="#9E3065", lw=2.3)
    pngs["ppt/media/ca_icon_es.png"] = _finish_fig(fig)

    # 3. Wheel Top-Left: 6 VLM Models (id=366, 102.6x67.5 -> viewBox 308x202 -> PNG image19.png 616x404)
    svgs["ppt/media/ca_vlm_models.svg"] = _svg(
        308, 202,
        # Patch grid card
        '<rect x="8" y="34" width="66" height="106" rx="8" fill="#E8F0FA" stroke="#255994" stroke-width="4.2"/>'
        '<rect x="17" y="45" width="48" height="48" rx="4" fill="#FFFFFF" stroke="#255994" stroke-width="2.6"/>'
        '<line x1="33" y1="45" x2="33" y2="93" stroke="#93C5FD" stroke-width="2.2"/>'
        '<line x1="49" y1="45" x2="49" y2="93" stroke="#93C5FD" stroke-width="2.2"/>'
        '<line x1="17" y1="61" x2="65" y2="61" stroke="#93C5FD" stroke-width="2.2"/>'
        '<line x1="17" y1="77" x2="65" y2="77" stroke="#93C5FD" stroke-width="2.2"/>'
        '<circle cx="49" cy="61" r="6" fill="#0F8B8D"/>'
        '<rect x="19" y="106" width="44" height="22" rx="5" fill="#C7DBF4" stroke="#255994" stroke-width="2.4"/>'
        '<path d="M77,88 H101 M95,81 L103,88 L95,95" stroke="#255994" stroke-width="4.0"/>'
        # Center VLM stack card (3 scales / 4 family dots)
        '<rect x="106" y="20" width="96" height="136" rx="10" fill="#F1F6FC" stroke="#255994" stroke-width="4.2"/>'
        '<rect x="118" y="34" width="72" height="24" rx="5" fill="#DBEAFE" stroke="#255994" stroke-width="2.8"/>'
        '<rect x="118" y="68" width="72" height="24" rx="5" fill="#BAE6FD" stroke="#1F86B5" stroke-width="2.8"/>'
        '<rect x="118" y="102" width="72" height="24" rx="5" fill="#99F6E4" stroke="#0F8B8D" stroke-width="2.8"/>'
        '<circle cx="128" cy="141" r="6.5" fill="#12947F"/>'
        '<circle cx="145" cy="141" r="6.5" fill="#1D63DC"/>'
        '<circle cx="162" cy="141" r="6.5" fill="#DC2646"/>'
        '<circle cx="179" cy="141" r="6.5" fill="#D97706"/>'
        '<path d="M205,88 H229 M223,81 L231,88 L223,95" stroke="#255994" stroke-width="4.0"/>'
        # Right (x,y) Reticle Output
        '<rect x="234" y="42" width="66" height="92" rx="8" fill="#E8F0FA" stroke="#255994" stroke-width="4.2"/>'
        '<circle cx="267" cy="88" r="20" fill="#FFFFFF" stroke="#0F8B8D" stroke-width="3.6"/>'
        '<line x1="267" y1="62" x2="267" y2="114" stroke="#0F8B8D" stroke-width="2.6"/>'
        '<line x1="241" y1="88" x2="293" y2="88" stroke="#0F8B8D" stroke-width="2.6"/>'
        '<circle cx="267" cy="88" r="6.5" fill="#DC2646"/>'
    )
    fig, ax = _new_fig(616, 404, 308, 202)
    ax.add_patch(FancyBboxPatch((8, 34), 66, 106, boxstyle="round,pad=0,rounding_size=8", facecolor="#E8F0FA", edgecolor="#255994", lw=4.2))
    ax.add_patch(FancyBboxPatch((17, 45), 48, 48, boxstyle="round,pad=0,rounding_size=4", facecolor="white", edgecolor="#255994", lw=2.6))
    for g in (33, 49):
        ax.plot([g, g], [45, 93], color="#93C5FD", lw=2.2)
    for g in (61, 77):
        ax.plot([17, 65], [g, g], color="#93C5FD", lw=2.2)
    ax.add_patch(Circle((49, 61), 6, facecolor="#0F8B8D"))
    ax.add_patch(FancyBboxPatch((19, 106), 44, 22, boxstyle="round,pad=0,rounding_size=5", facecolor="#C7DBF4", edgecolor="#255994", lw=2.4))
    ax.annotate("", xy=(104, 88), xytext=(76, 88), arrowprops=dict(arrowstyle="-|>", lw=3.8, color="#255994"))
    ax.add_patch(FancyBboxPatch((106, 20), 96, 136, boxstyle="round,pad=0,rounding_size=10", facecolor="#F1F6FC", edgecolor="#255994", lw=4.2))
    for yy, fc, ec in [(34, "#DBEAFE", "#255994"), (68, "#BAE6FD", "#1F86B5"), (102, "#99F6E4", "#0F8B8D")]:
        ax.add_patch(FancyBboxPatch((118, yy), 72, 24, boxstyle="round,pad=0,rounding_size=5", facecolor=fc, edgecolor=ec, lw=2.8))
    for cx_d, col in [(128, "#12947F"), (145, "#1D63DC"), (162, "#DC2646"), (179, "#D97706")]:
        ax.add_patch(Circle((cx_d, 141), 6.5, facecolor=col))
    ax.annotate("", xy=(232, 88), xytext=(204, 88), arrowprops=dict(arrowstyle="-|>", lw=3.8, color="#255994"))
    ax.add_patch(FancyBboxPatch((234, 42), 66, 92, boxstyle="round,pad=0,rounding_size=8", facecolor="#E8F0FA", edgecolor="#255994", lw=4.2))
    ax.add_patch(Circle((267, 88), 20, facecolor="white", edgecolor="#0F8B8D", lw=3.6))
    ax.plot([267, 267], [62, 114], color="#0F8B8D", lw=2.6)
    ax.plot([241, 293], [88, 88], color="#0F8B8D", lw=2.6)
    ax.add_patch(Circle((267, 88), 6.5, facecolor="#DC2646"))
    pngs["ppt/media/image19.png"] = _finish_fig(fig)

    # 4. Wheel Top-Sky & Top-Right: SimReady Scenes & Natural Pairs (image23.svg viewBox 147x100, image25.svg viewBox 117x100)
    svgs["ppt/media/image23.svg"] = _svg(
        147, 100,
        # Isometric 3D cutaway indoor room + camera frustum
        '<polygon points="73,8 134,36 73,64 12,36" fill="#E1EBF2" stroke="#196E94" stroke-width="2.6"/>'
        '<polygon points="12,36 73,64 73,92 12,64" fill="#CED5DB" stroke="#196E94" stroke-width="2.6"/>'
        '<polygon points="73,64 134,36 134,64 73,92" fill="#D8E6F2" stroke="#196E94" stroke-width="2.6"/>'
        '<polygon points="73,30 104,44 73,58 42,44" fill="#FFFFFF" stroke="#196E94" stroke-width="2.2"/>'
        '<polygon points="73,58 104,44 104,54 73,68" fill="#A5D8EB" stroke="#196E94" stroke-width="2.2"/>'
        '<line x1="25" y1="22" x2="70" y2="43" stroke="#0F8B8D" stroke-width="2.4" stroke-dasharray="4,3"/>'
        '<circle cx="23" cy="21" r="5" fill="#0F8B8D"/>'
    )
    fig, ax = _new_fig(294, 200, 147, 100)
    ax.add_patch(Polygon([(73, 8), (134, 36), (73, 64), (12, 36)], facecolor="#E1EBF2", edgecolor="#196E94", lw=2.6))
    ax.add_patch(Polygon([(12, 36), (73, 64), (73, 92), (12, 64)], facecolor="#CED5DB", edgecolor="#196E94", lw=2.6))
    ax.add_patch(Polygon([(73, 64), (134, 36), (134, 64), (73, 92)], facecolor="#D8E6F2", edgecolor="#196E94", lw=2.6))
    ax.add_patch(Polygon([(73, 30), (104, 44), (73, 58), (42, 44)], facecolor="white", edgecolor="#196E94", lw=2.2))
    ax.add_patch(Circle((23, 21), 5, facecolor="#0F8B8D"))
    pngs["ppt/media/image22.png"] = _finish_fig(fig)

    svgs["ppt/media/image25.svg"] = _svg(
        117, 100,
        # Paired MDL -> Preview Shader Node cards
        '<rect x="6" y="14" width="44" height="58" rx="6" fill="#D8E6F2" stroke="#196E94" stroke-width="2.5"/>'
        '<circle cx="28" cy="36" r="12" fill="#FFFFFF" stroke="#196E94" stroke-width="2.2"/>'
        '<path d="M23,31 A6,6 0 0,1 30,27" stroke="#196E94" stroke-width="2.0"/>'
        '<rect x="14" y="55" width="28" height="8" rx="3" fill="#93C5FD"/>'
        '<path d="M53,43 H64 M60,38 L65,43 L60,48" stroke="#0F6D66" stroke-width="2.6"/>'
        '<rect x="67" y="28" width="44" height="58" rx="6" fill="#CBEAE6" stroke="#0F6D66" stroke-width="2.5"/>'
        '<circle cx="89" cy="50" r="12" fill="#FFFFFF" stroke="#0F6D66" stroke-width="2.2"/>'
        '<line x1="80" y1="50" x2="98" y2="50" stroke="#0F6D66" stroke-width="1.8"/>'
        '<rect x="75" y="69" width="28" height="8" rx="3" fill="#5EEAD4"/>'
    )
    fig, ax = _new_fig(234, 200, 117, 100)
    ax.add_patch(FancyBboxPatch((6, 14), 44, 58, boxstyle="round,pad=0,rounding_size=6", facecolor="#D8E6F2", edgecolor="#196E94", lw=2.5))
    ax.add_patch(Circle((28, 36), 12, facecolor="white", edgecolor="#196E94", lw=2.2))
    ax.add_patch(FancyBboxPatch((67, 28), 44, 58, boxstyle="round,pad=0,rounding_size=6", facecolor="#CBEAE6", edgecolor="#0F6D66", lw=2.5))
    ax.add_patch(Circle((89, 50), 12, facecolor="white", edgecolor="#0F6D66", lw=2.2))
    pngs["ppt/media/image24.png"] = _finish_fig(fig)

    # 5. Wheel Highlights Sector (Green #337435 + #82B684 / #C7E6DA / #D8E8D9 / #F1F7FA / #D98D75)
    # 5a. id=218 image43.svg (116x58 aspect ~1.998): Glossy MDL sphere -> Flattened Preview sphere
    svgs["ppt/media/image43.svg"] = _svg(
        116, 58,
        '<circle cx="26" cy="29" r="20" fill="#82B684" stroke="#337435" stroke-width="2.4"/>'
        '<path d="M16,22 A12,12 0 0,1 28,14" stroke="#FFFFFF" stroke-width="3.0"/>'
        '<polygon points="34,13 35.6,17.4 40,19 35.6,20.6 34,25 32.4,20.6 28,19 32.4,17.4" fill="#FFFFFF"/>'
        '<path d="M51,29 H65 M60,23 L66,29 L60,35" stroke="#3E8E41" stroke-width="2.8"/>'
        '<circle cx="90" cy="29" r="20" fill="#D8E8D9" stroke="#337435" stroke-width="2.4"/>'
        '<line x1="72" y1="29" x2="108" y2="29" stroke="#337435" stroke-width="1.6" stroke-dasharray="3,2"/>'
        '<line x1="90" y1="11" x2="90" y2="47" stroke="#337435" stroke-width="1.6" stroke-dasharray="3,2"/>'
    )
    fig, ax = _new_fig(232, 116, 116, 58)
    ax.add_patch(Circle((26, 29), 20, facecolor="#82B684", edgecolor="#337435", lw=2.4))
    ax.add_patch(Arc((26, 29), 24, 24, theta1=125, theta2=190, color="white", lw=3.0))
    ax.annotate("", xy=(67, 29), xytext=(50, 29), arrowprops=dict(arrowstyle="-|>", lw=2.8, color="#3E8E41"))
    ax.add_patch(Circle((90, 29), 20, facecolor="#D8E8D9", edgecolor="#337435", lw=2.4))
    pngs["ppt/media/image42.png"] = _finish_fig(fig)

    # 5b. id=603 image27.svg (96x60 aspect ~1.593): Noise-floor meter inside WET-OP screen frame (padded cleanly above label)
    svgs["ppt/media/image27.svg"] = _svg(
        96, 60,
        '<rect x="8" y="3" width="80" height="44" rx="5" fill="#F1F7FA" stroke="#337435" stroke-width="2.4"/>'
        '<rect x="15" y="9" width="66" height="32" rx="3" fill="#C8DCE5" stroke="#337435" stroke-width="1.8"/>'
        '<line x1="18" y1="25" x2="78" y2="25" stroke="#337435" stroke-width="1.6" stroke-dasharray="4,3"/>'
        '<rect x="23" y="34" width="12" height="4" rx="1" fill="#337435"/>'
        '<rect x="42" y="26" width="12" height="12" rx="1.5" fill="#82B684" stroke="#337435" stroke-width="1.3"/>'
        '<rect x="61" y="13" width="12" height="25" rx="1.5" fill="#D98D75" stroke="#337435" stroke-width="1.3"/>'
    )
    fig, ax = _new_fig(192, 120, 96, 60)
    ax.add_patch(FancyBboxPatch((8, 3), 80, 44, boxstyle="round,pad=0,rounding_size=5", facecolor="#F1F7FA", edgecolor="#337435", lw=2.4))
    ax.add_patch(FancyBboxPatch((15, 9), 66, 32, boxstyle="round,pad=0,rounding_size=3", facecolor="#C8DCE5", edgecolor="#337435", lw=1.8))
    ax.plot([18, 78], [25, 25], color="#337435", lw=1.6, ls="--")
    ax.add_patch(Rectangle((23, 34), 12, 4, facecolor="#337435"))
    ax.add_patch(Rectangle((42, 26), 12, 12, facecolor="#82B684", edgecolor="#337435", lw=1.3))
    ax.add_patch(Rectangle((61, 13), 12, 25, facecolor="#D98D75", edgecolor="#337435", lw=1.3))
    pngs["ppt/media/image26.png"] = _finish_fig(fig)

    # 5c. id=185 image41.svg (110x60 aspect ~1.818): Foreground/background counterfactual mask swap
    svgs["ppt/media/image41.svg"] = _svg(
        110, 60,
        '<rect x="5" y="7" width="46" height="46" rx="5" fill="#D8E8D9" stroke="#337435" stroke-width="2.3"/>'
        '<polygon points="15,44 21,18 39,16 42,40 27,46" fill="#F1F7FA" stroke="#337435" stroke-width="1.9" stroke-dasharray="3.5,2.5"/>'
        '<path d="M56,24 H68 M64,20 L69,24 L64,28 M68,36 H56 M60,32 L55,36 L60,40" stroke="#3E8E41" stroke-width="2.2"/>'
        '<rect x="71" y="7" width="34" height="46" rx="5" fill="#C7E6DA" stroke="#337435" stroke-width="2.3"/>'
        '<polygon points="77,43 82,19 98,17 100,39 87,45" fill="#D98D75" stroke="#337435" stroke-width="2.0"/>'
    )
    fig, ax = _new_fig(220, 120, 110, 60)
    ax.add_patch(FancyBboxPatch((5, 7), 46, 46, boxstyle="round,pad=0,rounding_size=5", facecolor="#D8E8D9", edgecolor="#337435", lw=2.3))
    ax.add_patch(Polygon([(15, 44), (21, 18), (39, 16), (42, 40), (27, 46)], facecolor="#F1F7FA", edgecolor="#337435", lw=1.9, ls="--"))
    ax.add_patch(FancyBboxPatch((71, 7), 34, 46, boxstyle="round,pad=0,rounding_size=5", facecolor="#C7E6DA", edgecolor="#337435", lw=2.3))
    ax.add_patch(Polygon([(77, 43), (82, 19), (98, 17), (100, 39), (87, 45)], facecolor="#D98D75", edgecolor="#337435", lw=2.0))
    pngs["ppt/media/image40.png"] = _finish_fig(fig)

    # 5d. id=605 image29.svg (93x30 aspect ~3.136): Exact 3-box [✓][✓][!] Risk Gate
    svgs["ppt/media/image29.svg"] = _svg(
        93, 30,
        '<rect x="1.5" y="1.5" width="25.5" height="27" rx="3.8" fill="#C7E6DA" stroke="#337435" stroke-width="2.1"/>'
        '<polyline points="7,15 12.5,20.5 21,9.5" stroke="#337435" stroke-width="2.7"/>'
        '<rect x="33.5" y="1.5" width="25.5" height="27" rx="3.8" fill="#C7E6DA" stroke="#337435" stroke-width="2.1"/>'
        '<polyline points="39,15 44.5,20.5 53,9.5" stroke="#337435" stroke-width="2.7"/>'
        '<rect x="65.5" y="1.5" width="25.5" height="27" rx="3.8" fill="#FADBD8" stroke="#C0392B" stroke-width="2.1"/>'
        '<line x1="78.2" y1="7.8" x2="78.2" y2="16.8" stroke="#C0392B" stroke-width="2.9"/>'
        '<circle cx="78.2" cy="21.5" r="1.7" fill="#C0392B"/>'
    )
    fig, ax = _new_fig(279, 90, 93, 30)
    for xx, fc, ec in [(1.5, "#C7E6DA", "#337435"), (33.5, "#C7E6DA", "#337435"), (65.5, "#FADBD8", "#C0392B")]:
        ax.add_patch(FancyBboxPatch((xx, 1.5), 25.5, 27, boxstyle="round,pad=0,rounding_size=3.8", facecolor=fc, edgecolor=ec, lw=2.1))
    ax.plot([7, 12.5, 21], [15, 20.5, 9.5], color="#337435", lw=2.7)
    ax.plot([39, 44.5, 53], [15, 20.5, 9.5], color="#337435", lw=2.7)
    ax.plot([78.2, 78.2], [7.8, 16.8], color="#C0392B", lw=2.9)
    ax.add_patch(Circle((78.2, 21.5), 1.7, facecolor="#C0392B"))
    pngs["ppt/media/image28.png"] = _finish_fig(fig)

    # 6. Wheel Bottom-Right: Optical Cues (Amber #A56219 / #B1691B / #F4E4D2)
    # 6a. id=606 image31.svg (54x24 aspect ~2.265): Specular reflection V-ray + surface
    svgs["ppt/media/image31.svg"] = _svg(
        54, 24,
        '<rect x="6" y="16" width="42" height="5" rx="2" fill="#F4E4D2" stroke="#A56219" stroke-width="1.8"/>'
        '<path d="M12,4 L27,16 L42,4" stroke="#A56219" stroke-width="2.0"/>'
        '<polyline points="37,4.5 42,4 41.5,9" stroke="#A56219" stroke-width="1.8"/>'
        '<circle cx="27" cy="16" r="2.6" fill="#C9771F"/>'
    )
    fig, ax = _new_fig(162, 72, 54, 24)
    ax.add_patch(FancyBboxPatch((6, 16), 42, 5, boxstyle="round,pad=0,rounding_size=2", facecolor="#F4E4D2", edgecolor="#A56219", lw=1.8))
    ax.plot([12, 27, 42], [4, 16, 4], color="#A56219", lw=2.0)
    pngs["ppt/media/image30.png"] = _finish_fig(fig)

    # 6b. id=507 image21.svg (24x24 exact 1:1): Displaced precision crosshair (#B1691B)
    svgs["ppt/media/image21.svg"] = _svg(
        24, 24,
        '<circle cx="12" cy="12" r="7" stroke="#B1691B" stroke-width="1.8"/>'
        '<line x1="12" y1="3" x2="12" y2="5.5" stroke="#B1691B" stroke-width="1.8"/>'
        '<line x1="3" y1="12" x2="5.5" y2="12" stroke="#B1691B" stroke-width="1.8"/>'
        '<line x1="12" y1="18.5" x2="12" y2="21" stroke="#B1691B" stroke-width="1.8"/>'
        '<line x1="18.5" y1="12" x2="21" y2="12" stroke="#B1691B" stroke-width="1.8"/>'
        '<circle cx="9.8" cy="12" r="1.4" fill="#B1691B"/>'
        '<circle cx="15.2" cy="12" r="1.8" fill="#D97706"/>'
    )
    fig, ax = _new_fig(96, 96, 24, 24)
    ax.add_patch(Circle((12, 12), 7, facecolor="none", edgecolor="#B1691B", lw=1.8))
    for (x0, y0, x1, y1) in [(12, 3, 12, 5.5), (3, 12, 5.5, 12), (12, 18.5, 12, 21), (18.5, 12, 21, 12)]:
        ax.plot([x0, x1], [y0, y1], color="#B1691B", lw=1.8)
    ax.add_patch(Circle((9.8, 12), 1.5, facecolor="#B1691B"))
    ax.add_patch(Circle((15.2, 12), 1.8, facecolor="#D97706"))
    pngs["ppt/media/image20.png"] = _finish_fig(fig)

    # 6c. id=607 image33.svg (28x24 aspect ~1.151): Viewfinder brackets + split L*a*b* contrast disc
    svgs["ppt/media/image33.svg"] = _svg(
        28, 24,
        '<path d="M3,8 V3 H8 M20,3 H25 V8 M3,16 V21 H8 M20,21 H25 V16" stroke="#A56219" stroke-width="1.9"/>'
        '<circle cx="14" cy="12" r="5.5" fill="#F4E4D2" stroke="#A56219" stroke-width="1.6"/>'
        '<path d="M14,6.5 A5.5,5.5 0 0,0 14,17.5 Z" fill="#C9771F"/>'
    )
    fig, ax = _new_fig(112, 96, 28, 24)
    for px, py in [([3, 3, 8], [8, 3, 3]), ([20, 25, 25], [3, 3, 8]), ([3, 3, 8], [16, 21, 21]), ([20, 25, 25], [21, 21, 16])]:
        ax.plot(px, py, color="#A56219", lw=1.9)
    ax.add_patch(Circle((14, 12), 5.5, facecolor="#F4E4D2", edgecolor="#A56219", lw=1.6))
    ax.add_patch(Wedge((14, 12), 5.5, 90, 270, facecolor="#C9771F"))
    pngs["ppt/media/image32.png"] = _finish_fig(fig)

    # 6d. id=608 image35.svg (26x24 aspect ~1.053): Glass prism refraction (#A56219 + #F4E4D2)
    svgs["ppt/media/image35.svg"] = _svg(
        26, 24,
        '<polygon points="13,3 22,20 4,20" fill="#F4E4D2" stroke="#A56219" stroke-width="1.9"/>'
        '<line x1="1" y1="14" x2="8.5" y2="12.5" stroke="#A56219" stroke-width="1.7"/>'
        '<line x1="8.5" y1="12.5" x2="17.5" y2="14" stroke="#C9771F" stroke-width="1.6"/>'
        '<line x1="17.5" y1="14" x2="25" y2="11" stroke="#A56219" stroke-width="1.6"/>'
        '<line x1="17.5" y1="14" x2="25" y2="17.5" stroke="#A56219" stroke-width="1.6"/>'
    )
    fig, ax = _new_fig(104, 96, 26, 24)
    ax.add_patch(Polygon([(13, 3), (22, 20), (4, 20)], facecolor="#F4E4D2", edgecolor="#A56219", lw=1.9))
    ax.plot([1, 8.5, 17.5, 25], [14, 12.5, 14, 11], color="#A56219", lw=1.7)
    ax.plot([17.5, 25], [14, 17.5], color="#A56219", lw=1.7)
    pngs["ppt/media/image34.png"] = _finish_fig(fig)

    # 7. Wheel Bottom-Left: 4 VLM Families Dual-Room Comparison (id=609 image37.svg, viewBox 220x76 -> aspect ~2.891)
    svgs["ppt/media/image37.svg"] = _svg(
        220, 76,
        # Left card: Original (MDL) room wireframe + unified hits
        '<rect x="3" y="4" width="96" height="68" rx="4" fill="#E1EBF2" stroke="#93B2C4" stroke-width="2.0"/>'
        '<polyline points="20,6 20,44 96,44" stroke="#93B2C4" stroke-width="1.8"/>'
        '<line x1="4" y1="68" x2="20" y2="44" stroke="#93B2C4" stroke-width="1.8"/>'
        '<rect x="36" y="18" width="40" height="24" rx="2.5" fill="#FFFFFF" stroke="#6488A0" stroke-width="1.8"/>'
        '<circle cx="48" cy="29" r="3.6" fill="#12947F"/>'
        '<circle cx="57" cy="27" r="3.6" fill="#1D63DC"/>'
        '<circle cx="53" cy="34" r="3.6" fill="#DC2646"/>'
        '<circle cx="63" cy="32" r="3.6" fill="#D97706"/>'
        # Bridge arrow
        '<path d="M103,38 H115 M111,33 L116,38 L111,43" stroke="#932C5E" stroke-width="2.6"/>'
        # Right card: Converted (Preview) room + architecture divergence (85.7% unique loss)
        '<rect x="121" y="4" width="96" height="68" rx="4" fill="#F5E6EB" stroke="#C99FB2" stroke-width="2.0"/>'
        '<polyline points="138,6 138,44 214,44" stroke="#C99FB2" stroke-width="1.8"/>'
        '<line x1="122" y1="68" x2="138" y2="44" stroke="#C99FB2" stroke-width="1.8"/>'
        '<rect x="154" y="18" width="40" height="24" rx="2.5" fill="#FFFFFF" stroke="#932C5E" stroke-width="1.8"/>'
        '<circle cx="166" cy="28" r="3.6" fill="#12947F"/>'
        '<circle cx="176" cy="31" r="3.6" fill="#1D63DC"/>'
        '<circle cx="136" cy="54" r="4.2" fill="#DC2646" stroke="#FFFFFF" stroke-width="1.2"/>'
        '<circle cx="203" cy="56" r="4.2" fill="#D97706" stroke="#FFFFFF" stroke-width="1.2"/>'
    )
    fig, ax = _new_fig(440, 152, 220, 76)
    ax.add_patch(FancyBboxPatch((3, 4), 96, 68, boxstyle="round,pad=0,rounding_size=4", facecolor="#E1EBF2", edgecolor="#93B2C4", lw=2.0))
    ax.add_patch(Rectangle((36, 18), 40, 24, facecolor="white", edgecolor="#6488A0", lw=1.8))
    ax.annotate("", xy=(117, 38), xytext=(102, 38), arrowprops=dict(arrowstyle="-|>", lw=2.4, color="#932C5E"))
    ax.add_patch(FancyBboxPatch((121, 4), 96, 68, boxstyle="round,pad=0,rounding_size=4", facecolor="#F5E6EB", edgecolor="#C99FB2", lw=2.0))
    ax.add_patch(Rectangle((154, 18), 40, 24, facecolor="white", edgecolor="#932C5E", lw=1.8))
    pngs["ppt/media/image36.png"] = _finish_fig(fig)

    return svgs, pngs


def _update_shape_text_keep_style(
    sp: ET.Element,
    paras_spec: list[dict],
    *,
    algn_override: str | None = None,
) -> None:
    """Update text runs inside an existing WET-OP PPTX shape while cloning its native pPr/rPr typography."""
    txBody = sp.find(f"{{{P_NS}}}txBody")
    if txBody is None:
        return
    bodyPr = txBody.find(f"{{{A_NS}}}bodyPr")
    lstStyle = txBody.find(f"{{{A_NS}}}lstStyle")
    orig_ps = txBody.findall(f"{{{A_NS}}}p")

    # Collect per-paragraph style templates (fallback cleanly to last existing paragraph/run)
    tmpl_ps: list[tuple[ET.Element | None, ET.Element | None, ET.Element | None]] = []
    for p in orig_ps:
        pPr = p.find(f"{{{A_NS}}}pPr")
        first_r = p.find(f"{{{A_NS}}}r")
        rPr = first_r.find(f"{{{A_NS}}}rPr") if first_r is not None else None
        endPr = p.find(f"{{{A_NS}}}endParaRPr")
        tmpl_ps.append((pPr, rPr, endPr))
    if not tmpl_ps:
        tmpl_ps.append((None, None, None))

    for ch in list(txBody):
        if ch not in (bodyPr, lstStyle):
            txBody.remove(ch)

    for p_idx, p_info in enumerate(paras_spec):
        t_idx = min(p_idx, len(tmpl_ps) - 1)
        t_pPr, t_rPr, t_endPr = tmpl_ps[t_idx]
        p = ET.SubElement(txBody, f"{{{A_NS}}}p")
        if t_pPr is not None:
            new_pPr = deepcopy(t_pPr)
            if algn_override:
                new_pPr.attrib["algn"] = algn_override
            elif "algn" in p_info:
                new_pPr.attrib["algn"] = p_info["algn"]
            p.append(new_pPr)
        elif algn_override or "algn" in p_info:
            ET.SubElement(p, f"{{{A_NS}}}pPr", algn=p_info.get("algn", algn_override))

        runs = p_info.get("runs") or [p_info]
        for r_idx, r_info in enumerate(runs):
            if r_info.get("br"):
                br = ET.SubElement(p, f"{{{A_NS}}}br")
                if t_rPr is not None:
                    br_rPr = deepcopy(t_rPr)
                    if "sz" in r_info:
                        br_rPr.attrib["sz"] = str(r_info["sz"])
                    br.append(br_rPr)
                continue
            r = ET.SubElement(p, f"{{{A_NS}}}r")
            if t_rPr is not None:
                new_rPr = deepcopy(t_rPr)
            else:
                new_rPr = ET.Element(f"{{{A_NS}}}rPr", lang="en-US", b="1")
                ET.SubElement(new_rPr, f"{{{A_NS}}}latin", typeface="Arial")
                ET.SubElement(new_rPr, f"{{{A_NS}}}cs", typeface="Arial")
            if "sz" in r_info:
                new_rPr.attrib["sz"] = str(r_info["sz"])
            if "b" in r_info:
                new_rPr.attrib["b"] = "1" if r_info["b"] else "0"
            if "i" in r_info:
                new_rPr.attrib["i"] = "1" if r_info["i"] else "0"
            if "color" in r_info:
                sf = new_rPr.find(f"{{{A_NS}}}solidFill")
                if sf is None:
                    sf = ET.SubElement(new_rPr, f"{{{A_NS}}}solidFill")
                else:
                    for ch_sf in list(sf):
                        sf.remove(ch_sf)
                ET.SubElement(sf, f"{{{A_NS}}}srgbClr", val=r_info["color"])
            r.append(new_rPr)
            t = ET.SubElement(r, f"{{{A_NS}}}t")
            t.text = r_info["text"]

        if t_endPr is not None:
            p.append(deepcopy(t_endPr))
        else:
            ET.SubElement(p, f"{{{A_NS}}}endParaRPr", lang="en-US")


def _make_svg_pic_elem(
    sid: int,
    name: str,
    x_pt: float,
    y_pt: float,
    w_pt: float,
    h_pt: float,
    png_rid: str,
    svg_rid: str,
) -> ET.Element:
    pic = ET.Element(f"{{{P_NS}}}pic")
    nvPicPr = ET.SubElement(pic, f"{{{P_NS}}}nvPicPr")
    ET.SubElement(nvPicPr, f"{{{P_NS}}}cNvPr", id=str(sid), name=name)
    nvPicPr_c = ET.SubElement(nvPicPr, f"{{{P_NS}}}cNvPicPr")
    ET.SubElement(nvPicPr_c, f"{{{A_NS}}}picLocks", noChangeAspect="1")
    ET.SubElement(nvPicPr, f"{{{P_NS}}}nvPr")

    bf = ET.SubElement(pic, f"{{{P_NS}}}blipFill")
    blip = ET.SubElement(bf, f"{{{A_NS}}}blip")
    blip.attrib[f"{{{R_NS}}}embed"] = png_rid
    extLst = ET.SubElement(blip, f"{{{A_NS}}}extLst")
    ext = ET.SubElement(extLst, f"{{{A_NS}}}ext", uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}")
    svgb = ET.SubElement(ext, f"{{{ASVG_NS}}}svgBlip")
    svgb.attrib[f"{{{R_NS}}}embed"] = svg_rid
    st = ET.SubElement(bf, f"{{{A_NS}}}stretch")
    ET.SubElement(st, f"{{{A_NS}}}fillRect")

    spPr = ET.SubElement(pic, f"{{{P_NS}}}spPr")
    xf = ET.SubElement(spPr, f"{{{A_NS}}}xfrm")
    ET.SubElement(xf, f"{{{A_NS}}}off", x=pt(x_pt), y=pt(y_pt))
    ET.SubElement(xf, f"{{{A_NS}}}ext", cx=pt(w_pt), cy=pt(h_pt))
    prst = ET.SubElement(spPr, f"{{{A_NS}}}prstGeom", prst="rect")
    ET.SubElement(prst, f"{{{A_NS}}}avLst")
    return pic


def _export_pptx_to_pdf_com(pptx_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    ps_cmd = (
        "$ppt = New-Object -ComObject PowerPoint.Application; "
        f"$pres = $ppt.Presentations.Open('{str(pptx_path)}', $true, $false, $false); "
        f"$pres.SaveAs('{str(pdf_path)}', 32); "
        "$pres.Close(); "
        "$ppt.Quit(); "
        "[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-root", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\assets\cviu"))
    parser.add_argument("--v1-runs-dir", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\assets\cviu\formal_model_runs_v1"))
    parser.add_argument("--v3-runs-dir", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\runs"))
    parser.add_argument("--no-com", action="store_true", help="Only write PPTX without COM PDF export.")
    args = parser.parse_args()

    sf = json.loads((V3_RAW_DIR / "scaling_and_families.json").read_text(encoding="utf-8"))
    feats = json.loads((V3_RAW_DIR / "pair_optical_features.json").read_text(encoding="utf-8"))["records"]
    scenes_meta = {
        s["scene_id"]: s["family"]
        for s in json.loads((V1_META_DIR / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    }
    manifest = json.loads((V1_META_DIR / "manifest.json").read_text(encoding="utf-8"))["records"]
    m_by_oc = {(r["pair_id"], r["condition"]): r for r in manifest}

    cf_manifest_p = Path(r"I:\cpfs\.cviu_v3_work\cf_cache\counterfactual_manifest.json")
    cf_img_map = {}
    if cf_manifest_p.is_file():
        cf_img_map = {
            (r["pair_id"], r["condition"]): Path(r["image"]["path"])
            for r in json.loads(cf_manifest_p.read_text(encoding="utf-8"))["records"]
        }

    p8 = _index_oc(args.v1_runs_dir / "8b/formal_repeat0/predictions.jsonl")
    cf8 = _index_oc(args.v3_runs_dir / "counterfactual_qwen3_vl_8b/predictions.jsonl")

    # Four flagship models matching capability colors & WET-OP Legend order
    active_models = [
        ("molmo2_8b",             "Molmo2-8B",     "12947F", _index_oc(args.v3_runs_dir / "formal_molmo2_8b/predictions.jsonl")),
        ("qwen3_vl_8b_r0",        "Qwen3-VL-8B",   "1D63DC", p8),
        ("internvl3_5_8b",        "InternVL3.5",   "DC2646", _index_oc(args.v3_runs_dir / "formal_internvl3_5_8b/predictions.jsonl")),
        ("llava_next_mistral_7b", "LLaVA-Mistral", "D97706", _index_oc(args.v3_runs_dir / "formal_llava_next_mistral_7b/predictions.jsonl")),
    ]

    def _model_regime_flips(idx_map: dict) -> dict[str, float]:
        reg_map = {"RM": "Reflective/Metallic", "TG": "Transparent/Glass", "MD": "Matte/Diffuse", "ES": "Emissive/Screen"}
        res = {}
        for short, full in reg_map.items():
            sub = [f["pair_id"] for f in feats if f["prior_optical_regime"] == full]
            flips = sum(int(bool(idx_map[(pid, "original")]["hit"]) != bool(idx_map[(pid, "converted")]["hit"])) for pid in sub)
            res[short] = flips / max(len(sub), 1) * 100.0
        return res

    def _cluster_bars(idx_map: dict, domain_fn) -> tuple[float, float]:
        sub = [f["pair_id"] for f in feats if domain_fn(f)]
        both = sum(bool(idx_map[(p, "original")]["hit"]) and bool(idx_map[(p, "converted")]["hit"]) for p in sub)
        either = sum(bool(idx_map[(p, "original")]["hit"]) or bool(idx_map[(p, "converted")]["hit"]) for p in sub)
        return both / len(sub) * 100.0, either / len(sub) * 100.0

    def _render_clean(pid: str, cond: str, w_px: int, h_px: int, *, pad_frac: float = 1.60, cf_img: Path | None = None) -> bytes:
        rec = m_by_oc[(pid, "converted" if cond == "target_only" else "original" if cond in ("original", "background_only", "photometric_matched") else "converted")]
        img_p = cf_img if cf_img is not None else _resolve_asset(rec["image"]["path"], args.assets_root)
        msk_p = _resolve_asset(rec["mask"]["path"], args.assets_root)
        im = np.asarray(Image.open(img_p).convert("RGB"))
        msk = np.load(msk_p, allow_pickle=False).astype(bool)
        return _pure_scene_crop(im, msk, w_px, h_px, pad_frac=pad_frac)

    def _render_audit(pid: str, cond: str, pred_row: dict | None, w_px: int, h_px: int, *, cf_img: Path | None = None) -> bytes:
        rec = m_by_oc[(pid, "converted" if cond in ("target_only", "converted") else "original")]
        img_p = cf_img if cf_img is not None else _resolve_asset(rec["image"]["path"], args.assets_root)
        msk_p = _resolve_asset(rec["mask"]["path"], args.assets_root)
        im = np.asarray(Image.open(img_p).convert("RGB"))
        msk = np.load(msk_p, allow_pickle=False).astype(bool)
        pt_norm = pred_row.get("point_normalized") if pred_row else None
        is_hit = bool(pred_row["hit"]) if pred_row else True
        return _audit_pin_crop(im, msk, w_px, h_px, point_norm=pt_norm, hit=is_hit, pad_frac=1.95)

    def _render_cutout(pid: str, cond: str) -> bytes:
        rec = m_by_oc[(pid, cond)]
        im = np.asarray(Image.open(_resolve_asset(rec["image"]["path"], args.assets_root)).convert("RGB"))
        msk = np.load(_resolve_asset(rec["mask"]["path"], args.assets_root), allow_pickle=False).astype(bool)
        return _cutout_rgba_asset(im, msk, 460, 432)

    with zipfile.ZipFile(WETOP_PPTX, "r") as zin:
        entries = {n: zin.read(n) for n in zin.namelist()}

    # 1. Pure high-res scene crops (5x) & RGBA arched-clock cutouts & real KuJiaLe VLN rollout
    media_replacements = {
        # Top 8 gallery thumbnails (ratio 129.6/154.5 -> 648x772 px)
        "ppt/media/image1.png": _render_clean("MV7J6NIKTKJZ2AABAAAAADY8_usd:67a943f7f405a801:v0", "original", 648, 772, pad_frac=1.65),
        "ppt/media/image2.jpeg": _render_clean("MVUCSQAKTKJ5EAABAAAAAAY8_usd:073b824ac9c68c6c:v2", "converted", 648, 772, pad_frac=1.45),
        "ppt/media/image3.jpeg": _render_clean("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "original", 648, 772, pad_frac=1.55),
        "ppt/media/image4.png": _render_clean("MWF4WLIKTIFZIAABAAAAACY8_usd:790f1a4c4a29acba:v0", "original", 648, 772, pad_frac=1.65),
        "ppt/media/image5.png": _render_clean("MWF4WLIKTIFZIAABAAAAADQ8_usd:8f296c1d09c97da9:v0", "original", 648, 772, pad_frac=1.45),
        "ppt/media/image6.png": _render_clean("MVUHLWYKTKJ5EAABAAAAACQ8_usd:eb4d6edba08ddab1:v0", "original", 648, 772, pad_frac=1.45),
        "ppt/media/image7.png": _render_clean("MV5M25QKTKJZ2AABAAAAAAI8_usd:39af2d8e48814112:v0", "original", 648, 772, pad_frac=1.45),
        "ppt/media/image8.png": _render_clean("MWF4WLIKTIFZIAABAAAAAEA8_usd:26b4dbaac85d35d5:v2", "original", 648, 772, pad_frac=1.55),
        # Bottom-left 6 protocols (ratio 183.9/126.0 -> 920x630 px)
        "ppt/media/image9.png": _render_clean(
            "MWAX5JYKTKJZ2AABAAAAAAA8_usd:49332fc22c9d2612:v0", "photometric_matched", 920, 630, pad_frac=1.60,
            cf_img=cf_img_map.get(("MWAX5JYKTKJZ2AABAAAAAAA8_usd:49332fc22c9d2612:v0", "photometric_matched")),
        ),
        "ppt/media/image10.png": _render_clean(
            "MWAX5JYKTKJZ2AABAAAAAAA8_usd:49332fc22c9d2612:v0", "target_only", 920, 630, pad_frac=1.60,
            cf_img=cf_img_map.get(("MWAX5JYKTKJZ2AABAAAAAAA8_usd:49332fc22c9d2612:v0", "target_only")),
        ),
        "ppt/media/image11.png": _render_clean(
            "MWAX5JYKTKJZ2AABAAAAAAA8_usd:49332fc22c9d2612:v0", "background_only", 920, 630, pad_frac=1.60,
            cf_img=cf_img_map.get(("MWAX5JYKTKJZ2AABAAAAAAA8_usd:49332fc22c9d2612:v0", "background_only")),
        ),
        "ppt/media/image12.png": _render_clean("MV7J6NIKTKJZ2AABAAAAADY8_usd:fd8d1fd4074a7925:v0", "original", 920, 630, pad_frac=1.60),
        "ppt/media/image13.png": _render_clean("MVUCSQAKTKJ5EAABAAAAABA8_usd:52d264f7bf546f60:v0", "original", 920, 630, pad_frac=2.15),
        "ppt/media/image14.png": _crop_vln_rollout(920, 630),
        # Top-right 4 audit progression frames (ratio 123.1/59.2 -> 862x414 px)
        "ppt/media/image15.png": _render_audit("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "original", p8.get(("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "original")), 862, 414),
        "ppt/media/image16.png": _render_audit(
            "MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "photometric_matched",
            cf8.get(("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "photometric_matched")), 862, 414,
            cf_img=cf_img_map.get(("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "photometric_matched")),
        ),
        "ppt/media/image17.png": _render_audit(
            "MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "target_only",
            cf8.get(("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "target_only")), 862, 414,
            cf_img=cf_img_map.get(("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "target_only")),
        ),
        "ppt/media/image18.png": _render_audit("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "converted", p8.get(("MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1", "converted")), 862, 414),
        # Center bottom Shader2Sim studio cutouts (Arched Desk Clock MDL vs Preview)
        "ppt/media/image38.png": _render_cutout("MWF4WLIKTIFZIAABAAAAAEA8_usd:26b4dbaac85d35d5:v2", "original"),
        "ppt/media/image39.png": _render_cutout("MWF4WLIKTIFZIAABAAAAAEA8_usd:26b4dbaac85d35d5:v2", "converted"),
    }
    svgs, fallback_pngs = _craft_svgs_and_pngs()
    entries.update(media_replacements)
    entries.update(svgs)
    entries.update(fallback_pngs)

    # Save valid JPEGs into .jpeg slots
    for jk in ("ppt/media/image2.jpeg", "ppt/media/image3.jpeg"):
        im_tmp = Image.open(io.BytesIO(entries[jk])).convert("RGB")
        jbuf = io.BytesIO()
        im_tmp.save(jbuf, format="JPEG", quality=94)
        entries[jk] = jbuf.getvalue()

    # 2. Register new media files in slide1.xml.rels & [Content_Types].xml
    rels_root = ET.fromstring(entries["ppt/slides/_rels/slide1.xml.rels"])
    existing_rids = [int(r.attrib["Id"][3:]) for r in rels_root if r.attrib["Id"].startswith("rId")]
    next_rid_num = max(existing_rids) + 1

    def _add_rel(target: str) -> str:
        nonlocal next_rid_num
        rid = f"rId{next_rid_num}"
        next_rid_num += 1
        el = ET.SubElement(rels_root, f"{{{RELS_NS}}}Relationship")
        el.attrib["Id"] = rid
        el.attrib["Type"] = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
        el.attrib["Target"] = target
        return rid

    new_icon_rids = {
        "hub": (_add_rel("../media/ca_hub_sphere.png"), _add_rel("../media/ca_hub_sphere.svg")),
        "rm": (_add_rel("../media/ca_icon_rm.png"), _add_rel("../media/ca_icon_rm.svg")),
        "tg": (_add_rel("../media/ca_icon_tg.png"), _add_rel("../media/ca_icon_tg.svg")),
        "md": (_add_rel("../media/ca_icon_md.png"), _add_rel("../media/ca_icon_md.svg")),
        "es": (_add_rel("../media/ca_icon_es.png"), _add_rel("../media/ca_icon_es.svg")),
        "vlm_svg": _add_rel("../media/ca_vlm_models.svg"),
    }
    ET.register_namespace("", RELS_NS)
    entries["ppt/slides/_rels/slide1.xml.rels"] = ET.tostring(rels_root, encoding="utf-8", xml_declaration=True)

    ct_root = ET.fromstring(entries["[Content_Types].xml"])
    has_svg_def = any(el.tag.endswith("Default") and el.attrib.get("Extension") == "svg" for el in ct_root)
    if not has_svg_def:
        ET.SubElement(ct_root, f"{{{CT_NS}}}Default", Extension="svg", ContentType="image/svg+xml")
    existing_parts = {el.attrib.get("PartName") for el in ct_root if el.tag.endswith("Override")}
    for svg_part in svgs:
        pn = "/" + svg_part
        if pn not in existing_parts:
            ET.SubElement(ct_root, f"{{{CT_NS}}}Override", PartName=pn, ContentType="image/svg+xml")
    ET.register_namespace("", CT_NS)
    entries["[Content_Types].xml"] = ET.tostring(ct_root, encoding="utf-8", xml_declaration=True)

    # 3. Surgical slide1.xml edits preserving all original formatting & gradients
    root = ET.fromstring(entries["ppt/slides/slide1.xml"])
    spTree = root.find(f"{{{P_NS}}}cSld/{{{P_NS}}}spTree")

    m32 = sf["models"]["qwen3_vl_32b_r0"]["metrics"]
    flips_all = [sf["models"][k]["metrics"]["flip_rate"]["estimate"] * 100.0 for k in sf["models"]]
    min_fl, max_fl = min(flips_all), max(flips_all)
    min_dh = sf["models"].get("molmo2_8b", m32)["metrics"]["hit_rate_difference"]["estimate"] * 100.0

    # Style-preserving text replacements (id -> list of paragraphs)
    text_specs: dict[str, tuple[list[dict], str | None]] = {
        # Title & Subtitle
        "372": ([{"runs": [{"text": "Convert", "color": "173A6B"}, {"text": "Asset", "color": "0F8B8D"}]}], None),
        "714": ([{"runs": [{"text": "with ", "sz": 1340, "color": "526278"}, {"text": "3D Material Conversion & Risk Audit", "sz": 1340, "color": "526278"}]}], None),
        # Top 4 optical categories (preserve bold+italic & exact WET-OP header colors)
        "9":  ([{"runs": [{"text": "Reflective & Metallic (RM)", "sz": 1380}]}], None),
        "19": ([{"runs": [{"text": "Transparent & Glass (TG)", "sz": 1380}]}], None),
        "28": ([{"runs": [{"text": "Matte & Diffuse (MD)", "sz": 1450}]}], None),
        "40": ([{"runs": [{"text": "Emissive & Screen (ES)", "sz": 1420}]}], None),
        # Top 8 card labels (exact 2-line bold navy #173A6B with <a:br>)
        "11": ([{"runs": [{"text": "Stainless Kettle", "sz": 1020}, {"br": True, "sz": 1020}, {"text": "Specular Glare Strip", "sz": 1020}]}], None),
        "13": ([{"runs": [{"text": "Metallic Armchair", "sz": 1020}, {"br": True, "sz": 1020}, {"text": "Highlight Recovery", "sz": 1020}]}], None),
        "21": ([{"runs": [{"text": "Stacked Oven Glass", "sz": 1020}, {"br": True, "sz": 1020}, {"text": "Multi-Layer Refraction", "sz": 1020}]}], None),
        "23": ([{"runs": [{"text": "Glass Wall Display", "sz": 1020}, {"br": True, "sz": 1020}, {"text": "Mirror Reflection Loss", "sz": 1020}]}], None),
        "30": ([{"runs": [{"text": "Pedal Waste Bin", "sz": 1020}, {"br": True, "sz": 1020}, {"text": "Albedo & Roughness", "sz": 1020}]}], None),
        "32": ([{"runs": [{"text": "Timber-Frame Sofa", "sz": 1020}, {"br": True, "sz": 1020}, {"text": "Diffuse Edge Contrast", "sz": 1020}]}], None),
        "42": ([{"runs": [{"text": "Wall-Mounted Screen", "sz": 1020}, {"br": True, "sz": 1020}, {"text": "Emissive Radiance", "sz": 1020}]}], None),
        "44": ([{"runs": [{"text": "Arched Desk Clock", "sz": 1020}, {"br": True, "sz": 1020}, {"text": "Dial Contrast Loss", "sz": 1020}]}], None),
        # Rail pills + compose
        "188": ([{"runs": [{"text": "RM"}]}], None),
        "190": ([{"runs": [{"text": "TG"}]}], None),
        "192": ([{"runs": [{"text": "MD"}]}], None),
        "194": ([{"runs": [{"text": "ES"}]}], None),
        "197": ([{"runs": [{"text": "intervene"}]}], None),
        # Bottom-left Counterfactual & VLN section (compact 2-line inset so zero collision with circle halo!)
        "52": ([{"runs": [{"text": "Counterfactual & VLN protocols", "sz": 1600}]}], None),
        "54": ([{"runs": [{"text": "CIE L*a*b* Match", "sz": 990}, {"br": True, "sz": 990}, {"text": "Luminance Control", "sz": 990}]}], None),
        "56": ([{"runs": [{"text": "Target-Only Swap (Iᵀ)", "sz": 990}, {"br": True, "sz": 990}, {"text": "FG BSDF Isolation", "sz": 990}]}], None),
        "58": ([{"runs": [{"text": "Background Swap (Iᴮ)", "sz": 960}, {"br": True, "sz": 960}, {"text": "Context Coherence", "sz": 960}]}], None),
        "60": ([{"runs": [{"text": "Ray-Tracing Repeat", "sz": 990}, {"br": True, "sz": 990}, {"text": "3-Scene Noise Floor", "sz": 990}]}], None),
        "62": ([{"runs": [{"text": "Zero-VLM Risk Gate", "sz": 990}, {"br": True, "sz": 990}, {"text": "20 Geometry Cues", "sz": 990}]}], None),
        "64": ([{"runs": [{"text": "Closed-Loop DualVLN", "sz": 990}, {"br": True, "sz": 990}, {"text": "99 Unseen Rollouts", "sz": 990}]}], None),
        # Center wheel 7 sectors (exact template font ratios)
        "365": ([{"runs": [{"text": "6", "sz": 2475}]}, {"runs": [{"text": "VLM Models", "sz": 1400}]}], None),
        "216": ([{"runs": [{"text": "30"}]}], None),
        "217": ([{"runs": [{"text": "SimReady Scenes", "sz": 1280}]}], None),
        "247": ([{"runs": [{"text": "240 Targets", "sz": 1080}]}], None),
        "248": ([{"runs": [{"text": "480"}]}], None),
        "249": ([{"runs": [{"text": "Natural Pairs", "sz": 1350}]}], None),
        "254": ([{"runs": [{"text": "Highlights"}]}], None),
        "263": ([{"runs": [{"text": "BSDF shift"}]}], None),
        "270": ([{"runs": [{"text": "Noise floor"}]}], None),
        "285": ([{"runs": [{"text": "Mask CFs"}]}], None),
        "294": ([{"runs": [{"text": "Risk gate"}]}], None),
        "295": ([{"runs": [{"text": "Optical Cues", "sz": 1450}]}], None),
        "300": ([{"runs": [{"text": "Specular"}]}], None),
        "305": ([{"runs": [{"text": "Point shift"}]}], None),
        "311": ([{"runs": [{"text": "CIE L*a*b*"}]}, {"runs": [{"text": "contrast"}]}], None),
        "322": ([{"runs": [{"text": "Refraction"}]}, {"runs": [{"text": "& SSIM"}]}], None),
        "323": ([{"runs": [{"text": "Shader2Sim"}]}, {"runs": [{"text": "Assets"}]}], None),
        "328": ([{"runs": [{"text": "MDL"}]}], None),
        "329": ([{"runs": [{"text": "Preview"}]}], None),
        "2":   ([{"runs": [{"text": "4", "sz": 2475}]}], None),
        "330": ([{"runs": [{"text": " ", "sz": 2475}]}, {"runs": [{"text": "VLM Families", "sz": 1425}]}], None),
        "361": ([{"runs": [{"text": "2,880", "sz": 2150}]}], None),
        "362": ([{"runs": [{"text": "Counterfactual evals", "sz": 1080}]}], None),
        "363": ([{"runs": [{"text": "14,016", "sz": 2150}]}], None),
        "364": ([{"runs": [{"text": "Total BF16 evals", "sz": 1150}]}], None),
        # Top-right evaluation panel
        "67":  ([{"runs": [{"text": "Paired Decision Turnover Audit"}]}], None),
        "73":  ([{"runs": [{"text": "Orig Hit", "sz": 960}]}], "ctr"),
        "78":  ([{"runs": [{"text": "Lab Hit", "sz": 960}]}], "ctr"),
        "83":  ([{"runs": [{"text": "CF Hit", "sz": 960}]}], "ctr"),
        "88":  ([{"runs": [{"text": "Miss", "sz": 980}]}], "ctr"),
        "95":  ([{"runs": [{"text": "Min |ΔHit|"}]}], "r"),
        "96":  ([{"runs": [{"text": f"{min_dh:+.2f}%", "sz": 1650, "color": "0F766E"}]}], "l"),
        "98":  ([{"runs": [{"text": "Turnover"}]}], "r"),
        "99":  ([{"runs": [{"text": f"{min_fl:.1f}–{max_fl:.1f}%", "sz": 1520, "color": "1F3F73"}]}], "l"),
        "101": ([{"runs": [{"text": "Hazard"}]}], "r"),
        "102": ([{"runs": [{"text": "Silent Loss", "sz": 1550, "color": "C8203B"}]}], "l"),
        "104": ([{"runs": [{"text": "Geometric fidelity ≠ decision fidelity"}]}], None),
    }

    # Preserve WET-OP's crisp wheel-icon id=250..252, id=2, and target reticle id=47..51!
    # Remove ONLY: top-4 multi-shape card icons (id=5..8,16..18,26..27,35..39), center flask (369..371), extra inset (650).
    remove_ids = {
        "5", "6", "7", "8",
        "16", "17", "18",
        "26", "27",
        "35", "36", "37", "38", "39",
        "369", "370", "371",
        "650",
    }

    box_adjust: dict[str, tuple[float | None, float | None, float | None, float | None]] = {
        "714": (614.0, None, 349.0, None),
        "9":   (72.0,  None, 226.0, None),
        "19":  (381.0, None, 218.0, None),
        "28":  (1028.0, None, 222.0, None),
        "40":  (1320.0, None, 234.0, None),
        "52":  (196.0, None, 282.0, None),
        "58":  (417.0, None, 134.0, None),
        "217": (728.0, None, 121.0, None),
        "247": (752.0, 236.0, 72.0, 18.0),
        "249": (831.0, None, 100.0, None),
        "67":  (1035.0, None, 310.0, None),
        # Keep crisp chip widths well inside each 123pt thumbnail frame
        "72":  (1058.5, None, 48.0, None),
        "73":  (1058.5, None, 48.0, None),
        "77":  (1189.6, None, 46.0, None),
        "78":  (1189.6, None, 46.0, None),
        "82":  (1320.7, None, 44.0, None),
        "83":  (1320.7, None, 44.0, None),
        "87":  (1451.7, None, 46.0, None),
        "88":  (1451.7, None, 46.0, None),
        # Center KPI labels inside each 166.8pt score card
        "95":  (1042.0, None, 62.0, None),
        "96":  (1108.0, None, 86.0, None),
        "98":  (1214.0, None, 58.0, None),
        "99":  (1276.0, None, 96.0, None),
        "101": (1390.0, None, 48.0, None),
        "102": (1442.0, None, 106.0, None),
    }

    to_remove = []
    max_id = 850
    clear_srcrect_ids = {
        "10", "12", "20", "22", "29", "31", "41", "43",
        "53", "55", "57", "59", "61", "63",
        "69", "74", "79", "84", "325", "326", "366",
    }

    for child in list(spTree):
        nv = child.find(f".//{{{P_NS}}}cNvPr")
        sid = nv.attrib.get("id", "") if nv is not None else ""
        if sid.isdigit():
            max_id = max(max_id, int(sid))
        name = nv.attrib.get("name", "") if nv is not None else ""
        if sid in remove_ids:
            to_remove.append(child)
            continue

        # Shift left bottom-left target reticle (id=47..51) cleanly beside widened header
        if sid in {"47", "48", "49", "50", "51"}:
            off_e = child.find(f".//{{{A_NS}}}off")
            if off_e is not None:
                off_e.attrib["x"] = str(int(off_e.attrib["x"]) - int(round(56.0 * EMU_PER_PT)))

        # Clear srcRect so pre-framed high-DPI crops display 100% intact
        if sid in clear_srcrect_ids:
            sr = child.find(f"{{{P_NS}}}blipFill/{{{A_NS}}}srcRect")
            if sr is not None:
                sr.attrib.clear()

        # Upgrade id=366 wheel-robot blip with our vector ca_vlm_models.svg svgBlip
        if sid == "366":
            blip = child.find(f"{{{P_NS}}}blipFill/{{{A_NS}}}blip")
            if blip is not None:
                extLst = blip.find(f"{{{A_NS}}}extLst") or ET.SubElement(blip, f"{{{A_NS}}}extLst")
                for ex in list(extLst):
                    extLst.remove(ex)
                ex = ET.SubElement(extLst, f"{{{A_NS}}}ext", uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}")
                sb = ET.SubElement(ex, f"{{{ASVG_NS}}}svgBlip")
                sb.attrib[f"{{{R_NS}}}embed"] = new_icon_rids["vlm_svg"]

        # Exact bounding box tuning where text strings are wider
        if sid in box_adjust:
            nx, ny, ncx, ncy = box_adjust[sid]
            xf = child.find(f".//{{{A_NS}}}xfrm")
            if xf is not None:
                off_e, ext_e = xf.find(f"{{{A_NS}}}off"), xf.find(f"{{{A_NS}}}ext")
                if off_e is not None:
                    if nx is not None:
                        off_e.attrib["x"] = pt(nx)
                    if ny is not None:
                        off_e.attrib["y"] = pt(ny)
                if ext_e is not None:
                    if ncx is not None:
                        ext_e.attrib["cx"] = pt(ncx)
                    if ncy is not None:
                        ext_e.attrib["cy"] = pt(ncy)

        if sid in text_specs:
            p_spec, algn_ov = text_specs[sid]
            _update_shape_text_keep_style(child, p_spec, algn_override=algn_ov)
            continue

        # Remove WET-OP bottom-right Benchmark Results child elements (keep outer frame id=105)
        xf = child.find(f".//{{{A_NS}}}xfrm")
        if xf is not None:
            off = xf.find(f"{{{A_NS}}}off")
            if off is not None:
                x_pt = int(off.attrib["x"]) / EMU_PER_PT
                y_pt = int(off.attrib["y"]) / EMU_PER_PT
                if x_pt > 960 and y_pt > 440 and not (name == "panel" and abs(x_pt - 967.9) < 2.0):
                    to_remove.append(child)

    for ch in to_remove:
        spTree.remove(ch)

    sid_ctr = max_id + 10

    def next_id() -> int:
        nonlocal sid_ctr
        sid_ctr += 1
        return sid_ctr

    # 4. Insert Center Hub Split Shader Sphere SVG right above logo-disc (id=368)
    hub_pic = _make_svg_pic_elem(
        next_id(), "ca-hub-sphere-svg", 752.6, 317.2, 72.0, 72.0,
        new_icon_rids["hub"][0], new_icon_rids["hub"][1],
    )
    logo_idx = next(
        i for i, ch in enumerate(spTree)
        if ch.find(f".//{{{P_NS}}}cNvPr") is not None and ch.find(f".//{{{P_NS}}}cNvPr").attrib.get("id") == "368"
    )
    spTree.insert(logo_idx + 1, hub_pic)

    # 5. Insert Top 4 Domain Header SVGs inside panel strips (matching exact strip y center = 39.6)
    card_icons = [
        ("ca-icon-rm", 42.0, 26.6, new_icon_rids["rm"]),
        ("ca-icon-tg", 351.0, 26.6, new_icon_rids["tg"]),
        ("ca-icon-md", 998.0, 26.6, new_icon_rids["md"]),
        ("ca-icon-es", 1290.0, 26.6, new_icon_rids["es"]),
    ]
    for nm, ix, iy, (prid, srid) in card_icons:
        spTree.append(_make_svg_pic_elem(next_id(), nm, ix, iy, 26.0, 26.0, prid, srid))

    # 6. Rebuild Bottom-Right Benchmark Results using native OOXML helpers (exact WET-OP 3-cluster grouped nested bars!)
    spec_u = importlib.util.spec_from_file_location("wetop_u", WETOP_HELPER)
    wetop_u = importlib.util.module_from_spec(spec_u)
    assert spec_u and spec_u.loader
    spec_u.loader.exec_module(wetop_u)

    bm_stage = ET.Element("stage")
    wetop_u.add_rect(bm_stage, next_id(), "panel-title-strip", 973.7, 449.4, 582.0, 22.0, round_adj=25532, grad_hexes=("C9D2DF", "E4E8EF"))
    wetop_u.add_textbox(
        bm_stage, next_id(), "bm-title-text", 1012.0, 449.4, 126.0, 22.0,
        [{"text": "Benchmark Results", "sz_pt": 11.2, "bold": True, "italic": True, "color": "1B3765"}], algn="l",
    )
    # Frosted inline 4-model legend pill
    wetop_u.add_rect(bm_stage, next_id(), "bm-legend-bg", 1140.0, 451.0, 412.0, 18.8, fill_hex="FFFFFF", fill_alpha=92, line_hex="D5DFEC", line_w_pt=0.65, round_adj=22000)
    leg_w = 400.0 / len(active_models)
    for mi, (mkey, disp, col, _) in enumerate(active_models):
        lx = 1150.0 + mi * leg_w
        ly = 460.4
        wetop_u.add_line(bm_stage, next_id(), f"leg-ln-{mkey}", lx, ly, lx + 11.5, ly, line_hex=col, line_w_pt=1.7)
        wetop_u.add_ellipse(bm_stage, next_id(), f"leg-dt-{mkey}", lx + 5.75, ly, 1.5, fill_hex=col, line_hex="FFFFFF", line_w_pt=0.45)
        wetop_u.add_textbox(bm_stage, next_id(), f"leg-tx-{mkey}", lx + 13.5, 451.0, leg_w - 14.0, 18.8, [{"text": disp, "sz_pt": 8.0, "bold": True, "color": "0F172A"}], algn="l")

    # Left Sub-panel: Regime Flip Profile (Nightingale Rose 0–18%)
    wetop_u.add_textbox(
        bm_stage, next_id(), "bm-left-sub", 988.0, 472.2, 236.0, 12.2,
        [{"text": "Regime Flip Profile ", "sz_pt": 9.0, "bold": True, "color": "0F172A"},
         {"text": "(Flip %, 0–18%)", "sz_pt": 8.2, "bold": False, "color": "475569"}], algn="ctr",
    )
    cx, cy, R = 1106.0, 532.5, 38.0
    RMAX_ROSE = 18.0
    wetop_u.add_ellipse(bm_stage, next_id(), "rose-bg", cx, cy, R, fill_hex="FFFFFF", line_hex="CBD5E1", line_w_pt=0.75)
    for rp in (6.0, 12.0):
        wetop_u.add_ellipse(bm_stage, next_id(), f"rose-r-{int(rp)}", cx, cy, R * rp / RMAX_ROSE, fill_hex=None, line_hex="E2E8F0", line_w_pt=0.55, dash="dash")
    for deg_sep in (-90.0, 0.0, 90.0, 180.0):
        rad_s = math.radians(deg_sep)
        wetop_u.add_line(bm_stage, next_id(), f"rose-div-{int(deg_sep)}", cx, cy, cx + R * math.cos(rad_s), cy + R * math.sin(rad_s), line_hex="CBD5E1", line_w_pt=0.7)

    reg_flips = {mkey: _model_regime_flips(idx_m) for mkey, _, _, idx_m in active_models}
    quad_specs = [("RM", -135.0), ("TG", -45.0), ("MD", 45.0), ("ES", 135.0)]
    wedge_span = 68.0 / len(active_models)
    for reg_s, q_deg in quad_specs:
        start_base = q_deg - (len(active_models) / 2.0) * wedge_span
        for mi, (mkey, _, mcol, _) in enumerate(active_models):
            v = reg_flips[mkey][reg_s]
            rw = R * min(max(v, 0.8), RMAX_ROSE) / RMAX_ROSE
            a0 = math.radians(start_base + mi * wedge_span + 0.8)
            a1 = math.radians(start_base + (mi + 1) * wedge_span - 0.8)
            arc = [(cx + rw * math.cos(a0 + (a1 - a0) * k / 10.0), cy + rw * math.sin(a0 + (a1 - a0) * k / 10.0)) for k in range(11)]
            wetop_u.add_polygon(bm_stage, next_id(), f"rose-w-{reg_s}-{mkey}", [(cx, cy)] + arc, fill_hex=mcol, fill_alpha=84, line_hex="FFFFFF", line_w_pt=0.45)
        q_rad = math.radians(q_deg)
        lx = cx + (R + 5.0) * math.cos(q_rad)
        ly = cy + (R + 4.0) * math.sin(q_rad)
        mean_v = float(np.mean([reg_flips[mkey][reg_s] for mkey, _, _, _ in active_models]))
        tw = 74.0
        bx = lx if math.cos(q_rad) > 0 else lx - tw
        algn = "l" if math.cos(q_rad) > 0 else "r"
        wetop_u.add_textbox(
            bm_stage, next_id(), f"rose-lbl-{reg_s}", bx, ly - 6.0, tw, 12.0,
            [{"text": f"{reg_s} ", "sz_pt": 9.0, "bold": True, "color": "0F172A"},
             {"text": f"({mean_v:.1f}%)", "sz_pt": 7.8, "bold": True, "color": "475569"}], algn=algn,
        )

    # Vertical divider
    wetop_u.add_line(bm_stage, next_id(), "bm-divider", 1228.0, 475.5, 1228.0, 576.0, line_hex="CBD5E1", line_w_pt=0.8)

    # Right Sub-panel: Exact WET-OP 3-Cluster x 4-Model Nested Bars (Home 20 | Commercial 10 | All Scenes 30)
    wetop_u.add_textbox(
        bm_stage, next_id(), "bm-right-sub", 1235.0, 472.2, 319.0, 12.2,
        [{"text": "Domain Summary: ", "sz_pt": 9.0, "bold": True, "color": "0F172A"},
         {"text": "Both-Hit % (solid)", "sz_pt": 8.4, "bold": True, "color": "1D63DC"},
         {"text": " vs. ", "sz_pt": 8.2, "color": "475569"},
         {"text": "Union % (tinted)", "sz_pt": 8.4, "bold": True, "color": "0F172A"}], algn="ctr",
    )
    px0, px1 = 1261.0, 1553.0
    py_top, py_bot = 490.5, 563.5
    ph = py_bot - py_top
    YMAX = 105.0
    wetop_u.add_rect(bm_stage, next_id(), "bar-plot-bg", px0, py_top, px1 - px0, ph, fill_hex="FFFFFF", fill_alpha=78)
    for gy_val in (0, 25, 50, 75, 100):
        gy = py_bot - ph * (gy_val / YMAX)
        wetop_u.add_line(bm_stage, next_id(), f"bar-g-{gy_val}", px0, gy, px1, gy, line_hex="94A3B8" if gy_val == 0 else "E2E8F0", line_w_pt=0.85 if gy_val == 0 else 0.55, dash=None if gy_val == 0 else "dash")
        if gy_val in (0, 50, 100):
            wetop_u.add_textbox(bm_stage, next_id(), f"bar-yt-{gy_val}", px0 - 26.5, gy - 5.5, 24.0, 11.0, [{"text": str(gy_val), "sz_pt": 8.2, "bold": True, "color": "475569"}], algn="r")

    clusters = [
        ("Home (20)",       lambda f: scenes_meta[f["scene_id"]] == "home_scenes"),
        ("Commercial (10)", lambda f: scenes_meta[f["scene_id"]] == "commercial_scenes"),
        ("All Scenes (30)", lambda f: True),
    ]
    cw = (px1 - px0) / len(clusters)
    bar_w = 18.8
    bar_gap = 2.6
    grp_w = len(active_models) * bar_w + (len(active_models) - 1) * bar_gap
    for ci, (cname, cfn) in enumerate(clusters):
        gx0 = px0 + (ci + 0.5) * cw - grp_w * 0.5
        for mi, (mkey, _, mcol, idx_m) in enumerate(active_models):
            both_v, either_v = _cluster_bars(idx_m, cfn)
            bx = gx0 + mi * (bar_w + bar_gap)
            eh = ph * min(either_v, YMAX) / YMAX
            bh = ph * min(both_v, YMAX) / YMAX
            # Tinted outer Union % bar
            wetop_u.add_rect(bm_stage, next_id(), f"bu-{ci}-{mkey}", bx, py_bot - eh, bar_w, eh, fill_hex=mcol, fill_alpha=20, line_hex=mcol, line_w_pt=0.75)
            # Solid inner Both-Hit % bar
            wetop_u.add_rect(bm_stage, next_id(), f"bb-{ci}-{mkey}", bx, py_bot - bh, bar_w, bh, fill_hex=mcol, line_hex=mcol, line_w_pt=0.4)
            # Union label on top
            wetop_u.add_textbox(bm_stage, next_id(), f"bt-{ci}-{mkey}", bx - 3.5, py_bot - eh - 9.2, bar_w + 7.0, 9.0, [{"text": f"{either_v:.0f}", "sz_pt": 7.0, "bold": True, "color": mcol}], algn="ctr")
            # Both-Hit integer inside solid bar
            wetop_u.add_textbox(bm_stage, next_id(), f"bi-{ci}-{mkey}", bx - 3.0, py_bot - bh * 0.5 - 5.0, bar_w + 6.0, 10.0, [{"text": f"{both_v:.0f}%", "sz_pt": 6.6, "bold": True, "color": "FFFFFF"}], algn="ctr")
        wetop_u.add_textbox(bm_stage, next_id(), f"bx-{ci}", px0 + ci * cw, py_bot + 1.8, cw, 13.0, [{"text": cname, "sz_pt": 8.0, "bold": True, "color": "0F172A"}], algn="ctr")

    panel_idx = next(
        i for i, ch in enumerate(spTree)
        if ch.find(f".//{{{P_NS}}}cNvPr") is not None and ch.find(f".//{{{P_NS}}}cNvPr").attrib.get("id") == "105"
    )
    for offset, elem in enumerate(list(bm_stage)):
        spTree.insert(panel_idx + 1 + offset, elem)

    entries["ppt/slides/slide1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_PPTX, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            if not name.endswith("/"):
                zout.writestr(name, data)
    print("[ok] wrote surgical WET-OP Fig 1 PPTX:", OUT_PPTX)

    if not args.no_com:
        _export_pptx_to_pdf_com(OUT_PPTX, OUT_PDF)
        print("[ok] exported vector PDF via PowerPoint COM:", OUT_PDF)
        PREVIEW_PNG.parent.mkdir(parents=True, exist_ok=True)
        pdftoppm_exe = Path(r"E:\my_program\texlive\2025\bin\windows\pdftoppm.exe")
        stem = PREVIEW_PNG.parent / "fig1_overview_page"
        subprocess.run([str(pdftoppm_exe), "-png", "-r", "240", str(OUT_PDF), str(stem)], check=True)
        src_png = Path(f"{stem}-1.png")
        if src_png.is_file():
            im = Image.open(src_png).convert("RGB")
            arr = np.asarray(im)
            nonwhite = np.where((arr < 252).any(axis=2))
            if len(nonwhite[0]) > 0:
                y0 = max(0, int(nonwhite[0].min()) - 8)
                y1 = min(arr.shape[0], int(nonwhite[0].max()) + 8)
                x0 = max(0, int(nonwhite[1].min()) - 8)
                x1 = min(arr.shape[1], int(nonwhite[1].max()) + 8)
                im = im.crop((x0, y0, x1, y1))
            im.save(PREVIEW_PNG)
            print("[ok] rendered high-DPI PNG preview:", PREVIEW_PNG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
