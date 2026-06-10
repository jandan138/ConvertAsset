#!/usr/bin/env python3
"""Build a render-heavy atlas page for the ACL supplement."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
RAW = ROOT / "evidence" / "raw"
OUT = FIG_DIR / "fig_supplement_render_atlas.png"

WIDTH = 1800
MARGIN = 38
GAP_X = 24
GAP_Y = 18
PROXY_CELL_W = (WIDTH - 2 * MARGIN - 3 * GAP_X) // 4
PROXY_CELL_H = 246
HEADER_H = 28
BLOCK_LABEL_H = 34

PROXY_ROWS = [
    (
        "Proxy #0004 controlled object view",
        ("MDL front", RAW / "renders/chestofdrawers_0004/A_front.png"),
        ("noMDL front", RAW / "renders/chestofdrawers_0004/B_front.png"),
        ("MDL detail", RAW / "renders/chestofdrawers_0004/A_top_front_left.png"),
        ("noMDL detail", RAW / "renders/chestofdrawers_0004/B_top_front_left.png"),
    ),
    (
        "Proxy #0011 controlled object view",
        ("MDL front", RAW / "renders/chestofdrawers_0011/A_front.png"),
        ("noMDL front", RAW / "renders/chestofdrawers_0011/B_front.png"),
        ("MDL detail", RAW / "renders/chestofdrawers_0011/A_top_front_left.png"),
        ("noMDL detail", RAW / "renders/chestofdrawers_0011/B_top_front_left.png"),
    ),
    (
        "Proxy #0023 held-out object view",
        ("MDL front", RAW / "renders/chestofdrawers_0023/A_front.png"),
        ("noMDL front", RAW / "renders/chestofdrawers_0023/B_front.png"),
        ("MDL detail", RAW / "renders/chestofdrawers_0023/A_top_front_right.png"),
        ("noMDL detail", RAW / "renders/chestofdrawers_0023/B_top_front_right.png"),
    ),
    (
        "Proxy #0029 held-out object view",
        ("MDL front", RAW / "renders/chestofdrawers_0029/A_front.png"),
        ("noMDL front", RAW / "renders/chestofdrawers_0029/B_front.png"),
        ("MDL detail", RAW / "renders/chestofdrawers_0029/A_top_front_right.png"),
        ("noMDL detail", RAW / "renders/chestofdrawers_0029/B_top_front_right.png"),
    ),
]

SCENE_ROWS = [
    (
        "GRScenes view 01 scene context",
        ("MDL", FIG_DIR / "out_tmp/mdl_images/orbit_mdl_01.png"),
        ("noMDL", FIG_DIR / "out_tmp/nomdl_images/orbit_01.png"),
    ),
    (
        "GRScenes view 03 scene context",
        ("MDL", FIG_DIR / "out_tmp/mdl_images/orbit_mdl_03.png"),
        ("noMDL", FIG_DIR / "out_tmp/nomdl_images/orbit_03.png"),
    ),
    (
        "GRScenes view 05 additional camera",
        ("MDL", FIG_DIR / "out_tmp/mdl_images/orbit_mdl_05.png"),
        ("noMDL", FIG_DIR / "out_tmp/nomdl_images/orbit_05.png"),
    ),
    (
        "GRScenes view 07 additional camera",
        ("MDL", FIG_DIR / "out_tmp/mdl_images/orbit_mdl_07.png"),
        ("noMDL", FIG_DIR / "out_tmp/nomdl_images/orbit_07.png"),
    ),
]


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (246, 246, 246))
    canvas.paste(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return canvas


def _draw_cell(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    condition: str,
    path: Path,
    size: tuple[int, int],
) -> None:
    label_font = _font(17, bold=True)
    image_y = y + HEADER_H
    image = _fit_image(path, size)
    canvas.paste(image, (x, image_y))
    draw.rectangle((x, image_y, x + size[0], image_y + size[1]), outline=(155, 155, 155), width=2)

    tag_fill = (28, 28, 28) if condition.startswith("MDL") else (0, 75, 120)
    draw.text((x + 4, y + 1), condition, fill=tag_fill, font=label_font)


def _draw_proxy_context_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    label: str,
    cells: tuple[tuple[str, Path], tuple[str, Path], tuple[str, Path], tuple[str, Path]],
) -> int:
    block_font = _font(22, bold=True)
    draw.text((MARGIN, y), label, fill=(18, 18, 18), font=block_font)
    y += BLOCK_LABEL_H
    for col, (condition, path) in enumerate(cells):
        x = MARGIN + col * (PROXY_CELL_W + GAP_X)
        _draw_cell(canvas, draw, x=x, y=y, condition=condition, path=path, size=(PROXY_CELL_W, PROXY_CELL_H))
    return y + HEADER_H + PROXY_CELL_H + GAP_Y


def main() -> None:
    scene_groups = [
        (
            "GRScenes scene context views 01/03",
            SCENE_ROWS[0][1],
            SCENE_ROWS[0][2],
            SCENE_ROWS[1][1],
            SCENE_ROWS[1][2],
        ),
        (
            "GRScenes additional camera views 05/07",
            SCENE_ROWS[2][1],
            SCENE_ROWS[2][2],
            SCENE_ROWS[3][1],
            SCENE_ROWS[3][2],
        ),
    ]
    row_count = len(PROXY_ROWS) + len(scene_groups)
    height = (
        MARGIN * 2
        + len(PROXY_ROWS) * (BLOCK_LABEL_H + HEADER_H + PROXY_CELL_H)
        + len(scene_groups) * (BLOCK_LABEL_H + HEADER_H + PROXY_CELL_H)
        + (row_count - 1) * GAP_Y
    )
    canvas = Image.new("RGB", (WIDTH, height), (245, 245, 245))
    draw = ImageDraw.Draw(canvas)

    y = MARGIN
    for label, *cells in PROXY_ROWS:
        y = _draw_proxy_context_row(canvas, draw, y=y, label=label, cells=tuple(cells))
    for label, *cells in scene_groups:
        y = _draw_proxy_context_row(canvas, draw, y=y, label=label, cells=tuple(cells))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
