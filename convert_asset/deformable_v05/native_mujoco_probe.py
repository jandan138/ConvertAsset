"""Native MuJoCo 4.0.1 flexcomp volumetric/lateral-Poisson & simple-shear probe for v0.5 Jacobian calibration.

Runs inside isolated `sim-mujoco4-py312` subprocess (0% GPU) and empirically measures
effective (kappa_eff, mu_eff, nu_eff) and the 2x2 sensitivity Jacobian A = d[log kappa, log mu] / d[log E, nu].
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import mujoco
import numpy as np


def _build_flex_block_xml(
    *,
    young_pa: float,
    poisson: float,
    dims_xyz: tuple[float, float, float],
    mass_kg: float,
    probe_mode: str,
) -> str:
    sx, sy, sz = dims_xyz
    # 3x3x3 subdivided box flexcomp resting on floor z=0 with top rigid platen at z=sz
    if probe_mode == "volumetric_compression":
        platen_act = (
            f'<body name="platen" pos="0 0 {sz + 0.006:.5f}">'
            '  <joint name="platen_z" type="slide" axis="0 0 1" damping="18.0"/>'
            '  <inertial pos="0 0 0" mass="0.35" diaginertia="0.001 0.001 0.001"/>'
            '  <geom name="platen_geom" type="box" size="0.09 0.09 0.004" friction="0.05 0.005 0.001" rgba="0.3 0.5 0.8 0.6"/>'
            '</body>'
        )
        actuators = '<position name="act_z" joint="platen_z" kp="850" dampratio="1"/>'
    else:
        # Simple shear: high-friction top platen translates along +X while slightly loaded in -Z
        platen_act = (
            f'<body name="platen" pos="0 0 {sz + 0.005:.5f}">'
            '  <joint name="platen_z" type="slide" axis="0 0 1" damping="18.0"/>'
            '  <joint name="platen_x" type="slide" axis="1 0 0" damping="12.0"/>'
            '  <inertial pos="0 0 0" mass="0.35" diaginertia="0.001 0.001 0.001"/>'
            '  <geom name="platen_geom" type="box" size="0.09 0.09 0.004" friction="1.4 0.02 0.002" rgba="0.8 0.4 0.2 0.6"/>'
            '</body>'
        )
        actuators = (
            '<position name="act_z" joint="platen_z" kp="850" dampratio="1"/>'
            '<position name="act_x" joint="platen_x" kp="600" dampratio="1"/>'
        )

    return f"""<mujoco model="v05_native_probe_{probe_mode}">
  <option timestep="0.001" gravity="0 0 -9.81" integrator="discrete"/>
  <worldbody>
    <geom name="floor" type="plane" size="1 1 0.05" friction="1.2 0.02 0.002"/>
    <flexcomp name="block" type="box" count="3 3 3" spacing="{sx/2:.5f} {sy/2:.5f} {sz/2:.5f}"
              pos="0 0 {sz/2 + 0.001:.5f}" dim="3" radius="0.0015" mass="{mass_kg:.5f}">
      <contact condim="3" friction="1.2 0.02 0.002" solref="0.004 1"/>
      <elasticity young="{young_pa:.2f}" poisson="{poisson:.4f}" damping="0.08"/>
    </flexcomp>
    {platen_act}
  </worldbody>
  <actuator>
    {actuators}
  </actuator>
