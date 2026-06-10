#!/usr/bin/env python3
"""Crop selected InternNav supplemental sheets into per-case panels."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = ROOT / "shared" / "figures"
OUT_DIR = FIGURE_DIR / "supplement"


def crop_rows(source: Path, prefix: str, boxes: list[tuple[int, int, int, int]]) -> None:
    image = Image.open(source).convert("RGB")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for index, box in enumerate(boxes, start=1):
        crop = image.crop(box)
        crop.save(OUT_DIR / f"{prefix}_case{index:02d}.png")


def trim_panel(panel: Image.Image) -> Image.Image:
    """Remove near-uniform background margins from a source sheet cell."""
    background = Image.new("RGB", panel.size, panel.getpixel((0, panel.height - 1)))
    diff = ImageChops.difference(panel, background).convert("L")
    mask = diff.point(lambda pixel: 255 if pixel > 8 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return panel
    left, top, right, bottom = bbox
    pad = 4
    return panel.crop(
        (
            max(0, left - pad),
            max(0, top - pad),
            min(panel.width, right + pad),
            min(panel.height, bottom + pad),
        )
    )


def place_panel(panel: Image.Image, size: tuple[int, int]) -> Image.Image:
    panel = trim_panel(panel)
    contained = ImageOps.contain(panel, size, method=Image.Resampling.LANCZOS)
    cell = Image.new("RGB", size, "white")
    cell.paste(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return cell


def crop_0036_rows(
    source: Path,
    prefix: str,
    rows: list[tuple[tuple[int, int, int, int], str]],
) -> None:
    image = Image.open(source).convert("RGB")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    for index, (box, title) in enumerate(rows, start=1):
        row = image.crop(box)
        panel_area = row.crop((170, 0, row.width, row.height))
        column_width = panel_area.width // 6
        panels = [
            place_panel(
                panel_area.crop(
                    (
                        column_width * column,
                        0,
                        column_width * (column + 1) if column < 5 else panel_area.width,
                        row.height,
                    )
                ),
                (250, 150),
            )
            for column in range(6)
        ]

        gap = 10
        title_height = 28
        target_width, target_height = panels[0].size
        canvas_width = target_width * 3 + gap * 2
        canvas_height = title_height + target_height * 2 + gap
        canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((0, 6), title, fill=(20, 20, 20), font=font)

        for panel_index, panel in enumerate(panels):
            row_index = panel_index // 3
            col_index = panel_index % 3
            x = col_index * (target_width + gap)
            y = title_height + row_index * (target_height + gap)
            canvas.paste(panel, (x, y))

        canvas.save(OUT_DIR / f"{prefix}_case{index:02d}.png")


def main() -> None:
    crop_rows(
        FIGURE_DIR / "fig_internnav_rollout_selected6_supp.png",
        "internnav_selected6",
        [
            (0, 75, 1106, 435),
            (0, 485, 1106, 865),
            (0, 880, 1106, 1260),
            (0, 1298, 1106, 1678),
            (0, 1690, 1106, 2070),
            (0, 2090, 1106, 2470),
        ],
    )
    crop_0036_rows(
        FIGURE_DIR / "fig_internnav_rollout_0036_0066_selected6_supp.png",
        "internnav_0036_0066",
        [
            ((0, 60, 1706, 220), "898_898 | original_only_success"),
            ((0, 375, 1706, 535), "919_919 | modified_only_success"),
            ((0, 690, 1706, 850), "895_895 | both_failure_divergent"),
            ((0, 1005, 1706, 1165), "597_597 | both_success_divergent"),
            ((0, 1320, 1706, 1480), "891_891 | both_failure_neutral"),
            ((0, 1635, 1706, 1834), "598_598 | both_success_neutral"),
        ],
    )


if __name__ == "__main__":
    main()
