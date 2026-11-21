#!/usr/bin/env python3
"""Isolated Newton 1.8.0 deformable parity worker (SolverVBD + newton_overlay.usda)."""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import sys
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
    build_voxel_tet_mesh,
    compute_tet_deformation_gradients,
    vertical_span_m,
)


def _lame_from_e_nu(e: float, nu: float) -> tuple[float, float]:
    nu_c = min(max(float(nu), 0.05), 0.48)
    mu = float(e) / (2.0 * (1.0 + nu_c))
    lam = float(e) * nu_c / ((1.0 + nu_c) * (1.0 - 2.0 * nu_c))
    return mu, lam


def _default_params(spec: DeformableSourceSpec) -> dict[str, Any]:
    if spec.structural_family == "soft_solid":
        return {
            "E_scale": 1.0,
            "nu": float(spec.poissons_ratio),
            "k_damp": 4.0,
            "vbd_iterations": 10,
            "substeps": 4,
        }
    return {
        "tri_ke": 8.0e3,
        "tri_ka": 8.0e3,
        "tri_kd": 1.0,
        "edge_ke": 2.5,
        "edge_kd": 0.15,
        "vbd_iterations": 10,
        "substeps": 4,
    }


def _rot_y_matrix(angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def _run_probe(
    newton: Any,
    wp: Any,
    spec: DeformableSourceSpec,
    params: dict[str, Any],
    probe_name: str,
    budget: DeformableIntegrityBudget | None,
) -> dict[str, Any]:
    sx, sy, sz = spec.dimensions_xyz_m
    dt_frame = 0.002
    substeps = int(params.get("substeps", 4))
    sub_dt = dt_frame / substeps
    is_solid = spec.structural_family == "soft_solid"

    mb = newton.ModelBuilder()
    mb.add_ground_plane()

    platen_body = -1
    if is_solid:
        z_bottom = 0.030 if probe_name == "drop" else (0.045 if probe_name in ("gentle_grasp", "crush_counterfactual") else 0.002)
        verts_local, tets_local, _ = build_voxel_tet_mesh((sx, sy, sz), grid_xyz=(4, 4, 2))
        e_eff = float(spec.youngs_modulus_pa) * float(params.get("E_scale", 1.0))
        mu, lam = _lame_from_e_nu(e_eff, float(params.get("nu", spec.poissons_ratio)))
        mb.add_soft_mesh(
            pos=wp.vec3(0.0, 0.0, z_bottom + 0.5 * sz),
            rot=wp.quat_identity(),
            scale=1.0,
            vel=wp.vec3(0.0, 0.0, 0.0),
            vertices=[wp.vec3(float(v[0]), float(v[1]), float(v[2])) for v in verts_local],
            indices=[int(i) for i in tets_local.reshape(-1)],
            density=float(spec.density_kg_m3),
            k_mu=mu,
            k_lambda=lam,
            k_damp=float(params["k_damp"]),
            particle_radius=0.002,
        )
        platen_z0 = z_bottom + sz + 0.016
    else:
        z_offset = 0.020 if probe_name == "drop" else (0.045 if probe_name in ("gentle_grasp", "crush_counterfactual") else 0.0015)
        flat_v, faces, edges_local = build_grid_cloth_mesh(sx, sy, grid_xy=(10, 10))
        arched_v = build_arched_cloth_points(flat_v, sx, arch_height_m=0.032)
        areal_density = float(spec.mass_kg) / max(sx * sy, 1e-6)
        mb.add_cloth_mesh(
            pos=wp.vec3(0.0, 0.0, z_offset),
            rot=wp.quat_identity(),
            scale=1.0,
            vel=wp.vec3(0.0, 0.0, 0.0),
            vertices=[wp.vec3(float(v[0]), float(v[1]), float(v[2])) for v in arched_v],
            indices=[int(i) for i in faces.reshape(-1)],
            density=areal_density,
            tri_ke=float(params["tri_ke"]),
            tri_ka=float(params["tri_ka"]),
            tri_kd=float(params["tri_kd"]),
            edge_ke=float(params["edge_ke"]),
            edge_kd=float(params["edge_kd"]),
            particle_radius=0.002,
        )
        platen_z0 = z_offset + 0.032 + 0.016

    if probe_name == "compression_release":
        platen_body = mb.add_body(
            xform=wp.transform(wp.vec3(0.0, 0.0, platen_z0), wp.quat_identity()),
            is_kinematic=True,
            label="platen",
        )
        mb.add_shape_box(body=platen_body, hx=0.14, hy=0.14, hz=0.01)

    mb.color()
    model = mb.finalize()

    state0 = model.state()
    state1 = model.state()

    rest_pts = state0.particle_q.numpy().astype(np.float64).copy()
    h0 = max(vertical_span_m(rest_pts), 1e-4)
    center0 = rest_pts.mean(axis=0)

    thresh = (0.24 * sx) if is_solid else (0.40 * sx)
    grip_idx = np.flatnonzero(np.abs(rest_pts[:, 0] - center0[0]) >= thresh)
    if len(grip_idx) == 0:
        order_x = np.argsort(rest_pts[:, 0])
        k = max(2, len(order_x) // 6)
        grip_idx = np.concatenate((order_x[:k], order_x[-k:]))

    if probe_name in ("gentle_grasp", "crush_counterfactual") and len(grip_idx) > 0:
        flags = model.particle_flags.numpy()
        flags[grip_idx] = 0
        model.particle_flags = wp.array(flags, dtype=model.particle_flags.dtype, device=model.device)

    solver = newton.solvers.SolverVBD(model, iterations=int(params.get("vbd_iterations", 10)))
    pipeline = newton.CollisionPipeline(model)
    contacts = pipeline.contacts() if callable(getattr(pipeline, "contacts", None)) else model.contacts()

    tets = model.tet_indices.numpy().astype(np.int64) if is_solid else None
    edges = edges_local.astype(np.int64) if not is_solid else None

    total_steps = 180 if probe_name == "drop" else (200 if probe_name == "compression_release" else 110)
    h_hist: list[float] = []
    pos_hist: list[np.ndarray] = []
    min_z_all = float(rest_pts[:, 2].min())
    contact_steps = 0

    body_q_host = state0.body_q.numpy().copy() if platen_body >= 0 else None

    for step_i in range(total_steps):
        grip_target: np.ndarray | None = None
        if probe_name == "compression_release" and platen_body >= 0 and body_q_host is not None:
            z_bottom_ref = 0.002 if is_solid else 0.0015
            frac_target = 0.79 if is_solid else 0.52
            z_target_bot = z_bottom_ref + frac_target * h0
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
            body_q_host[platen_body, :3] = (0.0, 0.0, z_bot + 0.01)
            body_q_host[platen_body, 3:] = (0.0, 0.0, 0.0, 1.0)
            state0.body_q.assign(body_q_host)
            state1.body_q.assign(body_q_host)
        elif probe_name == "gentle_grasp" and len(grip_idx) > 0:
            s_sq = min(1.0, (step_i + 1) / 40.0) if is_solid else 0.0
            s_rot = min(1.0, max(0.0, (step_i - 15) / 75.0)) if is_solid else min(1.0, (step_i + 1) / 80.0)
            theta = math.radians(35.0) * s_rot
            rot = _rot_y_matrix(theta)
            rel = rest_pts[grip_idx] - center0[None, :]
            if is_solid:
                rel[:, 0] *= 1.0 - 0.05 * s_sq
            else:
                rel[:, 0] *= 1.0 + 0.02 * s_rot
            tgt = rel @ rot.T + center0[None, :] + np.array([0.0, 0.0, (0.03 if is_solid else 0.04) * s_rot])
            grip_target = tgt.astype(np.float32)
            q_host = state0.particle_q.numpy().copy()
            qd_host = state0.particle_qd.numpy().copy()
            q_host[grip_idx] = grip_target
            qd_host[grip_idx] = 0.0
            state0.particle_q.assign(q_host)
            state0.particle_qd.assign(qd_host)
        elif probe_name == "crush_counterfactual" and len(grip_idx) > 0:
            s_sq = min(1.0, (step_i + 1) / 80.0)
            rel = rest_pts[grip_idx] - center0[None, :]
            if is_solid:
                rel[:, 0] *= 1.0 - 0.58 * s_sq
            else:
                rel[:, 0] *= 1.0 + 0.62 * s_sq
            tgt = rel + center0[None, :]
            grip_target = tgt.astype(np.float32)
            q_host = state0.particle_q.numpy().copy()
            qd_host = state0.particle_qd.numpy().copy()
            q_host[grip_idx] = grip_target
            qd_host[grip_idx] = 0.0
            state0.particle_q.assign(q_host)
            state0.particle_qd.assign(qd_host)

        for _ in range(substeps):
            state0.clear_forces()
            pipeline.collide(state0, contacts)
            solver.step(state0, state1, None, contacts, sub_dt)
            state0, state1 = state1, state0
            if platen_body >= 0 and body_q_host is not None:
                state0.body_q.assign(body_q_host)
            if grip_target is not None:
                q_host = state0.particle_q.numpy().copy()
                qd_host = state0.particle_qd.numpy().copy()
                q_host[grip_idx] = grip_target
                qd_host[grip_idx] = 0.0
                state0.particle_q.assign(q_host)
                state0.particle_qd.assign(qd_host)

        cur_pts = state0.particle_q.numpy().astype(np.float64)
        if not np.all(np.isfinite(cur_pts)):
            return {
                "probe_name": probe_name,
                "finite_fraction": 0.0,
                "contact_fraction": 0.0,
                "penetration_absent": False,
                "settling_ratio": 1.0,
                "steps_executed": step_i + 1,
                "dt_s": dt_frame,
            }

        h_c = vertical_span_m(cur_pts)
        h_hist.append(h_c)
        min_z = float(cur_pts[:, 2].min())
        min_z_all = min(min_z_all, min_z)
        if probe_name in ("drop", "compression_release"):
            if min_z <= 0.012:
                contact_steps += 1
        else:
            contact_steps += 1

        if step_i % 5 == 0 or step_i == total_steps - 1:
            pos_hist.append(cur_pts.copy())

    pos_stack = np.stack(pos_hist, axis=0)
    polar_s = None
    naive_s = None
    edge_s = None
    if is_solid and tets is not None:
        F_stack = compute_tet_deformation_gradients(rest_pts, pos_stack, tets)
        polar_s = polar_stretch_strain_from_F(F_stack)
        naive_s = naive_rfws_strain_from_F(F_stack)
        strain_val = polar_s
        e_eff = float(spec.youngs_modulus_pa) * float(params.get("E_scale", 1.0))
        peak_force_n = float(e_eff * (sx * sy) * max(polar_s, 0.01))
    else:
        assert edges is not None
        edge_s = edge_stretch_strain(rest_pts, pos_stack, edges)
        strain_val = edge_s
        peak_force_n = float(spec.youngs_modulus_pa * (sx * 0.004) * max(edge_s, 0.01))

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

    return {
        "probe_name": probe_name,
        "finite_fraction": 1.0,
        "contact_fraction": float(contact_steps / total_steps),
        "penetration_absent": bool(min_z_all >= -0.010),
        "settling_ratio": settling,
        "steps_executed": total_steps,
        "dt_s": dt_frame,
        "drop_deformation": deform if probe_name == "drop" else None,
        "compression_deformation": deform if probe_name == "compression_release" else None,
        "recovery_ratio": recov,
        "polar_stretch_strain": polar_s,
        "edge_stretch_strain": edge_s,
        "naive_f_minus_i": naive_s,
        "peak_normal_force_n": peak_force_n,
        "peak_shear_force_n": 0.15 * peak_force_n,
        "damage_score": damage_score,
        "intact": intact,
        "extra": {"h0": h0, "h_min": h_min, "h_final": h_final, "n_particles": int(len(rest_pts))},
    }


def _export_newton_usda(out_dir: Path, spec: DeformableSourceSpec, params: dict[str, Any]) -> None:
    from pxr import Sdf, Usd, UsdGeom, Vt

    out_dir.mkdir(parents=True, exist_ok=True)
    usda_path = out_dir / "newton_overlay.usda"
    stage = Usd.Stage.CreateNew(str(usda_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())

    sx, sy, sz = spec.dimensions_xyz_m
    if spec.structural_family == "soft_solid":
        from convert_asset.deformable_parity.rfws_intake import build_subdivided_box_mesh

        verts, faces = build_subdivided_box_mesh((sx, sy, sz), subdiv_xyz=(4, 4, 2))
    else:
        flat_v, faces, _ = build_grid_cloth_mesh(sx, sy, grid_xy=(10, 10))
        verts = build_arched_cloth_points(flat_v, sx, arch_height_m=0.032)

    mesh = UsdGeom.Mesh.Define(stage, "/World/DeformableAsset")
    mesh.CreatePointsAttr(Vt.Vec3fArray([(float(v[0]), float(v[1]), float(v[2])) for v in verts]))
    mesh.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(faces)))
    mesh.CreateFaceVertexIndicesAttr(Vt.IntArray([int(i) for f in faces for i in f]))

    prim = mesh.GetPrim()
    prim.CreateAttribute("newton:engineVersion", Sdf.ValueTypeNames.String).Set("newton-1.8.0")
    prim.CreateAttribute("newton:solver", Sdf.ValueTypeNames.String).Set("SolverVBD")
    for k, v in params.items():
        if isinstance(v, (int, float)):
            prim.CreateAttribute(f"newton:{k}", Sdf.ValueTypeNames.Double).Set(float(v))
    stage.GetRootLayer().Save()


def _evaluate(
    newton: Any,
    wp: Any,
    spec: DeformableSourceSpec,
    probe_list: list[str],
    params: dict[str, Any],
    budget: DeformableIntegrityBudget | None,
) -> dict[str, Any]:
    probes: dict[str, Any] = {}
    for pname in probe_list:
        probes[pname] = _run_probe(newton, wp, spec, params, pname, budget)
        time.sleep(0.05)
    return probes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--response", required=True)
    args = parser.parse_args()

    req = json.loads(Path(args.request).read_text(encoding="utf-8"))
    spec = DeformableSourceSpec.from_dict(req["source_spec"])
    probe_list = list(req.get("probe_list", ["drop", "compression_release", "gentle_grasp", "crush_counterfactual"]))
    budget = DeformableIntegrityBudget.from_dict(req["budget"]) if req.get("budget") else None

    import warp as wp
    import newton

    wp.init()
    solver_name = "SolverVBD_SoftTet" if spec.structural_family == "soft_solid" else "SolverVBD_Cloth"

    if req.get("candidates"):
        results = []
        for idx, cand in enumerate(req["candidates"]):
            params = {**_default_params(spec), **dict(cand.get("params", {}))}
            probes = _evaluate(newton, wp, spec, probe_list, params, budget)
            results.append({"candidate_id": str(cand.get("id", f"c{idx}")), "params": params, "probes": probes})
        payload = {"engine_id": "newton18", "solver": solver_name, "results": results}
    else:
        params = {**_default_params(spec), **dict(req.get("params") or {})}
        probes = _evaluate(newton, wp, spec, probe_list, params, budget)
        artifact_relpath = ""
        if req.get("artifact_out_dir"):
            out_dir = Path(req["artifact_out_dir"])
            _export_newton_usda(out_dir, spec, params)
            artifact_relpath = "engines/newton18/newton_overlay.usda"
        payload = {
            "engine_id": "newton18",
            "solver": solver_name,
            "params": params,
            "probes": probes,
            "artifact_relpath": artifact_relpath,
        }

    Path(args.response).write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

