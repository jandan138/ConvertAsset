#!/usr/bin/env python3
"""Generate story-first ACL main and selected supplemental figures.

The generated material spheres are explanatory slots. All evidence-bearing
render, material, and navigation panels are read from existing project records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage

import gen_acl_main_figures_v2 as base


ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = ROOT / "paper/shared/figures"
RAW_DIR = ROOT / "paper/shared/evidence/raw"
COMPONENT_DIR = FIG_DIR / "generated_components/fig1_material_pairs_v1"
COMPONENT_ATLAS = COMPONENT_DIR / "atlas_selected.png"
COMPONENT_MANIFEST = COMPONENT_DIR / "manifest.yaml"
SPEC_PATH = FIG_DIR / "specs/fig_acl_method_chain_v3.spec.json"

OUTPUT_NAMES = {
    "fig1": "fig_acl_method_chain_v3",
    "table1": "fig_acl_evidence_registry_strip_v2",
    "fig2": "fig_render_scene_evidence_wide_v3",
    "fig3": "fig_material_effect_baseline_qualitative_v3",
    "fig4": "fig_internnav_rollout_main_v3",
    "quickstart": "fig_supplement_first_page_evidence_quickstart_v2",
    "vlm": "fig_supplement_vlm_coordinate_protocol_atlas_v2",
    "material": "fig_supplement_material_diagnostic_atlas_v2",
    "nav": "fig_supplement_navigation_media_atlas_v2",
}

COLORS = base.COLORS
FONT_ROLES = {"hero": 10.0, "title": 8.0, "body": 7.0, "note": 6.0}

VLM_ROOT = RAW_DIR / "grscene_vlm_grounding/retake_zoom_renders"
VLM_CASES = (
    {
        "name": "Backpack",
        "scene": "MV7J6NIKTKJZ2AABAAAAADQ8_usd",
        "target": "47aa36277a54f6ca90cc",
        "zoom": "zoom_018",
        "bbox": (207.811, 105.285, 376.441, 364.938),
        "note": "raw center can\nscore without the\nnormalized contract",
    },
    {
        "name": "Clock",
        "scene": "MV7J6NIKTKJZ2AABAAAAADQ8_usd",
        "target": "f35ef3d86c42446b7ddf",
        "zoom": "zoom_018",
        "bbox": (211.647, 107.436, 370.171, 360.234),
        "note": "bbox center maps\nto normalized-1000",
    },
    {
        "name": "Bottle",
        "scene": "MV7J6NIKTKJZ2AABAAAAADA8_usd",
        "target": "c27086f557d316584264",
        "zoom": "zoom_018",
        "bbox": (230.385, 89.121, 369.378, 372.696),
        "note": "answer, parse,\nand point stay\nseparate",
    },
)

SUPPLEMENTAL_MATERIAL_MANIFEST = (
    RAW_DIR / "material_effect_baseline/supplemental_qualitative_render_manifest.json"
)
NAV_SUMMARY = FIG_DIR / "fig_internnav_downstream_panel.png"

COMPONENT_SLOTS = (
    ("wood_source", 0, 0),
    ("wood_simplified", 0, 1),
    ("stone_source", 1, 0),
    ("stone_simplified", 1, 1),
    ("ceramic_source", 2, 0),
    ("ceramic_simplified", 2, 1),
    ("metal_source", 3, 0),
    ("metal_simplified", 3, 1),
)
COMPONENT_ALPHA_THRESHOLD = 12
COMPONENT_MIN_AREA_FRACTION = 0.01
COMPONENT_MAX_EDGE_WIDTH_FRACTION = 0.15


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def apply_style() -> None:
    base.apply_publication_style()
    plt.rcParams.update(
        {
            "font.size": FONT_ROLES["body"],
            "axes.titleweight": "bold",
            "savefig.transparent": False,
        }
    )


def _output_stem(name: str, output_dir: Path) -> Path:
    return output_dir / OUTPUT_NAMES[name]


def _save_bundle(fig: plt.Figure, stem: Path, dpi: int = 300) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = [stem.with_suffix(suffix) for suffix in (".svg", ".pdf", ".png")]
    fig.savefig(outputs[0], dpi=dpi, facecolor="white")
    fig.savefig(outputs[1], dpi=dpi, facecolor="white", metadata={"Creator": "Python/Matplotlib"})
    fig.savefig(outputs[2], dpi=dpi, facecolor="white")
    plt.close(fig)
    return outputs


def _fig_patch(fig: plt.Figure, patch: Any, *, zorder: float = -10) -> None:
    patch.set_transform(fig.transFigure)
    patch.set_clip_on(False)
    patch.set_zorder(zorder)
    fig.patches.append(patch)


def _arrow(
    fig: plt.Figure,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str,
    dashed: bool = False,
    width: float = 1.2,
    mutation_scale: float = 8,
) -> None:
    _fig_patch(
        fig,
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            linewidth=width,
            linestyle="--" if dashed else "-",
            color=color,
            shrinkA=0,
            shrinkB=0,
        ),
        zorder=8,
    )


def _section_heading(
    fig: plt.Figure,
    *,
    x: float,
    y: float,
    width: float,
    title: str,
    color: str = COLORS["structure"],
) -> None:
    fig.text(
        x,
        y,
        title,
        fontsize=FONT_ROLES["title"],
        fontweight="bold",
        color=COLORS["ink"],
        va="bottom",
    )
    _fig_patch(
        fig,
        Rectangle((x, y - 0.012), width, 0.006, facecolor=color, edgecolor="none"),
        zorder=-5,
    )


def _add_contained_image(
    fig: plt.Figure,
    rect: tuple[float, float, float, float],
    image_or_path: Image.Image | Path | str,
    *,
    border: str | None = COLORS["line"],
    face: str = "white",
    pad_fraction: float = 0.04,
) -> plt.Axes:
    image = (
        image_or_path.convert("RGBA")
        if isinstance(image_or_path, Image.Image)
        else Image.open(base._repo_path(image_or_path)).convert("RGBA")
    )
    ax = fig.add_axes(rect, zorder=2)
    ax.set_facecolor(face)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    alpha_bbox = image.getchannel("A").getbbox() or (0, 0, image.width, image.height)
    cropped = image.crop(alpha_bbox)
    width, height = cropped.size
    max_side = max(width, height)
    pad = max(1, int(round(max_side * pad_fraction)))
    canvas = Image.new(
        "RGBA", (max_side + 2 * pad, max_side + 2 * pad), (255, 255, 255, 0)
    )
    canvas.alpha_composite(
        cropped,
        ((canvas.width - width) // 2, (canvas.height - height) // 2),
    )
    white = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
    white.alpha_composite(canvas)
    ax.imshow(
        np.asarray(white.convert("RGB")),
        extent=(0, 1, 0, 1),
        interpolation="lanczos",
    )
    if border:
        ax.add_patch(
            Rectangle(
                (0, 0),
                1,
                1,
                transform=ax.transAxes,
                facecolor="none",
                edgecolor=border,
                linewidth=0.7,
            )
        )
    return ax


def _add_full_image(
    fig: plt.Figure,
    rect: tuple[float, float, float, float],
    image_or_path: Image.Image | Path | str,
    *,
    border: str = COLORS["line"],
    face: tuple[int, int, int] = (255, 255, 255),
) -> plt.Axes:
    image = (
        image_or_path.convert("RGB")
        if isinstance(image_or_path, Image.Image)
        else base._read_image(image_or_path)
    )
    physical_aspect = (rect[2] * fig.get_figwidth()) / (
        rect[3] * fig.get_figheight()
    )
    target_w = 1200
    target_h = max(1, int(round(target_w / physical_aspect)))
    contained = ImageOps.contain(
        image, (target_w, target_h), Image.Resampling.LANCZOS
    )
    canvas = Image.new("RGB", (target_w, target_h), face)
    canvas.paste(
        contained,
        ((target_w - contained.width) // 2, (target_h - contained.height) // 2),
    )
    ax = fig.add_axes(rect, zorder=2)
    ax.imshow(np.asarray(canvas), interpolation="lanczos")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(border)
        spine.set_linewidth(0.7)
    return ax


def prepare_material_components() -> dict[str, Any]:
    if not COMPONENT_ATLAS.is_file():
        raise FileNotFoundError(COMPONENT_ATLAS)
    atlas = Image.open(COMPONENT_ATLAS).convert("RGBA")
    atlas_array = np.asarray(atlas).copy()
    alpha_array = atlas_array[:, :, 3]
    labels, raw_component_count = ndimage.label(
        alpha_array > COMPONENT_ALPHA_THRESHOLD
    )
    sizes = np.bincount(labels.ravel())
    minimum_pixels = max(
        1000,
        int(round(atlas.width * atlas.height * COMPONENT_MIN_AREA_FRACTION)),
    )
    components: list[dict[str, Any]] = []
    for label in range(1, raw_component_count + 1):
        if int(sizes[label]) < minimum_pixels:
            continue
        ys, xs = np.where(labels == label)
        components.append(
            {
                "label": label,
                "pixels": int(sizes[label]),
                "centroid": (float(xs.mean()), float(ys.mean())),
            }
        )
    if len(components) != len(COMPONENT_SLOTS):
        raise ValueError(
            "expected exactly eight material-sphere components in the full atlas; "
            f"found {len(components)} above {minimum_pixels} pixels"
        )

    components.sort(key=lambda item: item["centroid"][1])
    ordered_components: list[dict[str, Any]] = []
    for row in range(4):
        row_components = components[row * 2 : (row + 1) * 2]
        ordered_components.extend(
            sorted(row_components, key=lambda item: item["centroid"][0])
        )

    COMPONENT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema_version": 1,
        "atlas": str(COMPONENT_ATLAS.relative_to(ROOT)),
        "atlas_sha256": _sha256(COMPONENT_ATLAS),
        "extraction_method": "whole_atlas_alpha_connected_components",
        "alpha_threshold": COMPONENT_ALPHA_THRESHOLD,
        "raw_alpha_component_count": int(raw_component_count),
        "significant_component_count": len(ordered_components),
        "minimum_component_pixels": minimum_pixels,
        "slots": {},
    }
    for (name, row, col), component_record in zip(
        COMPONENT_SLOTS, ordered_components
    ):
        label = int(component_record["label"])
        keep = ndimage.binary_dilation(labels == label, iterations=2)
        component_array = atlas_array.copy()
        component_array[:, :, 3] = np.where(keep, alpha_array, 0)
        component = Image.fromarray(component_array, mode="RGBA")
        alpha = component.getchannel("A")
        bbox = alpha.point(
            lambda value: 255 if value > COMPONENT_ALPHA_THRESHOLD else 0
        ).getbbox()
        if bbox is None:
            raise ValueError(f"empty alpha slot: {name}")
        cropped = component.crop(bbox)
        side = max(cropped.size)
        pad = max(10, int(round(side * 0.16)))
        square = Image.new(
            "RGBA", (side + 2 * pad, side + 2 * pad), (255, 255, 255, 0)
        )
        square.alpha_composite(
            cropped,
            ((square.width - cropped.width) // 2, (square.height - cropped.height) // 2),
        )
        square = square.resize((512, 512), Image.Resampling.LANCZOS)
        output = COMPONENT_DIR / f"{name}.png"
        square.save(output)
        out_alpha = np.asarray(square.getchannel("A"), dtype=np.float64)
        visible = out_alpha > COMPONENT_ALPHA_THRESHOLD
        ys, xs = np.nonzero(visible)
        weights = out_alpha[ys, xs]
        row_widths = np.count_nonzero(visible, axis=1)
        nonzero_widths = row_widths[row_widths > 0]
        maximum_width = int(nonzero_widths.max())
        top_edge_fraction = float(nonzero_widths[0] / maximum_width)
        bottom_edge_fraction = float(nonzero_widths[-1] / maximum_width)
        if max(top_edge_fraction, bottom_edge_fraction) > COMPONENT_MAX_EDGE_WIDTH_FRACTION:
            raise ValueError(
                f"truncated material-sphere silhouette for {name}: "
                f"top={top_edge_fraction:.3f}, bottom={bottom_edge_fraction:.3f}"
            )
        report["slots"][name] = {
            "path": str(output.relative_to(ROOT)),
            "sha256": _sha256(output),
            "grid_position": [row, col],
            "atlas_bbox": [int(value) for value in bbox],
            "atlas_centroid": [
                float(component_record["centroid"][0]),
                float(component_record["centroid"][1]),
            ],
            "atlas_visible_pixels": int(component_record["pixels"]),
            "alpha_bbox": [
                int(xs.min()),
                int(ys.min()),
                int(xs.max() + 1),
                int(ys.max() + 1),
            ],
            "alpha_centroid": [
                float(np.average(xs, weights=weights)),
                float(np.average(ys, weights=weights)),
            ],
            "visible_fraction": float(visible.mean()),
            "top_edge_width_fraction": top_edge_fraction,
            "bottom_edge_width_fraction": bottom_edge_fraction,
        }
    optics_path = COMPONENT_DIR / "optics.json"
    optics_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def _component(name: str) -> Path:
    path = COMPONENT_DIR / f"{name}.png"
    if not path.is_file():
        prepare_material_components()
    return path


def validate_fig1_spec() -> dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if not spec.get("review", {}).get("semantic_graph_approved"):
        raise ValueError("Figure 1 v3 semantic graph is not approved")
    edge_ids = {edge["id"] for edge in spec["edges"]}
    required = {
        "matched-to-proxy",
        "matched-to-vlm",
        "matched-to-material",
        "matched-to-stack",
    }
    if not required <= edge_ids:
        raise ValueError("Figure 1 v3 is missing one or more independent checks")
    for asset in spec["assets"]:
        path = (SPEC_PATH.parent / asset["path"]).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
    return spec


def _vlm_paths(case: dict[str, Any]) -> tuple[Path, Path]:
    root = VLM_ROOT / case["scene"] / case["target"] / case["zoom"]
    return root / "original/original_0000.png", root / "converted/converted_0000.png"


def _protocol_overlay(
    path: Path, bbox: tuple[float, float, float, float]
) -> Image.Image:
    image = base._read_image(path)
    draw = ImageDraw.Draw(image)
    x0, y0, x1, y1 = [int(round(value)) for value in bbox]
    cx, cy = int(round((x0 + x1) / 2)), int(round((y0 + y1) / 2))
    ix, iy = image.width // 2, image.height // 2
    width = max(3, image.width // 180)
    draw.rectangle((x0, y0, x1, y1), outline=COLORS["pass"], width=width)
    radius = max(5, image.width // 70)
    draw.ellipse(
        (ix - radius, iy - radius, ix + radius, iy + radius),
        fill=COLORS["structure"],
        outline="white",
        width=2,
    )
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=COLORS["converted"],
        outline="white",
        width=2,
    )
    return image


def _supplemental_material_records(
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], Path]]:
    manifest = json.loads(SUPPLEMENTAL_MATERIAL_MANIFEST.read_text(encoding="utf-8"))
    cases = list(manifest["selected_cases"])
    records: dict[tuple[str, str], Path] = {}
    for record in manifest["records"]:
        image = record.get("image") or {}
        if image.get("status") == "ready":
            records[(str(record["sample_id"]), str(record["condition"]))] = base._repo_path(
                image["path"]
            )
    return cases, records


def build_fig1(output_dir: Path) -> list[Path]:
    prepare_material_components()
    validate_fig1_spec()
    fig = plt.figure(figsize=(7.2, 3.3), facecolor="white")
    _section_heading(
        fig, x=0.025, y=0.935, width=0.265, title="MATERIAL INTERVENTION"
    )
    _section_heading(fig, x=0.325, y=0.935, width=0.44, title="MATCHED EVIDENCE")
    _section_heading(
        fig, x=0.80, y=0.935, width=0.175, title="INDEPENDENT CHECKS"
    )

    icon_ax = fig.add_axes((0.035, 0.72, 0.245, 0.15), zorder=2)
    icon_ax.set_xlim(0, 1)
    icon_ax.set_ylim(0, 1)
    icon_ax.axis("off")
    icon_ax.add_patch(
        FancyBboxPatch(
            (0.01, 0.12),
            0.20,
            0.72,
            boxstyle="round,pad=0.02",
            facecolor="white",
            edgecolor=COLORS["structure"],
            lw=1.3,
        )
    )
    icon_ax.text(
        0.11,
        0.48,
        ".usd",
        ha="center",
        va="center",
        fontsize=FONT_ROLES["title"],
        fontweight="bold",
        color=COLORS["ink"],
    )
    icon_ax.text(
        0.31,
        0.49,
        "+",
        ha="center",
        va="center",
        fontsize=FONT_ROLES["hero"],
        color=COLORS["muted"],
    )
    icon_ax.text(
        0.52,
        0.58,
        "MDL",
        ha="center",
        va="center",
        fontsize=FONT_ROLES["title"],
        fontweight="bold",
        color=COLORS["original"],
    )
    icon_ax.annotate(
        "",
        xy=(0.90, 0.49),
        xytext=(0.64, 0.49),
        arrowprops={
            "arrowstyle": "-|>",
            "lw": 1.5,
            "color": COLORS["structure"],
        },
    )
    icon_ax.text(
        0.77,
        0.70,
        "ConvertAsset",
        ha="center",
        fontsize=FONT_ROLES["note"],
        color=COLORS["ink"],
        fontweight="bold",
    )
    icon_ax.text(
        0.90,
        0.26,
        "noMDL",
        ha="center",
        fontsize=FONT_ROLES["title"],
        fontweight="bold",
        color=COLORS["converted"],
    )
    fig.text(
        0.157,
        0.695,
        "composition retained",
        ha="center",
        fontsize=FONT_ROLES["note"],
        color=COLORS["pass"],
    )
    fig.text(
        0.078,
        0.655,
        "MDL cues",
        ha="center",
        fontsize=FONT_ROLES["note"],
        fontweight="bold",
        color=COLORS["original"],
    )
    fig.text(
        0.242,
        0.655,
        "simplified cues",
        ha="center",
        fontsize=FONT_ROLES["note"],
        fontweight="bold",
        color=COLORS["converted"],
    )

    rows = ("wood", "stone", "ceramic", "metal")
    row_y = (0.515, 0.385, 0.255, 0.125)
    for row, y in zip(rows, row_y):
        _add_contained_image(
            fig,
            (0.045, y, 0.075, 0.115),
            _component(f"{row}_source"),
            border=None,
            pad_fraction=0.02,
        )
        _add_contained_image(
            fig,
            (0.205, y, 0.075, 0.115),
            _component(f"{row}_simplified"),
            border=None,
            pad_fraction=0.02,
        )
        _arrow(
            fig,
            (0.132, y + 0.057),
            (0.193, y + 0.057),
            color=COLORS["structure"],
            width=1.0,
            mutation_scale=7,
        )
    fig.text(
        0.162,
        0.075,
        "illustrative material pairs",
        ha="center",
        fontsize=FONT_ROLES["note"],
        color=COLORS["muted"],
    )

    _fig_patch(
        fig,
        FancyBboxPatch(
            (0.325, 0.10),
            0.44,
            0.79,
            boxstyle="round,pad=0.004,rounding_size=0.012",
            facecolor=COLORS["soft"],
            edgecolor=COLORS["line"],
            linewidth=0.8,
        ),
    )
    fig.text(
        0.545,
        0.835,
        "same scene · same camera",
        ha="center",
        fontsize=FONT_ROLES["body"],
        color=COLORS["muted"],
    )
    base._add_image(
        fig,
        (0.345, 0.245, 0.19, 0.54),
        base.SCENE_ORIGINAL,
        border=COLORS["original"],
        linewidth=1.0,
    )
    base._add_image(
        fig,
        (0.555, 0.245, 0.19, 0.54),
        base.SCENE_CONVERTED,
        border=COLORS["converted"],
        linewidth=1.0,
    )
    fig.text(
        0.440,
        0.195,
        "Original MDL",
        ha="center",
        fontsize=FONT_ROLES["title"],
        fontweight="bold",
        color=COLORS["original"],
    )
    fig.text(
        0.650,
        0.195,
        "noMDL",
        ha="center",
        fontsize=FONT_ROLES["title"],
        fontweight="bold",
        color=COLORS["converted"],
    )
    _arrow(
        fig,
        (0.538, 0.51),
        (0.552, 0.51),
        color=COLORS["structure"],
        width=1.3,
        mutation_scale=8,
    )
    _arrow(
        fig,
        (0.292, 0.50),
        (0.318, 0.50),
        color=COLORS["structure"],
        width=1.4,
        mutation_scale=9,
    )

    gates = (
        ("1", "Proxy similarity", "pixel + feature"),
        ("2", "VLM grounding", "answer + point"),
        ("3", "Material audit", "selected cases"),
        ("4", "Stack entry", "InternNav"),
    )
    gate_y = (0.69, 0.51, 0.33, 0.15)
    bus_x = 0.785
    _fig_patch(
        fig,
        Rectangle(
            (bus_x, 0.21),
            0.002,
            0.57,
            facecolor=COLORS["converted"],
            edgecolor="none",
        ),
        zorder=4,
    )
    _arrow(
        fig,
        (0.765, 0.50),
        (bus_x, 0.50),
        color=COLORS["converted"],
        dashed=True,
        width=1.2,
    )
    for (number, title, note), y in zip(gates, gate_y):
        _fig_patch(
            fig,
            FancyBboxPatch(
                (0.815, y - 0.055),
                0.16,
                0.12,
                boxstyle="round,pad=0.003,rounding_size=0.008",
                facecolor="white",
                edgecolor=COLORS["line"],
                linewidth=0.8,
            ),
        )
        _fig_patch(
            fig,
            Circle(
                (0.835, y + 0.005),
                0.014,
                facecolor=COLORS["structure"],
                edgecolor="none",
            ),
            zorder=3,
        )
        fig.text(
            0.835,
            y + 0.005,
            number,
            ha="center",
            va="center",
            fontsize=FONT_ROLES["note"],
            fontweight="bold",
            color="white",
        )
        fig.text(
            0.858,
            y + 0.025,
            title,
            fontsize=FONT_ROLES["body"],
            fontweight="bold",
            color=COLORS["ink"],
            va="center",
        )
        fig.text(
            0.858,
            y - 0.020,
            note,
            fontsize=FONT_ROLES["note"],
            color=COLORS["muted"],
            va="center",
        )
        _arrow(
            fig,
            (bus_x, y + 0.005),
            (0.806, y + 0.005),
            color=COLORS["converted"],
            dashed=True,
            width=1.0,
            mutation_scale=7,
        )
    return _save_bundle(fig, _output_stem("fig1", output_dir))


def _evidence_card(
    fig: plt.Figure,
    *,
    rect: tuple[float, float, float, float],
    number: str,
    title: str,
    evidence: str,
    boundary: str,
    images: Iterable[Image.Image | Path],
    borders: Iterable[str],
) -> None:
    x, y, w, h = rect
    _fig_patch(
        fig,
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.003,rounding_size=0.008",
            facecolor="white",
            edgecolor=COLORS["line"],
            linewidth=0.8,
        ),
    )
    _fig_patch(
        fig,
        Rectangle(
            (x, y + h - 0.09),
            w,
            0.09,
            facecolor=COLORS["structure"],
            edgecolor="none",
        ),
        zorder=-8,
    )
    fig.text(x + 0.014, y + h - 0.045, number, color="white", fontsize=7.5, fontweight="bold", va="center")
    fig.text(x + 0.045, y + h - 0.045, title, color="white", fontsize=7.5, fontweight="bold", va="center")
    image_list = list(images)
    border_list = list(borders)
    gap = 0.006
    image_w = (w - 0.024 - gap * (len(image_list) - 1)) / len(image_list)
    for index, image in enumerate(image_list):
        base._add_image(
            fig,
            (x + 0.012 + index * (image_w + gap), y + 0.205, image_w, h - 0.325),
            image,
            border=border_list[index],
            linewidth=0.7,
        )
    fig.text(x + 0.012, y + 0.145, evidence, fontsize=6.4, fontweight="bold", color=COLORS["ink"])
    fig.text(x + 0.012, y + 0.050, boundary, fontsize=6.0, color=COLORS["muted"])


def build_table1(output_dir: Path) -> list[Path]:
    selected, records = base._material_records()
    case = selected[0]
    fig = plt.figure(figsize=(7.2, 1.55), facecolor="white")
    margin, gap = 0.015, 0.012
    width = (1 - 2 * margin - 3 * gap) / 4
    xs = [margin + index * (width + gap) for index in range(4)]
    vlm_a = base._bbox_image(base.VLM_ORIGINAL, base.VLM_TARGET_BBOX, COLORS["original"])
    vlm_b = base._bbox_image(base.VLM_CONVERTED, base.VLM_TARGET_BBOX, COLORS["converted"])
    material_images = [
        base._material_image(case, records, condition)
        for condition in (
            "original_MDL",
            "existing_noMDL",
            "nvidia_asset_converter_preview_or_bake",
        )
    ]
    cards = (
        ("1", "Proxy", "24 matched pairs", "visual/feature proxy only", (base.OBJECT_ORIGINAL, base.OBJECT_CONVERTED), (COLORS["original"], COLORS["converted"])),
        ("2", "VLM", "15 clean + 30 stress", "fixed prompts; selected targets", (vlm_a, vlm_b), (COLORS["original"], COLORS["converted"])),
        ("3", "Material", "selected covered bins", "case audit; not failure rate", tuple(material_images), (COLORS["original"], COLORS["converted"], COLORS["nvidia"])),
        ("4", "Stack", "99 paired episodes", "entry check; not robustness", (base._nav_still("597_597", "original", "start"), base._nav_still("597_597", "nomdl", "end")), (COLORS["original"], COLORS["converted"])),
    )
    for x, values in zip(xs, cards):
        _evidence_card(fig, rect=(x, 0.04, width, 0.92), number=values[0], title=values[1], evidence=values[2], boundary=values[3], images=values[4], borders=values[5])
    return _save_bundle(fig, _output_stem("table1", output_dir))


def _condition_header(fig: plt.Figure, x: float, y: float, w: float, text: str, color: str) -> None:
    _fig_patch(fig, Rectangle((x, y), w, 0.05, facecolor=color, edgecolor="none"), zorder=-8)
    fig.text(x + w / 2, y + 0.025, text, ha="center", va="center", color="white", fontsize=7.2, fontweight="bold")


def build_fig2(output_dir: Path) -> list[Path]:
    fig = plt.figure(figsize=(7.2, 3.05), facecolor="white")
    left, right, width = 0.075, 0.525, 0.405
    _condition_header(fig, left, 0.91, width, "Original MDL", COLORS["original"])
    _condition_header(fig, right, 0.91, width, "noMDL", COLORS["converted"])
    fig.text(0.015, 0.83, "a", fontsize=8.0, fontweight="bold", color=COLORS["structure"])
    fig.text(0.035, 0.83, "Proxy object pair", fontsize=7.2, fontweight="bold", color=COLORS["ink"])
    base._add_image(fig, (left, 0.54, width, 0.32), base.OBJECT_ORIGINAL, crop=base.OBJECT_CROP, border=COLORS["original"], linewidth=0.9)
    base._add_image(fig, (right, 0.54, width, 0.32), base.OBJECT_CONVERTED, crop=base.OBJECT_CROP, border=COLORS["converted"], linewidth=0.9)
    fig.text(0.015, 0.44, "b", fontsize=8.0, fontweight="bold", color=COLORS["structure"])
    fig.text(0.035, 0.44, "GRScenes scene pair", fontsize=7.2, fontweight="bold", color=COLORS["ink"])
    base._add_image(fig, (left, 0.06, width, 0.34), base.SCENE_ORIGINAL, border=COLORS["original"], linewidth=0.9)
    base._add_image(fig, (right, 0.06, width, 0.34), base.SCENE_CONVERTED, border=COLORS["converted"], linewidth=0.9)
    return _save_bundle(fig, _output_stem("fig2", output_dir))


def build_fig3(output_dir: Path) -> list[Path]:
    selected, records = base._material_records()
    fig = plt.figure(figsize=(7.2, 3.15), facecolor="white")
    col_x = (0.14, 0.425, 0.71)
    col_w = 0.27
    headers = (
        ("Original MDL", COLORS["original"]),
        ("ConvertAsset noMDL", COLORS["converted"]),
        ("NVIDIA", COLORS["nvidia"]),
    )
    for x, (title, color) in zip(col_x, headers):
        _condition_header(fig, x, 0.925, col_w, title, color)
    row_y = (0.72, 0.505, 0.29, 0.075)
    row_h = 0.18
    conditions = (
        "original_MDL",
        "existing_noMDL",
        "nvidia_asset_converter_preview_or_bake",
    )
    for index, (case, y) in enumerate(zip(selected, row_y)):
        fig.text(0.018, y + row_h / 2, chr(ord("a") + index), fontsize=7.5, fontweight="bold", color=COLORS["structure"], va="center")
        fig.text(0.048, y + row_h / 2, str(case["target_category"]).capitalize(), fontsize=7.2, fontweight="bold", color=COLORS["ink"], va="center")
        for x, condition, (_, border) in zip(col_x, conditions, headers):
            base._add_image(fig, (x, y, col_w, row_h), base._material_image(case, records, condition), border=border, linewidth=0.8)
    return _save_bundle(fig, _output_stem("fig3", output_dir))


def build_fig4(output_dir: Path) -> list[Path]:
    cases = base._nav_case_map()
    fig = plt.figure(figsize=(7.2, 2.75), facecolor="white")
    col_x = (0.145, 0.355, 0.565, 0.775)
    col_w = 0.20
    columns = (
        ("Original start", COLORS["original"], "original", "start"),
        ("Original end", COLORS["original"], "original", "end"),
        ("noMDL start", COLORS["converted"], "nomdl", "start"),
        ("noMDL end", COLORS["converted"], "nomdl", "end"),
    )
    for x, (title, color, _, _) in zip(col_x, columns):
        _condition_header(fig, x, 0.91, col_w, title, color)
    fig.text(0.015, 0.955, "● executed", color=COLORS["trajectory"], fontsize=6.0, fontweight="bold")
    fig.text(0.015, 0.918, "● reference", color=COLORS["pass"], fontsize=6.0, fontweight="bold")
    row_y = (0.615, 0.335, 0.055)
    row_h = 0.235
    for row_index, (case_key, y) in enumerate(zip(base.NAV_CASES, row_y)):
        case = cases[case_key]
        case_type, sr = base._case_summary(case)
        short_type = {
            "both success divergent": "both success",
            "original only success": "original only",
            "modified only success": "noMDL only",
        }.get(case_type, case_type)
        score = sr.replace("SR O/N ", "")
        label = f"{case_key}\n{short_type} · {score}"
        fig.text(0.018, y + row_h / 2, chr(ord("a") + row_index), fontsize=7.5, fontweight="bold", color=COLORS["structure"], va="center")
        fig.text(0.048, y + row_h / 2, label, fontsize=6.1, color=COLORS["ink"], va="center", linespacing=1.45)
        for x, (_, border, condition, moment) in zip(col_x, columns):
            base._add_image(fig, (x, y, col_w, row_h), base._nav_still(case_key, condition, moment), border=border, linewidth=0.8)
    return _save_bundle(fig, _output_stem("fig4", output_dir))


def _quick_card(
    fig: plt.Figure,
    *,
    y: float,
    number: str,
    title: str,
    note: str,
    destination: str,
    images: Iterable[Image.Image | Path],
    borders: Iterable[str],
) -> None:
    x, w, h = 0.04, 0.92, 0.19
    _fig_patch(
        fig,
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.004,rounding_size=0.012",
            facecolor="white",
            edgecolor=COLORS["line"],
            linewidth=0.8,
        ),
    )
    _fig_patch(
        fig,
        Rectangle((x, y), 0.012, h, facecolor=COLORS["structure"], edgecolor="none"),
        zorder=-8,
    )
    image_list = list(images)
    border_list = list(borders)
    gap = 0.008
    image_w = (0.40 - gap * (len(image_list) - 1)) / len(image_list)
    for index, image in enumerate(image_list):
        base._add_image(
            fig,
            (x + 0.03 + index * (image_w + gap), y + 0.025, image_w, h - 0.05),
            image,
            border=border_list[index],
            linewidth=0.7,
        )
    fig.text(x + 0.47, y + h - 0.048, f"{number}  {title}", fontsize=7.5, fontweight="bold", color=COLORS["ink"], va="center")
    fig.text(x + 0.47, y + 0.077, note, fontsize=6.2, color=COLORS["muted"], va="center")
    fig.text(x + 0.47, y + 0.028, destination, fontsize=6.0, fontweight="bold", color=COLORS["structure"], va="center")


def build_quickstart(output_dir: Path) -> list[Path]:
    selected, records = base._material_records()
    case = selected[0]
    fig = plt.figure(figsize=(3.45, 5.0), facecolor="white")
    fig.text(0.04, 0.965, "Evidence quickstart", fontsize=10.0, fontweight="bold", color=COLORS["ink"], va="top")
    fig.text(0.04, 0.925, "Four checks, four distinct evidence surfaces", fontsize=6.5, color=COLORS["muted"], va="top")
    vlm_a = base._bbox_image(base.VLM_ORIGINAL, base.VLM_TARGET_BBOX, COLORS["original"])
    vlm_b = base._bbox_image(base.VLM_CONVERTED, base.VLM_TARGET_BBOX, COLORS["converted"])
    material_images = [
        base._material_image(case, records, condition)
        for condition in ("original_MDL", "existing_noMDL", "nvidia_asset_converter_preview_or_bake")
    ]
    _quick_card(fig, y=0.70, number="1", title="Proxy", note="matched object and scene renders", destination="render atlas + proxy metrics", images=(base.OBJECT_ORIGINAL, base.OBJECT_CONVERTED), borders=(COLORS["original"], COLORS["converted"]))
    _quick_card(fig, y=0.49, number="2", title="VLM grounding", note="target box and point contract", destination="coordinate protocol + stress tables", images=(vlm_a, vlm_b), borders=(COLORS["original"], COLORS["converted"]))
    _quick_card(fig, y=0.28, number="3", title="Material audit", note="selected bins across three routes", destination="material diagnostics + risk matrix", images=tuple(material_images), borders=(COLORS["original"], COLORS["converted"], COLORS["nvidia"]))
    _quick_card(fig, y=0.07, number="4", title="Stack entry", note="selected official InternNav views", destination="paired summary + case pages", images=(base._nav_still("597_597", "original", "start"), base._nav_still("597_597", "nomdl", "end")), borders=(COLORS["original"], COLORS["converted"]))
    return _save_bundle(fig, _output_stem("quickstart", output_dir))


def build_vlm_atlas(output_dir: Path) -> list[Path]:
    fig = plt.figure(figsize=(7.2, 5.25), facecolor="white")
    fig.text(0.025, 0.97, "VLM coordinate protocol", fontsize=10.0, fontweight="bold", color=COLORS["ink"], va="top")
    fig.text(0.025, 0.925, "same image · three coordinate objects", fontsize=6.5, color=COLORS["muted"], va="top")
    legend = (
        (COLORS["pass"], "target box"),
        (COLORS["structure"], "raw image center"),
        (COLORS["converted"], "normalized bbox center"),
    )
    for index, (color, label) in enumerate(legend):
        x = 0.34 + index * 0.205
        _fig_patch(fig, Circle((x, 0.94), 0.008, facecolor=color, edgecolor="none"), zorder=3)
        fig.text(x + 0.014, 0.94, label, fontsize=6.3, color=COLORS["ink"], va="center")
    _fig_patch(fig, FancyBboxPatch((0.81, 0.10), 0.16, 0.79, boxstyle="round,pad=0.003,rounding_size=0.008", facecolor="white", edgecolor=COLORS["line"], linewidth=0.7), zorder=-4)
    fig.text(0.89, 0.79, "Scored separately", fontsize=7.0, fontweight="bold", color=COLORS["structure"], ha="center")
    fig.text(0.84, 0.68, "answer", fontsize=6.3, fontweight="bold", color=COLORS["ink"])
    fig.text(0.84, 0.61, "parseable point", fontsize=6.3, fontweight="bold", color=COLORS["ink"])
    fig.text(0.84, 0.54, "point inside box", fontsize=6.3, fontweight="bold", color=COLORS["ink"])
    fig.text(0.89, 0.26, "raw px", fontsize=6.3, color=COLORS["structure"], ha="center")
    fig.text(0.89, 0.21, "↓ normalize", fontsize=6.3, color=COLORS["muted"], ha="center")
    fig.text(0.89, 0.16, "[0, 1000]", fontsize=6.3, color=COLORS["converted"], ha="center")

    row_y = (0.65, 0.37, 0.09)
    for case, y in zip(VLM_CASES, row_y):
        original, converted = _vlm_paths(case)
        _fig_patch(fig, FancyBboxPatch((0.025, y), 0.95, 0.245, boxstyle="round,pad=0.003,rounding_size=0.008", facecolor=COLORS["soft"], edgecolor=COLORS["line"], linewidth=0.7))
        fig.text(0.04, y + 0.19, case["name"], fontsize=7.5, fontweight="bold", color=COLORS["ink"])
        fig.text(0.04, y + 0.12, case["note"], fontsize=6.0, color=COLORS["muted"], va="center", linespacing=1.25)
        base._add_image(fig, (0.19, y + 0.025, 0.29, 0.19), _protocol_overlay(original, case["bbox"]), border=COLORS["original"], linewidth=0.8)
        base._add_image(fig, (0.50, y + 0.025, 0.29, 0.19), _protocol_overlay(converted, case["bbox"]), border=COLORS["converted"], linewidth=0.8)
        fig.text(0.335, y + 0.218, "Original MDL", fontsize=6.2, color=COLORS["original"], ha="center")
        fig.text(0.645, y + 0.218, "noMDL", fontsize=6.2, color=COLORS["converted"], ha="center")
    return _save_bundle(fig, _output_stem("vlm", output_dir))


def build_material_atlas(output_dir: Path) -> list[Path]:
    selected, records = base._material_records()
    limit_cases, limit_records = _supplemental_material_records()
    fig = plt.figure(figsize=(7.2, 7.4), facecolor="white")
    fig.text(0.02, 0.975, "Material diagnostics", fontsize=10.0, fontweight="bold", color=COLORS["ink"], va="top")
    fig.text(0.02, 0.94, "Covered bins", fontsize=7.5, fontweight="bold", color=COLORS["structure"], va="top")
    col_x = (0.17, 0.44, 0.71)
    col_w = 0.255
    headers = (
        ("Original MDL", COLORS["original"]),
        ("ConvertAsset noMDL", COLORS["converted"]),
        ("NVIDIA", COLORS["nvidia"]),
    )
    for x, (title, color) in zip(col_x, headers):
        _condition_header(fig, x, 0.885, col_w, title, color)
    conditions = ("original_MDL", "existing_noMDL", "nvidia_asset_converter_preview_or_bake")
    row_y = (0.745, 0.625, 0.505, 0.385)
    row_h = 0.095
    for index, (case, y) in enumerate(zip(selected, row_y)):
        fig.text(0.025, y + row_h / 2, chr(ord("a") + index), fontsize=7.0, fontweight="bold", color=COLORS["structure"], va="center")
        fig.text(0.055, y + row_h / 2, str(case["target_category"]).capitalize(), fontsize=6.7, fontweight="bold", color=COLORS["ink"], va="center")
        for x, condition, (_, border) in zip(col_x, conditions, headers):
            base._add_image(fig, (x, y, col_w, row_h), base._material_image(case, records, condition), border=border, linewidth=0.7)

    fig.text(0.02, 0.335, "LIMITATION CASES", fontsize=7.0, fontweight="bold", color=COLORS["converted"], va="top")
    for x, (title, color) in zip(col_x, headers):
        _condition_header(fig, x, 0.285, col_w, title, color)
    limit_y = (0.155, 0.025)
    for index, (case, y) in enumerate(zip(limit_cases, limit_y)):
        effects = case.get("covered_effects") or []
        label = str(effects[0]).replace("_", "\n") if effects else str(case["sample_id"])
        fig.text(0.025, y + 0.05, chr(ord("e") + index), fontsize=7.0, fontweight="bold", color=COLORS["converted"], va="center")
        fig.text(0.055, y + 0.05, label, fontsize=6.7, fontweight="bold", color=COLORS["ink"], va="center")
        for x, condition, (_, border) in zip(col_x, conditions, headers):
            path = limit_records[(str(case["sample_id"]), condition)]
            base._add_image(fig, (x, y, col_w, 0.10), path, border=border, linewidth=0.7)
    return _save_bundle(fig, _output_stem("material", output_dir))


def build_navigation_atlas(output_dir: Path) -> list[Path]:
    cases = base._nav_case_map()
    fig = plt.figure(figsize=(7.2, 7.0), facecolor="white")
    fig.text(0.025, 0.975, "InternNav evidence map", fontsize=10.0, fontweight="bold", color=COLORS["ink"], va="top")
    fig.text(0.025, 0.94, "paired summary, one route witness, and selected asymmetric endpoints", fontsize=6.5, color=COLORS["muted"], va="top")
    _add_full_image(fig, (0.04, 0.62, 0.92, 0.27), NAV_SUMMARY, border=COLORS["line"])

    fig.text(0.025, 0.585, "Route witness · 597_597 · both success", fontsize=7.5, fontweight="bold", color=COLORS["ink"])
    columns = (
        ("Original start", COLORS["original"], "original", "start"),
        ("Original end", COLORS["original"], "original", "end"),
        ("noMDL start", COLORS["converted"], "nomdl", "start"),
        ("noMDL end", COLORS["converted"], "nomdl", "end"),
    )
    col_x = (0.04, 0.275, 0.51, 0.745)
    for x, (title, color, condition, moment) in zip(col_x, columns):
        _condition_header(fig, x, 0.535, 0.215, title, color)
        base._add_image(fig, (x, 0.37, 0.215, 0.15), base._nav_still("597_597", condition, moment), border=color, linewidth=0.8)

    fig.text(0.025, 0.325, "Selected asymmetric endpoints", fontsize=7.5, fontweight="bold", color=COLORS["ink"])
    for case_key, y in (("898_898", 0.18), ("919_919", 0.035)):
        case_type, sr = base._case_summary(cases[case_key])
        fig.text(0.04, y + 0.055, f"{case_key}\n{case_type}\n{sr}", fontsize=6.2, color=COLORS["ink"], va="center", linespacing=1.4)
        base._add_image(fig, (0.23, y, 0.34, 0.11), base._nav_still(case_key, "original", "end"), border=COLORS["original"], linewidth=0.8)
        base._add_image(fig, (0.61, y, 0.34, 0.11), base._nav_still(case_key, "nomdl", "end"), border=COLORS["converted"], linewidth=0.8)
        fig.text(0.40, y + 0.115, "Original end", fontsize=6.0, color=COLORS["original"], ha="center")
        fig.text(0.78, y + 0.115, "noMDL end", fontsize=6.0, color=COLORS["converted"], ha="center")
    return _save_bundle(fig, _output_stem("nav", output_dir))


BUILDERS = {
    "fig1": build_fig1,
    "table1": build_table1,
    "fig2": build_fig2,
    "fig3": build_fig3,
    "fig4": build_fig4,
    "quickstart": build_quickstart,
    "vlm": build_vlm_atlas,
    "material": build_material_atlas,
    "nav": build_navigation_atlas,
}
MAIN_TARGETS = ("fig1", "table1", "fig2", "fig3", "fig4")
SUPPLEMENT_TARGETS = ("quickstart", "vlm", "material", "nav")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=(*BUILDERS, "main", "supplement", "all", "components"),
        default="all",
    )
    parser.add_argument("--output-dir", type=Path, default=FIG_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    apply_style()
    if args.target == "components":
        print(json.dumps(prepare_material_components(), indent=2, sort_keys=True))
        return 0
    targets = (
        (*MAIN_TARGETS, *SUPPLEMENT_TARGETS)
        if args.target == "all"
        else MAIN_TARGETS
        if args.target == "main"
        else SUPPLEMENT_TARGETS
        if args.target == "supplement"
        else (args.target,)
    )
    output_dir = args.output_dir.resolve()
    report: dict[str, list[str]] = {}
    for target in targets:
        report[target] = [str(path) for path in BUILDERS[target](output_dir)]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
