#!/usr/bin/env python3
"""Generate Figures 2-6 in WET-OP Bench (CVPR 2027) vector serif & palette styling."""

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, TextArea, VPacker
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Rectangle, Wedge
import numpy as np
from PIL import Image

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[4]
sys.path.insert(0, str(THIS_DIR))

from optical_and_risk_features import DEPLOY_AUTO_FEATURES  # noqa: E402
from v3_common import fit_standardized_l2_logreg, predict_proba_logreg  # noqa: E402

V3_RAW_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_v3"
V1_META_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_formal/v1"
NAV_99_SUMMARY = REPO_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/paired_99_summary.json"
NAV_99_SCENES = REPO_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/per_scene_aggregate_summary.json"
FIG_DIR = REPO_ROOT / "paper/venues/cviu/figures"
PREVIEW_DIR = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\fig_previews"
)

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8.2,
        "axes.labelsize": 8.4,
        "axes.titlesize": 8.8,
        "legend.fontsize": 7.0,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "axes.linewidth": 0.75,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

PALETTE = {
    "qwen3_vl_2b": ("Qwen3-VL-2B", "#64748B", "v", ":"),
    "qwen3_vl_8b_r0": ("Qwen3-VL-8B", "#0D9488", "s", "-"),
    "qwen3_vl_32b_r0": ("Qwen3-VL-32B", "#2563EB", "o", "-"),
    "internvl3_5_8b": ("InternVL3.5-8B", "#E11D48", "^", "-."),
    "molmo2_8b": ("Molmo2-8B", "#7C3AED", "D", "--"),
    "llava_next_mistral_7b": ("LLaVA-NeXT-Mistral-7B", "#D97706", "P", "-."),
    "pixtral_12b": ("Pixtral-12B", "#D97706", "P", "-."),
    "molmo_7b_o": ("Molmo-7B-O", "#B45309", "X", ":"),
}


def _pct2(pct: float, signed: bool = False) -> str:
    q = Decimal(f"{pct:.6f}").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if signed and q > 0:
        return f"+{q}%"
    if signed and q == 0:
        return "+0.00%"
    return f"{q}%"


def _pct1(pct: float, signed: bool = False) -> str:
    q = Decimal(f"{pct:.6f}").quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if signed and q > 0:
        return f"+{q}%"
    if signed and q == 0:
        return "+0.0%"
    return f"{q}%"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _index_oc(path: Path) -> dict[tuple[str, str], dict]:
    return {(str(r["pair_id"]), str(r["condition"])): r for r in _read_jsonl(path) if r.get("status") == "ok"}


def _resolve_asset(rel_or_abs: str, assets_root: Path) -> Path:
    s = rel_or_abs.replace("\\", "/")
    marker = "/experiments/cviu/"
    if marker in s:
        return assets_root / s.split(marker, 1)[1]
    p = Path(rel_or_abs)
    return p if p.is_file() else assets_root / rel_or_abs


