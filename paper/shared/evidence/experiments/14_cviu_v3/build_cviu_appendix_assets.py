#!/usr/bin/env python3
"""Generate WET-OP / CVPR-grade panoramic appendix plates (app_fig1..app_fig7) and tables for CVIU v3."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Rectangle
import numpy as np
from PIL import Image

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[4]
sys.path.insert(0, str(THIS_DIR))

from optical_and_risk_features import DEPLOY_AUTO_FEATURES  # noqa: E402
from v3_common import IMAGE_HEIGHT, IMAGE_WIDTH, resolve_asset_path, roc_auc_score_np  # noqa: E402

V3_RAW_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_v3"
V1_META_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_formal/v1"
RAW_DIR = REPO_ROOT / "paper/shared/evidence/raw"
OUT_FIG_DIR = REPO_ROOT / "paper/venues/cviu/figures/appendix"
OUT_TAB_DIR = REPO_ROOT / "paper/venues/cviu/tables"
PREVIEW_DIR = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\fig_previews\appendix"
)

# WET-OP cohesive publication palette
COL_NAVY = "#1B3765"
COL_INK = "#0F172A"
COL_SLATE = "#475569"
COL_MUTED = "#64748B"
COL_RULE = "#CBD5E1"
COL_LIGHT = "#F8FAFC"
COL_TEAL = "#12947F"
COL_COBALT = "#1D63DC"
COL_CRIMSON = "#DC2646"
COL_AMBER = "#D97706"

MODEL_SPECS = [
    ("molmo2_8b",             "Molmo2-8B",     COL_TEAL),
    ("qwen3_vl_8b_r0",        "Qwen3-VL-8B",   COL_COBALT),
    ("internvl3_5_8b",        "InternVL3.5",   COL_CRIMSON),
    ("llava_next_mistral_7b", "LLaVA-Mistral", COL_AMBER),
]


def _map_repo_path(raw_str: str | Path) -> Path:
    s = str(raw_str).replace("\\", "/")
    p = Path(raw_str)
    if p.exists():
        return p
    prefix = "/cpfs/user/zhuzihou/dev/ConvertAsset/"
    if s.startswith(prefix):
        cand = REPO_ROOT / s[len(prefix):]
        if cand.exists():
            return cand
    cand2 = REPO_ROOT / s.lstrip("/")
    if cand2.exists():
        return cand2
    return p


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _index_oc(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(r["pair_id"]), str(r["condition"])): r
        for r in _read_jsonl(path)
        if r.get("status") == "ok"
    }


def _load_mask(path: Path) -> np.ndarray:
    if path.suffix == ".npy":
        return np.load(path) > 0
    return np.asarray(Image.open(path).convert("L")) > 0


def _start_plate(width_in: float, height_in: float, title: str, right_tag: str) -> plt.Figure:
    """Create a borderless white panoramic plate with stacked 2-line WET-OP navy accent bar."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
    fig = plt.figure(figsize=(width_in, height_in), facecolor="white")
    bar_h_in = 0.30
    y_top = 1.0 - (0.04 / height_in)
    y_bar_bot = 1.0 - (0.04 + bar_h_in) / height_in
    bar_w = 0.048 / width_in
    fig.patches.append(Rectangle((0.008, y_bar_bot), bar_w, bar_h_in / height_in, transform=fig.transFigure, facecolor=COL_NAVY, edgecolor="none"))
    fig.text(0.018 + bar_w, y_top - 0.08 / height_in, title, fontsize=9.4, fontweight="bold", color=COL_INK, va="center", ha="left")
    fig.text(0.018 + bar_w, y_bar_bot + 0.065 / height_in, right_tag, fontsize=7.0, color=COL_SLATE, va="center", ha="left")
    rule_y = y_bar_bot - 0.035 / height_in
    fig.add_artist(plt.Line2D([0.008, 0.992], [rule_y, rule_y], transform=fig.transFigure, color=COL_RULE, lw=0.75))
    return fig


def _save_plate(fig: plt.Figure, stem: str) -> None:
    OUT_FIG_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    pdf_p = OUT_FIG_DIR / f"{stem}.pdf"
    png_p = PREVIEW_DIR / f"{stem}.png"
    fig.savefig(pdf_p, format="pdf")
    fig.savefig(png_p, format="png", dpi=200)
    plt.close(fig)
    print(f"[ok] wrote {pdf_p.name} (+ preview)")


def _show_image_ax(fig: plt.Figure, rect: list[float], img_path: Path, *, border_col: str = COL_RULE, border_lw: float = 0.65) -> plt.Axes:
    ax = fig.add_axes(rect)
    im = np.asarray(Image.open(img_path).convert("RGB"))
    ax.imshow(im)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor(border_col)
        sp.set_linewidth(border_lw)
    return ax


def _crop_box_around_mask(mask: np.ndarray, *, target_aspect: float = 4.0 / 3.0, pad_frac: float = 1.65) -> tuple[int, int, int, int]:
    h, w = mask.shape
    ys, xs = np.where(mask)
    x_min, x_max = float(xs.min()), float(xs.max())
    y_min, y_max = float(ys.min()), float(ys.max())
    bw, bh = x_max - x_min + 1.0, y_max - y_min + 1.0
    cx, cy = 0.5 * (x_min + x_max), 0.5 * (y_min + y_max)
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
    return x0, y0, min(w, int(round(x0 + cw))), min(h, int(round(y0 + ch)))


# =============================================================================
# 1. app_fig1_appearance_and_materials.pdf
# =============================================================================
def build_app_fig1() -> None:
    fig = _start_plate(
        7.2, 4.15,
        "Matched Multi-View Object, Orbit, and Material-Fixture Survival Audit",
        "App. A & App. B  |  Original (MDL) vs. ConvertAsset & NVIDIA PreviewSurface",
    )

    # Panel headers cleanly below stacked header rule
    fig.text(0.012, 0.875, "(a) Object & Scene Views (Orig vs. Conv)", fontsize=8.2, fontweight="bold", color=COL_INK)
    fig.text(0.452, 0.875, "(b) Three-Route Survival & Fixtures", fontsize=8.2, fontweight="bold", color=COL_INK)
    fig.add_artist(plt.Line2D([0.438, 0.438], [0.025, 0.895], transform=fig.transFigure, color=COL_RULE, lw=0.75, ls="--"))

    # Column headers
    fig.text(0.180, 0.842, "Original (MDL)", fontsize=7.2, fontweight="bold", color=COL_COBALT, ha="center")
    fig.text(0.346, 0.842, "ConvertAsset", fontsize=7.2, fontweight="bold", color=COL_CRIMSON, ha="center")
    for cj, (clbl, ccol) in enumerate([("Original", COL_COBALT), ("ConvertAsset", COL_CRIMSON), ("NVIDIA", COL_SLATE)]):
        fig.text(0.610 + cj * 0.150, 0.842, clbl, fontsize=7.2, fontweight="bold", color=ccol, ha="center")

    left_rows = [
        ("Chest #0004\n(Front)",  "PSNR 37.5 dB\nDINO 0.798",
         RAW_DIR / "renders/chestofdrawers_0004/A_front.png",
         RAW_DIR / "renders/chestofdrawers_0004/B_front.png"),
        ("Chest #0023\n(Top-R)",  "PSNR 30.6 dB\nLPIPS 0.032",
         RAW_DIR / "renders/chestofdrawers_0023/A_top_front_right.png",
         RAW_DIR / "renders/chestofdrawers_0023/B_top_front_right.png"),
        ("GRScene\nOrbit 01",     "Indoor Context\nIndirect Spec.",
         REPO_ROOT / "paper/shared/figures/out_tmp/mdl_images/orbit_mdl_01.png",
         REPO_ROOT / "paper/shared/figures/out_tmp/nomdl_images/orbit_01.png"),
        ("GRScene\nOrbit 05",     "Indoor Context\nSpecular Floor",
         REPO_ROOT / "paper/shared/figures/out_tmp/mdl_images/orbit_mdl_05.png",
         REPO_ROOT / "paper/shared/figures/out_tmp/nomdl_images/orbit_05.png"),
    ]
    for ri, (rlbl, rstat, p_o, p_c) in enumerate(left_rows):
        y0 = 0.640 - ri * 0.200
        fig.text(0.010, y0 + 0.115, rlbl, fontsize=7.0, fontweight="bold", color=COL_INK, va="center", ha="left")
        fig.text(0.010, y0 + 0.045, rstat, fontsize=6.2, color=COL_MUTED, va="center", ha="left")
        _show_image_ax(fig, [0.102, y0 + 0.012, 0.156, 0.172], p_o, border_col=COL_COBALT, border_lw=0.75)
        _show_image_ax(fig, [0.268, y0 + 0.012, 0.156, 0.172], p_c, border_col=COL_CRIMSON, border_lw=0.75)

    mf_qual = json.loads((RAW_DIR / "material_effect_baseline/qualitative_render_manifest.json").read_text(encoding="utf-8"))
    mf_supp = json.loads((RAW_DIR / "material_effect_baseline/supplemental_qualitative_render_manifest.json").read_text(encoding="utf-8"))
    recs = {(r["sample_id"], r["condition"]): _map_repo_path(r["image"]["path"]) for r in (mf_qual["records"] + mf_supp["records"])}
    conds = mf_qual["condition_order"]  # ['original_MDL', 'converted_noMDL_convertasset', 'converted_nvidia_usd']

    right_rows = [
        ("Clearcoat\nFixture",    "NVIDIA: Missing\n(0/1 Check)", "supplemental_clearcoat_omnipbr"),
        ("Procedural\nTexture",   "Checker lost\nin both conv.",  "supplemental_procedural_checker"),
        ("Glass\nBottle",         "Opacity &\nFresnel shift",     "c27086f557d316584264.zoom_018"),
        ("Arched\nClock",         "Metallic trim\n& dial glow",    "f35ef3d86c42446b7ddf.zoom_018"),
    ]
    for ri, (rlbl, rstat, sid) in enumerate(right_rows):
        y0 = 0.640 - ri * 0.200
        fig.text(0.448, y0 + 0.115, rlbl, fontsize=7.0, fontweight="bold", color=COL_INK, va="center", ha="left")
        fig.text(0.448, y0 + 0.045, rstat, fontsize=6.1, color=COL_CRIMSON if ri < 2 else COL_MUTED, va="center", ha="left")
        for cj, cond in enumerate(conds):
            ax = _show_image_ax(fig, [0.542 + cj * 0.150, y0 + 0.012, 0.138, 0.172], recs[(sid, cond)], border_col=COL_RULE, border_lw=0.65)
            if ri == 0 and cj == 2:
                ax.text(0.5, 0.5, "Prim Missing\n(0/1 Check)", transform=ax.transAxes, ha="center", va="center",
                        fontsize=6.6, fontweight="bold", color="#FCA5A5")

    _save_plate(fig, "app_fig1_appearance_and_materials")


