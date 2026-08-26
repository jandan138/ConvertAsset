from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_labspin_x8_r6_visual_fitted_lid_collision import (
    BASE_PROXY,
    LID_PROXY,
    build_r6,
)
from scripts.promote_labspin_x8_r6_visual_fitted_lid_collision import promote


SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "labspin_x8_task11_r5_rest_pose_20260824/package"
)


def _cube_signature(stage, root: str) -> dict[str, tuple[object, ...]]:
    from pxr import UsdGeom, UsdPhysics

    result = {}
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        if not path.startswith(root + "/") or not prim.IsA(UsdGeom.Cube):
            continue
        ops = UsdGeom.Xformable(prim).GetOrderedXformOps()
        result[path.rsplit("/", 1)[-1]] = (
            tuple(ops[0].Get()),
            tuple(ops[-1].Get()),
            prim.HasAPI(UsdPhysics.CollisionAPI),
            UsdGeom.Imageable(prim).GetVisibilityAttr().Get(),
        )
    return result


@pytest.mark.skipif(not SOURCE.is_dir(), reason="LABSPIN r5 package unavailable")
def test_r6_replaces_only_lid_proxies_with_visual_fitted_compound(tmp_path: Path) -> None:
    from pxr import Usd, UsdGeom, UsdPhysics

    source_stage = Usd.Stage.Open(str(SOURCE / "asset.usd"))
    before_base = _cube_signature(source_stage, BASE_PROXY)

    output = tmp_path / "package"
    result = build_r6(SOURCE, output)
    stage = Usd.Stage.Open(str(output / "asset.usd"))

    assert _cube_signature(stage, BASE_PROXY) == before_base
    assert not stage.GetPrimAtPath(f"{LID_PROXY}/main_shell")
    assert not stage.GetPrimAtPath(f"{LID_PROXY}/front_shell")
    expected = {
        "top_panel",
        "front_perimeter",
        "rear_perimeter",
        "left_perimeter",
        "right_perimeter",
        "handle_grip",
        "handle_post_left",
        "handle_post_right",
        "latch_tongue",
    }
    assert set(_cube_signature(stage, LID_PROXY)) == expected
    for name in expected:
        prim = stage.GetPrimAtPath(f"{LID_PROXY}/{name}")
        assert prim.HasAPI(UsdPhysics.CollisionAPI)
        assert UsdGeom.Imageable(prim).GetVisibilityAttr().Get() == "invisible"

    audit = json.loads(result["collision_audit"].read_text())
    assert audit["overall_status"] == "pass"
    assert audit["base_proxy_unchanged"] is True
    assert audit["old_main_shell_rear_excess_m"] > 0.06
    assert audit["maximum_authored_inflation_m"] == pytest.approx(0.001)
    assert all(item["source_visual_prims"] for item in audit["lid_proxies"])


@pytest.mark.skipif(not SOURCE.is_dir(), reason="LABSPIN r5 package unavailable")
def test_r6_manifest_stays_candidate_until_runtime_requalification(tmp_path: Path) -> None:
    output = tmp_path / "package"
    build_r6(SOURCE, output)

    manifest = json.loads((output / "evidence/manifest.json").read_text())
    assert manifest["overall_status"] == "candidate"
    assert manifest["blocked_reasons"] == [
        "r6_visual_fitted_lid_collision_runtime_qualification_pending"
    ]
    assert manifest["claims"]["visual_fitted_lid_collision"] is False
    assert manifest["claims"]["robot_policy_success"] is False
    assert manifest["source"]["r6_collision_derivation"]["raw_files_unchanged"] is True


@pytest.mark.skipif(not SOURCE.is_dir(), reason="LABSPIN r5 package unavailable")
def test_r6_promotion_requires_hash_bound_runtime_evidence(tmp_path: Path) -> None:
    from hashlib import sha256

    output = tmp_path / "package"
    build_r6(SOURCE, output)
    asset_sha = sha256((output / "asset.usd").read_bytes()).hexdigest()
    rest = {
        "status": "pass",
        "asset_usd_sha256": asset_sha,
        "claims": {
            "static_rest_pose_assembled": True,
            "first_step_pose_continuity": True,
            "robot_policy_success": False,
            "task11_success": False,
        },
    }
    behavior = {
        "status": "pass",
        "claims": {
            "contact_press_qualified": True,
            "button_causes_lid_open": True,
            "lid_remains_open_after_release": True,
            "rotor_open_interlock": True,
            "shutdown_causes_power_off": True,
            "robot_policy_success": False,
            "task11_success": False,
        },
    }
    (output / "evidence/rest_pose").mkdir(exist_ok=True)
    (output / "evidence/lid_behavior").mkdir(exist_ok=True)
    (output / "evidence/rest_pose/report.json").write_text(json.dumps(rest))
    (output / "evidence/lid_behavior/report.json").write_text(json.dumps(behavior))
    (output / "evidence/collision_fit/render_report.json").write_text(
        json.dumps(
            {
                "asset_usd_sha256": asset_sha,
                "visual_review": "pass",
                "images": [{"state": "closed"}, {"state": "open"}],
            }
        )
    )
    static_path = output / "evidence/task11_static_manifest.json"
    static = json.loads(static_path.read_text())
    static["asset_usd_sha256"] = asset_sha
    static_path.write_text(json.dumps(static))

    receipt = promote(output)
    manifest = json.loads((output / "evidence/manifest.json").read_text())
    assert receipt.is_file()
    assert manifest["overall_status"] == "pass"
    assert manifest["claims"]["visual_fitted_lid_collision"] is True
    assert manifest["claims"]["robot_policy_success"] is False


def test_r6_overlay_renderer_covers_closed_and_open_states() -> None:
    source = (
        Path(__file__).parents[1]
        / "scripts/render_labspin_x8_r6_collision_overlay.py"
    ).read_text()
    compile(source, "render_labspin_x8_r6_collision_overlay.py", "exec")
    assert '("closed", 0.0)' in source
    assert '("open", -1.361356817)' in source
    assert "__aan_collision_proxy" in source
    assert "visual_review" in source
