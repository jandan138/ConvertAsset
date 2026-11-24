"""Multi-engine v0.3 thin-shell compiler mapping Kirchhoff-Love shells to 4 OpenUSD simulators."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from convert_asset.deformable_parity.contracts import ALLOWED_ENGINES

from .bicubic_hermite_shell import build_hermite_shell_mesh
from .contracts_v08 import (
    BUNDLE_SCHEMA_VERSION_V03,
    EvidenceTierV08,
    HermiteShellSpec,
    ThinShellBundleManifestV03,
    ThinShellCalibrationRecord,
)
from .hermite_gs_binding import bind_gaussians_to_hermite_shell


_THIN_SHELL_ENGINE_PROFILES: dict[str, dict[str, Any]] = {
    "mujoco4": {"solver": "flexcomp_2d_shell", "mem_scale": 0.94, "bend_scale": 1.06, "rel": "mujoco4/mjc_shell_v03.usda"},
    "newton18": {"solver": "SolverVBD_Cloth", "mem_scale": 1.03, "bend_scale": 0.96, "rel": "newton18/newton_shell_v03.usda"},
    "genesis": {"solver": "PBD.Cloth", "mem_scale": 1.00, "bend_scale": 1.00, "rel": "genesis/genesis_shell_v03.json"},
    "isaac_physx": {"solver": "PhysX_SurfaceDeformable", "mem_scale": 1.07, "bend_scale": 0.92, "rel": "isaac/physx_shell_v03.usda"},
}


def calibrate_thin_shell_jacobian(spec: HermiteShellSpec) -> ThinShellCalibrationRecord:
    """Estimate decoupled 2x2 log-membrane / log-bending Jacobian A_shell via finite probes."""
    u0 = (math.log(max(spec.membrane_rigidity, 1e-6)), math.log(max(spec.bending_rigidity, 1e-9)))
    # Uniaxial stretch & cantilever bend responses scale smoothly with (k_mem, k_bend) with slight Poisson coupling
    def _probe_q(u: tuple[float, float]) -> np.ndarray:
        lm, lb = u
        # Effective log observables: membrane stretch compliance & cantilever curvature stiffness
        q_mem = lm + 0.04 * spec.poissons_ratio * (lb - u0[1])
        q_bend = lb + 0.02 * (lm - u0[0])
        return np.array([q_mem, q_bend], dtype=np.float64)

    q0 = _probe_q(u0)
    eps = 0.05
    a_mat = np.zeros((2, 2), dtype=np.float64)
    for col in range(2):
        up = list(u0)
        um = list(u0)
        up[col] += eps
        um[col] -= eps
        a_mat[:, col] = (_probe_q((up[0], up[1])) - _probe_q((um[0], um[1]))) / (2.0 * eps)

    cond = float(np.linalg.cond(a_mat))
    return ThinShellCalibrationRecord(
        control_names=("log_k_membrane", "log_k_bending"),
        u0=u0,
        q0_log_mem_bend=(float(q0[0]), float(q0[1])),
        jacobian_A_2x2=(
            (float(a_mat[0, 0]), float(a_mat[0, 1])),
            (float(a_mat[1, 0]), float(a_mat[1, 1])),
        ),
        condition_number=round(cond, 6),
        identified_contact_params={
            "clamp_stiffness_n_m": float(spec.clamp_stiffness_n_m),
            "coulomb_friction_mu": float(spec.coulomb_friction_mu),
            "capture_radius_m": float(spec.capture_radius_m),
        },
    )


def _write_shell_overlay(
    out_path: Path,
    engine_id: str,
    spec: HermiteShellSpec,
    eff: Mapping[str, Any],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix == ".json":
        out_path.write_text(
            json.dumps(
                {
                    "engine_id": engine_id,
                    "asset_id": spec.asset_id,
                    "structural_family": spec.structural_family,
                    "effective_params": dict(eff),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return

    usda = f'''#usda 1.0
(
    defaultPrim = "ThinShellOverlay"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "ThinShellOverlay"
{{
    custom string deformable:engineId = "{engine_id}"
    custom string deformable:assetId = "{spec.asset_id}"
    custom string deformable:structuralFamily = "{spec.structural_family}"
    custom double deformable:membraneRigidity = {float(eff["membrane_rigidity"]):.8f}
    custom double deformable:bendingRigidity = {float(eff["bending_rigidity"]):.10f}
    custom double deformable:thicknessM = {float(spec.thickness_m):.6f}
    custom double deformable:coulombFrictionMu = {float(spec.coulomb_friction_mu):.4f}
}}
'''
    out_path.write_text(usda, encoding="utf-8")


def compile_thin_shell_bundle_v03(
    spec: HermiteShellSpec,
    out_dir: str | Path,
    *,
    engines: Sequence[str] = ("mujoco4", "newton18", "genesis", "isaac_physx"),
    evidence_tier: str = EvidenceTierV08.FAST_CHECK_CPU_PREVIEW.value,
    base_rgb: tuple[float, float, float] = (0.24, 0.56, 0.78),
    pattern: str = "woven_grid",
) -> tuple[ThinShellBundleManifestV03, Path]:
    """Compile a multi_engine_deformable_bundle/v0.3 manifest, 4-engine overlays, & 3DGS binding."""
    b_dir = Path(out_dir)
    b_dir.mkdir(parents=True, exist_ok=True)

    mesh = build_hermite_shell_mesh(
        nx=spec.nx,
        ny=spec.ny,
        length_u_m=spec.length_u_m,
        length_v_m=spec.length_v_m,
        area_density_kg_m2=spec.area_density_kg_m2,
    )
    gs_rel = "hermite_gs_binding.npz"
    bind_gaussians_to_hermite_shell(
        mesh,
        out_npz_path=b_dir / gs_rel,
        base_rgb=base_rgb,
        pattern=pattern,
    )

    cal = calibrate_thin_shell_jacobian(spec)
    overlays: dict[str, dict[str, Any]] = {}
    for eng in engines:
        if eng not in ALLOWED_ENGINES:
            raise ValueError(f"Unsupported engine {eng!r}")
        prof = _THIN_SHELL_ENGINE_PROFILES[eng]
        eff = {
            "solver": prof["solver"],
            "membrane_rigidity": spec.membrane_rigidity / float(prof["mem_scale"]),
            "bending_rigidity": spec.bending_rigidity / float(prof["bend_scale"]),
            "coulomb_friction_mu": float(spec.coulomb_friction_mu),
            "thickness_m": float(spec.thickness_m),
            "artifact_relpath": prof["rel"],
        }
        _write_shell_overlay(b_dir / prof["rel"], eng, spec, eff)
        overlays[eng] = eff

    manifest = ThinShellBundleManifestV03(
        asset_id=spec.asset_id,
        hermite_spec=spec,
        calibration_record=cal,
        engine_overlays=overlays,
        gs_binding_relpath=gs_rel,
        evidence_tier=evidence_tier,
        schema_version=BUNDLE_SCHEMA_VERSION_V03,
    )
    manifest_path = b_dir / "bundle_v03_manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    return manifest, manifest_path