# =============================================================================
# 2. app_fig2_scene30_atlas.pdf
# =============================================================================
def build_app_fig2(
    scenes_meta: list[dict[str, Any]],
    feats: list[dict[str, Any]],
    m_by_oc: dict[tuple[str, str], dict[str, Any]],
    idx_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
    assets_root: Path,
) -> None:
    fig = _start_plate(
        7.2, 4.95,
        "30-Scene SimReady Catalog: Representative Natural Pairs Across Train / Val / Test Splits",
        "12 Stratified Highlight Scenes (of 30 Total: 20 Home + 10 Commercial · 480 Pairs)",
    )

    feats_by_sc: dict[str, list[dict[str, Any]]] = {}
    for r in feats:
        feats_by_sc.setdefault(r["scene_id"], []).append(r)

    # Pick 12 visually diverse stratified scenes: 6 train (4 home, 2 comm), 2 val (1 home, 1 comm), 4 test (3 home, 1 comm)
    by_bucket: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for s in sorted(scenes_meta, key=lambda x: (x["split"], x["family"], x["scene_id"])):
        by_bucket.setdefault((s["split"], s["family"]), []).append(s)

    selected = (
        by_bucket[("train", "home_scenes")][:4]
        + by_bucket[("train", "commercial_scenes")][:2]
        + by_bucket[("validation", "home_scenes")][:1]
        + by_bucket[("validation", "commercial_scenes")][:1]
        + by_bucket[("test", "home_scenes")][:3]
        + by_bucket[("test", "commercial_scenes")][:1]
    )

    # Assign canonical H01..H20 / C01..C10 codes identical to Table app_scenes30 (train -> val -> test)
    sorted_all = sorted(scenes_meta, key=lambda x: (x["split"] != "train", x["split"] != "validation", x["family"] != "home_scenes", x["scene_id"]))
    h_cnt, c_cnt = 0, 0
    scene_code: dict[str, str] = {}
    for s in sorted_all:
        if s["family"] == "home_scenes":
            h_cnt += 1
            scene_code[s["scene_id"]] = f"H{h_cnt:02d}"
        else:
            c_cnt += 1
            scene_code[s["scene_id"]] = f"C{c_cnt:02d}"

    split_style = {
        "train":      ("TRAIN", COL_TEAL),
        "validation": ("VAL",   COL_AMBER),
        "test":       ("TEST",  COL_COBALT),
    }

    ncols, nrows = 4, 3
    x_start, y_top = 0.010, 0.892
    cell_w, cell_h = 0.238, 0.278
    gap_x, gap_y = 0.009, 0.014

    for idx_s, s in enumerate(selected):
        r_i, c_i = divmod(idx_s, ncols)
        x0 = x_start + c_i * (cell_w + gap_x)
        yb = y_top - (r_i + 1) * cell_h - r_i * gap_y
        sid = s["scene_id"]
        spl_lbl, spl_col = split_style[s["split"]]

        # Card outline & header strip added to fig.patches (never paints over fig.axes images!)
        fig.patches.append(Rectangle((x0, yb), cell_w, cell_h, transform=fig.transFigure, fill=False, edgecolor=COL_RULE, lw=0.75))
        fig.patches.append(Rectangle((x0, yb + cell_h - 0.042), cell_w, 0.042, transform=fig.transFigure, facecolor="#F8FAFC", edgecolor="none"))
        fig.patches.append(Rectangle((x0, yb + cell_h - 0.042), 0.0055, 0.042, transform=fig.transFigure, facecolor=spl_col, edgecolor="none"))

        dom = "Home" if s["family"] == "home_scenes" else "Comm."
        uid_short = f"{sid[:4]}..{sid.replace('_usd', '')[-4:]}"
        fig.text(x0 + 0.011, yb + cell_h - 0.021, f"{scene_code[sid]} · {dom} ({uid_short})", fontsize=6.7, fontweight="bold", color=COL_INK, va="center")
        fig.text(x0 + cell_w - 0.008, yb + cell_h - 0.021, spl_lbl, fontsize=6.3, fontweight="bold", color=spl_col, va="center", ha="right")

        sc_feats = feats_by_sc[sid]
        # Representative pair with largest visual target change or central framing
        rep = max(sc_feats, key=lambda fr: fr["target_delta_L"] * (1.0 - abs(fr["center_dist_norm"] - 0.35)))
        pid = rep["pair_id"]
        po = resolve_asset_path(m_by_oc[(pid, "original")]["image"]["path"], assets_root)
        pc = resolve_asset_path(m_by_oc[(pid, "converted")]["image"]["path"], assets_root)

        img_w = 0.455 * cell_w
        img_h = img_w * (7.2 / 4.95) * 0.72
        img_y = yb + 0.082
        _show_image_ax(fig, [x0 + 0.008, img_y, img_w, img_h], po, border_col=COL_COBALT, border_lw=0.65)
        _show_image_ax(fig, [x0 + cell_w - 0.008 - img_w, img_y, img_w, img_h], pc, border_col=COL_CRIMSON, border_lw=0.65)
        fig.text(x0 + 0.008 + 0.5 * img_w, img_y + img_h + 0.010, "Orig (MDL)", fontsize=5.8, color=COL_COBALT, fontweight="bold", ha="center")
        fig.text(x0 + cell_w - 0.008 - 0.5 * img_w, img_y + img_h + 0.010, "Conv (Prev)", fontsize=5.8, color=COL_CRIMSON, fontweight="bold", ha="center")

        # Bottom summary metrics (regime counts + 4-family average hit shift & flip %)
        rm = sum(1 for f in sc_feats if f["prior_optical_regime"] == "Reflective/Metallic")
        tg = sum(1 for f in sc_feats if f["prior_optical_regime"] == "Transparent/Glass")
        md = sum(1 for f in sc_feats if f["prior_optical_regime"] == "Matte/Diffuse")
        es = sum(1 for f in sc_feats if f["prior_optical_regime"] == "Emissive/Screen")

        ho_vals, hc_vals, fl_vals = [], [], []
        for mkey, _, _ in MODEL_SPECS:
            im = idx_by_model[mkey]
            ho_vals.append(np.mean([bool(im[(f["pair_id"], "original")]["hit"]) for f in sc_feats]) * 100.0)
            hc_vals.append(np.mean([bool(im[(f["pair_id"], "converted")]["hit"]) for f in sc_feats]) * 100.0)
            fl_vals.append(np.mean([bool(im[(f["pair_id"], "original")]["hit"]) != bool(im[(f["pair_id"], "converted")]["hit"]) for f in sc_feats]) * 100.0)

        fig.text(x0 + 0.010, yb + 0.056, f"Regimes RM:{rm} TG:{tg} MD:{md} ES:{es}", fontsize=6.2, color=COL_SLATE)
        fig.text(x0 + 0.010, yb + 0.024, f"4-Fam Hit: {np.mean(ho_vals):.1f}%→{np.mean(hc_vals):.1f}% · Flip {np.mean(fl_vals):.1f}%", fontsize=6.4, fontweight="bold", color=COL_INK)

    _save_plate(fig, "app_fig2_scene30_atlas")


