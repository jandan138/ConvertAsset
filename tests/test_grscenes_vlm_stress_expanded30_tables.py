import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/tables/gen_vlm_stress_expanded30.py"


def load_table_module():
    spec = importlib.util.spec_from_file_location("grscenes_vlm_stress_expanded30_table", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_score(path: Path, *, backend: str, original_norm: float, converted_norm: float) -> None:
    score = {
        "schema_version": 5,
        "num_records": 60,
        "prediction_backends": [backend],
        "summary": [
            {
                "version": "converted",
                "n_answer": 30,
                "answer_accuracy": 1.0,
                "n_point": 30,
                "point_in_bbox_accuracy": 1 / 30,
                "n_point_normalized_1000": 30,
                "point_in_bbox_normalized_1000_accuracy": converted_norm,
            },
            {
                "version": "original",
                "n_answer": 30,
                "answer_accuracy": 1.0,
                "n_point": 30,
                "point_in_bbox_accuracy": 1 / 30,
                "n_point_normalized_1000": 30,
                "point_in_bbox_normalized_1000_accuracy": original_norm,
            },
        ],
        "pair_consistency": {
            "pair_count": 30,
            "point_pair_count": 30,
            "point_hit_agreement": 1.0,
            "both_point_hit_count": 1,
            "normalized_1000_point_pair_count": 30,
            "normalized_1000_point_hit_agreement": 28 / 30,
            "normalized_1000_both_point_hit_count": 27,
            "answer_pair_count": 30,
            "answer_match_agreement": 1.0,
        },
    }
    path.write_text(json.dumps(score), encoding="utf-8")


def test_build_rows_reports_expanded30_stress_ratios(tmp_path: Path) -> None:
    module = load_table_module()
    gemma_score = tmp_path / "stress_score_summary.json"
    qwen_score = tmp_path / "qwen_score_summary.json"
    write_score(gemma_score, backend="local_gemma4_multimodal", original_norm=0.9, converted_norm=29 / 30)
    write_score(qwen_score, backend="local_hf_qwen", original_norm=3 / 30, converted_norm=3 / 30)

    rows = module.build_rows(
        probes=[
            {
                "row_id": "gemma4_expanded30",
                "model": "Gemma4 local",
                "role": "canonical",
                "response_format": "structured_text",
                "coordinate_policy": "normalized-1000",
                "score_path": gemma_score,
                "claim_boundary": "final stress benchmark",
            },
            {
                "row_id": "qwen25_expanded30",
                "model": "Qwen2.5-VL",
                "role": "diagnostic",
                "response_format": "structured_text",
                "coordinate_policy": "normalized-1000",
                "score_path": qwen_score,
                "claim_boundary": "second model diagnostic",
            },
        ]
    )

    assert rows[0]["pair_count"] == "30"
    assert rows[0]["answer_original"] == "30/30"
    assert rows[0]["answer_converted"] == "30/30"
    assert rows[0]["raw_point_original"] == "1/30"
    assert rows[0]["raw_point_converted"] == "1/30"
    assert rows[0]["norm1000_point_original"] == "27/30"
    assert rows[0]["norm1000_point_converted"] == "29/30"
    assert rows[0]["norm1000_pair_hit_agreement"] == "28/30"
    assert rows[0]["norm1000_both_hit_pairs"] == "27/30"
    assert rows[1]["role"] == "diagnostic"


def test_latex_caption_uses_frozen_stress_set_language() -> None:
    module = load_table_module()

    latex = module.render_latex(
        [
            {
                "model": "Gemma4 local",
                "role": "canonical",
                "answer_rows": "60/60",
                "answer_original": "30/30",
                "answer_converted": "30/30",
                "raw_point_original": "1/30",
                "raw_point_converted": "1/30",
                "norm1000_point_original": "27/30",
                "norm1000_point_converted": "29/30",
                "norm1000_pair_hit_agreement": "28/30",
                "norm1000_both_hit_pairs": "27/30",
            }
        ]
    )

    assert "frozen 30-pair target-centered stress set" in latex
    assert "stress benchmark" not in latex
