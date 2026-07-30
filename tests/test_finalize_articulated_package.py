from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.finalize_articulated_package import (
    ArticulatedPackageFinalizationError,
    finalize_articulated_package,
)


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _write_fixture(
    root: Path,
    *,
    prequalification_manifest_sha256: str | None = None,
) -> tuple[Path, Path, Path, Path]:
    source = root / "source.usda"
    source.write_text("#usda 1.0\ndef Xform \"World\" {}\n", encoding="utf-8")
    source_sha = _digest(source)
    package_root = root / "package"
    asset = package_root / "asset.usd"
    asset.parent.mkdir(parents=True)
    asset.write_text("#usda 1.0\ndef Xform \"World\" {}\n", encoding="utf-8")
    asset_sha = _digest(asset)
    root_prim = "/World/Centrifuge"
    dof_mapping = [
        {
            "dof_index": 0,
            "joint_prim": f"{root_prim}/button_joint",
            "joint_type": "PhysicsPrismaticJoint",
            "axis": "Z",
        },
        {
            "dof_index": 1,
            "joint_prim": f"{root_prim}/rotor_joint",
            "joint_type": "PhysicsRevoluteJoint",
            "axis": "Y",
        },
        {
            "dof_index": 2,
            "joint_prim": f"{root_prim}/lid_joint",
            "joint_type": "PhysicsRevoluteJoint",
            "axis": "X",
        },
    ]
    reset_values = [
        {
            "joint_prim": item["joint_prim"],
            "joint_type": item["joint_type"],
            "reset_value": {"status": "pass", "value": 0.0},
        }
        for item in dof_mapping
    ]
    joints = [
        {
            "prim_path": item["joint_prim"],
            "joint_type": item["joint_type"],
            "axis": {"status": "pass", "value": item["axis"]},
            "limits": {
                "status": "pass",
                "lower": {
                    "status": "pass",
                    "value": -180.0 if item["joint_type"] == "PhysicsRevoluteJoint" else -0.05,
                },
                "upper": {"status": "pass", "value": 0.0},
            },
            "enabled": {"status": "pass", "value": True},
            "reset_value": {
                "status": "pass",
                "value": 0.0,
            },
        }
        for item in dof_mapping
    ]
    manifest: dict[str, object] = {
        "schema_version": "asset_application_normalizer.v1",
        "overall_status": "pass",
        "source": {"sha256": source_sha},
        "target": {"target_runtime_profile": "isaac41"},
        "entrypoints": {"asset_entry_prim": root_prim},
        "articulation_closure": {
            "status": "pass",
            "scope": {"mode": "asset_scope_prims", "asset_scope_prims": [root_prim]},
            "articulation_roots": [{"prim_path": root_prim}],
            "joints": joints,
            "dof_mapping": dof_mapping,
            "reset_values": reset_values,
            "summary": {
                "articulation_root_count": 1,
                "joint_count": len(joints),
                "controllable_dof_count": len(dof_mapping),
            },
        },
    }
    manifest_path = root / "package.manifest.json"
    embedded_manifest_path = package_root / "evidence" / "manifest.json"
    _write_json(manifest_path, manifest)
    _write_json(embedded_manifest_path, manifest)
    manifest_sha = _digest(manifest_path)

    profile = {
        "schema_version": "aan.articulated_device_profile.v1",
        "profile_id": "fixture.centrifuge",
        "revision": "r1",
        "source_sha256": source_sha,
        "asset_entry_prim": root_prim,
        "articulation_root_prim": root_prim,
        "runtime_units": {"revolute": "radian", "prismatic": "meter"},
        "semantic_joints": {
            "start_button": {
                "joint_prim": f"{root_prim}/button_joint",
                "part_prim": f"{root_prim}/button",
                "dof_index": 0,
                "runtime_reset_value": 0.0,
                "reset_state": "released",
                "states": {"released": [-0.0005, 0.0], "pressed": [-0.005, -0.004]},
            },
            "rotor": {
                "joint_prim": f"{root_prim}/rotor_joint",
                "part_prim": f"{root_prim}/rotor",
                "dof_index": 1,
                "runtime_reset_value": 0.0,
                "reset_state": "parked",
                "states": {"parked": [-0.05, 0.0]},
            },
            "lid": {
                "joint_prim": f"{root_prim}/lid_joint",
                "part_prim": f"{root_prim}/lid",
                "dof_index": 2,
                "runtime_reset_value": 0.0,
                "reset_state": "closed",
                "states": {"open": [-1.56, -1.45], "closed": [-0.087, 0.0]},
            },
        },
        "named_frames": {
            "tube_socket": {
                "parent_prim": root_prim,
                "translation_parent_local_m": [0.0, 0.0, 0.1],
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "authoritative": True,
            }
        },
        "required_runtime_task_gates": ["button_contact_cycle", "lid_contact_cycle"],
    }
    profile_path = root / "device_profile.json"
    _write_json(profile_path, profile)
    profile_sha = _digest(profile_path)

    report = {
        "schema_version": "aan.articulation_runtime_qualification.v1",
        "status": "pass",
        "runtime": {"runtime_profile": "isaac41"},
        "inputs": {
            "device_profile": {
                "schema_version": "aan.articulated_device_profile.v1",
                "profile_sha256": profile_sha,
                "source_sha256": source_sha,
            },
            "integrity": {
                "status": "pass",
                "centrifuge_manifest_sha256": (
                    prequalification_manifest_sha256 or manifest_sha
                ),
                "centrifuge_asset_usd_sha256_before": asset_sha,
                "centrifuge_asset_usd_sha256_after": asset_sha,
            },
            "qualified_package": {
                "asset_path": "asset.usd",
                "asset_entry_prim": root_prim,
                "runtime_profile": "isaac41",
                "prequalification_manifest_sha256": (
                    prequalification_manifest_sha256 or manifest_sha
                ),
                "asset_usd_sha256_before": asset_sha,
                "asset_usd_sha256_after": asset_sha,
            },
        },
        "drive_integrity": {"status": "pass"},
        "runtime_dof_mapping": [
            {
                "dof_index": 0,
                "dof_name": "PrismaticJoint",
                "joint_prim": f"{root_prim}/button_joint",
            },
            {
                "dof_index": 1,
                "dof_name": "RevoluteJoint",
                "joint_prim": f"{root_prim}/rotor_joint",
            },
            {
                "dof_index": 2,
                "dof_name": "RevoluteJoint",
                "joint_prim": f"{root_prim}/lid_joint",
            },
        ],
        "task_gates": {
            "button_contact_cycle": {"status": "pass"},
            "lid_contact_cycle": {"status": "pass"},
        },
    }
    report_path = root / "runtime_report.json"
    _write_json(report_path, report)
    return package_root, manifest_path, profile_path, report_path