# =============================================================================
# 3. app_fig3_readout_and_pilot.pdf
# =============================================================================
def build_app_fig3(sf: dict[str, Any], runs_dir: Path) -> None:
    fig = _start_plate(
        7.2, 2.95,
        "Prompt/Coordinate Readout Sensitivity and Four-Family Pilot Qualification",
        "App. D  |  30-Pair Coordinate Grid & Verified Parse Rates (24-Input Pilot vs. 960 Full Benchmark)",
    )

    # Data verified directly in tables/protocol_full.tex
    models_prot = ["Gemma4-E4B", "Qwen2.5-VL-7B", "Qwen3-VL-2B", "Qwen3-VL-8B", "InternVL3-8B", "Molmo-7B-D"]
    cols_prot = ["0–1000\nText", "0–1000\nJSON", "Pixel\nText", "Pixel\nJSON"]
    # Delta H = H_C - H_O (pp)
    deltas = np.array([
        [ +6.7,  -3.3,   0.0,   0.0],
        [ +3.3,  -6.6, -13.3, +13.3],
        [  0.0,  +3.3,   0.0,   0.0],
        [ +3.4,  +3.4,  +3.3,   0.0],
        [ +6.7, -16.7,  -6.7, +10.0],
        [ +6.7, -10.0,   0.0,   0.0],
    ])
    parse_tags = [
        ["30→30", "30→30", "30→30", "30→30"],
        ["29→29",  "9→12", "26→25", "18→22"],
        ["30→30", "30→30", "30→30", "30→30"],
        ["30→30", "30→30", "30→30", "30→30"],
        ["25→26", "11→7",  "30→29", "11→16"],
        ["30→30", "30→30", "30→30", "30→30"],
    ]

    fig.text(0.012, 0.840, r"(a) Archive Readout Matrix: $\Delta H$ (pp) & $V_O\rightarrow V_C$ (/30)", fontsize=7.8, fontweight="bold", color=COL_INK)
    ax_hm = fig.add_axes([0.135, 0.13, 0.315, 0.63])
    ax_hm.imshow(deltas, cmap="RdBu_r", vmin=-18, vmax=18, aspect="auto")
    for r in range(len(models_prot)):
        for c in range(len(cols_prot)):
            val = deltas[r, c]
            txt_c = "white" if abs(val) >= 11 else COL_INK
            ax_hm.text(c, r - 0.11, f"{val:+.1f}", ha="center", va="center", fontsize=6.8, fontweight="bold", color=txt_c)
            ax_hm.text(c, r + 0.24, parse_tags[r][c], ha="center", va="center", fontsize=5.8, color=txt_c)
    ax_hm.set_xticks(range(len(cols_prot)))
    ax_hm.set_xticklabels(cols_prot, fontsize=6.7, color=COL_INK)
    ax_hm.set_yticks(range(len(models_prot)))
    ax_hm.set_yticklabels(models_prot, fontsize=6.9, color=COL_INK)
    ax_hm.tick_params(length=0)
    for sp in ax_hm.spines.values():
        sp.set_edgecolor(COL_RULE)
        sp.set_linewidth(0.75)

    # Right (b): Top schematic Parse -> Align -> Score + Bottom Pilot vs Full valid parse bars
    fig.text(0.490, 0.840, "(b) Canonical Pipeline & Six-Checkpoint Valid Parse Yield", fontsize=7.8, fontweight="bold", color=COL_INK)
    ax_flow = fig.add_axes([0.490, 0.615, 0.495, 0.195], facecolor="white")
    ax_flow.set_xlim(0, 10)
    ax_flow.set_ylim(0, 2.2)
    ax_flow.axis("off")
    steps = [
        (0.1, 2.2, "1. Raw Output", "strict / flex / molmo2\n/ unit_float_xy"),
        (2.7, 2.2, "2. Parse Coord", "Midpoint if 4-num\nbox in [0, 1000)"),
        (5.3, 2.2, "3. Map Frame", "x = uW / 1000\ny = vH / 1000"),
        (7.9, 2.0, "4. Score Hit", "Point in mask\n$M_i^v$ (768×1024)"),
    ]
    for si, (bx, bw, st, sb) in enumerate(steps):
        ax_flow.add_patch(FancyBboxPatch((bx, 0.15), bw, 1.85, boxstyle="round,pad=0.06,rounding_size=0.14", facecolor=COL_LIGHT, edgecolor=COL_NAVY if si == 0 else COL_RULE, lw=0.8))
        ax_flow.text(bx + 0.5 * bw, 1.48, st, ha="center", va="center", fontsize=6.7, fontweight="bold", color=COL_INK)
        ax_flow.text(bx + 0.5 * bw, 0.72, sb, ha="center", va="center", fontsize=5.8, color=COL_SLATE)
        if si < len(steps) - 1:
            ax_flow.annotate("", xy=(bx + bw + 0.38, 1.08), xytext=(bx + bw + 0.02, 1.08), arrowprops=dict(arrowstyle="-|>", lw=1.0, color=COL_NAVY))

    # Load exact 6-checkpoint pilot & full valid-parse rates
    v1_8b = json.loads((V1_META_DIR / "qualification_8b_v2/qualification_result.json").read_text(encoding="utf-8"))
    v1_32b = json.loads((V1_META_DIR / "qualification_32b_v1/qualification_result.json").read_text(encoding="utf-8"))
    p_rows = []
    specs_v3 = [
        ("Qwen3-VL-32B", "qwen3_vl_32b_r0", v1_32b["valid_points"] / v1_32b["records"] * 100.0),
        ("Molmo2-8B",    "molmo2_8b",       json.loads((runs_dir / "pilot_qualification_molmo2_8b.json").read_text())["mode_stats"]["molmo2_1000"]["valid_rate"] * 100.0),
        ("Qwen3-VL-8B",  "qwen3_vl_8b_r0",  v1_8b["valid_points"] / v1_8b["records"] * 100.0),
        ("InternVL3.5",  "internvl3_5_8b",  json.loads((runs_dir / "pilot_qualification_internvl3_5_8b.json").read_text())["mode_stats"]["strict"]["valid_rate"] * 100.0),
        ("LLaVA-7B",     "llava_next_mistral_7b", json.loads((runs_dir / "pilot_qualification_llava_next_mistral_7b.json").read_text())["mode_stats"]["unit_float_xy"]["valid_rate"] * 100.0),
        ("Qwen3-VL-2B",  "qwen3_vl_2b",     json.loads((runs_dir / "pilot_qualification_qwen3_vl_2b.json").read_text())["mode_stats"]["flex_1000"]["valid_rate"] * 100.0),
    ]
    for lbl, skey, pil_v in specs_v3:
        m = sf["models"][skey]["metrics"]
        full_v = 0.5 * (m["original_valid_point_rate"]["estimate"] + m["converted_valid_point_rate"]["estimate"]) * 100.0
        p_rows.append((lbl, pil_v, full_v))

    ax_bar = fig.add_axes([0.595, 0.13, 0.385, 0.37])
    y_pos = np.arange(len(p_rows))
    h_b = 0.36
    ax_bar.barh(y_pos - h_b / 2, [r[1] for r in p_rows], height=h_b, color="#CBD5E1", edgecolor="#64748B", lw=0.6, label="24-Input Pilot")
    ax_bar.barh(y_pos + h_b / 2, [r[2] for r in p_rows], height=h_b, color=COL_COBALT, edgecolor=COL_NAVY, lw=0.6, label="960-Capture Full")
    ax_bar.axvline(90.0, color=COL_CRIMSON, ls="--", lw=0.95, label="90% Gate")
    for i, (_, pv, fv) in enumerate(p_rows):
        ax_bar.text(fv + 0.5, i + h_b / 2, f"{fv:.1f}%", va="center", ha="left", fontsize=6.1, fontweight="bold", color=COL_NAVY)
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels([r[0] for r in p_rows], fontsize=6.6, color=COL_INK)
    ax_bar.invert_yaxis()
    ax_bar.set_xlim(80, 106)
    ax_bar.set_xlabel("Valid Coordinate Parse Rate (%)", fontsize=6.8, color=COL_SLATE, labelpad=2)
    ax_bar.tick_params(axis="x", labelsize=6.5, colors=COL_SLATE)
    ax_bar.legend(loc="lower center", bbox_to_anchor=(0.45, 1.02), ncol=3, frameon=False, fontsize=5.8, columnspacing=0.9, handlelength=1.4)
    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)

    _save_plate(fig, "app_fig3_readout_and_pilot")


