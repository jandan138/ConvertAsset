import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("grscenes_run_vlm_predictions", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scoring_record(image_path: Path) -> dict:
    return {
        "sample_id": "pair.view_000.original",
        "pair_id": "pair.view_000",
        "version": "original",
        "task": "s1_referred_object_localization",
        "image": {"path": str(image_path), "width": 100, "height": 80},
        "target": {"bbox_xyxy": [10.0, 20.0, 30.0, 60.0], "category": "cup"},
        "expected_answers": ["cup"],
        "prediction": None,
    }


class FakeEngine:
    def __init__(self, text: str):
        self.text = text
        self.messages = []

    def generate(self, messages: list[dict]) -> str:
        self.messages.append(messages)
        return self.text


def test_parse_prediction_text_extracts_point_and_answer() -> None:
    module = load_runner_module()

    parsed = module.parse_prediction_text('Answer:\n{"point_xy": [25, 40], "answer": "cup"}')

    assert parsed == {"parse_status": "parsed", "point_xy": [25.0, 40.0], "answer": "cup"}


def test_parse_prediction_text_extracts_structured_text_point_and_answer() -> None:
    module = load_runner_module()

    parsed = module.parse_prediction_text("Point: 25, 40\nAnswer: cup", response_format="structured_text")

    assert parsed == {"parse_status": "parsed", "point_xy": [25.0, 40.0], "answer": "cup"}


def test_parse_prediction_text_extracts_structured_text_without_point_label() -> None:
    module = load_runner_module()

    parsed = module.parse_prediction_text("720,280\nAnswer: bottle", response_format="structured_text")

    assert parsed == {"parse_status": "parsed", "point_xy": [720.0, 280.0], "answer": "bottle"}


def test_parse_prediction_text_extracts_structured_text_without_labels() -> None:
    module = load_runner_module()

    parsed = module.parse_prediction_text("300,200\nbottle", response_format="structured_text")

    assert parsed == {"parse_status": "parsed", "point_xy": [300.0, 200.0], "answer": "bottle"}


def test_parse_prediction_text_extracts_structured_text_bbox_center() -> None:
    module = load_runner_module()

    parsed = module.parse_prediction_text("300,230,350,310\ncup", response_format="structured_text")

    assert parsed == {"parse_status": "parsed", "point_xy": [325.0, 270.0], "answer": "cup"}


def test_parse_prediction_text_reports_unparsed_output() -> None:
    module = load_runner_module()

    parsed = module.parse_prediction_text("I cannot tell.")

    assert parsed["parse_status"] == "parse_failed"
    assert parsed["point_xy"] is None
    assert parsed["answer"] is None


def test_build_prompt_can_request_normalized_1000_coordinates(tmp_path: Path) -> None:
    module = load_runner_module()

    prompt = module.build_prompt(scoring_record(tmp_path / "render.png"), coordinate_frame="normalized_1000")

    assert "normalized 0-1000 coordinate frame" in prompt
    assert "x=0 is the left image edge" in prompt
    assert "raw pixel" not in prompt.lower()


def test_build_prompt_can_request_structured_text_response(tmp_path: Path) -> None:
    module = load_runner_module()

    prompt = module.build_prompt(
        scoring_record(tmp_path / "render.png"),
        coordinate_frame="normalized_1000",
        response_format="structured_text",
    )

    assert "Point: x, y" in prompt
    assert "Answer: target category" in prompt
    assert "JSON" not in prompt


def test_run_predictions_preserves_record_and_adds_model_metadata(tmp_path: Path) -> None:
    module = load_runner_module()
    image_path = tmp_path / "render.png"
    image_path.write_bytes(b"fake image bytes")
    engine = FakeEngine("Point: 25, 40\nAnswer: cup")

    rows = module.run_predictions(
        [scoring_record(image_path)],
        engine,
        backend="local_hf_qwen",
        model_checkpoint="/models/qwen",
        temperature=0.0,
        max_new_tokens=64,
        coordinate_frame="normalized_1000",
        response_format="structured_text",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["sample_id"] == "pair.view_000.original"
    assert row["model_checkpoint"] == "/models/qwen"
    assert row["prediction"]["backend"] == "local_hf_qwen"
    assert row["prediction"]["point_xy"] == [25.0, 40.0]
    assert row["prediction"]["answer"] == "cup"
    assert row["prediction"]["parse_status"] == "parsed"
    assert row["prediction"]["coordinate_frame_requested"] == "normalized_1000"
    assert row["prompt"]["coordinate_frame"] == "normalized_1000"
    assert row["prompt"]["response_format"] == "structured_text"
    assert row["prompt"]["text"].startswith("You are evaluating a rendered indoor scene.")
    assert row["image"]["hash_sha256"]
    assert engine.messages[0][0]["content"][0]["type"] == "text"
    assert engine.messages[0][0]["content"][1]["type"] == "image_url"


def test_write_predictions_writes_jsonl_and_metadata(tmp_path: Path) -> None:
    module = load_runner_module()
    image_path = tmp_path / "render.png"
    image_path.write_bytes(b"fake image bytes")
    projection_report = tmp_path / "target_projection_qa_report.json"
    projection_report.write_text(json.dumps({"scoring_records": [scoring_record(image_path)]}), encoding="utf-8")
    out = tmp_path / "predictions.jsonl"
    rows = module.run_predictions(
        [scoring_record(image_path)],
        FakeEngine('{"point_xy": [25, 40], "answer": "cup"}'),
        backend="local_hf_qwen",
        model_checkpoint="/models/qwen",
        temperature=0.0,
        max_new_tokens=64,
        coordinate_frame="normalized_1000",
        response_format="json",
    )

    module.write_predictions(
        rows,
        out,
        projection_report=projection_report,
        backend="local_hf_qwen",
        model_checkpoint="/models/qwen",
        coordinate_frame="normalized_1000",
        response_format="json",
        argv=["--test"],
    )

    written = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    metadata = json.loads(out.with_suffix(out.suffix + ".metadata.json").read_text(encoding="utf-8"))
    assert written[0]["prediction"]["answer"] == "cup"
    assert metadata["backend"] == "local_hf_qwen"
    assert metadata["coordinate_frame"] == "normalized_1000"
    assert metadata["response_format"] == "json"
    assert metadata["claim_boundary"] == "model_prediction_scores_require_model_provenance_review"
    assert len(metadata["input_projection_report"]["hash_sha256"]) == 64
    assert len(metadata["output_jsonl"]["hash_sha256"]) == 64


def test_validate_run_plan_rejects_limited_canonical_output_and_missing_images(tmp_path: Path) -> None:
    module = load_runner_module()
    report = tmp_path / "target_projection_qa_report.json"
    canonical_out = report.parent / "predictions.jsonl"
    missing_image = tmp_path / "missing.png"
    records = [scoring_record(missing_image)]

    result = module.validate_run_plan(
        records,
        out=canonical_out,
        projection_report=report,
        limit=1,
        sample_ids=None,
        force=False,
    )

    assert result["ok"] is False
    assert "limited_run_requires_noncanonical_output_or_force" in result["blockers"]
    assert "missing_image_files" in result["blockers"]


def test_validate_run_plan_rejects_empty_selection(tmp_path: Path) -> None:
    module = load_runner_module()

    result = module.validate_run_plan(
        [],
        out=tmp_path / "probe_predictions.jsonl",
        projection_report=tmp_path / "target_projection_qa_report.json",
        limit=None,
        sample_ids=["missing"],
        force=False,
    )

    assert result["ok"] is False
    assert "empty_record_selection" in result["blockers"]


def test_openai_extraction_handles_content_block_responses() -> None:
    module = load_runner_module()
    engine = object.__new__(module.OpenAICompatibleEngine)

    text = engine._extract_text({"choices": [{"message": {"content": [{"type": "text", "text": "{\"answer\":\"cup\"}"}]}}]})

    assert text == '{"answer":"cup"}'


def test_gemma4_unsloth_detection_reads_quantized_config(tmp_path: Path) -> None:
    module = load_runner_module()
    model_path = tmp_path / "gemma-release"
    model_path.mkdir()
    (model_path / "config.json").write_text(
        json.dumps({"quantization_config": {"quant_method": "bitsandbytes", "load_in_4bit": True}}),
        encoding="utf-8",
    )

    assert module.LocalGemma4Engine._requires_unsloth_runtime(str(model_path)) is True


def test_importing_runner_does_not_import_heavy_model_modules() -> None:
    load_runner_module()

    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules
    assert "qwen_vl_utils" not in sys.modules
    assert "unsloth" not in sys.modules
