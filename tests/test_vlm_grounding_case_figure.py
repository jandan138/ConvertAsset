import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/figures/gen_vlm_grounding_cases.py"


def load_figure_module():
    spec = importlib.util.spec_from_file_location("gen_vlm_grounding_cases", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_point_to_pixel_handles_raw_and_normalized_coordinates() -> None:
    module = load_figure_module()

    assert module.point_to_pixel([300, 200], width=600, height=450, frame="raw_pixel") == (300.0, 200.0)
    assert module.point_to_pixel([500, 250], width=600, height=400, frame="normalized_1000") == (300.0, 100.0)
    assert module.point_to_pixel(None, width=600, height=450, frame="raw_pixel") is None


def test_status_line_is_short_enough_for_figure_cell() -> None:
    module = load_figure_module()
    entry = module.CaseEntry(
        version="converted",
        image_path=Path("/tmp/fake.png"),
        width=600,
        height=450,
        bbox_xyxy=[10, 20, 30, 40],
        point_xy=(10.0, 20.0),
        answer="target category: clock",
        answer_match=False,
        score_hit=False,
    )

    line = module.status_line(entry)

    assert line == "converted: pt miss, ans miss"
    assert module.answer_line(entry) == "ans=target category..."
    assert len(line) <= 32


def test_load_case_pairs_predictions_with_score_records(tmp_path: Path) -> None:
    module = load_figure_module()
    image_a = tmp_path / "original.png"
    image_b = tmp_path / "converted.png"
    image_a.write_bytes(b"fake original")
    image_b.write_bytes(b"fake converted")
    predictions_path = tmp_path / "predictions.jsonl"
    rows = [
        {
            "sample_id": "pair.view.original",
            "pair_id": "pair.view",
            "version": "original",
            "image": {"path": str(image_a), "width": 600, "height": 450},
            "target": {"bbox_xyxy": [10, 20, 30, 40], "category": "cup"},
            "prediction": {"point_xy": [500, 500], "answer": "cup"},
        },
        {
            "sample_id": "pair.view.converted",
            "pair_id": "pair.view",
            "version": "converted",
            "image": {"path": str(image_b), "width": 600, "height": 450},
            "target": {"bbox_xyxy": [12, 22, 32, 42], "category": "cup"},
            "prediction": {"point_xy": [250, 250], "answer": "mug"},
        },
    ]
    predictions_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "records": [
                    {"sample_id": "pair.view.original", "answer_match": True, "point_in_bbox_normalized_1000": True},
                    {"sample_id": "pair.view.converted", "answer_match": False, "point_in_bbox_normalized_1000": False},
                ]
            }
        ),
        encoding="utf-8",
    )

    case = module.load_case(
        {
            "title": "Clean success",
            "split": "clean",
            "model": "Gemma4",
            "pair_id": "pair.view",
            "predictions": predictions_path,
            "score_summary": summary_path,
            "point_frame": "normalized_1000",
            "score_metric": "point_in_bbox_normalized_1000",
        }
    )

    assert case.title == "Clean success"
    assert case.target_category == "cup"
    assert case.entries["original"].point_xy == (300.0, 225.0)
    assert case.entries["converted"].point_xy == (150.0, 112.5)
    assert case.entries["original"].answer_match is True
    assert case.entries["converted"].score_hit is False


def test_render_figure_uses_compact_grid_layout(tmp_path: Path) -> None:
    module = load_figure_module()
    cases = module.build_cases()
    out_png = tmp_path / "cases.png"
    out_pdf = tmp_path / "cases.pdf"

    module.render_figure(cases, out_png=out_png, out_pdf=out_pdf)

    from PIL import Image

    with Image.open(out_png) as image:
        width, height = image.size
    assert height / width < 0.85


def test_figure_layout_avoids_long_ids_and_uses_readable_point_markers() -> None:
    module = load_figure_module()
    case = module.build_cases()[0]

    title = module.case_title(case)

    assert case.pair_id not in title
    assert len(title) <= 70
    assert module.POINT_RADIUS >= 7
    assert module.STATUS_H >= 44


def test_default_case_specs_resolve_to_existing_render_images() -> None:
    module = load_figure_module()

    cases = module.build_cases()

    assert len(cases) == 4
    assert {case.split for case in cases} == {"clean", "stress"}
    assert {case.entries["original"].version for case in cases} == {"original"}
    assert {case.entries["converted"].version for case in cases} == {"converted"}
    for case in cases:
        for entry in case.entries.values():
            assert entry.image_path.exists()
            assert entry.bbox_xyxy


def test_default_case_specs_use_expanded30_stress_outputs() -> None:
    module = load_figure_module()

    stress_specs = [spec for spec in module.CASE_SPECS if spec["split"] == "stress"]

    assert len(stress_specs) == 2
    assert stress_specs[0]["predictions"].name == "stress_predictions.jsonl"
    assert stress_specs[0]["score_summary"].name == "stress_score_summary.json"
    assert "stress_expanded30_probes" in str(stress_specs[1]["predictions"])
    assert "qwen25_stress_expanded30_structured_score_summary.json" in str(stress_specs[1]["score_summary"])


def test_load_case_requires_score_records_for_selected_samples(tmp_path: Path) -> None:
    module = load_figure_module()
    image_a = tmp_path / "original.png"
    image_b = tmp_path / "converted.png"
    image_a.write_bytes(b"fake original")
    image_b.write_bytes(b"fake converted")
    predictions_path = tmp_path / "predictions.jsonl"
    rows = [
        {
            "sample_id": "pair.view.original",
            "pair_id": "pair.view",
            "version": "original",
            "image": {"path": str(image_a), "width": 600, "height": 450},
            "target": {"bbox_xyxy": [10, 20, 30, 40], "category": "cup"},
            "prediction": {"point_xy": [500, 500], "answer": "cup"},
        },
        {
            "sample_id": "pair.view.converted",
            "pair_id": "pair.view",
            "version": "converted",
            "image": {"path": str(image_b), "width": 600, "height": 450},
            "target": {"bbox_xyxy": [12, 22, 32, 42], "category": "cup"},
            "prediction": {"point_xy": [250, 250], "answer": "mug"},
        },
    ]
    predictions_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps({"records": [{"sample_id": "pair.view.original", "point_in_bbox_normalized_1000": True}]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing score record"):
        module.load_case(
            {
                "title": "Missing converted score",
                "split": "clean",
                "model": "Gemma4",
                "pair_id": "pair.view",
                "predictions": predictions_path,
                "score_summary": summary_path,
                "point_frame": "normalized_1000",
                "score_metric": "point_in_bbox_normalized_1000",
            }
        )