# =============================================================================
# 4. app_fig4_multifamily_gallery.pdf
# =============================================================================
def build_app_fig4(
    sf: dict[str, Any],
    feats: list[dict[str, Any]],
    m_by_oc: dict[tuple[str, str], dict[str, Any]],
    idx_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
    assets_root: Path,
) -> None:
    fig = _start_plate(
        7.2, 5.10,
        "Cross-Family Grounding Divergence (4 Families, 7B–8B) and MDL Dependency-Repair Audit",
        "App. E  |  85.7% (66/77) Single-Architecture Regressions Alongside Historical Repaired Views",
    )

    feat_by_pid = {r["pair_id"]: r for r in feats}
    # Select 4 deterministic visually strong real pairs illustrating the 4 qualitative regimes
    def _pick(cond_fn) -> str:
        cands = []
        for pid, f in feat_by_pid.items():
            if not (0.015 <= math.exp(f["log_area_frac"]) <= 0.14):
                continue
            status = {mk: (bool(idx_by_model[mk][(pid, "original")]["hit"]), bool(idx_by_model[mk][(pid, "converted")]["hit"])) for mk, _, _ in MODEL_SPECS}
            if cond_fn(f, status):
                cands.append((abs(f["target_delta_L"]) + (1.0 - f["target_ssim"]) * 30.0, pid))
        cands.sort(reverse=True)
        return cands[0][1]

    pid_gain = _pick(lambda f, st: f["prior_optical_regime"] == "Reflective/Metallic" and sum(not o and c for o, c in st.values()) >= 2)
    pid_q_loss = _pick(lambda f, st: (st["qwen3_vl_8b_r0"] == (True, False)) and all(c for mk, (_, c) in st.items() if mk != "qwen3_vl_8b_r0"))
    pid_i_loss = _pick(lambda f, st: (st["internvl3_5_8b"] == (True, False)) and all(c for mk, (_, c) in st.items() if mk != "internvl3_5_8b"))
    pid_shared = _pick(lambda f, st: sum(o and not c for o, c in st.values()) >= 3 or (sum(o and not c for o, c in st.values()) >= 2 and sum(not o and not c for o, c in st.values()) <= 1))

    rows_sel = [
        ("Shared Glare\nRecovery",      "≥2 Families Miss→Hit",  pid_gain),
        ("Qwen3-8B Only\nRegression",   "Only Qwen3 Hit→Miss",   pid_q_loss),
        ("InternVL3.5\nRegression",     "Only InternVL Hit→Miss", pid_i_loss),
        ("Multi-Family\nShared Loss",   "Cross-Arch Hit→Miss",   pid_shared),
    ]

    # Top legend strip for Left Gallery cleanly separated from panel (b) and row 1
    fig.text(0.012, 0.878, "(a) 4-Family Point Predictions (Orig MDL vs. Conv Preview)", fontsize=8.0, fontweight="bold", color=COL_INK)
    fig.text(0.012, 0.848, r"$\bullet$ = Hit    $\times$ = Miss    Dashed = $M_i^v$", fontsize=6.5, color=COL_MUTED)
    short_names = ["Molmo2-8B", "Qwen3-8B", "InternVL3.5", "LLaVA-7B"]
    for mi, (sn, (_, _, mcol)) in enumerate(zip(short_names, MODEL_SPECS)):
        fig.text(0.275 + mi * 0.092, 0.848, f"● {sn}", fontsize=6.2, fontweight="bold", color=mcol)
    fig.text(0.250, 0.818, "Original (MDL)", fontsize=7.2, fontweight="bold", color=COL_COBALT, ha="center")
    fig.text(0.502, 0.818, "Converted (UsdPreviewSurface)", fontsize=7.2, fontweight="bold", color=COL_CRIMSON, ha="center")

    fig.add_artist(plt.Line2D([0.642, 0.642], [0.025, 0.895], transform=fig.transFigure, color=COL_RULE, lw=0.75, ls="--"))

    for ri, (rtit, rsub, pid) in enumerate(rows_sel):
        f = feat_by_pid[pid]
        y0 = 0.625 - ri * 0.198
        fig.text(0.010, y0 + 0.130, rtit, fontsize=7.0, fontweight="bold", color=COL_INK, va="center")
        fig.text(0.010, y0 + 0.065, f"{rsub}\n{f['source_category']} · SSIM {f['target_ssim']:.2f}", fontsize=6.1, color=COL_SLATE, va="center")

        rec_o = m_by_oc[(pid, "original")]
        rec_c = m_by_oc[(pid, "converted")]
        msk_o = _load_mask(resolve_asset_path(rec_o["mask"]["path"], assets_root))
        msk_c = _load_mask(resolve_asset_path(rec_c["mask"]["path"], assets_root))
        x0_c, y0_c, x1_c, y1_c = _crop_box_around_mask(msk_o, target_aspect=1.40, pad_frac=1.70)

        for ci, (cond, img_p, msk_full, bcol) in enumerate([
            ("original",  resolve_asset_path(rec_o["image"]["path"], assets_root), msk_o, COL_COBALT),
            ("converted", resolve_asset_path(rec_c["image"]["path"], assets_root), msk_c, COL_CRIMSON),
        ]):
            ax = fig.add_axes([0.132 + ci * 0.252, y0 + 0.012, 0.236, 0.168])
            im = np.asarray(Image.open(img_p).convert("RGB"))[y0_c:y1_c, x0_c:x1_c]
            mc = msk_full[y0_c:y1_c, x0_c:x1_c]
            ax.imshow(im)
            if mc.any():
                ax.contour(mc.astype(float), levels=[0.5], colors=["#0F172A"], linewidths=1.1, alpha=0.5)
                ax.contour(mc.astype(float), levels=[0.5], colors=["#FFFFFF"], linewidths=0.75, linestyles="--", alpha=0.92)
            for mk, _, mcol in MODEL_SPECS:
                pr = idx_by_model[mk][(pid, cond)]
                ptn = pr.get("point_normalized")
                if ptn is None:
                    continue
                px = min(max(float(ptn[0]) * IMAGE_WIDTH / 1000.0 - x0_c, 6.0), (x1_c - x0_c) - 6.0)
                py = min(max(float(ptn[1]) * IMAGE_HEIGHT / 1000.0 - y0_c, 6.0), (y1_c - y0_c) - 6.0)
                hit = bool(pr["hit"])
                ax.scatter([px], [py], s=44 if hit else 50, marker="o" if hit else "X", color=mcol, edgecolors="white", linewidths=0.9, zorder=6)
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_edgecolor(bcol)
                sp.set_linewidth(0.75)

    # Right Top (b): 4-Family Regression Overlap Histogram
    fig.text(0.658, 0.878, "(b) 4-Family Overlap (n=480)", fontsize=8.0, fontweight="bold", color=COL_INK)
    ov = sf["family_overlap_4x8b"]
    l_hist = [ov["loss_count_histogram"][str(k)] for k in (1, 2, 3, 4)]
    g_hist = [ov["gain_count_histogram"][str(k)] for k in (1, 2, 3, 4)]
    ax_ov = fig.add_axes([0.698, 0.560, 0.285, 0.275])
    xs = np.arange(1, 5)
    ax_ov.bar(xs - 0.18, l_hist, width=0.34, color=COL_CRIMSON, edgecolor="#991B1B", lw=0.6, label="Loss (Hit→Miss)")
    ax_ov.bar(xs + 0.18, g_hist, width=0.34, color=COL_TEAL, edgecolor="#0F766E", lw=0.6, label="Gain (Miss→Hit)")
    for xi, lv, gv in zip(xs, l_hist, g_hist):
        ax_ov.text(xi - 0.18, lv + 1.5, str(lv), ha="center", va="bottom", fontsize=6.4, fontweight="bold", color="#991B1B")
        ax_ov.text(xi + 0.18, gv + 1.5, str(gv), ha="center", va="bottom", fontsize=6.4, fontweight="bold", color="#0F766E")
    ax_ov.text(0.96, 0.50, f"1-Model Only:\n{ov['single_family_only_share_of_losses']*100:.1f}% losses", transform=ax_ov.transAxes, ha="right", fontsize=6.4, fontweight="bold", color=COL_NAVY,
               bbox=dict(boxstyle="square,pad=0.22", facecolor=COL_LIGHT, edgecolor=COL_RULE, lw=0.6))
    ax_ov.set_xticks(xs)
    ax_ov.set_xticklabels(["1 Fam", "2 Fam", "3 Fam", "All 4"], fontsize=6.6, color=COL_INK)
    ax_ov.set_ylim(0, max(l_hist + g_hist) * 1.28)
    ax_ov.set_ylabel("Pairs (of 480)", fontsize=6.8, color=COL_SLATE)
    ax_ov.tick_params(axis="y", labelsize=6.4, colors=COL_SLATE)
    ax_ov.legend(loc="upper right", frameon=False, fontsize=6.1)
    ax_ov.spines["top"].set_visible(False)
    ax_ov.spines["right"].set_visible(False)

    # Right Bottom (c): Historical MDL Dependency-Repair Qualitative Pairs (Cup + Faucet)
    fig.text(0.658, 0.450, "(c) MDL-Repaired Qualitative Audit", fontsize=8.0, fontweight="bold", color=COL_INK)
    fig.text(0.658, 0.422, "Separate from inference; 0 shader errors", fontsize=6.2, color=COL_MUTED)
    fig.text(0.735, 0.394, "Orig (MDL)", fontsize=6.2, fontweight="bold", color=COL_COBALT, ha="center")
    fig.text(0.905, 0.394, "Conv (Preview)", fontsize=6.2, fontweight="bold", color=COL_CRIMSON, ha="center")
    rer = json.loads((RAW_DIR / "iclr_model_behavior/appendix_rerender_v1/manifest.json").read_text(encoding="utf-8"))
    rer_idx = {(r["pair_id"], r["condition"]): _map_repo_path(r["image"]["path"]) for r in rer["records"]}
    rer_cases = [("Glass Cup (Repaired)", "bb985fd4504a1afe8516.zoom_017"), ("Chrome Faucet (Repaired)", "c8ee4b66274b05d242c2.zoom_017")]
    for r_i, (rname, rpid) in enumerate(rer_cases):
        yr = 0.215 - r_i * 0.190
        fig.text(0.658, yr + 0.148, rname, fontsize=6.6, fontweight="bold", color=COL_INK)
        _show_image_ax(fig, [0.658, yr + 0.010, 0.155, 0.130], rer_idx[(rpid, "original")], border_col=COL_COBALT, border_lw=0.65)
        _show_image_ax(fig, [0.828, yr + 0.010, 0.155, 0.130], rer_idx[(rpid, "converted")], border_col=COL_CRIMSON, border_lw=0.65)

    _save_plate(fig, "app_fig4_multifamily_gallery")


