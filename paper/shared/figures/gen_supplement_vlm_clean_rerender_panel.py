#!/usr/bin/env python3
"""Build a clean VLM target-view render panel for the ACL supplement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont, ImageOps


FIG_DIR = Path(__file__).resolve().parent
ROOT = FIG_DIR.parents[2]
RAW = ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
OUT = FIG_DIR / "fig_supplement_vlm_clean_rerender_panel.png"

REPORTS = [
    RAW / "retake_zoom_paired_render_reports/47aa36277a54f6ca90cc.zoom_018.clean_rerender_20260528.json",
    RAW / "retake_zoom_paired_render_reports/f35ef3d86c42446b7ddf.zoom_018.clean_rerender_20260528.json",
    RAW / "retake_zoom_paired_render_reports/c27086f557d316584264.zoom_018.clean_rerender_20260528.json",
    RAW / "retake_zoom_paired_render_reports/e2ec085d524d5df4455d.zoom_020.clean_rerender_20260528.json",
]
PROJECTION_QA = RAW / "retake_zoom_expanded30_target_projection_qa_report.json"

WIDTH = 1600
MARGIN = 34
GAP_X = 16
GAP_Y = 26
BLOCK_GAP_X = 28
HEADER_H = 82
TITLE_H = 30
COLUMN_H = 24
STATUS_H = 34
BLOCK_COLUMNS = 2
BOX_COLOR = (0, 155, 115)
TEXT = (22, 22, 22)
MUTED = (80, 80, 80)


class RenderEntry(NamedTuple):
    pair_id: str
    target_category: str
    image_path: Path
    image_hash: str
    bbox_xyxy: list[float]
    condition: str
    mdl_error_signal: int


class CleanPair(NamedTuple):
    pair_id: str
    target_category: str
    source_scene_id: str
    view_id: str
    original: RenderEntry
    converted: RenderEntry


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_projection_index() -> dict[str, dict]:
    data = json.loads(PROJECTION_QA.read_text(encoding="utf-8"))
    return {pair["pair_id"]: pair for pair in data["pairs"]}


def _record_by_condition(report: dict) -> dict[str, dict]:
    return {record["material_condition"]: record for record in report["records"]}


def _load_entry(report: dict, projection: dict, condition: str) -> RenderEntry:
    record = _record_by_condition(report)[condition]
    image_info = record["image"]
    path = Path(image_info["path"])
    expected_hash = image_info["hash_sha256"]
    actual_hash = _sha256(path)
    if actual_hash != expected_hash:
        raise ValueError(f"Image hash mismatch for {report['pair_id']} {condition}: {path}")
    return RenderEntry(
        pair_id=report["pair_id"],
        target_category=report["target_category"],
        image_path=path,
        image_hash=actual_hash,
        bbox_xyxy=[float(v) for v in projection["projection"]["bbox_xyxy"]],
        condition=condition,
        mdl_error_signal=int(report["summary"][f"{condition}_mdl_error_signal"]),
    )


def load_pairs() -> list[CleanPair]:
    projections = _load_projection_index()
    pairs: list[CleanPair] = []
    for path in REPORTS:
        report = json.loads(path.read_text(encoding="utf-8"))
        summary = report["summary"]
        if not summary["both_commands_exit_zero"] or not summary["both_images_exist"]:
            raise ValueError(f"Clean rerender did not pass smoke gate: {path}")
        if summary["original_mdl_error_signal"] != 0 or summary["converted_mdl_error_signal"] != 0:
            raise ValueError(f"Clean rerender still has MDL error signal: {path}")
        projection = projections[report["pair_id"]]
        if projection["status"] != "projection_ok":
            raise ValueError(f"Projection is not usable for {report['pair_id']}")
        pairs.append(
            CleanPair(
                pair_id=report["pair_id"],
                target_category=report["target_category"],
                source_scene_id=report["source_scene_id"],
                view_id=report["view_id"],
                original=_load_entry(report, projection, "original"),
                converted=_load_entry(report, projection, "converted"),
            )
        )
    return pairs


def _fit_image(path: Path, size: tuple[int, int]) -> tuple[Image.Image, float, int, int]:
    image = Image.open(path).convert("RGB")
    scale = min(size[0] / image.width, size[1] / image.height)
    new_w = max(1, round(image.width * scale))
    new_h = max(1, round(image.height * scale))
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (250, 250, 250))
    x0 = (size[0] - new_w) // 2
    y0 = (size[1] - new_h) // 2
    canvas.paste(resized, (x0, y0))
    return canvas, scale, x0, y0


def _target_crop(entry: RenderEntry, size: tuple[int, int], padding: int = 110) -> Image.Image:
    image = Image.open(entry.image_path).convert("RGB")
    x1, y1, x2, y2 = entry.bbox_xyxy
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    crop_w = max(x2 - x1 + 2 * padding, image.width * 0.28)
    crop_h = max(y2 - y1 + 2 * padding, image.height * 0.28)
    target_aspect = size[0] / size[1]
    if crop_w / crop_h < target_aspect:
        crop_w = crop_h * target_aspect
    else:
        crop_h = crop_w / target_aspect
    left = max(0, min(image.width - crop_w, cx - crop_w / 2))
    top = max(0, min(image.height - crop_h, cy - crop_h / 2))
    crop = image.crop((round(left), round(top), round(left + crop_w), round(top + crop_h)))
    out = ImageOps.fit(crop, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    draw = ImageDraw.Draw(out)
    sx = size[0] / crop_w
    sy = size[1] / crop_h
    draw.rectangle(
        (
            (x1 - left) * sx,
            (y1 - top) * sy,
            (x2 - left) * sx,
            (y2 - top) * sy,
        ),
        outline=BOX_COLOR,
        width=3,
    )
    return out


def _draw_target_box(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    scale: float,
    ox: int,
    oy: int,
    bbox_xyxy: list[float],
) -> None:
    x1, y1, x2, y2 = bbox_xyxy
    draw.rectangle(
        (x + ox + x1 * scale, y + oy + y1 * scale, x + ox + x2 * scale, y + oy + y2 * scale),
        outline=BOX_COLOR,
        width=4,
    )


def _draw_entry(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    entry: RenderEntry,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    image, scale, ox, oy = _fit_image(entry.image_path, (w, h))
    canvas.paste(image, (x, y))
    _draw_target_box(draw, x=x, y=y, scale=scale, ox=ox, oy=oy, bbox_xyxy=entry.bbox_xyxy)
    draw.rectangle((x, y, x + w, y + h), outline=(150, 150, 150), width=2)


def _draw_pair(canvas: Image.Image, draw: ImageDraw.ImageDraw, pair: CleanPair, index: int) -> None:
    block_w = (WIDTH - 2 * MARGIN - BLOCK_GAP_X) // BLOCK_COLUMNS
    image_w = (block_w - GAP_X) // 2
    image_h = round(image_w * 0.72)
    block_h = TITLE_H + COLUMN_H + image_h + STATUS_H
    row = index // BLOCK_COLUMNS
    col = index % BLOCK_COLUMNS
    x = MARGIN + col * (block_w + BLOCK_GAP_X)
    y = MARGIN + HEADER_H + row * (block_h + GAP_Y)

    title_font = _font(21, bold=True)
    label_font = _font(15, bold=True)
    note_font = _font(13)
    draw.rounded_rectangle((x - 12, y - 10, x + block_w + 12, y + block_h - 4), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((x, y), f"{pair.target_category} | {pair.view_id} | MDL errors 0/0", fill=TEXT, font=title_font)
    y += TITLE_H
    draw.rectangle((x, y - 2, x + image_w, y + COLUMN_H - 2), fill=(236, 236, 236), outline=(150, 150, 150), width=1)
    draw.rectangle((x + image_w + GAP_X, y - 2, x + image_w * 2 + GAP_X, y + COLUMN_H - 2), fill=(236, 236, 236), outline=(150, 150, 150), width=1)
    draw.text((x + 6, y + 2), "Original MDL", fill=MUTED, font=label_font)
    draw.text((x + image_w + GAP_X + 6, y + 2), "Converted noMDL", fill=MUTED, font=label_font)
    y += COLUMN_H
    _draw_entry(canvas, draw, pair.original, x=x, y=y, w=image_w, h=image_h)
    _draw_entry(canvas, draw, pair.converted, x=x + image_w + GAP_X, y=y, w=image_w, h=image_h)
    y += image_h + 8
    draw.text((x, y), "green box: target projection", fill=MUTED, font=note_font)


def _draw_closeup_strip(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    pairs: list[CleanPair],
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(24, bold=True)
    note_font = _font(15)
    label_font = _font(12, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((x + 18, y + 14), "target close-up strip", fill=TEXT, font=title_font)
    draw.text((x + 18, y + 44), "bbox-centered crops reuse the same clean rerenders; no VLM point overlay is added", fill=MUTED, font=note_font)
    entries: list[tuple[str, RenderEntry]] = []
    for pair in pairs:
        entries.append((f"{pair.target_category} MDL", pair.original))
        entries.append((f"{pair.target_category} noMDL", pair.converted))
    tile_gap = 10
    tile_w = (w - 36 - tile_gap * (len(entries) - 1)) // len(entries)
    tile_h = h - 104
    tile_y = y + 76
    for idx, (label, entry) in enumerate(entries):
        tile_x = x + 18 + idx * (tile_w + tile_gap)
        crop = _target_crop(entry, (tile_w, tile_h))
        canvas.paste(crop, (tile_x, tile_y))
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + tile_h), outline=(140, 140, 140), width=2)
        draw.rectangle((tile_x, tile_y, tile_x + tile_w, tile_y + 24), fill=(236, 236, 236), outline=(140, 140, 140), width=1)
        draw.text((tile_x + 5, tile_y + 5), label, fill=TEXT, font=label_font)


def _draw_report_gates(
    draw: ImageDraw.ImageDraw,
    pairs: list[CleanPair],
    *,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    title_font = _font(24, bold=True)
    note_font = _font(15)
    body_font = _font(14)
    small_font = _font(12, bold=True)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=(252, 252, 252), outline=(174, 174, 174), width=2)
    draw.text((x + 18, y + 14), "clean-rerender report checks", fill=TEXT, font=title_font)
    draw.text((x + 18, y + 44), "each row keeps render quality, target projection, and result scope separate", fill=MUTED, font=note_font)
    row_y = y + 78
    row_h = 52
    for idx, pair in enumerate(pairs):
        yy = row_y + idx * (row_h + 10)
        fill = (246, 250, 255) if idx % 2 == 0 else (250, 250, 250)
        draw.rounded_rectangle((x + 18, yy, x + w - 18, yy + row_h), radius=6, fill=fill, outline=(186, 186, 186), width=1)
        draw.text((x + 34, yy + 10), pair.target_category, fill=TEXT, font=_font(17, bold=True))
        draw.text((x + 210, yy + 9), pair.view_id, fill=MUTED, font=body_font)
        draw.text((x + 370, yy + 9), "original exit 0 | noMDL exit 0", fill=(34, 96, 63), font=body_font)
        draw.text((x + 730, yy + 9), "MDL/KooPbr errors 0/0", fill=(34, 96, 63), font=body_font)
        draw.text((x + 1070, yy + 9), "target bbox only", fill=(38, 95, 156), font=body_font)
        draw.rounded_rectangle((x + w - 158, yy + 12, x + w - 36, yy + 40), radius=4, fill=(238, 247, 241), outline=(34, 130, 78), width=1)
        draw.text((x + w - 130, yy + 18), "PASS", fill=(34, 96, 63), font=small_font)
    draw.text(
        (x + 18, y + h - 34),
        "Reading rule: this panel supports the tabulated grounding evidence with clean target-view renders.",
        fill=MUTED,
        font=note_font,
    )


def render_panel(pairs: list[CleanPair], out: Path = OUT) -> None:
    block_w = (WIDTH - 2 * MARGIN - BLOCK_GAP_X) // BLOCK_COLUMNS
    image_w = (block_w - GAP_X) // 2
    image_h = round(image_w * 0.72)
    block_h = TITLE_H + COLUMN_H + image_h + STATUS_H
    rows = (len(pairs) + BLOCK_COLUMNS - 1) // BLOCK_COLUMNS
    closeup_h = 390
    report_h = 346
    height = MARGIN * 2 + HEADER_H + rows * block_h + (rows - 1) * GAP_Y + GAP_Y + closeup_h + GAP_Y + report_h
    canvas = Image.new("RGB", (WIDTH, height), (246, 246, 246))
    draw = ImageDraw.Draw(canvas)
    draw.text((MARGIN, MARGIN), "Post-repair GRScenes target-view renders", fill=TEXT, font=_font(32, bold=True))
    draw.text(
        (MARGIN, MARGIN + 46),
        "Clean rerender smoke reports show zero KooPbr/MDL error signal; this panel shows target boxes only, not VLM point overlays.",
        fill=MUTED,
        font=_font(18),
    )
    for index, pair in enumerate(pairs):
        _draw_pair(canvas, draw, pair, index)
    y = MARGIN + HEADER_H + rows * block_h + (rows - 1) * GAP_Y + GAP_Y
    _draw_closeup_strip(canvas, draw, pairs, x=MARGIN, y=y, w=WIDTH - 2 * MARGIN, h=closeup_h)
    y += closeup_h + GAP_Y
    _draw_report_gates(draw, pairs, x=MARGIN, y=y, w=WIDTH - 2 * MARGIN, h=report_h)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas = ImageOps.expand(canvas, border=1, fill=(220, 220, 220))
    canvas.save(out)


def main() -> None:
    pairs = load_pairs()
    render_panel(pairs)
    print(OUT)


if __name__ == "__main__":
    main()
