import importlib.util
import json
from pathlib import Path
import sys
import zipfile

from PIL import Image
from pptx import Presentation
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "paper/shared/figures"
SCRIPT = FIG_DIR / "gen_acl_method_chain_v4_pptx.py"
STEM = FIG_DIR / "fig_acl_method_chain_v4"


def load_module():
    sys.path.insert(0, str(FIG_DIR))
    spec = importlib.util.spec_from_file_location("gen_acl_method_chain_v4_pptx", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v4_editable_and_paper_outputs_exist() -> None:
    for suffix in (".pptx", ".svg", ".pdf", ".png"):
        path = STEM.with_suffix(suffix)
        assert path.is_file(), path
        assert path.stat().st_size > 1000, path
    with Image.open(STEM.with_suffix(".png")) as image:
        assert image.size == (2160, 990)
    qa = json.loads((FIG_DIR / "fig_acl_method_chain_v4.qa.json").read_text(encoding="utf-8"))
    assert qa["status"] == "pass"
    assert qa["findings"]["critical"] == []
    assert qa["findings"]["major"] == []


def test_v4_layout_preflight_rejects_no_current_item(tmp_path: Path) -> None:
    module = load_module()
    layout = module._build_layout(tmp_path)
    report = module.validate_layout(layout)
    assert report["ok"] is True
    assert report["findings"] == []
    assert report["text_count"] == 20
    assert report["image_count"] == 19
    assert len(report["font_sizes_pt"]) == 4
    assert report["minimum_font_pt"] >= 6.0


def test_v4_pptx_is_one_flat_editable_slide_without_cards() -> None:
    presentation = Presentation(STEM.with_suffix(".pptx"))
    assert len(presentation.slides) == 1
    assert presentation.slide_width == pytest.approx(7.2 * 914400)
    assert presentation.slide_height == pytest.approx(3.3 * 914400)
    slide = presentation.slides[0]
    names = [shape.name.lower() for shape in slide.shapes]
    assert not any("card" in name for name in names)
    assert sum(1 for shape in slide.shapes if shape.shape_type == 13) == 19
    text_shapes = [shape for shape in slide.shapes if shape.has_text_frame and shape.text]
    assert len(text_shapes) == 20
    assert all(shape.text_frame.word_wrap is False for shape in text_shapes)
    assert any(shape.text == "Proxy similarity" for shape in text_shapes)
    assert any(shape.text == "Stack entry" for shape in text_shapes)


def test_v4_pptx_has_no_external_or_machine_specific_relationships() -> None:
    with zipfile.ZipFile(STEM.with_suffix(".pptx")) as package:
        xml = "\n".join(
            package.read(name).decode("utf-8", errors="replace")
            for name in package.namelist()
            if name.endswith((".xml", ".rels"))
        )
    assert 'TargetMode="External"' not in xml
    assert "/cpfs/" not in xml
    assert "/root/" not in xml
    assert not any(
        int(value) > 0
        for value in __import__("re").findall(r'<a:effectRef[^>]*idx="(\d+)"', xml)
    )
    assert "outerShdw" not in xml


def test_v4_svg_is_self_contained_and_keeps_editable_text() -> None:
    text = STEM.with_suffix(".svg").read_text(encoding="utf-8")
    assert "<text" in text
    assert "data:image/png;base64," in text
    assert "/cpfs/" not in text
    assert "/root/" not in text
    assert "Proxy similarity" in text
    assert "Four bounded checks" in text


def test_v4_spec_keeps_approved_parallel_evidence_topology() -> None:
    spec = json.loads(
        (FIG_DIR / "specs/fig_acl_method_chain_v4.spec.json").read_text(
            encoding="utf-8"
        )
    )
    assert spec["mode"] == "inspired"
    assert spec["review"]["semantic_graph_approved"] is True
    edges = {edge["id"]: edge for edge in spec["edges"]}
    assert edges["matched-to-distribution"]["scope"] == "external"
    for check in ("proxy", "vlm", "material", "stack"):
        edge = edges[f"distribution-to-{check}"]
        assert edge["scope"] == "external"
        assert edge["arrowhead"] == "end"
    sphere_edges = [edge for edge in spec["edges"] if edge["id"].endswith("cue-simplification")]
    assert len(sphere_edges) == 4
    assert all("not measured evidence" in edge["meaning"] for edge in sphere_edges)


def test_v4_is_active_and_registered() -> None:
    intro = (ROOT / "paper/venues/acl27/sections/intro.tex").read_text(
        encoding="utf-8"
    )
    assert "fig_acl_method_chain_v4.pdf" in intro
    assert "fig_acl_method_chain_v3.pdf" not in intro
    assert "The spheres explain the" in intro
    registry = yaml.safe_load((FIG_DIR / "sources.yaml").read_text(encoding="utf-8"))
    entry = next(item for item in registry["figures"] if item["id"] == "fig_acl_method_chain_v4")
    assert entry["generated_by"] == "paper/shared/figures/gen_acl_method_chain_v4_pptx.py"
    assert {Path(path).suffix for path in entry["outputs"]} == {
        ".pptx",
        ".svg",
        ".pdf",
        ".png",
    }
