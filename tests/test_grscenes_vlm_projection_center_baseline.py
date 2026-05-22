import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/generate_projection_center_baseline_predictions.py"


def load_baseline_module():
    spec = importlib.util.spec_from_file_location("grscenes_projection_center_baseline", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scoring_record() -> dict:
    return {
        "sample_id": "pair.view_000.original",
        "pair_id": "pair.view_000",
        "version": "original",
        "task": "s1_referred_object_localization",
        "image": {"path": "/renders/original.png", "width": 100, "height": 100},
        "target": {"bbox_xyxy": [10.0, 20.0, 30.0, 60.0], "category": "cup"},
        "expected_answers": ["cup"],
        "prediction": None,
    }


def test_build_prediction_uses_bbox_center_and_category() -> None:
    module = load_baseline_module()

    first = module.build_prediction(scoring_record())
    second = module.build_prediction(scoring_record())

    assert first == second
    assert "prediction_generated_at_utc" not in first
    assert first["prediction"]["point_xy"] == [20.0, 40.0]
    assert first["prediction"]["answer"] == "cup"
    assert first["prediction"]["backend"] == "projection_center_smoke_baseline"
    assert first["model_checkpoint"] == "projection_center_smoke_baseline_no_vlm"


def test_main_writes_jsonl_predictions(tmp_path: Path) -> None:
    module = load_baseline_module()
    projection_report = {
        "scoring_records": [scoring_record()],
        "summary": {"scoring_record_count": 1},
    }
    projection_path = tmp_path / "target_projection_qa_report.json"
    out = tmp_path / "projection_center_baseline_predictions.jsonl"
    projection_path.write_text(json.dumps(projection_report), encoding="utf-8")

    status = module.main(["--projection-report", str(projection_path), "--out", str(out)])

    assert status == 0
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["prediction"]["point_xy"] == [20.0, 40.0]
    metadata = json.loads(out.with_suffix(out.suffix + ".metadata.json").read_text(encoding="utf-8"))
    assert metadata["backend"] == "projection_center_smoke_baseline"
    assert metadata["claim_boundary"] == "scoring_smoke_only_not_vlm_evidence"
    assert len(metadata["projection_report"]["hash_sha256"]) == 64
    assert len(metadata["output_jsonl"]["hash_sha256"]) == 64
