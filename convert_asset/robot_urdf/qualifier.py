"""SimReady Robot Qualification Gate (L0 USD Schema + L1 Pinocchio/Sim FK + L2 Physics).

Verifies modular assembled robots produced by `convert_asset.robot_urdf` BEFORE they
enter long-horizon manipulation tasks:
  - L0 (USD Schema / Physics): ArticulationRoot, Mass/Inertia, Collision approximation,
    Drive stiffness/damping, and optional NVIDIA `omni.asset_validator`.
  - L1 (Kinematics & Cross-Engine FK):
      * Pure-Python Pinocchio check (<1s, zero GPU): joint limits, inertia sanity,
        grasp_frame closing-axis alignment (catches 90-deg jaw rotation bugs), TCP
        centering (catches 45mm flange offset / off-center palm bugs), and positive
        open->close stroke.
      * Cross-engine FK check (inside Isaac Sim): Pinocchio FK vs Isaac Sim live
        grasp_frame / flange poses across multiple joint configurations (<2.5mm threshold).
  - L2 (Empty-Table Physics Smoke, ~15s inside Isaac Sim):
      * 120-step gravity & zero-action stability (no NaN, no collapse/explosion).
      * Mimic / follower EE closure verification (real USD fingertip span shrinks).
      * Single-cylinder grasp & lift unit test (60mm x 110mm rigid cylinder lifted >= 8cm).

CLI:
    # Fast pure-kinematics check (no Isaac Sim needed):
    python -m convert_asset.robot_urdf.qualifier --robot-id all --kinematics-only

    # Full L0+L1+L2 live Isaac Sim 4.1 qualification:
    $SIM_PY -m convert_asset.robot_urdf.qualifier --robot-id all
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import numpy as np


DEFAULT_ROBOTS_ARTIFACT_ROOT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/external_artifacts/cross_embodiment_robots_v1"
)


def _load_meta_and_paths(
    meta_or_dir: str | Path,
    usd_path: str | Path | None = None,
) -> tuple[dict[str, Any], Path, Path, Path]:
    p = Path(meta_or_dir).resolve()
    meta_path = p / "robot_assembly_meta.json" if p.is_dir() else p
    if not meta_path.is_file():
        raise FileNotFoundError(f"Missing robot_assembly_meta.json: {meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    urdf_path = Path(meta["urdf_path"]).resolve()
    resolved_usd = Path(usd_path).resolve() if usd_path is not None else urdf_path.with_suffix(".usd")
    return meta, meta_path, urdf_path, resolved_usd


def _arm_ee_type(meta: dict[str, Any], side: str) -> str:
    spec = meta.get("spec") or {}
    for arm in spec.get("arms") or []:
        if arm.get("side") == side:
            return str(arm.get("ee_type", "parallel_gripper"))
    n_drivers = len(meta.get("ee_driver_joints", {}).get(side, []))
    return "dexterous_hand" if n_drivers >= 5 else "parallel_gripper"


def _set_joint_q(pin_model: Any, q: np.ndarray, joint_name: str, value: float) -> None:
    if not pin_model.existJointName(joint_name):
        return
    jid = pin_model.getJointId(joint_name)
    idx_q = int(pin_model.joints[jid].idx_q)
    nq = int(pin_model.joints[jid].nq)
    if nq == 1:
        q[idx_q] = float(value)
    elif nq == 2:
        q[idx_q] = math.cos(float(value))
        q[idx_q + 1] = math.sin(float(value))


def _apply_ee_driver_targets(
    meta: dict[str, Any],
    side: str,
    driver_values: dict[str, float],
) -> dict[str, float]:
    """Expand EE driver joint targets to all EE joints including mimic followers."""
    targets: dict[str, float] = {jn: float(val) for jn, val in driver_values.items()}
    mimics = meta.get("mimic_joints", {}).get(side, {})
    for follower, mcfg in mimics.items():
        ref = mcfg["joint"]
        if ref in targets:
            mult = float(mcfg.get("multiplier", 1.0))
            off = float(mcfg.get("offset", 0.0))
            targets[follower] = targets[ref] * mult + off
    return targets


def _find_parallel_tip_frames(pin_model: Any, side: str) -> tuple[str | None, str | None]:
    import pinocchio as pin  # type: ignore

    prefix = f"{side}_ee_"
    body_names = [
        f.name
        for f in pin_model.frames
        if f.type == pin.FrameType.BODY and f.name.startswith(prefix)
    ]

    def _pick(side_kw: str) -> str | None:
        ranked: list[tuple[int, str]] = []
        for name in body_names:
            tail = name[len(prefix) :].lower()
            if side_kw not in tail:
                continue
            if "finger_tcp" in tail or "pad" in tail:
                score = 0
            elif "finger_tip" in tail or "tip_link" in tail:
                score = 1
            elif "finger" in tail and "mount" not in tail:
                score = 2
            else:
                continue
            ranked.append((score, name))
        ranked.sort()
        return ranked[0][1] if ranked else None

    return _pick("left"), _pick("right")


def _find_dexterous_tip_frames(pin_model: Any, side: str) -> tuple[list[str], str | None]:
    import pinocchio as pin  # type: ignore

    prefix = f"{side}_ee_"
    body_names = [
        f.name
        for f in pin_model.frames
        if f.type == pin.FrameType.BODY and f.name.startswith(prefix)
    ]
    tips = [n for n in body_names if re.search(r"(tip_link|finger\d+_tip|distal)", n[len(prefix) :].lower())]
    if not tips:
        tips = [n for n in body_names if "tip" in n[len(prefix) :].lower()]
    palms = [n for n in body_names if "palm" in n[len(prefix) :].lower()]
    return sorted(tips), (palms[0] if palms else None)


def _eval_ee_span_and_center(
    pin_model: Any,
    pin_data: Any,
    q: np.ndarray,
    grasp_frame: str,
    tip_frames: list[str],
) -> tuple[np.ndarray, list[np.ndarray], float]:
    """Return tip centroid, per-tip local coords in grasp_frame, and span."""
    import pinocchio as pin  # type: ignore

    pin.forwardKinematics(pin_model, pin_data, q)
    pin.updateFramePlacements(pin_model, pin_data)
    gf_id = pin_model.getFrameId(grasp_frame)
    inv_g = pin_data.oMf[gf_id].inverse()

    local_pts: list[np.ndarray] = []
    for tf in tip_frames:
        tid = pin_model.getFrameId(tf)
        p_local = np.asarray((inv_g * pin_data.oMf[tid]).translation, dtype=float)
        local_pts.append(p_local)

    centroid = np.mean(np.stack(local_pts, axis=0), axis=0)
    if len(local_pts) == 2:
        span = float(np.linalg.norm(local_pts[0] - local_pts[1]))
    else:
        dists = [float(np.linalg.norm(p - centroid)) for p in local_pts]
        span = float(np.mean(dists)) * 2.0
    return centroid, local_pts, span


def _infer_open_close_driver_values(
    pin_model: Any,
    pin_data: Any,
    meta: dict[str, Any],
    side: str,
    grasp_frame: str,
    tip_frames: list[str],
) -> tuple[dict[str, float], dict[str, float], float, float]:
    """Auto-detect which joint-limit end is OPEN vs CLOSED using Pinocchio FK."""
    import pinocchio as pin  # type: ignore

    drivers = meta.get("ee_driver_joints", {}).get(side, [])
    limits = meta.get("joint_limits", {})
    low_vals = {j: float(limits[j]["lower"]) for j in drivers if j in limits}
    high_vals = {j: float(limits[j]["upper"]) for j in drivers if j in limits}

    q_low = pin.neutral(pin_model)
    for jn, v in _apply_ee_driver_targets(meta, side, low_vals).items():
        _set_joint_q(pin_model, q_low, jn, v)
    _, _, span_low = _eval_ee_span_and_center(pin_model, pin_data, q_low, grasp_frame, tip_frames)

    q_high = pin.neutral(pin_model)
    for jn, v in _apply_ee_driver_targets(meta, side, high_vals).items():
        _set_joint_q(pin_model, q_high, jn, v)
    _, _, span_high = _eval_ee_span_and_center(pin_model, pin_data, q_high, grasp_frame, tip_frames)

    if span_low >= span_high:
        return low_vals, high_vals, span_low, span_high
    return high_vals, low_vals, span_high, span_low


def run_kinematic_qualification(
    meta_or_dir: str | Path,
    *,
    max_closing_axis_angle_deg: float = 15.0,
    max_parallel_tcp_err_m: float = 0.025,
    min_parallel_stroke_m: float = 0.025,
    max_dexterous_palm_offset_m: float = 0.045,
    min_dexterous_contraction_m: float = 0.015,
) -> dict[str, Any]:
    """Run pure-Python L1 kinematic & geometric qualification (<1s, zero GPU)."""
    import pinocchio as pin  # type: ignore

    meta, meta_path, urdf_path, _ = _load_meta_and_paths(meta_or_dir)
    failures: list[dict[str, Any]] = []
    warnings: list[str] = []

    # --- L1.1 URDF XML inertia & joint-limit audit ---
    root = ET.parse(urdf_path).getroot()
    bad_mass_links: list[str] = []
    bad_inertia_links: list[str] = []
    tiny_inertia_links: list[str] = []
    for link in root.findall("link"):
        lname = link.attrib.get("name", "<unnamed>")
        inertial = link.find("inertial")
        if inertial is None:
            bad_mass_links.append(lname)
            continue
        m_el = inertial.find("mass")
        m_val = float(m_el.attrib.get("value", "0")) if m_el is not None else 0.0
        if not math.isfinite(m_val) or m_val <= 0.0:
            bad_mass_links.append(lname)
        i_el = inertial.find("inertia")
        if i_el is None:
            bad_inertia_links.append(lname)
        else:
            ixx = float(i_el.attrib.get("ixx", "0"))
            iyy = float(i_el.attrib.get("iyy", "0"))
            izz = float(i_el.attrib.get("izz", "0"))
            if min(ixx, iyy, izz) <= 0.0 or not all(math.isfinite(v) for v in (ixx, iyy, izz)):
                bad_inertia_links.append(lname)
            elif min(ixx, iyy, izz) < 5e-6 and "grasp_frame" not in lname:
                tiny_inertia_links.append(lname)

    if bad_mass_links:
        failures.append({"code": "URDF_INVALID_MASS", "links": bad_mass_links})
    if bad_inertia_links:
        failures.append({"code": "URDF_INVALID_INERTIA", "links": bad_inertia_links})
    if tiny_inertia_links:
        warnings.append(f"Tiny inertia (<5e-6) on {len(tiny_inertia_links)} links: {tiny_inertia_links[:5]}")

    bad_limits: list[str] = []
    for jname, lim in (meta.get("joint_limits") or {}).items():
        lo, hi = float(lim.get("lower", 0.0)), float(lim.get("upper", 0.0))
        if not (math.isfinite(lo) and math.isfinite(hi) and lo < hi):
            bad_limits.append(jname)
    if bad_limits:
        failures.append({"code": "URDF_INVALID_JOINT_LIMITS", "joints": bad_limits})

    # --- L1.2 Pinocchio FK & Grasp Frame Geometry Audit ---
    pin_model = pin.buildModelFromUrdf(str(urdf_path))
    pin_data = pin_model.createData()
    arm_reports: dict[str, Any] = {}

    for side, grasp_frame in (meta.get("grasp_frames") or {}).items():
        if not pin_model.existFrame(grasp_frame):
            failures.append({"code": "MISSING_GRASP_FRAME", "side": side, "frame": grasp_frame})
            continue
        ee_type = _arm_ee_type(meta, side)
        if ee_type == "parallel_gripper":
            ltip, rtip = _find_parallel_tip_frames(pin_model, side)
            if not ltip or not rtip:
                failures.append(
                    {"code": "MISSING_PARALLEL_TIP_FRAMES", "side": side, "left_tip": ltip, "right_tip": rtip}
                )
                continue
            tip_frames = [ltip, rtip]
            open_vals, close_vals, span_open, span_close = _infer_open_close_driver_values(
                pin_model, pin_data, meta, side, grasp_frame, tip_frames
            )
            q_open = pin.neutral(pin_model)
            for jn, v in _apply_ee_driver_targets(meta, side, open_vals).items():
                _set_joint_q(pin_model, q_open, jn, v)
            open_mid, open_pts, _ = _eval_ee_span_and_center(pin_model, pin_data, q_open, grasp_frame, tip_frames)

            q_mid = pin.neutral(pin_model)
            mid_vals = {j: 0.5 * (open_vals[j] + close_vals[j]) for j in open_vals}
            for jn, v in _apply_ee_driver_targets(meta, side, mid_vals).items():
                _set_joint_q(pin_model, q_mid, jn, v)
            mid_center, _, span_mid = _eval_ee_span_and_center(pin_model, pin_data, q_mid, grasp_frame, tip_frames)

            q_close = pin.neutral(pin_model)
            for jn, v in _apply_ee_driver_targets(meta, side, close_vals).items():
                _set_joint_q(pin_model, q_close, jn, v)
            close_mid, _, _ = _eval_ee_span_and_center(pin_model, pin_data, q_close, grasp_frame, tip_frames)

            sep_vec = open_pts[0] - open_pts[1]
            sep_norm = float(np.linalg.norm(sep_vec))
            if sep_norm < 1e-6:
                angle_to_y_deg = 90.0
            else:
                cos_y = abs(float(sep_vec[1]) / sep_norm)
                angle_to_y_deg = math.degrees(math.acos(min(1.0, max(0.0, cos_y))))

            tcp_err_best_m = min(
                float(np.linalg.norm(mid_center)),
                float(np.linalg.norm(close_mid)),
                float(np.linalg.norm(open_mid)),
            )
            stroke_m = float(span_open - span_close)

            arm_reports[side] = {
                "ee_type": ee_type,
                "grasp_frame": grasp_frame,
                "tip_frames": tip_frames,
                "open_driver_values": open_vals,
                "close_driver_values": close_vals,
                "span_open_m": round(span_open, 5),
                "span_mid_m": round(span_mid, 5),
                "span_close_m": round(span_close, 5),
                "stroke_m": round(stroke_m, 5),
                "closing_axis_angle_to_y_deg": round(angle_to_y_deg, 3),
                "tcp_midpoint_open_local_m": [round(float(x), 5) for x in open_mid],
                "tcp_midpoint_mid_local_m": [round(float(x), 5) for x in mid_center],
                "tcp_midpoint_close_local_m": [round(float(x), 5) for x in close_mid],
                "tcp_err_best_m": round(tcp_err_best_m, 5),
            }

            if angle_to_y_deg > max_closing_axis_angle_deg:
                failures.append(
                    {
                        "code": "GRASP_FRAME_CLOSING_AXIS_MISALIGNED",
                        "side": side,
                        "angle_to_y_deg": round(angle_to_y_deg, 2),
                        "threshold_deg": max_closing_axis_angle_deg,
                    }
                )
            if tcp_err_best_m > max_parallel_tcp_err_m:
                failures.append(
                    {
                        "code": "GRASP_FRAME_TCP_OFFSET_TOO_LARGE",
                        "side": side,
                        "tcp_err_best_m": round(tcp_err_best_m, 5),
                        "threshold_m": max_parallel_tcp_err_m,
                    }
                )
            if stroke_m < min_parallel_stroke_m:
                failures.append(
                    {
                        "code": "GRIPPER_STROKE_TOO_SMALL",
                        "side": side,
                        "stroke_m": round(stroke_m, 5),
                        "threshold_m": min_parallel_stroke_m,
                    }
                )
        else:
            tips, palm = _find_dexterous_tip_frames(pin_model, side)
            if len(tips) < 3:
                failures.append({"code": "MISSING_DEXTEROUS_TIP_FRAMES", "side": side, "tips": tips})
                continue
            open_vals, close_vals, span_open, span_close = _infer_open_close_driver_values(
                pin_model, pin_data, meta, side, grasp_frame, tips
            )
            q_half = pin.neutral(pin_model)
            half_vals = {j: 0.55 * close_vals[j] + 0.45 * open_vals[j] for j in open_vals}
            for jn, v in _apply_ee_driver_targets(meta, side, half_vals).items():
                _set_joint_q(pin_model, q_half, jn, v)
            half_centroid, _, span_half = _eval_ee_span_and_center(pin_model, pin_data, q_half, grasp_frame, tips)

            q_close = pin.neutral(pin_model)
            for jn, v in _apply_ee_driver_targets(meta, side, close_vals).items():
                _set_joint_q(pin_model, q_close, jn, v)
            close_centroid, _, _ = _eval_ee_span_and_center(pin_model, pin_data, q_close, grasp_frame, tips)

            palm_offset_m = float(np.linalg.norm(half_centroid))
            contraction_m = float(span_open - span_close)

            arm_reports[side] = {
                "ee_type": ee_type,
                "grasp_frame": grasp_frame,
                "palm_frame": palm,
                "tip_frames": tips,
                "span_open_m": round(span_open, 5),
                "span_half_m": round(span_half, 5),
                "span_close_m": round(span_close, 5),
                "contraction_m": round(contraction_m, 5),
                "half_centroid_local_m": [round(float(x), 5) for x in half_centroid],
                "close_centroid_local_m": [round(float(x), 5) for x in close_centroid],
                "palm_pocket_err_m": round(palm_offset_m, 5),
            }

            if palm_offset_m > max_dexterous_palm_offset_m:
                failures.append(
                    {
                        "code": "DEXTEROUS_GRASP_FRAME_OFF_PALM_POCKET",
                        "side": side,
                        "palm_pocket_err_m": round(palm_offset_m, 5),
                        "threshold_m": max_dexterous_palm_offset_m,
                    }
                )
            if contraction_m < min_dexterous_contraction_m:
                failures.append(
                    {
                        "code": "DEXTEROUS_HAND_CONTRACTION_TOO_SMALL",
                        "side": side,
                        "contraction_m": round(contraction_m, 5),
                        "threshold_m": min_dexterous_contraction_m,
                    }
                )

    return {
        "robot_id": meta["robot_id"],
        "meta_path": str(meta_path),
        "urdf_path": str(urdf_path),
        "pinocchio_nq": int(pin_model.nq),
        "passed": len(failures) == 0,
        "failures": failures,
        "warnings": warnings,
        "arms": arm_reports,
    }


def _run_l0_usd_schema_audit(usd_path: Path, meta: dict[str, Any]) -> dict[str, Any]:
    """L0: OpenUSD / PhysX schema audit (+ optional omni.asset_validator)."""
    from pxr import Usd, UsdPhysics  # type: ignore

    failures: list[dict[str, Any]] = []
    warnings: list[str] = []

    if not usd_path.is_file():
        return {"passed": False, "failures": [{"code": "MISSING_USD", "usd_path": str(usd_path)}], "warnings": []}

    stage = Usd.Stage.Open(str(usd_path))
    art_roots: list[str] = []
    rigid_bodies = 0
    zero_mass_bodies: list[str] = []
    raw_mesh_colliders: list[str] = []
    actuated_drives: dict[str, dict[str, float]] = {}

    expected_actuated = {
        jn
        for d in (meta.get("arm_joints") or {}, meta.get("ee_joints") or {})
        for jlist in d.values()
        for jn in jlist
    }

    for prim in stage.Traverse():
        pstr = str(prim.GetPath())
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            art_roots.append(pstr)
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            rigid_bodies += 1
            if prim.HasAPI(UsdPhysics.MassAPI):
                mass_attr = UsdPhysics.MassAPI(prim).GetMassAttr()
                if mass_attr and mass_attr.HasValue():
                    if float(mass_attr.Get()) <= 0.0:
                        zero_mass_bodies.append(pstr)
        if prim.HasAPI(UsdPhysics.MeshCollisionAPI):
            if UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get() == "none":
                raw_mesh_colliders.append(pstr)
        if prim.HasAPI(UsdPhysics.DriveAPI):
            drive = UsdPhysics.DriveAPI.Get(prim, "angular") or UsdPhysics.DriveAPI.Get(prim, "linear")
            if drive:
                stiff = float(drive.GetStiffnessAttr().Get() or 0.0)
                damp = float(drive.GetDampingAttr().Get() or 0.0)
                actuated_drives[prim.GetName()] = {"stiffness": stiff, "damping": damp}

    if len(art_roots) == 0:
        failures.append({"code": "USD_NO_ARTICULATION_ROOT"})
    elif len(art_roots) > 1:
        warnings.append(f"Multiple ArticulationRootAPI prims found: {art_roots}")
    if zero_mass_bodies:
        failures.append({"code": "USD_ZERO_MASS_BODIES", "prims": zero_mass_bodies[:10]})
    if raw_mesh_colliders:
        failures.append({"code": "USD_RAW_MESH_COLLIDERS_NONE", "prims": raw_mesh_colliders[:10]})

    missing_drives = sorted(j for j in expected_actuated if j not in actuated_drives)
    zero_stiff_drives = sorted(
        j for j in expected_actuated if j in actuated_drives and actuated_drives[j]["stiffness"] <= 0.0
    )
    if missing_drives:
        failures.append({"code": "USD_MISSING_JOINT_DRIVES", "joints": missing_drives[:10], "count": len(missing_drives)})
    if zero_stiff_drives:
        failures.append({"code": "USD_ZERO_STIFFNESS_DRIVES", "joints": zero_stiff_drives[:10]})

    validator_info: dict[str, Any] = {"available": False}
    try:
        import omni.asset_validator.core as av  # type: ignore

        engine = av.ValidationEngine()
        results = engine.validate(str(usd_path))
        issues = [str(i) for i in results.issues() if getattr(i, "severity", None) and "ERROR" in str(i.severity)]
        validator_info = {"available": True, "error_count": len(issues), "sample_errors": issues[:5]}
    except Exception as exc:
        validator_info = {"available": False, "note": f"{type(exc).__name__}: {exc}"}

    return {
        "passed": len(failures) == 0,
        "usd_path": str(usd_path),
        "articulation_roots": art_roots,
        "rigid_body_count": rigid_bodies,
        "actuated_drive_count": len(actuated_drives),
        "omni_asset_validator": validator_info,
        "failures": failures,
        "warnings": warnings,
    }


def _find_prim_path_by_suffix(stage: Any, root_prefix: str, target_name: str) -> str | None:
    for prim in stage.Traverse():
        pstr = str(prim.GetPath())
        if pstr.startswith(root_prefix) and prim.GetName() == target_name:
            return pstr
    return None


def run_sim_qualification(
    meta_or_dir: str | Path,
    *,
    usd_path: str | Path | None = None,
    fk_tolerance_m: float = 0.0025,
    stability_steps: int = 120,
    run_cylinder_lift: bool = True,
    write_report: bool = True,
) -> dict[str, Any]:
    """Run full L0 + L1 (Pinocchio + Cross-Engine FK) + L2 (Physics) inside active SimulationApp."""
    import pinocchio as pin  # type: ignore
    from omni.isaac.core import World  # type: ignore
    from omni.isaac.core.objects import DynamicCylinder, DynamicSphere, FixedCuboid  # type: ignore
    from omni.isaac.core.robots import Robot  # type: ignore
    from omni.isaac.core.utils.stage import add_reference_to_stage, create_new_stage  # type: ignore
    from omni.isaac.core.utils.types import ArticulationAction  # type: ignore
    from pxr import PhysxSchema, Usd, UsdGeom, UsdPhysics, UsdShade  # type: ignore

    meta, meta_path, urdf_path, resolved_usd = _load_meta_and_paths(meta_or_dir, usd_path=usd_path)

    l1_kin = run_kinematic_qualification(meta_path)
    l0_usd = _run_l0_usd_schema_audit(resolved_usd, meta)

    create_new_stage()
    world = World(stage_units_in_meters=1.0, physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0)
    world.scene.add_default_ground_plane()

    robot_prim_path = f"/World/{meta['robot_id']}"
    add_reference_to_stage(usd_path=str(resolved_usd), prim_path=robot_prim_path)
    robot = world.scene.add(Robot(prim_path=robot_prim_path, name=meta["robot_id"]))
    world.reset()

    dof_names: list[str] = list(robot.dof_names)
    dof_idx = {n: i for i, n in enumerate(dof_names)}
    stage = world.stage
    pin_model = pin.buildModelFromUrdf(str(urdf_path))
    pin_data = pin_model.createData()

    def _step_to(targets_by_name: dict[str, float], n_steps: int) -> np.ndarray:
        cur = np.asarray(robot.get_joint_positions(), dtype=float)
        tgt = cur.copy()
        for jn, val in targets_by_name.items():
            if jn in dof_idx:
                tgt[dof_idx[jn]] = float(val)
        for s in range(1, n_steps + 1):
            alpha = min(1.0, s / max(1, n_steps // 2))
            cmd = cur * (1.0 - alpha) + tgt * alpha
            robot.apply_action(ArticulationAction(joint_positions=cmd))
            world.step(render=False)
        return np.asarray(robot.get_joint_positions(), dtype=float)

    def _sim_link_world_pos(link_name: str) -> np.ndarray | None:
        p = _find_prim_path_by_suffix(stage, robot_prim_path, link_name)
        if p is None:
            return None
        prim = stage.GetPrimAtPath(p)
        xform = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(prim)
        t = xform.ExtractTranslation()
        return np.array([float(t[0]), float(t[1]), float(t[2])], dtype=float)

    home_targets: dict[str, float] = {}
    for _, ajoints in (meta.get("arm_joints") or {}).items():
        default_arm = [0.0, -0.45, 0.0, -1.85, 0.0, 1.45, 0.78]
        for idx, jn in enumerate(ajoints):
            lim = meta["joint_limits"].get(jn, {"lower": -2.0, "upper": 2.0})
            val = default_arm[idx] if idx < len(default_arm) else 0.0
            home_targets[jn] = float(np.clip(val, lim["lower"] + 0.05, lim["upper"] - 0.05))
    for side, arep in l1_kin.get("arms", {}).items():
        if "open_driver_values" in arep:
            home_targets.update(_apply_ee_driver_targets(meta, side, arep["open_driver_values"]))

    # --- L2.1 Gravity & Zero-Action Stability Test ---
    q_home = _step_to(home_targets, 60)
    q_before_hold = q_home.copy()
    nan_detected = False
    for _ in range(stability_steps):
        robot.apply_action(ArticulationAction(joint_positions=q_before_hold))
        world.step(render=False)
        q_now = np.asarray(robot.get_joint_positions(), dtype=float)
        if not np.all(np.isfinite(q_now)):
            nan_detected = True
            break
    q_after_hold = np.asarray(robot.get_joint_positions(), dtype=float)
    max_hold_drift_rad = float(np.max(np.abs(q_after_hold - q_before_hold))) if not nan_detected else float("inf")
    l2_stability = {
        "passed": (not nan_detected) and (max_hold_drift_rad < 0.25),
        "steps": stability_steps,
        "nan_detected": nan_detected,
        "max_joint_drift_rad": round(max_hold_drift_rad, 5) if math.isfinite(max_hold_drift_rad) else None,
    }

    # --- L1 Cross-Engine FK Consistency (Pinocchio vs Isaac Sim) ---
    fk_checks: list[dict[str, Any]] = []
    max_fk_err_m = 0.0
    for tidx, delta in enumerate((0.0, 0.22, -0.18)):
        pose_targets = dict(home_targets)
        for _, ajoints in (meta.get("arm_joints") or {}).items():
            for j_i in (0, 2, 4):
                if j_i < len(ajoints):
                    jn = ajoints[j_i]
                    lim = meta["joint_limits"].get(jn, {"lower": -2.0, "upper": 2.0})
                    pose_targets[jn] = float(np.clip(home_targets[jn] + delta, lim["lower"] + 0.05, lim["upper"] - 0.05))
        q_sim = _step_to(pose_targets, 45)
        q_pin = pin.neutral(pin_model)
        for jn, idx in dof_idx.items():
            _set_joint_q(pin_model, q_pin, jn, float(q_sim[idx]))
        pin.forwardKinematics(pin_model, pin_data, q_pin)
        pin.updateFramePlacements(pin_model, pin_data)

        for side in (meta.get("grasp_frames") or {}):
            target_frame = meta["grasp_frames"][side]
            sim_pos = _sim_link_world_pos(target_frame)
            if sim_pos is None:
                target_frame = meta["flange_frames"][side]
                sim_pos = _sim_link_world_pos(target_frame)
            if sim_pos is None or not pin_model.existFrame(target_frame):
                fk_checks.append({"pose_idx": tidx, "side": side, "frame": target_frame, "error": "FRAME_NOT_FOUND"})
                max_fk_err_m = float("inf")
                continue
            pin_pos = np.asarray(pin_data.oMf[pin_model.getFrameId(target_frame)].translation, dtype=float)
            err_m = float(np.linalg.norm(sim_pos - pin_pos))
            max_fk_err_m = max(max_fk_err_m, err_m)
            fk_checks.append({"pose_idx": tidx, "side": side, "frame": target_frame, "err_m": round(err_m, 6)})
    l1_cross_fk = {
        "passed": math.isfinite(max_fk_err_m) and max_fk_err_m <= fk_tolerance_m,
        "max_pos_err_m": round(max_fk_err_m, 6) if math.isfinite(max_fk_err_m) else None,
        "tolerance_m": fk_tolerance_m,
        "checks": fk_checks,
    }

    # --- L2.2 Mimic / End-Effector Real Physical Closure Verification ---
    _step_to(home_targets, 30)
    ee_closure_report: dict[str, Any] = {}
    ee_closure_passed = True
    for side, arep in l1_kin.get("arms", {}).items():
        tip_frames: list[str] = list(arep.get("tip_frames", []))
        ee_type = arep.get("ee_type", "parallel_gripper")
        if ee_type == "parallel_gripper":
            open_vals = arep["open_driver_values"]
            close_vals = arep["close_driver_values"]
        else:
            open_vals, close_vals, _, _ = _infer_open_close_driver_values(
                pin_model, pin_data, meta, side, meta["grasp_frames"][side], tip_frames
            )

        open_targets = dict(home_targets)
        open_targets.update(_apply_ee_driver_targets(meta, side, open_vals))
        _step_to(open_targets, 30)
        open_pts = [p for tf in tip_frames if (p := _sim_link_world_pos(tf)) is not None]

        close_targets = dict(home_targets)
        close_targets.update(_apply_ee_driver_targets(meta, side, close_vals))
        q_closed = _step_to(close_targets, 70)
        close_pts = [p for tf in tip_frames if (p := _sim_link_world_pos(tf)) is not None]

        if len(open_pts) >= 2 and len(close_pts) >= 2:
            if len(open_pts) == 2:
                sim_open_span = float(np.linalg.norm(open_pts[0] - open_pts[1]))
                sim_close_span = float(np.linalg.norm(close_pts[0] - close_pts[1]))
            else:
                oc = np.mean(open_pts, axis=0)
                cc = np.mean(close_pts, axis=0)
                sim_open_span = float(np.mean([np.linalg.norm(p - oc) for p in open_pts])) * 2.0
                sim_close_span = float(np.mean([np.linalg.norm(p - cc) for p in close_pts])) * 2.0
            sim_shrink_m = sim_open_span - sim_close_span
        else:
            sim_open_span = sim_close_span = sim_shrink_m = 0.0

        follower_errs: list[float] = []
        for follower in (meta.get("mimic_joints", {}).get(side, {}) or {}):
            if follower in dof_idx and follower in close_targets:
                follower_errs.append(abs(float(q_closed[dof_idx[follower]]) - float(close_targets[follower])))
        max_follower_err = max(follower_errs) if follower_errs else 0.0
        min_req_shrink = 0.020 if ee_type == "parallel_gripper" else 0.012
        side_ok = (sim_shrink_m >= min_req_shrink) and (max_follower_err < 0.35)
        if not side_ok:
            ee_closure_passed = False
        ee_closure_report[side] = {
            "passed": side_ok,
            "sim_open_span_m": round(sim_open_span, 5),
            "sim_close_span_m": round(sim_close_span, 5),
            "sim_shrink_m": round(sim_shrink_m, 5),
            "max_mimic_follower_err_rad": round(max_follower_err, 5),
        }

    # --- L2.3 Empty-Table Single-Cylinder Grasp & Lift Test (Right Arm) ---
    l2_cylinder_lift: dict[str, Any] = {"skipped": not run_cylinder_lift, "passed": True}
    if run_cylinder_lift and "right" in (meta.get("grasp_frames") or {}):
        side = "right"
        arep = l1_kin["arms"][side]
        ee_type = arep["ee_type"]
        tip_frames = list(arep["tip_frames"])
        if ee_type == "parallel_gripper":
            open_vals = arep["open_driver_values"]
            close_vals = arep["close_driver_values"]
        else:
            open_vals, close_vals, _, _ = _infer_open_close_driver_values(
                pin_model, pin_data, meta, side, meta["grasp_frames"][side], tip_frames
            )

        open_targets = dict(home_targets)
        open_targets.update(_apply_ee_driver_targets(meta, side, open_vals))
        q_start = _step_to(open_targets, 40)

        # Orient right_grasp_frame cleanly for a vertical cylinder grasp using Pinocchio Jacobian:
        #   - parallel_gripper: top-down grasp (local Z -> [0, 0, -1], closing Y horizontal)
        #   - dexterous_hand:   human-like side power grasp (local Y -> [0, 0, 1], fingers curl horizontally)
        arm_jnames = list(meta["arm_joints"][side])
        gf_id = pin_model.getFrameId(meta["grasp_frames"][side])
        arm_v_cols = [int(pin_model.joints[pin_model.getJointId(jn)].idx_v) for jn in arm_jnames]
        # Compute minimal-twist target orientation:
        #   - parallel_gripper: align local Z -> [0, 0, -1] (preserve natural wrist yaw)
        #   - dexterous_hand:   human-like side power grasp (local Y -> [0, 0, 1])
        q_p0 = pin.neutral(pin_model)
        for jn, idx in dof_idx.items():
            _set_joint_q(pin_model, q_p0, jn, float(q_start[idx]))
        pin.forwardKinematics(pin_model, pin_data, q_p0)
        pin.updateFramePlacements(pin_model, pin_data)
        R0 = np.asarray(pin_data.oMf[gf_id].rotation, dtype=float)
        if ee_type == "parallel_gripper":
            z_des = np.array([0.0, 0.0, -1.0], dtype=float)
            x_proj = R0[:, 0] - float(np.dot(R0[:, 0], z_des)) * z_des
            if float(np.linalg.norm(x_proj)) < 1e-3:
                x_proj = np.array([1.0, 0.0, 0.0], dtype=float)
            x_des = x_proj / float(np.linalg.norm(x_proj))
            y_des = np.cross(z_des, x_des)
            R_des = np.column_stack([x_des, y_des, z_des])
        else:
            # Palm facing UP (+X_local -> [0, 0, +1]): open fingers stay below the object
            # with zero spawn overlap, then all 5 fingers curl upward to cradle & squeeze it.
            R_des = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)

        q_align = q_start.copy()
        for _ in range(70):
            q_p = pin.neutral(pin_model)
            for jn, idx in dof_idx.items():
                _set_joint_q(pin_model, q_p, jn, float(q_align[idx]))
            pin.forwardKinematics(pin_model, pin_data, q_p)
            pin.computeJointJacobians(pin_model, pin_data, q_p)
            pin.updateFramePlacements(pin_model, pin_data)
            R_cur = np.asarray(pin_data.oMf[gf_id].rotation, dtype=float)
            rot_err_vec = pin.log3(R_des @ R_cur.T)
            if float(np.linalg.norm(rot_err_vec)) < 0.03:
                break
            J_full = pin.getFrameJacobian(pin_model, pin_data, gf_id, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
            J_rot = J_full[3:6, arm_v_cols]
            step_w = np.clip(rot_err_vec, -0.15, 0.15)
            dq = J_rot.T @ np.linalg.solve(J_rot @ J_rot.T + 1e-2 * np.eye(3), step_w)
            dq = np.clip(dq, -0.06, 0.06)
            for k, jn in enumerate(arm_jnames):
                lim = meta["joint_limits"][jn]
                q_align[dof_idx[jn]] = float(np.clip(q_align[dof_idx[jn]] + dq[k], lim["lower"], lim["upper"]))
            for jn, v in _apply_ee_driver_targets(meta, side, open_vals).items():
                if jn in dof_idx:
                    q_align[dof_idx[jn]] = float(v)
            robot.apply_action(ArticulationAction(joint_positions=q_align))
            world.step(render=False)
        for _ in range(20):
            robot.apply_action(ArticulationAction(joint_positions=q_align))
            world.step(render=False)
        q_start = np.asarray(robot.get_joint_positions(), dtype=float)

        q_pin = pin.neutral(pin_model)
        for jn, idx in dof_idx.items():
            _set_joint_q(pin_model, q_pin, jn, float(q_start[idx]))
        pin.forwardKinematics(pin_model, pin_data, q_pin)
        pin.updateFramePlacements(pin_model, pin_data)
        gf_pos = np.asarray(pin_data.oMf[gf_id].translation, dtype=float)

        if ee_type == "parallel_gripper":
            cyl_h = 0.11
            cyl_r = 0.022
            support_h = 0.04
            support_z = float(gf_pos[2]) - cyl_h * 0.5 - support_h * 0.5 - 0.002

            world.scene.add(
                FixedCuboid(
                    prim_path="/World/QualTestSupport",
                    name="qual_test_support",
                    position=np.array([gf_pos[0], gf_pos[1], support_z], dtype=float),
                    scale=np.array([0.16, 0.16, support_h], dtype=float),
                )
            )
            cyl = world.scene.add(
                DynamicCylinder(
                    prim_path="/World/QualTestCylinder",
                    name="qual_test_cylinder",
                    position=np.array([gf_pos[0], gf_pos[1], gf_pos[2]], dtype=float),
                    radius=cyl_r,
                    height=cyl_h,
                    mass=0.10,
                )
            )
        else:
            # For 5-finger palm-up power grasp, pre-cup the hand to 35% flexion so the
            # fingers form a cradle, spawn a 64mm sphere directly in the cupped palm,
            # then curl all 5 fingers to wrap & lift.
            cup_vals = {}
            for j in open_vals:
                if re.search(r"finger[2-5]_joint2$", j):
                    lim = meta["joint_limits"][j]
                    cup_vals[j] = float(np.clip(0.0, lim["lower"], lim["upper"]))
                else:
                    cup_vals[j] = 0.35 * close_vals[j] + 0.65 * open_vals[j]
            cup_cmd = {jn: float(q_start[idx]) for jn, idx in dof_idx.items()}
            cup_cmd.update(_apply_ee_driver_targets(meta, side, cup_vals))
            q_start = _step_to(cup_cmd, 30)
            q_pin2 = pin.neutral(pin_model)
            for jn, idx in dof_idx.items():
                _set_joint_q(pin_model, q_pin2, jn, float(q_start[idx]))
            pin.forwardKinematics(pin_model, pin_data, q_pin2)
            pin.updateFramePlacements(pin_model, pin_data)
            gf_pos = np.asarray(pin_data.oMf[gf_id].translation, dtype=float)
            cyl = world.scene.add(
                DynamicSphere(
                    prim_path="/World/QualTestCylinder",
                    name="qual_test_cylinder",
                    position=np.array([gf_pos[0], gf_pos[1], gf_pos[2] + 0.012], dtype=float),
                    radius=0.034,
                    mass=0.10,
                )
            )
        cmat = UsdShade.Material.Define(stage, "/World/Looks/QualCylFriction")
        pmat = UsdPhysics.MaterialAPI.Apply(cmat.GetPrim())
        pmat.CreateStaticFrictionAttr(1.2)
        pmat.CreateDynamicFrictionAttr(1.0)
        pmat.CreateRestitutionAttr(0.0)
        PhysxSchema.PhysxMaterialAPI.Apply(cmat.GetPrim()).CreateFrictionCombineModeAttr("max")
        UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath("/World/QualTestCylinder")).Bind(
            cmat, UsdShade.Tokens.weakerThanDescendants, "physics"
        )

        for _ in range(15):
            robot.apply_action(ArticulationAction(joint_positions=q_start))
            world.step(render=False)
        cyl_pos_0, _ = cyl.get_world_pose()
        z0 = float(cyl_pos_0[2])

        # For dexterous hands, keep lateral abduction (joint2 on fingers 2-5) neutral and
        # curl flexion joints cleanly into a cylindrical power-wrap rather than lateral splay.
        if ee_type == "dexterous_hand":
            grasp_vals = {}
            for j in open_vals:
                if re.search(r"finger[2-5]_joint2$", j):
                    lim = meta["joint_limits"][j]
                    grasp_vals[j] = float(np.clip(0.0, lim["lower"], lim["upper"]))
                elif re.search(r"finger1_joint1$", j):
                    grasp_vals[j] = 0.85 * close_vals[j] + 0.15 * open_vals[j]
                else:
                    grasp_vals[j] = 0.72 * close_vals[j] + 0.28 * open_vals[j]
        else:
            grasp_vals = close_vals
        close_cmd = {jn: float(q_start[idx]) for jn, idx in dof_idx.items()}
        close_cmd.update(_apply_ee_driver_targets(meta, side, grasp_vals))
        q_grasped = _step_to(close_cmd, 65)

        q_cur = q_grasped.copy()
        n_lift_steps = 45
        dz_per_step = 0.14 / n_lift_steps
        for _ in range(n_lift_steps):
            q_p = pin.neutral(pin_model)
            for jn, idx in dof_idx.items():
                _set_joint_q(pin_model, q_p, jn, float(q_cur[idx]))
            pin.forwardKinematics(pin_model, pin_data, q_p)
            pin.computeJointJacobians(pin_model, pin_data, q_p)
            pin.updateFramePlacements(pin_model, pin_data)
            J_full = pin.getFrameJacobian(pin_model, pin_data, gf_id, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
            J_arm = J_full[:, arm_v_cols]
            dx = np.array([0.0, 0.0, dz_per_step, 0.0, 0.0, 0.0], dtype=float)
            dq = J_arm.T @ np.linalg.solve(J_arm @ J_arm.T + 1e-3 * np.eye(6), dx)
            dq = np.clip(dq, -0.05, 0.05)
            for k, jn in enumerate(arm_jnames):
                lim = meta["joint_limits"][jn]
                q_cur[dof_idx[jn]] = float(np.clip(q_cur[dof_idx[jn]] + dq[k], lim["lower"], lim["upper"]))
            for jn, v in _apply_ee_driver_targets(meta, side, grasp_vals).items():
                if jn in dof_idx:
                    q_cur[dof_idx[jn]] = float(v)
            robot.apply_action(ArticulationAction(joint_positions=q_cur))
            world.step(render=False)

        for _ in range(60):
            robot.apply_action(ArticulationAction(joint_positions=q_cur))
            world.step(render=False)

        cyl_pos_1, _ = cyl.get_world_pose()
        q_end = np.asarray(robot.get_joint_positions(), dtype=float)
        q_p_end = pin.neutral(pin_model)
        for jn, idx in dof_idx.items():
            _set_joint_q(pin_model, q_p_end, jn, float(q_end[idx]))
        pin.forwardKinematics(pin_model, pin_data, q_p_end)
        pin.updateFramePlacements(pin_model, pin_data)
        gf_end = np.asarray(pin_data.oMf[gf_id].translation, dtype=float)

        lift_dz = float(cyl_pos_1[2]) - z0
        dist_to_gf = float(np.linalg.norm(np.asarray(cyl_pos_1, dtype=float) - gf_end))
        lift_passed = (lift_dz >= 0.08) and (dist_to_gf <= 0.14)
        l2_cylinder_lift = {
            "skipped": False,
            "passed": lift_passed,
            "side": side,
            "z0_m": round(z0, 4),
            "z1_m": round(float(cyl_pos_1[2]), 4),
            "lift_delta_z_m": round(lift_dz, 4),
            "cyl_to_grasp_frame_dist_m": round(dist_to_gf, 4),
            "threshold_lift_m": 0.08,
        }

    overall_passed = bool(
        l0_usd["passed"]
        and l1_kin["passed"]
        and l1_cross_fk["passed"]
        and l2_stability["passed"]
        and ee_closure_passed
        and l2_cylinder_lift["passed"]
    )
    report = {
        "schema": "convert-asset-robot-qualification/v1",
        "robot_id": meta["robot_id"],
        "usd_path": str(resolved_usd),
        "urdf_path": str(urdf_path),
        "passed": overall_passed,
        "l0_usd_schema": l0_usd,
        "l1_kinematics": l1_kin,
        "l1_cross_engine_fk": l1_cross_fk,
        "l2_stability": l2_stability,
        "l2_ee_closure": {"passed": ee_closure_passed, "arms": ee_closure_report},
        "l2_cylinder_lift": l2_cylinder_lift,
    }
    if write_report:
        out_path = resolved_usd.parent / "robot_qualification_report.json"
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SimReady Robot Qualification Gate (L0+L1+L2).")
    parser.add_argument("--robot-id", default="all", help="Robot ID or 'all'")
    parser.add_argument("--robots-dir", default=str(DEFAULT_ROBOTS_ARTIFACT_ROOT))
    parser.add_argument(
        "--kinematics-only",
        action="store_true",
        help="Run pure-Python L1 Pinocchio kinematics qualification without launching Isaac Sim.",
    )
    parser.add_argument("--no-lift-test", action="store_true", help="Skip L2 single-cylinder lift test.")
    args = parser.parse_args()

    root = Path(args.robots_dir)
    if args.robot_id == "all":
        robot_dirs = sorted(p.parent for p in root.glob("*/robot_assembly_meta.json"))
    else:
        robot_dirs = [root / args.robot_id]

    if not robot_dirs:
        raise SystemExit(f"No assembled robots found under {root}")

    if args.kinematics_only:
        all_ok = True
        for rdir in robot_dirs:
            rep = run_kinematic_qualification(rdir)
            status = "PASS" if rep["passed"] else "FAIL"
            print(f"[L1-KIN {status}] {rep['robot_id']} failures={rep['failures']}")
            all_ok = all_ok and rep["passed"]
        raise SystemExit(0 if all_ok else 1)

    from isaacsim import SimulationApp  # type: ignore

    app = SimulationApp({"headless": True})
    all_ok = True
    try:
        for rdir in robot_dirs:
            rep = run_sim_qualification(rdir, run_cylinder_lift=not args.no_lift_test)
            status = "PASS" if rep["passed"] else "FAIL"
            lift = rep["l2_cylinder_lift"]
            fk_err = rep["l1_cross_engine_fk"]["max_pos_err_m"]
            print(
                f"[QUAL {status}] {rep['robot_id']} | L0={rep['l0_usd_schema']['passed']} "
                f"L1_kin={rep['l1_kinematics']['passed']} L1_fk={rep['l1_cross_engine_fk']['passed']}({fk_err}m) "
                f"L2_stab={rep['l2_stability']['passed']} L2_ee={rep['l2_ee_closure']['passed']} "
                f"L2_lift={lift['passed']}(dz={lift.get('lift_delta_z_m')}m)"
            )
            all_ok = all_ok and rep["passed"]
    finally:
        app.close()
    raise SystemExit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