def _save_both(fig: plt.Figure, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    pdf_p = FIG_DIR / f"{stem}.pdf"
    png_p = PREVIEW_DIR / f"{stem}.png"
    fig.savefig(pdf_p, format="pdf", bbox_inches="tight", pad_inches=0.04)
    fig.savefig(png_p, dpi=220, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"[ok] wrote {pdf_p.name} and {png_p.name}", flush=True)


def _crop_box(mask: np.ndarray, pad_frac: float = 1.6, aspect: float = 16.0 / 9.0) -> tuple[int, int, int, int]:
    H, W = mask.shape
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return 0, 0, W, H
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    bw, bh = max(x1 - x0, 140), max(y1 - y0, 140)
    box_w = max(bw * pad_frac, bh * pad_frac * aspect, 360.0)
    box_h = box_w / aspect
    if box_h > H:
        box_h = float(H)
        box_w = box_h * aspect
    if box_w > W:
        box_w = float(W)
        box_h = box_w / aspect
    cx0 = int(round(min(max(cx - box_w * 0.5, 0.0), W - box_w)))
    cy0 = int(round(min(max(cy - box_h * 0.5, 0.0), H - box_h)))
    return cx0, cy0, min(W, cx0 + int(round(box_w))), min(H, cy0 + int(round(box_h)))


def build_fig2_case_workflows(assets_root: Path, v1_runs_dir: Path, v3_runs_dir: Path, cf_cache_dir: Path) -> None:
    """WET-OP Fig 2 exact dark-slate 5-column visual progression workflow strips."""
    manifest = json.loads((V1_META_DIR / "manifest.json").read_text(encoding="utf-8"))["records"]
    m_by_oc = {(r["pair_id"], r["condition"]): r for r in manifest}
    cf_man_p = cf_cache_dir / "counterfactual_manifest.json"
    cf_imgs = {}
    if cf_man_p.is_file():
        cf_imgs = {(r["pair_id"], r["condition"]): Path(r["image"]["path"]) for r in json.loads(cf_man_p.read_text(encoding="utf-8"))["records"]}

    p8 = _index_oc(v1_runs_dir / "8b/formal_repeat0/predictions.jsonl")
    cf8 = _index_oc(v3_runs_dir / "counterfactual_qwen3_vl_8b/predictions.jsonl")
    piv = _index_oc(v3_runs_dir / "formal_internvl3_5_8b/predictions.jsonl")
    cfiv_p = v3_runs_dir / "counterfactual_internvl3_5_8b/predictions.jsonl"
    cfiv = _index_oc(cfiv_p) if cfiv_p.is_file() else {}

    # 3 diverse rows matching WET-OP Fig 2 rows (a), (b), (c)
    rows_spec = [
        {
            "row_lbl": "(a) Reflective Glare Gain",
            "badge_col": "#2563EB",
            "pid": "MWAX5JYKTKJZ2AABAAAAAAA8_usd:49332fc22c9d2612:v0",
            "model_main": p8,
            "model_cf": cf8,
            "model_tag": "Qwen3-VL-8B",
            "foot": [
                ("1. Original (MDL)", "Glare obscures panel", "Specular highlight"),
                ("2. CIE Lab Match", "Color/lum matched", "Non-photometric test"),
                ("3. Background CF", "Context swapped", "Target unchanged"),
                ("4. Target CF", "Glare suppressed", "Decision flips → Hit"),
                ("5. Preview (Full)", "Holistic match", "Consistent Hit"),
            ],
        },
        {
            "row_lbl": "(b) Holistic Refraction Loss",
            "badge_col": "#D97706",
            "pid": "MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v1",
            "model_main": p8,
            "model_cf": cf8,
            "model_tag": "Qwen3-VL-8B",
            "foot": [
                ("1. Original (MDL)", "Glass door Hit", "Multi-lobe reflections"),
                ("2. CIE Lab Match", "Holds Hit", "Photometric invariant"),
                ("3. Background CF", "Holds Hit", "Context compatible"),
                ("4. Target CF", "Holds Hit", "Local glass intact"),
                ("5. Preview (Full)", "Holistic loss → Miss", "2×2 interaction fail"),
            ],
        },
        {
            "row_lbl": "(c) Cross-Family Clock Shift",
            "badge_col": "#0D9488",
            "pid": "MWF4WLIKTIFZIAABAAAAAEA8_usd:26b4dbaac85d35d5:v2",
            "model_main": piv,
            "model_cf": cfiv,
            "model_tag": "InternVL3.5-8B",
            "foot": [
                ("1. Original (MDL)", "Clock face Hit", "Emissive dial cue"),
                ("2. CIE Lab Match", "Holds Hit", "Photometric invariant"),
                ("3. Background CF", "Holds Hit", "Desk context swapped"),
                ("4. Target CF", "Face flattened → Miss", "Target shader only"),
                ("5. Preview (Full)", "Drops off dial → Miss", "Silent regression"),
            ],
        },
    ]

    cond_order = ["original", "photometric_matched", "background_only", "target_only", "converted"]
    cond_short = ["Original", "CIE Match", "Bg Swap", "Target CF", "Converted"]

    fig = plt.figure(figsize=(10.5, 5.45))
    gs = fig.add_gridspec(3, 5, hspace=0.45, wspace=0.07, left=0.04, right=0.995, top=0.96, bottom=0.07)

    for r_i, spec in enumerate(rows_spec):
        pid = spec["pid"]
        mask_p = _resolve_asset(m_by_oc[(pid, "original")]["mask"]["path"], assets_root)
        mask_o = np.load(mask_p, allow_pickle=False).astype(bool)
        mask_c_p = _resolve_asset(m_by_oc[(pid, "converted")]["mask"]["path"], assets_root)
        mask_c = np.load(mask_c_p, allow_pickle=False).astype(bool)
        crop = _crop_box(mask_o, pad_frac=1.75, aspect=1.55)
        x0, y0, x1, y1 = crop

        for c_i, (cond, c_lbl) in enumerate(zip(cond_order, cond_short)):
            ax = fig.add_subplot(gs[r_i, c_i])
            if cond in ("original", "converted"):
                img_p = _resolve_asset(m_by_oc[(pid, cond)]["image"]["path"], assets_root)
                pred_row = spec["model_main"].get((pid, cond))
            else:
                img_p = cf_imgs.get((pid, cond), _resolve_asset(m_by_oc[(pid, "original")]["image"]["path"], assets_root))
                pred_row = spec["model_cf"].get((pid, cond))

            im = np.asarray(Image.open(img_p).convert("RGB"))
            msk = mask_c if cond in ("target_only", "converted") else mask_o
            im_c = im[y0:y1, x0:x1]
            m_c = msk[y0:y1, x0:x1]
            ax.imshow(im_c)
            if m_c.any():
                ax.contour(m_c.astype(float), levels=[0.5], colors=["#0F172A"], linewidths=1.35, alpha=0.45, zorder=3)
                ax.contour(m_c.astype(float), levels=[0.5], colors=["#FFFFFF"], linewidths=0.85, linestyles="--", alpha=0.88, zorder=4)

            hit_str = ""
            badge_bg = spec["badge_col"]
            if pred_row and pred_row.get("point_normalized") is not None:
                ptn = pred_row["point_normalized"]
                px = min(max(float(ptn[0]) * 1024.0 / 1000.0 - x0, 8.0), (x1 - x0) - 8.0)
                py = min(max(float(ptn[1]) * 768.0 / 1000.0 - y0, 8.0), (y1 - y0) - 8.0)
                is_hit = bool(pred_row["hit"])
                ax.scatter([px], [py], s=78, marker="o" if is_hit else "X", color="#10B981" if is_hit else "#E11D48", edgecolors="white", linewidths=1.2, zorder=6)
                hit_str = "Hit" if is_hit else "Miss"
                badge_bg = "#0D9488" if is_hit else "#E11D48"

            # Top-left circle step number + pill status (WET-OP Fig 2 signature)
            ax.text(0.05, 0.92, f"{c_i + 1}", transform=ax.transAxes, color="white", fontsize=7.0, fontweight="bold", ha="center", va="top",
                    bbox=dict(boxstyle="circle,pad=0.20", facecolor=spec["badge_col"], edgecolor="white", lw=0.8), zorder=8)
            pill = f"{c_lbl}" + (f": {hit_str}" if hit_str else "")
            ax.text(0.15, 0.92, pill, transform=ax.transAxes, color="#0F172A" if not hit_str else "white", fontsize=6.6, fontweight="bold", ha="left", va="top",
                    bbox=dict(boxstyle="round,pad=0.18", facecolor="white" if not hit_str else badge_bg, edgecolor="none", alpha=0.92), zorder=8)

            # Dark-slate bottom strip inside dark bar below frame (clip_on=False!)
            f_title, f_cue, _ = spec["foot"][c_i]
            ax.text(0.5, -0.04, f"{f_title}\n{f_cue}", transform=ax.transAxes, ha="center", va="top", fontsize=6.3, color="#0F172A",
                    linespacing=1.18,
                    bbox=dict(boxstyle="square,pad=0.22", facecolor="#F1F5F9", edgecolor="#CBD5E1", lw=0.6))
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_edgecolor("#CBD5E1")
                sp.set_linewidth(0.8)

            if c_i == 0:
                ax.text(-0.08, 0.5, spec["row_lbl"], transform=ax.transAxes, rotation=90, va="center", ha="right",
                        fontsize=7.6, fontweight="bold", color="#0F172A")

    _save_both(fig, "fig2_case_workflows")


def build_fig3_pipeline(assets_root: Path | None = None, v1_runs_dir: Path | None = None) -> None:
    """Delegate Figure 3 generation to the CVPR borderless OOXML PPTX -> COM PDF builder."""
    import build_fig3_cvpr_pptx

    argv_orig = sys.argv[:]
    try:
        cmd = [str(Path(build_fig3_cvpr_pptx.__file__).resolve())]
        if assets_root is not None:
            cmd += ["--assets-root", str(assets_root)]
        if v1_runs_dir is not None:
            cmd += ["--v1-runs-dir", str(v1_runs_dir)]
        sys.argv = cmd
        build_fig3_cvpr_pptx.main()
    finally:
        sys.argv = argv_orig


def build_fig4_variance_and_polar(v1_runs_dir: Path, v3_runs_dir: Path) -> None:
    """3-panel Figure 4: (a) 4-Level Variance Floor, (b) 4-Family Scaling/Turnover, (c) WET-OP Polar Profile."""
    vd = json.loads((V3_RAW_DIR / "variance_decomposition.json").read_text(encoding="utf-8"))
    sf = json.loads((V3_RAW_DIR / "scaling_and_families.json").read_text(encoding="utf-8"))
    feats = json.loads((V3_RAW_DIR / "pair_optical_features.json").read_text(encoding="utf-8"))["records"]
    feat_by_pid = {r["pair_id"]: r for r in feats}

    fig = plt.figure(figsize=(10.5, 3.80))
    ax1 = fig.add_axes([0.135, 0.17, 0.24, 0.70])
    ax2 = fig.add_axes([0.435, 0.17, 0.25, 0.70])
    ax3 = fig.add_axes([0.740, 0.18, 0.22, 0.62], polar=True)

    # Panel (a): Paired L3 Ray-Tracing Floor vs L4 Shader Conversion across all 6 checkpoints (+ L1/L2 baselines)
    l3_map = vd.get("level3_raytracing_rerender", {})
    l4_map = vd.get("level4_material_conversion_on_control_pairs", {})
    ckpt_rows = [
        ("Qwen3-VL-2B",  "qwen3_vl_2b",           "qwen3_vl_2b"),
        ("LLaVA-Mistral","llava_next_mistral_7b", "llava_next_mistral_7b"),
        ("InternVL3.5",  "internvl3_5_8b",        "internvl3_5_8b"),
        ("Qwen3-VL-8B",  "8b",                    "8b"),
        ("Molmo2-8B",    "molmo2_8b",             "molmo2_8b"),
        ("Qwen3-VL-32B", "32b",                   "32b"),
    ]
    ckpt_rows = [(lbl, k3, k4) for lbl, k3, k4 in ckpt_rows if k3 in l3_map and k4 in l4_map]
    y_c = np.arange(len(ckpt_rows))
    h_b = 0.34
    v_l3 = [l3_map[k3]["hit_flip_rate"] * 100.0 for _, k3, _ in ckpt_rows]
    v_l4 = [l4_map[k4]["flip_rate"] * 100.0 for _, _, k4 in ckpt_rows]
    ax1.barh(y_c - h_b * 0.52, v_l3, height=h_b, color="#3B82F6", alpha=0.88, label="L3: Re-Render Floor")
    ax1.barh(y_c + h_b * 0.52, v_l4, height=h_b, color="#E11D48", alpha=0.90, label="L4: Shader Conversion")

    l2 = vd.get("level2_stochastic_decoding_8b_t02", {})
    y_extra = len(ckpt_rows) + 0.15
    ax1.axvline(0.0, color="#0F172A", lw=0.8)
    if l2:
        pw_v = l2["pairwise_hit_disagreement_rate"] * 100.0
        any_v = l2["inputs_with_any_flip_rate"] * 100.0
        ax1.barh([y_extra], [pw_v], height=0.45, color="#7C3AED", alpha=0.88, label="L2: T=0.2 (8B pw/any)")
        ax1.barh([y_extra], [any_v], height=0.45, color="none", edgecolor="#7C3AED", ls="--", lw=1.15)
        ax1.text(any_v + 0.4, y_extra, f"{_pct1(pw_v)}/{_pct1(any_v)}", va="center", fontsize=6.0, color="#5B21B6", fontweight="bold")

    max_xa = max(v_l3 + v_l4 + ([l2["inputs_with_any_flip_rate"] * 100.0] if l2 else [16.7]))
    for idx, (v3, v4) in enumerate(zip(v_l3, v_l4)):
        ax1.text(v3 + 0.4, idx - h_b * 0.52, f"{_pct2(v3)}", va="center", fontsize=5.8, color="#1D4ED8")
        ax1.text(v4 + 0.4, idx + h_b * 0.52, f"{_pct2(v4)}", va="center", fontsize=6.0, fontweight="bold", color="#9F1239")

    all_y = list(y_c) + ([y_extra] if l2 else [])
    all_lbls = [f"{lbl}\n(L1=0.0%)" for lbl, _, _ in ckpt_rows] + (["L2: T=0.2\n(8B 5-draw)"] if l2 else [])
    ax1.set_yticks(all_y)
    ax1.set_yticklabels(all_lbls, fontsize=6.2)
    ax1.set_xlim(0, max(25.0, max_xa + 6.5))
    ax1.set_ylim(-0.6, (y_extra if l2 else len(ckpt_rows) - 1) + 0.6)
    ax1.set_xlabel("Control-Scene Flip Rate (%)", fontsize=7.8)
    ax1.set_title("(a) L1–L4 Variance Hierarchy", fontweight="bold", fontsize=8.3)
    ax1.legend(loc="center right", bbox_to_anchor=(0.99, 0.72), frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=5.6, borderpad=0.22)
    ax1.grid(axis="x", ls=":", lw=0.5, color="#CBD5E1")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Panel (b): Scaling & Cross-Family Turnover on All 480 Pairs
    pref_order = [
        "qwen3_vl_2b",
        "llava_next_mistral_7b",
        "pixtral_12b",
        "molmo_7b_o",
        "molmo2_8b",
        "internvl3_5_8b",
        "qwen3_vl_8b_r0",
        "qwen3_vl_32b_r0",
    ]
    m_keys = [k for k in pref_order if k in sf["models"]] + [k for k in sorted(sf["models"]) if k not in pref_order]
    losses = np.array([sf["models"][k]["metrics"]["loss_rate"]["estimate"] * 100.0 for k in m_keys])
    gains = np.array([sf["models"][k]["metrics"]["gain_rate"]["estimate"] * 100.0 for k in m_keys])
    flips = np.array([sf["models"][k]["metrics"]["flip_rate"]["estimate"] * 100.0 for k in m_keys])
    ci_lo = np.array([sf["models"][k]["metrics"]["flip_rate"]["scene_bootstrap_ci95"][0] * 100.0 for k in m_keys])
    ci_hi = np.array([sf["models"][k]["metrics"]["flip_rate"]["scene_bootstrap_ci95"][1] * 100.0 for k in m_keys])
    dhits = [sf["models"][k]["metrics"]["hit_rate_difference"]["estimate"] * 100.0 for k in m_keys]

    x_b = np.arange(len(m_keys))
    ax2.bar(x_b, losses, width=0.52, color="#E11D48", label="Loss (O→C miss)")
    ax2.bar(x_b, gains, bottom=losses, width=0.52, color="#0D9488", label="Gain (O→C hit)")
    ax2.errorbar(x_b, flips, yerr=[flips - ci_lo, ci_hi - flips], fmt="none", ecolor="#0F172A", capsize=3.0, lw=1.1, zorder=4)
    for i, (fl, hi, dh) in enumerate(zip(flips, ci_hi, dhits)):
        ax2.text(i, hi + 0.4, f"{_pct1(fl)}\n({dh:+.1f})", ha="center", va="bottom", fontsize=6.2, fontweight="bold", color="#0F172A")
    ax2.set_xticks(x_b)
    x_lbls = [
        PALETTE.get(k, (k,))[0]
        .replace("LLaVA-NeXT-Mistral-7B", "LLaVA-7B")
        .replace("Qwen3-VL-", "Q3-")
        .replace("InternVL3.5-", "IV3.5-")
        .replace("Molmo2-", "M2-")
        for k in m_keys
    ]
    ax2.set_xticklabels(x_lbls, fontsize=6.3)
    ax2.set_ylim(0, max(30.0, float(ci_hi.max()) + 4.8))
    ax2.set_ylabel("Paired Flip Rate (%)", fontsize=7.8)
    ax2.set_title("(b) 30-Scene Scaling & Families (480 Pairs)", fontweight="bold", fontsize=8.3)
    ax2.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=6.4, borderpad=0.25)
    ax2.grid(axis="y", ls=":", lw=0.5, color="#CBD5E1")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # Panel (c): WET-OP Fig 4 exact colored-sector Polar Profile of Converted Hit Rate (H_C %) across 10 axes
    polar_groups = [
        ("Regime", "#3730A3", "#C7D2FE", [("RM", lambda f: f["prior_optical_regime"] == "Reflective/Metallic"),
                                          ("TG", lambda f: f["prior_optical_regime"] == "Transparent/Glass"),
                                          ("MD", lambda f: f["prior_optical_regime"] == "Matte/Diffuse"),
                                          ("ES", lambda f: f["prior_optical_regime"] == "Emissive/Screen")]),
        ("Scale",  "#B45309", "#FDE68A", [("Large", lambda f: f["log_area_frac"] > -1.75),
                                          ("Small", lambda f: f["log_area_frac"] <= -1.75)]),
        ("Framing","#9F1239", "#FECDD3", [("Center", lambda f: f["center_dist_norm"] <= 0.35),
                                          ("Periph.", lambda f: f["center_dist_norm"] > 0.35)]),
        ("Distort","#155E75", "#A5F3FC", [("Low", lambda f: f["pixel_optical_regime"] == "Low-Distortion"),
                                          ("Degr.", lambda f: f["pixel_optical_regime"] != "Low-Distortion")]),
    ]
    spokes = [(g_name, txt_col, sec_col, tag, fn) for g_name, txt_col, sec_col, items in polar_groups for tag, fn in items]
    N_sp = len(spokes)
    rmax = 104.0
    ax3.set_facecolor("#FFFFFF")
    ax3.set_theta_offset(np.pi / 2.0)
    ax3.set_theta_direction(-1)
    ax3.set_ylim(0, rmax)
    ax3.set_yticks([0, 40, 70, 100])
    ax3.set_yticklabels([])
    ax3.yaxis.grid(True, color="#CBD5E1", lw=0.55)
    ax3.xaxis.grid(True, color="#CBD5E1", lw=0.55)
    ax3.spines["polar"].set_color("#94A3B8")
    ax3.spines["polar"].set_linewidth(0.8)
    angles = np.linspace(0, 2 * np.pi, N_sp, endpoint=False).tolist()
    ax3.set_xticks(angles)
    ax3.set_xticklabels([])
    for rt, rtl in [(40, "40%"), (70, "70%"), (100, "100%")]:
        ax3.text(np.pi * 0.25, rt, rtl, ha="center", va="center", fontsize=5.8, color="#475569",
                 bbox=dict(boxstyle="round,pad=0.05", facecolor="white", edgecolor="none", alpha=0.82), zorder=7)

    step = 2 * np.pi / N_sp
    idx_s = 0
    for _, _, sec_col, items in polar_groups:
        k = len(items)
        th0, th1 = idx_s * step - step * 0.5, (idx_s + k - 1) * step + step * 0.5
        arc = np.linspace(th0, th1, 48)
        ax3.fill(np.concatenate([[th0], arc, [th0]]), np.concatenate([[0.0], np.full_like(arc, rmax), [0.0]]), color=sec_col, alpha=0.28, lw=0, zorder=0)
        ax3.plot([th0, th0], [0, rmax], color="white", lw=1.0, zorder=1)
        idx_s += k

    # Plot representative 4 independent families on polar axes
    polar_models = []
    for k in ("qwen3_vl_8b_r0", "internvl3_5_8b", "molmo2_8b", "llava_next_mistral_7b", "molmo_7b_o", "pixtral_12b", "qwen3_vl_32b_r0"):
        if k in sf["models"]:
            p = (v1_runs_dir / ("32b" if "32b" in k else "8b") / "formal_repeat0/predictions.jsonl") if k.endswith("_r0") else (v3_runs_dir / f"formal_{k}/predictions.jsonl")
            if p.is_file():
                polar_models.append((k, _index_oc(p)))
    for k, idx_m in polar_models[:4]:
        disp, col, mk, ls = PALETTE.get(k, (k, "#334155", "o", "-"))
        vals_p = []
        for _, _, _, _, fn in spokes:
            pids = [f["pair_id"] for f in feats if fn(f)]
            hc_m = np.mean([int(bool(idx_m[(pid, "converted")]["hit"])) for pid in pids if (pid, "converted") in idx_m]) * 100.0
            vals_p.append(hc_m)
        ax3.plot(angles + [angles[0]], vals_p + [vals_p[0]], color=col, lw=1.25, ls=ls, marker=mk, ms=2.5, markeredgecolor="white", markeredgewidth=0.3, label=disp, zorder=5)
        ax3.fill(angles + [angles[0]], vals_p + [vals_p[0]], color=col, alpha=0.04, zorder=4)

    for ang, (g_name, txt_col, _, sub_lbl, _) in zip(angles, spokes):
        sx, sy = np.sin(ang), np.cos(ang)
        r_lbl = rmax * 1.11
        align_m = "center" if abs(sx) < 0.16 else ("left" if sx > 0 else "right")
        box_algn = (0.5, 0.0 if sy > 0 else 1.0) if abs(sx) < 0.16 else ((0.0, 0.5) if sx > 0 else (1.0, 0.5))
        t1 = TextArea(g_name, textprops=dict(color=txt_col, fontweight="bold", fontsize=6.4))
        t2 = TextArea(sub_lbl, textprops=dict(color="#334155", fontsize=6.0))
        vbox = VPacker(children=[t1, t2], align=align_m, pad=0, sep=0.4)
        ax3.add_artist(AnnotationBbox(vbox, (ang, r_lbl), xycoords="data", box_alignment=box_algn, frameon=False, pad=0.0, annotation_clip=False))

    fig.text(0.85, 0.965, "(c) Converted Hit Profile (%)", ha="center", va="top", fontsize=8.3, fontweight="bold", color="#0F172A")
    ax3.legend(loc="lower center", bbox_to_anchor=(0.5, -0.28), ncol=2, frameon=False, fontsize=6.2, handlelength=1.6, columnspacing=0.9)

    _save_both(fig, "fig4_variance_and_polar")


