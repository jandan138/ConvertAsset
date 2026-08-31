from __future__ import annotations

from pathlib import Path

from pxr import Usd, UsdGeom

from scripts.build_ika_oven_125_relocatable import build_package
from scripts.qualify_ika_oven_125_relocatable import (
    MOUNTS,
    build_fixtures,
    evaluate_reports,
)


def test_direct_stage_fixture_preserves_the_fixed_package_root(
    tmp_path: Path,
) -> None:
    output = tmp_path / "oven"
    build_package(output)

    fixtures = build_fixtures(output / "package", output / "qualification")

    assert set(fixtures) == {"direct_stage"}
    for name, spec in MOUNTS.items():
        stage = Usd.Stage.Open(str(fixtures[name]))
        root = stage.GetPrimAtPath(spec["root"])
        assert root.IsValid()
        translation = UsdGeom.Xformable(root).GetLocalTransformation().ExtractTranslation()
        assert list(translation) == spec["translation"]
        graph = stage.GetPrimAtPath(
            spec["device_root"] + "/ControlPanel/Runtime/ControllerGraph"
        )
        assert graph.IsValid() and graph.IsActive()
        assert stage.GetPrimAtPath("/World/PhysicsScene").IsValid()
        assert not stage.GetRootLayer().GetExternalReferences()


def test_full_parity_requires_every_namespace_report_to_pass() -> None:
    passing = {
        name: {"status": "PASS", "passed": True, "runtime": "isaac41"}
        for name in MOUNTS
    }
    assert evaluate_reports(passing)["status"] == "pass"

    passing["direct_stage"] = {
        "status": "FAIL",
        "passed": False,
        "runtime": "isaac41",
    }
    result = evaluate_reports(passing)
    assert result["status"] == "blocked"
    assert result["blocked_namespaces"] == ["direct_stage"]
