#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read a faces.csv (path,faces) file, compute summary stats, render publication-quality
SVG charts, and write a Markdown report into the same output directory.

No third-party dependencies: all charts are hand-crafted SVGs with consistent
paper-friendly typography (serif font), clear axes and gridlines, and quantile
annotations. Results are vector graphics suitable for print.

Usage:
    python3 scripts/plot_faces_report.py \
            /opt/my_dev/ConvertAsset/reports/faces_YYYYMMDD_HHMMSS/faces.csv \
            --out-dir /opt/my_dev/ConvertAsset/reports/faces_YYYYMMDD_HHMMSS
"""
from __future__ import annotations
import os
import csv
import math
import argparse
from datetime import datetime
from typing import List, Tuple


def read_faces_csv(csv_path: str) -> List[Tuple[str, int]]:
    rows: List[Tuple[str, int]] = []
    with open(csv_path, "r", newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        # Expect header [path, faces]
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


def nice_unit(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.2f}K"
    return str(n)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def svg_header(w: int, h: int) -> str:
    # Use serif fonts and black text for print; white background; crisp edges
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">\n'
        f'<rect width="100%" height="100%" fill="#ffffff"/>\n'
        f'<style>\n'
        f'  text {{ fill: #000; font-family: "Times New Roman", Times, Georgia, serif; }}\n'
        f'  .axis {{ stroke: #000; stroke-width: 1.5; shape-rendering: crispEdges; }}\n'
        f'  .grid {{ stroke: #cccccc; stroke-width: 1; shape-rendering: crispEdges; }}\n'
        f'  .tick {{ stroke: #000; stroke-width: 1; }}\n'
        f'</style>\n'
    )


def svg_footer() -> str:
    return "</svg>\n"


def _nice_ticks(vmin: float, vmax: float, nticks: int = 6) -> List[float]:
    if vmin == vmax:
        return [vmin]
    span = vmax - vmin
    raw = span / max(1, nticks - 1)
    mag = 10 ** math.floor(math.log10(raw))
    norm = raw / mag
    if norm < 1.5:
        step = 1 * mag
    elif norm < 3:
        step = 2 * mag
    elif norm < 7:
        step = 5 * mag
    else:
        step = 10 * mag
    start = math.floor(vmin / step) * step
    end = math.ceil(vmax / step) * step
    ticks = []
    x = start
    # Safe guard for extreme loops
    for _ in range(1000):
        if x > end + 1e-9:
            break
        ticks.append(x)
        x += step
    return ticks


def draw_histogram_svg(values: List[int], out_path: str, bins: int = 50, width: int = 1200, height: int = 700, title: str = "Faces per asset (histogram)") -> None:
    if not values:
        save_text(out_path, svg_header(width, height) + svg_footer())
        return
    margin_left = 90
    margin_bottom = 80
    margin_top = 20
    margin_right = 30
    margin = 60  # kept for minor spacing reuse
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        vmax = vmin + 1

    bin_edges = [vmin + i * (vmax - vmin) / bins for i in range(bins + 1)]
    counts = [0] * bins
    for v in values:
        if v == vmax:
            idx = bins - 1
        else:
            idx = int((v - vmin) / (vmax - vmin) * bins)
            idx = max(0, min(bins - 1, idx))
        counts[idx] += 1

    max_count = max(counts) if counts else 1

    svg = [svg_header(width, height)]

    # Axes
    x0 = margin_left
    y0 = height - margin_bottom
    x1 = width - margin_right
    y1 = margin_top
    svg.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    svg.append(f'<line class="axis" x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}"/>')

    # Gridlines and ticks
    xticks = _nice_ticks(vmin, vmax, nticks=6)
    yticks = _nice_ticks(0, max_count, nticks=5)
    for t in xticks:
        px = x0 + (t - vmin) / (vmax - vmin) * plot_w
        svg.append(f'<line class="grid" x1="{px:.2f}" y1="{y0}" x2="{px:.2f}" y2="{y1}"/>')
        svg.append(f'<line class="tick" x1="{px:.2f}" y1="{y0}" x2="{px:.2f}" y2="{y0+6}"/>')
        svg.append(f'<text x="{px:.2f}" y="{y0+28}" text-anchor="middle" font-size="14">{nice_unit(int(t))}</text>')
    for t in yticks:
        py = y0 - (t - 0) / (max_count - 0 if max_count>0 else 1) * plot_h
        svg.append(f'<line class="grid" x1="{x0}" y1="{py:.2f}" x2="{x1}" y2="{py:.2f}"/>')
        svg.append(f'<line class="tick" x1="{x0-6}" y1="{py:.2f}" x2="{x0}" y2="{py:.2f}"/>')
        svg.append(f'<text x="{x0-10}" y="{py+5:.2f}" text-anchor="end" font-size="14">{int(t)}</text>')

    # Bars
    bar_w = plot_w / bins
    for i, c in enumerate(counts):
        if c == 0:
            continue
        x = x0 + i * bar_w
        h = (c / max_count) * plot_h
        y = y0 - h
        svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w-1:.2f}" height="{h:.2f}" fill="#1f77b4"/>')

    # Quantile lines (median, p90, p99)
    vals_sorted = sorted(values)
    q_pairs = [(0.5, "Median"), (0.9, "p90"), (0.99, "p99")]
    colors = {0.5: "#d62728", 0.9: "#2ca02c", 0.99: "#9467bd"}
    for q, label in q_pairs:
        qv = percentile(vals_sorted, q)
        px = x0 + (qv - vmin) / (vmax - vmin) * plot_w
        svg.append(f'<line x1="{px:.2f}" y1="{y0}" x2="{px:.2f}" y2="{y1}" stroke="{colors[q]}" stroke-width="1.5" stroke-dasharray="6,4"/>')
        svg.append(f'<text x="{px+6:.2f}" y="{y1+18}" text-anchor="start" font-size="12" fill="{colors[q]}">{label}: {nice_unit(int(qv))}</text>')

    # Axis labels
    svg.append(f'<text x="{(x0+x1)/2:.2f}" y="{height-20}" text-anchor="middle" font-size="16">Faces per asset</text>')
    svg.append(f'<text transform="translate(20,{(y0+y1)/2:.2f}) rotate(-90)" text-anchor="middle" font-size="16">Count of assets</text>')

    svg.append(svg_footer())
    save_text(out_path, "".join(svg))


def draw_log_histogram_svg(values: List[int], out_path: str, base: float = 10.0, width: int = 1200, height: int = 700, title: str = "Log-binned histogram") -> None:
    if not values:
        save_text(out_path, svg_header(width, height) + svg_footer())
        return
    margin_left = 90
    margin_bottom = 80
    margin_top = 20
    margin_right = 30
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    vmin = max(1, min(values))
    vmax = max(values)

    # Build log-spaced edges: base^k up to cover vmax
    kmin = int(math.floor(math.log(vmin, base)))
    kmax = int(math.ceil(math.log(max(vmax, vmin+1), base)))
    edges = [base ** k for k in range(kmin, kmax + 1)]
    bins = len(edges) - 1
    counts = [0] * bins

    for v in values:
        if v <= edges[0]:
            counts[0] += 1
            continue
        if v >= edges[-1]:
            counts[-1] += 1
            continue
        # binary search
        lo, hi = 0, len(edges) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if edges[mid] <= v:
                lo = mid + 1
            else:
                hi = mid
        idx = max(0, min(bins - 1, lo - 1))
        counts[idx] += 1

    max_count = max(counts) if counts else 1

    svg = [svg_header(width, height)]
    x0 = margin_left
    y0 = height - margin_bottom
    x1 = width - margin_right
    y1 = margin_top
    svg.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    svg.append(f'<line class="axis" x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}"/>')

    # Gridlines/ticks at powers of base
    for i, e in enumerate(edges):
        px = x0 + (i / (len(edges) - 1)) * plot_w
        svg.append(f'<line class="grid" x1="{px:.2f}" y1="{y0}" x2="{px:.2f}" y2="{y1}"/>')
        svg.append(f'<line class="tick" x1="{px:.2f}" y1="{y0}" x2="{px:.2f}" y2="{y0+6}"/>')
        svg.append(f'<text x="{px:.2f}" y="{y0+28}" text-anchor="middle" font-size="14">{nice_unit(int(e))}</text>')

    yticks = _nice_ticks(0, max_count, nticks=5)
    for t in yticks:
        py = y0 - (t / (max_count if max_count>0 else 1)) * plot_h
        svg.append(f'<line class="grid" x1="{x0}" y1="{py:.2f}" x2="{x1}" y2="{py:.2f}"/>')
        svg.append(f'<line class="tick" x1="{x0-6}" y1="{py:.2f}" x2="{x0}" y2="{py:.2f}"/>')
        svg.append(f'<text x="{x0-10}" y="{py+5:.2f}" text-anchor="end" font-size="14">{int(t)}</text>')

    bar_w = plot_w / max(1, bins)
    for i, c in enumerate(counts):
        if c == 0:
            continue
        x = x0 + i * bar_w
        h = (c / max_count) * plot_h
        y = y0 - h
        svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w-1:.2f}" height="{h:.2f}" fill="#2ca02c"/>')

    # X labels using first, mid, last edges
    # Axis labels
    svg.append(f'<text x="{(x0+x1)/2:.2f}" y="{height-20}" text-anchor="middle" font-size="16">Faces per asset (log10 bins)</text>')
    svg.append(f'<text transform="translate(20,{(y0+y1)/2:.2f}) rotate(-90)" text-anchor="middle" font-size="16">Count of assets</text>')

    svg.append(svg_footer())
    save_text(out_path, "".join(svg))


def draw_cdf_svg(values: List[int], out_path: str, width: int = 1200, height: int = 700, title: str = "CDF of faces") -> None:
    if not values:
        save_text(out_path, svg_header(width, height) + svg_footer())
        return
    margin_left = 90
    margin_bottom = 80
    margin_top = 20
    margin_right = 30
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    vals = sorted(values)
    vmin, vmax = vals[0], vals[-1]
    if vmax == vmin:
        vmax = vmin + 1
    n = len(vals)

    points = []
    # sample up to 2000 points for polyline to keep size reasonable
    step = max(1, n // 2000)
    for i in range(0, n, step):
        v = vals[i]
        cdf = i / (n - 1) if n > 1 else 1.0
        x = margin_left + (v - vmin) / (vmax - vmin) * plot_w
        y = (height - margin_bottom) - cdf * plot_h
        points.append((x, y))

    svg = [svg_header(width, height)]
    x0 = margin_left
    y0 = height - margin_bottom
    x1 = width - margin_right
    y1 = margin_top
    svg.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    svg.append(f'<line class="axis" x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}"/>')

    # Grid / ticks
    xticks = _nice_ticks(vmin, vmax, nticks=6)
    for t in xticks:
        px = x0 + (t - vmin) / (vmax - vmin) * plot_w
        svg.append(f'<line class="grid" x1="{px:.2f}" y1="{y0}" x2="{px:.2f}" y2="{y1}"/>')
        svg.append(f'<line class="tick" x1="{px:.2f}" y1="{y0}" x2="{px:.2f}" y2="{y0+6}"/>')
        svg.append(f'<text x="{px:.2f}" y="{y0+28}" text-anchor="middle" font-size="14">{nice_unit(int(t))}</text>')
    for frac, lbl in [(0.0, "0"), (0.25, "0.25"), (0.5, "0.5"), (0.75, "0.75"), (1.0, "1.0")]:
        py = y0 - frac * plot_h
        svg.append(f'<line class="grid" x1="{x0}" y1="{py:.2f}" x2="{x1}" y2="{py:.2f}"/>')
        svg.append(f'<line class="tick" x1="{x0-6}" y1="{py:.2f}" x2="{x0}" y2="{py:.2f}"/>')
        svg.append(f'<text x="{x0-10}" y="{py+5:.2f}" text-anchor="end" font-size="14">{lbl}</text>')

    # polyline
    pts_attr = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    svg.append(f'<polyline fill="none" stroke="#d62728" stroke-width="2.5" points="{pts_attr}"/>')

    # Quantile markers
    vals_sorted = sorted(values)
    for q in [0.5, 0.9, 0.99]:
        qv = percentile(vals_sorted, q)
        px = x0 + (qv - vmin) / (vmax - vmin) * plot_w
        py = y0 - q * plot_h
        svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="#1f77b4"/>')
        svg.append(f'<text x="{px+6:.2f}" y="{py-6:.2f}" text-anchor="start" font-size="12">{int(q*100)}%: {nice_unit(int(qv))}</text>')

    # Axis labels
    svg.append(f'<text x="{(x0+x1)/2:.2f}" y="{height-20}" text-anchor="middle" font-size="16">Faces per asset</text>')
    svg.append(f'<text transform="translate(20,{(y0+y1)/2:.2f}) rotate(-90)" text-anchor="middle" font-size="16">CDF</text>')

    svg.append(svg_footer())
    save_text(out_path, "".join(svg))


def draw_top_bar_svg(pairs: List[Tuple[str, int]], out_path: str, top_n: int = 20, width: int = 1200, height: int = 900, title: str = "Top 20 assets by faces") -> None:
    if not pairs:
        save_text(out_path, svg_header(width, height) + svg_footer())
        return
    pairs = sorted(pairs, key=lambda x: x[1], reverse=True)[:top_n]
    margin_left = 420  # wider for readable labels
    margin_right = 60
    margin_top = 30
    margin_bottom = 40
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    max_v = max(v for _, v in pairs)

    svg = [svg_header(width, height)]

    # Axes (horizontal bar chart)
    x0 = margin_left
    y0 = height - margin_bottom
    x1 = width - margin_right
    y1 = margin_top
    svg.append(f'<line class="axis" x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}"/>')
    svg.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')

    # Y positions for bars
    n = len(pairs)
    bar_h = plot_h / max(1, n)
    gap = min(10, bar_h * 0.15)

    # Grid and x ticks
    xticks = _nice_ticks(0, max_v, nticks=5)
    for t in xticks:
        px = x0 + (t / (max_v if max_v>0 else 1)) * plot_w
        svg.append(f'<line class="grid" x1="{px:.2f}" y1="{y1}" x2="{px:.2f}" y2="{y0}"/>')
        svg.append(f'<line class="tick" x1="{px:.2f}" y1="{y0}" x2="{px:.2f}" y2="{y0+6}"/>')
        svg.append(f'<text x="{px:.2f}" y="{y0+26}" text-anchor="middle" font-size="14">{nice_unit(int(t))}</text>')

    for i, (p, v) in enumerate(pairs):
        # label on the left
        parts = [pp for pp in p.split('/') if pp]
        label = "/".join(parts[-2:]) if len(parts) >= 2 else os.path.basename(p)
        cy = y1 + i * bar_h + bar_h/2
        svg.append(f'<text x="{x0-10}" y="{cy+5:.2f}" text-anchor="end" font-size="14">{label}</text>')
        # bar to the right
        w = (v / (max_v if max_v>0 else 1)) * plot_w
        svg.append(f'<rect x="{x0:.2f}" y="{cy - (bar_h-gap)/2:.2f}" width="{w:.2f}" height="{(bar_h-gap):.2f}" fill="#ff7f0e"/>')
        # value label near bar end
        svg.append(f'<text x="{x0 + w + 6:.2f}" y="{cy+5:.2f}" text-anchor="start" font-size="12">{nice_unit(v)}</text>')

    # Axis labels
    svg.append(f'<text x="{(x0+x1)/2:.2f}" y="{height-8}" text-anchor="middle" font-size="16">Faces</text>')

    svg.append(svg_footer())
    save_text(out_path, "".join(svg))


def write_markdown(out_dir: str, figures: dict, stats: dict, top_pairs: List[Tuple[str, int]]) -> None:
    md_path = os.path.join(out_dir, "faces_report.md")
    lines: List[str] = []
    lines.append(f"# Faces report\n\n")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append("## Summary\n\n")
    lines.append(f"- Files matched: {stats['count']}\n")
    lines.append(f"- Total faces: {stats['total']}\n")
    lines.append(f"- Mean faces: {stats['mean']:.2f}\n")
    lines.append(f"- Min faces: {stats['min']} (in {stats['min_path']})\n")
    lines.append(f"- Median (p50): {int(stats['p50'])}\n")
    lines.append(f"- p90: {int(stats['p90'])}, p95: {int(stats['p95'])}, p99: {int(stats['p99'])}\n")
    lines.append(f"- Max faces: {stats['max']} (in {stats['max_path']})\n\n")

    lines.append("## Charts\n\n")
    lines.append(f"![Histogram linear]({os.path.basename(figures['hist_linear'])})\n\n")
    lines.append(f"![Histogram log bins]({os.path.basename(figures['hist_log'])})\n\n")
    lines.append(f"![CDF]({os.path.basename(figures['cdf'])})\n\n")
    lines.append(f"![Top 20 by faces]({os.path.basename(figures['top20'])})\n\n")

    lines.append("## Top 20 assets by faces\n\n")
    lines.append("| Rank | Faces | Path |\n|---:|---:|:---|\n")
    for i, (p, v) in enumerate(sorted(top_pairs, key=lambda x: x[1], reverse=True)[:20], 1):
        lines.append(f"| {i} | {v} | {p} |\n")

    lines.append("\n---\n")
    lines.append("Report generated by scripts/plot_faces_report.py (SVG charts, no external deps).\n")

    save_text(md_path, "".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate faces report with SVG charts")
    ap.add_argument("csv_path", help="faces.csv produced by batch_count_faces.py")
    ap.add_argument("--out-dir", default=None, help="Output directory (default: same dir as csv)")
    args = ap.parse_args()

    csv_path = os.path.abspath(args.csv_path)
    if not os.path.isfile(csv_path):
        print("CSV not found:", csv_path)
        return 2

    out_dir = os.path.abspath(args.out_dir or os.path.dirname(csv_path))
    ensure_dir(out_dir)

    pairs = read_faces_csv(csv_path)
    if not pairs:
        print("No data rows found in:", csv_path)
        return 0

    values = [v for _, v in pairs]
    vals_sorted = sorted(values)
    total = int(sum(values))
    count = len(values)
    mean = total / count
    vmin = min(values)
    vmax = max(values)
    min_path = min(pairs, key=lambda x: x[1])[0]
    max_path = max(pairs, key=lambda x: x[1])[0]

    stats = {
        "count": count,
        "total": total,
        "mean": mean,
        "min": vmin,
        "max": vmax,
        "min_path": min_path,
        "max_path": max_path,
        "p50": percentile(vals_sorted, 0.5),
        "p90": percentile(vals_sorted, 0.9),
        "p95": percentile(vals_sorted, 0.95),
        "p99": percentile(vals_sorted, 0.99),
    }

    # Figures
    fig_hist_linear = os.path.join(out_dir, "faces_hist_linear.svg")
    fig_hist_log = os.path.join(out_dir, "faces_hist_log.svg")
    fig_cdf = os.path.join(out_dir, "faces_cdf.svg")
    fig_top20 = os.path.join(out_dir, "faces_top20.svg")

    draw_histogram_svg(values, fig_hist_linear, bins=50, title="Histogram (linear bins)")
    draw_log_histogram_svg(values, fig_hist_log, base=2.0, title="Histogram (log2 bins)")
    draw_cdf_svg(values, fig_cdf, title="CDF of faces per asset")
    draw_top_bar_svg(pairs, fig_top20, top_n=20, title="Top 20 assets by faces")

    figures = {
        "hist_linear": fig_hist_linear,
        "hist_log": fig_hist_log,
        "cdf": fig_cdf,
        "top20": fig_top20,
    }

    write_markdown(out_dir, figures, stats, pairs)

    print("Report generated at:", os.path.join(out_dir, "faces_report.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