def test_finalizer_promotes_a_hash_bound_articulated_package(tmp_path: Path) -> None:
    package_root, manifest_path, profile_path, report_path = _write_fixture(tmp_path)

    result = finalize_articulated_package(
        package_root=package_root,
        manifest_path=manifest_path,
        profile_path=profile_path,
        runtime_report_path=report_path,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    embedded = package_root / "evidence" / "manifest.json"
    contract = manifest["articulation_contract"]
    assert manifest_path.read_bytes() == embedded.read_bytes()
    assert contract["status"] == "pass"
    assert contract["profile"]["profile_sha256"] == _digest(
        package_root / "articulation" / "device_profile.json"
    )
    assert contract["runtime_qualification"]["report_sha256"] == _digest(
        package_root / "evidence" / "articulation_runtime_qualification" / "report.json"
    )
    assert result["status"] == "pass"


def test_finalizer_rejects_a_report_not_bound_to_the_input_manifest(
    tmp_path: Path,
) -> None:
    package_root, manifest_path, profile_path, report_path = _write_fixture(
        tmp_path,
        prequalification_manifest_sha256="0" * 64,
    )

    with pytest.raises(
        ArticulatedPackageFinalizationError,
        match="prequalification manifest SHA-256",
    ):
        finalize_articulated_package(
            package_root=package_root,
            manifest_path=manifest_path,
            profile_path=profile_path,
            runtime_report_path=report_path,
        )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        ("profile_sha256", "0" * 64, "device_profile.profile_sha256"),
        ("source_sha256", "0" * 64, "device_profile.source_sha256"),
    ],
)
def test_finalizer_rejects_a_report_bound_to_a_different_device_profile(
    tmp_path: Path,
    field_name: str,
    value: str,
    message: str,
) -> None:
    package_root, manifest_path, profile_path, report_path = _write_fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["inputs"]["device_profile"][field_name] = value
    _write_json(report_path, report)

    with pytest.raises(
        ArticulatedPackageFinalizationError,
        match=message,
    ):
        finalize_articulated_package(
            package_root=package_root,
            manifest_path=manifest_path,
            profile_path=profile_path,
            runtime_report_path=report_path,
        )


