#!/usr/bin/env python3
"""Build a readable main-text InternNav qualitative rollout panel."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
MEDIA_ROOT = (
    ROOT
    / "paper/shared/evidence/raw/internnav_vln_downstream/"
    "official_selected_qualitative_videos"
)
CASE_MANIFEST = MEDIA_ROOT / "manifests/kujiale0036_0066_video_case_manifest.json"
STILL_ROOT = MEDIA_ROOT / "stills/kujiale0036_0066"
OUT = ROOT / "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png"
OUT_COLUMN = ROOT / "paper/shared/figures/fig_internnav_rollout_0036_0066_column.png"

MAIN_CASE_KEYS = ("597_597", "898_898", "919_919")
COLUMN_CASE_KEY = "597_597"
MAIN_LABEL_W = 270
MAIN_CELL_W = 350
MAIN_CELL_H = 180
MAIN_GAP = 14
MAIN_ROW_KEY_FONT_PX = 22
MAIN_ROW_DETAIL_FONT_PX = 16
COLUMNS = (
    ("original", "start", "Original start"),
    ("original", "end", "Original end"),
    ("nomdl", "start", "noMDL start"),
    ("nomdl", "end", "noMDL end"),
)
CONDITION_ALIASES = {
    "original": "original",
    "nomdl": "nomdl",
}
OVERLAY_LEGEND = [
    {"color": "purple", "meaning": "agent action arrow and executed trajectory"},
    {"color": "green", "meaning": "reference path"},
]
LEGEND_SWATCHES = {
    "purple": (122, 64, 200),
    "green": (24, 140, 52),
}
AGENT_OVERLAY_COLOR = (122, 64, 200)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/usr/share/fonts/dejavu") / name,
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cases_by_key() -> dict[str, dict[str, Any]]:
    manifest = _load_json(CASE_MANIFEST)
    return {str(case["path_key"]): case for case in manifest["selected_cases"]}


def _still_path(path_key: str, condition: str, label: str) -> Path:
    pattern = f"kujiale0036_0066_{path_key}_{condition}_{label}_*.png"
    matches = sorted(STILL_ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"missing still for {path_key} {condition} {label}")
    return matches[0]


def _is_agent_overlay_red(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return r >= 150 and g <= 120 and b <= 120 and r >= g + 70 and r >= b + 70


def _recolor_agent_overlay(image: Image.Image) -> tuple[Image.Image, int]:
    """Recolor InternNav's red navigation overlay without editing source stills."""

    output = image.copy()
    pixels = []
    recolored = 0
    for pixel in output.getdata():
        if _is_agent_overlay_red(pixel):
            pixels.append(AGENT_OVERLAY_COLOR)
            recolored += 1
        else:
            pixels.append(pixel)
    output.putdata(pixels)
    return output, recolored


def _load_still(path: Path, size: tuple[int, int]) -> tuple[Image.Image, int]:
    image = Image.open(path).convert("RGB")
    image, recolored = _recolor_agent_overlay(image)
    return image.resize(size, Image.Resampling.LANCZOS), recolored


def _draw_label(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] = (25, 25, 25),
) -> None:
    draw.text(xy, text, fill=fill, font=font)


def _draw_overlay_legend(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
) -> None:
    x, y = xy
    swatch_w = 28
    text_gap = 8
    item_gap = 34
    for item in OVERLAY_LEGEND:
        color_name = str(item["color"])
        label = str(item["meaning"])
        swatch = LEGEND_SWATCHES[color_name]
        draw.rounded_rectangle((x, y + 5, x + swatch_w, y + 13), radius=3, fill=swatch)
        text_x = x + swatch_w + text_gap
        draw.text((text_x, y), label, fill=(55, 55, 55), font=font)
        bbox = draw.textbbox((text_x, y), label, font=font)
        x = bbox[2] + item_gap


