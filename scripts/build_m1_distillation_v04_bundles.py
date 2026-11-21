"""Build and MuJoCo4-verify all M1 v0.4 deformable bundles & parametric borosilicate glassware CAD."""

from __future__ import annotations

import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from convert_asset.distillation_v04 import (  # noqa: E402
    build_all_glassware_cad_v04,
    build_all_v04_deformable_bundles,
)


BUNDLES_ROOT = _REPO_ROOT / "external_artifacts" / "distillation_v04_bundles"
CAD_ROOT = _REPO_ROOT / "external_artifacts" / "distillation_v04_cad"


def main() -> int:
    print("Building M1 v0.4 4 annular/sculpted deformable bundles + MuJoCo4 settle probes...")
    def_summaries = build_all_v04_deformable_bundles(BUNDLES_ROOT, tex_size=1024, run_mujoco_probe=True)
    for aid, man in def_summaries.items():
        print(
            aid,
            json.dumps(
                {
                    "family": man["source"]["structural_family"],
                    "tets": man["skinning"]["n_phys_tets"],
                    "min_det": man["skinning"]["min_tet_det"],
                    "skin_err": man["skinning"]["max_rest_skin_err_m"],
                    "mujoco4_probe": man["mujoco4_probe"],
                }
            ),
        )

    print("Building M1 v0.4 12 parametric borosilicate glassware OpenUSD CAD components...")
    cad_doc = build_all_glassware_cad_v04(CAD_ROOT)
    layout = cad_doc["layout"]
    print(
        "CAD layout:",
        json.dumps(
            {
                "component_count": len(cad_doc["components"]),
                "max_coaxial_error_mm": layout["max_coaxial_error_mm"],
                "lower_inlet_barb_z": layout["lower_inlet_barb_root_world"][2],
                "upper_outlet_barb_z": layout["upper_outlet_barb_root_world"][2],
            }
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

