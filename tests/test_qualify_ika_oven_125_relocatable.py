from __future__ import annotations

from pathlib import Path

from pxr import Usd, UsdGeom

from scripts.build_ika_oven_125_identity_root import build
from scripts.qualify_ika_oven_125_relocatable import (
    MOUNTS,
    build_fixtures,
    evaluate_reports,
)


def test_each_fixture_relocates_the_identity_root_without_baking_descendants(
    tmp_path: Path,
) -> None:
    output = tmp_path / "oven"
    build(output)

    fixtures = build_fixtures(output / "package", output / "qualification")

    assert set(fixtures) == set(MOUNTS)
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
        assert stage.GetRootLayer().GetExternalReferences()


def test_full_parity_requires_every_namespace_report_to_pass() -> None:
    passing = {
        name: {"status": "PASS", "passed": True, "runtime": "isaac41"}
        for name in MOUNTS
    }
    assert evaluate_reports(passing)["status"] == "pass"

    passing["vr_scene"] = {
        "status": "FAIL",
        "passed": False,
        "runtime": "isaac41",
    }
    result = evaluate_reports(passing)
    assert result["status"] == "blocked"
    assert result["full_function_blocked_namespaces"] == ["vr_scene"]
