#!/usr/bin/env python3
"""Build a CVPR/SIGGRAPH-grade borderless horizontal pipeline Figure 3 (PPTX -> COM PDF).

Design philosophy ("zero AI smell"):
- Open white (#FFFFFF) 1000 x 320 pt borderless canvas divided solely by thin 0.65pt
  dashed vertical rules (#CBD5E1) across four causal stages (a)-(d).
- Zero nested pastel cards, zero candy-colored 1/2/3/4 circles, zero filler text walls.
- Anchored on held-out test Top-20% regression pair MVUCSQAKTKJ5EAABAAAAADI8_usd:35af5bf65c1e423e:v0
  (reflective black-glass gas cooktop; Qwen3-VL-32B Hit -> Miss, s_i flagged above tau_80).
- All optical maps (CIE Delta E*_ab, Sobel edge magnitude loss, 21-d standardized z-scores) and
  the 480-pair 30-scene LOSO risk score distribution are computed directly from frozen v3 data.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
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
from matplotlib.patches import Patch
import numpy as np
from PIL import Image, ImageDraw

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[4]
sys.path.insert(0, str(THIS_DIR))

from optical_and_risk_features import DEPLOY_AUTO_FEATURES, _sobel_mag  # noqa: E402
from v3_common import (  # noqa: E402
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    fit_standardized_l2_logreg,
    predict_proba_logreg,
    resolve_asset_path,
    srgb_uint8_to_lab,
)

V3_RAW_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_v3"
V1_META_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_formal/v1"
WETOP_ROOT = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\wetop_inspect\wet-op-cvpr2027-full-package"
)
WETOP_PPTX = WETOP_ROOT / "3_editable_figures_pptx/Figure1_WET-OP_Bench_Overview.pptx"
WETOP_HELPER = WETOP_ROOT / "4_scripts_and_data/update_fig1_pptx.py"

OUT_PPTX = REPO_ROOT / "paper/venues/cviu/figures/Figure3_ConvertAsset_Pipeline.pptx"
OUT_PDF = REPO_ROOT / "paper/venues/cviu/figures/fig3_pipeline.pdf"
PREVIEW_PNG = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\fig_previews\fig3_pipeline.png"
)

ANCHOR_PAIR_ID = "MVUCSQAKTKJ5EAABAAAAADI8_usd:35af5bf65c1e423e:v0"
SLIDE_W_PT = 1000.0
SLIDE_H_PT = 320.0
EMU_PER_PT = 12700

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

ET.register_namespace("p", P_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("r", R_NS)


def pt(val: float) -> str:
    return str(int(round(val * EMU_PER_PT)))


def _load_wetop_helpers():
    spec = importlib.util.spec_from_file_location("wetop_u", str(WETOP_HELPER))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _index_oc(path: Path) -> dict[tuple[str, str], dict]:
    return {
        (str(r["pair_id"]), str(r["condition"])): r
        for r in _read_jsonl(path)
        if r.get("status") == "ok"
    }


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


def _crop_window(mask: np.ndarray, *, target_aspect: float, pad_frac: float = 1.65) -> tuple[int, int, int, int]:
    """Compute a crisp geometry-locked crop box [y0:y1, x0:x1] around mask with target_aspect = w/h."""
    h, w = mask.shape
    ys, xs = np.where(mask)
    x_min, x_max = float(xs.min()), float(xs.max())
    y_min, y_max = float(ys.min()), float(ys.max())
    bw = x_max - x_min + 1.0
    bh = y_max - y_min + 1.0
    cx = 0.5 * (x_min + x_max)
    cy = 0.5 * (y_min + y_max)

    cw = max(bw * pad_frac, bh * pad_frac * target_aspect, 360.0)
    ch = cw / target_aspect
    if ch > h * 0.94:
        ch = h * 0.94
        cw = ch * target_aspect
    if cw > w * 0.94:
        cw = w * 0.94
        ch = cw / target_aspect

    x0 = int(round(max(0.0, min(w - cw, cx - 0.5 * cw))))
    y0 = int(round(max(0.0, min(h - ch, cy - 0.5 * ch))))
    x1 = min(w, int(round(x0 + cw)))
    y1 = min(h, int(round(y0 + ch)))
    return x0, y0, x1, y1


def _render_shader_ball(mode: str, size: int = 440) -> bytes:
    """Render a physically inspired multi-lobe MDL vs flattened Preview BRDF material sphere."""
    yy, xx = np.mgrid[-1.12:1.12:complex(size), -1.12:1.12:complex(size)]
    # Shift sphere up slightly to give room for soft contact shadow underneath
    sy = yy + 0.08
    sx = xx
    r2 = sx * sx + sy * sy

    # Soft ground contact shadow under sphere center (0, 0.90)
    sh_d2 = (sx / 0.72) ** 2 + ((yy - 0.92) / 0.14) ** 2
    sh_alpha = np.exp(-2.3 * sh_d2) * (0.28 if mode == "mdl" else 0.16)

    inside = r2 < 1.0
    r = np.sqrt(np.clip(r2, 0.0, 10.0))
    # Antialiased coverage mask (1.0 inside, smooth falloff over 0.014 radius)
    cov = np.clip((1.007 - r) / 0.014, 0.0, 1.0)

    nz = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))
    nx, ny = sx, -sy  # +y up in reflection coordinates
    # View vector v = (0, 0, 1)
    ndotv = np.clip(nz, 0.0, 1.0)

    # Studio environment reflection direction R = 2(N.V)N - V = (2*nz*nx, 2*nz*ny, 2*nz^2 - 1)
    rx = 2.0 * nz * nx
    ry = 2.0 * nz * ny
    rz = 2.0 * nz * nz - 1.0

    # Key light from upper-left front, rim from upper-right
    l1 = np.array([-0.50, 0.62, 0.60])
    l1 /= np.linalg.norm(l1)
    l2 = np.array([0.62, 0.45, 0.64])
    l2 /= np.linalg.norm(l2)
    h1 = l1 + np.array([0.0, 0.0, 1.0])
    h1 /= np.linalg.norm(h1)
    h2 = l2 + np.array([0.0, 0.0, 1.0])
    h2 /= np.linalg.norm(h2)

    ndotl1 = np.clip(nx * l1[0] + ny * l1[1] + nz * l1[2], 0.0, 1.0)
    ndotl2 = np.clip(nx * l2[0] + ny * l2[1] + nz * l2[2], 0.0, 1.0)
    ndoth1 = np.clip(nx * h1[0] + ny * h1[1] + nz * h1[2], 0.0, 1.0)
    ndoth2 = np.clip(nx * h2[0] + ny * h2[1] + nz * h2[2], 0.0, 1.0)

    if mode == "mdl":
        # Rich obsidian reflective glass/ceramic coat + crisp studio softbox + sharp GGX glints
        fresnel = 0.22 + 0.78 * ((1.0 - ndotv) ** 3.8)
        # Sharp upper-left studio softbox window + cool sky fill + horizon reflection band
        softbox = np.exp(-((((rx + 0.34) / 0.22) ** 4) + (((ry - 0.54) / 0.16) ** 4)) * 1.8)
        softbox2 = 0.80 * np.exp(-(((rx - 0.52) / 0.18) ** 2 + ((ry - 0.34) / 0.24) ** 2) * 3.2)
        horizon = 0.36 * np.exp(-((ry - 0.02) / 0.14) ** 2) * (0.45 + 0.55 * np.tanh(rz * 1.4))
        env = softbox[:, :, None] * np.array([1.0, 0.99, 0.97])[None, None, :] + softbox2[:, :, None] * np.array([0.82, 0.91, 1.0])[None, None, :]
        env += horizon[:, :, None] * np.array([0.60, 0.72, 0.88])[None, None, :]

        base = np.array([0.045, 0.065, 0.095])[None, None, :]
        diff = base * (0.40 + 1.25 * ndotl1[:, :, None] + 0.50 * ndotl2[:, :, None])
        spec1 = 1.65 * (ndoth1 ** 95)[:, :, None] * np.array([1.0, 0.99, 0.97])[None, None, :]
        spec2 = 0.65 * (ndoth2 ** 60)[:, :, None] * np.array([0.85, 0.94, 1.0])[None, None, :]
        rgb_lin = diff + fresnel[:, :, None] * (0.95 * env) + (0.42 + 0.58 * fresnel[:, :, None]) * (spec1 + spec2)
        # Subtle cyan-slate rim highlight separating dark obsidian from white background
        rgb_lin += ((1.0 - ndotv) ** 3.6)[:, :, None] * 0.30 * np.array([0.68, 0.80, 0.94])[None, None, :]
        # Hairline crisp outer contour
        rim_edge = np.clip((r - 0.965) / 0.035, 0.0, 1.0) * inside
        rgb_lin = rgb_lin * (1.0 - 0.25 * rim_edge[:, :, None])
    else:
        # Flattened UsdPreviewSurface matte slate-gray proxy (collapsed reflections & washed coat)
        base = np.array([0.43, 0.45, 0.49])[None, None, :]
        diff = base * (0.38 + 0.52 * ndotl1[:, :, None] + 0.18 * ndotl2[:, :, None])
        broad_spec = 0.09 * (ndoth1 ** 9)[:, :, None]
        fres_soft = 0.05 * ((1.0 - ndotv) ** 3.0)[:, :, None]
        rgb_lin = diff + broad_spec + fres_soft

    rgb_srgb = np.clip(np.where(rgb_lin <= 0.0031308, 12.92 * rgb_lin, 1.055 * (np.clip(rgb_lin, 0.0, 1.0) ** (1.0 / 2.4)) - 0.055), 0.0, 1.0)

    # Composite over transparent background + soft contact shadow
    out = np.zeros((size, size, 4), dtype=np.float64)
    sh_rgb = np.array([0.06, 0.09, 0.16])[None, None, :]
    out[:, :, :3] = sh_rgb * (1.0 - cov[:, :, None]) + rgb_srgb * cov[:, :, None]
    out[:, :, 3] = np.clip(np.maximum(cov, sh_alpha * (1.0 - cov * 0.9)), 0.0, 1.0)
    rgba = np.clip(np.rint(out * 255.0), 0.0, 255.0).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG")
    return buf.getvalue()


def _render_paired_plate(
    img_path: Path,
    mask_crop: np.ndarray,
    *,
    crop_box: tuple[int, int, int, int],
    pred_norm: list[float],
    is_hit: bool,
    tag_text: str,
    prev_pred_norm: list[float] | None = None,
) -> bytes:
    """Render a crisp sharp-edged render plate with subtle mask contour, Qwen3-VL-32B pin, and corner label."""
    x0, y0, x1, y1 = crop_box
    cw, ch = x1 - x0, y1 - y0
    im = np.asarray(Image.open(img_path).convert("RGB"))[y0:y1, x0:x1]

    fig = plt.figure(figsize=(3.35, 3.35 * ch / cw), dpi=200)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.imshow(im)
    if mask_crop.any():
        ax.contour(mask_crop.astype(float), levels=[0.5], colors=["#0F172A"], linewidths=1.35, alpha=0.55, zorder=3)
        ax.contour(mask_crop.astype(float), levels=[0.5], colors=["#FFFFFF"], linewidths=0.85, linestyles="--", alpha=0.92, zorder=4)

    px = min(max(float(pred_norm[0]) * IMAGE_WIDTH / 1000.0 - x0, 10.0), cw - 10.0)
    py = min(max(float(pred_norm[1]) * IMAGE_HEIGHT / 1000.0 - y0, 10.0), ch - 10.0)

    if prev_pred_norm is not None:
        ox = min(max(float(prev_pred_norm[0]) * IMAGE_WIDTH / 1000.0 - x0, 10.0), cw - 10.0)
        oy = min(max(float(prev_pred_norm[1]) * IMAGE_HEIGHT / 1000.0 - y0, 10.0), ch - 10.0)
        ax.plot([ox, px], [oy, py], linestyle="-", linewidth=2.2, color="white", alpha=0.85, zorder=4)
        ax.plot([ox, px], [oy, py], linestyle=":", linewidth=1.5, color="#DC2626", zorder=5)
        ax.scatter([ox], [oy], s=48, marker="o", facecolor="none", edgecolor="white", linewidths=2.2, zorder=5)
        ax.scatter([ox], [oy], s=48, marker="o", facecolor="none", edgecolor="#0F766E", linewidths=1.2, zorder=5)

    col = "#0F766E" if is_hit else "#DC2626"
    marker = "o" if is_hit else "X"
    ax.scatter([px], [py], s=140 if is_hit else 160, marker=marker, color=col, edgecolors="white", linewidths=1.6, zorder=6)

    # Clean minimal top-left white translucent plate tag (no rounded candy pill)
    ax.text(
        0.028,
        0.95,
        tag_text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.2,
        fontweight="bold",
        fontfamily="Arial",
        color="#0F172A" if is_hit else "#991B1B",
        bbox=dict(boxstyle="square,pad=0.22", facecolor="white", edgecolor="#CBD5E1" if is_hit else "#FECACA", alpha=0.92, lw=0.7),
        zorder=8,
    )
    ax.set_xlim(0, cw)
    ax.set_ylim(ch, 0)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    return buf.getvalue()


def _render_mask_plate(mask_crop: np.ndarray, *, full_mask: np.ndarray, crop_box: tuple[int, int, int, int], d_norm: float) -> bytes:
    """Render simulator binary target mask M_i^v on #0F172A with bbox & center-offset vector."""
    x0, y0, x1, y1 = crop_box
    cw, ch = x1 - x0, y1 - y0

    fig = plt.figure(figsize=(2.4, 2.4 * ch / cw), dpi=200)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], facecolor="#0F172A")
    # Paint dark slate canvas + crisp cool-white binary silhouette
    canvas = np.zeros((ch, cw, 3), dtype=np.float32)
    canvas[:, :] = np.array([15, 23, 42], dtype=np.float32) / 255.0
    canvas[mask_crop] = np.array([241, 245, 249], dtype=np.float32) / 255.0
    ax.imshow(canvas)

    ys, xs = np.where(mask_crop)
    bx0, bx1 = xs.min(), xs.max()
    by0, by1 = ys.min(), ys.max()
    cx_m, cy_m = float(xs.mean()), float(ys.mean())
    cx_img, cy_img = 0.5 * IMAGE_WIDTH - x0, 0.5 * IMAGE_HEIGHT - y0

    # Dashed bounding box & centroid offset arrow
    rect = plt.Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, edgecolor="#38BDF8", linewidth=1.2, linestyle="--", zorder=4)
    ax.add_patch(rect)
    ax.plot([cx_img, cx_m], [cy_img, cy_m], color="#38BDF8", linewidth=1.3, linestyle="-", zorder=5)
    ax.scatter([cx_m], [cy_m], s=36, color="#38BDF8", edgecolor="#0F172A", linewidths=0.8, zorder=6)
    ax.scatter([cx_img], [cy_img], s=32, marker="+", color="#CBD5E1", linewidths=1.2, zorder=5)
    ax.text(
        0.04,
        0.94,
        r"$M_i^v$",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        fontweight="bold",
        fontfamily="Arial",
        color="#F8FAFC",
        zorder=7,
    )
    ax.text(
        0.96,
        0.06,
        rf"$d={d_norm:.2f}$",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.6,
        fontfamily="Arial",
        color="#7DD3FC",
        zorder=7,
    )
    ax.set_xlim(0, cw)
    ax.set_ylim(ch, 0)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    return buf.getvalue()


