#!/usr/bin/env python3
"""Generate a compact qualitative comparison figure for the GRScenes case study."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent / "out_tmp"
PAIRS = [
    ("orbit_mdl_01.png", "orbit_01.png", "View 1"),
    ("orbit_mdl_03.png", "orbit_03.png", "View 2"),
]
OUT_PNG = Path(__file__).resolve().parent / "fig_grscene_qualitative.png"

CELL_W = 420
CELL_H = 236
MARGIN = 24
GAP_X = 24
GAP_Y = 22
TITLE_H = 24
LABEL_H = 28


def _fit_image(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    img.thumbnail((CELL_W, CELL_H))
    canvas = Image.new("RGB", (CELL_W, CELL_H), "white")
    x = (CELL_W - img.width) // 2
    y = (CELL_H - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def main() -> None:
    rows = len(PAIRS)
    width = MARGIN * 2 + CELL_W * 2 + GAP_X
    height = MARGIN * 2 + TITLE_H + rows * (CELL_H + LABEL_H) + (rows - 1) * GAP_Y

    canvas = Image.new("RGB", (width, height), (248, 248, 248))
    draw = ImageDraw.Draw(canvas)

    draw.text((MARGIN + 150, MARGIN), "MDL", fill="black")
    draw.text((MARGIN + CELL_W + GAP_X + 140, MARGIN), "noMDL", fill="black")

    y0 = MARGIN + TITLE_H
    for idx, (mdl_name, nomdl_name, view_label) in enumerate(PAIRS):
        y = y0 + idx * (CELL_H + LABEL_H + GAP_Y)
        mdl_img = _fit_image(ROOT / "mdl_images" / mdl_name)
        nomdl_img = _fit_image(ROOT / "nomdl_images" / nomdl_name)
        canvas.paste(mdl_img, (MARGIN, y))
        canvas.paste(nomdl_img, (MARGIN + CELL_W + GAP_X, y))

        draw.rectangle((MARGIN, y, MARGIN + CELL_W, y + CELL_H), outline=(180, 180, 180), width=1)
        draw.rectangle(
            (MARGIN + CELL_W + GAP_X, y, MARGIN + CELL_W + GAP_X + CELL_W, y + CELL_H),
            outline=(180, 180, 180),
            width=1,
        )
        draw.text((MARGIN + 6, y + CELL_H + 5), view_label, fill=(40, 40, 40))

    canvas.save(OUT_PNG)
    print(OUT_PNG)


if __name__ == "__main__":
    main()
