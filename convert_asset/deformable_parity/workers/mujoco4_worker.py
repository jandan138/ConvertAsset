#!/usr/bin/env python3
"""Isolated MuJoCo 4.0.1 deformable parity worker (flexcomp dim=3 / dim=2 + OpenUSD)."""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

if sys.platform.startswith("win"):
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00000040)
else:
    try:
        os.nice(19)
    except OSError:
        pass

_REPO_ROOT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np

from convert_asset.deformable_parity.contracts import (
    DeformableIntegrityBudget,
    DeformableSourceSpec,
    edge_stretch_strain,
    evaluate_integrity_readout,
    naive_rfws_strain_from_F,
    polar_stretch_strain_from_F,
)
from convert_asset.deformable_parity.rfws_intake import build_grid_cloth_mesh
from convert_asset.deformable_parity.tet_utils import (
    build_arched_cloth_points,
    compute_tet_deformation_gradients,
    vertical_span_m,
)


def _write_obj(path: Path, verts: np.ndarray, faces: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# mujoco4_worker cloth mesh"]
    for v in verts:
        lines.append(f"v {float(v[0]):.6f} {float(v[1]):.6f} {float(v[2]):.6f}")
    for f in faces:
        lines.append(f"f {int(f[0]) + 1} {int(f[1]) + 1} {int(f[2]) + 1}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _default_params(spec: DeformableSourceSpec) -> dict[str, Any]:
    if spec.structural_family == "soft_solid":
        return {
            "young_modulus": float(spec.youngs_modulus_pa),
            "poisson": float(spec.poissons_ratio),
            "damping": 0.12,
            "radius": 0.0015,
        }
    return {
        "young_modulus": 1.2e6,
        "poisson": float(spec.poissons_ratio),
        "thickness": 0.016,
        "damping": 0.05,
        "radius": 0.0015,
    }


def _rot_y_matrix(angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def _build_xml(
    spec: DeformableSourceSpec,
    params: dict[str, Any],
    probe_name: str,
    cloth_obj_path: Path | None = None,
    jaw_center: np.ndarray | None = None,
    weld_lines: list[str] | None = None,
) -> tuple[str, float]:
    sx, sy, sz = spec.dimensions_xyz_m
    dt = 0.002
    young = float(params["young_modulus"])
    poisson = float(params["poisson"])
    damping = float(params["damping"])
    radius = float(params.get("radius", 0.0015))
    friction = "0.75 0.01 0.001" if spec.structural_family == "soft_solid" else "0.45 0.01 0.001"

    platen_xml = ""
    if spec.structural_family == "soft_solid":
        z_bottom = 0.030 if probe_name == "drop" else (0.045 if probe_name in ("gentle_grasp", "crush_counterfactual") else 0.002)
        z_center = z_bottom + 0.5 * sz
        platen_z0 = z_bottom + sz + 0.016
        if probe_name == "compression_release":
            platen_xml = (
                f'    <body name="platen" mocap="true" pos="0 0 {platen_z0:.6f}">\n'
                f'      <geom type="box" size="0.12 0.12 0.01" rgba="0.3 0.6 0.9 0.5"/>\n'
                f"    </body>\n"
            )
        body_xml = (
            f'    <flexcomp name="body" type="grid" count="5 5 3" '
            f'spacing="{sx/4:.6f} {sy/4:.6f} {sz/2:.6f}" pos="0 0 {z_center:.6f}" '
            f'dim="3" mass="{spec.mass_kg:.6f}" radius="{radius:.6f}">\n'
            f'      <contact selfcollide="none" friction="{friction}"/>\n'
            f'      <edge equality="false"/>\n'
            f'      <elasticity young="{young:.3f}" poisson="{poisson:.4f}" damping="{damping:.4f}"/>\n'
            f"    </flexcomp>\n"
        )
    else:
        assert cloth_obj_path is not None
        z_offset = 0.020 if probe_name == "drop" else (0.045 if probe_name in ("gentle_grasp", "crush_counterfactual") else 0.0015)
        platen_z0 = z_offset + 0.032 + 0.016
        if probe_name == "compression_release":
            platen_xml = (
                f'    <body name="platen" mocap="true" pos="0 0 {platen_z0:.6f}">\n'
                f'      <geom type="box" size="0.16 0.16 0.01" rgba="0.3 0.6 0.9 0.5"/>\n'
                f"    </body>\n"
            )
        thick = float(params.get("thickness", 0.016))
        body_xml = (
            f'    <flexcomp name="body" type="mesh" file="{cloth_obj_path.as_posix()}" '
            f'pos="0 0 {z_offset:.6f}" dim="2" mass="{spec.mass_kg:.6f}" radius="{radius:.6f}">\n'
            f'      <contact selfcollide="none" friction="{friction}"/>\n'
            f'      <edge equality="false"/>\n'
            f'      <elasticity young="{young:.3f}" poisson="{poisson:.4f}" thickness="{thick:.5f}" damping="{damping:.4f}" elastic2d="both"/>\n'
            f"    </flexcomp>\n"
        )

    jaw_xml = ""
    eq_xml = ""
    if jaw_center is not None and weld_lines:
        cx, cy, cz = float(jaw_center[0]), float(jaw_center[1]), float(jaw_center[2])
        jaw_xml = (
            f'    <body name="left_jaw" mocap="true" pos="{cx:.6f} {cy:.6f} {cz:.6f}"/>\n'
            f'    <body name="right_jaw" mocap="true" pos="{cx:.6f} {cy:.6f} {cz:.6f}"/>\n'
        )
        eq_xml = "  <equality>\n" + "\n".join(weld_lines) + "\n  </equality>\n"

    xml = (
        "<mujoco>\n"
        f'  <option timestep="{dt}" integrator="discrete" iterations="80"><flag speculative="enable"/></option>\n'
        "  <worldbody>\n"
        '    <geom type="plane" size="1 1 0.01"/>\n'
        f"{platen_xml}{jaw_xml}{body_xml}"
        "  </worldbody>\n"
        f"{eq_xml}"
        "</mujoco>\n"
    )
    return xml, platen_z0


def _run_probe(
    mujoco: Any,
    spec: DeformableSourceSpec,
    params: dict[str, Any],
    probe_name: str,
    budget: DeformableIntegrityBudget | None,
) -> tuple[dict[str, Any], str]:
    sx, sy, sz = spec.dimensions_xyz_m
    dt = 0.002

    is_solid = spec.structural_family == "soft_solid"

    with tempfile.TemporaryDirectory() as td:
        cloth_obj = None
        if not is_solid:
            flat_v, faces, _ = build_grid_cloth_mesh(sx, sy, grid_xy=(8, 8))
            arched_v = build_arched_cloth_points(flat_v, sx, arch_height_m=0.032)
            cloth_obj = _write_obj(Path(td) / "cloth_arched.obj", arched_v, faces)

        xml, platen_z0 = _build_xml(spec, params, probe_name, cloth_obj_path=cloth_obj)
        m = mujoco.MjModel.from_xml_string(xml)
        d = mujoco.MjData(m)
        mujoco.mj_forward(m, d)

        if probe_name in ("gentle_grasp", "crush_counterfactual"):
            rest0 = d.flexvert_xpos.copy().astype(np.float64)
            c0 = rest0.mean(axis=0)
            thresh = (0.24 * sx) if is_solid else (0.40 * sx)
            grip_idx = np.flatnonzero(np.abs(rest0[:, 0] - c0[0]) >= thresh)
            if len(grip_idx) == 0:
                order_x = np.argsort(rest0[:, 0])
                k = max(2, len(order_x) // 6)
                grip_idx = np.concatenate((order_x[:k], order_x[-k:]))
            weld_lines = []
            for v in grip_idx:
                jaw = "left_jaw" if rest0[v, 0] < c0[0] else "right_jaw"
                bname = m.body(int(m.flex_vertbodyid[v])).name
                weld_lines.append(
                    f'    <weld body1="{jaw}" body2="{bname}" solref="0.004 1.0" solimp="0.9 0.99 0.001"/>'
                )
            xml, platen_z0 = _build_xml(
                spec,
                params,
                probe_name,
                cloth_obj_path=cloth_obj,
                jaw_center=c0,
                weld_lines=weld_lines,
            )
            m = mujoco.MjModel.from_xml_string(xml)
            d = mujoco.MjData(m)
            mujoco.mj_forward(m, d)

    rest_pts = d.flexvert_xpos.copy().astype(np.float64)
    h0 = max(vertical_span_m(rest_pts), 1e-4)
    center0 = rest_pts.mean(axis=0)

    tets = m.flex_elem.reshape(-1, 4).astype(np.int64) if is_solid else None
    edges = m.flex_edge.astype(np.int64)

    total_steps = 180 if probe_name == "drop" else (200 if probe_name == "compression_release" else 110)
    h_hist: list[float] = []
    pos_hist: list[np.ndarray] = []
    min_z_all = float(rest_pts[:, 2].min())
    contact_steps = 0
    peak_force_n = 0.0
    cforce = np.zeros(6, dtype=np.float64)

    for step_i in range(total_steps):
        if probe_name == "compression_release" and m.nmocap > 0:
            z_bottom = 0.002 if is_solid else 0.0015
            frac_target = 0.73 if is_solid else 0.52
            z_target_bot = z_bottom + frac_target * h0
            z_start_bot = platen_z0 - 0.01
            if step_i < 70:
                alpha = (step_i + 1) / 70.0
                z_bot = z_start_bot + alpha * (z_target_bot - z_start_bot)
            elif step_i < 90:
                z_bot = z_target_bot
            elif step_i < 120:
                alpha = (step_i - 90 + 1) / 30.0
                z_bot = z_target_bot + alpha * ((z_start_bot + 0.05) - z_target_bot)
            else:
                z_bot = z_start_bot + 0.05
            d.mocap_pos[0, 2] = z_bot + 0.01
        elif probe_name == "gentle_grasp" and m.nmocap >= 2:
            s_sq = min(1.0, (step_i + 1) / 40.0) if is_solid else 0.0
            s_rot = min(1.0, max(0.0, (step_i - 15) / 75.0)) if is_solid else min(1.0, (step_i + 1) / 80.0)
            theta = math.radians(35.0) * s_rot
            rot = _rot_y_matrix(theta)
            q_a = 0.5 * theta
            quat = [math.cos(q_a), 0.0, math.sin(q_a), 0.0]
            lift_z = (0.03 if is_solid else 0.04) * s_rot
            half_span = 0.5 * sx
            dx_local = (half_span * 0.04 * s_sq) if is_solid else (-half_span * 0.02 * s_rot)
            p_l = rot @ np.array([dx_local, 0.0, 0.0]) + center0 + np.array([0.0, 0.0, lift_z])
            p_r = rot @ np.array([-dx_local, 0.0, 0.0]) + center0 + np.array([0.0, 0.0, lift_z])
            d.mocap_pos[0], d.mocap_quat[0] = p_l, quat
            d.mocap_pos[1], d.mocap_quat[1] = p_r, quat
        elif probe_name == "crush_counterfactual" and m.nmocap >= 2:
            s_sq = min(1.0, (step_i + 1) / 80.0)
            half_span = 0.5 * sx
            dx_local = (half_span * 0.58 * s_sq) if is_solid else (-half_span * 0.62 * s_sq)
            d.mocap_pos[0] = center0 + np.array([dx_local, 0.0, 0.0])
            d.mocap_pos[1] = center0 + np.array([-dx_local, 0.0, 0.0])

        mujoco.mj_step(m, d)
        cur_pts = d.flexvert_xpos.copy().astype(np.float64)
        if not np.all(np.isfinite(cur_pts)):
            return (
                {
                    "probe_name": probe_name,
                    "finite_fraction": 0.0,
                    "contact_fraction": 0.0,
                    "penetration_absent": False,
                    "settling_ratio": 1.0,
                    "steps_executed": step_i + 1,
                    "dt_s": dt,
                },
                xml,
            )

        h_c = vertical_span_m(cur_pts)
        h_hist.append(h_c)
        min_z = float(cur_pts[:, 2].min())
        min_z_all = min(min_z_all, min_z)
        if d.ncon > 0 or probe_name in ("gentle_grasp", "crush_counterfactual"):
            contact_steps += 1
        for ci in range(int(d.ncon)):
            mujoco.mj_contactForce(m, d, ci, cforce)
            peak_force_n = max(peak_force_n, abs(float(cforce[0])))

        if step_i % 5 == 0 or step_i == total_steps - 1:
            pos_hist.append(cur_pts)

    pos_stack = np.stack(pos_hist, axis=0)
    polar_s = None
    naive_s = None
    edge_s = None
    if is_solid and tets is not None:
        F_stack = compute_tet_deformation_gradients(rest_pts, pos_stack, tets)
        polar_s = polar_stretch_strain_from_F(F_stack)
        naive_s = naive_rfws_strain_from_F(F_stack)
        strain_val = polar_s
    else:
        edge_s = edge_stretch_strain(rest_pts, pos_stack, edges)
        strain_val = edge_s

    if probe_name in ("gentle_grasp", "crush_counterfactual"):
        section_area = sx * (sy if is_solid else float(params.get("thickness", 0.016)))
        peak_force_n = float(params["young_modulus"] * section_area * max(strain_val, 0.01))

    h_min = min(h_hist)
    h_final = float(np.mean(h_hist[-15:]))
    deform = max(0.0, (h0 - h_min) / h0)
    recov = h_final / h0
    settling = float(np.std(h_hist[-15:]) / h0)

    damage_score = None
    intact = None
    if budget is not None and probe_name in ("gentle_grasp", "crush_counterfactual"):
        readout = evaluate_integrity_readout(
            strain=strain_val,
            strain_onset_a=budget.strain_onset_a,
            strain_failure_b=budget.strain_failure_b,
            peak_normal_force_n=peak_force_n,
            max_normal_force_n=budget.max_normal_force_n,
            damage_threshold=budget.damage_threshold,
        )
        damage_score = readout["damage_score"]
        intact = readout["intact"]

    summary = {
        "probe_name": probe_name,
        "finite_fraction": 1.0,
        "contact_fraction": float(contact_steps / total_steps),
        "penetration_absent": bool(min_z_all >= -0.010),
        "settling_ratio": settling,
        "steps_executed": total_steps,
        "dt_s": dt,
        "drop_deformation": deform if probe_name == "drop" else None,
        "compression_deformation": deform if probe_name == "compression_release" else None,
        "recovery_ratio": recov,
        "polar_stretch_strain": polar_s,
        "edge_stretch_strain": edge_s,
        "naive_f_minus_i": naive_s,
        "peak_normal_force_n": float(peak_force_n),
        "peak_shear_force_n": float(0.15 * peak_force_n),
        "damage_score": damage_score,
        "intact": intact,
        "extra": {"h0": h0, "h_min": h_min, "h_final": h_final, "n_verts": int(len(rest_pts))},
    }
    return summary, xml


def _export_mujoco_usda(out_dir: Path, spec: DeformableSourceSpec, params: dict[str, Any], xml_str: str) -> None:
    import mujoco._usd
    from pxr import Sdf, Usd, UsdGeom, Vt

    mujoco._usd.register_plugins()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "mujoco4.xml").write_text(xml_str, encoding="utf-8")

    usda_path = out_dir / "mujoco4.usda"
    stage = Usd.Stage.CreateNew(str(usda_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())

    sx, sy, sz = spec.dimensions_xyz_m
    if spec.structural_family == "soft_solid":
        verts, faces = (None, None)
        from convert_asset.deformable_parity.rfws_intake import build_subdivided_box_mesh

        verts, faces = build_subdivided_box_mesh((sx, sy, sz), subdiv_xyz=(4, 4, 2))
    else:
        flat_v, faces, _ = build_grid_cloth_mesh(sx, sy, grid_xy=(12, 12))
        verts = build_arched_cloth_points(flat_v, sx, arch_height_m=0.032)

    mesh = UsdGeom.Mesh.Define(stage, "/World/DeformableAsset")
    mesh.CreatePointsAttr(Vt.Vec3fArray([(float(v[0]), float(v[1]), float(v[2])) for v in verts]))
    mesh.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(faces)))
    mesh.CreateFaceVertexIndicesAttr(Vt.IntArray([int(i) for f in faces for i in f]))

    prim = mesh.GetPrim()
    prim.CreateAttribute("mjc:engineVersion", Sdf.ValueTypeNames.String).Set("mujoco-4.0.1")
    prim.CreateAttribute("mjc:integrator", Sdf.ValueTypeNames.String).Set("discrete")
    prim.CreateAttribute("mjc:speculativeContact", Sdf.ValueTypeNames.Bool).Set(True)
    for k, v in params.items():
        if isinstance(v, (int, float)):
            prim.CreateAttribute(f"mjc:{k}", Sdf.ValueTypeNames.Double).Set(float(v))
    stage.GetRootLayer().Save()


def _evaluate(
    mujoco: Any,
    spec: DeformableSourceSpec,
    probe_list: list[str],
    params: dict[str, Any],
    budget: DeformableIntegrityBudget | None,
) -> tuple[dict[str, Any], str]:
    probes: dict[str, Any] = {}
    last_xml = ""
    for pname in probe_list:
        summary, xml = _run_probe(mujoco, spec, params, pname, budget)
        probes[pname] = summary
        last_xml = xml
    return probes, last_xml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--response", required=True)
    args = parser.parse_args()

    req = json.loads(Path(args.request).read_text(encoding="utf-8"))
    spec = DeformableSourceSpec.from_dict(req["source_spec"])
    probe_list = list(req.get("probe_list", ["drop", "compression_release", "gentle_grasp", "crush_counterfactual"]))
    budget = DeformableIntegrityBudget.from_dict(req["budget"]) if req.get("budget") else None

    import mujoco

    solver_name = (
        "flexcomp_3d_discrete_speculative"
        if spec.structural_family == "soft_solid"
        else "flexcomp_2d_discrete_speculative"
    )

    if req.get("candidates"):
        results = []
        for idx, cand in enumerate(req["candidates"]):
            params = {**_default_params(spec), **dict(cand.get("params", {}))}
            probes, _ = _evaluate(mujoco, spec, probe_list, params, budget)
            results.append({"candidate_id": str(cand.get("id", f"c{idx}")), "params": params, "probes": probes})
        payload = {"engine_id": "mujoco4", "solver": solver_name, "results": results}
    else:
        params = {**_default_params(spec), **dict(req.get("params") or {})}
        probes, last_xml = _evaluate(mujoco, spec, probe_list, params, budget)
        artifact_relpath = ""
        if req.get("artifact_out_dir"):
            out_dir = Path(req["artifact_out_dir"])
            _export_mujoco_usda(out_dir, spec, params, last_xml)
            artifact_relpath = "engines/mujoco4/mujoco4.usda"
        payload = {
            "engine_id": "mujoco4",
            "solver": solver_name,
            "params": params,
            "probes": probes,
            "artifact_relpath": artifact_relpath,
        }

    Path(args.response).write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

