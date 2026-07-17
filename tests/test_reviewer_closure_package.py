import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/09_reviewer_closure_package/build_reviewer_closure_package.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("reviewer_closure_package", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _score_record(sample_id: str, version: str, *, answer: bool | None, norm: bool | None, raw: bool | None) -> dict:
    return {
        "sample_id": f"{sample_id}.{version}",
        "version": version,
        "task": "s1_referred_object_localization",
        "answer_match": answer,
        "point_in_bbox_normalized_1000": norm,
        "point_in_bbox": raw,
    }


def test_bootstrap_ci_is_deterministic_for_identical_deltas() -> None:
    module = load_module()

    result = module.bootstrap_mean_ci([0.25, 0.25, 0.25], rounds=200, seed=7)

    assert result == {"mean": 0.25, "ci95_low": 0.25, "ci95_high": 0.25}


def test_vlm_paired_rows_compute_original_converted_delta_and_ci() -> None:
    module = load_module()
    score = {
        "schema_version": 5,
        "records": [
            _score_record("pair_a", "original", answer=True, norm=True, raw=False),
            _score_record("pair_a", "converted", answer=True, norm=False, raw=False),
            _score_record("pair_b", "original", answer=False, norm=False, raw=True),
            _score_record("pair_b", "converted", answer=True, norm=True, raw=True),
        ],
    }

    rows = module.build_vlm_stat_rows(score, evidence_id="gemma4_expanded30", model="Gemma4")
    by_metric = {row["metric_id"]: row for row in rows}

    assert by_metric["answer_accuracy"]["n"] == 2
    assert by_metric["answer_accuracy"]["original_mean"] == 0.5
    assert by_metric["answer_accuracy"]["converted_mean"] == 1.0
    assert by_metric["answer_accuracy"]["mean_delta_converted_minus_original"] == 0.5
    assert by_metric["norm1000_point"]["mean_delta_converted_minus_original"] == 0.0
    assert by_metric["raw_point"]["original_mean"] == 0.5
    assert by_metric["raw_point"]["converted_mean"] == 0.5
    assert by_metric["answer_accuracy"]["claim_boundary"] == "paired_bootstrap_ci_descriptive"


def test_internnav_rows_use_episode_level_deltas() -> None:
    module = load_module()
    transitions = [
        {
            "original_SR": 1.0,
            "nomdl_SR": 0.0,
            "delta_SR_nomdl_minus_original": -1.0,
            "original_NE": 5.0,
            "nomdl_NE": 4.0,
            "delta_NE_nomdl_minus_original": -1.0,
        },
        {
            "original_SR": 0.0,
            "nomdl_SR": 1.0,
            "delta_SR_nomdl_minus_original": 1.0,
            "original_NE": 3.0,
            "nomdl_NE": 2.0,
            "delta_NE_nomdl_minus_original": -1.0,
        },
    ]

    rows = module.build_internnav_stat_rows(transitions)
    by_metric = {row["metric_id"]: row for row in rows}

    assert by_metric["SR"]["n"] == 2
    assert by_metric["SR"]["original_mean"] == 0.5
    assert by_metric["SR"]["converted_mean"] == 0.5
    assert by_metric["SR"]["mean_delta_converted_minus_original"] == 0.0
    assert by_metric["NE"]["original_mean"] == 4.0
    assert by_metric["NE"]["converted_mean"] == 3.0
    assert by_metric["NE"]["mean_delta_converted_minus_original"] == -1.0
    assert by_metric["NE"]["direction"] == "noMDL lower"


def _projection_record(version: str) -> dict:
    return {
        "sample_id": f"pair_001.{version}",
        "pair_id": "pair_001",
        "version": version,
        "task": "s1_referred_object_localization",
        "image": {"width": 100, "height": 100, "path": f"/tmp/{version}.png"},
        "target": {"bbox_xyxy": [10.0, 20.0, 30.0, 60.0], "category": "cup"},
        "expected_answers": ["cup"],
        "prediction": None,
    }


def test_coordinate_baselines_include_pixel_and_normalized_oracles() -> None:
    module = load_module()
    projection_report = {"scoring_records": [_projection_record("original"), _projection_record("converted")]}

    rows, artifacts = module.build_coordinate_baseline_package(projection_report)
    by_id = {row["baseline_id"]: row for row in rows}

    assert set(by_id) == {
        "random_seeded_pixel",
        "image_center_pixel",
        "bbox_center_pixel",
        "bbox_center_normalized_1000",
    }
    assert by_id["bbox_center_pixel"]["raw_point_original"] == "1/1"
    assert by_id["bbox_center_pixel"]["norm1000_point_original"] == "0/1"
    assert by_id["bbox_center_normalized_1000"]["raw_point_original"] == "0/1"
    assert by_id["bbox_center_normalized_1000"]["norm1000_point_original"] == "1/1"
    assert artifacts["bbox_center_pixel"]["predictions"][0]["prediction"]["point_xy"] == [20.0, 40.0]
    assert artifacts["bbox_center_normalized_1000"]["predictions"][0]["prediction"]["point_xy"] == [200.0, 400.0]


def test_recommender_maps_risk_matrix_to_actions() -> None:
    module = load_module()
    risk_profile = {
        "rows": [
            {
                "effect": "normal_bump",
                "sample_source": "GRScenes expanded30",
                "claim_allowed": "bounded_static_and_selected_qualitative",
                "qualitative_status": "selected_panel_ready",
                "convertasset_risk": "bounded_visual_review_warn_or_pass",
                "nvidia_risk": "bounded_visual_review_warn_or_pass",
            },
            {
                "effect": "clearcoat",
                "sample_source": "supplemental_official_or_sample_wrapper",
                "claim_allowed": "selected_nvidia_failure_case",
                "qualitative_status": "supplemental_visual_fail",
                "convertasset_risk": "clearcoat_approximated_by_preview_surface",
                "nvidia_risk": "target_missing",
            },
            {
                "effect": "procedural_texture",
                "sample_source": "supplemental_official_or_sample_wrapper",
                "claim_allowed": "diagnostic_limitation_case",
                "qualitative_status": "supplemental_visual_fail",
                "convertasset_risk": "checker_not_preserved",
                "nvidia_risk": "checker_not_preserved",
            },
        ]
    }

    rows = module.build_safe_conversion_recommender_rows(risk_profile)
    by_effect = {row["effect"]: row for row in rows}

    assert by_effect["normal_bump"]["risk_level"] == "bounded_low"
    assert by_effect["normal_bump"]["convertasset_action"] == "convert_with_static_gate_and_selected_visual_review"
    assert by_effect["clearcoat"]["risk_level"] == "manual_review_high"
    assert by_effect["clearcoat"]["nvidia_action"] == "do_not_trust_without_target_retention_gate"
    assert by_effect["procedural_texture"]["risk_level"] == "high"
    assert by_effect["procedural_texture"]["convertasset_action"] == "keep_mdl_or_bake_before_claiming_preservation"


def test_write_table_outputs_create_csv_and_latex(tmp_path: Path) -> None:
    module = load_module()
    rows = [
        {
            "dataset": "GRScenes VLM expanded30",
            "evidence_id": "gemma4_expanded30",
            "metric_id": "answer_accuracy",
            "metric": "Answer accuracy",
            "n": 30,
            "original_mean": 1.0,
            "converted_mean": 1.0,
            "mean_delta_converted_minus_original": 0.0,
            "ci95_low": 0.0,
            "ci95_high": 0.0,
            "direction": "tie",
            "claim_boundary": "paired_bootstrap_ci_descriptive",
        }
    ]
    csv_path = tmp_path / "stats.csv"
    tex_path = tmp_path / "stats.tex"

    module.write_stat_table(csv_path, tex_path, rows)

    loaded = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    assert loaded[0]["metric_id"] == "answer_accuracy"
    tex = tex_path.read_text(encoding="utf-8")
    assert "\\label{tab:reviewer_closure_paired_ci}" in tex
    assert "Paired bootstrap confidence intervals" in tex
