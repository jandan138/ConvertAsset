#!/usr/bin/env python3
"""Isolated Genesis 1.4.7 deformable parity worker (MPM.ElastoPlastic + PBD.Cloth)."""

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
    vertical_span_m,
)


def _write_obj(path: Path, verts: np.ndarray, faces: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# genesis_worker cloth mesh"]
    for v in verts:
        lines.append(f"v {float(v[0]):.6f} {float(v[1]):.6f} {float(v[2]):.6f}")
    for f in faces:
        lines.append(f"f {int(f[0]) + 1} {int(f[1]) + 1} {int(f[2]) + 1}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _default_params(spec: DeformableSourceSpec) -> dict[str, Any]:
    if spec.structural_family == "soft_solid":
        return {
            "E": float(spec.youngs_modulus_pa),
            "nu": float(spec.poissons_ratio),
            "rho": float(spec.density_kg_m3),
            "yield_lower": 0.16,
            "yield_higher": 0.25,
            "von_mises_yield_stress": float(spec.yield_stress_pa or 5000.0) * 1.6,
            "grid_density": 96,
            "substeps": 12,
        }
    return {
        "rho": 0.22,
        "static_friction": 0.45,
        "kinetic_friction": 0.35,
        "stretch_compliance": 1e-6,
        "bending_compliance": 2e-5,
        "stretch_relaxation": 0.4,
        "bending_relaxation": 0.3,
        "air_resistance": 0.015,
    }


def _rot_y_matrix(angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def _quat_y_wxyz(angle_rad: float) -> tuple[float, float, float, float]:
    return (math.cos(0.5 * angle_rad), 0.0, math.sin(0.5 * angle_rad), 0.0)


def _run_soft_solid_probe(
    gs: Any,
    qd_to_torch: Any,
    spec: DeformableSourceSpec,
    params: dict[str, Any],
    probe_name: str,
    budget: DeformableIntegrityBudget | None,
) -> dict[str, Any]:
    import torch

    sx, sy, sz = spec.dimensions_xyz_m
    dt = 0.002
    substeps = int(params.get("substeps", 8))
    grid_density = int(params.get("grid_density", 128))
    z_bottom = 0.030 if probe_name == "drop" else (0.045 if probe_name in ("gentle_grasp", "crush_counterfactual") else 0.002)

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=dt, substeps=substeps),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.22, -0.22, -0.08),
            upper_bound=(0.22, 0.22, 0.25),
            grid_density=grid_density,
        ),
        show_viewer=False,
    )
    scene.add_entity(gs.morphs.Plane())
    platen = None
    platen_z0 = z_bottom + sz + 0.015
    if probe_name == "compression_release":
        platen = scene.add_entity(
            material=gs.materials.Rigid(gravity_compensation=1.0, rho=1e5, coup_softness=0.002),
            morph=gs.morphs.Box(pos=(0.0, 0.0, platen_z0), size=(0.18, 0.18, 0.02), fixed=False),
        )

    left_jaw = None
    right_jaw = None
    jaw_offset_x = 0.42 * sx
    jaw_z0 = z_bottom + 0.5 * sz
    if probe_name in ("gentle_grasp", "crush_counterfactual"):
        left_jaw = scene.add_entity(
            morph=gs.morphs.Box(
                pos=(-jaw_offset_x, 0.0, jaw_z0),
                size=(0.008, 0.008, 0.008),
                fixed=True,
                collision=False,
                visualization=True,
            ),
        )
        right_jaw = scene.add_entity(
            morph=gs.morphs.Box(
                pos=(jaw_offset_x, 0.0, jaw_z0),
                size=(0.008, 0.008, 0.008),
                fixed=True,
                collision=False,
                visualization=True,
            ),
        )

    mpm_box = scene.add_entity(
        material=gs.materials.MPM.ElastoPlastic(
            E=float(params["E"]),
            nu=float(params["nu"]),
            rho=float(params["rho"]),
            yield_lower=float(params["yield_lower"]),
            yield_higher=float(params["yield_higher"]),
            use_von_mises=True,
            von_mises_yield_stress=float(params["von_mises_yield_stress"]),
        ),
        morph=gs.morphs.Box(pos=(0.0, 0.0, z_bottom + 0.5 * sz), size=(sx, sy, sz)),
    )
    scene.build()

    p_start = getattr(mpm_box, "particle_start", mpm_box._particle_start)
    p_count = getattr(mpm_box, "n_particles", mpm_box._n_particles)
    p_end = p_start + p_count

    def _read_pos() -> np.ndarray:
        t = mpm_box.get_particles_pos()
        if t.ndim == 3:
            t = t[0]
        return t.detach().cpu().numpy().astype(np.float64)

    def _read_F() -> np.ndarray:
        f_all = qd_to_torch(mpm_box._solver.mpm_state.particles.F, copy=True)
        return f_all[p_start:p_end, 0].detach().cpu().numpy().astype(np.float64)

    pos0 = _read_pos()
    h0 = max(vertical_span_m(pos0), 1e-4)
    center0 = pos0.mean(axis=0)

    if probe_name in ("gentle_grasp", "crush_counterfactual") and left_jaw is not None and right_jaw is not None:
        left_mask = pos0[:, 0] <= (center0[0] - 0.24 * sx)
        right_mask = pos0[:, 0] >= (center0[0] + 0.24 * sx)
        if not np.any(left_mask) or not np.any(right_mask):
            order_x = np.argsort(pos0[:, 0])
            k = max(1, len(order_x) // 5)
            left_mask = np.zeros(len(pos0), dtype=bool)
            right_mask = np.zeros(len(pos0), dtype=bool)
            left_mask[order_x[:k]] = True
            right_mask[order_x[-k:]] = True
        stiff = 25000.0
        mpm_box.set_particle_constraints(
            torch.as_tensor(left_mask, dtype=gs.tc_bool, device=gs.device),
            int(left_jaw.links[0].idx),
            stiffness=stiff,
        )
        mpm_box.set_particle_constraints(
            torch.as_tensor(right_mask, dtype=gs.tc_bool, device=gs.device),
            int(right_jaw.links[0].idx),
            stiffness=stiff,
        )

    h_hist: list[float] = []
    f_hist: list[np.ndarray] = []
    min_z_all = float(pos0[:, 2].min())
    contact_steps = 0
    total_steps = 180 if probe_name == "drop" else (200 if probe_name == "compression_release" else 110)

    for step_i in range(total_steps):
        if probe_name == "compression_release" and platen is not None:
            z_target_bot = float(pos0[:, 2].min()) + 0.85 * h0
            z_start_bot = platen_z0 - 0.01

            def _platen_z_bot(idx: int) -> float:
                if idx < 0:
                    return z_start_bot
                if idx < 70:
                    return z_start_bot + ((idx + 1) / 70.0) * (z_target_bot - z_start_bot)
                if idx < 90:
                    return z_target_bot
                if idx < 120:
                    return z_target_bot + ((idx - 90 + 1) / 30.0) * ((z_start_bot + 0.04) - z_target_bot)
                return z_start_bot + 0.04

            z_cur = _platen_z_bot(step_i - 1)
            z_nxt = _platen_z_bot(step_i)
            vz = (z_nxt - z_cur) / dt
            platen.set_pos((0.0, 0.0, z_cur + 0.01), zero_velocity=False)
            platen.set_dofs_velocity(np.array([0.0, 0.0, vz, 0.0, 0.0, 0.0], dtype=np.float32))
        elif probe_name == "gentle_grasp" and left_jaw is not None and right_jaw is not None:
            s_sq = min(1.0, (step_i + 1) / 40.0)
            s_rot = min(1.0, max(0.0, (step_i - 15) / 75.0))
            theta = math.radians(35.0) * s_rot
            rot = _rot_y_matrix(theta)
            lift = np.array([0.0, 0.0, jaw_z0 + 0.03 * s_rot], dtype=np.float64)
            dx = jaw_offset_x * (1.0 - 0.05 * s_sq)
            lp = rot @ np.array([-dx, 0.0, 0.0]) + lift
            rp = rot @ np.array([dx, 0.0, 0.0]) + lift
            q = _quat_y_wxyz(theta)
            left_jaw.set_pos(tuple(lp.tolist()))
            left_jaw.set_quat(q)
            right_jaw.set_pos(tuple(rp.tolist()))
            right_jaw.set_quat(q)
        elif probe_name == "crush_counterfactual" and left_jaw is not None and right_jaw is not None:
            s_sq = min(1.0, (step_i + 1) / 80.0)
            dx = jaw_offset_x * (1.0 - 0.58 * s_sq)
            left_jaw.set_pos((-dx, 0.0, jaw_z0))
            right_jaw.set_pos((dx, 0.0, jaw_z0))

        scene.step()
        pos_c = _read_pos()
        if not np.all(np.isfinite(pos_c)):
            return {
                "probe_name": probe_name,
                "finite_fraction": 0.0,
                "contact_fraction": 0.0,
                "penetration_absent": False,
                "settling_ratio": 1.0,
                "steps_executed": step_i + 1,
                "dt_s": dt,
            }
        h_c = vertical_span_m(pos_c)
        h_hist.append(h_c)
        min_z = float(pos_c[:, 2].min())
        min_z_all = min(min_z_all, min_z)
        if probe_name == "drop":
            if min_z <= 0.012:
                contact_steps += 1
        elif probe_name == "compression_release":
            if min_z <= 0.008:
                contact_steps += 1
        else:
            contact_steps += 1
        if step_i % 5 == 0 or step_i == total_steps - 1:
            f_hist.append(_read_F())

    f_stack = np.stack(f_hist, axis=0)
    polar_s = polar_stretch_strain_from_F(f_stack)
    naive_s = naive_rfws_strain_from_F(f_stack)
    h_min = min(h_hist)
    h_final = float(np.mean(h_hist[-15:]))
    deform = max(0.0, (h0 - h_min) / h0)
    recov = h_final / h0
    settling = float(np.std(h_hist[-15:]) / h0)

    area = sx * sy
    peak_force_n = float(params["E"] * area * max(polar_s, deform))

    damage_score = None
    intact = None
    if budget is not None and probe_name in ("gentle_grasp", "crush_counterfactual"):
        readout = evaluate_integrity_readout(
            strain=polar_s,
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
        "dt_s": dt,
        "drop_deformation": deform if probe_name == "drop" else None,
        "compression_deformation": deform if probe_name == "compression_release" else None,
        "recovery_ratio": recov,
        "polar_stretch_strain": polar_s,
        "edge_stretch_strain": None,
        "naive_f_minus_i": naive_s,
        "peak_normal_force_n": peak_force_n,
        "peak_shear_force_n": 0.15 * peak_force_n,
        "damage_score": damage_score,
        "intact": intact,
        "extra": {"h0": h0, "h_min": h_min, "h_final": h_final, "n_particles": int(p_count)},
    }


def _run_cloth_probe(
    gs: Any,
    spec: DeformableSourceSpec,
    params: dict[str, Any],
    probe_name: str,
    budget: DeformableIntegrityBudget | None,
) -> dict[str, Any]:
    import torch

    wx, wy, _ = spec.dimensions_xyz_m
    dt = 0.002
    flat_v, faces, _ = build_grid_cloth_mesh(wx, wy, grid_xy=(12, 12))
    arched_v = build_arched_cloth_points(flat_v, wx, arch_height_m=0.032)
    z_offset = 0.020 if probe_name == "drop" else (0.045 if probe_name in ("gentle_grasp", "crush_counterfactual") else 0.0015)

    with tempfile.TemporaryDirectory() as td:
        obj_path = _write_obj(Path(td) / "cloth_arched.obj", arched_v, faces)
        scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=dt, substeps=10),
            pbd_options=gs.options.PBDOptions(
                max_stretch_solver_iterations=6,
                max_bending_solver_iterations=4,
            ),
            show_viewer=False,
        )
        scene.add_entity(gs.morphs.Plane())
        h0_est = 0.032
        platen = None
        platen_z0 = z_offset + h0_est + 0.015
        if probe_name == "compression_release":
            platen = scene.add_entity(
                morph=gs.morphs.Box(pos=(0.0, 0.0, platen_z0), size=(0.24, 0.24, 0.02), fixed=True),
            )
        left_jaw = None
        right_jaw = None
        jaw_offset_x = 0.45 * wx
        if probe_name in ("gentle_grasp", "crush_counterfactual"):
            left_jaw = scene.add_entity(
                morph=gs.morphs.Box(
                    pos=(-jaw_offset_x, 0.0, z_offset),
                    size=(0.008, 0.008, 0.008),
                    fixed=True,
                    collision=False,
                    visualization=True,
                ),
            )
            right_jaw = scene.add_entity(
                morph=gs.morphs.Box(
                    pos=(jaw_offset_x, 0.0, z_offset),
                    size=(0.008, 0.008, 0.008),
                    fixed=True,
                    collision=False,
                    visualization=True,
                ),
            )
        cloth = scene.add_entity(
            material=gs.materials.PBD.Cloth(
                rho=float(params["rho"]),
                static_friction=float(params["static_friction"]),
                kinetic_friction=float(params["kinetic_friction"]),
                stretch_compliance=float(params["stretch_compliance"]),
                bending_compliance=float(params["bending_compliance"]),
                stretch_relaxation=float(params["stretch_relaxation"]),
                bending_relaxation=float(params["bending_relaxation"]),
                air_resistance=float(params["air_resistance"]),
            ),
            morph=gs.morphs.Mesh(file=str(obj_path), pos=(0.0, 0.0, z_offset)),
        )
        scene.build()

        def _read_cloth() -> np.ndarray:
            t = cloth.get_particles_pos()
            if t.ndim == 3:
                t = t[0]
            return t.detach().cpu().numpy().astype(np.float64)

        pos0 = _read_cloth()
        h0 = max(vertical_span_m(pos0), 1e-4)
        edges_raw = np.asarray(cloth.edges, dtype=np.int64)
        if edges_raw.ndim != 2 or edges_raw.shape[1] != 2:
            edges_raw = edges_raw.reshape(-1, 2)
        center0 = pos0.mean(axis=0)
        left_idx = np.flatnonzero(pos0[:, 0] <= (center0[0] - 0.40 * wx))
        right_idx = np.flatnonzero(pos0[:, 0] >= (center0[0] + 0.40 * wx))

        total_steps = 180 if probe_name == "drop" else (200 if probe_name == "compression_release" else 110)
        if probe_name in ("gentle_grasp", "crush_counterfactual") and left_jaw is not None and right_jaw is not None:
            if len(left_idx) > 0:
                cloth.fix_particles_to_link(
                    int(left_jaw.links[0].idx),
                    particles_idx_local=torch.as_tensor(left_idx, dtype=gs.tc_int, device=gs.device),
                )
            if len(right_idx) > 0:
                cloth.fix_particles_to_link(
                    int(right_jaw.links[0].idx),
                    particles_idx_local=torch.as_tensor(right_idx, dtype=gs.tc_int, device=gs.device),
                )

        h_hist: list[float] = []
        edge_hist: list[np.ndarray] = []
        min_z_all = float(pos0[:, 2].min())
        contact_steps = 0

        for step_i in range(total_steps):
            if probe_name == "compression_release" and platen is not None:
                z_target_bot = z_offset + 0.52 * h0
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
                platen.set_pos((0.0, 0.0, z_bot + 0.01))
            elif probe_name == "gentle_grasp" and left_jaw is not None and right_jaw is not None:
                s_rot = min(1.0, (step_i + 1) / 80.0)
                theta = math.radians(35.0) * s_rot
                rot = _rot_y_matrix(theta)
                lift = np.array([0.0, 0.0, z_offset + 0.04 * s_rot], dtype=np.float64)
                dx = jaw_offset_x * (1.0 + 0.02 * s_rot)
                lp = rot @ np.array([-dx, 0.0, 0.0]) + lift
                rp = rot @ np.array([dx, 0.0, 0.0]) + lift
                q = _quat_y_wxyz(theta)
                left_jaw.set_pos(tuple(lp.tolist()))
                left_jaw.set_quat(q)
                right_jaw.set_pos(tuple(rp.tolist()))
                right_jaw.set_quat(q)
            elif probe_name == "crush_counterfactual" and left_jaw is not None and right_jaw is not None:
                s_pull = min(1.0, (step_i + 1) / 80.0)
                dx = jaw_offset_x * (1.0 + 0.62 * s_pull)
                left_jaw.set_pos((-dx, 0.0, z_offset))
                right_jaw.set_pos((dx, 0.0, z_offset))

            scene.step()
            pos_c = _read_cloth()
            if not np.all(np.isfinite(pos_c)):
                return {
                    "probe_name": probe_name,
                    "finite_fraction": 0.0,
                    "contact_fraction": 0.0,
                    "penetration_absent": False,
                    "settling_ratio": 1.0,
                    "steps_executed": step_i + 1,
                    "dt_s": dt,
                }
            h_c = vertical_span_m(pos_c)
            h_hist.append(h_c)
            min_z = float(pos_c[:, 2].min())
            min_z_all = min(min_z_all, min_z)
            if probe_name in ("drop", "compression_release"):
                if min_z <= 0.008:
                    contact_steps += 1
            else:
                contact_steps += 1
            if step_i % 5 == 0 or step_i == total_steps - 1:
                edge_hist.append(pos_c)

        edge_s = edge_stretch_strain(pos0, np.stack(edge_hist, axis=0), edges_raw)
        h_min = min(h_hist)
        h_final = float(np.mean(h_hist[-15:]))
        deform = max(0.0, (h0 - h_min) / h0)
        recov = h_final / h0
        settling = float(np.std(h_hist[-15:]) / h0)
        peak_force_n = float(spec.youngs_modulus_pa * (wx * 0.004) * max(edge_s, 0.01))

        damage_score = None
        intact = None
        if budget is not None and probe_name in ("gentle_grasp", "crush_counterfactual"):
            readout = evaluate_integrity_readout(
                strain=edge_s,
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
            "dt_s": dt,
            "drop_deformation": deform if probe_name == "drop" else None,
            "compression_deformation": deform if probe_name == "compression_release" else None,
            "recovery_ratio": recov,
            "polar_stretch_strain": None,
            "edge_stretch_strain": edge_s,
            "naive_f_minus_i": None,
            "peak_normal_force_n": peak_force_n,
            "peak_shear_force_n": 0.20 * peak_force_n,
            "damage_score": damage_score,
            "intact": intact,
            "extra": {"h0": h0, "h_min": h_min, "h_final": h_final, "n_particles": int(len(pos0))},
        }


