"""Build M1 distillation_v06 via Unified Blender 4.4.3 -> OpenUSD SimReady Asset Forge (SKILL.md)."""

from __future__ import annotations

import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from convert_asset.blender_forge.runner import PILOT_SPECS, forge_asset_end_to_end  # noqa: E402
from convert_asset.distillation_v06.blender_distillation_v06_kit import run_blender_kit_generation  # noqa: E402
from convert_asset.distillation_v06.omniglass_usd_packager_v06 import package_v06_usd_assets  # noqa: E402


DEFAULT_OUT = _REPO_ROOT / "external_artifacts" / "distillation_v06_assets"


def main() -> int:
    # 1. Forge ART-001 Articulated Heating Bath + 4-Engine Deformable Amber Latex Hose Bundle/v0.2 via blender_forge
    forged_sub: dict[str, object] = {}
    for key in ("heating_bath", "latex_hose"):
        spec = PILOT_SPECS[key]
        res = forge_asset_end_to_end(spec, DEFAULT_OUT / "blender_forge_v06" / spec.asset_id)
        forged_sub[key] = {
            "asset_id": res["asset_id"],
            "overall_passed": res["hygiene_report"]["overall_passed"],
            "blender_version": res["hygiene_report"]["blender_version"],
            "contact_sheet": res["deliverables"]["studio_contact_sheet"],
            "deliverables": res["deliverables"],
        }

    # 2. Forge all 20 high-poly UV/separated-collision OmniGlass instruments + Full-Train Cycles AgX 4-View Sheet
    blender_dir = DEFAULT_OUT / "blender_meshes"
    run_blender_kit_generation(blender_dir, cycles_device="CPU")
    summary = package_v06_usd_assets(blender_dir, DEFAULT_OUT)

    print(
        json.dumps(
            {
                "blender_version": summary["blender_version"],
                "instrument_count": summary["instrument_count"],
                "omniglass_mdl_bundled": summary["omniglass_mdl_bundled"],
                "kit_studio_contact_sheet": summary["studio_contact_sheet"],
                "blender_forge_subbundles": forged_sub,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
