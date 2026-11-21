#!/usr/bin/env python3
"""Render the locked fig1-0922 layout to PNG (PIL), SVG, and PPTX.

Native layer (frames, bands, swatches, text) is drawn at 3x supersample and
Lanczos-downscaled; raster slots are then pasted 1:1 at their locked source
coordinates. Text size is calibrated per element so the rendered ink width
matches the measured source ink box; ink top-left is pinned exactly.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import layout as L

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
SS = 3  # supersample factor for the native layer

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf"

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(bold: bool, size3: int) -> ImageFont.FreeTypeFont:
    key = (FONT_BOLD if bold else FONT_REG, size3)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(key[0], size3)
    return _font_cache[key]


def ink_bbox(img: Image.Image, thresh: int = 690) -> tuple[int, int, int, int] | None:
    import numpy as np
    a = np.asarray(img.convert("RGB")).astype(int).sum(axis=2)
    ys, xs = (a < thresh).nonzero()
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _mask_fn(color: str):
    import numpy as np

    def m(a):  # a: HxWx3 int array
        R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        s = R + G + B
        if color == L.NAVY:
            return (s < 330) & (B >= R)
        if color == L.SUB:
            return (s < 520) & (B > R + 15) & (R > 40)
        if color == L.BLUE:
            return (B > 170) & (R < 130) & (G < 170)
        if color == L.ORANGE:
            return (R > 180) & (G < 140) & (B < 90)
        if color == L.TEAL:
            return (G > 90) & (R < 90) & (B > 80) & (s < 480)
        return s < 400

    return m


def measure_pipeline(text: str, bold: bool, size3: int, color: str):
    """Render text at 3x in `color`, downscale, measure ink box at 1x with
    the same mask used on the source. Returns (ink_box, glyph_w, glyph_h)."""
    import numpy as np
    f = font(bold, size3)
    bbox = f.getbbox(text)
    w3 = (bbox[2] - bbox[0]) + 4 * SS * 4
    h3 = (bbox[3] - bbox[1]) + 8 * SS * 4
    tile = Image.new("RGB", (max(w3, 8), max(h3, 8)), "white")
    d = ImageDraw.Draw(tile)
    px, py = 4 * SS * 2 - bbox[0], 4 * SS * 2 - bbox[1]
    d.text((px, py), text, font=f, fill=color)
    tile1 = tile.resize((tile.width // SS, tile.height // SS), Image.LANCZOS)
    a = np.asarray(tile1).astype(int)
    ys, xs = _mask_fn(color)(a).nonzero()
    if len(xs) == 0:
        return None
    ink = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return ink


def calibrate(text: str, bold: bool, target_w: int, color: str):
    """Return (size3, dx, dy): best size plus 1x ink top-left correction."""
    best, best_err, best_ink = None, 1 << 30, None
    for size3 in range(24, 165, 3):
        ink = measure_pipeline(text, bold, size3, color)
        if ink is None:
            continue
        w = ink[2] - ink[0] + 1
        err = abs(w - target_w)
        if err < best_err:
            best, best_err, best_ink = size3, err, ink
        if err <= 1:
            break
    return best, best_ink


def draw_frames(d: ImageDraw.ImageDraw) -> None:
    for (x0, y0, x1, y1), r, fill, border, bw in L.FRAMES:
        d.rounded_rectangle(
            [x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1],
            radius=r * SS,
            fill=fill,
            outline=border,
            width=max(1, round(bw * SS)),
        )


def draw_bands(base: Image.Image) -> None:
    d = ImageDraw.Draw(base)
    for (x0, y0, x1, y1), r, fill in L.BANDS:
        # rounded top corners, square bottom: draw rounded rect then square off bottom half
        d.rounded_rectangle(
            [x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1],
            radius=r * SS,
            fill=fill,
        )
        d.rectangle([x0 * SS, (y1 - r) * SS, x1 * SS - 1, y1 * SS - 1], fill=fill)


def draw_rects(d: ImageDraw.ImageDraw) -> None:
    for (x0, y0, x1, y1), fill in L.RECTS:
        d.rectangle([x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1], fill=fill)


def draw_texts(d: ImageDraw.ImageDraw, sizes: dict[str, list]) -> None:
    for key, text, ink, color, bold in L.TEXTS:
        size3, cx, cy = sizes[key]
        f = font(bold, size3)
        bbox = f.getbbox(text)
        px = (ink[0] + cx) * SS - bbox[0]
        py = (ink[1] + cy) * SS - bbox[1]
        d.text((px, py), text, font=f, fill=color)


def build_sizes() -> dict[str, list]:
    cache_path = HERE / "work" / "font_sizes.json"
    if cache_path.exists():
        return {k: list(v) for k, v in json.loads(cache_path.read_text()).items()}
    sizes: dict[str, list] = {}
    for key, text, ink, color, bold in L.TEXTS:
        target_w = ink[2] - ink[0] + 1
        size3, measured = calibrate(text, bold, target_w, color)
        if measured is None:
            sizes[key] = [60, 0, 0]
            continue
        # tile pad was 8px at 1x; correction shifts final ink onto the target
        cx, cy = 8 - measured[0], 8 - measured[1]
        sizes[key] = [size3, cx, cy]
    cache_path.write_text(json.dumps(sizes, indent=1))
    return sizes


def load_image(name: str, assets_dir: Path) -> Image.Image:
    """Real assets override the replica slots; everything else falls back."""
    cand = assets_dir / f"{name}.png"
    if cand.exists():
        return Image.open(cand).convert("RGB")
    return Image.open(ASSETS / f"{name}.png").convert("RGB")


def render_png(out_path: Path, assets_dir: Path | None = None) -> Image.Image:
    assets_dir = assets_dir or ASSETS
    W, H = L.CANVAS
    base = Image.new("RGB", (W * SS, H * SS), L.CANVAS_COLOR)
    d = ImageDraw.Draw(base)
    draw_frames(d)
    draw_bands(base)
    draw_rects(d)
    sizes = build_sizes()
    draw_texts(d, sizes)
    base = base.resize((W, H), Image.LANCZOS)
    meta = json.loads((assets_dir / "crops.json").read_text())
    for name in L.IMAGE_ORDER:
        img = load_image(name, assets_dir)
        x0, y0, _x1, _y1 = meta[name]["box"]
        base.paste(img, (x0, y0))
    base.save(out_path)
    return base


# ---------------------------------------------------------------- SVG

def svg_escape(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(out_path: Path, assets_dir: Path | None = None) -> None:
    assets_dir = assets_dir or ASSETS
    W, H = L.CANVAS
    sizes = build_sizes()
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{L.CANVAS_COLOR}"/>',
    ]
    for (x0, y0, x1, y1), r, fill, border, bw in L.FRAMES:
        parts.append(
            f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="{r}" '
            f'fill="{fill}" stroke="{border}" stroke-width="{bw}"/>'
        )
    for (x0, y0, x1, y1), r, fill in L.BANDS:
        parts.append(f'<path d="M{x0},{y1} L{x0},{y0+r} Q{x0},{y0} {x0+r},{y0} '
                     f'L{x1-r},{y0} Q{x1},{y0} {x1},{y0+r} L{x1},{y1} Z" fill="{fill}"/>')
    for (x0, y0, x1, y1), fill in L.RECTS:
        parts.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="{fill}"/>')
    for key, text, ink, color, bold in L.TEXTS:
        size3, cx, cy = sizes[key]
        f = font(bold, size3)
        bbox = f.getbbox(text)
        asc, _desc = f.getmetrics()
        x = ink[0] + cx - bbox[0] / SS
        y = ink[1] + cy - bbox[1] / SS + asc / SS
        weight = ' font-weight="bold"' if bold else ""
        parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="Liberation Sans Narrow, Arial Narrow, Helvetica, sans-serif" '
            f'font-size="{size3/SS:.2f}"{weight} fill="{color}">{svg_escape(text)}</text>'
        )
    meta = json.loads((assets_dir / "crops.json").read_text())
    for name in L.IMAGE_ORDER:
        src = assets_dir / f"{name}.png"
        if not src.exists():
            src = ASSETS / f"{name}.png"
        data = base64.b64encode(src.read_bytes()).decode()
        x0, y0, x1, y1 = meta[name]["box"]
        parts.append(
            f'<image x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" '
            f'xlink:href="data:image/png;base64,{data}"/>'
        )
    parts.append("</svg>")
    out_path.write_text("\n".join(parts))


# --------------------------------------------------------------- PPTX

EMU_PER_PX = 9525.0
# LibreOffice/PowerPoint place first-line text with an internal offset vs the
# PIL-measured ascender geometry; measured on round07 render: +4px x, +3.5px y.
PPTX_TEXT_DX = 0.0
PPTX_TEXT_DY = -1.5


def render_pptx(out_path: Path, assets_dir: Path | None = None) -> None:
    assets_dir = assets_dir or ASSETS
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.util import Emu, Pt

    W, H = L.CANVAS
    sizes = build_sizes()
    prs = Presentation()
    prs.slide_width = Emu(int(round(W * EMU_PER_PX)))
    prs.slide_height = Emu(int(round(H * EMU_PER_PX)))
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    def emu(px: float) -> Emu:
        return Emu(int(round(px * EMU_PER_PX)))

    def rgb(hexcolor: str) -> RGBColor:
        return RGBColor.from_string(hexcolor.lstrip("#").upper())

    def add_rect(box, fill, border=None, bw=1.0, radius=None, name="rect"):
        x0, y0, x1, y1 = box
        shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
        sp = slide.shapes.add_shape(shape_type, emu(x0), emu(y0), emu(x1 - x0), emu(y1 - y0))
        sp.name = name
        if radius:
            shorter = min(x1 - x0, y1 - y0)
            try:
                sp.adjustments[0] = max(0.0, min(0.5, radius / shorter))
            except Exception:
                pass
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
        if border:
            sp.line.color.rgb = rgb(border)
            sp.line.width = Pt(bw * 0.75)
        else:
            sp.line.fill.background()
        sp.shadow.inherit = False
        # strip theme style (keeps fill/line explicit, no theme effect refs)
        style = sp._element.find(
            '{http://schemas.openxmlformats.org/presentationml/2006/main}style'
        )
        if style is not None:
            sp._element.remove(style)
        return sp

    # canvas background
    add_rect([0, 0, W, H], L.CANVAS_COLOR, name="canvas")
    for i, (box, r, fill, border, bw) in enumerate(L.FRAMES):
        add_rect(box, fill, border, bw, radius=r, name=f"frame_{i:02d}")
    for i, (box, r, fill) in enumerate(L.BANDS):
        x0, y0, x1, y1 = box
        add_rect([x0, y0, x1, y1 - r], fill, radius=r, name=f"band_top_{i}")
        add_rect([x0, y1 - r, x1, y1], fill, name=f"band_bot_{i}")
    for i, (box, fill) in enumerate(L.RECTS):
        add_rect(box, fill, name=f"swatch_{i}")

    for key, text, ink, color, bold in L.TEXTS:
        size3, cx, cy = sizes[key]
        size_px = size3 / SS
        f = font(bold, size3)
        bbox = f.getbbox(text)
        # position textbox so glyph ink lands on measured ink top-left
        px = ink[0] + cx - bbox[0] / SS + PPTX_TEXT_DX
        py = ink[1] + cy - bbox[1] / SS + PPTX_TEXT_DY
        w_px = (bbox[2] - bbox[0]) / SS + 16
        h_px = size_px * 1.6
        tb = slide.shapes.add_textbox(emu(px), emu(py), emu(w_px), emu(h_px))
        tb.name = f"text_{key}"
        tf = tb.text_frame
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.TOP
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = text
        run.font.name = "Liberation Sans Narrow"
        run.font.size = Pt(size_px * 0.75)
        run.font.bold = bold
        run.font.color.rgb = rgb(color)

    meta = json.loads((assets_dir / "crops.json").read_text())
    for name in L.IMAGE_ORDER:
        src = assets_dir / f"{name}.png"
        if not src.exists():
            src = ASSETS / f"{name}.png"
        x0, y0, x1, y1 = meta[name]["box"]
        pic = slide.shapes.add_picture(
            str(src), emu(x0), emu(y0), emu(x1 - x0), emu(y1 - y0)
        )
        pic.name = f"img_{name}"
    prs.save(out_path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="rounds/round01/fig1.png")
    ap.add_argument("--svg", default=None)
    ap.add_argument("--pptx", default=None)
    ap.add_argument("--assets-dir", default=None,
                    help="override asset dir (e.g. assets/real); missing slots fall back to assets/")
    args = ap.parse_args()
    assets_dir = Path(args.assets_dir) if args.assets_dir else None
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    render_png(out, assets_dir)
    print("png ->", out)
    if args.svg:
        render_svg(Path(args.svg), assets_dir)
        print("svg ->", args.svg)
    if args.pptx:
        render_pptx(Path(args.pptx), assets_dir)
        print("pptx ->", args.pptx)


if __name__ == "__main__":
    main()