def _row_label(case: dict[str, Any]) -> list[str]:
    path_key = str(case["path_key"])
    case_type = str(case.get("case_type", "")).replace("_", " ")
    scene_id = str(case.get("scene_id", "")).replace("kujiale_", "KJ ")
    original_sr = case.get("metrics", {}).get("original", {}).get("SR")
    nomdl_sr = case.get("metrics", {}).get("modified", {}).get("SR")
    return [
        path_key,
        case_type,
        f"{scene_id}  SR O/N {original_sr:g}/{nomdl_sr:g}",
    ]


def build() -> dict[str, Any]:
    cases = _cases_by_key()
    selected = [cases[key] for key in MAIN_CASE_KEYS]

    cell_w, cell_h = MAIN_CELL_W, MAIN_CELL_H
    label_w = MAIN_LABEL_W
    gap = MAIN_GAP
    header_h = 110
    row_h = cell_h + 40
    margin = 18
    width = margin * 2 + label_w + len(COLUMNS) * cell_w + (len(COLUMNS) - 1) * gap
    height = margin * 2 + header_h + len(selected) * row_h

    canvas = Image.new("RGB", (width, height), (248, 248, 245))
    draw = ImageDraw.Draw(canvas)
    font_title = _font(24, bold=True)
    font_header = _font(18, bold=True)
    font_label = _font(MAIN_ROW_KEY_FONT_PX, bold=True)
    font_detail = _font(MAIN_ROW_DETAIL_FONT_PX)
    font_small = _font(15)

    _draw_label(
        draw,
        (margin, margin),
        "Selected official KuJiaLe InternNav rollouts (0036/0066)",
        font_title,
    )
    _draw_label(
        draw,
        (margin, margin + 32),
        "Start/end frames shown for readability; selected videos/contact sheets retain full start-mid-end evidence.",
        font_small,
        fill=(70, 70, 70),
    )
    _draw_overlay_legend(draw, (margin, margin + 58), font_small)
    recolor_counts: list[dict[str, Any]] = []

    x0 = margin + label_w
    y_header = margin + header_h - 30
    for index, (_, _, title) in enumerate(COLUMNS):
        x = x0 + index * (cell_w + gap)
        _draw_label(draw, (x + 8, y_header), title, font_header)

    for row_index, case in enumerate(selected):
        y = margin + header_h + row_index * row_h
        draw.rectangle(
            (margin, y - 6, width - margin, y + cell_h + 14),
            outline=(205, 205, 198),
            width=1,
        )
        for line_index, line in enumerate(_row_label(case)):
            font = font_label if line_index == 0 else font_detail
            _draw_label(draw, (margin + 10, y + 20 + line_index * 29), line, font)

        for col_index, (condition, label, _) in enumerate(COLUMNS):
            x = x0 + col_index * (cell_w + gap)
            still_path = _still_path(str(case["path_key"]), CONDITION_ALIASES[condition], label)
            still, recolored = _load_still(still_path, (cell_w, cell_h))
            recolor_counts.append(
                {
                    "path": str(still_path.relative_to(ROOT)),
                    "source_red_overlay_pixels_recolored": recolored,
                }
            )
            canvas.paste(still, (x, y))
            draw.rectangle((x, y, x + cell_w, y + cell_h), outline=(180, 180, 180), width=1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT)
    column_report = build_column_panel(cases[COLUMN_CASE_KEY])
    return {
        "path": str(OUT.relative_to(ROOT)),
        "size_bytes": OUT.stat().st_size,
        "hash_sha256": _sha256(OUT),
        "case_keys": list(MAIN_CASE_KEYS),
        "columns": [title for _, _, title in COLUMNS],
        "layout": {
            "output_width_px": width,
            "output_height_px": height,
            "row_label_width_px": label_w,
            "frame_cell_width_px": cell_w,
            "frame_cell_height_px": cell_h,
            "row_key_font_px": MAIN_ROW_KEY_FONT_PX,
            "row_detail_font_px": MAIN_ROW_DETAIL_FONT_PX,
        },
        "overlay_legend": OVERLAY_LEGEND,
        "overlay_recolor": {
            "source_overlay_color": "red",
            "display_overlay_color": "purple",
            "counts": recolor_counts,
            "total_source_red_overlay_pixels_recolored": sum(
                record["source_red_overlay_pixels_recolored"] for record in recolor_counts
            ),
        },
        "column_panel": column_report,
    }