# =============================================================================
# 5. app_fig5_features_and_counterfactuals.pdf
# =============================================================================
def build_app_fig5(ra: dict[str, Any], om: dict[str, Any]) -> None:
    fig = _start_plate(
        7.2, 3.45,
        "21-Feature Standardized Risk-Gate Weights and Dual-Family Counterfactual Comparison",
        "App. F  |  any_8b_32b_loss (C=0.01) & Paired 2,880-Evaluation Attribution",
    )

    # Left (a): All 21 standardized coefficients sorted by |w|
    fig.text(0.012, 0.855, "(a) Standardized L2 Logistic Weights (21 Auto Features)", fontsize=7.9, fontweight="bold", color=COL_INK)
    coefs = ra["targets"]["any_8b_32b_loss"]["deploy_auto"]["standardized_coefficients_train_fit"]
    coefs_s = sorted(coefs, key=lambda d: abs(d["coef"]), reverse=True)
    geom_set = {"log_area_frac", "aspect_ratio", "center_dist_norm", "border_touch", "mask_iou"}
    names = [c["feature"].replace("cat_is_", "cat:").replace("_appliance_or_metal", "_metal").replace("_transparent_or_glass", "_glass").replace("_or_screen", "_screen") for c in coefs_s]
    vals = [c["coef"] for c in coefs_s]
    bar_cols = [
        COL_NAVY if c["feature"] in geom_set else (COL_AMBER if c["feature"].startswith("cat_is_") else COL_TEAL)
        for c in coefs_s
    ]

    ax_w = fig.add_axes([0.215, 0.11, 0.285, 0.70])
    ys = np.arange(len(names))
    ax_w.barh(ys, vals, height=0.68, color=bar_cols, edgecolor="none", alpha=0.92)
    ax_w.axvline(0.0, color=COL_INK, lw=0.8)
    ax_w.set_yticks(ys)
    ax_w.set_yticklabels(names, fontsize=5.8, color=COL_INK)
    ax_w.invert_yaxis()
    ax_w.set_xlabel("Standardized L2 Weight (C = 0.01)", fontsize=6.6, color=COL_SLATE)
    ax_w.tick_params(axis="x", labelsize=6.3, colors=COL_SLATE)
    ax_w.set_xlim(-0.072, 0.072)
    leg_p = [Patch(facecolor=COL_NAVY, label="Geom (5)"), Patch(facecolor=COL_TEAL, label="Optical Δ (13)"), Patch(facecolor=COL_AMBER, label="Prior (3)")]
    ax_w.legend(handles=leg_p, loc="lower right", frameon=True, facecolor="white", edgecolor=COL_RULE, fontsize=5.7)
    ax_w.spines["top"].set_visible(False)
    ax_w.spines["right"].set_visible(False)

    # Right (b): Top = All-480 vs Exact-473 Residual; Bottom = 4 Prior Regimes Net Delta across Qwen3-VL-8B & InternVL3.5-8B-HF
    fig.text(0.535, 0.855, "(b) Dual-Family Counterfactuals (Qwen3-8B vs. InternVL3.5)", fontsize=7.9, fontweight="bold", color=COL_INK)

    ax_top = fig.add_axes([0.585, 0.53, 0.395, 0.26])
    q_all = om["by_model"]["qwen3_vl_8b"]["all_480_pairs"]["full_minus_photometric_flip_rate"]
    q_ex = om["by_model"]["qwen3_vl_8b"]["exact_473_identical_mask_pairs"]["full_minus_photometric_flip_rate"]
    i_all = om["by_model"]["internvl3_5_8b"]["all_480_pairs"]["full_minus_photometric_flip_rate"]
    i_ex = om["by_model"]["internvl3_5_8b"]["exact_473_identical_mask_pairs"]["full_minus_photometric_flip_rate"]

    x_g = np.array([0, 1])
    w_g = 0.32
    q_y = [q_all["difference"] * 100.0, q_ex["difference"] * 100.0]
    i_y = [i_all["difference"] * 100.0, i_ex["difference"] * 100.0]
    q_err = [[(q_all["difference"] - q_all["paired_scene_bootstrap_ci95"][0]) * 100.0, (q_ex["difference"] - q_ex["paired_scene_bootstrap_ci95"][0]) * 100.0],
             [(q_all["paired_scene_bootstrap_ci95"][1] - q_all["difference"]) * 100.0, (q_ex["paired_scene_bootstrap_ci95"][1] - q_ex["difference"]) * 100.0]]
    i_err = [[(i_all["difference"] - i_all["paired_scene_bootstrap_ci95"][0]) * 100.0, (i_ex["difference"] - i_ex["paired_scene_bootstrap_ci95"][0]) * 100.0],
             [(i_all["paired_scene_bootstrap_ci95"][1] - i_all["difference"]) * 100.0, (i_ex["paired_scene_bootstrap_ci95"][1] - i_ex["difference"]) * 100.0]]
    ax_top.bar(x_g - w_g / 2, q_y, width=w_g, color=COL_COBALT, label="Qwen3-VL-8B", yerr=q_err, capsize=3, error_kw=dict(lw=0.9, ecolor=COL_NAVY))
    ax_top.bar(x_g + w_g / 2, i_y, width=w_g, color=COL_CRIMSON, label="InternVL3.5-8B", yerr=i_err, capsize=3, error_kw=dict(lw=0.9, ecolor="#7F1D1D"))
    for xi, qv, iv in zip(x_g, q_y, i_y):
        ax_top.text(xi - w_g / 2, qv + q_err[1][xi] + 0.3, f"+{qv:.2f}%", ha="center", va="bottom", fontsize=6.1, fontweight="bold", color=COL_COBALT)
        ax_top.text(xi + w_g / 2, iv + i_err[1][xi] + 0.3, f"+{iv:.2f}%", ha="center", va="bottom", fontsize=6.1, fontweight="bold", color=COL_CRIMSON)
    ax_top.set_xticks(x_g)
    ax_top.set_xticklabels(["All 480 Pairs\n(Non-Photo Residual)", "Exact-Mask 473\n(IoU = 1.000)"], fontsize=6.6, color=COL_INK)
    ax_top.set_ylabel("F − Photo (%)", fontsize=6.7, color=COL_SLATE)
    ax_top.set_ylim(0, 9.8)
    ax_top.tick_params(axis="y", labelsize=6.3, colors=COL_SLATE)
    ax_top.legend(loc="upper right", frameon=False, fontsize=6.0, ncol=2)
    ax_top.spines["top"].set_visible(False)
    ax_top.spines["right"].set_visible(False)

    # Bottom right: Net ΔH across 4 optical regimes
    ax_bot = fig.add_axes([0.585, 0.11, 0.395, 0.30])
    reg_order = [("Reflective/\nMetallic", "Reflective/Metallic"), ("Emissive/\nScreen", "Emissive/Screen"),
                 ("Transparent/\nGlass", "Transparent/Glass"), ("Matte/\nDiffuse", "Matte/Diffuse")]
    xr = np.arange(len(reg_order))
    q_regs = [om["by_model"]["qwen3_vl_8b"]["stratified_by_prior_optical_regime"][k]["net_delta"]["estimate"] * 100.0 for _, k in reg_order]
    i_regs = [om["by_model"]["internvl3_5_8b"]["stratified_by_prior_optical_regime"][k]["net_delta"]["estimate"] * 100.0 for _, k in reg_order]
    ax_bot.axhline(0.0, color=COL_INK, lw=0.75)
    ax_bot.bar(xr - w_g / 2, q_regs, width=w_g, color=COL_COBALT)
    ax_bot.bar(xr + w_g / 2, i_regs, width=w_g, color=COL_CRIMSON)
    for xi, qv, iv in zip(xr, q_regs, i_regs):
        ax_bot.text(xi - w_g / 2, qv + (0.3 if qv >= 0 else -0.4), f"{qv:+.1f}%", ha="center", va="bottom" if qv >= 0 else "top", fontsize=5.9, fontweight="bold", color=COL_COBALT)
        ax_bot.text(xi + w_g / 2, iv + (0.3 if iv >= 0 else -0.4), f"{iv:+.1f}%", ha="center", va="bottom" if iv >= 0 else "top", fontsize=5.9, fontweight="bold", color=COL_CRIMSON)
    ax_bot.set_xticks(xr)
    ax_bot.set_xticklabels([lbl for lbl, _ in reg_order], fontsize=6.3, color=COL_INK)
    ax_bot.set_ylabel("Net ΔH (%)", fontsize=6.7, color=COL_SLATE)
    ax_bot.set_ylim(-2.8, 9.2)
    ax_bot.tick_params(axis="y", labelsize=6.3, colors=COL_SLATE)
    ax_bot.spines["top"].set_visible(False)
    ax_bot.spines["right"].set_visible(False)

    _save_plate(fig, "app_fig5_features_and_counterfactuals")


