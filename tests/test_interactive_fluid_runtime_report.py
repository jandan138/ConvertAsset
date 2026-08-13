from __future__ import annotations

from convert_asset.asset_application_normalizer.interactive_fluid_scene import (
    classify_interactive_fluid_runtime_log,
)
from scripts.record_interactive_fluid_runtime_observation import finalize_package


def test_gpu_incompatible_convex_blocks_fluid_qualification() -> None:
    report = classify_interactive_fluid_runtime_log(
        "ConvexDecompositionTask: failed to cook GPU-compatible mesh. "
        "Non-GPU-compatible convex mesh is not able to collide with particle system."
    )
    assert report["overall_status"] == "blocked"
    assert report["gates"]["visual_mesh_convex_cooking"]["status"] == "blocked"
    assert "gpu_incompatible_visual_mesh_convex_decomposition" in report["blocked_reasons"]


def test_clean_log_does_not_invent_runtime_pass() -> None:
    report = classify_interactive_fluid_runtime_log("Isaac startup complete")
    assert report["overall_status"] == "incomplete"
    assert report["gates"]["visual_mesh_convex_cooking"]["status"] == "not_observed"


def test_finalize_package_records_report_in_hash_closure(tmp_path) -> None:
    package = tmp_path / "package"
    (package / "evidence/runtime_qualification").mkdir(parents=True)
    (package / "asset.usd").write_text("usd", encoding="utf-8")
    report = package / "evidence/runtime_qualification/report.json"
    report.write_text(
        '{"overall_status":"blocked","blocked_reasons":["x"]}\n',
        encoding="utf-8",
    )
    manifest = package / "evidence/manifest.json"
    manifest.write_text('{"closure":{"files":[]}}\n', encoding="utf-8")

    finalize_package(package, report)

    payload = __import__("json").loads(manifest.read_text())
    paths = {item["path"] for item in payload["closure"]["files"]}
    assert "evidence/runtime_qualification/report.json" in paths
    assert "evidence/manifest.json" not in paths
    assert payload["overall_status"] == "blocked"
