from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from convert_asset.asset_application_normalizer.interaction_authoring import (
    finalize_interaction_contract,
)
from convert_asset.asset_application_normalizer.package_layout import TargetPackageLayout


def _static_contract(package_root: Path) -> dict:
    layout = TargetPackageLayout(package_root)
    layout.root.mkdir(parents=True, exist_ok=True)
    layout.interaction_profile_json.parent.mkdir(parents=True)
    layout.interaction_overlay_usd.parent.mkdir(parents=True)
    layout.physics_profile_json.parent.mkdir(parents=True)
    layout.root_usd.write_text("#usda 1.0\n", encoding="utf-8")
    layout.interaction_profile_json.write_text("{}\n", encoding="utf-8")
    layout.interaction_overlay_usd.write_text("#usda 1.0\n", encoding="utf-8")
    layout.physics_profile_json.write_text("{}\n", encoding="utf-8")
    layout.physics_overlay_usd.write_text("#usda 1.0\n", encoding="utf-8")
    return finalize_interaction_contract(
        layout,
        {
            "schema_version": "aan.interaction_contract.v1",
            "status": "pass",
            "asset_entry_prim": "/World/vessel",
            "runtime_identity": {
                "rigid_root_prim": "/World/vessel",
                "exactly_one_active_rigid_body": True,
                "active_rigid_body_prims": ["/World/vessel"],
            },
            "disabled_source_rigid_bodies": [],
            "collider_prims": [
                {
                    "prim_path": "/World/vessel/mesh",
                    "purpose": ["containment", "gripper", "support"],
                }
            ],
            "open_top": {
                "required": True,
                "axis_body_local": [0.0, 1.0, 0.0],
                "aperture_frame": "opening",
                "status": "declared",
                "evidence": {"status": "declared"},
            },
            "named_frames": {
                name: {"prim_path": f"/World/vessel/__aan_frame_{name}"}
                for name in ("opening", "grasp", "support")
            },
            "root_motion_gate": {
                "status": "not_run",
                "required": True,
                "min_translation_m": 0.05,
                "evidence": {"status": "not_run", "observations": []},
            },
            "stable_support_gate": {
                "status": "not_run",
                "required": True,
                "evidence": {"status": "not_run", "observations": []},
            },
            "gripper_collision_gate": {
                "status": "not_run",
                "required": True,
                "evidence": {"status": "not_run", "observations": []},
            },
        },
    )


def _bound_report(contract: dict, package_root: Path, probes: dict) -> dict:
    return {
        "schema_version": "aan.interaction_runtime_qualification_report.v1",
        "status": (
            "pass"
            if all(item["status"] == "pass" for item in probes.values())
            else "blocked"
        ),
        "binding": {
            "run_id": "runtime-canary-1",
            "root_usd_sha256": hashlib.sha256(
                (package_root / "asset.usd").read_bytes()
            ).hexdigest(),
            "runtime_tree_sha256": contract["closure"]["runtime_tree_sha256"],
            "prequalification_contract_payload_sha256": contract["closure"][
                "contract_payload_sha256"
            ],
        },
        "probes": probes,
    }


def test_runtime_closure_validation_ignores_evidence_but_rejects_runtime_tree_change(
    tmp_path: Path,
) -> None:
    from convert_asset.asset_application_normalizer.interaction_runtime_qualification import (
        validate_runtime_package_closure,
    )

    contract = _static_contract(tmp_path)
    evidence = tmp_path / "evidence" / "interaction_runtime_qualification"
    evidence.mkdir(parents=True)
    (evidence / "report.json").write_text("{}\n", encoding="utf-8")

    assert validate_runtime_package_closure(tmp_path, contract)["status"] == "pass"

    (tmp_path / "overlays" / "interaction.usda").write_text(
        "#usda 1.0\n# changed\n", encoding="utf-8"
    )
    closure = validate_runtime_package_closure(tmp_path, contract)
    assert closure["status"] == "blocked"
    assert "runtime tree digest" in "; ".join(closure["errors"])