# =============================================================================
# 6 & 7. Consolidated Full-Width Navigation Plates (app_fig6 & app_fig7)
# =============================================================================
def _build_nav_plate(cases: list[tuple[str, str, str]], still_dir: Path, title: str, right_tag: str, stem: str) -> None:
    """Render 6 navigation episodes in a crisp 2-col x 3-row panoramic plate."""
    fig = _start_plate(7.2, 4.85, title, right_tag)
    fig.text(0.012, 0.014, "Overlays: Red = executed trajectory    Green = reference path    Separate qualitative video reruns from 99-pair metric evaluations.", fontsize=6.7, color=COL_SLATE)

    ncols, nrows = 2, 3
    x_start, y_top = 0.012, 0.868
    cell_w, cell_h = 0.484, 0.268
    gap_x, gap_y = 0.012, 0.012

    # Column-level Start / Middle / End header labels across top of both panel columns
    for ci in range(ncols):
        cx0 = x_start + ci * (cell_w + gap_x)
        for ji, clbl in enumerate(["Start", "Middle", "End"]):
            fig.text(cx0 + 0.045 + (ji + 0.5) * 0.145, 0.880, clbl, fontsize=6.7, fontweight="bold", color=COL_NAVY, ha="center", va="center")

    for idx_c, (group_tag, pkey, scene_lbl) in enumerate(cases):
        ri, ci = divmod(idx_c, ncols)
        x0 = x_start + ci * (cell_w + gap_x)
        yb = y_top - (ri + 1) * cell_h - ri * gap_y

        fig.patches.append(Rectangle((x0, yb), cell_w, cell_h, transform=fig.transFigure, fill=False, edgecolor=COL_RULE, lw=0.75))
        fig.patches.append(Rectangle((x0, yb + cell_h - 0.036), cell_w, 0.036, transform=fig.transFigure, facecolor=COL_LIGHT, edgecolor="none"))
        fig.patches.append(Rectangle((x0, yb + cell_h - 0.036), 0.0045, 0.036, transform=fig.transFigure, facecolor=COL_NAVY, edgecolor="none"))
        ep_id = pkey.split("_")[0]
        fig.text(x0 + 0.010, yb + cell_h - 0.018, f"Episode {ep_id} · Scene {scene_lbl}", fontsize=7.0, fontweight="bold", color=COL_INK, va="center")

        for vi, (ver, vlbl, vcol) in enumerate([("original", "Orig", COL_COBALT), ("nomdl", "Conv", COL_CRIMSON)]):
            yv = yb + cell_h - 0.042 - (vi + 1) * 0.107
            fig.text(x0 + 0.022, yv + 0.050, vlbl, fontsize=6.2, fontweight="bold", color=vcol, rotation=90, va="center", ha="center")
            for ji, st_name in enumerate(["start", "mid", "end"]):
                matches = list(still_dir.glob(f"{group_tag}_{pkey}_{ver}_{st_name}_*.png"))
                if len(matches) != 1:
                    raise FileNotFoundError(f"Expected 1 still for {group_tag} {pkey} {ver} {st_name}, got {matches}")
                _show_image_ax(fig, [x0 + 0.045 + ji * 0.145, yv + 0.004, 0.139, 0.098], matches[0], border_col=vcol, border_lw=0.55)

    _save_plate(fig, stem)


def build_nav_plates() -> None:
    base = RAW_DIR / "internnav_vln_downstream/official_selected_qualitative_videos"
    q31 = json.loads((base / "manifests/kujiale0031_video_basic_qa.json").read_text(encoding="utf-8"))
    keys31 = list(dict.fromkeys(r["path_key"] for r in q31["video_records"]))
    cases31 = [("kujiale0031", k, "0031") for k in keys31[:6]]
    _build_nav_plate(
        cases31, base / "stills/kujiale0031",
        "Closed-Loop Navigation Reruns (1/2): Scene 0031 Across Six Paired Episodes",
        "App. G  |  DualVLN Scene 0031 (Original MDL vs. Converted Preview)",
        "app_fig6_nav_plate1",
    )

    c36 = json.loads((base / "manifests/kujiale0036_0066_video_case_manifest.json").read_text(encoding="utf-8"))["selected_cases"]
    cases36 = [("kujiale0036_0066", r["path_key"], r["scene_id"].split("_")[-1]) for r in c36[:6]]
    _build_nav_plate(
        cases36, base / "stills/kujiale0036_0066",
        "Closed-Loop Navigation Reruns (2/2): Scenes 0066 & 0036 Across Six Paired Episodes",
        "App. G  |  DualVLN Scenes 0066 & 0036 (Original MDL vs. Converted Preview)",
        "app_fig7_nav_plate2",
    )


