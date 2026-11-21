import importlib.util
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/figures/gen_acl_main_figures_v2.py"
FIG_DIR = ROOT / "paper/shared/figures"


def load_module():
    spec = importlib.util.spec_from_file_location("gen_acl_main_figures_v2", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_figure1_semantic_graph_has_parallel_evidence_gates() -> None:
    module = load_module()
    spec = module.validate_figure1_spec()

    edges = {edge["id"]: edge for edge in spec["edges"]}
    expected = {
        "matched-to-proxy",
        "matched-to-vlm",
        "matched-to-material",
        "matched-to-stack",
    }

    assert spec["mode"] == "inspired"
    assert spec["review"]["semantic_graph_approved"] is True
    assert expected.issubset(edges)
    assert {edges[name]["from"] for name in expected} == {
        "matched.out.proxy",
        "matched.out.vlm",
        "matched.out.material",
        "matched.out.stack",
    }
    assert all(edges[name]["scope"] == "external" for name in expected)


def test_acl_main_figure_bundles_are_complete_and_versioned() -> None:
    module = load_module()

    for name, stem in module.OUTPUTS.items():
        assert name in {"fig1", "table1", "fig2", "fig3", "fig4"}
        for suffix in (".svg", ".pdf", ".png"):
            path = stem.with_suffix(suffix)
            assert path.is_file(), path
            assert path.stat().st_size > 1000, path


def test_svg_text_remains_editable_and_paths_are_portable() -> None:
    module = load_module()

    for stem in module.OUTPUTS.values():
        text = stem.with_suffix(".svg").read_text(encoding="utf-8")
        assert "<text" in text
        assert "/cpfs/" not in text
        assert "/root/" not in text
        assert "font-family" in text


def test_png_dimensions_match_declared_final_aspect_ratios() -> None:
    expected = {
        "fig1": (2160, 1080),
        "table1": (2160, 486),
        "fig2": (2160, 975),
        "fig3": (2160, 960),
        "fig4": (2160, 900),
    }
    module = load_module()

    for name, size in expected.items():
        with Image.open(module.OUTPUTS[name].with_suffix(".png")) as image:
            assert image.size == size


def test_source_registry_tracks_each_v2_bundle() -> None:
    import yaml

    registry = yaml.safe_load((FIG_DIR / "sources.yaml").read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in registry["figures"]}
    expected_ids = {
        "fig_acl_method_chain_v2",
        "fig_acl_evidence_registry_strip_v1",
        "fig_render_scene_evidence_wide_v2",
        "fig_material_effect_baseline_qualitative_v2",
        "fig_internnav_rollout_main_v2",
    }

    assert expected_ids.issubset(by_id)
    for figure_id in expected_ids:
        entry = by_id[figure_id]
        assert entry["generated_by"] == "paper/shared/figures/gen_acl_main_figures_v2.py"
        assert {Path(path).suffix for path in entry["outputs"]} == {".svg", ".pdf", ".png"}
        assert entry["sources"]


def test_figure1_spec_contains_only_repo_relative_asset_paths() -> None:
    spec_path = FIG_DIR / "specs/fig_acl_method_chain_v2.spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    for asset in spec["assets"]:
        path = Path(asset["path"])
        assert not path.is_absolute()
        resolved = (spec_path.parent / path).resolve()
        assert resolved.is_relative_to(ROOT)