def test_finalizer_rejects_nonstandard_json_in_runtime_evidence(
    tmp_path: Path,
) -> None:
    package_root, manifest_path, profile_path, report_path = _write_fixture(tmp_path)
    report_path.write_text('{"status": Infinity}\n', encoding="utf-8")

    with pytest.raises(ArticulatedPackageFinalizationError, match="valid JSON"):
        finalize_articulated_package(
            package_root=package_root,
            manifest_path=manifest_path,
            profile_path=profile_path,
            runtime_report_path=report_path,
        )


def test_finalizer_rejects_a_closure_without_controllable_joint_records(
    tmp_path: Path,
) -> None:
    package_root, manifest_path, profile_path, report_path = _write_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["articulation_closure"]["joints"]
    _write_json(manifest_path, manifest)
    _write_json(package_root / "evidence" / "manifest.json", manifest)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["inputs"]["integrity"]["centrifuge_manifest_sha256"] = _digest(
        manifest_path
    )
    report["inputs"]["qualified_package"][
        "prequalification_manifest_sha256"
    ] = _digest(manifest_path)
    _write_json(report_path, report)

    with pytest.raises(ArticulatedPackageFinalizationError, match="closure.joints"):
        finalize_articulated_package(
            package_root=package_root,
            manifest_path=manifest_path,
            profile_path=profile_path,
            runtime_report_path=report_path,
        )


def test_finalizer_rejects_duplicate_static_dof_joint_paths(tmp_path: Path) -> None:
    package_root, manifest_path, profile_path, report_path = _write_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mapping = manifest["articulation_closure"]["dof_mapping"]
    mapping[2]["joint_prim"] = mapping[1]["joint_prim"]
    _write_json(manifest_path, manifest)
    _write_json(package_root / "evidence" / "manifest.json", manifest)

    with pytest.raises(ArticulatedPackageFinalizationError, match="joint_prim.*unique"):
        finalize_articulated_package(
            package_root=package_root,
            manifest_path=manifest_path,
            profile_path=profile_path,
            runtime_report_path=report_path,
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("dotted_semantic_name", "semantic joint names"),
        ("dotted_state_name", "names without"),
        ("dotted_frame_name", "named frame names"),
        ("state_outside_limits", "within static joint limits"),
        ("wrong_qualified_entry", "qualified package asset_entry_prim"),
    ],
)
def test_finalizer_rejects_consumer_incompatible_profile_or_report(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    package_root, manifest_path, profile_path, report_path = _write_fixture(tmp_path)
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if mutation == "dotted_semantic_name":
        profile["semantic_joints"]["lid.state"] = profile["semantic_joints"].pop(
            "lid"
        )
        _write_json(profile_path, profile)
    elif mutation == "dotted_state_name":
        states = profile["semantic_joints"]["lid"]["states"]
        states["open.state"] = states.pop("open")
        _write_json(profile_path, profile)
    elif mutation == "dotted_frame_name":
        profile["named_frames"]["tube.socket"] = profile["named_frames"].pop(
            "tube_socket"
        )
        _write_json(profile_path, profile)
    elif mutation == "state_outside_limits":
        profile["semantic_joints"]["lid"]["states"]["open"] = [-4.0, -3.0]
        _write_json(profile_path, profile)
    else:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["inputs"]["qualified_package"]["asset_entry_prim"] = "/World/Other"
        _write_json(report_path, report)

    with pytest.raises(ArticulatedPackageFinalizationError, match=message):
        finalize_articulated_package(
            package_root=package_root,
            manifest_path=manifest_path,
            profile_path=profile_path,
            runtime_report_path=report_path,
        )
