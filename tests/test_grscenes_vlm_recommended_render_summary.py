import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/summarize_recommended_paired_renders.py"


def load_summary_module():
    spec = importlib.util.spec_from_file_location("grscenes_summarize_recommended_paired_renders", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(condition: str, pixels: int, image_path: str) -> dict:
    return {
        "sample_id": f"pair.view_000.{condition}",
        "material_condition": condition,
        "exit_code": 0,
        "image": {
            "path": image_path,
            "hash_sha256": "a" * 64,
            "non_dark_pixel_count": pixels,
            "width": 600,
            "height": 450,
        },
        "stderr_summary": {"counts": {"KooPbr": 0, "KooPbr_maps": 0}},
    }


def _report(pair_id: str, *, original_pixels: int, converted_pixels: int) -> dict:
    return {
        "pair_id": pair_id,
        "summary": {
            "both_commands_exit_zero": True,
            "both_images_exist": True,
            "original_mdl_error_signal": 7,
            "converted_mdl_error_signal": 0,
        },
        "records": [
            _record("original", original_pixels, f"/renders/{pair_id}/original.png"),
            _record("converted", converted_pixels, f"/renders/{pair_id}/converted.png"),
        ],
    }


def test_build_summary_requires_reports_for_all_recommended_pairs(tmp_path: Path) -> None:
    module = load_summary_module()
    preflight = {
        "recommended_pairs_by_target": {
            "target_a": {"pair_id": "pair_a.view_000"},
            "target_b": {"pair_id": "pair_b.view_000"},
        }
    }
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "pair_a.view_000.json").write_text(json.dumps(_report("pair_a.view_000", original_pixels=4, converted_pixels=5)))

    try:
        module.build_recommended_render_summary(preflight, report_dirs=[report_dir], fallback_reports=[])
    except FileNotFoundError as exc:
        assert "pair_b.view_000" in str(exc)
    else:
        raise AssertionError("missing recommended pair report should fail")


def test_build_summary_counts_non_dark_and_black_failures(tmp_path: Path) -> None:
    module = load_summary_module()
    preflight = {
        "summary": {"centerline_clear_pair_count": 2},
        "recommended_pairs_by_target": {
            "target_a": {"pair_id": "pair_a.view_000"},
            "target_b": {"pair_id": "pair_b.view_000"},
        },
    }
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "pair_a.view_000.json").write_text(json.dumps(_report("pair_a.view_000", original_pixels=4, converted_pixels=5)))
    (report_dir / "pair_b.view_000.json").write_text(json.dumps(_report("pair_b.view_000", original_pixels=0, converted_pixels=6)))

    summary = module.build_recommended_render_summary(preflight, report_dirs=[report_dir], fallback_reports=[])

    assert summary["summary"]["recommended_pair_count"] == 2
    assert summary["summary"]["reports_found_count"] == 2
    assert summary["summary"]["paired_non_dark_render_smoke_count"] == 1
    assert summary["summary"]["black_or_missing_image_count"] == 1
    assert summary["summary"]["render_smoke_pass_count"] == 1
    assert summary["summary"]["claim_boundary"] == "render_smoke_only_requires_projection_visual_qa_and_vlm_predictions"
    assert summary["pairs"][1]["render_smoke_pass"] is False


def test_main_writes_summary_with_fallback_report(tmp_path: Path) -> None:
    module = load_summary_module()
    preflight_path = tmp_path / "visibility_preflight_report.json"
    report_dir = tmp_path / "reports"
    fallback = tmp_path / "paired_render_smoke_report.json"
    out = tmp_path / "recommended_paired_render_summary.json"
    report_dir.mkdir()
    preflight_path.write_text(
        json.dumps({"recommended_pairs_by_target": {"target_a": {"pair_id": "pair_a.view_000"}}}),
        encoding="utf-8",
    )
    fallback.write_text(json.dumps(_report("pair_a.view_000", original_pixels=4, converted_pixels=5)), encoding="utf-8")

    status = module.main(
        [
            "--preflight-report",
            str(preflight_path),
            "--report-dir",
            str(report_dir),
            "--fallback-report",
            str(fallback),
            "--out",
            str(out),
        ]
    )

    assert status == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["summary"]["recommended_pair_count"] == 1
    assert written["summary"]["fallback_report_count"] == 1
    assert written["pairs"][0]["report_path"] == str(fallback)
    assert written["pairs"][0]["report_source"] == "fallback_report"
