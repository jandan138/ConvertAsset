"""CLI and Python runner for the unified Blender 4.4+ -> OpenUSD SimReady Asset Forge."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from .contracts import AssetForgeSpec, resolve_blender44_bin
from .simready_assembler import assemble_forged_asset


PILOT_SPECS: dict[str, AssetForgeSpec] = {
    "incubator": AssetForgeSpec(
        asset_id="precision_benchtop_incubator_01",
        family="articulated_cad",
        template="precision_benchtop_incubator",
        dimensions_xyz_m=(0.340, 0.280, 0.260),
        dimension_tolerance_m=0.001,
        mass_kg=6.8,
        cycles_device="CPU",
        cycles_samples=32,
        render_resolution=(640, 480),
    ),
    "croissant": AssetForgeSpec(
        asset_id="blender_croissant_artisan_01",
        family="deformable_sculpted",
        template="artisan_butter_croissant",
        dimensions_xyz_m=(0.125, 0.068, 0.048),
        dimension_tolerance_m=0.001,
        mass_kg=0.068,
        cycles_device="CPU",
        cycles_samples=32,
        render_resolution=(640, 480),
        deformable_params={
            "category": "flaky_croissant_pastry",
            "structural_family": "soft_solid",
            "youngs_modulus_pa": 14000.0,
            "poissons_ratio": 0.28,
            "fragility_tier": "high",
            "max_normal_force_n": 4.5,
            "max_shear_force_n": 1.8,
        },
    ),
    "heating_bath": AssetForgeSpec(
        asset_id="heating_stirrer_bath_v06",
        family="articulated_cad",
        template="magnetic_heating_water_bath",
        dimensions_xyz_m=(0.156, 0.176, 0.168),
        dimension_tolerance_m=0.001,
        mass_kg=1.85,
        cycles_device="CPU",
        cycles_samples=32,
        render_resolution=(640, 480),
    ),
    "latex_hose": AssetForgeSpec(
        asset_id="amber_latex_hose_v06",
        family="deformable_sculpted",
        template="amber_latex_cooling_hose",
        dimensions_xyz_m=(0.380, 0.130, 0.115),
        dimension_tolerance_m=0.001,
        mass_kg=0.072,
        cycles_device="CPU",
        cycles_samples=32,
        render_resolution=(640, 480),
        deformable_params={
            "category": "amber_latex_cooling_hose",
            "structural_family": "rod_cable",
            "youngs_modulus_pa": 1450000.0,
            "poissons_ratio": 0.48,
            "fragility_tier": "low",
            "max_normal_force_n": 45.0,
            "max_shear_force_n": 25.0,
        },
    ),
}


def forge_asset_end_to_end(
    spec: AssetForgeSpec,
    out_dir: str | Path,
    *,
    blender_bin: str | Path | None = None,
) -> dict[str, Any]:
    """Execute Blender 4.4+ headless build + Cycles AgX studio render + SimReady assembly."""
    runtime = resolve_blender44_bin(blender_bin)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    spec_path = out / "asset_forge_spec.json"
    spec_path.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")

    worker_script = Path(__file__).resolve().parent / "bpy_worker.py"
    cmd = [
        runtime.executable,
        "--background",
        "--factory-startup",
        "--python",
        str(worker_script),
        "--",
        "--spec",
        str(spec_path),
        "--out-dir",
        str(out),
    ]
    creationflags = 0
    if os.name == "nt":
        # Run at BELOW_NORMAL priority so local concurrent tasks (e.g., distillation_v04) stay unaffected
        creationflags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
        creationflags=creationflags,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Blender 4.4+ worker failed (rc={proc.returncode}):\n"
            f"STDOUT:\n{proc.stdout[-2000:]}\nSTDERR:\n{proc.stderr[-2000:]}"
        )

    receipt_path = out / "blender_worker_receipt.json"
    if not receipt_path.is_file():
        raise FileNotFoundError(f"Expected worker receipt at {receipt_path}")
    worker_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return assemble_forged_asset(spec, worker_receipt, out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Unified Blender 4.4+ -> OpenUSD SimReady Asset Forge.")
    parser.add_argument(
        "--pilot",
        choices=["incubator", "croissant", "heating_bath", "latex_hose", "distillation", "all"],
        default="all",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path(r"I:\cpfs\shared\simulation\zhuzihou\dev\ConvertAsset\external_artifacts\blender_forge_pilots_20261121"),
    )
    parser.add_argument("--blender-bin", type=Path, default=None)
    parser.add_argument("--cycles-device", choices=["CPU", "OPTIX", "CUDA"], default="CPU")
    args = parser.parse_args()

    if args.pilot == "all":
        keys = ["incubator", "croissant"]
    elif args.pilot == "distillation":
        keys = ["heating_bath", "latex_hose"]
    else:
        keys = [args.pilot]
    results: dict[str, Any] = {}
    for k in keys:
        base = PILOT_SPECS[k]
        spec = AssetForgeSpec(**{**base.__dict__, "cycles_device": args.cycles_device})
        res = forge_asset_end_to_end(spec, args.out_root / spec.asset_id, blender_bin=args.blender_bin)
        results[k] = {
            "asset_id": res["asset_id"],
            "overall_passed": res["hygiene_report"]["overall_passed"],
            "measured_dims": res["hygiene_report"]["measured_dimensions_xyz_m"],
            "max_dim_err_m": res["hygiene_report"]["max_dimension_error_m"],
            "non_manifold_edges": res["hygiene_report"]["non_manifold_edge_count"],
            "visual_tris": res["hygiene_report"]["total_visual_triangles"],
            "proxy_tris": res["hygiene_report"]["total_collision_or_proxy_triangles"],
            "contact_sheet": res["deliverables"]["studio_contact_sheet"],
            "deliverables": res["deliverables"],
        }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

