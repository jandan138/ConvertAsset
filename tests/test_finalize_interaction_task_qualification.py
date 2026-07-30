from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.finalize_interaction_task_qualification import (
    InteractionTaskFinalizationError,
    finalize_interaction_task_qualification,
)


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_package(
    root: Path,
    *,
    entry_prim: str,
) -> tuple[Path, Path]:
    package = root / "package"
    package.mkdir(parents=True)
    (package / "asset.usd").write_text("#usda 1.0\n", encoding="utf-8")
    asset_sha256 = _digest(package / "asset.usd")
    manifest = {
        "schema_version": "asset_application_normalizer.v1",
        "overall_status": "pass",
        "entrypoints": {"asset_entry_prim": entry_prim},
        "interaction_contract": {
            "status": "pass",
            "asset_entry_prim": entry_prim,
            "runtime_identity": {
                "rigid_root_prim": entry_prim,
                "active_rigid_body_prims": [entry_prim],
                "exactly_one_active_rigid_body": True,
            },
            "closure": {
                "status": "pass",
                "artifacts": [
                    {"path": "asset.usd", "sha256": asset_sha256}
                ],
            },
            "named_frames": {
                "support": {
                    "prim_path": f"{entry_prim}/__aan_frame_support",
                    "parent_prim": entry_prim,
                    "translation_body_local_usd": [0.0, 0.0, 0.0],
                    "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                    "authoritative": True,
                }
            },
        },
    }
    serialized = json.dumps(manifest, indent=2) + "\n"
    manifest_path = root / "package.manifest.json"
    manifest_path.write_text(serialized, encoding="utf-8")
    embedded = package / "evidence" / "manifest.json"
    embedded.parent.mkdir(parents=True)
    embedded.write_text(serialized, encoding="utf-8")
    return package, manifest_path


def _write_fixture(
    root: Path,
) -> tuple[Path, Path, Path, Path, Path]:
    rack_package, rack_manifest = _write_package(
        root / "rack",
        entry_prim="/World/TubeRack",
    )
    tube_package, tube_manifest = _write_package(
        root / "tube",
        entry_prim="/World/TestTube",
    )
    report = {
        "schema_version": "aan.tube_rack_insertion_qualification.v2",
        "status": "pass",
        "inputs": {
            "rack": {
                "package_manifest_sha256": _digest(rack_manifest),
                "asset_usd_sha256": _digest(rack_package / "asset.usd"),
                "asset_entry_prim": "/World/TubeRack",
            },
            "tube": {
                "package_manifest_sha256": _digest(tube_manifest),
                "asset_usd_sha256": _digest(tube_package / "asset.usd"),
                "asset_entry_prim": "/World/TestTube",
            },
        },
        "protocol": {
            "tube_kinematic": False,
            "authored_translation_updates": 0,
        },
        "source_integrity": {
            "status": "pass",
            "rack_asset_usd_sha256_before": _digest(rack_package / "asset.usd"),
            "rack_asset_usd_sha256_after": _digest(rack_package / "asset.usd"),
            "tube_asset_usd_sha256_before": _digest(tube_package / "asset.usd"),
            "tube_asset_usd_sha256_after": _digest(tube_package / "asset.usd"),
        },
        "gates": {
            name: {"status": "pass"}
            for name in (
                "composition_identity",
                "dynamic_insertion",
                "side_clearance",
                "bottom_contact",
                "source_integrity",
            )
        },
    }
    report_path = root / "runtime-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return (
        rack_package,
        rack_manifest,
        tube_package,
        tube_manifest,
        report_path,
    )


def test_finalizer_copies_report_and_hash_binds_top_level_qualification(
    tmp_path: Path,
) -> None:
    (
        rack_package,
        rack_manifest,
        tube_package,
        tube_manifest,
        report_path,
    ) = _write_fixture(tmp_path)

    result = finalize_interaction_task_qualification(
        rack_package_root=rack_package,
        rack_manifest_path=rack_manifest,
        tube_package_root=tube_package,
        tube_manifest_path=tube_manifest,
        runtime_report_path=report_path,
    )

    package_report = (
        rack_package
        / "evidence"
        / "task_qualifications"
        / "tube_insertion"
        / "report.json"
    )
    promotion = package_report.with_name("promotion.json")
    manifest = json.loads(rack_manifest.read_text(encoding="utf-8"))
    binding = manifest["task_qualifications"][0]
    assert package_report.read_bytes() == report_path.read_bytes()
    assert binding["qualification_id"] == "tube_insertion"
    assert binding["report_sha256"] == _digest(package_report)
    assert binding["inputs"]["tube"]["package_manifest_sha256"] == _digest(
        tube_manifest
    )
    assert rack_manifest.read_bytes() == (
        rack_package / "evidence" / "manifest.json"
    ).read_bytes()
    assert promotion.is_file()
    assert result["final_manifest_sha256"] == _digest(rack_manifest)


@pytest.mark.parametrize(
    ("target", "value", "message"),
    [
        ("status", "blocked", "status"),
        ("rack_manifest", "0" * 64, "rack manifest"),
        ("tube_manifest", "0" * 64, "tube manifest"),
        ("rack_entry", "/World/Wrong", "rack entry"),
        ("tube_asset", "0" * 64, "tube asset"),
    ],
)
def test_finalizer_rejects_unbound_or_failing_report_without_mutating_package(
    tmp_path: Path,
    target: str,
    value: str,
    message: str,
) -> None:
    (
        rack_package,
        rack_manifest,
        tube_package,
        tube_manifest,
        report_path,
    ) = _write_fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if target == "status":
        report["status"] = value
    elif target == "rack_manifest":
        report["inputs"]["rack"]["package_manifest_sha256"] = value
    elif target == "tube_manifest":
        report["inputs"]["tube"]["package_manifest_sha256"] = value
    elif target == "rack_entry":
        report["inputs"]["rack"]["asset_entry_prim"] = value
    elif target == "tube_asset":
        report["inputs"]["tube"]["asset_usd_sha256"] = value
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    before = rack_manifest.read_bytes()

    with pytest.raises(InteractionTaskFinalizationError, match=message):
        finalize_interaction_task_qualification(
            rack_package_root=rack_package,
            rack_manifest_path=rack_manifest,
            tube_package_root=tube_package,
            tube_manifest_path=tube_manifest,
            runtime_report_path=report_path,
        )

    assert rack_manifest.read_bytes() == before
    assert not (
        rack_package / "evidence" / "task_qualifications"
    ).exists()


def test_finalizer_refuses_to_replace_an_existing_promotion(
    tmp_path: Path,
) -> None:
    (
        rack_package,
        rack_manifest,
        tube_package,
        tube_manifest,
        report_path,
    ) = _write_fixture(tmp_path)
    arguments = {
        "rack_package_root": rack_package,
        "rack_manifest_path": rack_manifest,
        "tube_package_root": tube_package,
        "tube_manifest_path": tube_manifest,
        "runtime_report_path": report_path,
    }
    finalize_interaction_task_qualification(**arguments)

    with pytest.raises(InteractionTaskFinalizationError, match="existing"):
        finalize_interaction_task_qualification(**arguments)
