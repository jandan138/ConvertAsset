#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate publication-quality figures (PNG + PDF) with Matplotlib from faces.csv (path,faces).

Usage:
  python3 scripts/plot_faces_report_mpl.py \
      /opt/my_dev/ConvertAsset/reports/faces_YYYYMMDD_HHMMSS/faces.csv \
      --out-dir /opt/my_dev/ConvertAsset/reports/faces_YYYYMMDD_HHMMSS

Figures (both .png and .pdf):
  - faces_hist_linear_mpl
  - faces_hist_log_mpl
  - faces_cdf_mpl
  - faces_top20_mpl

The script avoids extra dependencies (no pandas, seaborn). It configures Matplotlib
for a paper-friendly serif style and saves high-resolution outputs (PNG 300 DPI + PDF).
"""
from __future__ import annotations
import os
import csv
import math
import argparse
from typing import List, Tuple

# Headless backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def read_faces_csv(csv_path: str) -> List[Tuple[str, int]]:
    rows: List[Tuple[str, int]] = []
    with open(csv_path, "r", newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        for line in r:
            if not line:
                continue
            p = line[0]
            try:
                faces = int(line[1])
            except Exception:
                continue
            rows.append((p, faces))
    return rows


def percentile(sorted_vals: List[int], q: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return float(d0 + d1)


def setup_style():
    # Serif font and clean axis for paper-like style
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Times", "Georgia"],
        "axes.titlesize": 16,
        "axes.labelsize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.alpha": 0.3,
        "grid.linestyle": "-",
        "grid.linewidth": 0.8,
    })


def save_figure(fig: plt.Figure, out_base: str):
    png_path = out_base + ".png"
    pdf_path = out_base + ".pdf"
    fig.tight_layout()
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)
    return png_path, pdf_path


def plot_hist_linear(values: List[int], out_base: str):
    vals = np.asarray(values)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.grid(True, which="both")
    n, bins, patches = ax.hist(vals, bins=50, color="#1f77b4", edgecolor="#1f77b4", alpha=0.85)
    ax.set_xlabel("Faces per asset")
    ax.set_ylabel("Count of assets")

    # Quantile lines
    svals = np.sort(vals)
    for q, color, label in [(0.5, "#d62728", "Median"), (0.9, "#2ca02c", "p90"), (0.99, "#9467bd", "p99")]:
        qv = percentile(list(svals), q)
        ax.axvline(qv, color=color, linestyle="--", linewidth=1.5)
        ax.text(qv, ax.get_ylim()[1]*0.95, f"{label}: {int(qv):,}", color=color, rotation=90,
                va="top", ha="right", fontsize=11, bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=2))

    return save_figure(fig, out_base)


def plot_hist_log(values: List[int], out_base: str):
    vals = np.asarray(values)
    vmin = max(1, int(vals.min()))
    vmax = int(vals.max())
    # Log-spaced bins in base 10
    bins = np.logspace(np.log10(vmin), np.log10(max(vmax, vmin+1)), 50)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.grid(True, which="both")
    ax.hist(vals, bins=bins, color="#2ca02c", edgecolor="#2ca02c", alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlabel("Faces per asset (log scale)")
    ax.set_ylabel("Count of assets")
    return save_figure(fig, out_base)


def plot_cdf(values: List[int], out_base: str):
    vals = np.sort(np.asarray(values))
    n = len(vals)
    y = np.linspace(0, 1, n)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.grid(True, which="both")
    ax.plot(vals, y, color="#d62728", linewidth=2.0)
    ax.set_xlabel("Faces per asset")
    ax.set_ylabel("CDF")

    # Quantile markers
    for q, color in [(0.5, "#1f77b4"), (0.9, "#1f77b4"), (0.99, "#1f77b4")]:
        qv = percentile(list(vals), q)
        ax.scatter([qv], [q], color=color, s=25, zorder=5)
        ax.text(qv, q, f" {int(q*100)}%: {int(qv):,}", va="bottom", ha="left", fontsize=11,
                bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=1))

    return save_figure(fig, out_base)


def plot_top20(pairs: List[Tuple[str, int]], out_base: str):
    top = sorted(pairs, key=lambda x: x[1], reverse=True)[:20]
    labels = ["/".join([p for p in t[0].split('/') if p][-2:]) for t in top]
    values = [t[1] for t in top]
    y = np.arange(len(top))

    fig, ax = plt.subplots(figsize=(10, 9))
    ax.grid(True, axis="x")
    bars = ax.barh(y, values, color="#ff7f0e", alpha=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()  # largest at top
    ax.set_xlabel("Faces")

    # Value labels
    for rect, v in zip(bars, values):
        x = rect.get_width()
        y0 = rect.get_y() + rect.get_height()/2
        ax.text(x + max(values)*0.01, y0, f"{v:,}", va="center", ha="left", fontsize=11)

    return save_figure(fig, out_base)


def write_markdown_append(out_dir: str, stats_block: str, fig_pairs: List[Tuple[str, str]]):
    md_path = os.path.join(out_dir, "faces_report.md")
    lines: List[str] = []
    lines.append("\n## Matplotlib charts (PNG/PDF)\n\n")
    for title, png_name in [
        ("Histogram (linear)", os.path.basename(fig_pairs[0][0])),
        ("Histogram (log10 bins)", os.path.basename(fig_pairs[1][0])),
        ("CDF", os.path.basename(fig_pairs[2][0])),
        ("Top 20", os.path.basename(fig_pairs[3][0])),
    ]:
        lines.append(f"**{title}**\n\n")
        lines.append(f"![{title}]({png_name})\n\n")
    with open(md_path, "a", encoding="utf-8") as f:
        f.write("".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Matplotlib figures for faces report")
    ap.add_argument("csv_path", help="faces.csv produced by batch_count_faces.py")
    ap.add_argument("--out-dir", default=None, help="Output directory (default: same dir as csv)")
    args = ap.parse_args()

    csv_path = os.path.abspath(args.csv_path)
    if not os.path.isfile(csv_path):
        print("CSV not found:", csv_path)
        return 2
    out_dir = os.path.abspath(args.out_dir or os.path.dirname(csv_path))
    os.makedirs(out_dir, exist_ok=True)

    pairs = read_faces_csv(csv_path)
    if not pairs:
        print("No data rows found in:", csv_path)
        return 0

    values = [v for _, v in pairs]

    setup_style()

    fig1 = plot_hist_linear(values, os.path.join(out_dir, "faces_hist_linear_mpl"))
    fig2 = plot_hist_log(values, os.path.join(out_dir, "faces_hist_log_mpl"))
    fig3 = plot_cdf(values, os.path.join(out_dir, "faces_cdf_mpl"))
    fig4 = plot_top20(pairs, os.path.join(out_dir, "faces_top20_mpl"))

    write_markdown_append(out_dir, "", [fig1, fig2, fig3, fig4])

    print("Matplotlib figures generated at:", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
