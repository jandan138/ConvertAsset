#!/usr/bin/env python3
"""Build a wide ACL panel for proxy and GRScenes render evidence."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
RAW = ROOT / "evidence" / "raw"
OUT = FIG_DIR / "fig_render_scene_evidence_wide.png"
OUT_PDF = FIG_DIR / "fig_render_scene_evidence_wide.pdf"

OBJECT_PAIRS = [
    (
        "#0011",
        RAW / "renders/chestofdrawers_0011/A_top_front_right.png",
        RAW / "renders/chestofdrawers_0011/B_top_front_right.png",
        (250, 80, 730, 650),
    ),
    (
        "#0023",
        RAW / "renders/chestofdrawers_0023/A_top_front_right.png",
        RAW / "renders/chestofdrawers_0023/B_top_front_right.png",
        (45, 90, 1010, 700),
    ),
]
SCENE_PAIRS = [
    (
        "View 1",
        FIG_DIR / "out_tmp/mdl_images/orbit_mdl_01.png",
        FIG_DIR / "out_tmp/nomdl_images/orbit_01.png",
    ),
    (
        "View 2",
        FIG_DIR / "out_tmp/mdl_images/orbit_mdl_03.png",
        FIG_DIR / "out_tmp/nomdl_images/orbit_03.png",
    ),
]

WIDTH = 1800
MARGIN = 34
GAP = 26
CELL_W = (WIDTH - 2 * MARGIN - GAP) // 2
OBJECT_CELL_W = CELL_W
OBJECT_H = 380
SCENE_H = 360
TITLE_H = 0
SUBTITLE_H = 0
ROW_LABEL_H = 28
ROW_FOOTER_H = 0
ROW_GAP = 20


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    names = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in names if bold else reversed(names):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _fit(
    path: Path,
    size: tuple[int, int],
    *,
    fill: tuple[int, int, int],
    crop: tuple[int, int, int, int] | None = None,
    cover: bool = False,
) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if crop is not None:
        image = image.crop(crop)
    if cover:
        return ImageOps.fit(
            image,
            size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, fill)
    canvas.paste(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return canvas


def _draw_cell(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    path: Path,
    size: tuple[int, int],
    header: str,
    sublabel: str,
    fill: tuple[int, int, int],
    crop: tuple[int, int, int, int] | None = None,
    cover: bool = False,
) -> None:
    header_font = _font(22, bold=True)
    label_font = _font(14)
    draw.text((x, y), header, fill=(20, 20, 20), font=header_font)
    image_y = y + ROW_LABEL_H
    canvas.paste(_fit(path, size, fill=fill, crop=crop, cover=cover), (x, image_y))
    draw.rectangle((x, image_y, x + size[0], image_y + size[1]), outline=(160, 160, 160), width=1)
    if sublabel and ROW_FOOTER_H > 0:
        draw.text((x + 6, image_y + size[1] + 5), sublabel, fill=(45, 45, 45), font=label_font)


def _draw_row_label(
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    label: str,
    note: str,
) -> None:
    label_font = _font(21, bold=True)
    note_font = _font(13)
    draw.text((MARGIN, y), label, fill=(25, 25, 25), font=label_font)
    if note:
        draw.text((MARGIN + 310, y + 3), note, fill=(70, 70, 70), font=note_font)


def _object_sublabel(asset_label: str, path: Path, crop: tuple[int, int, int, int] | None) -> str:
    view = path.stem.split("_", 1)[1].replace("_", "-")
    crop_prefix = "cropped " if crop is not None else ""
    return f"{asset_label} {crop_prefix}{view} object view"


def main() -> None:
    height = (
        MARGIN
        + TITLE_H
        + SUBTITLE_H
        + ROW_LABEL_H
        + OBJECT_H
        + ROW_FOOTER_H
        + ROW_GAP
        + ROW_LABEL_H
        + SCENE_H
        + ROW_FOOTER_H
        + MARGIN
    )
    canvas = Image.new("RGB", (WIDTH, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    y = MARGIN + TITLE_H + SUBTITLE_H
    scene_x_positions = [MARGIN, MARGIN + CELL_W + GAP]
    object_row_w = OBJECT_CELL_W * 2 + GAP
    object_x_positions = [(WIDTH - object_row_w) // 2, (WIDTH - object_row_w) // 2 + OBJECT_CELL_W + GAP]

    asset_label, mdl_path, nomdl_path, crop = OBJECT_PAIRS[0]
    _draw_row_label(
        draw,
        y=y,
        label="Proxy object pair",
        note="",
    )
    y += ROW_LABEL_H
    for col, (condition, path) in enumerate((("Original MDL", mdl_path), ("noMDL", nomdl_path))):
        _draw_cell(
            canvas,
            draw,
            x=object_x_positions[col],
            y=y,
            path=path,
            size=(OBJECT_CELL_W, OBJECT_H),
            header=condition,
            sublabel=_object_sublabel(asset_label, path, crop),
            fill=(246, 246, 246),
            crop=crop,
            cover=True,
        )

    y += ROW_LABEL_H + OBJECT_H + ROW_FOOTER_H + ROW_GAP
    view_label, mdl_path, nomdl_path = SCENE_PAIRS[0]
    _draw_row_label(
        draw,
        y=y,
        label="GRScenes scene pair",
        note="",
    )
    y += ROW_LABEL_H
    for col, (condition, path) in enumerate((("Original MDL", mdl_path), ("noMDL", nomdl_path))):
        _draw_cell(
            canvas,
            draw,
            x=scene_x_positions[col],
            y=y,
            path=path,
            size=(CELL_W, SCENE_H),
            header=condition,
            sublabel=f"GRScenes {view_label}",
            fill=(250, 250, 250),
            cover=True,
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT)
    canvas.save(OUT_PDF, "PDF", resolution=300.0)
    print(OUT)
    print(OUT_PDF)


if __name__ == "__main__":
    main()
