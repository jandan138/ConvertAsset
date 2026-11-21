#!/usr/bin/env python3
"""Generate the 4 publication-grade CVIU v3 PDF figures and 200-DPI PNG previews."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
from PIL import Image

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[4]
sys.path.insert(0, str(THIS_DIR))

from optical_and_risk_features import DEPLOY_AUTO_FEATURES  # noqa: E402
from v3_common import fit_standardized_l2_logreg, predict_proba_logreg  # noqa: E402


V3_RAW_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_v3"
V1_META_DIR = REPO_ROOT / "paper/shared/evidence/raw/cviu_formal/v1"
V1_RUNS_DIR = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\v1_runs\formal_model_runs_v1"
)
V3_RUNS_DIR = Path(r"J:\我的云端硬盘\UltraSync\ConvertAsset\remote_runs\cviu_v3_20261116\runs")
HERO_CACHE_DIR = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\hero_assets"
)
FIG_DIR = REPO_ROOT / "paper/venues/cviu/figures"
PREVIEW_DIR = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\59ea6f86-d5f8-405c-9b08-ab0a69eb188a\scratch\fig_previews"
)


def _pct2(pct: float, signed: bool = False) -> str:
    """Format a percentage (already *100) using half-up 2-decimal rounding."""
    q = Decimal(f"{pct:.6f}").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if signed and q > 0:
        return f"+{q}%"
    if signed and q == 0:
        return "+0.00%"
    return f"{q}%"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9.0,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def _save_both(fig: plt.Figure, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.06)
    fig.savefig(PREVIEW_DIR / f"{stem}.png", dpi=200, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print(f"[ok] wrote {stem}.pdf and preview .png", flush=True)


def _load_idx(jsonl_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (r["pair_id"], r["condition"]): r
        for r in (json.loads(l) for l in jsonl_path.read_text(encoding="utf-8").splitlines() if l.strip())
    }


def _resolve_hero_member(raw_path: str) -> Path:
    prefix = "/cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/"
    rel = raw_path.replace("\\", "/")
    if rel.startswith(prefix):
        rel = rel[len(prefix) :]
    return HERO_CACHE_DIR / rel


def _crop_bounds(mask: np.ndarray, pad_frac: float = 1.6, min_w: int = 380) -> tuple[int, int, int, int]:
    h, w = mask.shape
    ys, xs = np.where(mask)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    bw, bh = max(x1 - x0, 40), max(y1 - y0, 40)
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    half_w = max(min_w / 2.0, bw * (0.5 + pad_frac))
    half_h = half_w * (3.0 / 4.0)
    if half_w * 2 > w:
        half_w = w / 2.0
        half_h = h / 2.0
    if half_h * 2 > h:
        half_h = h / 2.0
        half_w = half_h * (4.0 / 3.0)
    lx0 = int(max(0, min(w - 2 * half_w, cx - half_w)))
    ly0 = int(max(0, min(h - 2 * half_h, cy - half_h)))
    lx1 = int(min(w, lx0 + 2 * half_w))
    ly1 = int(min(h, ly0 + 2 * half_h))
    return lx0, ly0, lx1, ly1


def build_hero_figure() -> None:
    manifest = json.loads((V1_META_DIR / "manifest.json").read_text(encoding="utf-8"))["records"]
    m_by_oc = {(r["pair_id"], r["condition"]): r for r in manifest}
    p8 = _load_idx(V1_RUNS_DIR / "8b/formal_repeat0/predictions.jsonl")
    piv = _load_idx(V3_RUNS_DIR / "formal_internvl3_5_8b/predictions.jsonl")

    loss_priority = [
        "MV5M25QKTKJZ2AABAAAAAAY8_usd:2811da39a8d6280c:v0",
        "MWBGLKQKTKJZ2AABAAAAABI8_usd:4217587705500ad5:v0",
        "MVUHLWYKTKJ5EAABAAAAAAI8_usd:8f5736c4d6534ecd:v1",
        "MWBGLKQKTKJZ2AABAAAAABI8_usd:6c92c334d17a6dc5:v0",
    ]
    gain_priority = [
        "MWAX5JYKTKJZ2AABAAAAAAA8_usd:49332fc22c9d2612:v0",
        "MVUCSQAKTKJ5EAABAAAAAAY8_usd:073b824ac9c68c6c:v2",
        "MVUHLWYKTKJ5EAABAAAAAAY8_usd:c952e846e2258e1d:v0",
    ]

    def _pick(cands: list[str]) -> str:
        for pid in cands:
            ro, rc = m_by_oc.get((pid, "original")), m_by_oc.get((pid, "converted"))
            if not ro or not rc:
                continue
            if all(_resolve_hero_member(x).is_file() for x in (ro["image"]["path"], rc["image"]["path"], ro["mask"]["path"])):
                return pid
        raise FileNotFoundError(f"No cached hero pair found among {cands} under {HERO_CACHE_DIR}")

    loss_pid = _pick(loss_priority)
    gain_pid = _pick(gain_priority)
    print(f"[hero] using loss_pid={loss_pid}, gain_pid={gain_pid}", flush=True)

    fig = plt.figure(figsize=(13.6, 6.4))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.05, 1.05, 1.15], wspace=0.14, hspace=0.20)

    def _draw_panel(ax: plt.Axes, pid: str, cond: str, title: str, badge: str, badge_color: str, crop: tuple[int, int, int, int]) -> None:
        rec = m_by_oc[(pid, cond)]
        im = np.array(Image.open(_resolve_hero_member(rec["image"]["path"])).convert("RGB"))
        mask = np.load(_resolve_hero_member(rec["mask"]["path"]), allow_pickle=False)
        x0, y0, x1, y1 = crop
        im_c = im[y0:y1, x0:x1]
        m_c = mask[y0:y1, x0:x1]
        ax.imshow(im_c)
        ax.contour(m_c.astype(float), levels=[0.5], colors=["#00E5FF"], linewidths=1.8)

        for model_name, pred_map, mk_hit, mk_miss, c_hit, c_miss, dx_lbl in (
            ("Qwen3-VL-8B", p8, "o", "X", "#00C853", "#FF1744", 8),
            ("InternVL3.5-8B", piv, "s", "^", "#2979FF", "#FF9100", 8),
        ):
            row = pred_map[(pid, cond)]
            pt = row.get("point_normalized")
            if pt is not None:
                px = float(pt[0]) * 1024.0 / 1000.0 - x0
                py = float(pt[1]) * 768.0 / 1000.0 - y0
                ch, cw = im_c.shape[:2]
                px = min(max(px, 10), cw - 10)
                py = min(max(py, 10), ch - 10)
                hit = bool(row["hit"])
                ax.scatter(
                    [px],
                    [py],
                    s=105 if hit else 115,
                    marker=mk_hit if hit else mk_miss,
                    color=c_hit if hit else c_miss,
                    edgecolors="white",
                    linewidths=1.3,
                    zorder=6,
                )
        ax.set_title(title, pad=5, fontsize=9.5)
        ax.text(
            0.03,
            0.93,
            badge,
            transform=ax.transAxes,
            color="white",
            fontsize=8.2,
            fontweight="bold",
            va="top",
            bbox=dict(boxstyle="round,pad=0.25", facecolor=badge_color, edgecolor="none", alpha=0.9),
        )
        ax.set_xticks([])
        ax.set_yticks([])

    mask_loss = np.load(_resolve_hero_member(m_by_oc[(loss_pid, "original")]["mask"]["path"]), allow_pickle=False)
    crop_loss = _crop_bounds(mask_loss, pad_frac=1.45, min_w=420)
    mask_gain = np.load(_resolve_hero_member(m_by_oc[(gain_pid, "original")]["mask"]["path"]), allow_pickle=False)
    crop_gain = _crop_bounds(mask_gain, pad_frac=1.35, min_w=420)

    q_loss = m_by_oc[(loss_pid, "original")]["query"].replace("Point to ", 'Query: "').rstrip(".") + '"'
    q_gain = m_by_oc[(gain_pid, "original")]["query"].replace("Point to ", 'Query: "').rstrip(".") + '"'

    def _badge(pid: str, cond: str) -> tuple[str, str]:
        h_q = bool(p8[(pid, cond)]["hit"])
        h_i = bool(piv[(pid, cond)]["hit"])
        lbl = f"{'Original' if cond == 'original' else 'Converted'} | Q8:{'Hit' if h_q else 'Miss'} · IV3.5:{'Hit' if h_i else 'Miss'}"
        col = "#1B5E20" if (h_q and h_i) else ("#B71C1C" if not (h_q or h_i) else "#E65100")
        return lbl, col

    b_lo, c_lo = _badge(loss_pid, "original")
    b_lc, c_lc = _badge(loss_pid, "converted")
    b_go, c_go = _badge(gain_pid, "original")
    b_gc, c_gc = _badge(gain_pid, "converted")

    ax_lo = fig.add_subplot(gs[0, 0])
    ax_lc = fig.add_subplot(gs[1, 0])
    _draw_panel(ax_lo, loss_pid, "original", f"(a) Loss Example — Original (MDL)\n{q_loss}", b_lo, c_lo, crop_loss)
    _draw_panel(ax_lc, loss_pid, "converted", "(a') Converted (UsdPreviewSurface)", b_lc, c_lc, crop_loss)

    ax_go = fig.add_subplot(gs[0, 1])
    ax_gc = fig.add_subplot(gs[1, 1])
    _draw_panel(ax_go, gain_pid, "original", f"(b) Gain Example — Original (MDL)\n{q_gain}", b_go, c_go, crop_gain)
    _draw_panel(ax_gc, gain_pid, "converted", "(b') Converted (UsdPreviewSurface)", b_gc, c_gc, crop_gain)

    # Legend below image columns
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color="#00E5FF", lw=2, label="Target Mask Contour"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#00C853", markeredgecolor="w", markersize=8, label="Qwen3-VL-8B Hit"),
        Line2D([0], [0], marker="X", color="w", markerfacecolor="#FF1744", markeredgecolor="w", markersize=8, label="Qwen3-VL-8B Miss"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#2979FF", markeredgecolor="w", markersize=7.5, label="InternVL3.5-8B Hit"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#FF9100", markeredgecolor="w", markersize=8, label="InternVL3.5-8B Miss"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.35, -0.02), fontsize=8.3)

    # Right column: Closed-Loop Quantitative Research Framework
    ax_r = fig.add_subplot(gs[:, 2])
    ax_r.set_xlim(0, 1)
    ax_r.set_ylim(0, 1)
    ax_r.axis("off")
    ax_r.set_title("(c) CVIU v3 Closed-Loop Evidence Architecture\n(30 Scenes, 480 Pairs, 9,936 BF16 Predictions)", pad=5, fontsize=9.5)

    cards = [
        (
            0.69,
            "#E3F2FD",
            "#1565C0",
            "RQ1: Aggregate Invariance vs. Turnover",
            "• Qwen3-VL-2B: Net ΔHit = +0.00%, yet 14.17% flip\n"
            "• Scaling 2B → 8B → 32B: Flips 14.2% → 9.4% → 4.2%\n"
            "• InternVL3.5-8B (cross-family): 10.21% flip (43.3 px)\n"
            "• Exceeds 0.00% greedy & 1.0–3.1% render noise floor",
        ),
        (
            0.36,
            "#FFF3E0",
            "#E65100",
            "RQ2: Optical Counterfactuals (1,440 images)",
            "• CIE L*a*b* photometric control alone: 5.83% flips\n"
            "• Non-photometric BSDF residual: +3.54% [1.25, 5.83]\n"
            "• Trade-off: Reflective/Metallic +4.43% glare gain\n"
            "  vs. structural/contrast erosion driving Losses",
        ),
        (
            0.03,
            "#E8F5E9",
            "#2E7D32",
            "RQ3: Zero-VLM Pre-Deployment Risk Gate",
            "• Global RGB MAE baseline: 0.432 test AUROC (chance)\n"
            "• Geometry + paired delta gate: 0.743 test / 0.732 LOSO\n"
            "• Flags 20% high-risk assets → catches 52.0% Losses\n"
            "  (+ RQ4: 99-episode closed-loop VLN case study, 30.3%)",
        ),
    ]
    for y0_c, fc, ec, head, body in cards:
        patch = FancyBboxPatch((0.02, y0_c), 0.96, 0.27, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor=fc, edgecolor=ec, linewidth=1.6)
        ax_r.add_patch(patch)
        ax_r.text(0.055, y0_c + 0.225, head, fontsize=8.7, fontweight="bold", color=ec, va="top")
        ax_r.text(0.055, y0_c + 0.175, body, fontsize=8.0, color="#212121", va="top", linespacing=1.35)

    for ya in (0.685, 0.355):
        ax_r.annotate("", xy=(0.50, ya - 0.032), xytext=(0.50, ya + 0.005), arrowprops=dict(arrowstyle="-|>", lw=2.0, color="#455A64"))

    _save_both(fig, "cviu_v3_hero")


def build_variance_and_scaling_figure() -> None:
    vd = json.loads((V3_RAW_DIR / "variance_decomposition.json").read_text(encoding="utf-8"))
    sf = json.loads((V3_RAW_DIR / "scaling_and_families.json").read_text(encoding="utf-8"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 4.7), gridspec_kw={"width_ratios": [1.0, 1.18], "wspace": 0.26})

    # Panel (a): 4-level variance decomposition
    labels_a = [
        "L1: Greedy Repeat\n(2B/8B/32B, T=0)",
        "L3: Ray-Tracing Re-render\n(Qwen3-VL-32B)",
        "L3: Ray-Tracing Re-render\n(Qwen3-VL-8B)",
        "L4: Material Conversion\n(Qwen3-VL-32B, 48 pairs)",
        "L4: Material Conversion\n(Qwen3-VL-8B, 48 pairs)",
        "L2: Stochastic T=0.2\n(8B pairwise / any-flip)",
    ]
    vals_a = [
        0.0,
        vd["level3_raytracing_rerender"]["32b"]["hit_flip_rate"] * 100.0,
        vd["level3_raytracing_rerender"]["8b"]["hit_flip_rate"] * 100.0,
        vd["level4_material_conversion_on_control_pairs"]["32b"]["flip_rate"] * 100.0,
        vd["level4_material_conversion_on_control_pairs"]["8b"]["flip_rate"] * 100.0,
        vd["level2_stochastic_decoding_8b_t02"]["pairwise_hit_disagreement_rate"] * 100.0,
    ]
    shifts_a = [
        0.0,
        vd["level3_raytracing_rerender"]["32b"]["mean_point_displacement_px"],
        vd["level3_raytracing_rerender"]["8b"]["mean_point_displacement_px"],
        vd["level4_material_conversion_on_control_pairs"]["32b"]["mean_point_displacement_px"],
        vd["level4_material_conversion_on_control_pairs"]["8b"]["mean_point_displacement_px"],
        vd["level2_stochastic_decoding_8b_t02"]["mean_point_displacement_px"],
    ]
    colors_a = ["#90A4AE", "#64B5F6", "#1E88E5", "#FF8A65", "#D84315", "#8E24AA"]
    y_pos = np.arange(len(labels_a))
    ax1.barh(y_pos, vals_a, height=0.58, color=colors_a, edgecolor="none")
    any_flip = vd["level2_stochastic_decoding_8b_t02"]["inputs_with_any_flip_rate"] * 100.0
    ax1.barh([5], [any_flip], height=0.58, color="none", edgecolor="#8E24AA", linestyle="--", linewidth=1.6, label="Stochastic any-flip across 5 draws (16.67%)")

    for idx, (v, px) in enumerate(zip(vals_a, shifts_a)):
        txt = f"{_pct2(v)} ({px:.1f} px)" if idx < 5 else f"{_pct2(v)} / {_pct2(any_flip)} ({px:.1f} px)"
        x_txt = max(v, any_flip if idx == 5 else v) + 0.4
        ax1.text(x_txt, idx, txt, va="center", fontsize=8.0, fontweight="bold" if idx in (3, 4) else "normal")

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels_a)
    ax1.set_xlim(0, 26.0)
    ax1.set_xlabel("Hit-Status Disagreement / Flip Rate (%)")
    ax1.set_title("(a) Four-Level Variance Floor (3 Control Scenes)")
    ax1.grid(axis="x", linestyle=":", alpha=0.45)

    # Panel (b): 30-scene / 480-pair Scaling & Cross-Family
    order_keys = ["qwen3_vl_2b", "qwen3_vl_8b_r0", "internvl3_5_8b", "qwen3_vl_32b_r0"]
    short_names = ["Qwen3-VL-2B\n(56.3→56.3%)", "Qwen3-VL-8B\n(81.3→83.1%)", "InternVL3.5-8B\n(80.2→79.6%)", "Qwen3-VL-32B\n(91.7→92.1%)"]
    losses = np.array([sf["models"][k]["metrics"]["loss_rate"]["estimate"] * 100.0 for k in order_keys])
    gains = np.array([sf["models"][k]["metrics"]["gain_rate"]["estimate"] * 100.0 for k in order_keys])
    flips = np.array([sf["models"][k]["metrics"]["flip_rate"]["estimate"] * 100.0 for k in order_keys])
    ci_lo = np.array([sf["models"][k]["metrics"]["flip_rate"]["scene_bootstrap_ci95"][0] * 100.0 for k in order_keys])
    ci_hi = np.array([sf["models"][k]["metrics"]["flip_rate"]["scene_bootstrap_ci95"][1] * 100.0 for k in order_keys])
    disps = [sf["models"][k]["metrics"]["cross_condition_point_displacement_px"]["estimate"] for k in order_keys]
    dhits = [sf["models"][k]["metrics"]["hit_rate_difference"]["estimate"] * 100.0 for k in order_keys]

    x_pos = np.arange(len(order_keys))
    ax2.bar(x_pos, losses, width=0.52, color="#E53935", label="Regression Loss (O-hit → C-miss)")
    ax2.bar(x_pos, gains, bottom=losses, width=0.52, color="#00897B", label="Conversion Gain (O-miss → C-hit)")
    ax2.errorbar(x_pos, flips, yerr=[flips - ci_lo, ci_hi - flips], fmt="none", ecolor="#263238", capsize=4, lw=1.4, zorder=4)

    for i, (fl, lo, ga, hi, dh, dp) in enumerate(zip(flips, losses, gains, ci_hi, dhits, disps)):
        ax2.text(i, hi + 0.55, f"Flip {_pct2(fl)}\n(Δ={_pct2(dh, signed=True)}, {dp:.1f} px)", ha="center", va="bottom", fontsize=7.8, fontweight="bold")
        if lo >= 2.2:
            ax2.text(
                i,
                lo * 0.5,
                f"{lo:.1f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=7.8,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.12", facecolor="#E53935", edgecolor="none", alpha=0.92),
                zorder=6,
            )
        if ga >= 2.2:
            ax2.text(
                i,
                lo + ga * 0.5,
                f"{ga:.1f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=7.8,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.12", facecolor="#00897B", edgecolor="none", alpha=0.92),
                zorder=6,
            )

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(short_names)
    ax2.set_xlim(-0.58, 3.55)
    ax2.set_ylim(0, 22.0)
    ax2.set_ylabel("Paired Decision Turnover Rate (%)")
    ax2.set_title("(b) 30-Scene Scaling & Cross-Family Turnover (480 Pairs)")
    ax2.legend(loc="upper right", frameon=True, facecolor="white", framealpha=0.9)
    ax2.grid(axis="y", linestyle=":", alpha=0.45)

    _save_both(fig, "cviu_v3_variance_and_scaling")


def build_mechanisms_figure() -> None:
    om = json.loads((V3_RAW_DIR / "optical_mechanisms.json").read_text(encoding="utf-8"))
    all480 = om["all_480_pairs"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 4.7), gridspec_kw={"width_ratios": [1.05, 1.15], "wspace": 0.28})

    # Panel (a): Counterfactuals vs Original
    conds = ["photo", "B", "T", "F"]
    c_labels = [
        "CIE L*a*b* Matched\n(Photometric Only)",
        "Background-Only\nConverted (I^B)",
        "Target-Only\nConverted (I^T)",
        "Full Conversion\n(I^F / UsdPreview)",
    ]
    losses = np.array([all480["losses_vs_original"][c]["estimate"] * 100.0 for c in conds])
    gains = np.array([all480["gains_vs_original"][c]["estimate"] * 100.0 for c in conds])
    flips = np.array([all480["flips_vs_original"][c]["estimate"] * 100.0 for c in conds])
    ci_lo = np.array([all480["flips_vs_original"][c]["scene_bootstrap_ci95"][0] * 100.0 for c in conds])
    ci_hi = np.array([all480["flips_vs_original"][c]["scene_bootstrap_ci95"][1] * 100.0 for c in conds])
    hits = [all480["hit_rates"][c]["estimate"] * 100.0 for c in conds]

    x = np.arange(len(conds))
    ax1.bar(x, losses, width=0.52, color="#EF5350", label="Loss vs. Original")
    ax1.bar(x, gains, bottom=losses, width=0.52, color="#26A69A", label="Gain vs. Original")
    ax1.errorbar(x, flips, yerr=[flips - ci_lo, ci_hi - flips], fmt="none", ecolor="#263238", capsize=4, lw=1.4, zorder=5)

    for i, (fl, hi, hr) in enumerate(zip(flips, ci_hi, hits)):
        ax1.text(i, hi + 0.35, f"{_pct2(fl)}\n(Hit {hr:.1f}%)", ha="center", va="bottom", fontsize=8.0, fontweight="bold")

    # Bracket comparing F vs photo
    y_br = 13.5
    ax1.plot([0, 0, 3, 3], [y_br - 0.35, y_br, y_br, y_br - 0.35], lw=1.5, color="#1A237E")
    ax1.text(1.5, y_br + 0.25, "Non-photometric BSDF residual: +3.54% [1.25%, 5.83%]", ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#1A237E")

    ax1.set_xticks(x)
    ax1.set_xticklabels(c_labels, fontsize=8.1)
    ax1.set_ylim(0, 18.2)
    ax1.set_ylabel("Decision Flip Rate vs. Original (%)")
    ax1.set_title("(a) 480-Pair Silhouette & Photometric Counterfactuals")
    ax1.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9)
    ax1.grid(axis="y", linestyle=":", alpha=0.45)

    # Panel (b): Prior optical regime stratification
    strata_order = ["Reflective/Metallic", "Matte/Diffuse", "Transparent/Glass", "Emissive/Screen"]
    strata = om["stratified_by_prior_optical_regime_8b"]
    y = np.arange(len(strata_order))
    s_loss = np.array([strata[k]["loss_rate"]["estimate"] * 100.0 for k in strata_order])
    s_gain = np.array([strata[k]["gain_rate"]["estimate"] * 100.0 for k in strata_order])
    s_net = np.array([strata[k]["net_delta"]["estimate"] * 100.0 for k in strata_order])
    s_n = [strata[k]["pair_count"] for k in strata_order]

    ax2.barh(y, -s_loss, height=0.52, color="#E53935", label="Regression Loss (%)")
    ax2.barh(y, s_gain, height=0.52, color="#00897B", label="Conversion Gain (%)")
    ax2.axvline(0.0, color="#37474F", lw=1.2)
    for i, (lo, ga, net, n) in enumerate(zip(s_loss, s_gain, s_net, s_n)):
        ax2.text(-lo - 0.25, i, f"-{_pct2(lo)}", ha="right", va="center", fontsize=8.0, color="#B71C1C", fontweight="bold")
        ax2.text(ga + 0.25, i, f"{_pct2(ga, signed=True)}  (Net {_pct2(net, signed=True)})", ha="left", va="center", fontsize=8.0, color="#004D40", fontweight="bold")

    ax2.set_yticks(y)
    ax2.set_yticklabels([f"{k}\n(n={n})" for k, n in zip(strata_order, s_n)])
    ax2.set_xlim(-8.5, 14.5)
    ax2.set_ylim(-0.55, 3.85)
    ax2.set_xlabel("Bidirectional Outcome Share (%)  [← Losses  |  Gains →]")
    ax2.set_title("(b) Optical Trade-Off Across Material Regimes (Qwen3-VL-8B)")
    ax2.legend(loc="upper right", ncol=2, frameon=True, facecolor="white", framealpha=0.95)
    ax2.grid(axis="x", linestyle=":", alpha=0.45)

    _save_both(fig, "cviu_v3_mechanisms")


def build_risk_gate_figure() -> None:
    ra = json.loads((V3_RAW_DIR / "risk_auditor.json").read_text(encoding="utf-8"))
    feats = json.loads((V3_RAW_DIR / "pair_optical_features.json").read_text(encoding="utf-8"))["records"]
    p8 = _load_idx(V1_RUNS_DIR / "8b/formal_repeat0/predictions.jsonl")
    p32 = _load_idx(V1_RUNS_DIR / "32b/formal_repeat0/predictions.jsonl")

    tgt_reports = ra["targets"]["any_8b_32b_loss"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 4.7), gridspec_kw={"width_ratios": [1.08, 1.08], "wspace": 0.26})

    # Panel (a): AUROC comparison
    models = [
        ("deploy_auto", "Deploy Auto\n(20 features)"),
        ("geometry_only", "Geometry Only\n(5 features)"),
        ("pixel_only", "Pixel Deltas\n(11 features)"),
        ("baseline_target_rgb_mae", "Target\nRGB MAE"),
        ("baseline_global_rgb_mae", "Global\nRGB MAE"),
    ]
    x = np.arange(len(models))
    w = 0.36
    test_aucs = [tgt_reports[k]["test_10_scenes"]["auroc"] for k, _ in models]
    loso_aucs = [tgt_reports[k]["loso_30_scenes"]["auroc"] for k, _ in models]

    b1 = ax1.bar(x - w / 2, test_aucs, width=w, color="#1E88E5", label="Held-out Test (10 scenes, n=160)")
    b2 = ax1.bar(x + w / 2, loso_aucs, width=w, color="#26A69A", label="30-Scene LOSO CV (n=480)")
    ax1.axhline(0.50, color="#78909C", linestyle="--", lw=1.2, label="Random Chance (0.50)")
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 0.015, f"{h:.3f}", ha="center", va="bottom", fontsize=7.6, fontweight="bold")

    ax1.set_xticks(x)
    ax1.set_xticklabels([lbl for _, lbl in models])
    ax1.set_ylim(0.0, 0.90)
    ax1.set_ylabel("ROC-AUC Predicting Conversion Loss")
    ax1.set_title("(a) Zero-VLM Pre-Deployment Risk Gate vs. Pixel Baselines")
    ax1.legend(loc="upper right", frameon=True, facecolor="white", framealpha=0.9)
    ax1.grid(axis="y", linestyle=":", alpha=0.45)

    # Panel (b): Dense Selective QA Retention Curve
    rows = []
    for f in feats:
        pid = f["pair_id"]
        l8 = int(bool(p8[(pid, "original")]["hit"]) and not bool(p8[(pid, "converted")]["hit"]))
        l32 = int(bool(p32[(pid, "original")]["hit"]) and not bool(p32[(pid, "converted")]["hit"]))
        rows.append({"split": f["split"], "scene_id": f["scene_id"], "y": int(bool(l8 or l32)), "f": f})

    tr_i = [i for i, r in enumerate(rows) if r["split"] == "train"]
    te_i = [i for i, r in enumerate(rows) if r["split"] == "test"]
    cols_geom = ("log_area_frac", "aspect_ratio", "center_dist_norm", "border_touch", "mask_iou")

    def _curve(y_arr: np.ndarray, s_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        order = np.argsort(-s_arr, kind="mergesort")
        ys = y_arr[order]
        cum = np.concatenate([[0.0], np.cumsum(ys) / max(ys.sum(), 1)])
        fracs = np.linspace(0.0, 1.0, len(cum))
        return fracs * 100.0, cum * 100.0

    X_auto = np.array([[float(r["f"][c]) for c in DEPLOY_AUTO_FEATURES] for r in rows], dtype=np.float64)
    y_all = np.array([r["y"] for r in rows], dtype=np.int64)
    c_auto = float(tgt_reports["deploy_auto"]["selected_c"])
    fit_auto = fit_standardized_l2_logreg(X_auto[tr_i], y_all[tr_i], c_reg=c_auto)
    s_test_auto = predict_proba_logreg(fit_auto, X_auto[te_i])
    s_test_gmae = np.array([float(rows[i]["f"]["global_rgb_mae"]) for i in te_i], dtype=np.float64)

    X_geom = np.array([[float(r["f"][c]) for c in cols_geom] for r in rows], dtype=np.float64)
    c_geom = float(tgt_reports["geometry_only"]["selected_c"])
    loso_geom = np.zeros(len(rows), dtype=np.float64)
    for sc in sorted({r["scene_id"] for r in rows}):
        tr = [i for i, r in enumerate(rows) if r["scene_id"] != sc]
        te = [i for i, r in enumerate(rows) if r["scene_id"] == sc]
        loso_geom[te] = predict_proba_logreg(fit_standardized_l2_logreg(X_geom[tr], y_all[tr], c_reg=c_geom), X_geom[te])

    fx_a, fy_a = _curve(y_all[te_i], s_test_auto)
    fx_l, fy_l = _curve(y_all, loso_geom)
    fx_m, fy_m = _curve(y_all[te_i], s_test_gmae)

    ax2.plot(fx_a, fy_a, color="#1E88E5", lw=2.3, label="Deploy Auto (Test 10 scenes: 41.7% @ 20%)")
    ax2.plot(fx_l, fy_l, color="#00897B", lw=2.3, linestyle="-.", label="Geometry Gate (30-LOSO: 52.0% @ 20%)")
    ax2.plot(fx_m, fy_m, color="#E53935", lw=1.8, linestyle=":", label="Global RGB MAE Baseline (16.7% @ 20%)")
    ax2.plot([0, 100], [0, 100], color="#90A4AE", lw=1.2, linestyle="--", label="Random Triage")
    ax2.axvline(20.0, color="#37474F", lw=1.0, linestyle="--", alpha=0.6)
    ax2.scatter([20.0, 20.0, 20.0], [41.7, 52.0, 16.7], s=55, color=["#1E88E5", "#00897B", "#E53935"], zorder=6)

    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 103)
    ax2.set_xlabel("Manual / Selective Shader Inspection Budget (%)")
    ax2.set_ylabel("Conversion Regressions Caught (%)")
    ax2.set_title("(b) Selective QA Hybrid Retention Curves")
    ax2.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.92, fontsize=8.0)
    ax2.grid(linestyle=":", alpha=0.45)

    _save_both(fig, "cviu_v3_risk_gate")


def main() -> None:
    build_hero_figure()
    build_variance_and_scaling_figure()
    build_mechanisms_figure()
    build_risk_gate_figure()


if __name__ == "__main__":
    main()