def _evaluate(
    gs: Any,
    qd_to_torch: Any,
    spec: DeformableSourceSpec,
    probe_list: list[str],
    params: dict[str, Any],
    budget: DeformableIntegrityBudget | None,
) -> dict[str, Any]:
    probes: dict[str, Any] = {}
    for pname in probe_list:
        if spec.structural_family == "soft_solid":
            probes[pname] = _run_soft_solid_probe(gs, qd_to_torch, spec, params, pname, budget)
        else:
            probes[pname] = _run_cloth_probe(gs, spec, params, pname, budget)
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

    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

    import torch
    import genesis as gs
    from genesis.utils.misc import qd_to_torch

    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(0.08)
    gs.init(backend=gs.cuda, logging_level="warning")

    solver_name = "MPM.ElastoPlastic" if spec.structural_family == "soft_solid" else "PBD.Cloth"

    if req.get("candidates"):
        results = []
        for idx, cand in enumerate(req["candidates"]):
            params = {**_default_params(spec), **dict(cand.get("params", {}))}
            probes = _evaluate(gs, qd_to_torch, spec, probe_list, params, budget)
            results.append({"candidate_id": str(cand.get("id", f"c{idx}")), "params": params, "probes": probes})
        payload = {"engine_id": "genesis", "solver": solver_name, "results": results}
    else:
        params = {**_default_params(spec), **dict(req.get("params") or {})}
        probes = _evaluate(gs, qd_to_torch, spec, probe_list, params, budget)
        artifact_relpath = ""
        if req.get("artifact_out_dir"):
            out_dir = Path(req["artifact_out_dir"])
            out_dir.mkdir(parents=True, exist_ok=True)
            cfg_path = out_dir / "genesis_config.json"
            cfg_path.write_text(
                json.dumps(
                    {"engine_id": "genesis", "solver": solver_name, "asset_id": spec.asset_id, "params": params},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            artifact_relpath = "engines/genesis/genesis_config.json"
        payload = {
            "engine_id": "genesis",
            "solver": solver_name,
            "params": params,
            "probes": probes,
            "artifact_relpath": artifact_relpath,
        }

    Path(args.response).write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