def test_probe_evaluation_is_fail_closed_and_diagnostic() -> None:
    from convert_asset.asset_application_normalizer.interaction_runtime_qualification import (
        evaluate_probe_observations,
    )

    probes = evaluate_probe_observations(
        {
            "cooked_aperture": {
                "finite": True,
                "probe_radius_m": 0.003,
                "entry_center_clear": True,
                "bottom_hit": True,
                "bottom_depth_m": 0.16,
                "vessel_height_m": 0.20,
                "side_hits": {"positive": True, "negative": True},
            },
            "stable_support": {
                "finite": True,
                "support_height_error_m": 0.001,
                "tail_max_linear_speed_m_s": 0.01,
                "tail_max_angular_speed_rad_s": 0.05,
                "tilt_deg": 2.0,
                "lateral_drift_m": 0.002,
                "scene_to_rigid_position_error_m": 0.0001,
            },
            "root_motion_parity": {
                "finite": True,
                "translation_m": 0.061,
                "scene_to_rigid_position_error_m": 0.0002,
                "scene_to_rigid_orientation_error_deg": 0.02,
            },
            "bilateral_gripper_proxy_collision": {
                "finite": True,
                "probe_radius_m": 0.003,
                "positive_hit": True,
                "negative_hit": False,
                "positive_distance_m": 0.01,
                "negative_distance_m": None,
            },
        },
        root_motion_requirement={"min_translation_m": 0.05},
    )

    assert probes["cooked_aperture"]["status"] == "pass"
    assert probes["stable_support"]["status"] == "pass"
    assert probes["root_motion_parity"]["status"] == "pass"
    assert probes["bilateral_gripper_proxy_collision"]["status"] == "blocked"
    assert "negative" in "; ".join(
        probes["bilateral_gripper_proxy_collision"]["errors"]
    )


def test_report_promotes_only_the_corresponding_runtime_gate(tmp_path: Path) -> None:
    from convert_asset.asset_application_normalizer.interaction_runtime_qualification import (
        promote_interaction_runtime_gates,
    )

    contract = _static_contract(tmp_path)
    probes = {
        "cooked_aperture": {"status": "blocked", "errors": ["virtual cap hit"]},
        "stable_support": {"status": "pass", "errors": []},
        "root_motion_parity": {"status": "pass", "errors": []},
        "bilateral_gripper_proxy_collision": {
            "status": "blocked",
            "errors": ["negative side did not hit"],
        },
    }
    report = _bound_report(contract, tmp_path, probes)
    promoted = promote_interaction_runtime_gates(
        contract,
        report,
        report_path="evidence/interaction_runtime_qualification/report.json",
        report_sha256="a" * 64,
    )

    assert promoted["open_top"]["status"] == "blocked"
    assert promoted["stable_support_gate"]["status"] == "pass"
    assert promoted["root_motion_gate"]["status"] == "pass"
    assert promoted["gripper_collision_gate"]["status"] == "blocked"
    assert "runtime_qualification" not in promoted
    assert "claim_boundary" not in promoted["gripper_collision_gate"]
    assert promoted["closure"]["artifacts"] == contract["closure"]["artifacts"]
    assert (
        promoted["closure"]["runtime_tree_sha256"]
        == contract["closure"]["runtime_tree_sha256"]
    )
    assert (
        promoted["closure"]["contract_payload_sha256"]
        != contract["closure"]["contract_payload_sha256"]
    )


