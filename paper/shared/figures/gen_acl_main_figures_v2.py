#!/usr/bin/env python3
"""Generate the ACL main-paper visual system with Python/Matplotlib.

The script reads existing evidence artifacts without modifying them and emits
versioned SVG, PDF, and PNG bundles for the five visual assets used by the ACL
main manuscript.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = ROOT / "paper/shared/figures"
RAW_DIR = ROOT / "paper/shared/evidence/raw"
SPEC_PATH = FIG_DIR / "specs/fig_acl_method_chain_v2.spec.json"

OUTPUTS = {
    "fig1": FIG_DIR / "fig_acl_method_chain_v2",
    "table1": FIG_DIR / "fig_acl_evidence_registry_strip_v1",
    "fig2": FIG_DIR / "fig_render_scene_evidence_wide_v2",
    "fig3": FIG_DIR / "fig_material_effect_baseline_qualitative_v2",
    "fig4": FIG_DIR / "fig_internnav_rollout_main_v2",
}

COLORS = {
    "structure": "#0F4D92",
    "structure_mid": "#3775BA",
    "structure_soft": "#EAF1F8",
    "original": "#0F4D92",
    "converted": "#E67E22",
    "converted_soft": "#FCEBDD",
    "pass": "#168A45",
    "pass_soft": "#E9F5ED",
    "trajectory": "#7A40C8",
    "nvidia": "#6B7280",
    "ink": "#1F2933",
    "muted": "#5B6573",
    "line": "#C9D2DC",
    "soft": "#F4F7FB",
    "white": "#FFFFFF",
    "danger": "#C43D3D",
}

OBJECT_ORIGINAL = RAW_DIR / "renders/chestofdrawers_0011/A_top_front_right.png"
OBJECT_CONVERTED = RAW_DIR / "renders/chestofdrawers_0011/B_top_front_right.png"
OBJECT_CROP = (250, 80, 730, 650)
SCENE_ORIGINAL = FIG_DIR / "out_tmp/mdl_images/orbit_mdl_01.png"
SCENE_CONVERTED = FIG_DIR / "out_tmp/nomdl_images/orbit_01.png"
VLM_ORIGINAL = (
    RAW_DIR
    / "grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd"
    / "47aa36277a54f6ca90cc/zoom_018/original/original_0000.png"
)
VLM_CONVERTED = (
    RAW_DIR
    / "grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd"
    / "47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png"
)
VLM_TARGET_BBOX = (207.811, 105.285, 376.441, 364.938)
MATERIAL_MANIFEST = RAW_DIR / "material_effect_baseline/qualitative_render_manifest.json"
NAV_ROOT = (
    RAW_DIR
    / "internnav_vln_downstream/official_selected_qualitative_videos"
)
NAV_CASE_MANIFEST = NAV_ROOT / "manifests/kujiale0036_0066_video_case_manifest.json"
NAV_STILL_ROOT = NAV_ROOT / "stills/kujiale0036_0066"
NAV_CASES = ("597_597", "898_898", "919_919")


def apply_publication_style() -> None:
    """Apply the manuscript-wide Python figure style."""

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 7,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


def _repo_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        return ROOT / path
    parts = path.parts
    if "paper" in parts:
        return ROOT / Path(*parts[parts.index("paper") :])
    return path


def _read_image(path: str | Path) -> Image.Image:
    resolved = _repo_path(path)
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return Image.open(resolved).convert("RGB")


def _cover_array(
    path_or_image: str | Path | Image.Image,
    aspect: float,
    *,
    crop: tuple[float, float, float, float] | None = None,
) -> np.ndarray:
    image = _read_image(path_or_image) if not isinstance(path_or_image, Image.Image) else path_or_image.convert("RGB")
    if crop is not None:
        image = image.crop(tuple(int(round(value)) for value in crop))
    width, height = image.size
    current = width / height
    if current > aspect:
        new_width = int(round(height * aspect))
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    elif current < aspect:
        new_height = int(round(width / aspect))
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))
    return np.asarray(image)


def _bbox_image(path: Path, bbox: tuple[float, float, float, float], color: str) -> Image.Image:
    image = _read_image(path)
    draw = ImageDraw.Draw(image)
    width = max(3, int(round(image.width / 180)))
    draw.rectangle(tuple(int(round(value)) for value in bbox), outline=color, width=width)
    return image


def _recolor_navigation_overlay(image: Image.Image) -> Image.Image:
    data = np.asarray(image.convert("RGB")).copy()
    red = (
        (data[:, :, 0] >= 150)
        & (data[:, :, 1] <= 120)
        & (data[:, :, 2] <= 120)
        & (data[:, :, 0] >= data[:, :, 1] + 70)
        & (data[:, :, 0] >= data[:, :, 2] + 70)
    )
    data[red] = np.array([122, 64, 200], dtype=np.uint8)
    return Image.fromarray(data)


def _add_image(
    fig: plt.Figure,
    rect: tuple[float, float, float, float],
    path_or_image: str | Path | Image.Image,
    *,
    crop: tuple[float, float, float, float] | None = None,
    border: str = COLORS["line"],
    linewidth: float = 0.6,
) -> plt.Axes:
    ax = fig.add_axes(rect)
    physical_aspect = (rect[2] * fig.get_figwidth()) / (rect[3] * fig.get_figheight())
    ax.imshow(_cover_array(path_or_image, physical_aspect, crop=crop), interpolation="lanczos")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(border)
        spine.set_linewidth(linewidth)
    return ax


def _figure_patch(fig: plt.Figure, patch: Any, *, zorder: float = -10) -> None:
    patch.set_transform(fig.transFigure)
    patch.set_clip_on(False)
    patch.set_zorder(zorder)
    fig.patches.append(patch)


def _panel(
    fig: plt.Figure,
    rect: tuple[float, float, float, float],
    title: str,
    *,
    accent: str = COLORS["structure"],
    face: str = COLORS["soft"],
    subtitle: str | None = None,
    title_size: float = 9.0,
    header_fraction: float = 0.105,
) -> None:
    x, y, w, h = rect
    _figure_patch(
        fig,
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.004,rounding_size=0.012",
            facecolor=face,
            edgecolor=accent,
            linewidth=1.1,
        ),
    )
    header_h = h * header_fraction
    _figure_patch(fig, Rectangle((x, y + h - header_h), w, header_h, facecolor=accent, edgecolor="none"), zorder=-9)
    fig.text(x + 0.012, y + h - header_h / 2, title, color="white", fontsize=title_size, fontweight="bold", va="center")
    if subtitle:
        fig.text(x + w - 0.012, y + h - header_h / 2, subtitle, color="white", fontsize=5.6, va="center", ha="right")


def _arrow(
    fig: plt.Figure,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str,
    linestyle: str = "-",
    width: float = 1.4,
    mutation_scale: float = 9,
) -> None:
    _figure_patch(
        fig,
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            linewidth=width,
            linestyle=linestyle,
            color=color,
            shrinkA=0,
            shrinkB=0,
        ),
        zorder=5,
    )


def _save_bundle(fig: plt.Figure, stem: Path, *, dpi: int = 300) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = [stem.with_suffix(suffix) for suffix in (".svg", ".pdf", ".png")]
    fig.savefig(outputs[0], dpi=dpi, facecolor="white")
    fig.savefig(outputs[1], dpi=dpi, facecolor="white", metadata={"Creator": "Python/Matplotlib"})
    fig.savefig(outputs[2], dpi=dpi, facecolor="white")
    plt.close(fig)
    return outputs


def _material_records() -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    manifest = json.loads(MATERIAL_MANIFEST.read_text(encoding="utf-8"))
    selected = list(manifest["selected_cases"])
    records = {
        (str(record["sample_id"]), str(record["condition"])): record
        for record in manifest["records"]
        if (record.get("image") or {}).get("status") == "ready"
    }
    return selected, records


def _material_image(
    case: dict[str, Any],
    records: dict[tuple[str, str], dict[str, Any]],
    condition: str,
) -> Path:
    record = records[(str(case["sample_id"]), condition)]
    return _repo_path(record["image"]["path"])


def _nav_case_map() -> dict[str, dict[str, Any]]:
    manifest = json.loads(NAV_CASE_MANIFEST.read_text(encoding="utf-8"))
    return {str(case["path_key"]): case for case in manifest["selected_cases"]}


def _nav_still(case_key: str, condition: str, moment: str) -> Image.Image:
    matches = sorted(NAV_STILL_ROOT.glob(f"kujiale0036_0066_{case_key}_{condition}_{moment}_*.png"))
    if not matches:
        raise FileNotFoundError(f"missing InternNav still: {case_key} {condition} {moment}")
    return _recolor_navigation_overlay(_read_image(matches[0]))


def validate_figure1_spec() -> dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if not spec.get("review", {}).get("semantic_graph_approved"):
        raise ValueError("Figure 1 semantic graph is not approved")
    panel_ids = {panel["id"] for panel in spec["panels"]}
    port_ids = {port["id"] for port in spec["ports"]}
    if len(panel_ids) != len(spec["panels"]) or len(port_ids) != len(spec["ports"]):
        raise ValueError("Figure 1 spec contains duplicate semantic ids")
    for port in spec["ports"]:
        if port.get("owner") not in panel_ids:
            raise ValueError(f"unknown port owner: {port}")
    for edge in spec["edges"]:
        if edge["from"] not in port_ids or edge["to"] not in port_ids:
            raise ValueError(f"unknown edge endpoint: {edge}")
    expected_gate_edges = {
        "matched-to-proxy",
        "matched-to-vlm",
        "matched-to-material",
        "matched-to-stack",
    }
    actual = {edge["id"] for edge in spec["edges"]}
    if not expected_gate_edges <= actual:
        raise ValueError("Figure 1 must fan matched evidence into four parallel gates")
    for asset in spec.get("assets", []):
        source = (SPEC_PATH.parent / asset["path"]).resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
    return spec


def _draw_tree(ax: plt.Axes, x: float, y: float, scale: float, color: str) -> None:
    nodes = [(x, y), (x - 0.13 * scale, y - 0.20 * scale), (x + 0.13 * scale, y - 0.20 * scale), (x - 0.19 * scale, y - 0.40 * scale), (x - 0.05 * scale, y - 0.40 * scale), (x + 0.18 * scale, y - 0.40 * scale)]
    for a, b in ((0, 1), (0, 2), (1, 3), (1, 4), (2, 5)):
        ax.plot([nodes[a][0], nodes[b][0]], [nodes[a][1], nodes[b][1]], color=color, lw=1.2)
    for index, (nx, ny) in enumerate(nodes):
        face = COLORS["pass_soft"] if index > 0 and color == COLORS["converted"] else "white"
        ax.add_patch(Rectangle((nx - 0.035 * scale, ny - 0.035 * scale), 0.07 * scale, 0.07 * scale, facecolor=face, edgecolor=color, lw=1.0))


def build_fig1() -> list[Path]:
    validate_figure1_spec()
    selected, records = _material_records()
    material_case = selected[0]
    fig = plt.figure(figsize=(7.2, 3.6), facecolor="white")

    source = (0.015, 0.055, 0.185, 0.89)
    conversion = (0.225, 0.055, 0.405, 0.89)
    gates = (0.665, 0.055, 0.32, 0.89)
    _panel(fig, source, "Source assets")
    _panel(fig, conversion, "Controlled perturbation", subtitle="composition preserved")
    _panel(fig, gates, "Bounded evaluation gates", title_size=8.5)

    ax_source = fig.add_axes((0.032, 0.66, 0.15, 0.18))
    ax_source.set_xlim(0, 1)
    ax_source.set_ylim(0, 1)
    ax_source.axis("off")
    ax_source.add_patch(FancyBboxPatch((0.02, 0.13), 0.32, 0.72, boxstyle="round,pad=0.02", facecolor="white", edgecolor=COLORS["structure"], lw=1.4))
    ax_source.text(0.18, 0.48, ".usd", ha="center", va="center", fontsize=10, fontweight="bold", color=COLORS["ink"])
    _draw_tree(ax_source, 0.70, 0.78, 1.1, COLORS["structure"])
    ax_source.text(0.52, 0.02, "composed scene hierarchy", fontsize=5.7, color=COLORS["muted"], ha="center")

    _add_image(fig, (0.032, 0.37, 0.15, 0.25), SCENE_ORIGINAL, border=COLORS["structure_mid"])
    fig.text(0.036, 0.595, "representative source view", fontsize=5.6, color="white", bbox={"facecolor": COLORS["structure"], "edgecolor": "none", "pad": 1.5})
    swatch_ax = fig.add_axes((0.032, 0.105, 0.15, 0.20))
    swatch_ax.set_xlim(0, 1)
    swatch_ax.set_ylim(0, 1)
    swatch_ax.axis("off")
    swatches = ["#7B4D27", "#292929", "#E9E4D8", "#777777"]
    for index, color in enumerate(swatches):
        cx = 0.14 + index * 0.24
        swatch_ax.add_patch(Circle((cx, 0.58), 0.105, facecolor=color, edgecolor="#4A4A4A", lw=0.6))
        swatch_ax.add_patch(Circle((cx - 0.035, 0.62), 0.025, facecolor="white", edgecolor="none", alpha=0.8))
    swatch_ax.text(0.5, 0.20, "MDL material cues", ha="center", fontsize=6.4, fontweight="bold", color=COLORS["ink"])

    conv_ax = fig.add_axes((0.248, 0.59, 0.36, 0.24))
    conv_ax.set_xlim(0, 1)
    conv_ax.set_ylim(0, 1)
    conv_ax.axis("off")
    _draw_tree(conv_ax, 0.18, 0.78, 1.0, COLORS["original"])
    _draw_tree(conv_ax, 0.82, 0.78, 1.0, COLORS["converted"])
    conv_ax.annotate("", xy=(0.64, 0.58), xytext=(0.36, 0.58), arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": COLORS["structure"]})
    conv_ax.text(0.18, 0.14, "source USD", ha="center", fontsize=7.2, fontweight="bold", color=COLORS["original"])
    conv_ax.text(0.82, 0.14, "noMDL USD", ha="center", fontsize=7.2, fontweight="bold", color=COLORS["converted"])
    conv_ax.text(0.50, 0.83, "rewrite materials + composition paths", ha="center", fontsize=7.0, fontweight="bold", color=COLORS["ink"])
    conv_ax.text(0.50, 0.02, "references retained  ·  paths rewritten  ·  materials converted", ha="center", fontsize=5.7, color=COLORS["pass"])

    fig.text(0.25, 0.545, "Matched evidence", fontsize=7.7, fontweight="bold", color=COLORS["ink"])
    _add_image(fig, (0.248, 0.18, 0.165, 0.33), SCENE_ORIGINAL, border=COLORS["original"], linewidth=1.0)
    _add_image(fig, (0.445, 0.18, 0.165, 0.33), SCENE_CONVERTED, border=COLORS["converted"], linewidth=1.0)
    fig.text(0.3305, 0.145, "Original MDL", ha="center", fontsize=6.7, fontweight="bold", color=COLORS["original"])
    fig.text(0.5275, 0.145, "noMDL", ha="center", fontsize=6.7, fontweight="bold", color=COLORS["converted"])
    _arrow(fig, (0.416, 0.345), (0.442, 0.345), color=COLORS["structure"], width=1.3)
    fig.text(0.429, 0.115, "same scene · paired view", ha="center", fontsize=5.6, color=COLORS["muted"])

    _arrow(fig, (0.202, 0.50), (0.222, 0.50), color=COLORS["structure"], width=1.6)
    _arrow(fig, (0.427, 0.575), (0.427, 0.525), color=COLORS["structure"], width=1.5)

    gate_x, gate_w = 0.687, 0.276
    gate_h = 0.168
    gate_ys = [0.665, 0.467, 0.269, 0.071]
    gate_defs = [
        ("1  Proxy similarity", "pixel + feature similarity", COLORS["structure"]),
        ("2  VLM grounding", "answer + point\nsame target contract", COLORS["structure"]),
        ("3  Material audit", "selected cases across 3 routes", COLORS["structure"]),
        ("4  Stack entry", "InternNav views\nSR · SPL · NE", COLORS["structure"]),
    ]
    for y, (title, note, accent) in zip(gate_ys, gate_defs):
        _figure_patch(fig, FancyBboxPatch((gate_x, y), gate_w, gate_h, boxstyle="round,pad=0.003,rounding_size=0.008", facecolor="white", edgecolor=COLORS["line"], linewidth=0.8))
        _figure_patch(fig, Rectangle((gate_x, y), 0.008, gate_h, facecolor=accent, edgecolor="none"), zorder=-9)
        fig.text(gate_x + 0.108, y + gate_h - 0.045, title, fontsize=6.8, fontweight="bold", color=COLORS["ink"], va="center")
        fig.text(gate_x + 0.108, y + 0.026, note, fontsize=5.15, color=COLORS["muted"], va="bottom", linespacing=1.1)

    _add_image(fig, (gate_x + 0.016, gate_ys[0] + 0.027, 0.078, 0.118), OBJECT_ORIGINAL, crop=OBJECT_CROP, border=COLORS["original"])
    vlm_preview = _bbox_image(VLM_ORIGINAL, VLM_TARGET_BBOX, COLORS["converted"])
    _add_image(fig, (gate_x + 0.016, gate_ys[1] + 0.027, 0.078, 0.118), vlm_preview, crop=(150, 65, 435, 405), border=COLORS["converted"])
    material_paths = [_material_image(material_case, records, cond) for cond in ("original_MDL", "existing_noMDL", "nvidia_asset_converter_preview_or_bake")]
    for index, path in enumerate(material_paths):
        _add_image(fig, (gate_x + 0.014 + index * 0.028, gate_ys[2] + 0.045, 0.027, 0.082), path, border=(COLORS["original"], COLORS["converted"], COLORS["nvidia"])[index], linewidth=0.5)
    nav_preview = _nav_still("597_597", "nomdl", "end")
    _add_image(fig, (gate_x + 0.016, gate_ys[3] + 0.027, 0.078, 0.118), nav_preview, border=COLORS["trajectory"])

    bus_x = 0.651
    _figure_patch(fig, Rectangle((bus_x, 0.145), 0.0018, 0.59, facecolor=COLORS["converted"], edgecolor="none"), zorder=4)
    _arrow(fig, (0.612, 0.345), (bus_x, 0.345), color=COLORS["converted"], linestyle="--", width=1.2)
    for y in gate_ys:
        gate_mid = y + gate_h / 2
        _arrow(fig, (bus_x, gate_mid), (gate_x - 0.006, gate_mid), color=COLORS["converted"], linestyle="--", width=1.1, mutation_scale=7)

    return _save_bundle(fig, OUTPUTS["fig1"])


def _strip_card(
    fig: plt.Figure,
    rect: tuple[float, float, float, float],
    *,
    index: str,
    title: str,
    evidence: str,
    boundary: str,
    images: Iterable[str | Path | Image.Image],
    borders: Iterable[str],
) -> None:
    x, y, w, h = rect
    _figure_patch(fig, FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.003,rounding_size=0.009", facecolor="white", edgecolor=COLORS["line"], linewidth=0.8))
    _figure_patch(fig, Rectangle((x, y + h - 0.075), w, 0.075, facecolor=COLORS["structure"], edgecolor="none"), zorder=-9)
    fig.text(x + 0.012, y + h - 0.037, index, color="white", fontsize=7.4, fontweight="bold", va="center")
    fig.text(x + 0.037, y + h - 0.037, title, color="white", fontsize=7.2, fontweight="bold", va="center")
    image_list = list(images)
    border_list = list(borders)
    image_gap = 0.006
    image_w = (w - 0.024 - image_gap * (len(image_list) - 1)) / len(image_list)
    for idx, image in enumerate(image_list):
        _add_image(fig, (x + 0.012 + idx * (image_w + image_gap), y + 0.185, image_w, h - 0.285), image, border=border_list[idx], linewidth=0.7)
    fig.text(x + 0.012, y + 0.135, evidence, fontsize=5.55, color=COLORS["ink"], fontweight="bold")
    fig.text(x + 0.012, y + 0.047, boundary, fontsize=5.25, color=COLORS["muted"], bbox={"facecolor": COLORS["soft"], "edgecolor": COLORS["line"], "boxstyle": "round,pad=0.22", "linewidth": 0.5})


def build_table1() -> list[Path]:
    selected, records = _material_records()
    case = selected[0]
    fig = plt.figure(figsize=(7.2, 1.62), facecolor="white")
    margin = 0.015
    gap = 0.012
    width = (1 - 2 * margin - 3 * gap) / 4
    cards = [margin + index * (width + gap) for index in range(4)]
    vlm_a = _bbox_image(VLM_ORIGINAL, VLM_TARGET_BBOX, COLORS["original"])
    vlm_b = _bbox_image(VLM_CONVERTED, VLM_TARGET_BBOX, COLORS["converted"])
    material_images = [_material_image(case, records, condition) for condition in ("original_MDL", "existing_noMDL", "nvidia_asset_converter_preview_or_bake")]
    _strip_card(fig, (cards[0], 0.04, width, 0.92), index="1", title="Proxy", evidence="24 matched render pairs", boundary="visual/feature proxy only", images=(OBJECT_ORIGINAL, OBJECT_CONVERTED), borders=(COLORS["original"], COLORS["converted"]))
    _strip_card(fig, (cards[1], 0.04, width, 0.92), index="2", title="VLM", evidence="15 clean + 30 stress pairs", boundary="fixed prompts; selected targets", images=(vlm_a, vlm_b), borders=(COLORS["original"], COLORS["converted"]))
    _strip_card(fig, (cards[2], 0.04, width, 0.92), index="3", title="Material", evidence="selected covered bins", boundary="case audit; not failure rate", images=material_images, borders=(COLORS["original"], COLORS["converted"], COLORS["nvidia"]))
    _strip_card(fig, (cards[3], 0.04, width, 0.92), index="4", title="Stack", evidence="99 paired InternNav episodes", boundary="stack entry; not robustness", images=(_nav_still("597_597", "original", "start"), _nav_still("597_597", "nomdl", "end")), borders=(COLORS["original"], COLORS["converted"]))
    return _save_bundle(fig, OUTPUTS["table1"])


def _condition_header(fig: plt.Figure, x: float, y: float, w: float, text: str, color: str) -> None:
    _figure_patch(fig, Rectangle((x, y), w, 0.045, facecolor=color, edgecolor="none"))
    fig.text(x + w / 2, y + 0.0225, text, ha="center", va="center", color="white", fontsize=6.8, fontweight="bold")


def build_fig2() -> list[Path]:
    fig = plt.figure(figsize=(7.2, 3.25), facecolor="white")
    left, right, gap = 0.06, 0.515, 0.025
    width = 0.425
    _condition_header(fig, left, 0.905, width, "Original MDL", COLORS["original"])
    _condition_header(fig, right, 0.905, width, "noMDL", COLORS["converted"])
    fig.text(0.015, 0.82, "a", fontsize=8, fontweight="bold")
    fig.text(0.035, 0.82, "Proxy object pair", fontsize=7.2, fontweight="bold", color=COLORS["ink"])
    _add_image(fig, (left, 0.52, width, 0.36), OBJECT_ORIGINAL, crop=OBJECT_CROP, border=COLORS["original"], linewidth=0.9)
    _add_image(fig, (right, 0.52, width, 0.36), OBJECT_CONVERTED, crop=OBJECT_CROP, border=COLORS["converted"], linewidth=0.9)
    fig.text(0.015, 0.435, "b", fontsize=8, fontweight="bold")
    fig.text(0.035, 0.435, "GRScenes scene pair", fontsize=7.2, fontweight="bold", color=COLORS["ink"])
    _add_image(fig, (left, 0.06, width, 0.35), SCENE_ORIGINAL, border=COLORS["original"], linewidth=0.9)
    _add_image(fig, (right, 0.06, width, 0.35), SCENE_CONVERTED, border=COLORS["converted"], linewidth=0.9)
    return _save_bundle(fig, OUTPUTS["fig2"])


def _effect_label(case: dict[str, Any]) -> str:
    mapping = {
        "opacity_transparency": "opacity",
        "emission": "emission",
        "normal_bump": "normal/bump",
        "displacement_height": "height",
    }
    labels = [mapping.get(str(value), str(value)) for value in case.get("covered_effects", [])]
    if len(labels) >= 4:
        return " · ".join(labels[:2]) + "\n" + " · ".join(labels[2:])
    if len(labels) == 3:
        return labels[0] + "\n" + " · ".join(labels[1:])
    return "\n".join(labels)


def build_fig3() -> list[Path]:
    selected, records = _material_records()
    fig = plt.figure(figsize=(7.2, 3.2), facecolor="white")
    label_x = 0.015
    col_x = (0.175, 0.445, 0.715)
    col_w = 0.255
    headers = (("Original MDL", COLORS["original"]), ("ConvertAsset noMDL", COLORS["converted"]), ("NVIDIA", COLORS["nvidia"]))
    for x, (title, color) in zip(col_x, headers):
        _condition_header(fig, x, 0.925, col_w, title, color)
    row_y = (0.725, 0.51, 0.295, 0.08)
    row_h = 0.18
    conditions = ("original_MDL", "existing_noMDL", "nvidia_asset_converter_preview_or_bake")
    for index, (case, y) in enumerate(zip(selected, row_y)):
        category = str(case["target_category"]).capitalize()
        fig.text(label_x, y + row_h - 0.018, chr(ord("a") + index), fontsize=7.5, fontweight="bold", color=COLORS["structure"])
        fig.text(label_x + 0.022, y + row_h - 0.018, category, fontsize=7.0, fontweight="bold", color=COLORS["ink"])
        fig.text(label_x + 0.022, y + 0.035, _effect_label(case), fontsize=4.55, color=COLORS["muted"], linespacing=1.15)
        for x, condition, (_, border) in zip(col_x, conditions, headers):
            _add_image(fig, (x, y, col_w, row_h), _material_image(case, records, condition), border=border, linewidth=0.8)
    return _save_bundle(fig, OUTPUTS["fig3"])


def _case_summary(case: dict[str, Any]) -> tuple[str, str]:
    case_type = str(case.get("case_type", "")).replace("_", " ")
    metrics = case.get("metrics", {})
    original = metrics.get("original", {}).get("SR")
    converted = metrics.get("modified", {}).get("SR")
    return case_type, f"SR O/N {original:g}/{converted:g}"


def build_fig4() -> list[Path]:
    cases = _nav_case_map()
    fig = plt.figure(figsize=(7.2, 3.0), facecolor="white")
    label_x, label_w = 0.012, 0.13
    col_x = (0.15, 0.36, 0.57, 0.78)
    col_w = 0.20
    column_defs = (
        ("Original start", COLORS["original"]),
        ("Original end", COLORS["original"]),
        ("noMDL start", COLORS["converted"]),
        ("noMDL end", COLORS["converted"]),
    )
    for x, (title, color) in zip(col_x, column_defs):
        _condition_header(fig, x, 0.905, col_w, title, color)
    fig.text(0.015, 0.963, "● executed", color=COLORS["trajectory"], fontsize=5.4, fontweight="bold")
    fig.text(0.015, 0.925, "● reference", color=COLORS["pass"], fontsize=5.4, fontweight="bold")
    row_y = (0.625, 0.34, 0.055)
    row_h = 0.235
    columns = (("original", "start"), ("original", "end"), ("nomdl", "start"), ("nomdl", "end"))
    for row_index, (case_key, y) in enumerate(zip(NAV_CASES, row_y)):
        case = cases[case_key]
        case_type, sr = _case_summary(case)
        fig.text(label_x, y + row_h - 0.03, chr(ord("a") + row_index), fontsize=7.5, fontweight="bold", color=COLORS["structure"])
        fig.text(label_x + 0.022, y + row_h - 0.03, case_key, fontsize=7.2, fontweight="bold", color=COLORS["ink"])
        fig.text(label_x + 0.022, y + 0.105, case_type, fontsize=5.4, color=COLORS["muted"], wrap=True)
        fig.text(label_x + 0.022, y + 0.040, sr, fontsize=5.5, color=COLORS["ink"], fontweight="bold")
        for x, (condition, moment), (_, border) in zip(col_x, columns, column_defs):
            _add_image(fig, (x, y, col_w, row_h), _nav_still(case_key, condition, moment), border=border, linewidth=0.8)
    return _save_bundle(fig, OUTPUTS["fig4"])


BUILDERS = {
    "fig1": build_fig1,
    "table1": build_table1,
    "fig2": build_fig2,
    "fig3": build_fig3,
    "fig4": build_fig4,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", choices=(*BUILDERS, "all"), default="all")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    apply_publication_style()
    selected = BUILDERS if args.figure == "all" else {args.figure: BUILDERS[args.figure]}
    report: dict[str, list[str]] = {}
    for name, builder in selected.items():
        report[name] = [str(path.relative_to(ROOT)) for path in builder()]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
