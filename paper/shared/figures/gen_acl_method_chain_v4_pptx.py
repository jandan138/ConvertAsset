#!/usr/bin/env python3
"""Generate the editable, image-led ACL Figure 1 v4.

The PPTX is the editable layout master. LibreOffice exports the paper PDF and
Poppler rasterizes that PDF for page-scale QA. A self-contained SVG mirror is
generated from the same geometry. Existing experiment artifacts are read-only.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Literal
import zipfile

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

import gen_acl_main_figures_v2 as base
import gen_acl_paper_figures_v3 as v3


ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = ROOT / "paper/shared/figures"
SPEC_PATH = FIG_DIR / "specs/fig_acl_method_chain_v4.spec.json"
STEM = FIG_DIR / "fig_acl_method_chain_v4"

SLIDE_W = 7.2
SLIDE_H = 3.3
SVG_UNITS_PER_INCH = 100.0
FONT_NAME = "Liberation Sans"
FONT_REGULAR = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
FONT_BOLD = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
MIN_FONT_PT = 6.0

COLORS = {
    "ink": "202A38",
    "muted": "667085",
    "line": "CBD5E1",
    "soft": "F5F7FA",
    "original": "0F4D92",
    "converted": "E67E22",
    "nvidia": "6B7280",
    "white": "FFFFFF",
}


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h


@dataclass(frozen=True)
class TextItem:
    name: str
    box: Box
    text: str
    size: float
    color: str = COLORS["ink"]
    bold: bool = False
    align: Literal["left", "center", "right"] = "left"
    valign: Literal["top", "middle", "bottom"] = "middle"
    margin: float = 0.015


@dataclass(frozen=True)
class ImageItem:
    name: str
    box: Box
    path: Path
    border: str | None = None
    border_pt: float = 0.65


@dataclass(frozen=True)
class RectItem:
    name: str
    box: Box
    fill: str


@dataclass(frozen=True)
class ArrowItem:
    name: str
    start: tuple[float, float]
    end: tuple[float, float]
    color: str = COLORS["original"]
    width_pt: float = 0.9
    head: Literal["none", "right", "down"] = "none"


@dataclass
class Layout:
    texts: list[TextItem]
    images: list[ImageItem]
    rects: list[RectItem]
    arrows: list[ArrowItem]


def _rgb(hex_value: str) -> RGBColor:
    value = hex_value.lstrip("#")
    return RGBColor.from_string(value)


def _validate_spec() -> dict[str, object]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if not spec.get("review", {}).get("semantic_graph_approved"):
        raise ValueError("Figure 1 v4 semantic graph is not approved")
    edge_ids = {str(edge["id"]) for edge in spec.get("edges", [])}
    required = {
        "intervention-to-matched",
        "matched-to-distribution",
        "distribution-to-proxy",
        "distribution-to-vlm",
        "distribution-to-material",
        "distribution-to-stack",
    }
    if missing := sorted(required - edge_ids):
        raise ValueError(f"Figure 1 v4 spec is missing edges: {missing}")
    return spec


def _source_assets() -> dict[str, Image.Image | Path]:
    for material in ("wood", "stone", "ceramic", "metal"):
        for condition in ("source", "simplified"):
            path = v3.COMPONENT_DIR / f"{material}_{condition}.png"
            if not path.is_file():
                raise FileNotFoundError(path)

    selected, records = base._material_records()
    material_case = selected[0]
    return {
        "hero_original": base.SCENE_ORIGINAL,
        "hero_converted": base.SCENE_CONVERTED,
        "proxy_original": base.OBJECT_ORIGINAL,
        "proxy_converted": base.OBJECT_CONVERTED,
        "vlm_original": base._bbox_image(
            base.VLM_ORIGINAL, base.VLM_TARGET_BBOX, f"#{COLORS['original']}"
        ),
        "vlm_converted": base._bbox_image(
            base.VLM_CONVERTED, base.VLM_TARGET_BBOX, f"#{COLORS['converted']}"
        ),
        "material_original": base._material_image(
            material_case, records, "original_MDL"
        ),
        "material_converted": base._material_image(
            material_case, records, "existing_noMDL"
        ),
        "material_nvidia": base._material_image(
            material_case, records, "nvidia_asset_converter_preview_or_bake"
        ),
        "stack_original": base._nav_still("597_597", "original", "start"),
        "stack_converted": base._nav_still("597_597", "nomdl", "end"),
    }


def _as_image(value: Image.Image | Path) -> Image.Image:
    if isinstance(value, Image.Image):
        return value.convert("RGBA")
    return Image.open(value).convert("RGBA")


def _prepare_contained(
    value: Image.Image | Path,
    *,
    box: Box,
    output: Path,
    background: str = COLORS["white"],
    ppi: int = 600,
) -> Path:
    width = max(1, round(box.w * ppi))
    height = max(1, round(box.h * ppi))
    image = _as_image(value)
    contained = ImageOps.contain(image, (width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (width, height), f"#{background}")
    canvas.alpha_composite(
        contained,
        ((width - contained.width) // 2, (height - contained.height) // 2),
    )
    canvas.convert("RGB").save(output, quality=95)
    return output


def _text(
    name: str,
    box: Box,
    text: str,
    size: float,
    *,
    color: str = COLORS["ink"],
    bold: bool = False,
    align: Literal["left", "center", "right"] = "left",
    valign: Literal["top", "middle", "bottom"] = "middle",
    margin: float = 0.015,
) -> TextItem:
    return TextItem(name, box, text, size, color, bold, align, valign, margin)


def _build_layout(work_dir: Path) -> Layout:
    source = _source_assets()
    texts: list[TextItem] = []
    images: list[ImageItem] = []
    rects: list[RectItem] = []
    arrows: list[ArrowItem] = []

    texts.append(
        _text(
            "hero-statement",
            Box(0.14, 0.055, 6.92, 0.24),
            "Rewrite materials, hold scene and camera fixed, then run four independent checks",
            9.0,
            bold=True,
        )
    )
    texts.extend(
        [
            _text("panel-a", Box(0.14, 0.34, 2.12, 0.18), "(a)  Material rewrite", 7.2, bold=True),
            _text("panel-b", Box(2.62, 0.34, 1.70, 0.18), "(b)  Matched render pair", 7.2, bold=True),
            _text(
                "same-view",
                Box(5.28, 0.34, 1.68, 0.18),
                "same scene · same camera",
                6.0,
                color=COLORS["muted"],
                align="right",
            ),
            _text(
                "rewrite-flow",
                Box(0.14, 0.54, 2.35, 0.18),
                "MDL graph  →  ConvertAsset  →  UsdPreviewSurface",
                6.0,
                color=COLORS["muted"],
            ),
        ]
    )

    sphere_size = 0.34
    pair_specs = (
        ("wood", 0.16, 0.78, "wood"),
        ("stone", 1.22, 0.78, "stone"),
        ("ceramic", 0.16, 1.38, "ceramic"),
        ("metal", 1.22, 1.38, "metal"),
    )
    for material, x, y, label in pair_specs:
        source_path = v3.COMPONENT_DIR / f"{material}_source.png"
        target_path = v3.COMPONENT_DIR / f"{material}_simplified.png"
        images.extend(
            [
                ImageItem(f"{material}-source", Box(x, y, sphere_size, sphere_size), source_path),
                ImageItem(
                    f"{material}-simplified",
                    Box(x + 0.54, y, sphere_size, sphere_size),
                    target_path,
                ),
            ]
        )
        arrows.append(
            ArrowItem(
                f"{material}-arrow",
                (x + 0.37, y + sphere_size / 2),
                (x + 0.50, y + sphere_size / 2),
                COLORS["original"],
                0.8,
                "right",
            )
        )
        texts.append(
            _text(
                f"{material}-label",
                Box(x, y + 0.36, 0.88, 0.14),
                label,
                6.0,
                color=COLORS["muted"],
                align="center",
            )
        )

    arrows.append(
        ArrowItem(
            "intervention-to-hero",
            (2.35, 1.29),
            (2.56, 1.29),
            COLORS["original"],
            1.0,
            "right",
        )
    )

    hero_boxes = (
        ("hero-original", Box(2.62, 0.62, 2.10, 1.26), "hero_original", COLORS["original"]),
        ("hero-converted", Box(4.86, 0.62, 2.10, 1.26), "hero_converted", COLORS["converted"]),
    )
    for name, box, source_key, border in hero_boxes:
        prepared = _prepare_contained(
            source[source_key], box=box, output=work_dir / f"{name}.png"
        )
        images.append(ImageItem(name, box, prepared, border, 0.9))
    texts.extend(
        [
            _text(
                "hero-original-label",
                Box(2.62, 1.91, 2.10, 0.16),
                "Original MDL",
                7.2,
                color=COLORS["original"],
                bold=True,
                align="center",
            ),
            _text(
                "hero-converted-label",
                Box(4.86, 1.91, 2.10, 0.16),
                "noMDL",
                7.2,
                color=COLORS["converted"],
                bold=True,
                align="center",
            ),
            _text(
                "panel-c",
                Box(0.14, 2.16, 2.10, 0.18),
                "(c)  Four bounded checks",
                7.2,
                bold=True,
            ),
        ]
    )

    module_x = (0.14, 1.86, 3.58, 5.30)
    module_w = 1.58
    module_centers = tuple(x + module_w / 2 for x in module_x)
    arrows.extend(
        [
            ArrowItem("distribution-stem", (4.79, 2.08), (4.79, 2.40), COLORS["original"], 0.8),
            ArrowItem("distribution-rail", (module_centers[0], 2.40), (module_centers[-1], 2.40), COLORS["original"], 0.8),
        ]
    )
    for index, center in enumerate(module_centers, start=1):
        arrows.append(
            ArrowItem(
                f"distribution-{index}",
                (center, 2.40),
                (center, 2.52),
                COLORS["original"],
                0.8,
                "down",
            )
        )

    module_specs = (
        (
            "proxy",
            "Proxy similarity",
            "pixel + feature",
            (("proxy_original", COLORS["original"]), ("proxy_converted", COLORS["converted"])),
        ),
        (
            "vlm",
            "VLM grounding",
            "answer + point",
            (("vlm_original", COLORS["original"]), ("vlm_converted", COLORS["converted"])),
        ),
        (
            "material",
            "Material audit",
            "selected cases",
            (
                ("material_original", COLORS["original"]),
                ("material_converted", COLORS["converted"]),
                ("material_nvidia", COLORS["nvidia"]),
            ),
        ),
        (
            "stack",
            "Stack entry",
            "InternNav",
            (("stack_original", COLORS["original"]), ("stack_converted", COLORS["converted"])),
        ),
    )
    for index, (module, title, note, sources) in enumerate(module_specs):
        x = module_x[index]
        texts.append(_text(f"{module}-title", Box(x, 2.53, module_w, 0.15), title, 6.8, bold=True))
        gap = 0.035
        image_w = (module_w - gap * (len(sources) - 1)) / len(sources)
        for image_index, (source_key, border) in enumerate(sources):
            box = Box(x + image_index * (image_w + gap), 2.70, image_w, 0.34)
            prepared = _prepare_contained(
                source[source_key],
                box=box,
                output=work_dir / f"{module}-{image_index}.png",
                background=COLORS["soft"],
            )
            images.append(
                ImageItem(f"{module}-image-{image_index}", box, prepared, border, 0.65)
            )
        texts.append(
            _text(
                f"{module}-note",
                Box(x, 3.05, module_w, 0.20),
                note,
                6.0,
                color=COLORS["muted"],
                margin=0.04,
            )
        )
        if index < 3:
            rects.append(
                RectItem(
                    f"separator-{index + 1}",
                    Box(x + module_w + 0.065, 2.55, 0.008, 0.66),
                    COLORS["line"],
                )
            )
    return Layout(texts, images, rects, arrows)


def _boxes_overlap(a: Box, b: Box, tolerance: float = 0.002) -> bool:
    return not (
        a.right <= b.x + tolerance
        or b.right <= a.x + tolerance
        or a.bottom <= b.y + tolerance
        or b.bottom <= a.y + tolerance
    )


def _font_path(item: TextItem) -> Path:
    return FONT_BOLD if item.bold else FONT_REGULAR


def _measure_text(item: TextItem, dpi: int = 288) -> tuple[float, float]:
    font_px = max(1, round(item.size * dpi / 72.0))
    font = ImageFont.truetype(str(_font_path(item)), font_px)
    canvas = Image.new("RGB", (8, 8), "white")
    draw = ImageDraw.Draw(canvas)
    bbox = draw.multiline_textbbox((0, 0), item.text, font=font, spacing=round(font_px * 0.2))
    width = max(0, bbox[2] - bbox[0]) * 1.08
    ascent, descent = font.getmetrics()
    height = (ascent + descent) * max(1, item.text.count("\n") + 1) * 1.08
    return width / dpi, height / dpi


def validate_layout(layout: Layout) -> dict[str, object]:
    findings: list[str] = []
    all_boxes: list[tuple[str, Box]] = []
    for item in layout.texts:
        all_boxes.append((item.name, item.box))
        if item.size < MIN_FONT_PT:
            findings.append(f"{item.name}: font {item.size} pt below {MIN_FONT_PT} pt")
        width, height = _measure_text(item)
        available_w = item.box.w - 2 * item.margin
        available_h = item.box.h - 2 * item.margin
        if width > available_w or height > available_h:
            findings.append(
                f"{item.name}: text {width:.3f}x{height:.3f} in exceeds "
                f"{available_w:.3f}x{available_h:.3f} in"
            )
    for item in layout.images:
        all_boxes.append((item.name, item.box))
    for item in layout.rects:
        all_boxes.append((item.name, item.box))
    for name, box in all_boxes:
        if box.x < 0 or box.y < 0 or box.right > SLIDE_W or box.bottom > SLIDE_H:
            findings.append(f"{name}: box outside slide: {box}")
    for arrow in layout.arrows:
        for point in (arrow.start, arrow.end):
            if not (0 <= point[0] <= SLIDE_W and 0 <= point[1] <= SLIDE_H):
                findings.append(f"{arrow.name}: endpoint outside slide: {point}")
    allowed_image_text_pairs = {
        ("wood-label", "wood-source"),
        ("wood-label", "wood-simplified"),
        ("stone-label", "stone-source"),
        ("stone-label", "stone-simplified"),
        ("ceramic-label", "ceramic-source"),
        ("ceramic-label", "ceramic-simplified"),
        ("metal-label", "metal-source"),
        ("metal-label", "metal-simplified"),
    }
    for text_item in layout.texts:
        for image_item in layout.images:
            if _boxes_overlap(text_item.box, image_item.box) and (
                text_item.name,
                image_item.name,
            ) not in allowed_image_text_pairs:
                findings.append(f"{text_item.name}: overlaps image {image_item.name}")
    if findings:
        raise ValueError("layout validation failed:\n- " + "\n- ".join(findings))
    return {
        "ok": True,
        "slide_inches": [SLIDE_W, SLIDE_H],
        "text_count": len(layout.texts),
        "image_count": len(layout.images),
        "shape_count": len(layout.rects) + len(layout.arrows),
        "font_sizes_pt": sorted({item.size for item in layout.texts}),
        "minimum_font_pt": min(item.size for item in layout.texts),
        "text_safe_margin_inches": min(item.margin for item in layout.texts),
        "findings": [],
    }


def _add_rect(slide, item: RectItem) -> None:
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(item.box.x),
        Inches(item.box.y),
        Inches(item.box.w),
        Inches(item.box.h),
    )
    shape.name = item.name
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(item.fill)
    shape.line.fill.background()


def _add_arrow(slide, item: ArrowItem) -> None:
    x1, y1 = item.start
    x2, y2 = item.end
    line_h = max(0.006, item.width_pt / 72.0)
    if abs(y2 - y1) < 1e-8:
        box = Box(min(x1, x2), y1 - line_h / 2, abs(x2 - x1), line_h)
    elif abs(x2 - x1) < 1e-8:
        box = Box(x1 - line_h / 2, min(y1, y2), line_h, abs(y2 - y1))
    else:
        raise ValueError(f"only orthogonal arrow segments are supported: {item.name}")
    _add_rect(slide, RectItem(item.name + "-line", box, item.color))
    if item.head == "none":
        return
    head_size = 0.055
    head = slide.shapes.add_shape(
        MSO_SHAPE.ISOSCELES_TRIANGLE,
        Inches(x2 - head_size / 2),
        Inches(y2 - head_size / 2),
        Inches(head_size),
        Inches(head_size),
    )
    head.name = item.name + "-head"
    head.rotation = 90 if item.head == "right" else 180
    head.fill.solid()
    head.fill.fore_color.rgb = _rgb(item.color)
    head.line.fill.background()


def _add_image(slide, item: ImageItem) -> None:
    picture = slide.shapes.add_picture(
        str(item.path),
        Inches(item.box.x),
        Inches(item.box.y),
        Inches(item.box.w),
        Inches(item.box.h),
    )
    picture.name = item.name
    if item.border:
        border = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(item.box.x),
            Inches(item.box.y),
            Inches(item.box.w),
            Inches(item.box.h),
        )
        border.name = item.name + "-border"
        border.fill.background()
        border.line.color.rgb = _rgb(item.border)
        border.line.width = Pt(item.border_pt)


def _add_text(slide, item: TextItem) -> None:
    shape = slide.shapes.add_textbox(
        Inches(item.box.x),
        Inches(item.box.y),
        Inches(item.box.w),
        Inches(item.box.h),
    )
    shape.name = item.name
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = False
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.margin_left = Inches(item.margin)
    frame.margin_right = Inches(item.margin)
    frame.margin_top = Inches(item.margin)
    frame.margin_bottom = Inches(item.margin)
    frame.vertical_anchor = {
        "top": MSO_ANCHOR.TOP,
        "middle": MSO_ANCHOR.MIDDLE,
        "bottom": MSO_ANCHOR.BOTTOM,
    }[item.valign]
    paragraph = frame.paragraphs[0]
    paragraph.alignment = {
        "left": PP_ALIGN.LEFT,
        "center": PP_ALIGN.CENTER,
        "right": PP_ALIGN.RIGHT,
    }[item.align]
    paragraph.space_before = Pt(0)
    paragraph.space_after = Pt(0)
    run = paragraph.add_run()
    run.text = item.text
    run.font.name = FONT_NAME
    run.font.size = Pt(item.size)
    run.font.bold = item.bold
    run.font.color.rgb = _rgb(item.color)


def _neutralize_theme_effects(path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="pptx-flat-") as tmp_value:
        tmp = Path(tmp_value)
        rebuilt = tmp / path.name
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
            rebuilt, "w", zipfile.ZIP_DEFLATED
        ) as target:
            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    text = re.sub(
                        r'(<a:effectRef\b[^>]*\bidx=")[^"]+("[^>]*>)',
                        r"\g<1>0\2",
                        text,
                    )
                    text = re.sub(
                        r"<a:outerShdw\b[^>]*>.*?</a:outerShdw>",
                        "",
                        text,
                        flags=re.DOTALL,
                    )
                    data = text.encode("utf-8")
                target.writestr(info, data)
        shutil.copyfile(rebuilt, path)


def build_pptx(layout: Layout, output: Path) -> None:
    presentation = Presentation()
    presentation.slide_width = Inches(SLIDE_W)
    presentation.slide_height = Inches(SLIDE_H)
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(COLORS["white"])
    for item in layout.rects:
        _add_rect(slide, item)
    for item in layout.arrows:
        _add_arrow(slide, item)
    for item in layout.images:
        _add_image(slide, item)
    for item in layout.texts:
        _add_text(slide, item)
    presentation.save(output)
    _neutralize_theme_effects(output)


def _svg_box(box: Box) -> tuple[float, float, float, float]:
    return tuple(value * SVG_UNITS_PER_INCH for value in (box.x, box.y, box.w, box.h))


def _svg_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _image_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build_svg(layout: Layout, output: Path) -> None:
    width = SLIDE_W * SVG_UNITS_PER_INCH
    height = SLIDE_H * SVG_UNITS_PER_INCH
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="2160" height="990" viewBox="0 0 {width:g} {height:g}">',
        f'<rect x="0" y="0" width="{width:g}" height="{height:g}" fill="#FFFFFF"/>',
    ]
    for item in layout.rects:
        x, y, w, h = _svg_box(item.box)
        parts.append(
            f'<rect id="{_svg_escape(item.name)}" x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="#{item.fill}"/>'
        )
    for item in layout.arrows:
        x1, y1 = (value * SVG_UNITS_PER_INCH for value in item.start)
        x2, y2 = (value * SVG_UNITS_PER_INCH for value in item.end)
        parts.append(
            f'<line id="{_svg_escape(item.name)}" x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="#{item.color}" stroke-width="{item.width_pt * SVG_UNITS_PER_INCH / 72:.3f}"/>'
        )
        if item.head == "right":
            size = 3.2
            points = f"{x2:.3f},{y2:.3f} {x2-size:.3f},{y2-size/1.6:.3f} {x2-size:.3f},{y2+size/1.6:.3f}"
            parts.append(f'<polygon points="{points}" fill="#{item.color}"/>')
        elif item.head == "down":
            size = 3.2
            points = f"{x2:.3f},{y2:.3f} {x2-size/1.6:.3f},{y2-size:.3f} {x2+size/1.6:.3f},{y2-size:.3f}"
            parts.append(f'<polygon points="{points}" fill="#{item.color}"/>')
    for item in layout.images:
        x, y, w, h = _svg_box(item.box)
        parts.append(
            f'<image id="{_svg_escape(item.name)}" x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" preserveAspectRatio="none" href="{_image_data_url(item.path)}"/>'
        )
        if item.border:
            parts.append(
                f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="none" stroke="#{item.border}" stroke-width="{item.border_pt * SVG_UNITS_PER_INCH / 72:.3f}"/>'
            )
    for item in layout.texts:
        x, y, w, h = _svg_box(item.box)
        anchor = {"left": "start", "center": "middle", "right": "end"}[item.align]
        tx = {"left": x + item.margin * SVG_UNITS_PER_INCH, "center": x + w / 2, "right": x + w - item.margin * SVG_UNITS_PER_INCH}[item.align]
        font_size = item.size * SVG_UNITS_PER_INCH / 72.0
        ty = y + h / 2 + font_size * 0.34
        weight = "700" if item.bold else "400"
        parts.append(
            f'<text id="{_svg_escape(item.name)}" x="{tx:.3f}" y="{ty:.3f}" text-anchor="{anchor}" font-family="{FONT_NAME}" font-size="{font_size:.3f}" font-weight="{weight}" fill="#{item.color}">{_svg_escape(item.text)}</text>'
        )
    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)


def export_pptx(pptx_path: Path, pdf_path: Path, png_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="fig1-v4-render-") as tmp_value:
        tmp = Path(tmp_value)
        profile = tmp / "lo-profile"
        _run(
            [
                "soffice",
                "--headless",
                f"-env:UserInstallation=file://{profile}",
                "--convert-to",
                "pdf:impress_pdf_Export",
                "--outdir",
                str(tmp),
                str(pptx_path),
            ]
        )
        rendered_pdf = tmp / f"{pptx_path.stem}.pdf"
        if not rendered_pdf.is_file():
            raise FileNotFoundError(rendered_pdf)
        normalized_pdf = tmp / f"{pptx_path.stem}-pdf15.pdf"
        _run(
            [
                "gs",
                "-q",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.5",
                "-dNOPAUSE",
                "-dBATCH",
                "-dSAFER",
                "-dAutoRotatePages=/None",
                "-dDownsampleColorImages=false",
                "-dDownsampleGrayImages=false",
                "-dDownsampleMonoImages=false",
                f"-sOutputFile={normalized_pdf}",
                str(rendered_pdf),
            ]
        )
        shutil.copyfile(normalized_pdf, pdf_path)
    _run(
        [
            "pdftocairo",
            "-png",
            "-singlefile",
            "-r",
            "300",
            str(pdf_path),
            str(png_path.with_suffix("")),
        ]
    )


def build(output_dir: Path) -> dict[str, object]:
    _validate_spec()
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_dir / STEM.name
    with tempfile.TemporaryDirectory(prefix="fig1-v4-assets-") as tmp_value:
        layout = _build_layout(Path(tmp_value))
        layout_report = validate_layout(layout)
        build_svg(layout, stem.with_suffix(".svg"))
        build_pptx(layout, stem.with_suffix(".pptx"))
        export_pptx(
            stem.with_suffix(".pptx"),
            stem.with_suffix(".pdf"),
            stem.with_suffix(".png"),
        )
    with Image.open(stem.with_suffix(".png")) as image:
        if image.size != (2160, 990):
            raise ValueError(f"unexpected PNG dimensions: {image.size}")
    return {
        "ok": True,
        "outputs": [
            str(stem.with_suffix(suffix).relative_to(ROOT))
            for suffix in (".pptx", ".svg", ".pdf", ".png")
        ],
        "layout": layout_report,
    }


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