def test_report_binding_mismatch_cannot_promote_any_gate(tmp_path: Path) -> None:
    from convert_asset.asset_application_normalizer.interaction_runtime_qualification import (
        promote_interaction_runtime_gates,
    )

    contract = _static_contract(tmp_path)
    probes = {
        name: {"status": "pass", "errors": []}
        for name in (
            "cooked_aperture",
            "stable_support",
            "root_motion_parity",
            "bilateral_gripper_proxy_collision",
        )
    }
    report = _bound_report(contract, tmp_path, probes)
    report["binding"]["runtime_tree_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="runtime_tree_sha256"):
        promote_interaction_runtime_gates(
            contract,
            report,
            report_path="evidence/interaction_runtime_qualification/report.json",
            report_sha256="a" * 64,
        )


def test_host_adapter_runs_bound_worker_and_updates_sidecar_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from convert_asset.asset_application_normalizer import (
        interaction_runtime_qualification as qualification,
    )

    package_root = tmp_path / "package"
    contract = _static_contract(package_root)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "interaction_contract": contract,
                "claims_forbidden": [
                    "The declared open-top collider has passed a runtime aperture probe.",
                    "The interaction rigid root has passed the required runtime motion probe.",
                    "Stable support and gripper collision have passed runtime probes.",
                    "A bilateral proxy collision probe proves a robot grasp.",
                ],
            }
        ),
        encoding="utf-8",
    )
    runtime_python = tmp_path / "isaac-python"
    runtime_python.write_text("#!/bin/sh\n", encoding="utf-8")

    def fake_run(argv, **_kwargs):
        report_path = Path(argv[argv.index("--report-out") + 1])
        request_path = Path(argv[argv.index("--request") + 1])
        request = json.loads(request_path.read_text(encoding="utf-8"))
        observations = {
            "cooked_aperture": {
                "finite": True,
                "probe_radius_m": 0.003,
                "entry_center_clear": True,
                "bottom_hit": True,
                "bottom_depth_m": 0.16,
                "vessel_height_m": 0.20,
                "side_hits": {"positive": True, "negative": True},
            },
            "stable_support": {
                "finite": True,
                "support_height_error_m": 0.001,
                "tail_max_linear_speed_m_s": 0.01,
                "tail_max_angular_speed_rad_s": 0.05,
                "tilt_deg": 2.0,
                "lateral_drift_m": 0.002,
                "scene_to_rigid_position_error_m": 0.0001,
            },
            "root_motion_parity": {
                "finite": True,
                "translation_m": 0.061,
                "scene_to_rigid_position_error_m": 0.0002,
                "scene_to_rigid_orientation_error_deg": 0.02,
            },
            "bilateral_gripper_proxy_collision": {
                "finite": True,
                "probe_radius_m": 0.003,
                "positive_hit": True,
                "negative_hit": True,
                "positive_distance_m": 0.01,
                "negative_distance_m": 0.01,
            },
        }
        probes = qualification.evaluate_probe_observations(
            observations,
            root_motion_requirement={"min_translation_m": 0.05},
        )
        report_path.write_text(
            json.dumps(
                {
                    "schema_version": qualification.REPORT_SCHEMA_VERSION,
                    "status": "pass",
                    "binding": request["binding"],
                    "probes": probes,
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(argv, 0, stdout="worker ok\n", stderr="")

    monkeypatch.setattr(qualification.subprocess, "run", fake_run)
    result = qualification.run_interaction_runtime_qualification(
        package_root,
        manifest_path,
        runtime_python=runtime_python,
        expected_runtime_version="4.1",
    )

    assert result.overall_status == "pass"
    assert result.interaction_contract["open_top"]["status"] == "pass"
    assert result.interaction_contract["root_motion_gate"]["status"] == "pass"
    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert updated["interaction_contract"]["stable_support_gate"]["status"] == "pass"
    assert "runtime_qualification" not in updated["interaction_contract"]
    assert updated["claims_forbidden"] == [
        "A bilateral proxy collision probe proves a robot grasp."
    ]
    assert (
        manifest_path.read_bytes()
        == (package_root / "evidence" / "manifest.json").read_bytes()
    )
    assert qualification.validate_runtime_package_closure(
        package_root,
        updated["interaction_contract"],
    )["status"] == "pass"