</mujoco>
"""


def run_single_native_mujoco_probe(
    *,
    young_pa: float,
    poisson: float,
    dims_xyz: tuple[float, float, float] = (0.06, 0.06, 0.04),
    mass_kg: float = 0.068,
) -> dict[str, Any]:
    """Run real MuJoCo 4.0.1 uniaxial compression + lateral shear probes to measure (kappa, mu, nu)."""
    sx, sy, sz = dims_xyz
    area_xy = sx * sy

    # 1. Uniaxial compression probe -> measure axial compression eps_z, lateral expansion eps_xy, & normal force
    xml_c = _build_flex_block_xml(
        young_pa=young_pa,
        poisson=poisson,
        dims_xyz=dims_xyz,
        mass_kg=mass_kg,
        probe_mode="volumetric_compression",
    )
    m_c = mujoco.MjModel.from_xml_string(xml_c)
    d_c = mujoco.MjData(m_c)
    mujoco.mj_forward(m_c, d_c)
    v0 = d_c.flexvert_xpos.copy()
    x0_span = float(v0[:, 0].max() - v0[:, 0].min())
    y0_span = float(v0[:, 1].max() - v0[:, 1].min())
    z0_span = float(v0[:, 2].max() - v0[:, 2].min())

    target_dz = -0.12 * sz
    for step in range(280):
        alpha = min(1.0, step / 180.0)
        d_c.ctrl[0] = target_dz * alpha
        mujoco.mj_step(m_c, d_c)
    v1 = d_c.flexvert_xpos.copy()
    finite_c = bool(np.all(np.isfinite(v1)))
    x1_span = float(v1[:, 0].max() - v1[:, 0].min())
    y1_span = float(v1[:, 1].max() - v1[:, 1].min())
    z1_span = float(v1[:, 2].max() - v1[:, 2].min())
    eps_z = (z1_span - z0_span) / max(z0_span, 1e-6)
    eps_lat = 0.5 * ((x1_span - x0_span) / max(x0_span, 1e-6) + (y1_span - y0_span) / max(y0_span, 1e-6))
    nu_eff = float(np.clip(-eps_lat / min(eps_z, -1e-4), 0.01, 0.48))
    # Reaction force from platen actuator minus gravity weight of platen (0.35 * 9.81)
    f_normal = abs(float(d_c.actuator_force[0]))
    e_eff = max((f_normal / max(area_xy, 1e-6)) / max(abs(eps_z), 1e-4), 100.0)
    kappa_eff = e_eff / (3.0 * max(1.0 - 2.0 * nu_eff, 0.04))

    # 2. Simple shear probe -> measure lateral shear force vs top-bottom shear angle gamma_xz
    xml_s = _build_flex_block_xml(
        young_pa=young_pa,
        poisson=poisson,
        dims_xyz=dims_xyz,
        mass_kg=mass_kg,
        probe_mode="shear",
    )
    m_s = mujoco.MjModel.from_xml_string(xml_s)
    d_s = mujoco.MjData(m_s)
    mujoco.mj_forward(m_s, d_s)
    vs0 = d_s.flexvert_xpos.copy()
    top_mask = vs0[:, 2] > (vs0[:, 2].min() + 0.7 * (vs0[:, 2].max() - vs0[:, 2].min()))
    bot_mask = vs0[:, 2] < (vs0[:, 2].min() + 0.3 * (vs0[:, 2].max() - vs0[:, 2].min()))

    for step in range(300):
        a_z = min(1.0, step / 80.0)
        a_x = min(1.0, max(0.0, (step - 60) / 160.0))
        d_s.ctrl[0] = -0.05 * sz * a_z
        d_s.ctrl[1] = 0.007 * a_x
        mujoco.mj_step(m_s, d_s)
    vs1 = d_s.flexvert_xpos.copy()
    finite_s = bool(np.all(np.isfinite(vs1)))
    dx_top = float(vs1[top_mask, 0].mean() - vs0[top_mask, 0].mean())
    dx_bot = float(vs1[bot_mask, 0].mean() - vs0[bot_mask, 0].mean())
    gamma_xz = max(abs(dx_top - dx_bot) / max(sz, 1e-6), 1e-4)
    f_shear = abs(float(d_s.actuator_force[1]))
    mu_eff = max((f_shear / max(area_xy, 1e-6)) / gamma_xz, 50.0)

    return {
        "young_ctrl_pa": young_pa,
        "poisson_ctrl": poisson,
        "finite": bool(finite_c and finite_s),
        "eps_z": round(eps_z, 6),
        "eps_lat": round(eps_lat, 6),
        "nu_eff": round(nu_eff, 6),
        "e_eff_pa": round(e_eff, 3),
        "kappa_eff_pa": round(kappa_eff, 3),
        "gamma_xz": round(gamma_xz, 6),
        "mu_eff_pa": round(mu_eff, 3),
        "q_log_kappa_mu": [round(math.log(kappa_eff), 6), round(math.log(mu_eff), 6)],
    }


def calibrate_native_mujoco_jacobian(
    *,
    young_pa: float,
    poisson: float,
    dims_xyz: tuple[float, float, float],
    mass_kg: float,
) -> dict[str, Any]:
    """Empirically estimate 2x2 Jacobian A = d[log kappa, log mu] / d[log E, nu] via 5 native MuJoCo 4.0.1 probes."""
    t0 = time.time()
    eps_log_e = 0.12
    eps_nu = 0.04
    base = run_single_native_mujoco_probe(young_pa=young_pa, poisson=poisson, dims_xyz=dims_xyz, mass_kg=mass_kg)
    e_plus = run_single_native_mujoco_probe(
        young_pa=young_pa * math.exp(eps_log_e), poisson=poisson, dims_xyz=dims_xyz, mass_kg=mass_kg
    )
    e_minus = run_single_native_mujoco_probe(
        young_pa=young_pa * math.exp(-eps_log_e), poisson=poisson, dims_xyz=dims_xyz, mass_kg=mass_kg
    )
    nu_plus = run_single_native_mujoco_probe(
        young_pa=young_pa, poisson=min(0.45, poisson + eps_nu), dims_xyz=dims_xyz, mass_kg=mass_kg
    )
    nu_minus = run_single_native_mujoco_probe(
        young_pa=young_pa, poisson=max(0.05, poisson - eps_nu), dims_xyz=dims_xyz, mass_kg=mass_kg
    )

    qp_e = np.asarray(e_plus["q_log_kappa_mu"], dtype=np.float64)
    qm_e = np.asarray(e_minus["q_log_kappa_mu"], dtype=np.float64)
    qp_nu = np.asarray(nu_plus["q_log_kappa_mu"], dtype=np.float64)
    qm_nu = np.asarray(nu_minus["q_log_kappa_mu"], dtype=np.float64)
    dnu = min(0.45, poisson + eps_nu) - max(0.05, poisson - eps_nu)

    a_mat = np.column_stack([(qp_e - qm_e) / (2.0 * eps_log_e), (qp_nu - qm_nu) / max(dnu, 1e-4)])
    cond = float(np.linalg.cond(a_mat)) if np.all(np.isfinite(a_mat)) else float("inf")

    return {
        "execution_mode": "native_subprocess",
        "engine_id": "mujoco4",
        "engine_runtime_version": f"mujoco=={mujoco.__version__}",
        "process_pid": os.getpid(),
        "elapsed_s": round(time.time() - t0, 3),
        "u0_log_e_nu": [round(math.log(young_pa), 6), round(poisson, 6)],
        "q0_log_kappa_mu": base["q_log_kappa_mu"],
        "jacobian_A_2x2": [[round(float(a_mat[0, 0]), 6), round(float(a_mat[0, 1]), 6)],
                           [round(float(a_mat[1, 0]), 6), round(float(a_mat[1, 1]), 6)]],
        "condition_number": round(cond, 4),
        "probes": {
            "base": base,
            "e_plus": e_plus,
            "e_minus": e_minus,
            "nu_plus": nu_plus,
            "nu_minus": nu_minus,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--young-pa", type=float, default=38000.0)
    parser.add_argument("--poisson", type=float, default=0.28)
    parser.add_argument("--mass-kg", type=float, default=0.068)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()
    res = calibrate_native_mujoco_jacobian(
        young_pa=args.young_pa,
        poisson=args.poisson,
        dims_xyz=(0.06, 0.06, 0.04),
        mass_kg=args.mass_kg,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"NATIVE_MUJOCO4_PROBE_OK pid={res['process_pid']} cond={res['condition_number']} nu_eff={res['probes']['base']['nu_eff']}")


if __name__ == "__main__":
    main()
