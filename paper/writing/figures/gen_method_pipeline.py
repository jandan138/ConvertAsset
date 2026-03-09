#!/usr/bin/env python3
"""Generate a publication-ready methodology pipeline figure for the paper."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path(__file__).resolve().parent
STEM = "fig_method_pipeline"


def add_box(ax, x, y, w, h, title, body, facecolor, edgecolor="#253238", lw=1.2):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=lw,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h - 0.04,
        title,
        ha="center",
        va="top",
        fontsize=9.0,
        fontweight="bold",
        color="#162026",
        family="DejaVu Serif",
    )
    ax.text(
        x + 0.03,
        y + h - 0.11,
        body,
        ha="left",
        va="top",
        fontsize=6.2,
        color="#1f2a30",
        family="DejaVu Serif",
        linespacing=1.14,
    )


def add_arrow(ax, start, end, color="#44545c", style="-|>", mutation_scale=11, lw=1.2, ls="-"):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=mutation_scale,
        linewidth=lw,
        linestyle=ls,
        color=color,
        shrinkA=0,
        shrinkB=0,
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(arrow)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 9,
            "axes.linewidth": 0.8,
        }
    )

    fig = plt.figure(figsize=(7.1, 3.0), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    add_box(
        ax,
        0.02,
        0.43,
        0.15,
        0.34,
        "Input Scene",
        "USD stage with MDL\nmaterials and arcs.",
        facecolor="#edf2f5",
    )

    add_box(
        ax,
        0.21,
        0.43,
        0.18,
        0.34,
        "1. Traverse",
        "Collect sublayers,\nreferences, payloads,\nvariants, and clips.\nNo flattening.\nCycle detection +\nde-duplication.",
        facecolor="#e8f1fb",
    )

    add_box(
        ax,
        0.42,
        0.43,
        0.18,
        0.34,
        "2. Convert",
        "Per-file MDL -> Preview.\nMap base color,\nroughness, metallic,\nand normal.\nDrop advanced\nMDL features.",
        facecolor="#eaf6ef",
    )

    add_box(
        ax,
        0.63,
        0.43,
        0.18,
        0.34,
        "3. Rewrite",
        "Redirect arcs to sibling\n*_noMDL.usd files.\nPreserve scene structure\nand an openable root\ncomposition.",
        facecolor="#fbf1e7",
    )

    add_box(
        ax,
        0.84,
        0.43,
        0.14,
        0.34,
        "Converted USD",
        "Preview-only materials\nwith preserved\ncomposition.",
        facecolor="#edf2f5",
    )

    add_box(
        ax,
        0.84,
        0.09,
        0.065,
        0.16,
        "GLB",
        "",
        facecolor="#f5f7fa",
        lw=1.0,
    )

    add_box(
        ax,
        0.915,
        0.09,
        0.065,
        0.16,
        "Eval",
        "",
        facecolor="#f5f7fa",
        lw=1.0,
    )

    add_arrow(ax, (0.17, 0.60), (0.21, 0.60))
    add_arrow(ax, (0.39, 0.60), (0.42, 0.60))
    add_arrow(ax, (0.60, 0.60), (0.63, 0.60))
    add_arrow(ax, (0.81, 0.60), (0.84, 0.60))

    add_arrow(ax, (0.91, 0.43), (0.91, 0.27), lw=1.0, ls="--")
    add_arrow(ax, (0.91, 0.27), (0.872, 0.25), lw=1.0, ls="--")
    add_arrow(ax, (0.91, 0.27), (0.947, 0.25), lw=1.0, ls="--")

    ax.text(
        0.50,
        0.90,
        "Composition-preserving MDL-to-UsdPreviewSurface conversion pipeline",
        ha="center",
        va="center",
        fontsize=8.9,
        fontweight="bold",
        color="#162026",
        family="DejaVu Serif",
    )
    ax.text(
        0.50,
        0.85,
        "Each referenced file is processed independently and remains in-place inside the USD composition.",
        ha="center",
        va="center",
        fontsize=7.4,
        color="#43545c",
        family="DejaVu Serif",
    )

    for ext in ("svg", "pdf", "png"):
        fig.savefig(
            OUT_DIR / f"{STEM}.{ext}",
            bbox_inches="tight",
            pad_inches=0.03,
            dpi=300,
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