def _render_delta_e_map(orig_rgb: np.ndarray, conv_rgb: np.ndarray, mask_full: np.ndarray, crop_box: tuple[int, int, int, int]) -> bytes:
    """Compute true pixelwise CIE Delta E*_ab heatmap inside crop + magma colorbar."""
    x0, y0, x1, y1 = crop_box
    o_c = orig_rgb[y0:y1, x0:x1]
    c_c = conv_rgb[y0:y1, x0:x1]
    m_c = mask_full[y0:y1, x0:x1]

    o_lab, _ = srgb_uint8_to_lab(o_c)
    c_lab, _ = srgb_uint8_to_lab(c_c)
    delta_e = np.linalg.norm(o_lab - c_lab, axis=-1)
    vmax = float(max(50.0, np.quantile(delta_e, 0.99)))

    fig = plt.figure(figsize=(2.8, 1.72), dpi=220)
    ax = fig.add_axes([0.01, 0.02, 0.80, 0.96])
    im_h = ax.imshow(delta_e, cmap="magma", vmin=0.0, vmax=vmax)
    if m_c.any():
        ax.contour(m_c.astype(float), levels=[0.5], colors=["#FFFFFF"], linewidths=1.0, linestyles="--", alpha=0.9)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor("#64748B")
        sp.set_linewidth(0.8)

    cax = fig.add_axes([0.835, 0.10, 0.045, 0.80])
    cb = fig.colorbar(im_h, cax=cax)
    cb.ax.tick_params(labelsize=6.8, length=2, pad=2, colors="#334155")
    cb.set_ticks([0, int(round(vmax / 2)), int(round(vmax))])
    cb.outline.set_edgecolor("#94A3B8")
    cb.outline.set_linewidth(0.6)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220, facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _render_sobel_loss_map(orig_rgb: np.ndarray, conv_rgb: np.ndarray, mask_full: np.ndarray, crop_box: tuple[int, int, int, int]) -> bytes:
    """Compute true Sobel edge-magnitude delta |nabla I^O| - |nabla I^C| heatmap + RdBu_r colorbar."""
    x0, y0, x1, y1 = crop_box
    o_lab, _ = srgb_uint8_to_lab(orig_rgb[y0:y1, x0:x1])
    c_lab, _ = srgb_uint8_to_lab(conv_rgb[y0:y1, x0:x1])
    sob_o = _sobel_mag(o_lab[:, :, 0])
    sob_c = _sobel_mag(c_lab[:, :, 0])
    edge_drop = sob_o - sob_c  # >0 = edges lost/flattened upon shader conversion
    m_c = mask_full[y0:y1, x0:x1]
    vlim = float(max(8.0, np.quantile(np.abs(edge_drop), 0.985)))

    fig = plt.figure(figsize=(2.8, 1.72), dpi=220)
    ax = fig.add_axes([0.01, 0.02, 0.80, 0.96])
    im_h = ax.imshow(edge_drop, cmap="RdBu_r", vmin=-vlim, vmax=vlim)
    if m_c.any():
        ax.contour(m_c.astype(float), levels=[0.5], colors=["#0F172A"], linewidths=0.95, linestyles="--", alpha=0.8)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor("#64748B")
        sp.set_linewidth(0.8)

    cax = fig.add_axes([0.835, 0.10, 0.045, 0.80])
    cb = fig.colorbar(im_h, cax=cax)
    cb.ax.tick_params(labelsize=6.6, length=2, pad=2, colors="#334155")
    cb.set_ticks([-int(round(vlim)), 0, int(round(vlim))])
    cb.outline.set_edgecolor("#94A3B8")
    cb.outline.set_linewidth(0.6)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220, facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _render_geom_prior_plate(area_frac: float, aspect: float, d_norm: float) -> bytes:
    """Render clean vector schematic showing target geometry cues + 4 optical regime indicators [RM | TG | MD | ES]."""
    fig = plt.figure(figsize=(2.8, 1.72), dpi=220)
    ax = fig.add_axes([0.01, 0.02, 0.80, 0.96], facecolor="#F8FAFC")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)

    # Top area: Normalized image frame [1024 x 768] showing bbox aspect & center offset d_norm
    ax.add_patch(plt.Rectangle((0.6, 2.35), 8.8, 4.1, fill=True, facecolor="#FFFFFF", edgecolor="#CBD5E1", lw=0.8))
    ax.scatter([5.0], [4.4], s=18, marker="+", color="#94A3B8", lw=0.9, zorder=3)
    # Target box at left-center matching cooktop framing
    ax.add_patch(plt.Rectangle((1.8, 3.05), 3.1, 1.55, fill=True, facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.0, zorder=4))
    ax.scatter([3.35], [3.82], s=18, color="#0F172A", zorder=5)
    ax.plot([5.0, 3.35], [4.4, 3.82], color="#0F766E", lw=1.1, ls="--", zorder=5)
    ax.text(4.35, 4.98, r"$d_{\mathrm{norm}}$", fontsize=7.2, fontweight="bold", color="#0F766E", ha="center", fontfamily="Arial")
    ax.text(6.9, 4.4, f"area={area_frac*100:.1f}%\nw/h={aspect:.2f}", fontsize=6.8, color="#334155", va="center", ha="center", fontfamily="Arial")

    # Bottom row: 4 optical regime indicator switches [RM | TG | MD | ES]
    regimes = [("RM", True), ("TG", False), ("MD", False), ("ES", False)]
    for i, (lbl, active) in enumerate(regimes):
        bx = 0.6 + i * 2.25
        fc = "#0F172A" if active else "#FFFFFF"
        tc = "#FFFFFF" if active else "#64748B"
        ec = "#0F172A" if active else "#CBD5E1"
        ax.add_patch(plt.Rectangle((bx, 0.45), 2.05, 1.35, fill=True, facecolor=fc, edgecolor=ec, lw=0.85))
        ax.text(bx + 1.025, 1.125, lbl, fontsize=7.4, fontweight="bold", color=tc, ha="center", va="center", fontfamily="Arial")

    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor("#CBD5E1")
        sp.set_linewidth(0.75)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220, facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _render_feature_barcode(z_vec: np.ndarray) -> bytes:
    """Render 21-cell vertical standardized z-score barcode (13 Optical | 5 Geom | 3 Prior)."""
    fig = plt.figure(figsize=(0.55, 4.4), dpi=240)
    ax = fig.add_axes([0.08, 0.02, 0.84, 0.96])
    data = z_vec.reshape(-1, 1)
    ax.imshow(data, cmap="RdBu_r", vmin=-2.8, vmax=2.8, aspect="auto", interpolation="nearest")

    n = len(z_vec)
    for y_sep in np.arange(0.5, n - 0.5, 1.0):
        ax.axhline(y_sep, color="white", lw=0.7)
    # Stronger separators between Optical (13), Geom (5), and Prior (3) blocks
    ax.axhline(12.5, color="#0F172A", lw=1.4)
    ax.axhline(17.5, color="#0F172A", lw=1.4)

    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor("#0F172A")
        sp.set_linewidth(1.1)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=240, facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _render_risk_distribution(
    loso_scores: np.ndarray,
    y_true: np.ndarray,
    anchor_loso_score: float,
    anchor_test_score: float,
    test_tau80: float,
) -> bytes:
    """Render Tufte-style 480-pair LOSO risk-score distribution split at tau_80 with sample pin."""
    tau_loso = float(np.quantile(loso_scores, 0.80))
    # Cap visualization x-range cleanly at 0.140 while keeping extremes inside final bin
    x_min, x_max = 0.015, 0.140
    clipped = np.clip(loso_scores, x_min, x_max - 1e-4)
    bins = np.linspace(x_min, x_max, 22)

    fig = plt.figure(figsize=(4.4, 2.72), dpi=260)
    ax = fig.add_axes([0.13, 0.21, 0.84, 0.72], facecolor="white")

    counts_all, edges = np.histogram(clipped, bins=bins)
    counts_pos, _ = np.histogram(clipped[y_true == 1], bins=bins)
    centers = 0.5 * (edges[:-1] + edges[1:])
    width = (edges[1] - edges[0]) * 0.86

    # Shaded Top-20% risk zone background
    ax.axvspan(tau_loso, x_max, color="#FFF1F2", alpha=0.85, zorder=0)

    for c_x, n_all, n_pos, x_l, x_r in zip(centers, counts_all, counts_pos, edges[:-1], edges[1:]):
        flagged_bin = 0.5 * (x_l + x_r) >= tau_loso
        fc = "#FDA4AF" if flagged_bin else "#CBD5E1"
        ec = "#E11D48" if flagged_bin else "#94A3B8"
        if n_all > 0:
            ax.bar(c_x, n_all, width=width, color=fc, edgecolor=ec, linewidth=0.55, zorder=2)
        if n_pos > 0:
            ax.bar(c_x, n_pos, width=width, color="#991B1B", edgecolor="#7F1D1D", linewidth=0.5, zorder=3)

    ymax = max(counts_all.max() * 1.15, 10)
    ax.axvline(tau_loso, color="#0F172A", linestyle="--", linewidth=1.25, zorder=5)
    ax.text(
        tau_loso + 0.002,
        ymax * 0.94,
        rf"$\tau_{{80}}={tau_loso:.3f}$",
        fontsize=8.0,
        fontweight="bold",
        fontfamily="Arial",
        color="#0F172A",
        ha="left",
        va="top",
        zorder=6,
    )

    # Sample s_i pin (anchored right at anchor_loso_score)
    sx = min(anchor_loso_score, x_max - 0.005)
    ax.plot([sx, sx], [0, ymax * 0.62], color="#B91C1C", lw=1.4, zorder=6)
    ax.scatter([sx], [ymax * 0.62], s=38, color="#B91C1C", edgecolor="white", linewidths=0.8, zorder=7)
    ax.text(
        sx - 0.003,
        ymax * 0.66,
        f"Sample $s_i$\n({anchor_test_score:.3f}>{test_tau80:.3f} test)",
        fontsize=6.9,
        fontweight="bold",
        fontfamily="Arial",
        color="#991B1B",
        ha="center",
        va="bottom",
        zorder=7,
    )

    # Zone headers inside plot
    ax.text(0.036, ymax * 0.94, "80% Auto-Admit", fontsize=7.6, fontweight="bold", fontfamily="Arial", color="#475569", ha="center", va="top")
    ax.text(0.112, ymax * 0.94, "Top-20%", fontsize=7.6, fontweight="bold", fontfamily="Arial", color="#B91C1C", ha="center", va="top")

    # Legend swatch in corner for true regressions (explicit Patch so swatch color is dark crimson #991B1B)
    loss_patch = Patch(facecolor="#991B1B", edgecolor="#7F1D1D", linewidth=0.5, label="Actual Loss (y=1)")
    ax.legend(handles=[loss_patch], loc="center right", bbox_to_anchor=(1.0, 0.36), frameon=False, fontsize=6.7, handlelength=1.1, handletextpad=0.4)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(0, ymax)
    ax.set_xlabel(r"Predicted Risk Score $s_i = \sigma(\mathbf{w}^\top \mathbf{x}_i + b)$ [480 LOSO]", fontsize=7.3, fontfamily="Arial", color="#334155", labelpad=3)
    ax.set_ylabel("Pairs", fontsize=7.6, fontfamily="Arial", color="#334155", labelpad=3)
    ax.set_xticks([0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14])
    ax.set_xticklabels([".02", ".04", ".06", ".08", ".10", ".12", r"$\geq$.14"], fontsize=7.0, fontfamily="Arial", color="#475569")
    ax.tick_params(axis="y", labelsize=7.0, colors="#475569", length=2.5, pad=2)
    ax.tick_params(axis="x", length=2.5, pad=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#475569")
    ax.spines["bottom"].set_color("#475569")
    ax.spines["left"].set_linewidth(0.75)
    ax.spines["bottom"].set_linewidth(0.75)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=260, facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _add_arrow(wetop_u, spTree, sid: int, name: str, x1: float, y1: float, x2: float, y2: float,
               *, line_hex: str = "334155", line_w_pt: float = 0.9, dash: str | None = None, head: bool = True) -> ET.Element:
    cxn = wetop_u.add_line(spTree, sid, name, x1, y1, x2, y2, line_hex=line_hex, line_w_pt=line_w_pt, dash=dash)
    if head:
        ln = cxn.find(f".//{{{A_NS}}}ln")
        if ln is not None:
            ET.SubElement(ln, f"{{{A_NS}}}tailEnd", type="triangle", w="med", len="med")
    return cxn


def _add_pic(spTree, sid: int, name: str, x: float, y: float, w: float, h: float, rid: str,
             *, border_hex: str | None = None, border_w_pt: float = 0.75) -> ET.Element:
    pic = ET.SubElement(spTree, f"{{{P_NS}}}pic")
    nvPicPr = ET.SubElement(pic, f"{{{P_NS}}}nvPicPr")
    ET.SubElement(nvPicPr, f"{{{P_NS}}}cNvPr", id=str(sid), name=name)
    nvPicPr_c = ET.SubElement(nvPicPr, f"{{{P_NS}}}cNvPicPr")
    ET.SubElement(nvPicPr_c, f"{{{A_NS}}}picLocks", noChangeAspect="1")
    ET.SubElement(nvPicPr, f"{{{P_NS}}}nvPr")

    bf = ET.SubElement(pic, f"{{{P_NS}}}blipFill")
    blip = ET.SubElement(bf, f"{{{A_NS}}}blip")
    blip.attrib[f"{{{R_NS}}}embed"] = rid
    st = ET.SubElement(bf, f"{{{A_NS}}}stretch")
    ET.SubElement(st, f"{{{A_NS}}}fillRect")

    spPr = ET.SubElement(pic, f"{{{P_NS}}}spPr")
    xf = ET.SubElement(spPr, f"{{{A_NS}}}xfrm")
    ET.SubElement(xf, f"{{{A_NS}}}off", x=pt(x), y=pt(y))
    ET.SubElement(xf, f"{{{A_NS}}}ext", cx=pt(w), cy=pt(h))
    prst = ET.SubElement(spPr, f"{{{A_NS}}}prstGeom", prst="rect")
    ET.SubElement(prst, f"{{{A_NS}}}avLst")
    if border_hex:
        ln = ET.SubElement(spPr, f"{{{A_NS}}}ln", w=pt(border_w_pt))
        sf = ET.SubElement(ln, f"{{{A_NS}}}solidFill")
        ET.SubElement(sf, f"{{{A_NS}}}srgbClr", val=border_hex)
    return pic


def _add_framed_label_box(
    wetop_u,
    spTree,
    next_id_fn,
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    lines_spec: list[tuple[str, float, bool, str]],
    *,
    fill_hex: str = "F8FAFC",
    line_hex: str = "475569",
    line_w_pt: float = 0.75,
    dash: str | None = None,
    algn: str = "ctr",
) -> None:
    """Create a crisp rectangle (sharp edges, optional dash) with vertically centered lines of text."""
    sp = wetop_u.add_rect(spTree, next_id_fn(), f"{name}-box", x, y, w, h, fill_hex=fill_hex, line_hex=line_hex, line_w_pt=line_w_pt)
    if dash:
        ln = sp.find(f".//{{{A_NS}}}ln")
        if ln is not None:
            ET.SubElement(ln, f"{{{A_NS}}}prstDash", val=dash)
    if len(lines_spec) == 1:
        txt, sz, bold, col = lines_spec[0]
        wetop_u.add_textbox(
            spTree, next_id_fn(), f"{name}-t", x + 2.0, y, w - 4.0, h,
            [{"text": txt, "sz_pt": sz, "bold": bold, "color": col}],
            algn=algn, anchor="ctr",
        )
    else:
        step_y = h / len(lines_spec)
        for idx, (txt, sz, bold, col) in enumerate(lines_spec):
            wetop_u.add_textbox(
                spTree, next_id_fn(), f"{name}-t{idx}", x + 2.0, y + idx * step_y + 1.0, w - 4.0, step_y - 1.0,
                [{"text": txt, "sz_pt": sz, "bold": bold, "color": col}],
                algn=algn, anchor="ctr",
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-root", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\assets\cviu"))
    parser.add_argument("--v1-runs-dir", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\assets\cviu\formal_model_runs_v1"))
    parser.add_argument("--no-com", action="store_true", help="Write PPTX only without PowerPoint COM PDF export.")
    args = parser.parse_args()

    wetop_u = _load_wetop_helpers()

    # Load frozen CVIU v3 data + fit standardized L2 logistic risk gate identically to analyze_v3_all.py
    feats = json.loads((V3_RAW_DIR / "pair_optical_features.json").read_text(encoding="utf-8"))["records"]
    manifest = json.loads((V1_META_DIR / "manifest.json").read_text(encoding="utf-8"))["records"]
    m_by_oc = {(r["pair_id"], r["condition"]): r for r in manifest}
    idx8 = _index_oc(args.v1_runs_dir / "8b/formal_repeat0/predictions.jsonl")
    idx32 = _index_oc(args.v1_runs_dir / "32b/formal_repeat0/predictions.jsonl")

    # Group DEPLOY_AUTO_FEATURES semantically into top->bottom Optical (13), Geom (5), Prior (3)
    geom_cols = ["log_area_frac", "aspect_ratio", "center_dist_norm", "border_touch", "mask_iou"]
    prior_cols = [c for c in DEPLOY_AUTO_FEATURES if c.startswith("cat_is_")]
    opt_cols = [c for c in DEPLOY_AUTO_FEATURES if c not in geom_cols and c not in prior_cols]
    ordered_cols = opt_cols + geom_cols + prior_cols
    assert len(ordered_cols) == 21

    X = np.array([[float(r[c]) for c in DEPLOY_AUTO_FEATURES] for r in feats], dtype=np.float64)
    X_ord = np.array([[float(r[c]) for c in ordered_cols] for r in feats], dtype=np.float64)
    y = np.array(
        [
            int(
                (bool(idx8[(r["pair_id"], "original")]["hit"]) and not bool(idx8[(r["pair_id"], "converted")]["hit"]))
                or (bool(idx32[(r["pair_id"], "original")]["hit"]) and not bool(idx32[(r["pair_id"], "converted")]["hit"]))
            )
            for r in feats
        ],
        dtype=np.int64,
    )
    train_idx = [i for i, r in enumerate(feats) if r["split"] == "train"]
    test_idx = [i for i, r in enumerate(feats) if r["split"] == "test"]

    train_fit = fit_standardized_l2_logreg(X[train_idx], y[train_idx], c_reg=0.01)
    test_scores = predict_proba_logreg(train_fit, X[test_idx])
    tau80_test = float(np.quantile(test_scores, 0.80))

    # 30-scene LOSO scores
    scenes = sorted(set(r["scene_id"] for r in feats))
    loso_scores = np.zeros(len(feats), dtype=np.float64)
    for sc in scenes:
        tr_i = [i for i, r in enumerate(feats) if r["scene_id"] != sc]
        te_i = [i for i, r in enumerate(feats) if r["scene_id"] == sc]
        fold_m = fit_standardized_l2_logreg(X[tr_i], y[tr_i], c_reg=0.01)
        loso_scores[te_i] = predict_proba_logreg(fold_m, X[te_i])

    # Anchor pair stats + standardization against train split
    anch_idx = next(i for i, r in enumerate(feats) if r["pair_id"] == ANCHOR_PAIR_ID)
    anch = feats[anch_idx]
    anch_test_score = float(predict_proba_logreg(train_fit, X[anch_idx : anch_idx + 1])[0])
    anch_loso_score = float(loso_scores[anch_idx])

    ord_mean = X_ord[train_idx].mean(axis=0)
    ord_std = np.where(X_ord[train_idx].std(axis=0) > 1e-8, X_ord[train_idx].std(axis=0), 1.0)
    z_vec = (X_ord[anch_idx] - ord_mean) / ord_std

    # Load anchor renders & binary masks
    rec_o = m_by_oc[(ANCHOR_PAIR_ID, "original")]
    rec_c = m_by_oc[(ANCHOR_PAIR_ID, "converted")]
    img_o_p = resolve_asset_path(rec_o["image"]["path"], args.assets_root)
    img_c_p = resolve_asset_path(rec_c["image"]["path"], args.assets_root)
    msk_o_p = resolve_asset_path(rec_o["mask"]["path"], args.assets_root)
    orig_rgb = np.asarray(Image.open(img_o_p).convert("RGB"))
    conv_rgb = np.asarray(Image.open(img_c_p).convert("RGB"))
    mask_full = (np.load(msk_o_p) > 0) if msk_o_p.suffix == ".npy" else (np.asarray(Image.open(msk_o_p).convert("L")) > 0)

    crop_box = _crop_window(mask_full, target_aspect=134.0 / 96.0, pad_frac=1.68)
    mask_crop = mask_full[crop_box[1] : crop_box[3], crop_box[0] : crop_box[2]]

    p32_o = idx32[(ANCHOR_PAIR_ID, "original")]
    p32_c = idx32[(ANCHOR_PAIR_ID, "converted")]

    # Generate all high-DPI sub-images
    media_bytes: dict[str, bytes] = {
        "ppt/media/fig3_ball_mdl.png": _render_shader_ball("mdl"),
        "ppt/media/fig3_ball_prev.png": _render_shader_ball("preview"),
        "ppt/media/fig3_plate_o.png": _render_paired_plate(
            img_o_p, mask_crop, crop_box=crop_box,
            pred_norm=p32_o["point_normalized"], is_hit=bool(p32_o["hit"]),
            tag_text=r"$I_i^O$ (MDL) $\cdot$ Hit",
        ),
        "ppt/media/fig3_plate_c.png": _render_paired_plate(
            img_c_p, mask_crop, crop_box=crop_box,
            pred_norm=p32_c["point_normalized"], is_hit=bool(p32_c["hit"]),
            tag_text=r"$I_i^C$ (Preview) $\cdot$ Miss",
            prev_pred_norm=p32_o["point_normalized"],
        ),
        "ppt/media/fig3_mask.png": _render_mask_plate(
            mask_crop, full_mask=mask_full, crop_box=crop_box, d_norm=float(anch["center_dist_norm"])
        ),
        "ppt/media/fig3_delta_e.png": _render_delta_e_map(orig_rgb, conv_rgb, mask_full, crop_box),
        "ppt/media/fig3_sobel.png": _render_sobel_loss_map(orig_rgb, conv_rgb, mask_full, crop_box),
        "ppt/media/fig3_geom_prior.png": _render_geom_prior_plate(
            area_frac=math.exp(float(anch["log_area_frac"])),
            aspect=float(anch["aspect_ratio"]),
            d_norm=float(anch["center_dist_norm"]),
        ),
        "ppt/media/fig3_barcode.png": _render_feature_barcode(z_vec),
        "ppt/media/fig3_hist.png": _render_risk_distribution(
            loso_scores, y, anch_loso_score, anch_test_score, tau80_test
        ),
    }

    # Open clean WET-OP PPTX container and strip slide1/media to blank pure-white 1000x320pt canvas
    with zipfile.ZipFile(WETOP_PPTX, "r") as zin:
        entries = {info.filename: zin.read(info.filename) for info in zin.infolist() if not info.filename.startswith("ppt/media/")}

    # Update slide dimensions to 1000 x 320 pt & drop guide extensions
    pres_root = ET.fromstring(entries["ppt/presentation.xml"])
    sldSz = pres_root.find(f"{{{P_NS}}}sldSz")
    if sldSz is not None:
        sldSz.attrib["cx"] = pt(SLIDE_W_PT)
        sldSz.attrib["cy"] = pt(SLIDE_H_PT)
        sldSz.attrib["type"] = "custom"
    extLst = pres_root.find(f"{{{P_NS}}}extLst")
    if extLst is not None:
        pres_root.remove(extLst)
    entries["ppt/presentation.xml"] = ET.tostring(pres_root, encoding="utf-8", xml_declaration=True)

    # Rebuild slide1.xml.rels keeping only layout & notesSlide, appending new fig3_* PNG rels
    rels_root = ET.fromstring(entries["ppt/slides/_rels/slide1.xml.rels"])
    for rel in list(rels_root):
        if "media/" in rel.attrib.get("Target", ""):
            rels_root.remove(rel)
    media_rids: dict[str, str] = {}
    for idx_m, m_path in enumerate(media_bytes, start=10):
        rid = f"rId{idx_m}"
        ET.SubElement(
            rels_root,
            f"{{{RELS_NS}}}Relationship",
            Id=rid,
            Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
            Target=f"../{m_path[4:]}",
        )
        media_rids[m_path] = rid
    entries["ppt/slides/_rels/slide1.xml.rels"] = ET.tostring(rels_root, encoding="utf-8", xml_declaration=True)
    for m_path, m_data in media_bytes.items():
        entries[m_path] = m_data

    # Clean slide1.xml and force pure #FFFFFF background
    slide_root = ET.fromstring(entries["ppt/slides/slide1.xml"])
    cSld = slide_root.find(f"{{{P_NS}}}cSld")
    assert cSld is not None
    old_bg = cSld.find(f"{{{P_NS}}}bg")
    if old_bg is not None:
        cSld.remove(old_bg)
    bg = ET.Element(f"{{{P_NS}}}bg")
    bgPr = ET.SubElement(bg, f"{{{P_NS}}}bgPr")
    sf = ET.SubElement(bgPr, f"{{{A_NS}}}solidFill")
    ET.SubElement(sf, f"{{{A_NS}}}srgbClr", val="FFFFFF")
    ET.SubElement(bgPr, f"{{{A_NS}}}effectLst")
    cSld.insert(0, bg)

    spTree = cSld.find(f"{{{P_NS}}}spTree")
    assert spTree is not None
    for ch in list(spTree):
        tag = ch.tag.split("}")[-1]
        if tag not in ("nvGrpSpPr", "grpSpPr"):
            spTree.remove(ch)

    id_counter = [100]

    def next_id() -> int:
        id_counter[0] += 1
        return id_counter[0]

    # =========================================================================
    # Open Column Dashed Hairline Separators & Stage Headers (a)-(d)
    # =========================================================================
    for di, dx in enumerate((222.0, 472.0, 754.0)):
        wetop_u.add_line(spTree, next_id(), f"col-sep-{di}", dx, 12.0, dx, 276.0, line_hex="CBD5E1", line_w_pt=0.70, dash="dash")

    headers = [
        (12.0,  208.0, "(a) USD Scene & Shader Lowering"),
        (232.0, 236.0, "(b) Geometry-Locked Paired Renders"),
        (482.0, 266.0, "(c) Zero-VLM Optical & Geometric Maps"),
        (764.0, 228.0, "(d) Family-Calibrated Risk Gate"),
    ]
    for hi, (hx, hw, htxt) in enumerate(headers):
        wetop_u.add_textbox(
            spTree, next_id(), f"hdr-{hi}", hx, 8.0, hw, 18.0,
            [{"text": htxt, "sz_pt": 11.2, "bold": True, "color": "0F172A"}],
            algn="l", anchor="ctr",
        )

    # =========================================================================
    # Stage (a): USD Scene & Shader Lowering (x = 12 .. 216)
    # =========================================================================
    _add_framed_label_box(
        wetop_u, spTree, next_id, "usd-root", 30.0, 40.0, 86.0, 20.0,
        [("Scene.usd", 8.8, True, "0F172A")],
        fill_hex="F8FAFC", line_hex="64748B", line_w_pt=0.80,
    )
    # Vertical DAG trunk from (34, 60) down to (34, 122), stopping above feedback entry at y=131
    wetop_u.add_line(spTree, next_id(), "dag-trunk", 34.0, 60.0, 34.0, 122.0, line_hex="94A3B8", line_w_pt=0.75)
    for bi, by in enumerate((76.0, 99.0, 122.0)):
        wetop_u.add_line(spTree, next_id(), f"dag-b-{bi}", 34.0, by, 44.0, by, line_hex="94A3B8", line_w_pt=0.75)

    _add_framed_label_box(
        wetop_u, spTree, next_id, "dag-mesh", 44.0, 66.5, 78.0, 19.0,
        [("Mesh & Pose (Lock)", 7.6, False, "475569")],
        fill_hex="FFFFFF", line_hex="94A3B8", line_w_pt=0.65, dash="dash",
    )
    _add_framed_label_box(
        wetop_u, spTree, next_id, "dag-cam", 44.0, 89.5, 78.0, 19.0,
        [("Camera (1024×768)", 7.6, False, "475569")],
        fill_hex="FFFFFF", line_hex="94A3B8", line_w_pt=0.65, dash="dash",
    )
    _add_framed_label_box(
        wetop_u, spTree, next_id, "dag-mdl", 44.0, 113.5, 78.0, 22.0,
        [("MDL Shader Graph", 7.8, True, "0F172A")],
        fill_hex="F8FAFC", line_hex="0F172A", line_w_pt=0.90,
    )
    # Wire from MDL leaf node -> NVIDIA MDL material ball
    wetop_u.add_line(spTree, next_id(), "mdl-w1", 122.0, 124.5, 130.0, 124.5, line_hex="475569", line_w_pt=0.80)
    wetop_u.add_line(spTree, next_id(), "mdl-w2", 130.0, 124.5, 130.0, 77.0, line_hex="475569", line_w_pt=0.80)
    _add_arrow(wetop_u, spTree, next_id(), "mdl-w3", 130.0, 77.0, 138.0, 77.0, line_hex="475569", line_w_pt=0.80)

    _add_pic(spTree, next_id(), "ball-mdl", 138.0, 39.0, 70.0, 70.0, media_rids["ppt/media/fig3_ball_mdl.png"])
    wetop_u.add_textbox(
        spTree, next_id(), "ball-mdl-t1", 128.0, 110.0, 90.0, 12.0,
        [{"text": "NVIDIA MDL", "sz_pt": 8.6, "bold": True, "color": "0F172A"}], algn="ctr",
    )
    wetop_u.add_textbox(
        spTree, next_id(), "ball-mdl-t2", 128.0, 121.5, 90.0, 11.0,
        [{"text": "Multi-lobe BRDF", "sz_pt": 7.3, "bold": False, "color": "475569"}], algn="ctr",
    )

    # Middle Deterministic Export arrow & label
    _add_arrow(wetop_u, spTree, next_id(), "lower-arr", 173.0, 136.0, 173.0, 174.0, line_hex="334155", line_w_pt=1.05)
    wetop_u.add_textbox(
        spTree, next_id(), "lower-t1", 22.0, 144.0, 140.0, 12.0,
        [{"text": "Deterministic Export", "sz_pt": 8.2, "bold": True, "color": "0F172A"}], algn="r",
    )
    wetop_u.add_textbox(
        spTree, next_id(), "lower-t2", 22.0, 155.5, 140.0, 11.0,
        [{"text": "0 VLM calls · Pose locked", "sz_pt": 7.3, "bold": False, "color": "475569"}], algn="r",
    )

    # Bottom simplified Preview shader graph & sphere
    _add_framed_label_box(
        wetop_u, spTree, next_id, "prev-geom", 30.0, 188.0, 92.0, 19.0,
        [("Geometry (Identical)", 7.6, False, "64748B")],
        fill_hex="FFFFFF", line_hex="CBD5E1", line_w_pt=0.65, dash="dash",
    )
    wetop_u.add_line(spTree, next_id(), "prev-down", 76.0, 207.0, 76.0, 218.0, line_hex="94A3B8", line_w_pt=0.75)
    _add_framed_label_box(
        wetop_u, spTree, next_id, "prev-node", 30.0, 218.0, 92.0, 22.0,
        [("UsdPreviewSurface", 7.8, True, "0F172A")],
        fill_hex="F8FAFC", line_hex="0F172A", line_w_pt=0.85,
    )
    wetop_u.add_textbox(
        spTree, next_id(), "prev-note", 28.0, 243.5, 96.0, 11.0,
        [{"text": "Metallic-roughness proxy", "sz_pt": 7.1, "bold": False, "color": "64748B"}], algn="ctr",
    )
    wetop_u.add_line(spTree, next_id(), "prev-w1", 122.0, 229.0, 130.0, 229.0, line_hex="475569", line_w_pt=0.80)
    wetop_u.add_line(spTree, next_id(), "prev-w2", 130.0, 229.0, 130.0, 212.0, line_hex="475569", line_w_pt=0.80)
    _add_arrow(wetop_u, spTree, next_id(), "prev-w3", 130.0, 212.0, 138.0, 212.0, line_hex="475569", line_w_pt=0.80)

    _add_pic(spTree, next_id(), "ball-prev", 138.0, 175.0, 70.0, 70.0, media_rids["ppt/media/fig3_ball_prev.png"])
    wetop_u.add_textbox(
        spTree, next_id(), "ball-prev-t1", 128.0, 246.0, 90.0, 12.0,
        [{"text": "UsdPreviewSurface", "sz_pt": 8.4, "bold": True, "color": "0F172A"}], algn="ctr",
    )
    wetop_u.add_textbox(
        spTree, next_id(), "ball-prev-t2", 128.0, 257.5, 90.0, 11.0,
        [{"text": "Flattened BSDF lobes", "sz_pt": 7.3, "bold": False, "color": "475569"}], algn="ctr",
    )

    # Arrows Stage (a) -> Stage (b) across x=222 divider
    _add_arrow(wetop_u, spTree, next_id(), "a2b-top", 210.0, 77.0, 233.0, 77.0, line_hex="334155", line_w_pt=0.95)
    _add_arrow(wetop_u, spTree, next_id(), "a2b-bot", 210.0, 212.0, 233.0, 212.0, line_hex="334155", line_w_pt=0.95)

    # =========================================================================
    # Stage (b): Geometry-Locked Paired Renders (x = 232 .. 462)
    # =========================================================================
    wetop_u.add_textbox(
        spTree, next_id(), "b-query", 232.0, 30.0, 234.0, 13.0,
        [
            {"text": "q", "sz_pt": 7.7, "italic": True, "color": "334155"},
            {"text": "i", "sz_pt": 7.7, "italic": True, "baseline": -25000, "color": "334155"},
            {"text": ": “Point to the gas cooktop beneath the pots”", "sz_pt": 7.7, "italic": True, "color": "334155"},
        ],
        algn="l",
    )
    _add_pic(spTree, next_id(), "plate-o", 234.0, 48.0, 134.0, 96.0, media_rids["ppt/media/fig3_plate_o.png"], border_hex="0F172A", border_w_pt=0.80)
    wetop_u.add_textbox(
        spTree, next_id(), "b-mid-note", 234.0, 148.0, 134.0, 12.0,
        [{"text": "Matched pose & mask (Test pair)", "sz_pt": 7.2, "bold": False, "color": "475569"}], algn="ctr",
    )
    _add_pic(spTree, next_id(), "plate-c", 234.0, 165.0, 134.0, 96.0, media_rids["ppt/media/fig3_plate_c.png"], border_hex="0F172A", border_w_pt=0.80)
    wetop_u.add_textbox(
        spTree, next_id(), "b-bot-note", 234.0, 263.5, 134.0, 11.0,
        [
            {"text": "SSIM", "sz_pt": 7.3, "color": "475569"},
            {"text": "tgt", "sz_pt": 7.3, "baseline": -25000, "color": "475569"},
            {"text": " = 0.351 · ΔL* = 39.5", "sz_pt": 7.3, "color": "475569"},
        ],
        algn="ctr",
    )

    # Right sub-column in (b): Target mask M_i^v & locked geometry rows
    wetop_u.add_textbox(
        spTree, next_id(), "b-m-t1", 374.0, 48.5, 88.0, 12.0,
        [
            {"text": "Target Mask M", "sz_pt": 8.4, "bold": True, "color": "0F172A"},
            {"text": "i", "sz_pt": 8.4, "bold": True, "baseline": -25000, "color": "0F172A"},
            {"text": "v", "sz_pt": 8.4, "bold": True, "baseline": 30000, "color": "0F172A"},
        ],
        algn="ctr",
    )
    wetop_u.add_textbox(
        spTree, next_id(), "b-m-t2", 374.0, 61.5, 88.0, 11.0,
        [{"text": "Mask IoU = 1.000", "sz_pt": 7.8, "bold": True, "color": "0F766E"}], algn="ctr",
    )
    _add_pic(spTree, next_id(), "plate-mask", 375.0, 76.0, 84.0, 60.0, media_rids["ppt/media/fig3_mask.png"], border_hex="0F172A", border_w_pt=0.80)

    geom_rows = [
        ("Area frac",   f"{math.exp(float(anch['log_area_frac']))*100:.1f}%"),
        ("Aspect w/h",  f"{float(anch['aspect_ratio']):.2f}"),
        ("Offset d",    f"{float(anch['center_dist_norm']):.2f}"),
        ("Border",      f"{int(anch['border_touch'])}"),
        ("Regime",      "RM"),
    ]
    for ri, (rk, rv) in enumerate(geom_rows):
        ry = 144.0 + ri * 17.5
        wetop_u.add_textbox(spTree, next_id(), f"gr-k-{ri}", 375.0, ry, 52.0, 13.0, [{"text": rk, "sz_pt": 7.3, "color": "475569"}], algn="l")
        wetop_u.add_textbox(spTree, next_id(), f"gr-v-{ri}", 426.0, ry, 34.0, 13.0, [{"text": rv, "sz_pt": 7.5, "bold": True, "color": "0F172A"}], algn="r")
        if ri < len(geom_rows) - 1:
            wetop_u.add_line(spTree, next_id(), f"gr-ln-{ri}", 375.0, ry + 15.0, 459.0, ry + 15.0, line_hex="E2E8F0", line_w_pt=0.50)

    # Clean right-hand collector bracket ']' from Stage (b) right edge -> Stage (c)
    wetop_u.add_line(spTree, next_id(), "b2c-top", 459.0,  54.0, 465.0,  54.0, line_hex="475569", line_w_pt=0.80)
    wetop_u.add_line(spTree, next_id(), "b2c-mid", 459.0, 106.0, 465.0, 106.0, line_hex="475569", line_w_pt=0.80)
    wetop_u.add_line(spTree, next_id(), "b2c-bot", 459.0, 248.0, 465.0, 248.0, line_hex="475569", line_w_pt=0.80)
    wetop_u.add_line(spTree, next_id(), "b2c-bus", 465.0,  54.0, 465.0, 248.0, line_hex="475569", line_w_pt=0.80)
    _add_arrow(wetop_u, spTree, next_id(), "b2c-go", 465.0, 152.0, 484.0, 152.0, line_hex="334155", line_w_pt=0.95)

    # =========================================================================
    # Stage (c): Zero-VLM Optical & Geometric Maps (x = 482 .. 744)
    # =========================================================================
    map_rows = [
        ("ppt/media/fig3_delta_e.png", 44.0,
         [{"text": "CIE ΔE*", "sz_pt": 8.2, "bold": True, "color": "0F172A"}, {"text": "ab", "sz_pt": 8.2, "bold": True, "baseline": -25000, "color": "0F172A"}, {"text": " Map", "sz_pt": 8.2, "bold": True, "color": "0F172A"}],
         [[{"text": f"ΔL* = {float(anch['target_delta_L']):.1f}", "sz_pt": 7.2, "color": "475569"}],
          [{"text": "Δab*", "sz_pt": 7.2, "color": "475569"}, {"text": f" = {float(anch['target_delta_ab']):.1f}", "sz_pt": 7.2, "color": "475569"}],
          [{"text": f"SSIM = {float(anch['target_ssim']):.2f}", "sz_pt": 7.2, "color": "475569"}]]),
        ("ppt/media/fig3_sobel.png", 121.0,
         [{"text": "Sobel Edge Δ∇L*", "sz_pt": 8.2, "bold": True, "color": "0F172A"}],
         [[{"text": f"Ratio r = {float(anch['target_sobel_edge_ratio']):.2f}", "sz_pt": 7.2, "color": "475569"}],
          [{"text": f"Spec Δ = {float(anch['target_specular_delta']):+.2f}", "sz_pt": 7.2, "color": "475569"}],
          [{"text": f"Bnd ΔC = {float(anch['boundary_contrast_delta_lab']):+.0f}", "sz_pt": 7.2, "color": "475569"}]]),
        ("ppt/media/fig3_geom_prior.png", 198.0,
         [{"text": "Geom & Priors", "sz_pt": 8.2, "bold": True, "color": "0F172A"}],
         [[{"text": f"log A = {float(anch['log_area_frac']):.2f}", "sz_pt": 7.2, "color": "475569"}],
          [{"text": "d", "sz_pt": 7.2, "color": "475569"}, {"text": "norm", "sz_pt": 7.2, "baseline": -25000, "color": "475569"}, {"text": f" = {float(anch['center_dist_norm']):.2f}", "sz_pt": 7.2, "color": "475569"}],
          [{"text": "Prior: RM = 1", "sz_pt": 7.2, "color": "475569"}]]),
    ]
    for mi, (m_key, my, m_title_runs, m_line_runs_list) in enumerate(map_rows):
        _add_pic(spTree, next_id(), f"cmap-{mi}", 486.0, my, 108.0, 66.0, media_rids[m_key])
        wetop_u.add_textbox(
            spTree, next_id(), f"cm-t-{mi}", 597.0, my + 4.0, 64.0, 13.0,
            m_title_runs, algn="l",
        )
        for li, l_runs in enumerate(m_line_runs_list):
            wetop_u.add_textbox(
                spTree, next_id(), f"cm-l-{mi}-{li}", 597.0, my + 20.0 + li * 13.0, 64.0, 12.0,
                l_runs, algn="l",
            )
        _add_arrow(wetop_u, spTree, next_id(), f"cm-arr-{mi}", 660.0, my + 33.0, 681.0, my + 33.0, line_hex="475569", line_w_pt=0.80)

    # Standardized z-score feature vector barcode strip
    wetop_u.add_textbox(
        spTree, next_id(), "bar-hdr", 669.0, 31.0, 48.0, 13.0,
        [{"text": "Vector x", "sz_pt": 8.6, "bold": True, "color": "0F172A"}, {"text": "i", "sz_pt": 8.6, "bold": True, "baseline": -25000, "color": "0F172A"}],
        algn="ctr",
    )
    _add_pic(spTree, next_id(), "barcode", 682.0, 48.0, 22.0, 206.0, media_rids["ppt/media/fig3_barcode.png"])
    wetop_u.add_textbox(spTree, next_id(), "blk-opt", 707.0, 88.0, 44.0, 24.0, [{"text": "Optical Δ", "sz_pt": 7.3, "bold": True, "color": "334155"}], algn="l")
    wetop_u.add_textbox(spTree, next_id(), "blk-geo", 707.0, 188.0, 44.0, 16.0, [{"text": "Geom (5)", "sz_pt": 7.3, "bold": True, "color": "334155"}], algn="l")
    wetop_u.add_textbox(spTree, next_id(), "blk-pri", 707.0, 226.0, 44.0, 16.0, [{"text": "Prior (RM)", "sz_pt": 7.3, "bold": True, "color": "334155"}], algn="l")
    wetop_u.add_textbox(
        spTree, next_id(), "bar-sub", 662.0, 258.0, 68.0, 12.0,
        [{"text": "z-scored features", "sz_pt": 7.1, "color": "475569"}], algn="ctr",
    )

    # Arrow Stage (c) -> Stage (d) straight across open slot y=152
    _add_arrow(wetop_u, spTree, next_id(), "c2d-arr", 705.0, 152.0, 765.0, 152.0, line_hex="334155", line_w_pt=0.95)

    # =========================================================================
    # Stage (d): Family-Calibrated Risk Gate (x = 764 .. 990)
    # =========================================================================
    wetop_u.add_textbox(
        spTree, next_id(), "d-sub", 764.0, 29.5, 226.0, 13.0,
        [
            {"text": "Risk score s", "sz_pt": 7.8, "color": "334155"},
            {"text": "i", "sz_pt": 7.8, "baseline": -25000, "color": "334155"},
            {"text": " = σ(w", "sz_pt": 7.8, "color": "334155"},
            {"text": "T", "sz_pt": 7.8, "baseline": 30000, "color": "334155"},
            {"text": "x", "sz_pt": 7.8, "color": "334155"},
            {"text": "i", "sz_pt": 7.8, "baseline": -25000, "color": "334155"},
            {"text": " + b)  ·  Zero-VLM L2 gate", "sz_pt": 7.8, "color": "334155"},
        ],
        algn="l",
    )
    _add_pic(spTree, next_id(), "risk-hist", 765.0, 46.0, 225.0, 138.0, media_rids["ppt/media/fig3_hist.png"])

    # Downward arrows from histogram into decision branches
    _add_arrow(wetop_u, spTree, next_id(), "d-left-arr",  817.0, 185.0, 817.0, 201.0, line_hex="0F766E", line_w_pt=0.90)
    _add_arrow(wetop_u, spTree, next_id(), "d-right-arr", 933.0, 185.0, 933.0, 201.0, line_hex="B91C1C", line_w_pt=0.95)

    _add_framed_label_box(
        wetop_u, spTree, next_id, "gate-admit", 766.0, 202.0, 102.0, 62.0,
        [
            ("Auto-Admit (80%)",          8.5, True,  "0F172A"),
            ("Deploy UsdPreview",         7.6, True,  "0F766E"),
            ("+4.4% glare gain · 0 QA",   7.0, False, "475569"),
        ],
        fill_hex="F8FAFC", line_hex="94A3B8", line_w_pt=0.80,
    )
    _add_framed_label_box(
        wetop_u, spTree, next_id, "gate-flag", 874.0, 202.0, 117.0, 62.0,
        [
            ("Flagged (Top-20%)",           8.5, True,  "991B1B"),
            ("52.0% LOSO Recall",           7.9, True,  "B91C1C"),
            ("0.743 Test AUROC (vs. .432 MAE)", 6.4, False, "334155"),
        ],
        fill_hex="FEF2F2", line_hex="B91C1C", line_w_pt=0.95,
    )

    # =========================================================================
    # Restrained Orthogonal Feedback Loop (Flagged -> Native MDL Shader Graph)
    # =========================================================================
    wetop_u.add_line(spTree, next_id(), "fb-down",  933.0, 264.0, 933.0, 294.0, line_hex="B91C1C", line_w_pt=0.90, dash="dash")
    wetop_u.add_line(spTree, next_id(), "fb-horiz", 933.0, 294.0,   9.0, 294.0, line_hex="B91C1C", line_w_pt=0.90, dash="dash")
    wetop_u.add_line(spTree, next_id(), "fb-up",      9.0, 294.0,   9.0, 131.0, line_hex="B91C1C", line_w_pt=0.90, dash="dash")
    _add_arrow(wetop_u, spTree, next_id(), "fb-in",   9.0, 131.0,  43.0, 131.0, line_hex="B91C1C", line_w_pt=0.95, dash="dash")

    # Crisp white knockout mask along y=294 horizontal segment so label sits directly on line
    wetop_u.add_rect(spTree, next_id(), "fb-mask", 248.0, 285.0, 480.0, 18.0, fill_hex="FFFFFF", line_hex=None)
    wetop_u.add_textbox(
        spTree, next_id(), "fb-text", 252.0, 286.0, 472.0, 16.0,
        [{"text": "Selective MDL Preservation  ·  Revert flagged top-20% shaders to native MDL (eliminates 80% manual QA)",
          "sz_pt": 8.0, "bold": True, "color": "991B1B"}],
        algn="ctr", anchor="ctr",
    )

    entries["ppt/slides/slide1.xml"] = ET.tostring(slide_root, encoding="utf-8", xml_declaration=True)
    OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_PPTX, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            if not name.endswith("/"):
                zout.writestr(name, data)
    print("[ok] wrote CVPR Fig 3 PPTX:", OUT_PPTX)

    if not args.no_com:
        _export_pptx_to_pdf_com(OUT_PPTX, OUT_PDF)
        print("[ok] exported vector PDF via PowerPoint COM:", OUT_PDF)
        PREVIEW_PNG.parent.mkdir(parents=True, exist_ok=True)
        pdftoppm_exe = Path(r"E:\my_program\texlive\2025\bin\windows\pdftoppm.exe")
        stem = PREVIEW_PNG.parent / "fig3_pipeline_page"
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
