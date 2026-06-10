import importlib.util
from pathlib import Path

from PIL import ImageFilter, ImageStat


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/figures/gen_render_scene_evidence_wide.py"


def load_figure_module():
    spec = importlib.util.spec_from_file_location("gen_render_scene_evidence_wide", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_proxy_object_row_has_at_least_one_readable_contrast_sample() -> None:
    module = load_figure_module()

    contrasts: list[float] = []
    for _, mdl_path, nomdl_path, crop in module.OBJECT_PAIRS:
        for path in (mdl_path, nomdl_path):
            image = module._fit(
                path,
                (module.OBJECT_CELL_W, module.OBJECT_H),
                fill=(246, 246, 246),
                crop=crop,
                cover=True,
            ).convert("L")
            contrasts.append(ImageStat.Stat(image).stddev[0])

    assert max(contrasts) >= 12.0


def test_proxy_object_row_uses_near_full_text_width_for_pdf_readability() -> None:
    module = load_figure_module()

    available_width = module.WIDTH - 2 * module.MARGIN
    object_row_width = 2 * module.OBJECT_CELL_W + module.GAP

    assert module.OBJECT_CELL_W >= int(module.CELL_W * 0.95)
    assert object_row_width >= int(available_width * 0.95)


def test_render_scene_panel_uses_visual_first_layout_without_microcopy() -> None:
    module = load_figure_module()

    assert module.TITLE_H == 0
    assert module.SUBTITLE_H == 0
    assert module.ROW_FOOTER_H == 0
    assert module.OBJECT_H >= 380
    assert module.SCENE_H >= 360


def test_selected_proxy_object_row_has_front_or_angled_detail_at_pdf_scale() -> None:
    module = load_figure_module()

    _, mdl_path, nomdl_path, crop = module.OBJECT_PAIRS[0]
    assert "_back" not in mdl_path.stem
    assert "_back" not in nomdl_path.stem
    assert "front" in mdl_path.stem
    assert "front" in nomdl_path.stem

    selected_edge_counts = []
    selected_contrasts = []
    for path in (mdl_path, nomdl_path):
        image = module._fit(
            path,
            (module.OBJECT_CELL_W, module.OBJECT_H),
            fill=(246, 246, 246),
            crop=crop,
            cover=True,
        ).convert("L")
        edges = image.filter(ImageFilter.FIND_EDGES)
        strong_edge_pixels = sum(edges.histogram()[30:])
        selected_edge_counts.append(strong_edge_pixels)
        selected_contrasts.append(ImageStat.Stat(image).stddev[0])

    assert min(selected_edge_counts) >= 3000
    assert min(selected_contrasts) >= 7.0


def test_selected_proxy_object_crop_improves_pdf_scale_detail() -> None:
    module = load_figure_module()

    _, mdl_path, nomdl_path, crop = module.OBJECT_PAIRS[0]
    assert crop is not None

    def min_contrast(crop_box: tuple[int, int, int, int] | None) -> float:
        contrasts = []
        for path in (mdl_path, nomdl_path):
            image = module._fit(
                path,
                (module.OBJECT_CELL_W, module.OBJECT_H),
                fill=(246, 246, 246),
                crop=crop_box,
                cover=True,
            ).convert("L")
            contrasts.append(ImageStat.Stat(image).stddev[0])
        return min(contrasts)

    assert min_contrast(crop) >= min_contrast(None) + 2.0


def test_selected_proxy_object_crop_has_pdf_scale_minimum_contrast() -> None:
    module = load_figure_module()

    _, mdl_path, nomdl_path, crop = module.OBJECT_PAIRS[0]
    assert crop is not None

    selected_contrasts = []
    for path in (mdl_path, nomdl_path):
        image = module._fit(
            path,
            (module.OBJECT_CELL_W, module.OBJECT_H),
            fill=(246, 246, 246),
            crop=crop,
            cover=True,
        ).convert("L")
        selected_contrasts.append(ImageStat.Stat(image).stddev[0])

    assert min(selected_contrasts) >= 11.5


def test_selected_proxy_object_sublabel_names_the_view(monkeypatch, tmp_path) -> None:
    module = load_figure_module()

    sublabels: list[str] = []

    def collect_sublabel(*args, **kwargs) -> None:
        if kwargs.get("header") in {"Original MDL", "noMDL"}:
            sublabels.append(kwargs["sublabel"])

    monkeypatch.setattr(module, "_draw_cell", collect_sublabel)
    monkeypatch.setattr(module, "OUT", tmp_path / "fig.png")
    monkeypatch.setattr(module, "OUT_PDF", tmp_path / "fig.pdf")

    module.main()

    assert "#0011 cropped top-front-right object view" in sublabels[:2]
    assert "#0011 full object view" not in sublabels[:2]
