#!/usr/bin/env python3
"""Run serialized M1 4-engine deformable parity compilation on both pilot assets."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.deformable_parity import (
    build_pilot_flexible_wiping_cloth_spec,
    build_pilot_fragile_chocopie_tofu_spec,
    compile_multi_engine_deformable_bundle,
)


def main() -> None:
    out_root = REPO_ROOT / "tmp" / "deformable_pilot_m1"
    out_root.mkdir(parents=True, exist_ok=True)

    builders = [
        build_pilot_fragile_chocopie_tofu_spec,
        build_pilot_flexible_wiping_cloth_spec,
    ]
    summary_all: dict[str, dict] = {}
    for builder in builders:
        t0 = time.time()
        # First write source spec in a temp dir so we know asset_id, or directly under asset dir
        probe_dir = out_root / "_staging"
        spec = builder(probe_dir)
        asset_dir = out_root / spec.asset_id
        spec = builder(asset_dir)
        manifest = compile_multi_engine_deformable_bundle(spec, asset_dir)
        elapsed = time.time() - t0
        summary_all[spec.asset_id] = {
            "elapsed_s": round(elapsed, 2),
            "all_parity_verified": all(e.parity_verified for e in manifest.engines.values()),
            "engines": {
                eid: {
                    "fit_loss_drop": round(e.fit_loss_drop, 4),
                    "verify_loss_compression": round(e.verify_loss_compression, 4),
                    "cal_passed": e.cal_passed,
                    "independent_passed": e.independent_passed,
                    "gentle_intact": e.gentle_grasp.intact if e.gentle_grasp else None,
                    "gentle_damage": round(e.gentle_grasp.damage_score, 4) if (e.gentle_grasp and e.gentle_grasp.damage_score is not None) else None,
                    "gentle_polar_strain": round(e.gentle_grasp.polar_stretch_strain, 4) if (e.gentle_grasp and e.gentle_grasp.polar_stretch_strain is not None) else None,
                    "gentle_naive_strain": round(e.gentle_grasp.naive_f_minus_i, 4) if (e.gentle_grasp and e.gentle_grasp.naive_f_minus_i is not None) else None,
                    "crush_intact": e.crush_counterfactual.intact if e.crush_counterfactual else None,
                    "crush_damage": round(e.crush_counterfactual.damage_score, 4) if (e.crush_counterfactual and e.crush_counterfactual.damage_score is not None) else None,
                    "parity_verified": e.parity_verified,
                }
                for eid, e in manifest.engines.items()
            },
        }
        print(f"=== {spec.asset_id} ({elapsed:.1f}s) ===", flush=True)
        print(json.dumps(summary_all[spec.asset_id], indent=2), flush=True)


if __name__ == "__main__":
    main()

