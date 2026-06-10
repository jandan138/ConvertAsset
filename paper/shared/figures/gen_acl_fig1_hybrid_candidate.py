#!/usr/bin/env python3
"""Build preview-only ACL Figure 1 hybrid candidates.

This script creates a candidate bitmap for visual comparison only. It does not
update the active LaTeX source. Real project render artifacts are used for the
evidence-like visual anchors; schematic arrows, labels, and stage framing are
drawn deterministically.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = ROOT / "paper/shared/figures"
RAW_DIR = ROOT / "paper/shared/evidence/raw"
CANDIDATE_DIR = FIG_DIR / "candidates"
OUT = CANDIDATE_DIR / "fig_acl_method_chain_hybrid_real_v1.png"
OUT_PDF = CANDIDATE_DIR / "fig_acl_method_chain_hybrid_real_v1.pdf"
OUT_META = CANDIDATE_DIR / "fig_acl_method_chain_hybrid_real_v1.meta.json"

WIDTH = 1800
HEIGHT = 900
MARGIN = 34
GAP = 24
CARD_W = (WIDTH - 2 * MARGIN - 3 * GAP) // 4
CARD_H = HEIGHT - 2 * MARGIN

COLORS = {
    "blue": (18, 75, 170),
    "green": (20, 130, 42),
    "orange": (237, 112, 20),
    "purple": (110, 55, 190),
    "ink": (26, 26, 26),
    "muted": (78, 78, 78),
    "line": (216, 216, 216),
    "panel": (252, 252, 250),
    "soft": (247, 247, 244),
}

OBJECT_ORIG = RAW_DIR / "renders/chestofdrawers_0011/A_top_front_right.png"
OBJECT_NOMDL = RAW_DIR / "renders/chestofdrawers_0011/B_top_front_right.png"
SCENE_ORIG = FIG_DIR / "out_tmp/mdl_images/orbit_mdl_01.png"
SCENE_NOMDL = FIG_DIR / "out_tmp/nomdl_images/orbit_01.png"
STILL_ROOT = (
    RAW_DIR
    / "internnav_vln_downstream/official_selected_qualitative_videos/stills/kujiale0036_0066"
)
INTERNNAV_STILLS = [
    STILL_ROOT / "kujiale0036_0066_597_597_original_start_000000.png",
    STILL_ROOT / "kujiale0036_0066_597_597_original_end_000113.png",
    STILL_ROOT / "kujiale0036_0066_597_597_nomdl_start_000000.png",
    STILL_ROOT / "kujiale0036_0066_597_597_nomdl_end_000101.png",
]


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for root in (Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/dejavu")):
        path = root / name
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _load_fit(
    path: Path,
    size: tuple[int, int],
    *,
    crop: tuple[int, int, int, int] | None = None,
    cover: bool = False,
    fill: tuple[int, int, int] = (246, 246, 244),
) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if crop is not None:
        image = image.crop(crop)
    if cover:
        return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, fill)
    canvas.paste(contained, ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2))
    return canvas


def _text_center(draw: ImageDraw.ImageDraw, box, text: str, font, fill) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    x = box[0] + (box[2] - box[0] - (bbox[2] - bbox[0])) / 2
    y = box[1] + (box[3] - box[1] - (bbox[3] - bbox[1])) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _arrow(draw: ImageDraw.ImageDraw, start, end, color, width: int = 8) -> None:
    draw.line((start, end), fill=color, width=width)
    x0, y0 = start
    x1, y1 = end
    if abs(x1 - x0) >= abs(y1 - y0):
        sign = 1 if x1 >= x0 else -1
        pts = [(x1, y1), (x1 - sign * 24, y1 - 15), (x1 - sign * 24, y1 + 15)]
    else:
        sign = 1 if y1 >= y0 else -1
        pts = [(x1, y1), (x1 - 15, y1 - sign * 24), (x1 + 15, y1 - sign * 24)]
    draw.polygon(pts, fill=color)


def _stage_frame(draw: ImageDraw.ImageDraw, x: int, index: int, title: str, color) -> None:
    y = MARGIN
    draw.rounded_rectangle(
        (x, y, x + CARD_W, y + CARD_H),
        radius=16,
        fill=(255, 255, 255),
        outline=color,
        width=4,
    )
    badge = (x + 22, y + 20, x + 86, y + 84)
    draw.ellipse(badge, fill=color)
    _text_center(draw, badge, str(index), _font(38, bold=True), (255, 255, 255))
    draw.text((x + 112, y + 28), title, font=_font(36, bold=True), fill=color)


def _draw_file_icon(draw: ImageDraw.ImageDraw, box) -> None:
    x0, y0, x1, y1 = box
    fold = 34
    draw.rounded_rectangle((x0, y0, x1, y1), radius=10, outline=(20, 20, 20), width=6, fill=(255, 255, 255))
    draw.line((x1 - fold, y0, x1 - fold, y0 + fold, x1, y0 + fold), fill=(20, 20, 20), width=5)
    draw.text((x0 + 32, y0 + 92), ".usd", font=_font(32, bold=True), fill=(20, 20, 20))


def _draw_graph(draw: ImageDraw.ImageDraw, origin, scale: int = 1, color=(30, 30, 30)) -> None:
    x, y = origin
    boxes = [(x + 70, y), (x + 20, y + 92), (x + 120, y + 92), (x - 10, y + 184), (x + 60, y + 184), (x + 150, y + 184)]
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)]
    for a, b in edges:
        ax, ay = boxes[a]
        bx, by = boxes[b]
        draw.line((ax + 15, ay + 15, bx + 15, by + 15), fill=color, width=3 * scale)
    for bx, by in boxes:
        draw.rectangle((bx, by, bx + 30, by + 30), outline=color, width=3 * scale, fill=(255, 255, 255))


def _draw_molecule_icon(draw: ImageDraw.ImageDraw, center, color=(30, 30, 30)) -> None:
    x, y = center
    nodes = [(x, y), (x + 34, y - 26), (x + 48, y + 22), (x + 78, y - 6)]
    for a, b in ((0, 1), (0, 2), (2, 3)):
        draw.line((nodes[a], nodes[b]), fill=color, width=3)
    for nx, ny in nodes:
        draw.ellipse((nx - 7, ny - 7, nx + 7, ny + 7), fill=color)


def _draw_sphere(draw: ImageDraw.ImageDraw, center, radius: int, fill, outline=(130, 130, 130)) -> None:
    x, y = center
    box = (x - radius, y - radius, x + radius, y + radius)
    draw.ellipse(box, fill=fill, outline=outline, width=2)
    draw.ellipse((x - radius // 2, y - radius // 2, x - radius // 8, y - radius // 8), fill=(255, 255, 255))
    draw.ellipse((x - radius, y + radius - 8, x + radius, y + radius + 8), fill=(210, 210, 205), outline=(170, 170, 165))


def _draw_stage1(canvas: Image.Image, draw: ImageDraw.ImageDraw, x: int) -> None:
    _draw_file_icon(draw, (x + 38, 148, x + 162, 292))
    _draw_graph(draw, (x + 228, 152))
    crop = (250, 80, 730, 650)
    thumb = _load_fit(OBJECT_ORIG, (168, 160), crop=crop, cover=True)
    scene = _load_fit(SCENE_ORIG, (168, 160), cover=True)
    canvas.paste(thumb, (x + 36, 340))
    canvas.paste(scene, (x + 220, 340))
    for bx in (x + 36, x + 220):
        draw.rectangle((bx, 340, bx + 168, 500), outline=(170, 170, 170), width=1)
    sphere_colors = [(120, 74, 28), (35, 35, 35), (232, 228, 214), (55, 48, 42)]
    for idx, color in enumerate(sphere_colors):
        _draw_sphere(draw, (x + 76 + idx * 86, 650), 36, color)


def _draw_stage2(canvas: Image.Image, draw: ImageDraw.ImageDraw, x: int) -> None:
    rows = [
        ((126, 70, 28), (198, 198, 198)),
        ((40, 40, 40), (210, 210, 210)),
        ((232, 228, 214), (218, 218, 218)),
        ((52, 45, 40), (206, 206, 206)),
    ]
    for idx, (src, dst) in enumerate(rows):
        cy = 172 + idx * 92
        _draw_sphere(draw, (x + 78, cy), 28, src)
        _arrow(draw, (x + 126, cy), (x + 226, cy), COLORS["green"], width=6)
        _draw_sphere(draw, (x + 284, cy), 28, dst)
        _draw_molecule_icon(draw, (x + 344, cy - 4), color=(30, 30, 30))
    for ix, label in enumerate(("Refs", "Variants")):
        bx = x + 36 + ix * 190
        by = 580
        draw.rounded_rectangle((bx, by, bx + 168, by + 190), radius=10, outline=COLORS["green"], width=3, fill=(250, 253, 250))
        draw.text((bx + 22, by + 18), label, font=_font(22, bold=True), fill=COLORS["green"])
        if ix == 0:
            for j in range(3):
                draw.rectangle((bx + 28, by + 65 + j * 38, bx + 54, by + 91 + j * 38), outline=(30, 30, 30), width=2)
                _arrow(draw, (bx + 70, by + 78 + j * 38), (bx + 128, by + 78 + j * 38), COLORS["green"], width=4)
                draw.rectangle((bx + 132, by + 65 + j * 38, bx + 154, by + 91 + j * 38), outline=(30, 30, 30), width=2)
        else:
            nodes = [
                (bx + 72, by + 72),
                (bx + 110, by + 106),
                (bx + 78, by + 146),
                (bx + 134, by + 150),
            ]
            for a, b in ((0, 1), (1, 2), (1, 3)):
                ax, ay = nodes[a]
                bx2, by2 = nodes[b]
                draw.line((ax + 12, ay + 12, bx2 + 12, by2 + 12), fill=(35, 35, 35), width=3)
            for nx, ny in nodes:
                draw.rectangle((nx, ny, nx + 24, ny + 24), outline=(35, 35, 35), width=3, fill=(255, 255, 255))
            draw.ellipse((bx + 112, by + 122, bx + 158, by + 168), outline=COLORS["green"], width=6)
            draw.line((bx + 124, by + 145, bx + 136, by + 158, bx + 152, by + 130), fill=COLORS["green"], width=5)


def _draw_stage3(canvas: Image.Image, draw: ImageDraw.ImageDraw, x: int) -> None:
    img_w, img_h = 170, 180
    orig = _load_fit(SCENE_ORIG, (img_w, img_h), cover=True)
    conv = _load_fit(SCENE_NOMDL, (img_w, img_h), cover=True)
    canvas.paste(orig, (x + 34, 168))
    canvas.paste(conv, (x + 226, 168))
    for bx, label in ((x + 34, "Original"), (x + 226, "Converted")):
        draw.rectangle((bx, 168, bx + img_w, 168 + img_h), outline=(170, 170, 170), width=1)
        _text_center(draw, (bx, 360, bx + img_w, 396), label, _font(20, bold=True), COLORS["ink"])
    _arrow(draw, (x + 207, 258), (x + 222, 258), COLORS["orange"], width=5)
    draw.rounded_rectangle((x + 42, 455, x + 392, 555), radius=12, outline=COLORS["orange"], width=4, fill=(255, 253, 248))
    draw.text((x + 86, 488), "Target: box", font=_font(32, bold=True), fill=COLORS["ink"])
    draw.rectangle((x + 300, 482, x + 350, 532), fill=(173, 120, 62), outline=(120, 82, 40), width=2)
    draw.line((x + 300, 482, x + 326, 464, x + 376, 464, x + 350, 482), fill=(143, 96, 48), width=2)
    draw.line((x + 350, 482, x + 376, 464, x + 376, 514, x + 350, 532), fill=(143, 96, 48), width=2)
    bot_y = 628
    draw.rounded_rectangle((x + 50, bot_y, x + 116, bot_y + 70), radius=10, outline=(40, 40, 40), width=5)
    draw.ellipse((x + 74, bot_y - 28, x + 92, bot_y - 10), outline=(40, 40, 40), width=5)
    draw.line((x + 83, bot_y - 10, x + 83, bot_y), fill=(40, 40, 40), width=5)
    draw.text((x + 154, bot_y + 2), "?", font=_font(56, bold=True), fill=(45, 45, 45))
    _arrow(draw, (x + 230, bot_y + 36), (x + 304, bot_y + 36), COLORS["ink"], width=6)
    draw.rounded_rectangle((x + 326, bot_y - 12, x + 392, bot_y + 84), radius=8, fill=(78, 42, 16))
    draw.ellipse((x + 344, bot_y + 4, x + 374, bot_y + 34), outline=COLORS["orange"], width=5)
    draw.line((x + 359, bot_y - 4, x + 359, bot_y + 44), fill=COLORS["orange"], width=4)
    draw.line((x + 336, bot_y + 19, x + 382, bot_y + 19), fill=COLORS["orange"], width=4)


def _draw_stage4(canvas: Image.Image, draw: ImageDraw.ImageDraw, x: int) -> None:
    cell_w, cell_h = 172, 120
    positions = [(x + 34, 164), (x + 226, 164), (x + 34, 308), (x + 226, 308)]
    labels = ["O start", "O end", "N start", "N end"]
    for path, pos, label in zip(INTERNNAV_STILLS, positions, labels):
        image = _load_fit(path, (cell_w, cell_h), cover=True)
        canvas.paste(image, pos)
        draw.rectangle((pos[0], pos[1], pos[0] + cell_w, pos[1] + cell_h), outline=(170, 170, 170), width=1)
        draw.text((pos[0] + 8, pos[1] + cell_h + 5), label, font=_font(15, bold=True), fill=COLORS["ink"])
    draw.rounded_rectangle((x + 36, 504, x + 392, 634), radius=12, outline=COLORS["purple"], width=3, fill=(251, 248, 255))
    _arrow(draw, (x + 78, 602), (x + 334, 532), COLORS["purple"], width=8)
    draw.line((x + 72, 585, x + 134, 565, x + 198, 560, x + 292, 530, x + 336, 520), fill=COLORS["green"], width=6)
    draw.ellipse((x + 62, 576, x + 88, 602), fill=(255, 255, 255), outline=COLORS["green"], width=5)
    draw.text((x + 318, 500), "*", font=_font(62, bold=True), fill=COLORS["green"])
    for idx, label in enumerate(("SR", "SPL", "NE")):
        bx = x + 36 + idx * 124
        by = 698
        draw.rounded_rectangle((bx, by, bx + 100, by + 84), radius=10, outline=COLORS["purple"], width=3, fill=(255, 255, 255))
        _text_center(draw, (bx, by, bx + 100, by + 84), label, _font(32, bold=True), COLORS["purple"])


def build() -> dict:
    for path in [OBJECT_ORIG, OBJECT_NOMDL, SCENE_ORIG, SCENE_NOMDL, *INTERNNAV_STILLS]:
        if not path.exists():
            raise FileNotFoundError(path)

    canvas = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    xs = [MARGIN + i * (CARD_W + GAP) for i in range(4)]
    stages = [
        (1, "USD / MDL", COLORS["blue"], _draw_stage1),
        (2, "noMDL", COLORS["green"], _draw_stage2),
        (3, "VLM Checks", COLORS["orange"], _draw_stage3),
        (4, "InternNav", COLORS["purple"], _draw_stage4),
    ]
    for x, (index, title, color, body_fn) in zip(xs, stages):
        _stage_frame(draw, x, index, title, color)
        body_fn(canvas, draw, x)
    for i, color in enumerate((COLORS["blue"], COLORS["green"], COLORS["orange"])):
        _arrow(draw, (xs[i] + CARD_W - 4, HEIGHT // 2), (xs[i + 1] + 4, HEIGHT // 2), color, width=10)

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT)
    canvas.save(OUT_PDF, "PDF", resolution=300.0)
    meta = {
        "status": "preview_only_acl_fig1_hybrid_candidate",
        "output": str(OUT.relative_to(ROOT)),
        "output_pdf": str(OUT_PDF.relative_to(ROOT)),
        "mode": "hybrid_real_render_anchors",
        "claim_boundary": "Candidate only; not wired into the ACL paper. Real render thumbnails are recorded project artifacts, but the assembled figure remains an overview roadmap.",
        "source_assets": [str(p.relative_to(ROOT)) for p in [OBJECT_ORIG, OBJECT_NOMDL, SCENE_ORIG, SCENE_NOMDL, *INTERNNAV_STILLS]],
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


if __name__ == "__main__":
    report = build()
    print(report["output"])
    print(report["output_pdf"])
