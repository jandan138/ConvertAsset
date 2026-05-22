import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py"


def load_score_module():
    spec = importlib.util.spec_from_file_location("grscenes_score_grounding", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(pair_id: str, version: str, point_xy: list[float], answer: str = "cup") -> dict:
    return {
        "sample_id": f"{pair_id}.{version}",
        "pair_id": pair_id,
        "version": version,
        "task": "s1_referred_object_localization",
        "target": {"bbox_xyxy": [10.0, 10.0, 30.0, 30.0]},
        "prediction": {"point_xy": point_xy, "answer": answer},
        "expected_answers": ["cup"],
        "model_checkpoint": "projection_center_smoke_baseline_no_vlm",
    }


def test_score_reports_original_converted_pair_consistency() -> None:
    module = load_score_module()

    result = module.score(
        [
            record("pair_a", "original", [20.0, 20.0]),
            record("pair_a", "converted", [22.0, 20.0]),
            record("pair_b", "original", [20.0, 20.0]),
            record("pair_b", "converted", [80.0, 80.0]),
        ]
    )

    consistency = result["pair_consistency"]
    assert consistency["pair_count"] == 2
    assert consistency["point_pair_count"] == 2
    assert consistency["point_hit_agreement"] == 0.5
    assert consistency["both_point_hit_count"] == 1
    assert consistency["mean_prediction_point_delta_px"] == 43.426407
    assert consistency["answer_pair_count"] == 2
    assert consistency["answer_match_agreement"] == 1.0
    assert result["prediction_backends"] == ["unknown"]
    assert result["model_checkpoints"] == ["projection_center_smoke_baseline_no_vlm"]


def test_score_marks_projection_center_baseline_as_scoring_smoke_only() -> None:
    module = load_score_module()
    baseline_record = record("pair_a", "original", [20.0, 20.0])
    baseline_record["prediction"]["backend"] = "projection_center_smoke_baseline"

    result = module.score([baseline_record])

    assert result["prediction_backends"] == ["projection_center_smoke_baseline"]
    assert result["claim_boundary"] == "scoring_smoke_only_not_vlm_evidence"


def test_score_marks_mixed_baseline_and_model_predictions_as_not_claimable() -> None:
    module = load_score_module()
    baseline_record = record("pair_a", "original", [20.0, 20.0])
    baseline_record["prediction"]["backend"] = "projection_center_smoke_baseline"
    model_record = record("pair_a", "converted", [20.0, 20.0])
    model_record["prediction"]["backend"] = "local_hf_qwen2_5_vl"
    model_record["model_checkpoint"] = "/models/qwen"

    result = module.score([baseline_record, model_record])

    assert result["prediction_backends"] == [
        "local_hf_qwen2_5_vl",
        "projection_center_smoke_baseline",
    ]
    assert result["claim_boundary"] == "mixed_projection_baseline_and_model_predictions_not_claimable"


def test_pair_consistency_does_not_mix_tasks_with_same_pair_id() -> None:
    module = load_score_module()
    s1_original = record("pair_a", "original", [20.0, 20.0])
    s1_converted = record("pair_a", "converted", [20.0, 20.0])
    s2_original = record("pair_a", "original", [20.0, 20.0])
    s2_converted = record("pair_a", "converted", [80.0, 80.0])
    for item in [s2_original, s2_converted]:
        item["task"] = "s2_object_attribute"

    result = module.score([s1_original, s1_converted, s2_original, s2_converted])

    consistency = result["pair_consistency"]
    assert consistency["pair_count"] == 2
    assert consistency["point_pair_count"] == 2
    assert consistency["point_hit_agreement"] == 0.5
    assert consistency["both_point_hit_count"] == 1


def test_pair_consistency_reports_duplicate_pair_version_rows() -> None:
    module = load_score_module()

    result = module.score(
        [
            record("pair_a", "original", [20.0, 20.0]),
            record("pair_a", "original", [80.0, 80.0]),
            record("pair_a", "converted", [20.0, 20.0]),
        ]
    )

    consistency = result["pair_consistency"]
    assert consistency["pair_count"] == 1
    assert consistency["duplicate_pair_version_count"] == 1
    assert consistency["both_point_hit_count"] == 1


def test_score_treats_malformed_and_non_finite_points_as_unscored() -> None:
    module = load_score_module()
    bad_point = record("pair_a", "original", [20.0, 20.0])
    bad_point["prediction"]["point_xy"] = [float("nan"), 20.0]
    bad_box = record("pair_a", "converted", [20.0, 20.0])
    bad_box["target"]["bbox_xyxy"] = ["bad", 10.0, 30.0, 30.0]

    result = module.score([bad_point, bad_box])

    assert [row["point_in_bbox"] for row in result["records"]] == [None, None]
    assert result["pair_consistency"]["point_pair_count"] == 0
    json.dumps(result, allow_nan=False)


def test_score_rejects_string_coordinates_and_non_dict_schema_objects() -> None:
    module = load_score_module()
    string_point = record("pair_a", "original", [20.0, 20.0])
    string_point["prediction"]["point_xy"] = "25"
    string_box = record("pair_a", "converted", [20.0, 20.0])
    string_box["target"]["bbox_xyxy"] = "1234"
    non_dict_prediction = record("pair_b", "original", [20.0, 20.0])
    non_dict_prediction["prediction"] = "bad"
    non_dict_target = record("pair_b", "converted", [20.0, 20.0])
    non_dict_target["target"] = "bad"

    result = module.score([string_point, string_box, non_dict_prediction, non_dict_target])

    assert [row["point_in_bbox"] for row in result["records"]] == [None, None, None, None]
    assert result["pair_consistency"]["point_pair_count"] == 0
    json.dumps(result, allow_nan=False)


def test_main_writes_score_provenance(tmp_path: Path) -> None:
    module = load_score_module()
    predictions = tmp_path / "predictions.jsonl"
    out = tmp_path / "score_summary.json"
    row = record("pair_a", "original", [20.0, 20.0])
    row["prediction"]["backend"] = "projection_center_smoke_baseline"
    predictions.write_text(json.dumps(row) + "\n", encoding="utf-8")

    status = module.main(["--predictions", str(predictions), "--out", str(out)])

    assert status == 0
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["schema_version"] == 2
    provenance = result["score_provenance"]
    assert provenance["input_predictions"]["path"] == str(predictions)
    assert len(provenance["input_predictions"]["hash_sha256"]) == 64
    assert provenance["scorer"]["script_path"].endswith("score_grounding.py")
    assert len(provenance["scorer"]["script_hash_sha256"]) == 64
