import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/build_stress_vlm_run_manifest.py"


def load_manifest_module():
    spec = importlib.util.spec_from_file_location("grscenes_build_stress_vlm_run_manifest", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scoring_record(pair_id: str, version: str, category: str) -> dict:
    return {
        "sample_id": f"{pair_id}.{version}",
        "pair_id": pair_id,
        "version": version,
        "task": "s1_referred_object_localization",
        "image": {"path": f"/renders/{pair_id}/{version}.png", "width": 600, "height": 450},
        "target": {"category": category, "bbox_xyxy": [100.0, 120.0, 300.0, 360.0]},
        "expected_answers": [category],
        "prediction": None,
    }


def projection_report(pair_categories: dict[str, str]) -> dict:
    return {
        "schema_version": 1,
        "status": "projection_subset_report",
        "summary": {
            "selection_id": "zoom_stress",
            "selected_pair_count": len(pair_categories),
            "scoring_record_count": len(pair_categories) * 2,
        },
        "selected_pair_ids": list(pair_categories),
        "pairs": [
            {
                "pair_id": pair_id,
                "target_id": pair_id.split(".")[0],
                "source_scene_id": "scene_usd",
                "view_id": pair_id.split(".")[-1],
                "projection": {"status": "projection_ok", "bbox_xyxy": [100.0, 120.0, 300.0, 360.0]},
                "status": "projection_ok",
            }
            for pair_id in pair_categories
        ],
        "scoring_records": [
            record
            for pair_id, category in pair_categories.items()
            for record in [
                scoring_record(pair_id, "original", category),
                scoring_record(pair_id, "converted", category),
            ]
        ],
    }


def visual_review_report(verdicts: dict[str, tuple[str, str]]) -> dict:
    return {
        "schema_version": 1,
        "status": "independent_visual_review_batch",
        "summary": {},
        "pairs": [
            {
                "packet_id": f"S{index:02d}",
                "pair_id": pair_id,
                "target_category": category,
                "verdict": verdict,
                "visible_evidence": f"{pair_id} target visible",
                "main_risk_or_retake": f"{pair_id} stress risk",
            }
            for index, (pair_id, (verdict, category)) in enumerate(verdicts.items(), start=1)
        ],
    }


def source(path: str, report: dict) -> dict:
    return {"path": path, "hash_sha256": "a" * 64, "report": report}


def test_build_stress_manifest_accepts_pass_and_warn_but_excludes_fail() -> None:
    module = load_manifest_module()
    pair_categories = {
        "p01.zoom_016": "clock",
        "p02.zoom_017": "faucet",
        "p03.zoom_018": "pillow",
    }

    manifest = module.build_stress_vlm_run_manifest(
        projection_report(pair_categories),
        visual_review_sources=[
            source(
                "visual.json",
                visual_review_report(
                    {
                        "p01.zoom_016": ("PASS", "clock"),
                        "p02.zoom_017": ("WARN", "faucet"),
                        "p03.zoom_018": ("FAIL", "pillow"),
                    }
                ),
            )
        ],
        protocol={"schema_version": 2},
        min_stress_pairs=2,
        min_target_categories=2,
        predictions_path=Path("/missing/predictions.jsonl"),
        score_summary_path=Path("/missing/score_summary.json"),
        selection_id="stress_v1",
    )

    assert manifest["status"] == "stress_vlm_run_manifest"
    assert manifest["claim_status"] == "pilot_only"
    assert manifest["final_benchmark_claimable"] is False
    assert manifest["summary"]["stress_pair_count"] == 2
    assert manifest["summary"]["stress_scoring_record_count"] == 4
    assert manifest["summary"]["stress_verdict_counts"] == {"PASS": 1, "WARN": 1}
    assert manifest["summary"]["excluded_pair_count"] == 1
    assert manifest["summary"]["selected_target_category_counts"] == {"clock": 1, "faucet": 1}
    assert manifest["summary"]["ready_for_model_run"] is True
    assert manifest["summary"]["ready_for_final_benchmark_run"] is False
    assert "canonical_predictions_missing" in manifest["summary"]["blockers"]
    assert "canonical_score_summary_missing" in manifest["summary"]["blockers"]
    assert [pair["pair_id"] for pair in manifest["selected_pairs"]] == ["p01.zoom_016", "p02.zoom_017"]
    assert [pair["pair_id"] for pair in manifest["excluded_pairs"]] == ["p03.zoom_018"]
    assert manifest["scoring_records"][1]["visual_review"]["verdict"] == "PASS"
    assert manifest["scoring_records"][2]["visual_review"]["verdict"] == "WARN"
    assert "not a clean material-preservation benchmark" in manifest["claim_gate"]["forbidden_claims"]


def test_build_stress_manifest_blocks_final_gate_when_category_coverage_is_too_small() -> None:
    module = load_manifest_module()
    pair_categories = {
        "p01.zoom_016": "clock",
        "p02.zoom_017": "clock",
    }

    manifest = module.build_stress_vlm_run_manifest(
        projection_report(pair_categories),
        visual_review_sources=[
            source(
                "visual.json",
                visual_review_report(
                    {
                        "p01.zoom_016": ("PASS", "clock"),
                        "p02.zoom_017": ("WARN", "clock"),
                    }
                ),
            )
        ],
        protocol={"schema_version": 2},
        min_stress_pairs=2,
        min_target_categories=2,
        predictions_path=Path("/missing/predictions.jsonl"),
        score_summary_path=Path("/missing/score_summary.json"),
        selection_id="stress_v1",
    )

    assert manifest["summary"]["ready_for_model_run"] is True
    assert "target_category_count_below_minimum_final_benchmark_gate" in manifest["summary"]["blockers"]
    assert manifest["claim_gate"]["final_benchmark_claimable"] is False
    assert manifest["claim_gate"]["claim_status"] == "pilot_only"


def test_build_stress_manifest_excludes_non_runnable_pairs() -> None:
    module = load_manifest_module()
    report = projection_report(
        {
            "p01.zoom_016": "clock",
            "p02.zoom_017": "faucet",
            "p03.zoom_018": "pillow",
        }
    )
    report["pairs"][1]["status"] = "projection_too_small"

    manifest = module.build_stress_vlm_run_manifest(
        report,
        visual_review_sources=[
            source(
                "visual.json",
                visual_review_report(
                    {
                        "p01.zoom_016": ("MAYBE", "clock"),
                        "p02.zoom_017": ("PASS", "faucet"),
                    }
                ),
            )
        ],
        protocol={"schema_version": 2},
        min_stress_pairs=1,
        min_target_categories=1,
        predictions_path=Path("/missing/predictions.jsonl"),
        score_summary_path=Path("/missing/score_summary.json"),
        selection_id="stress_v1",
    )

    assert manifest["summary"]["ready_for_model_run"] is False
    assert manifest["summary"]["unsupported_verdict_pair_ids"] == ["p01.zoom_016"]
    assert manifest["summary"]["projection_blocked_pair_ids"] == ["p02.zoom_017"]
    assert manifest["summary"]["missing_visual_review_pair_ids"] == ["p03.zoom_018"]
    assert manifest["summary"]["model_run_blockers"] == [
        "empty_scoring_records",
        "missing_visual_review_pairs",
        "projection_blocked_pairs_present",
        "unsupported_visual_review_verdicts_present",
    ]
    assert manifest["selected_pairs"] == []
    assert [pair["pair_id"] for pair in manifest["excluded_pairs"]] == [
        "p01.zoom_016",
        "p02.zoom_017",
        "p03.zoom_018",
    ]


def test_main_writes_stress_manifest_with_input_hashes(tmp_path: Path) -> None:
    module = load_manifest_module()
    projection_path = tmp_path / "projection.json"
    visual_path = tmp_path / "visual.json"
    protocol_path = tmp_path / "protocol.yaml"
    out_path = tmp_path / "stress_manifest.json"
    projection_path.write_text(json.dumps(projection_report({"p01.zoom_016": "clock"})), encoding="utf-8")
    visual_path.write_text(json.dumps(visual_review_report({"p01.zoom_016": ("WARN", "clock")})), encoding="utf-8")
    protocol_path.write_text("schema_version: 2\n", encoding="utf-8")

    status = module.main(
        [
            "--projection-report",
            str(projection_path),
            "--visual-review-report",
            str(visual_path),
            "--protocol",
            str(protocol_path),
            "--min-stress-pairs",
            "1",
            "--min-target-categories",
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
    assert written["summary"]["ready_for_model_run"] is True
    assert written["summary"]["stress_pair_count"] == 1
    assert written["scoring_records"][0]["prompt_contract"]["coordinate_frame"] == "normalized_1000"
    assert written["scoring_records"][0]["prediction"] is None
