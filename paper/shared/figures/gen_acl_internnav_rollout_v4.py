#!/usr/bin/env python3
"""Generate ACL Figure 4 v4 with a bounded left label gutter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gen_acl_main_figures_v2 as base
import gen_acl_paper_figures_v3 as v3


ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = ROOT / "paper/shared/figures"
OUTPUT_NAME = "fig_internnav_rollout_main_v4"
OUTPUT_FORMATS = (".svg", ".pdf", ".png")

FIG_WIDTH = 7.2
FIG_HEIGHT = 2.75
FIRST_IMAGE_X = 0.150
LABEL_RIGHT_X = 0.138
LABEL_IMAGE_GAP = FIRST_IMAGE_X - LABEL_RIGHT_X
COL_X = (0.1500, 0.3575, 0.5650, 0.7725)
COL_W = 0.1975
ROW_Y = (0.615, 0.335, 0.055)
ROW_H = 0.235


def _validate_layout(
    fig: plt.Figure,
    *,
    row_labels: list[Any],
) -> dict[str, object]:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    figure_box = fig.bbox
    findings: list[str] = []
    minimum_gap_px = LABEL_IMAGE_GAP * figure_box.width

    for label in row_labels:
        bbox = label.get_window_extent(renderer=renderer)
        image_left_px = FIRST_IMAGE_X * figure_box.width
        if bbox.x1 > image_left_px - minimum_gap_px:
            findings.append(
                f"{label.get_text().splitlines()[0]} reaches x={bbox.x1:.2f}px; "
                f"maximum is {image_left_px - minimum_gap_px:.2f}px"
            )

    for text in fig.texts:
        bbox = text.get_window_extent(renderer=renderer)
        if (
            bbox.x0 < -0.5
            or bbox.y0 < -0.5
            or bbox.x1 > figure_box.width + 0.5
            or bbox.y1 > figure_box.height + 0.5
        ):
            findings.append(f"text outside canvas: {text.get_text()!r}")

    for index, axis in enumerate(fig.axes):
        bbox = axis.get_position()
        if bbox.x0 < 0 or bbox.y0 < 0 or bbox.x1 > 1 or bbox.y1 > 1:
            findings.append(f"axis {index} outside normalized canvas: {bbox.bounds}")

    if findings:
        raise ValueError("Figure 4 layout validation failed:\n- " + "\n- ".join(findings))

    return {
        "ok": True,
        "canvas_inches": [FIG_WIDTH, FIG_HEIGHT],
        "label_right_x": LABEL_RIGHT_X,
        "first_image_x": FIRST_IMAGE_X,
        "declared_gap_fraction": LABEL_IMAGE_GAP,
        "declared_gap_pixels_at_300_dpi": LABEL_IMAGE_GAP * FIG_WIDTH * 300,
        "row_label_count": len(row_labels),
        "column_count": len(COL_X),
        "findings": [],
    }


def build(output_dir: Path) -> dict[str, object]:
    v3.apply_style()
    cases = base._nav_case_map()
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), facecolor="white")

    columns = (
        ("Original start", v3.COLORS["original"], "original", "start"),
        ("Original end", v3.COLORS["original"], "original", "end"),
        ("noMDL start", v3.COLORS["converted"], "nomdl", "start"),
        ("noMDL end", v3.COLORS["converted"], "nomdl", "end"),
    )
    for x, (title, color, _, _) in zip(COL_X, columns):
        v3._condition_header(fig, x, 0.91, COL_W, title, color)

    fig.text(
        0.015,
        0.955,
        "● executed",
        color=v3.COLORS["trajectory"],
        fontsize=6.0,
        fontweight="bold",
    )
    fig.text(
        0.015,
        0.918,
        "● reference",
        color=v3.COLORS["pass"],
        fontsize=6.0,
        fontweight="bold",
    )

    row_labels: list[Any] = []
    for row_index, (case_key, y) in enumerate(zip(base.NAV_CASES, ROW_Y)):
        case = cases[case_key]
        case_type, sr = base._case_summary(case)
        short_type = {
            "both success divergent": "both success",
            "original only success": "original only",
            "modified only success": "noMDL only",
        }.get(case_type, case_type)
        score = sr.replace("SR O/N ", "")
        label = f"{case_key}\n{short_type}\nSR O/N {score}"
        fig.text(
            0.018,
            y + ROW_H / 2,
            chr(ord("a") + row_index),
            fontsize=7.5,
            fontweight="bold",
            color=v3.COLORS["structure"],
            va="center",
        )
        row_labels.append(
            fig.text(
                LABEL_RIGHT_X,
                y + ROW_H / 2,
                label,
                fontsize=6.0,
                color=v3.COLORS["ink"],
                ha="right",
                va="center",
                linespacing=1.22,
            )
        )
        for x, (_, border, condition, moment) in zip(COL_X, columns):
            base._add_image(
                fig,
                (x, y, COL_W, ROW_H),
                base._nav_still(case_key, condition, moment),
                border=border,
                linewidth=0.8,
            )

    report = _validate_layout(fig, row_labels=row_labels)
    outputs = v3._save_bundle(fig, output_dir / OUTPUT_NAME)
    output_labels: list[str] = []
    for path in outputs:
        try:
            output_labels.append(str(path.relative_to(ROOT)))
        except ValueError:
            output_labels.append(str(path))
    report["outputs"] = output_labels
    report["formats"] = list(OUTPUT_FORMATS)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=FIG_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(build(args.output_dir.resolve()), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
