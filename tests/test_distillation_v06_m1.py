"""Unit tests for M1 distillation_v06 Blender 20-instrument kit, OmniGlass MDL shaders, and coaxial 24/29 CAD geometry."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

from pxr import Usd, UsdGeom

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from convert_asset.distillation_v06.apparatus_specs_v06 import (  # noqa: E402
    BILIBILI_SOP_STAGES_V06,
    V06_APPARATUS_LAYOUT,
    V06_INSTRUMENT_IDS,
)


ASSETS_DIR = _REPO_ROOT / "external_artifacts" / "distillation_v06_assets"


def test_v06_blender_omniglass_assets_and_frosted_tapers() -> None:
    manifest_p = ASSETS_DIR / "m1_v06_manifest.json"
    assert manifest_p.is_file(), "Run scripts/build_m1_distillation_v06_assets.py first"
    manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
    assert manifest["omniglass_mdl_bundled"] is True
    assert tuple(int(x) for x in str(manifest["blender_version"]).split(".")[:2]) >= (4, 4)
    assert Path(manifest["studio_contact_sheet"]).is_file()
    assert (ASSETS_DIR / "deps" / "mdl" / "OmniGlass.mdl").is_file()
    assert manifest["instrument_count"] == len(V06_INSTRUMENT_IDS) == 20

    # Verify blender-simready-asset-forge ART-001 Heating Bath + 4-Engine Deformable Hose bundle/v0.2
    bath_h = json.loads(
        (ASSETS_DIR / "blender_forge_v06" / "heating_stirrer_bath_v06" / "forge_manifest_and_critic_handoff.json").read_text(encoding="utf-8")
    )
    hose_h = json.loads(
        (ASSETS_DIR / "blender_forge_v06" / "amber_latex_hose_v06" / "forge_manifest_and_critic_handoff.json").read_text(encoding="utf-8")
    )
    assert bath_h["hygiene_report"]["overall_passed"] is True
    assert hose_h["hygiene_report"]["overall_passed"] is True
    assert len(hose_h["deliverables"]["deformable_bundle_v02_engines"]) == 4

    for aid in V06_INSTRUMENT_IDS:
        entry = manifest["instruments"][aid]
        usd_p = Path(entry["usd_path"])
        assert usd_p.is_file()
        assert entry["total_tris"] >= 100
        assert entry["uv_present"] is True
        assert entry["visual_collision_separated"] is True
        assert entry["total_col_tris"] <= entry["total_tris"]
        stage = Usd.Stage.Open(str(usd_p))
        assert stage is not None
        root = stage.GetDefaultPrim()
        assert root.IsValid()
        assert stage.GetPrimAtPath(f"/{aid}/Visuals").IsValid()
        assert stage.GetPrimAtPath(f"/{aid}/Collisions").IsValid()
        meshes = [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
        assert len(meshes) >= 2

    # Verify frosted 24/29 ground-glass joints exist as separate submeshes on core glassware
    for glass_id in ("round_bottom_flask_250ml", "distillation_head_75deg", "liebig_condenser_24_29", "vacuum_tail_adapter"):
        subs = manifest["instruments"][glass_id]["submeshes"]
        assert "clear_glass" in subs and "frosted_glass" in subs
        txt = Path(manifest["instruments"][glass_id]["usd_path"]).read_text(encoding="utf-8")
        assert "OmniGlass.mdl" in txt
        assert "frosting_roughness" in txt


def test_v06_coaxial_kinematic_chain_and_12_bilibili_stages() -> None:
    assert len(BILIBILI_SOP_STAGES_V06) == 12
    # Strictly monotonic Bilibili reference timestamps (02:27 -> 06:20)
    prev_end = 0.0
    for st in BILIBILI_SOP_STAGES_V06:
        assert float(st["bilibili_start_s"]) >= prev_end
        assert float(st["bilibili_end_s"]) > float(st["bilibili_start_s"])
        prev_end = float(st["bilibili_end_s"])

    # Verify sub-millimeter thermometer bulb-to-sidearm lip alignment ("平齐")
    z_lip = float(V06_APPARATUS_LAYOUT["sidearm_bottom_lip_z_world"])
    z_thm = float(V06_APPARATUS_LAYOUT["thermometer_assembled_z_world"])
    z_bulb_local = float(V06_APPARATUS_LAYOUT["thermometer_bulb_top_local_z"])
    assert abs((z_thm + z_bulb_local) - z_lip) < 1e-4

    # Verify Liebig condenser axis is pitched 15 deg DOWNWARD (-Z), never upward!
    ax = V06_APPARATUS_LAYOUT["condenser_axis_world"]
    assert ax[0] > 0.95 and ax[2] < -0.24
    assert math.isclose(math.hypot(ax[0], ax[2]), 1.0, abs_tol=1e-6)

    # Verify "下进上出": lower inlet barb Z < upper outlet barb Z
    assert V06_APPARATUS_LAYOUT["lower_inlet_barb_root_world"][2] < V06_APPARATUS_LAYOUT["upper_outlet_barb_root_world"][2] - 0.030