def build_column_panel(case: dict[str, Any]) -> dict[str, Any]:
    cell_w, cell_h = 500, 250
    gap = 18
    header_h = 98
    row_label_h = 28
    row_gap = 16
    row_h = row_label_h + cell_h + row_gap
    margin = 16
    width = margin * 2 + 2 * cell_w + gap
    height = margin * 2 + header_h + 2 * row_h

    canvas = Image.new("RGB", (width, height), (248, 248, 245))
    draw = ImageDraw.Draw(canvas)
    font_title = _font(24, bold=True)
    font_header = _font(19, bold=True)
    font_label = _font(18, bold=True)
    font_small = _font(14)

    path_key = str(case["path_key"])
    scene_id = str(case.get("scene_id", "")).replace("kujiale_", "KJ ")
    case_type = str(case.get("case_type", "")).replace("_", " ")
    original_sr = case.get("metrics", {}).get("original", {}).get("SR")
    nomdl_sr = case.get("metrics", {}).get("modified", {}).get("SR")

    _draw_label(
        draw,
        (margin, margin),
        "Representative official InternNav rollout",
        font_title,
    )
    _draw_label(
        draw,
        (margin, margin + 31),
        f"{scene_id} / path {path_key} / {case_type}; SR original/noMDL {original_sr:g}/{nomdl_sr:g}",
        font_small,
        fill=(70, 70, 70),
    )
    _draw_overlay_legend(draw, (margin, margin + 55), font_small)
    recolor_counts: list[dict[str, Any]] = []

    x0 = margin
    y_header = margin + header_h - 27
    for col_index, title in enumerate(("Start", "End")):
        x = x0 + col_index * (cell_w + gap)
        _draw_label(draw, (x + 8, y_header), title, font_header)

    for row_index, (condition, row_title) in enumerate(
        (("original", "Original"), ("nomdl", "noMDL"))
    ):
        y = margin + header_h + row_index * row_h
        draw.rectangle(
            (margin, y - 4, width - margin, y + row_label_h + cell_h + 4),
            outline=(205, 205, 198),
            width=1,
        )
        _draw_label(draw, (margin + 8, y + 4), row_title, font_label)
        for col_index, label in enumerate(("start", "end")):
            x = x0 + col_index * (cell_w + gap)
            image_y = y + row_label_h
            still_path = _still_path(path_key, CONDITION_ALIASES[condition], label)
            still, recolored = _load_still(still_path, (cell_w, cell_h))
            recolor_counts.append(
                {
                    "path": str(still_path.relative_to(ROOT)),
                    "source_red_overlay_pixels_recolored": recolored,
                }
            )
            canvas.paste(still, (x, image_y))
            draw.rectangle(
                (x, image_y, x + cell_w, image_y + cell_h),
                outline=(180, 180, 180),
                width=1,
            )

    OUT_COLUMN.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT_COLUMN)
    return {
        "path": str(OUT_COLUMN.relative_to(ROOT)),
        "size_bytes": OUT_COLUMN.stat().st_size,
        "hash_sha256": _sha256(OUT_COLUMN),
        "case_key": COLUMN_CASE_KEY,
        "overlay_legend": OVERLAY_LEGEND,
        "overlay_recolor": {
            "source_overlay_color": "red",
            "display_overlay_color": "purple",
            "counts": recolor_counts,
            "total_source_red_overlay_pixels_recolored": sum(
                record["source_red_overlay_pixels_recolored"] for record in recolor_counts
            ),
        },
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
