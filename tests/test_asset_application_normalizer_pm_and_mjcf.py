import json
from pathlib import Path

from convert_asset.asset_application_normalizer.pm_evidence_table import (
    build_pm_evidence_table,
    render_pm_evidence_markdown,
)
from convert_asset.asset_application_normalizer.mjcf_scout import build_mjcf_scout_manifest


def _write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_pm_evidence_table_maps_ready_and_blocked_rows(tmp_path: Path) -> None:
    ready_manifest = _write_json(
        tmp_path / "ready_manifest.json",
        {
            "schema_version": "asset_application_normalizer.v1",
            "asset_id": "Beaker_01",
            "task_id": "AAN08.TransparentBeaker",
            "overall_status": "pass",
            "milestone": "AAN-07-benchmark-contract",
            "source": {"path": "/assets/Beaker_01.usd", "source_format": "usd"},
            "target": {
                "target_runtime_profile": "isaac41",
                "target_benchmark_profile": "ebench-lift2",
            },
            "stage_gates": [
                {"stage": "usd_closure", "status": "pass"},
                {"stage": "material_closure", "status": "pass"},
                {"stage": "physics_static", "status": "pass"},
                {"stage": "runtime_smoke", "status": "pass"},
                {"stage": "benchmark_contract", "status": "pass"},
            ],
            "runtime_evidence": {
                "status": "pass",
                "render_readback": {
                    "status": "pass",
                    "non_background_ratio": 0.3,
                    "bbox_ratio": 0.4,
                },
            },
            "benchmark_contract": {
                "status": "pass",
                "task_files": {
                    "task_config": "task/task_config.yaml",
                    "required_prims": "task/required_prims.yaml",
                    "evaluator": "task/evaluator.yaml",
                },
            },
            "blocked_reasons": [],
            "waivers": [],
            "claims_allowed": ["EBench task readiness is achieved."],
            "claims_forbidden": ["Full visual material parity beyond recorded evidence."],
        },
    )
    blocked_manifest = _write_json(
        tmp_path / "blocked_manifest.json",
        {
            "schema_version": "asset_application_normalizer.v1",
            "asset_id": "RemoteUriBlocked",
            "task_id": "AAN09.RemoteUriBlocked",
            "overall_status": "blocked",
            "milestone": "AAN-07-benchmark-contract",
            "source": {"path": "/assets/remote_uri_block.usda", "source_format": "usd"},
            "target": {
                "target_runtime_profile": "isaac41",
                "target_benchmark_profile": "ebench-lift2",
            },
            "stage_gates": [
                {"stage": "usd_closure", "status": "blocked"},
                {"stage": "runtime_smoke", "status": "not_run"},
                {"stage": "benchmark_contract", "status": "not_run"},
            ],
            "blocked_reasons": [
                {
                    "blocker_id": "aan03_block_remote_uri",
                    "summary": "Remote URI is unauthorized.",
                }
            ],
            "waivers": [],
            "claims_allowed": ["AAN-03 inspected the source graph."],
            "claims_forbidden": ["EBench task readiness is achieved."],
        },
    )
    negative_summary = _write_json(
        tmp_path / "negative_summary.json",
        {
            "schema_version": "aan09.negative_gate_summary.v1",
            "status": "pass",
            "failure_modes": {
                "aan03_block_remote_uri": {"count": 1},
            },
            "waiver_count": 0,
        },
    )

    table = build_pm_evidence_table([ready_manifest, blocked_manifest], [negative_summary])

    assert table["schema_version"] == "aan09_5.pm_evidence_table.v1"
    assert table["summary"]["asset_count"] == 2
    assert table["summary"]["status_counts"] == {"blocked": 1, "ready": 1}
    assert table["summary"]["waiver_count"] == 0
    assert table["summary"]["failure_modes"] == {"aan03_block_remote_uri": 1}
    ready_row = next(row for row in table["rows"] if row["asset_id"] == "Beaker_01")
    assert ready_row["pm_status"] == "ready"
    assert ready_row["gate_summary"] == "usd_closure=pass, material_closure=pass, physics_static=pass, runtime_smoke=pass, benchmark_contract=pass"
    assert ready_row["evidence_summary"]["runtime"] == "pass"
    assert ready_row["evidence_summary"]["benchmark_contract"] == "pass"
    blocked_row = next(row for row in table["rows"] if row["asset_id"] == "RemoteUriBlocked")
    assert blocked_row["pm_status"] == "blocked"
    assert blocked_row["failure_mode"] == "aan03_block_remote_uri"
    assert blocked_row["claim_boundary"]["forbidden"][0] == "EBench task readiness is achieved."

    markdown = render_pm_evidence_markdown(table)
    assert "| Beaker_01 | ready |" in markdown
    assert "| RemoteUriBlocked | blocked |" in markdown
    assert "aan03_block_remote_uri" in markdown


