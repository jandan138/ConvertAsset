#!/usr/bin/env python3
"""Isolated Isaac Sim 6.0.1 zero-RTX in-memory PhysX deformable parity worker."""

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

os.environ.setdefault("ISAACSIM_PORTABLE_ROOT", r"I:\isaacsim-data\6.0.1")

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


def _default_params(spec: DeformableSourceSpec) -> dict[str, Any]:
    if spec.structural_family == "soft_solid":
        return {
            "youngs_modulus": float(spec.youngs_modulus_pa),
            "poissons_ratio": float(spec.poissons_ratio),
            "elasticity_damping": 0.08,
            "dynamic_friction": 0.60,
        }
    return {
        "youngs_modulus": 1.8e5,
        "poissons_ratio": float(spec.poissons_ratio),
        "surface_thickness": 0.008,
        "surface_stretch_stiffness": 2.0e3,
        "surface_shear_stiffness": 8.0e2,
        "surface_bend_stiffness": 4.0e2,
        "elasticity_damping": 0.05,
    }


def _rot_y_matrix(angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def _apply_small_collision_offsets(prim: Any, rest_offset: float = 0.001, contact_offset: float = 0.004) -> None:
    from pxr import PhysxSchema

    if not prim or not prim.IsValid():
        return
    col_api = PhysxSchema.PhysxCollisionAPI.Apply(prim)
    col_api.CreateRestOffsetAttr().Set(float(rest_offset))
    col_api.CreateContactOffsetAttr().Set(float(contact_offset))


def _create_kinematic_box(
    stage: Any,
    prim_path: str,
    size_xyz: tuple[float, float, float],
    pos_xyz: tuple[float, float, float],
    with_collision: bool = True,
) -> tuple[Any, tuple[Any, Any]]:
    from pxr import Gf, UsdGeom, UsdPhysics

    cube = UsdGeom.Cube.Define(stage, prim_path)
    cube.CreateSizeAttr(1.0)
    scale_vec = Gf.Vec3d(*size_xyz)
    xform_op = cube.AddTransformOp()
    mat = Gf.Transform(Gf.Vec3d(*pos_xyz), Gf.Rotation(Gf.Quatd(1.0)), scale_vec).GetMatrix()
    xform_op.Set(mat)
    if with_collision:
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        _apply_small_collision_offsets(cube.GetPrim())
    rb = UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
    rb.CreateKinematicEnabledAttr().Set(True)
    return cube.GetPrim(), (xform_op, scale_vec)


def _create_jaw_anchor(
    stage: Any,
    prim_path: str,
    center_xyz: np.ndarray,
) -> tuple[Any, Any]:
    from pxr import Gf, UsdGeom

    xf = UsdGeom.Xform.Define(stage, prim_path)
    xform_op = xf.AddTransformOp()
    mat = Gf.Transform(
        Gf.Vec3d(float(center_xyz[0]), float(center_xyz[1]), float(center_xyz[2])),
        Gf.Rotation(Gf.Quatd(1.0)),
        Gf.Vec3d(1.0),
    ).GetMatrix()
    xform_op.Set(mat)
    return xf.GetPrim(), xform_op


def _author_vtx_xform_attachment(
    stage: Any,
    att_path: str,
    deformable_path: str,
    jaw_path: str,
    vtx_indices: np.ndarray,
    local_positions: np.ndarray,
) -> None:
    from pxr import Gf, Sdf, Vt

    att_prim = stage.DefinePrim(att_path, "OmniPhysicsVtxXformAttachment")
    att_prim.CreateAttribute("omniphysics:attachmentEnabled", Sdf.ValueTypeNames.Bool).Set(True)
    att_prim.CreateRelationship("omniphysics:src0").SetTargets([Sdf.Path(deformable_path)])
    att_prim.CreateRelationship("omniphysics:src1").SetTargets([Sdf.Path(jaw_path)])
    att_prim.CreateAttribute("omniphysics:vtxIndicesSrc0", Sdf.ValueTypeNames.IntArray).Set(
        Vt.IntArray([int(i) for i in vtx_indices])
    )
    att_prim.CreateAttribute("omniphysics:localPositionsSrc1", Sdf.ValueTypeNames.Point3fArray).Set(
        Vt.Vec3fArray([Gf.Vec3f(float(p[0]), float(p[1]), float(p[2])) for p in local_positions])
    )


def _build_stage_for_probe(
    physx_utils: Any,
    deformableUtils: Any,
    physicsUtils: Any,
    spec: DeformableSourceSpec,
    params: dict[str, Any],
    probe_name: str,
) -> tuple[Any, Any, np.ndarray, np.ndarray, np.ndarray, Any, Any, Any, float]:
    from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics, Vt

    stage = physx_utils.new_memory_stage(attach_stage=False)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    default_prim = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(default_prim.GetPrim())

    scene = UsdPhysics.Scene.Define(stage, "/World/physicsScene")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(9.81)
    ps_api = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    ps_api.CreateEnableGPUDynamicsAttr().Set(True)
    ps_api.CreateBroadphaseTypeAttr().Set("GPU")
    ps_api.GetMaxPositionIterationCountAttr().Set(16)

    plane_path = physicsUtils.add_ground_plane(stage, "/World/GroundPlane", "Z", 2.0, Gf.Vec3f(0.0), Gf.Vec3f(0.5))
    _apply_small_collision_offsets(stage.GetPrimAtPath(str(plane_path) + "/CollisionPlane"))

    sx, sy, sz = spec.dimensions_xyz_m
    is_solid = spec.structural_family == "soft_solid"

    platen_op = None
    left_op = None
    right_op = None
    platen_z0 = 0.06
    center0 = np.zeros(3, dtype=np.float64)

    if is_solid:
        z_bottom = 0.030 if probe_name == "drop" else (0.045 if probe_name in ("gentle_grasp", "crush_counterfactual") else 0.002)
        verts_local, tets_local, _ = build_voxel_tet_mesh((sx, sy, sz), grid_xyz=(4, 4, 2))
        rest_pts = verts_local.copy()
        rest_pts[:, 2] += z_bottom + 0.5 * sz

        tet_prim = UsdGeom.TetMesh.Define(stage, "/World/DeformableAsset")
        tet_prim.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(float(p[0]), float(p[1]), float(p[2])) for p in rest_pts]))
        tet_prim.CreateTetVertexIndicesAttr(
            Vt.Vec4iArray([Gf.Vec4i(int(t[0]), int(t[1]), int(t[2]), int(t[3])) for t in tets_local])
        )
        deformableUtils.set_physics_volume_deformable_body(stage, Sdf.Path("/World/DeformableAsset"))
        _apply_small_collision_offsets(tet_prim.GetPrim())

        mat_path = "/World/Materials/DeformableMat"
        deformableUtils.add_deformable_material(
            stage,
            mat_path,
            density=float(spec.density_kg_m3),
            static_friction=0.75,
            dynamic_friction=float(params.get("dynamic_friction", 0.60)),
            youngs_modulus=float(params["youngs_modulus"]),
            poissons_ratio=float(params["poissons_ratio"]),
        )
        mat_prim = stage.GetPrimAtPath(mat_path)
        mat_prim.ApplyAPI("PhysxDeformableMaterialAPI")
        mat_prim.GetAttribute("physxDeformableMaterial:elasticityDamping").Set(float(params["elasticity_damping"]))
        physicsUtils.add_physics_material_to_prim(stage, tet_prim.GetPrim(), mat_path)
        body_prim = tet_prim
        topo = tets_local.astype(np.int64)
        platen_z0 = z_bottom + sz + 0.016
    else:
        z_offset = 0.020 if probe_name == "drop" else (0.045 if probe_name in ("gentle_grasp", "crush_counterfactual") else 0.0015)
        flat_v, faces_local, edges_local = build_grid_cloth_mesh(sx, sy, grid_xy=(10, 10))
        arched_v = build_arched_cloth_points(flat_v, sx, arch_height_m=0.032)
        rest_pts = arched_v.copy()
        rest_pts[:, 2] += z_offset

        cloth_prim = UsdGeom.Mesh.Define(stage, "/World/DeformableAsset")
        cloth_prim.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(float(p[0]), float(p[1]), float(p[2])) for p in rest_pts]))
        cloth_prim.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(faces_local)))
        cloth_prim.CreateFaceVertexIndicesAttr(Vt.IntArray([int(i) for f in faces_local for i in f]))
        deformableUtils.set_physics_surface_deformable_body(stage, Sdf.Path("/World/DeformableAsset"))
        _apply_small_collision_offsets(cloth_prim.GetPrim())

        mat_path = "/World/Materials/DeformableMat"
        deformableUtils.add_surface_deformable_material(
            stage,
            mat_path,
            density=float(spec.mass_kg) / max(sx * sy, 1e-6) / max(float(params.get("surface_thickness", 0.008)), 1e-4),
            static_friction=0.45,
            dynamic_friction=0.35,
            youngs_modulus=float(params["youngs_modulus"]),
            poissons_ratio=float(params["poissons_ratio"]),
            surface_thickness=float(params.get("surface_thickness", 0.008)),
            surface_stretch_stiffness=float(params["surface_stretch_stiffness"]),
            surface_shear_stiffness=float(params["surface_shear_stiffness"]),
            surface_bend_stiffness=float(params["surface_bend_stiffness"]),
        )
        mat_prim = stage.GetPrimAtPath(mat_path)
        mat_prim.ApplyAPI("PhysxDeformableMaterialAPI")
        mat_prim.GetAttribute("physxDeformableMaterial:elasticityDamping").Set(float(params["elasticity_damping"]))
        physicsUtils.add_physics_material_to_prim(stage, cloth_prim.GetPrim(), mat_path)
        body_prim = cloth_prim
        topo = edges_local.astype(np.int64)
        platen_z0 = z_offset + 0.032 + 0.016

    center0 = rest_pts.mean(axis=0)
    if probe_name == "compression_release":
        _, platen_op = _create_kinematic_box(
            stage,
            "/World/Platen",
            size_xyz=(0.24, 0.24, 0.02),
            pos_xyz=(0.0, 0.0, platen_z0),
            with_collision=True,
        )
    elif probe_name in ("gentle_grasp", "crush_counterfactual"):
        thresh = (0.24 * sx) if is_solid else (0.40 * sx)
        left_vtx = np.flatnonzero(rest_pts[:, 0] <= (center0[0] - thresh))
        right_vtx = np.flatnonzero(rest_pts[:, 0] >= (center0[0] + thresh))
        if len(left_vtx) == 0 or len(right_vtx) == 0:
            order_x = np.argsort(rest_pts[:, 0])
            k = max(2, len(order_x) // 6)
            left_vtx = order_x[:k]
            right_vtx = order_x[-k:]

        _, left_op = _create_jaw_anchor(stage, "/World/LeftJaw", center0)
        _, right_op = _create_jaw_anchor(stage, "/World/RightJaw", center0)
        _author_vtx_xform_attachment(
            stage,
            "/World/AttachLeft",
            "/World/DeformableAsset",
            "/World/LeftJaw",
            left_vtx,
            rest_pts[left_vtx] - center0[None, :],
        )
        _author_vtx_xform_attachment(
            stage,
            "/World/AttachRight",
            "/World/DeformableAsset",
            "/World/RightJaw",
            right_vtx,
            rest_pts[right_vtx] - center0[None, :],
        )

    return stage, body_prim, rest_pts, topo, np.array([platen_z0], dtype=np.float64), platen_op, left_op, right_op, 0.0


def _run_probe(
    sim_iface: Any,
    physx_utils: Any,
    deformableUtils: Any,
    physicsUtils: Any,
    spec: DeformableSourceSpec,
    params: dict[str, Any],
    probe_name: str,
    budget: DeformableIntegrityBudget | None,
) -> dict[str, Any]:
    from pxr import Gf, UsdUtils

    dt = 0.002
    is_solid = spec.structural_family == "soft_solid"
    sx, sy, sz = spec.dimensions_xyz_m

    stage, body_prim, rest_pts, topo, pz_arr, platen_op, left_op, right_op, _ = _build_stage_for_probe(
        physx_utils, deformableUtils, physicsUtils, spec, params, probe_name
    )
    platen_z0 = float(pz_arr[0])
    h0 = max(vertical_span_m(rest_pts), 1e-4)
    center0 = rest_pts.mean(axis=0)
    half_span = 0.5 * sx

    stage_id = UsdUtils.StageCache.Get().GetId(stage).ToLongInt()
    sim_iface.attach_stage(stage_id)

    total_steps = 180 if probe_name == "drop" else (200 if probe_name == "compression_release" else 110)
    h_hist: list[float] = []
    pos_hist: list[np.ndarray] = []
    min_z_all = float(rest_pts[:, 2].min())
    contact_steps = 0

    for step_i in range(total_steps):
        if probe_name == "compression_release" and platen_op is not None:
            z_bottom = 0.004 if is_solid else 0.0015
            frac_target = 0.82 if is_solid else 0.52
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
            op, scale_v = platen_op
            mat = Gf.Transform(Gf.Vec3d(0.0, 0.0, z_bot + 0.01), Gf.Rotation(Gf.Quatd(1.0)), scale_v).GetMatrix()
            op.Set(mat)
        elif probe_name == "gentle_grasp" and left_op is not None and right_op is not None:
            s_sq = min(1.0, (step_i + 1) / 40.0) if is_solid else 0.0
            s_rot = min(1.0, max(0.0, (step_i - 15) / 75.0)) if is_solid else min(1.0, (step_i + 1) / 80.0)
            theta = math.radians(35.0) * s_rot
            rot = _rot_y_matrix(theta)
            lift_z = (0.03 if is_solid else 0.04) * s_rot
            dx_local = (half_span * 0.04 * s_sq) if is_solid else (-half_span * 0.02 * s_rot)
            p_l = rot @ np.array([dx_local, 0.0, 0.0]) + center0 + np.array([0.0, 0.0, lift_z])
            p_r = rot @ np.array([-dx_local, 0.0, 0.0]) + center0 + np.array([0.0, 0.0, lift_z])
            gf_rot = Gf.Rotation(Gf.Vec3d(0.0, 1.0, 0.0), math.degrees(theta))
            unit_scale = Gf.Vec3d(1.0)
            left_op.Set(Gf.Transform(Gf.Vec3d(*p_l.tolist()), gf_rot, unit_scale).GetMatrix())
            right_op.Set(Gf.Transform(Gf.Vec3d(*p_r.tolist()), gf_rot, unit_scale).GetMatrix())
        elif probe_name == "crush_counterfactual" and left_op is not None and right_op is not None:
            s_sq = min(1.0, (step_i + 1) / 80.0)
            dx_local = (half_span * 0.58 * s_sq) if is_solid else (-half_span * 0.62 * s_sq)
            p_l = center0 + np.array([dx_local, 0.0, 0.0])
            p_r = center0 + np.array([-dx_local, 0.0, 0.0])
            ident_rot = Gf.Rotation(Gf.Quatd(1.0))
            unit_scale = Gf.Vec3d(1.0)
            left_op.Set(Gf.Transform(Gf.Vec3d(*p_l.tolist()), ident_rot, unit_scale).GetMatrix())
            right_op.Set(Gf.Transform(Gf.Vec3d(*p_r.tolist()), ident_rot, unit_scale).GetMatrix())

        sim_iface.simulate(dt, step_i * dt)
        sim_iface.fetch_results()

        cur_pts = np.asarray(body_prim.GetPointsAttr().Get(), dtype=np.float64).copy()
        if not np.all(np.isfinite(cur_pts)):
            sim_iface.detach_stage()
            physx_utils.release_memory_stage(stage, detach_stage=False)
            return {
                "probe_name": probe_name,
                "finite_fraction": 0.0,
                "contact_fraction": 0.0,
                "penetration_absent": False,
                "settling_ratio": 1.0,
                "steps_executed": step_i + 1,
                "dt_s": dt,
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
            pos_hist.append(cur_pts)

    sim_iface.detach_stage()
    physx_utils.release_memory_stage(stage, detach_stage=False)

    pos_stack = np.stack(pos_hist, axis=0)
    polar_s = None
    naive_s = None
    edge_s = None
    if is_solid:
        F_stack = compute_tet_deformation_gradients(rest_pts, pos_stack, topo)
        polar_s = polar_stretch_strain_from_F(F_stack)
        naive_s = naive_rfws_strain_from_F(F_stack)
        strain_val = polar_s
        peak_force_n = float(params["youngs_modulus"] * (sx * sy) * max(polar_s, 0.01))
    else:
        edge_s = edge_stretch_strain(rest_pts, pos_stack, topo)
        strain_val = edge_s
        peak_force_n = float(params["youngs_modulus"] * (sx * float(params.get("surface_thickness", 0.008))) * max(edge_s, 0.01))

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
        "dt_s": dt,
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
        "extra": {
            "h0": h0,
            "h_min": h_min,
            "h_final": h_final,
            "min_z_all": min_z_all,
            "n_verts": int(len(rest_pts)),
        },
    }


def _export_isaac_usda(
    out_dir: Path,
    physx_utils: Any,
    deformableUtils: Any,
    physicsUtils: Any,
    spec: DeformableSourceSpec,
    params: dict[str, Any],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stage, _, _, _, _, _, _, _, _ = _build_stage_for_probe(
        physx_utils, deformableUtils, physicsUtils, spec, params, "drop"
    )
    usda_path = out_dir / "isaac_physx.usda"
    stage.Export(str(usda_path))
    physx_utils.release_memory_stage(stage, detach_stage=False)


def _evaluate(
    sim_iface: Any,
    physx_utils: Any,
    deformableUtils: Any,
    physicsUtils: Any,
    spec: DeformableSourceSpec,
    probe_list: list[str],
    params: dict[str, Any],
    budget: DeformableIntegrityBudget | None,
) -> dict[str, Any]:
    probes: dict[str, Any] = {}
    for pname in probe_list:
        probes[pname] = _run_probe(
            sim_iface, physx_utils, deformableUtils, physicsUtils, spec, params, pname, budget
        )
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

    from isaacsim import SimulationApp

    app = SimulationApp(
        {
            "headless": True,
            "create_new_stage": False,
            "disable_viewport_updates": True,
            "renderer": "MinimalRendering",
            "minimal_shading_mode": 4,
            "samples_per_pixel_per_frame": 1,
            "denoiser": False,
            "multi_gpu": False,
            "anti_aliasing": 0,
            "limit_cpu_threads": 6,
            "fast_shutdown": True,
            "shutdown_watchdog_timeout": 5.0,
            "extra_args": [
                "--/app/asyncRendering=False",
                "--/physics/updateToUsd=True",
                "--/physics/updateParticlesToUsd=True",
                "--/physics/suppressReadback=False",
            ],
        }
    )

    from omni.physx import get_physx_simulation_interface
    from omni.physx.scripts import deformableUtils, physicsUtils, utils as physx_utils

    sim_iface = get_physx_simulation_interface()
    solver_name = "PhysX_VolumeTet" if spec.structural_family == "soft_solid" else "PhysX_SurfaceDeformable"

    if req.get("candidates"):
        results = []
        for idx, cand in enumerate(req["candidates"]):
            params = {**_default_params(spec), **dict(cand.get("params", {}))}
            probes = _evaluate(
                sim_iface, physx_utils, deformableUtils, physicsUtils, spec, probe_list, params, budget
            )
            results.append({"candidate_id": str(cand.get("id", f"c{idx}")), "params": params, "probes": probes})
            time.sleep(0.08)
        payload = {"engine_id": "isaac_physx", "solver": solver_name, "results": results}
    else:
        params = {**_default_params(spec), **dict(req.get("params") or {})}
        probes = _evaluate(
            sim_iface, physx_utils, deformableUtils, physicsUtils, spec, probe_list, params, budget
        )
        artifact_relpath = ""
        if req.get("artifact_out_dir"):
            _export_isaac_usda(
                Path(req["artifact_out_dir"]), physx_utils, deformableUtils, physicsUtils, spec, params
            )
            artifact_relpath = "engines/isaac_physx/isaac_physx.usda"
        payload = {
            "engine_id": "isaac_physx",
            "solver": solver_name,
            "params": params,
            "probes": probes,
            "artifact_relpath": artifact_relpath,
        }

    Path(args.response).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    sys.stdout.flush()
    app.close()


if __name__ == "__main__":
    main()
