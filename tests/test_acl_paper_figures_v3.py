import importlib.util
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
from scipy import ndimage
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "paper/shared/figures"
SCRIPT = FIG_DIR / "gen_acl_paper_figures_v3.py"


def load_module():
    sys.path.insert(0, str(FIG_DIR))
    spec = importlib.util.spec_from_file_location("gen_acl_paper_figures_v3", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v3_output_bundles_are_complete() -> None:
    module = load_module()
    for name in module.OUTPUT_NAMES.values():
        for suffix in (".svg", ".pdf", ".png"):
            path = FIG_DIR / f"{name}{suffix}"
            assert path.is_file(), path
            assert path.stat().st_size > 1000, path


def test_v3_png_dimensions_match_publication_contract() -> None:
    expected = {
        "fig_acl_method_chain_v3.png": (2160, 990),
        "fig_acl_evidence_registry_strip_v2.png": (2160, 465),
        "fig_render_scene_evidence_wide_v3.png": (2160, 915),
        "fig_material_effect_baseline_qualitative_v3.png": (2160, 945),
        "fig_internnav_rollout_main_v3.png": (2160, 825),
        "fig_supplement_first_page_evidence_quickstart_v2.png": (1035, 1500),
        "fig_supplement_vlm_coordinate_protocol_atlas_v2.png": (2160, 1575),
        "fig_supplement_material_diagnostic_atlas_v2.png": (2160, 2220),
        "fig_supplement_navigation_media_atlas_v2.png": (2160, 2100),
    }
    for name, size in expected.items():
        with Image.open(FIG_DIR / name) as image:
            assert image.size == size


def test_material_sphere_slots_are_transparent_single_components() -> None:
    module = load_module()
    component_dir = FIG_DIR / "generated_components/fig1_material_pairs_v1"
    manifest = yaml.safe_load(
        (component_dir / "manifest.yaml").read_text(encoding="utf-8")
    )
    optics = json.loads((component_dir / "optics.json").read_text(encoding="utf-8"))
    assert manifest["mode"] == "figure_composition"
    assert "not experimental renders" in manifest["claim_boundary"]
    assert optics["extraction_method"] == "whole_atlas_alpha_connected_components"
    assert optics["significant_component_count"] == 8
    expected_grid = {
        name: [row, col] for name, row, col in module.COMPONENT_SLOTS
    }
    atlas_bboxes = set()
    for slot_name, path_value in manifest["slots"].items():
        path = ROOT / path_value
        with Image.open(path) as image:
            assert image.mode == "RGBA"
            alpha = np.asarray(image.getchannel("A"))
        labels, count = ndimage.label(alpha > 12)
        sizes = np.bincount(labels.ravel())
        significant = sum(size >= 100 for size in sizes[1:])
        assert count >= 1
        assert significant == 1, path
        assert (alpha == 0).mean() >= 0.35
        row_widths = np.count_nonzero(alpha > module.COMPONENT_ALPHA_THRESHOLD, axis=1)
        nonzero_widths = row_widths[row_widths > 0]
        maximum_width = int(nonzero_widths.max())
        assert nonzero_widths[0] / maximum_width <= module.COMPONENT_MAX_EDGE_WIDTH_FRACTION
        assert nonzero_widths[-1] / maximum_width <= module.COMPONENT_MAX_EDGE_WIDTH_FRACTION

        record = optics["slots"][slot_name]
        assert record["grid_position"] == expected_grid[slot_name]
        assert record["top_edge_width_fraction"] <= module.COMPONENT_MAX_EDGE_WIDTH_FRACTION
        assert record["bottom_edge_width_fraction"] <= module.COMPONENT_MAX_EDGE_WIDTH_FRACTION
        bbox = tuple(record["alpha_bbox"])
        aspect = (bbox[2] - bbox[0]) / (bbox[3] - bbox[1])
        assert 0.85 <= aspect <= 1.15
        atlas_bboxes.add(tuple(record["atlas_bbox"]))
    assert len(atlas_bboxes) == 8


def test_fig1_story_first_complexity_budget() -> None:
    svg = FIG_DIR / "fig_acl_method_chain_v3.svg"
    tree = ET.parse(svg)
    tags: dict[str, int] = {}
    texts: list[str] = []
    font_sizes: set[str] = set()
    for element in tree.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        tags[tag] = tags.get(tag, 0) + 1
        if tag in {"text", "tspan"} and element.text and element.text.strip():
            texts.append(element.text.strip())
        font_sizes.update(
            re.findall(r"font-size:\s*([^;]+)", element.attrib.get("style", ""))
        )
    shapes = sum(
        tags.get(tag, 0)
        for tag in (
            "path",
            "rect",
            "circle",
            "ellipse",
            "polygon",
            "polyline",
            "line",
            "image",
        )
    )
    words = sum(
        len(re.findall(r"[A-Za-z0-9][A-Za-z0-9/+.:-]*", text))
        for text in texts
    )
    assert shapes <= 100
    assert tags.get("text", 0) <= 35
    assert words <= 100
    assert len(font_sizes) <= 4
    numeric_sizes = [
        float(re.match(r"[0-9.]+", size).group()) for size in font_sizes
    ]
    assert min(numeric_sizes) >= 6.0


def test_v3_svgs_keep_editable_text_and_portable_paths() -> None:
    module = load_module()
    for name in module.OUTPUT_NAMES.values():
        text = (FIG_DIR / f"{name}.svg").read_text(encoding="utf-8")
        assert "<text" in text
        assert "/cpfs/" not in text
        assert "/root/" not in text


def test_fig1_semantics_and_generated_asset_boundary() -> None:
    spec = json.loads(
        (FIG_DIR / "specs/fig_acl_method_chain_v3.spec.json").read_text(
            encoding="utf-8"
        )
    )
    assert spec["review"]["semantic_graph_approved"] is True
    edges = {edge["id"]: edge for edge in spec["edges"]}
    for edge_id in (
        "matched-to-proxy",
        "matched-to-vlm",
        "matched-to-material",
        "matched-to-stack",
    ):
        assert edges[edge_id]["scope"] == "external"
    sphere_edges = [
        edge for edge in spec["edges"] if edge["id"].endswith("cue-simplification")
    ]
    assert len(sphere_edges) == 4
    assert all("not measured evidence" in edge["meaning"] for edge in sphere_edges)


def test_acl_latex_uses_v4_fig1_and_selected_v3_v2_figures() -> None:
    main = (ROOT / "paper/venues/acl27/main.tex").read_text(encoding="utf-8")
    intro = (ROOT / "paper/venues/acl27/sections/intro.tex").read_text(
        encoding="utf-8"
    )
    results = (ROOT / "paper/venues/acl27/sections/results.tex").read_text(
        encoding="utf-8"
    )
    limitations = (ROOT / "paper/venues/acl27/sections/limitations.tex").read_text(
        encoding="utf-8"
    )
    assert "fig_acl_evidence_registry_strip_v2.pdf" in main
    assert "fig_acl_method_chain_v4.pdf" in intro
    assert "fig_acl_method_chain_v3.pdf" not in intro
    assert "The spheres explain the" in intro
    assert "fig_render_scene_evidence_wide_v3.pdf" in results
    assert "fig_material_effect_baseline_qualitative_v3.pdf" in results
    assert "fig_internnav_rollout_main_v4.pdf" in results
    assert "fig_internnav_rollout_main_v3.pdf" not in results
    assert "fig_internnav_rollout_main_v4.pdf" not in limitations
    expected = {
        "00_overview.tex": "fig_supplement_first_page_evidence_quickstart_v2.pdf",
        "02_vlm_protocol.tex": "fig_supplement_vlm_coordinate_protocol_atlas_v2.pdf",
        "04_material_effects.tex": "fig_supplement_material_diagnostic_atlas_v2.pdf",
        "05_internnav_visuals.tex": "fig_supplement_navigation_media_atlas_v2.pdf",
    }
    root = ROOT / "paper/venues/acl27/sections/supplement"
    for filename, figure in expected.items():
        assert figure in (root / filename).read_text(encoding="utf-8")


def test_v3_figures_are_registered() -> None:
    registry = yaml.safe_load((FIG_DIR / "sources.yaml").read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in registry["figures"]}
    expected = {
        "fig_acl_method_chain_v3",
        "fig_acl_evidence_registry_strip_v2",
        "fig_render_scene_evidence_wide_v3",
        "fig_material_effect_baseline_qualitative_v3",
        "fig_internnav_rollout_main_v3",
        "fig_supplement_first_page_evidence_quickstart_v2",
        "fig_supplement_vlm_coordinate_protocol_atlas_v2",
        "fig_supplement_material_diagnostic_atlas_v2",
        "fig_supplement_navigation_media_atlas_v2",
    }
    assert expected <= by_id.keys()
    for figure_id in expected:
        entry = by_id[figure_id]
        assert entry["generated_by"] == "paper/shared/figures/gen_acl_paper_figures_v3.py"
        assert {Path(path).suffix for path in entry["outputs"]} == {
            ".svg",
            ".pdf",
            ".png",
        }