def test_pm_evidence_table_marks_contract_only_manifest_runtime_pending(tmp_path: Path) -> None:
    contract_manifest = _write_json(
        tmp_path / "contract_manifest.json",
        {
            "schema_version": "asset_application_normalizer.v1",
            "asset_id": "DryingBox_01_overlay",
            "task_id": "AAN07.DryingBox",
            "overall_status": "pass",
            "milestone": "AAN-07-benchmark-contract",
            "source": {"path": "/assets/DryingBox_01.usd", "source_format": "usd"},
            "target": {
                "target_runtime_profile": "isaac41",
                "target_benchmark_profile": "ebench-lift2",
            },
            "stage_gates": [
                {"stage": "usd_closure", "status": "pass"},
                {"stage": "material_closure", "status": "pass"},
                {"stage": "physics_static", "status": "pass"},
                {"stage": "benchmark_contract", "status": "pass"},
            ],
            "runtime_evidence": {"status": "not_run"},
            "benchmark_contract": {"status": "pass"},
            "blocked_reasons": [],
            "waivers": [],
            "claims_allowed": ["EBench task contract is present."],
            "claims_forbidden": ["Isaac runtime smoke passed."],
        },
    )

    table = build_pm_evidence_table([contract_manifest])

    row = table["rows"][0]
    assert row["pm_status"] == "contract_ready_runtime_pending"
    assert table["summary"]["status_counts"] == {"contract_ready_runtime_pending": 1}
    markdown = render_pm_evidence_markdown(table)
    assert "| DryingBox_01_overlay | contract_ready_runtime_pending |" in markdown


def test_mjcf_scout_extracts_inventory_and_semantic_gaps(tmp_path: Path) -> None:
    source = tmp_path / "autobio_like_mjcf.xml"
    source.write_text(
        """<mujoco model="autobio_like">
  <asset>
    <mesh name="dish_mesh" file="meshes/dish.obj"/>
    <texture name="glass_texture" file="textures/glass.png" type="2d"/>
    <material name="glass" texture="glass_texture" rgba="0.8 0.9 1.0 0.35"/>
  </asset>
  <worldbody>
    <body name="sample" pos="0 0 0">
      <geom name="sample_geom" type="mesh" mesh="dish_mesh" material="glass"/>
      <joint name="slide" type="slide" axis="1 0 0" range="0 0.1"/>
      <site name="sensor_site"/>
      <body name="child" pos="0 0 0.02">
        <geom name="child_geom" type="sphere" size="0.01"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="slide_motor" joint="slide"/>
  </actuator>
  <sensor>
    <touch name="touch_sensor" site="sensor_site"/>
  </sensor>
  <contact>
    <pair geom1="sample_geom" geom2="child_geom"/>
  </contact>
  <equality>
    <weld name="lock" body1="sample" body2="child"/>
  </equality>
  <tendon>
    <spatial name="tendon"/>
  </tendon>
  <extension>
    <plugin plugin="custom.fluid"/>
  </extension>
</mujoco>
""",
        encoding="utf-8",
    )

    manifest = build_mjcf_scout_manifest(source)

    assert manifest["schema_version"] == "aan10.mjcf_scout.v1"
    assert manifest["overall_status"] == "semantic_gap_report_only"
    assert manifest["source"]["source_format"] == "mjcf"
    assert manifest["source"]["model"] == "autobio_like"
    assert manifest["inventory"]["counts"] == {
        "bodies": 2,
        "geoms": 2,
        "joints": 1,
        "sites": 1,
        "meshes": 1,
        "textures": 1,
        "materials": 1,
        "actuators": 1,
        "sensors": 1,
        "contacts": 1,
        "equality": 1,
        "tendons": 1,
        "plugins": 1,
    }
    assert manifest["inventory"]["bodies"][0]["path"] == "/sample"
    assert manifest["inventory"]["bodies"][1]["path"] == "/sample/child"
    gap_categories = {gap["category"] for gap in manifest["semantic_gaps"]}
    assert {"actuator", "sensor", "contact", "equality", "tendon", "plugin"} <= gap_categories
    assert "MJCF has been converted to USD." in manifest["claims_forbidden"]
    assert "AutoBio official reproduction is supported." in manifest["claims_forbidden"]
