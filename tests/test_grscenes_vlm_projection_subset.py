import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/select_projection_subset.py"


def load_subset_module():
    spec = importlib.util.spec_from_file_location("grscenes_select_projection_subset", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def projection_report(pair_id: str, *, category: str = "cup") -> dict:
    return {
        "schema_version": 1,
        "status": "target_projection_qa_report",
        "summary": {"image_width": 600, "image_height": 450},
        "pairs": [
            {
                "pair_id": pair_id,
                "target_id": pair_id.split(".")[0],
                "projection": {"status": "projection_ok", "bbox_xyxy": [1, 2, 3, 4]},
                "status": "projection_ok",
            }
        ],
        "scoring_records": [
            {
                "sample_id": f"{pair_id}.original",
                "pair_id": pair_id,
                "version": "original",
                "task": "s1_referred_object_localization",
                "image": {"path": f"/renders/{pair_id}/original.png", "width": 600, "height": 450},
                "target": {"category": category, "bbox_xyxy": [1, 2, 3, 4]},
                "expected_answers": [category],
            },
            {
                "sample_id": f"{pair_id}.converted",
                "pair_id": pair_id,
                "version": "converted",
                "task": "s1_referred_object_localization",
                "image": {"path": f"/renders/{pair_id}/converted.png", "width": 600, "height": 450},
                "target": {"category": category, "bbox_xyxy": [1, 2, 3, 4]},
                "expected_answers": [category],
            },
        ],
    }


def test_build_subset_preserves_requested_pair_order_across_reports() -> None:
    module = load_subset_module()

    subset = module.build_projection_subset(
        [
            {"path": "first.json", "hash_sha256": "a" * 64, "report": projection_report("p01.view_001")},
            {"path": "second.json", "hash_sha256": "b" * 64, "report": projection_report("p02.view_003")},
        ],
        pair_ids=["p02.view_003", "p01.view_001"],
        selection_id="pass_only",
    )

    assert subset["summary"]["selection_mode"] == "explicit_pair_ids_from_projection_reports"
    assert subset["summary"]["selected_pair_count"] == 2
    assert subset["summary"]["projection_ok_pair_count"] == 2
    assert subset["summary"]["scoring_record_count"] == 4
    assert [item["pair_id"] for item in subset["pairs"]] == ["p02.view_003", "p01.view_001"]
    assert [item["pair_id"] for item in subset["scoring_records"]] == [
        "p02.view_003",
        "p02.view_003",
        "p01.view_001",
        "p01.view_001",
    ]
    assert [item["path"] for item in subset["source_projection_reports"]] == ["first.json", "second.json"]


def test_build_subset_rejects_missing_or_duplicate_selected_pairs() -> None:
    module = load_subset_module()

    reports = [
        {"path": "first.json", "hash_sha256": "a" * 64, "report": projection_report("p01.view_001")},
        {"path": "second.json", "hash_sha256": "b" * 64, "report": projection_report("p01.view_001")},
    ]
    try:
        module.build_projection_subset(reports, pair_ids=["p01.view_001"], selection_id="pass_only")
    except ValueError as exc:
        assert "selected pair appears in multiple reports" in str(exc)
    else:
        raise AssertionError("duplicate selected pair should fail")

    try:
        module.build_projection_subset(
            reports[:1],
            pair_ids=["p01.view_001", "p01.view_001"],
            selection_id="pass_only",
        )
    except ValueError as exc:
        assert "selected pair requested more than once" in str(exc)
    else:
        raise AssertionError("repeated requested pair should fail")

    try:
        module.build_projection_subset(reports[:1], pair_ids=["missing.view_000"], selection_id="pass_only")
    except KeyError as exc:
        assert "missing.view_000" in str(exc)
    else:
        raise AssertionError("missing selected pair should fail")


def test_main_writes_subset_with_source_hashes(tmp_path: Path) -> None:
    module = load_subset_module()
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    out = tmp_path / "pass_only_projection.json"
    first.write_text(json.dumps(projection_report("p01.view_001")), encoding="utf-8")
    second.write_text(json.dumps(projection_report("p02.view_003", category="faucet")), encoding="utf-8")

    status = module.main(
        [
            "--projection-report",
            str(first),
            "--projection-report",
            str(second),
            "--pair-id",
            "p01.view_001",
            "--pair-id",
            "p02.view_003",
            "--selection-id",
            "gemma4_pass_only_visual_qa",
            "--out",
            str(out),
        ]
    )

    assert status == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["summary"]["selection_id"] == "gemma4_pass_only_visual_qa"
    assert written["summary"]["selected_pair_count"] == 2
    assert len(written["source_projection_reports"][0]["hash_sha256"]) == 64
    assert len(written["generator_provenance"]["script_hash_sha256"]) == 64