def build_fig5_causal_and_risk(v1_runs_dir: Path, v3_runs_dir: Path) -> None:
    """WET-OP exp_causal_ablations exact 3-panel vector figure: (a) 2-Family Counterfactuals, (b) Regime Trade-off, (c) Zero-VLM Risk Gate."""
    om = json.loads((V3_RAW_DIR / "optical_mechanisms.json").read_text(encoding="utf-8"))
    ra = json.loads((V3_RAW_DIR / "risk_auditor.json").read_text(encoding="utf-8"))
    feats = json.loads((V3_RAW_DIR / "pair_optical_features.json").read_text(encoding="utf-8"))["records"]
    p8 = _index_oc(v1_runs_dir / "8b/formal_repeat0/predictions.jsonl")
    p32 = _index_oc(v1_runs_dir / "32b/formal_repeat0/predictions.jsonl")
    extra_idxs = []
    for folder in sorted(v3_runs_dir.glob("formal_*")):
        comp = folder / "completion.json"
        pred = folder / "predictions.jsonl"
        if pred.is_file() and (not comp.is_file() or json.loads(comp.read_text(encoding="utf-8")).get("status") == "complete"):
            extra_idxs.append(_index_oc(pred))

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.15), gridspec_kw={"width_ratios": [1.05, 1.05, 1.12], "wspace": 0.30})

    # Panel (a): Dual-family counterfactual flip curves
    ax = axes[0]
    by_m = om.get("by_model", {"qwen3_vl_8b": om})
    conds = ["photo", "B", "T", "F"]
    x_c = np.arange(len(conds))
    m_styles = [("qwen3_vl_8b", "Qwen3-VL-8B", "#2563EB", "o", "-"), ("internvl3_5_8b", "InternVL3.5-8B", "#E11D48", "^", "-.")]
    max_y = 14.0
    for mk, lbl, col, mkr, ls in m_styles:
        if mk not in by_m:
            continue
        rep = by_m[mk]["all_480_pairs"]
        ys = [rep["flips_vs_original"][c]["estimate"] * 100.0 for c in conds]
        lo = [rep["flips_vs_original"][c]["scene_bootstrap_ci95"][0] * 100.0 for c in conds]
        hi = [rep["flips_vs_original"][c]["scene_bootstrap_ci95"][1] * 100.0 for c in conds]
        max_y = max(max_y, max(hi) + 3.0)
        ax.errorbar(x_c + (-0.06 if mk == "qwen3_vl_8b" else 0.06), ys, yerr=[np.array(ys) - lo, np.array(hi) - ys],
                    color=col, marker=mkr, markersize=4.5, lw=1.6, ls=ls, capsize=3, label=f"{lbl} (ΔBSDF={_pct2(rep['full_minus_photometric_flip_rate']['difference']*100, signed=True)})", zorder=4)
    ax.set_xticks(x_c)
    ax.set_xticklabels(["CIE Lab\n($I^{\\mathrm{photo}}$)", "Bg-Only\n($I^B$)", "Target\n($I^T$)", "Full\n($I^F$)"], fontsize=7.3)
    ax.set_ylim(0, max_y + 1.5)
    ax.set_ylabel("Flip Rate vs. Original (%)", fontsize=8.0)
    ax.set_title("(a) Counterfactual BSDF Residual", fontweight="bold", fontsize=8.4, pad=5)
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=6.3, borderpad=0.25)
    ax.grid(True, ls=":", lw=0.5, color="#CBD5E1", alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel (b): Bidirectional Optical Trade-off Across Regimes
    ax = axes[1]
    strata_order = ["Reflective/Metallic", "Matte/Diffuse", "Transparent/Glass", "Emissive/Screen"]
    strata = om["stratified_by_prior_optical_regime_8b"]
    y_s = np.arange(len(strata_order))
    s_loss = np.array([strata[k]["loss_rate"]["estimate"] * 100.0 for k in strata_order])
    s_gain = np.array([strata[k]["gain_rate"]["estimate"] * 100.0 for k in strata_order])
    s_net = np.array([strata[k]["net_delta"]["estimate"] * 100.0 for k in strata_order])
    ax.barh(y_s, -s_loss, height=0.50, color="#E11D48", edgecolor="#9F1239", lw=0.5, label="Loss (%)")
    ax.barh(y_s, s_gain, height=0.50, color="#0D9488", edgecolor="#115E59", lw=0.5, label="Gain (%)")
    ax.axvline(0.0, color="#334155", lw=1.0)
    for i, (lo, ga, net) in enumerate(zip(s_loss, s_gain, s_net)):
        ax.text(-lo - 0.3, i, f"-{_pct2(lo)}", ha="right", va="center", fontsize=6.6, color="#9F1239", fontweight="bold")
        ax.text(ga + 0.3, i, f"+{_pct2(ga)} ({net:+.2f}%)", ha="left", va="center", fontsize=6.6, color="#115E59", fontweight="bold")
    ax.set_yticks(y_s)
    ax.set_yticklabels(["Reflective\n(n=158)", "Matte\n(n=88)", "Glass\n(n=176)", "Emissive\n(n=58)"], fontsize=7.0)
    ax.set_xlim(-8.8, 15.8)
    ax.set_ylim(-0.55, 3.85)
    ax.set_xlabel("Outcome Share (%  [←Loss | Gain→])", fontsize=8.0)
    ax.set_title("(b) Optical Regime Trade-Off (8B)", fontweight="bold", fontsize=8.4, pad=5)
    ax.legend(loc="upper right", ncol=2, frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=6.3, borderpad=0.22)
    ax.grid(axis="x", ls=":", lw=0.5, color="#CBD5E1", alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel (c): Dense empirical step-wise Selective QA Retention Curves (matching WET-OP green target zone!)
    ax = axes[2]
    ax.axvspan(15, 25, color="#BBF7D0", alpha=0.55, zorder=1)
    ax.axvline(20.0, color="#15803D", lw=0.85, ls="--", zorder=2)
    ax.plot([0, 100], [0, 100], color="#94A3B8", lw=0.9, ls=":", label="Random (20.0%)", zorder=2)

    def _retention_curve(y_true: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        order = np.argsort(-scores, kind="mergesort")
        y_sorted = y_true[order]
        tot = max(int(y_sorted.sum()), 1)
        xs = np.concatenate([[0.0], np.arange(1, len(y_sorted) + 1) / len(y_sorted) * 100.0])
        ys = np.concatenate([[0.0], np.cumsum(y_sorted) / tot * 100.0])
        return xs, ys

    all_idxs = [p8, p32] + extra_idxs
    y_8b32b = np.array([int(
        (bool(p8[(f["pair_id"], "original")]["hit"]) and not bool(p8[(f["pair_id"], "converted")]["hit"]))
        or (bool(p32[(f["pair_id"], "original")]["hit"]) and not bool(p32[(f["pair_id"], "converted")]["hit"]))
    ) for f in feats], dtype=np.int64)
    y_anyfam = np.array([int(any(
        (f["pair_id"], "original") in ix and (f["pair_id"], "converted") in ix
        and bool(ix[(f["pair_id"], "original")]["hit"]) and not bool(ix[(f["pair_id"], "converted")]["hit"])
        for ix in all_idxs
    )) for f in feats], dtype=np.int64)

    splits = np.array([f["split"] for f in feats])
    scenes = np.array([f["scene_id"] for f in feats])
    tr_m = splits == "train"
    te_m = splits == "test"

    X_dep = np.array([[float(f[c]) for c in DEPLOY_AUTO_FEATURES] for f in feats], dtype=np.float64)
    c_dep = float(ra["targets"]["any_8b_32b_loss"]["deploy_auto"]["selected_c"])
    fit_dep = fit_standardized_l2_logreg(X_dep[tr_m], y_8b32b[tr_m], c_reg=c_dep)
    s_dep_te = predict_proba_logreg(fit_dep, X_dep[te_m])
    xs_d, ys_d = _retention_curve(y_8b32b[te_m], s_dep_te)
    r20_d = ra["targets"]["any_8b_32b_loss"]["deploy_auto"]["test_10_scenes"]["top_20pct_recall"] * 100.0
    ax.plot(xs_d, ys_d, color="#2563EB", lw=1.65, ls="-", label=f"8B/32B Gate (Test): {r20_d:.1f}%", zorder=4)

    geom_cols = ("log_area_frac", "aspect_ratio", "center_dist_norm", "border_touch", "mask_iou")
    X_geo = np.array([[float(f[c]) for c in geom_cols] for f in feats], dtype=np.float64)
    c_geo = float(ra["targets"]["any_8b_32b_loss"]["geometry_only"]["selected_c"])
    s_geo_loso = np.zeros(len(feats), dtype=np.float64)
    for sc in sorted(set(scenes)):
        f_fit = fit_standardized_l2_logreg(X_geo[scenes != sc], y_8b32b[scenes != sc], c_reg=c_geo)
        s_geo_loso[scenes == sc] = predict_proba_logreg(f_fit, X_geo[scenes == sc])
    xs_g, ys_g = _retention_curve(y_8b32b, s_geo_loso)
    r20_g = ra["targets"]["any_8b_32b_loss"]["geometry_only"]["loso_30_scenes"]["top_20pct_recall"] * 100.0
    ax.plot(xs_g, ys_g, color="#0D9488", lw=1.65, ls="-.", label=f"Geom. Gate (LOSO): {r20_g:.1f}%", zorder=4)

    if "any_family_loss" in ra["targets"]:
        c_af = float(ra["targets"]["any_family_loss"]["deploy_auto"]["selected_c"])
        fit_af = fit_standardized_l2_logreg(X_dep[tr_m], y_anyfam[tr_m], c_reg=c_af)
        s_af_te = predict_proba_logreg(fit_af, X_dep[te_m])
        xs_af, ys_af = _retention_curve(y_anyfam[te_m], s_af_te)
        r20_af = ra["targets"]["any_family_loss"]["deploy_auto"]["test_10_scenes"]["top_20pct_recall"] * 100.0
        ax.plot(xs_af, ys_af, color="#7C3AED", lw=1.55, ls="--", label=f"All-Family Gate: {r20_af:.1f}%", zorder=5)

    s_mae_te = np.array([float(f["global_rgb_mae"]) for f in feats])[te_m]
    xs_m, ys_m = _retention_curve(y_8b32b[te_m], s_mae_te)
    r20_m = ra["targets"]["any_8b_32b_loss"]["baseline_global_rgb_mae"]["test_10_scenes"]["top_20pct_recall"] * 100.0
    ax.plot(xs_m, ys_m, color="#E11D48", lw=1.5, ls=":", label=f"Global RGB MAE: {r20_m:.1f}%", zorder=3)

    ax.text(21.5, 7.0, "Target:\n20% QA", fontsize=6.4, color="#14532D", fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 104)
    ax.set_xlabel("Inspection Budget (%)", fontsize=8.0)
    ax.set_ylabel("Regressions Caught (%)", fontsize=8.0)
    ax.set_title("(c) Zero-VLM Risk Gate Retention", fontweight="bold", fontsize=8.4, pad=5)
    ax.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=5.8, borderpad=0.22)
    ax.grid(True, ls=":", lw=0.5, color="#CBD5E1", alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.subplots_adjust(left=0.06, right=0.99, bottom=0.17, top=0.88)
    _save_both(fig, "fig5_causal_and_risk")


def build_fig6_navigation_vln() -> None:
    """WET-OP-styled KuJiaLe 99-episode closed-loop navigation case-study figure."""
    p99 = json.loads(NAV_99_SUMMARY.read_text(encoding="utf-8"))
    psc = json.loads(NAV_99_SCENES.read_text(encoding="utf-8"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 2.85), gridspec_kw={"width_ratios": [1.05, 1.25], "wspace": 0.28})

    # Panel (a): 99 Paired Outcomes Transition Breakdown
    cats = ["Both\nSuccess", "Both\nFail", "Regression\n(O=1, C=0)", "Gain\n(O=0, C=1)"]
    counts = [35, 34, 17, 13]
    cols = ["#2563EB", "#94A3B8", "#E11D48", "#0D9488"]
    x_a = np.arange(len(cats))
    bars = ax1.bar(x_a, counts, width=0.55, color=cols, edgecolor="white", lw=0.8)
    for b, cnt in zip(bars, counts):
        ax1.text(b.get_x() + b.get_width() * 0.5, cnt + 1.0, f"{cnt}\n({cnt/99*100:.1f}%)", ha="center", va="bottom", fontsize=7.0, fontweight="bold", color="#0F172A")
    ax1.set_xticks(x_a)
    ax1.set_xticklabels(cats, fontsize=7.2)
    ax1.set_ylim(0, 44)
    ax1.set_ylabel("Episode Count (Total = 99)", fontsize=8.0)
    ax1.set_title("(a) Closed-Loop Episode Turnover (30/99 = 30.3%)", fontweight="bold", fontsize=8.4)
    ax1.grid(axis="y", ls=":", lw=0.5, color="#CBD5E1")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Panel (b): Per-Scene & Aggregate SR_O vs SR_C + SPL_O vs SPL_C (WET-OP Bar Style)
    scenes_lbl = ["Scene 0031\n(n=33, 8 flips)", "Scene 0036\n(n=33, 11 flips)", "Scene 0066\n(n=33, 11 flips)", "Overall All\n(n=99, 30 flips)"]
    sr_o = [51.5, 81.8, 24.2, 52.5]
    sr_c = [57.6, 60.6, 27.3, 48.5]
    spl_o = [47.9, 70.0, 24.2, 47.4]
    spl_c = [49.6, 55.0, 24.3, 43.0]
    xg = np.arange(len(scenes_lbl))
    w = 0.20
    ax2.bar(xg - 1.5 * w, sr_o, width=w, color="#2563EB", label="SR Orig (MDL)")
    ax2.bar(xg - 0.5 * w, sr_c, width=w, color="#E11D48", label="SR Conv (Preview)")
    ax2.bar(xg + 0.5 * w, spl_o, width=w, color="#93C5FD", hatch="///", edgecolor="#2563EB", lw=0.5, label="SPL Orig")
    ax2.bar(xg + 1.5 * w, spl_c, width=w, color="#FECDD3", hatch="///", edgecolor="#E11D48", lw=0.5, label="SPL Conv")
    for idx in range(len(xg)):
        d_sr = sr_c[idx] - sr_o[idx]
        ax2.text(idx, max(sr_o[idx], sr_c[idx]) + 3.0, f"ΔSR {d_sr:+.1f} pp", ha="center", va="bottom",
                 fontsize=6.8, fontweight="bold", color="#E11D48" if d_sr < 0 else "#0D9488")
    ax2.set_xticks(xg)
    ax2.set_xticklabels(scenes_lbl, fontsize=7.0)
    ax2.set_ylim(0, 98)
    ax2.set_ylabel("Navigation Rate (%)", fontsize=8.0)
    ax2.set_title("(b) KuJiaLe DualVLN Scene Breakdown (SR & SPL)", fontweight="bold", fontsize=8.4)
    ax2.legend(loc="upper right", ncol=2, frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=6.4, borderpad=0.22)
    ax2.grid(axis="y", ls=":", lw=0.5, color="#CBD5E1")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.subplots_adjust(left=0.06, right=0.99, bottom=0.20, top=0.87)
    _save_both(fig, "fig6_navigation_vln")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-root", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\assets\cviu"))
    parser.add_argument("--v1-runs-dir", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\assets\cviu\formal_model_runs_v1"))
    parser.add_argument("--v3-runs-dir", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\runs"))
    parser.add_argument("--cf-cache-dir", type=Path, default=Path(r"I:\cpfs\.cviu_v3_work\cf_cache"))
    args = parser.parse_args()

    build_fig2_case_workflows(args.assets_root, args.v1_runs_dir, args.v3_runs_dir, args.cf_cache_dir)
    build_fig3_pipeline(args.assets_root, args.v1_runs_dir)
    build_fig4_variance_and_polar(args.v1_runs_dir, args.v3_runs_dir)
    build_fig5_causal_and_risk(args.v1_runs_dir, args.v3_runs_dir)
    build_fig6_navigation_vln()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
