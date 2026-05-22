import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/build_canonical_vlm_run_manifest.py"


def load_manifest_module():
    spec = importlib.util.spec_from_file_location("grscenes_build_canonical_vlm_run_manifest", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scoring_record(pair_id: str, version: str, category: str = "cup") -> dict:
    return {
        "sample_id": f"{pair_id}.{version}",
        "pair_id": pair_id,
        "version": version,
        "task": "s1_referred_object_localization",
        "image": {"path": f"/renders/{pair_id}/{version}.png", "width": 600, "height": 450},
        "target": {"category": category, "bbox_xyxy": [10.0, 20.0, 50.0, 80.0]},
        "expected_answers": [category],
        "prediction": None,
    }


def projection_report(pair_ids: list[str]) -> dict:
    return {
        "schema_version": 1,
        "status": "projection_subset_report",
        "summary": {"selection_id": "pass_only", "selected_pair_count": len(pair_ids), "scoring_record_count": len(pair_ids) * 2},
        "selected_pair_ids": pair_ids,
        "pairs": [
            {
                "pair_id": pair_id,
                "target_id": pair_id.split(".")[0],
                "source_scene_id": "scene_usd",
                "view_id": pair_id.split(".")[-1],
                "projection": {"status": "projection_ok", "bbox_xyxy": [10.0, 20.0, 50.0, 80.0]},
                "status": "projection_ok",
            }
            for pair_id in pair_ids
        ],
        "scoring_records": [
            record
            for pair_id in pair_ids
            for record in [scoring_record(pair_id, "original"), scoring_record(pair_id, "converted")]
        ],
    }


def visual_review_report(verdicts: dict[str, str]) -> dict:
    return {
        "schema_version": 1,
        "status": "independent_visual_review_batch",
        "summary": {},
        "pairs": [
            {
                "packet_id": f"P{index:02d}",
                "pair_id": pair_id,
                "target_category": "cup",
                "verdict": verdict,
                "visible_evidence": f"{pair_id} visual evidence",
                "main_risk": f"{pair_id} risk",
                "retake_recommendation": f"{pair_id} retake",
            }
            for index, (pair_id, verdict) in enumerate(verdicts.items(), start=1)
        ],
    }


def source(path: str, report: dict) -> dict:
    return {"path": path, "hash_sha256": "a" * 64, "report": report}


def test_build_manifest_splits_pass_warn_fail_and_blocks_small_final_gate() -> None:
    module = load_manifest_module()

    manifest = module.build_canonical_vlm_run_manifest(
        projection_report(["p01.view_001", "p02.view_003"]),
        visual_review_sources=[source("visual.json", visual_review_report({"p01.view_001": "PASS", "p02.view_003": "PASS", "p03.view_000": "WARN", "p04.view_000": "FAIL"}))],
        protocol={"schema_version": 2},
        min_pass_pairs=3,
        selection_id="canonical_pass_only_v1",
    )

    assert manifest["status"] == "canonical_vlm_run_manifest"
    assert manifest["claim_status"] == "pilot_only"
    assert manifest["final_benchmark_claimable"] is False
    assert manifest["summary"]["pass_pair_count"] == 2
    assert manifest["summary"]["pass_scoring_record_count"] == 4
    assert manifest["summary"]["warn_pair_count"] == 1
    assert manifest["summary"]["fail_pair_count"] == 1
    assert manifest["summary"]["ready_for_final_benchmark_run"] is False
    assert manifest["summary"]["ready_for_pilot_model_run"] is True
    assert "pass_pair_count_below_minimum_final_benchmark_gate" in manifest["summary"]["blockers"]
    assert manifest["claim_gate"]["claim_status"] == "pilot_only"
    assert manifest["claim_gate"]["final_benchmark_claimable"] is False
    assert "only_four_visual_qa_pass_pairs" in manifest["claim_gate"]["blocked_by"]
    assert "canonical_predictions_missing" in manifest["claim_gate"]["blocked_by"]
    assert "not a final GRScenes benchmark result" in manifest["claim_gate"]["forbidden_claims"]
    assert manifest["protocol"]["coordinate_frame"] == "normalized_1000"
    assert manifest["protocol"]["response_format"] == "structured_text"
    assert manifest["protocol"]["primary_point_metric"] == "point_in_bbox_normalized_1000_accuracy"
    assert [pair["pair_id"] for pair in manifest["selected_pairs"]] == ["p01.view_001", "p02.view_003"]
    assert manifest["scoring_records"][0]["visual_review"]["verdict"] == "PASS"
    assert [pair["pair_id"] for pair in manifest["retake_candidates"]] == ["p03.view_000"]
    assert [pair["pair_id"] for pair in manifest["excluded_pairs"]] == ["p04.view_000"]


def test_build_manifest_blocks_selected_pairs_without_pass_visual_review() -> None:
    module = load_manifest_module()

    manifest = module.build_canonical_vlm_run_manifest(
        projection_report(["p01.view_001", "p02.view_003"]),
        visual_review_sources=[source("visual.json", visual_review_report({"p01.view_001": "PASS", "p02.view_003": "WARN"}))],
        protocol={"schema_version": 2},
        min_pass_pairs=1,
        selection_id="canonical_pass_only_v1",
    )

    assert manifest["summary"]["ready_for_pilot_model_run"] is False
    assert manifest["summary"]["ready_for_final_benchmark_run"] is False
    assert "selected_pair_without_pass_visual_review" in manifest["summary"]["blockers"]
    assert [pair["pair_id"] for pair in manifest["selected_pairs"]] == ["p01.view_001"]
    assert manifest["rejected_selected_pairs"][0]["pair_id"] == "p02.view_003"
    assert manifest["rejected_selected_pairs"][0]["visual_review"]["verdict"] == "WARN"


def test_main_writes_manifest_with_hashes_and_runner_compatible_records(tmp_path: Path) -> None:
    module = load_manifest_module()
    projection_path = tmp_path / "projection.json"
    visual_path = tmp_path / "visual.json"
    protocol_path = tmp_path / "protocol.yaml"
    out_path = tmp_path / "canonical.json"
    projection_path.write_text(json.dumps(projection_report(["p01.view_001"])), encoding="utf-8")
    visual_path.write_text(json.dumps(visual_review_report({"p01.view_001": "PASS"})), encoding="utf-8")
    protocol_path.write_text("schema_version: 2\n", encoding="utf-8")

    status = module.main(
        [
            "--projection-report",
            str(projection_path),
            "--visual-review-report",
            str(visual_path),
            "--protocol",
            str(protocol_path),
            "--min-pass-pairs",
            "1",
            "--out",
            str(out_path),
        ]
    )

    assert status == 0
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(written["inputs"]["projection_report"]["hash_sha256"]) == 64
    assert len(written["inputs"]["visual_review_reports"][0]["hash_sha256"]) == 64
    assert len(written["inputs"]["runner"]["hash_sha256"]) == 64
    assert len(written["inputs"]["scorer"]["hash_sha256"]) == 64
    assert written["summary"]["ready_for_final_benchmark_run"] is True
    assert written["summary"]["claim_boundary"] == "canonical_input_manifest_only_not_model_metric_evidence"
    assert written["claim_gate"]["claim_status"] == "pilot_only"
    assert written["claim_gate"]["final_benchmark_claimable"] is False
    assert "canonical_score_summary_missing" in written["claim_gate"]["blocked_by"]
    assert written["scoring_records"][0]["prediction"] is None
    assert written["scoring_records"][0]["prompt_contract"]["coordinate_frame"] == "normalized_1000"
    assert written["scoring_records"][0]["image"]["hash_sha256"] is None