# =============================================================================
# Three Rich Automated LaTeX Table* Files (tables/app_*.tex)
# =============================================================================
def write_appendix_tables(
    scenes_meta: list[dict[str, Any]],
    feats: list[dict[str, Any]],
    idx_by_model: dict[str, dict[tuple[str, str], dict[str, Any]]],
    om: dict[str, Any],
    ra: dict[str, Any],
) -> None:
    OUT_TAB_DIR.mkdir(parents=True, exist_ok=True)
    feats_by_sc: dict[str, list[dict[str, Any]]] = {}
    for r in feats:
        feats_by_sc.setdefault(r["scene_id"], []).append(r)

    # -------------------------------------------------------------------------
    # Table 1: app_scenes30.tex (all 30 scenes x 5 representative checkpoints)
    # -------------------------------------------------------------------------
    sorted_all = sorted(scenes_meta, key=lambda x: (x["split"] != "train", x["split"] != "validation", x["family"] != "home_scenes", x["scene_id"]))
    h_idx, c_idx = 0, 0
    lines_30 = [
        "% Generated automatically by build_cviu_appendix_assets.py from pair_optical_features.json and v3 predictions",
        "\\begin{tabular}{@{}llllcrrrrrrr@{}}",
        "\\toprule",
        "Code & Scene ID & Dom. & Split & RM/TG/MD/ES & SSIM & $\\Delta L^*$ & Qwen3-8B & Qwen3-32B & InternVL3.5 & Molmo2-8B & LLaVA-7B \\\\",
        "\\midrule",
    ]
    tbl_models = ["qwen3_vl_8b_r0", "qwen3_vl_32b_r0", "internvl3_5_8b", "molmo2_8b", "llava_next_mistral_7b"]

    prev_split = None
    for s in sorted_all:
        sid = s["scene_id"]
        spl = s["split"]
        if prev_split is not None and spl != prev_split:
            lines_30.append("\\midrule")
        prev_split = spl
        if s["family"] == "home_scenes":
            h_idx += 1
            code = f"H{h_idx:02d}"
            dom = "Home"
        else:
            c_idx += 1
            code = f"C{c_idx:02d}"
            dom = "Comm"
        sc_f = feats_by_sc[sid]
        rm = sum(1 for f in sc_f if f["prior_optical_regime"] == "Reflective/Metallic")
        tg = sum(1 for f in sc_f if f["prior_optical_regime"] == "Transparent/Glass")
        md = sum(1 for f in sc_f if f["prior_optical_regime"] == "Matte/Diffuse")
        es = sum(1 for f in sc_f if f["prior_optical_regime"] == "Emissive/Screen")
        ssim_m = np.mean([f["target_ssim"] for f in sc_f])
        dl_m = np.mean([f["target_delta_L"] for f in sc_f])

        m_cells = []
        for mk in tbl_models:
            im = idx_by_model[mk]
            ho = np.mean([bool(im[(f["pair_id"], "original")]["hit"]) for f in sc_f]) * 100.0
            hc = np.mean([bool(im[(f["pair_id"], "converted")]["hit"]) for f in sc_f]) * 100.0
            fl = np.mean([bool(im[(f["pair_id"], "original")]["hit"]) != bool(im[(f["pair_id"], "converted")]["hit"]) for f in sc_f]) * 100.0
            m_cells.append(f"{ho:.0f}/{hc:.0f} ({fl:.1f})")
        spl_s = "Train" if spl == "train" else ("Val" if spl == "validation" else "Test")
        uid_s = f"{sid[:4]}..{sid.replace('_usd', '')[-4:]}"
        lines_30.append(
            f"{code} & \\texttt{{{uid_s}}} & {dom} & {spl_s} & {rm}/{tg}/{md}/{es} & {ssim_m:.2f} & {dl_m:.1f} & "
            + " & ".join(m_cells) + " \\\\"
        )

    # All-30 summary row
    rm_t = sum(1 for f in feats if f["prior_optical_regime"] == "Reflective/Metallic")
    tg_t = sum(1 for f in feats if f["prior_optical_regime"] == "Transparent/Glass")
    md_t = sum(1 for f in feats if f["prior_optical_regime"] == "Matte/Diffuse")
    es_t = sum(1 for f in feats if f["prior_optical_regime"] == "Emissive/Screen")
    all_cells = []
    for mk in tbl_models:
        im = idx_by_model[mk]
        ho = np.mean([bool(im[(f["pair_id"], "original")]["hit"]) for f in feats]) * 100.0
        hc = np.mean([bool(im[(f["pair_id"], "converted")]["hit"]) for f in feats]) * 100.0
        fl = np.mean([bool(im[(f["pair_id"], "original")]["hit"]) != bool(im[(f["pair_id"], "converted")]["hit"]) for f in feats]) * 100.0
        all_cells.append(f"\\textbf{{{ho:.1f}/{hc:.1f} ({fl:.1f})}}")
    lines_30 += [
        "\\midrule",
        f"\\textbf{{All 30}} & \\textbf{{480 pairs}} & 20H/10C & 15/5/10 & \\textbf{{{rm_t}/{tg_t}/{md_t}/{es_t}}} & "
        f"\\textbf{{{np.mean([f['target_ssim'] for f in feats]):.2f}}} & \\textbf{{{np.mean([f['target_delta_L'] for f in feats]):.1f}}} & "
        + " & ".join(all_cells) + " \\\\",
        "\\bottomrule",
        "\\end{tabular}",
    ]
    (OUT_TAB_DIR / "app_scenes30.tex").write_text("\n".join(lines_30) + "\n", encoding="utf-8")

    # -------------------------------------------------------------------------
    # Table 2: app_counterfactual_dual.tex (Dual-family factorial & regimes)
    # -------------------------------------------------------------------------
    q_om = om["by_model"]["qwen3_vl_8b"]
    i_om = om["by_model"]["internvl3_5_8b"]

    def _ci_fmt(node: dict[str, Any], key: str = "estimate", ci_key: str = "scene_bootstrap_ci95", scale: float = 100.0, signed: bool = False) -> str:
        val = node[key] * scale
        lo, hi = node[ci_key][0] * scale, node[ci_key][1] * scale
        sign = "+" if (signed and val >= 0) else ""
        return f"{sign}{val:.2f} [{lo:+.2f}, {hi:+.2f}]" if signed else f"{val:.2f} [{lo:.2f}, {hi:.2f}]"

    lines_cf = [
        "% Generated automatically by build_cviu_appendix_assets.py from optical_mechanisms.json",
        "\\begin{tabular}{@{}lrrrr@{}}",
        "\\toprule",
        "Subgroup / Counterfactual Contrast & Pairs ($n$) & Metric & \\textsc{Qwen3-VL-8B} (\\% / 95\\% CI) & \\textsc{InternVL3.5-8B-HF} (\\% / 95\\% CI) \\\\",
        "\\midrule",
        "\\multicolumn{5}{@{}l}{\\textit{Panel A: Factorial Counterfactual Contrast (All 480 Pairs vs.\\ Exact-Mask 473 Subset, $\\mathrm{IoU}=1.000$)}} \\\\",
    ]
    cf_rows = [
        ("Photometric Matched ($I^{\\text{photo}}$ vs.\\ $I^O$)", "all_480_pairs", ("flips_vs_original", "photo"), "Flip\\%", False),
        ("Background Swap Only ($I^B$ vs.\\ $I^O$)",               "all_480_pairs", ("flips_vs_original", "B"),     "Flip\\%", False),
        ("Target Silhouette Only ($I^T$ vs.\\ $I^O$)",             "all_480_pairs", ("flips_vs_original", "T"),     "Flip\\%", False),
        ("Full Conversion ($I^F$ vs.\\ $I^O$)",                    "all_480_pairs", ("flips_vs_original", "F"),     "Flip\\%", False),
        ("Non-Photometric Residual ($I^F - I^{\\text{photo}}$)",   "all_480_pairs", ("full_minus_photometric_flip_rate", None), "$\\Delta$Flip", True),
        ("Exact-Mask Residual ($\\mathrm{IoU}=1.000$, $n{=}473$)", "exact_473_identical_mask_pairs", ("full_minus_photometric_flip_rate", None), "$\\Delta$Flip", True),
    ]
    for lbl, sub_k, (k1, k2), mlbl, is_diff in cf_rows:
        qn = q_om[sub_k][k1][k2] if k2 else q_om[sub_k][k1]
        in_ = i_om[sub_k][k1][k2] if k2 else i_om[sub_k][k1]
        n_p = q_om[sub_k]["pair_count"]
        q_str = _ci_fmt(qn, "difference" if is_diff else "estimate", "paired_scene_bootstrap_ci95" if is_diff else "scene_bootstrap_ci95", signed=is_diff)
        i_str = _ci_fmt(in_, "difference" if is_diff else "estimate", "paired_scene_bootstrap_ci95" if is_diff else "scene_bootstrap_ci95", signed=is_diff)
        lines_cf.append(f"{lbl} & {n_p} & {mlbl} & {q_str} & {i_str} \\\\")

    lines_cf += [
        "\\midrule",
        "\\multicolumn{5}{@{}l}{\\textit{Panel B: Prior Surface Optical Regimes ($\\Delta H = H_C - H_O$ and Flip Rate)}} \\\\",
    ]
    for reg in ("Reflective/Metallic", "Emissive/Screen", "Transparent/Glass", "Matte/Diffuse"):
        qr = q_om["stratified_by_prior_optical_regime"][reg]
        ir = i_om["stratified_by_prior_optical_regime"][reg]
        n_r = qr["pair_count"]
        lines_cf.append(
            f"{reg} & {n_r} & $\\Delta H$ (Flip) & "
            f"{qr['net_delta']['estimate']*100:+.2f}\\% ({qr['flip_rate']['estimate']*100:.2f}\\%) & "
            f"{ir['net_delta']['estimate']*100:+.2f}\\% ({ir['flip_rate']['estimate']*100:.2f}\\%) \\\\"
        )

    lines_cf += [
        "\\midrule",
        "\\multicolumn{5}{@{}l}{\\textit{Panel C: Objective Pixel-Distortion Regimes (Independent of Category Labels)}} \\\\",
    ]
    for reg in ("Low-Distortion", "Texture/Detail-Degraded", "Specular-Stripped", "Mask/Opacity-Shift"):
        qr = q_om["stratified_by_pixel_optical_regime"][reg]
        ir = i_om["stratified_by_pixel_optical_regime"][reg]
        n_r = qr["pair_count"]
        lines_cf.append(
            f"{reg} & {n_r} & $\\Delta H$ (Flip) & "
            f"{qr['net_delta']['estimate']*100:+.2f}\\% ({qr['flip_rate']['estimate']*100:.2f}\\%) & "
            f"{ir['net_delta']['estimate']*100:+.2f}\\% ({ir['flip_rate']['estimate']*100:.2f}\\%) \\\\"
        )
    lines_cf += ["\\bottomrule", "\\end{tabular}"]
    (OUT_TAB_DIR / "app_counterfactual_dual.tex").write_text("\n".join(lines_cf) + "\n", encoding="utf-8")

    # -------------------------------------------------------------------------
    # Table 3: app_features21.tex (Complete 21-feature inventory + AUROC + L2 weight)
    # -------------------------------------------------------------------------
    idx8 = idx_by_model["qwen3_vl_8b_r0"]
    idx32 = idx_by_model["qwen3_vl_32b_r0"]
    y_loss = np.array(
        [
            int(
                (bool(idx8[(r["pair_id"], "original")]["hit"]) and not bool(idx8[(r["pair_id"], "converted")]["hit"]))
                or (bool(idx32[(r["pair_id"], "original")]["hit"]) and not bool(idx32[(r["pair_id"], "converted")]["hit"]))
            )
            for r in feats
        ],
        dtype=np.int64,
    )
    w_map = {
        d["feature"]: d["coef"]
        for d in ra["targets"]["any_8b_32b_loss"]["deploy_auto"]["standardized_coefficients_train_fit"]
    }

    desc_map = {
        "log_area_frac": "Logarithm of target pixel area fraction",
        "aspect_ratio": "Target bounding-box width-to-height ratio",
        "center_dist_norm": "Euclidean distance from frame center (normalized)",
        "border_touch": "Indicator whether target bbox touches image border",
        "mask_iou": "Mask overlap IoU between original and converted captures",
        "global_rgb_mae": "Full-frame mean absolute RGB difference",
        "target_rgb_mae": "Target-mask mean absolute RGB difference",
        "bg_rgb_mae": "Background mean absolute RGB difference",
        "target_delta_L": "Mean target lightness shift $|\\Delta L^*|$",
        "target_delta_ab": "Mean target chromatic shift $\\|\\Delta(a^*, b^*)\\|_2$",
        "target_std_L_ratio": "Converted-to-original lightness std ratio on target",
        "target_ssim": "Local $8{\\times}8$ structural similarity inside target",
        "bg_ssim": "Local $8{\\times}8$ structural similarity on background",
        "target_sobel_edge_ratio": "Converted-to-original Sobel $|\\nabla L^*|$ ratio on target",
        "target_specular_delta": "Highlight pixel ($Y>0.88$) fraction shift on target",
        "ring_specular_delta": "12-px exterior ring specular fraction shift",
        "boundary_contrast_delta": "8-px inner/outer contour lightness contrast shift",
        "boundary_contrast_delta_lab": "8-px inner/outer contour $\\mathrm{CIE}~\\Delta E_{ab}^*$ shift",
        "cat_is_transparent_or_glass": "Transparent/glass object category prior",
        "cat_is_reflective_appliance_or_metal": "Reflective appliance/metal category prior",
        "cat_is_emissive_or_screen": "Emissive/screen category prior",
    }

    geom_cols = ["log_area_frac", "aspect_ratio", "center_dist_norm", "border_touch", "mask_iou"]
    prior_cols = [c for c in DEPLOY_AUTO_FEATURES if c.startswith("cat_is_")]
    opt_cols = [c for c in DEPLOY_AUTO_FEATURES if c not in geom_cols and c not in prior_cols]

    lines_f = [
        "% Generated automatically by build_cviu_appendix_assets.py from pair_optical_features.json & risk_auditor.json",
        "\\begin{tabular}{@{}llrrrr@{}}",
        "\\toprule",
        "Feature Name & Definition & No-Loss ($n{=}455$) & Loss ($n{=}25$) & Univar.\\ AUROC & $\\ell_2$ Weight $w_j$ \\\\",
        "\\midrule",
    ]
    for grp_title, grp_cols in [
        ("Simulator Mask Geometry (5)", geom_cols),
        ("Paired Optical, Chromatic \\& Structural Deltas (13)", opt_cols),
        ("Coarse Target Category Priors (3)", prior_cols),
    ]:
        lines_f.append(f"\\multicolumn{{6}}{{@{{}}l}}{{\\textit{{{grp_title}}}}} \\\\")
        for col in grp_cols:
            vals = np.array([float(r[col]) for r in feats], dtype=np.float64)
            v0, v1 = vals[y_loss == 0], vals[y_loss == 1]
            auc_pos = roc_auc_score_np(y_loss, vals) or 0.5
            auc_dir = max(auc_pos, 1.0 - auc_pos)
            lbl_tex = col.replace("_", "\\_")
            lines_f.append(
                f"\\texttt{{{lbl_tex}}} & {desc_map[col]} & "
                f"{v0.mean():.3f} $\\pm$ {v0.std():.3f} & {v1.mean():.3f} $\\pm$ {v1.std():.3f} & "
                f"{auc_dir:.3f} & {w_map[col]:+.4f} \\\\"
            )
        lines_f.append("\\midrule")
    lines_f[-1] = "\\bottomrule"
    lines_f.append("\\end{tabular}")
    (OUT_TAB_DIR / "app_features21.tex").write_text("\n".join(lines_f) + "\n", encoding="utf-8")
    print("[ok] wrote app_scenes30.tex, app_counterfactual_dual.tex, app_features21.tex")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-root", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\assets\cviu"))
    parser.add_argument("--v1-runs-dir", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\assets\cviu\formal_model_runs_v1"))
    parser.add_argument("--v3-runs-dir", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\runs"))
    args = parser.parse_args()

    sf = json.loads((V3_RAW_DIR / "scaling_and_families.json").read_text(encoding="utf-8"))
    om = json.loads((V3_RAW_DIR / "optical_mechanisms.json").read_text(encoding="utf-8"))
    ra = json.loads((V3_RAW_DIR / "risk_auditor.json").read_text(encoding="utf-8"))
    feats = json.loads((V3_RAW_DIR / "pair_optical_features.json").read_text(encoding="utf-8"))["records"]
    scenes_meta = json.loads((V1_META_DIR / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    manifest = json.loads((V1_META_DIR / "manifest.json").read_text(encoding="utf-8"))["records"]
    m_by_oc = {(r["pair_id"], r["condition"]): r for r in manifest}

    idx_by_model = {
        "qwen3_vl_8b_r0":        _index_oc(args.v1_runs_dir / "8b/formal_repeat0/predictions.jsonl"),
        "qwen3_vl_32b_r0":       _index_oc(args.v1_runs_dir / "32b/formal_repeat0/predictions.jsonl"),
        "molmo2_8b":             _index_oc(args.v3_runs_dir / "formal_molmo2_8b/predictions.jsonl"),
        "internvl3_5_8b":        _index_oc(args.v3_runs_dir / "formal_internvl3_5_8b/predictions.jsonl"),
        "llava_next_mistral_7b": _index_oc(args.v3_runs_dir / "formal_llava_next_mistral_7b/predictions.jsonl"),
    }

    build_app_fig1()
    build_app_fig2(scenes_meta, feats, m_by_oc, idx_by_model, args.assets_root)
    build_app_fig3(sf, args.v3_runs_dir)
    build_app_fig4(sf, feats, m_by_oc, idx_by_model, args.assets_root)
    build_app_fig5(ra, om)
    build_nav_plates()
    write_appendix_tables(scenes_meta, feats, idx_by_model, om, ra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
