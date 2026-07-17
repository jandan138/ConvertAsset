import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/figures/gen_internnav_main_readable.py"
LIMITATIONS = ROOT / "paper/venues/acl27/sections/limitations.tex"


def load_module():
    assert SCRIPT.exists(), "InternNav rollout figure generator is missing"
    spec = importlib.util.spec_from_file_location("gen_internnav_main_readable", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_internnav_readable_panel_reports_overlay_legend() -> None:
    module = load_module()

    report = module.build()

    assert report["overlay_legend"] == [
        {"color": "purple", "meaning": "agent action arrow and executed trajectory"},
        {"color": "green", "meaning": "reference path"},
    ]
    assert report["overlay_recolor"]["source_overlay_color"] == "red"
    assert report["overlay_recolor"]["display_overlay_color"] == "purple"
    assert report["overlay_recolor"]["total_source_red_overlay_pixels_recolored"] > 0


def test_internnav_readable_panel_uses_wider_page_scale_row_labels() -> None:
    module = load_module()

    report = module.build()

    layout = report["layout"]
    assert layout["output_width_px"] == 1748
    assert layout["row_label_width_px"] >= 270
    assert layout["frame_cell_width_px"] <= 350
    assert layout["row_key_font_px"] >= 22
    assert layout["row_detail_font_px"] >= 16


def test_internnav_rollout_caption_names_red_and_green_overlays() -> None:
    text = LIMITATIONS.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "purple executed paths and action arrows" in normalized
    assert "overlay color changed for readability" in normalized
    assert "green reference paths" in normalized


def test_internnav_caption_avoids_rollout_linebreak_hotspot() -> None:
    text = LIMITATIONS.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "Selected InternNav path panels." in normalized
    assert "trajectory overlays for orientation only" in normalized
    assert "Quantitative stack-entry measurements remain tied to the 99-episode paired run" in normalized
    assert "The rollout panel only orients readers." in normalized
    assert "Load/render measures stability only, not speedup" in normalized
    assert "Selected qualitative InternNav rollout panel" not in normalized
    assert "Selected InternNav path panel." not in normalized
    assert "representative start/end example for reader orientation" not in normalized
    assert "selected rollout panels are qualitative evidence only" not in normalized
    assert "NVIDIA official-scene performance remains ungated" not in normalized
    assert "broader guidelines require larger licensed scene corpora" not in normalized


def test_acl_limitations_uses_wide_internnav_path_panel() -> None:
    text = LIMITATIONS.read_text(encoding="utf-8")

    assert r"\begin{figure*}[t]" in text
    assert r"\end{figure*}" in text
    assert r"\caption{" in text
    assert r"\captionof{figure}" not in text
    assert "fig_internnav_rollout_0036_0066_main3_readable.png" in text
    assert "fig_internnav_rollout_0036_0066_column.png" not in text

    panel_start = text.index(r"\begin{figure*}[t]")
    panel_end = text.index(r"\end{figure*}", panel_start)
    panel = text[panel_start:panel_end]
    assert "fig_internnav_rollout_0036_0066_main3_readable.png" in panel
    assert r"\includegraphics[width=\textwidth]" in panel


def test_wide_internnav_panel_precedes_limitations_text_to_avoid_blank_column() -> None:
    text = LIMITATIONS.read_text(encoding="utf-8")

    assert text.index(r"\begin{figure*}[t]") < text.index(r"\section*{Limitations}")
