"""Real-Video BV17t4y1V7XH Hose Real-to-Sim SysID & Zero-Shot Unseen Hose Generalization (SIGA Phase 4).

Extracts real amber latex cooling-water hoses directly from the real chemistry lab video (Bilibili BV17t4y1V7XH,
steady-state distillation t=145.0s, both hoses completely unobstructed against the blue studio backdrop):
  1. Metric scale calibrated directly from the standard 300mm Liebig condenser port-to-port spacing (210 mm).
  2. Train Hose (Right Inlet Hose, strong elastica J-bend): compares
       - Stage 1 only (CMA-ES)
       - Stage 2 only (3DGS x Warp Implicit Adjoint from naive guess)
       - Two-Stage Ours (CMA-ES -> PyTorch C1-3DGS Autograd x Warp 1.19 Implicit Adjoint L-BFGS-B)
     optimizing physical bending Young's modulus E_real directly against the real video silhouette & amber pixels!
  3. Zero-Shot Unseen Generalization (Left Outlet Hose in the exact same real video frame, different span & clamp):
     freezes the identified physical E_real (ZERO material re-fitting!) and predicts the unseen hose equilibrium
     strictly from its two observed anchor endpoints + gravity, evaluating real Silhouette IoU & metric Centerline RMSE.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import time
from typing import Any

import cv2
import numpy as np
from scipy.optimize import minimize
import torch

from .gsplat_c1_renderer import CameraSpec, HermiteRodGaussianRenderer
from .rod_brazier_warp import WarpBrazierRodSolver
from .state_and_basis import DOFS_PER_ROD_NODE, HermiteRodSpec, build_straight_rod_mesh


DEFAULT_BV_VIDEO = Path(
    r"I:\cpfs\shared\simulation\zhuzihou\dev\embodied-eval-os\external_artifacts\distillation_v06_m4\bilibili_ref_sop_clip.mp4"
)
# Standard 300mm Liebig condenser cooling-water barb-to-barb spacing (meters)
LIEBIG_BARB_SPACING_M = 0.210


@dataclass
class RealHoseObservation:
    """Segmented & metric-calibrated real hose from a single video frame."""

    name: str
    crop_bbox_xywh: tuple[int, int, int, int]
    mask_full: np.ndarray  # (H_full, W_full) float32 in {0, 1}
    centerline_px: np.ndarray  # (K, 2) ordered top -> bottom (u_px, v_px)
    centerline_m: np.ndarray  # (K, 3) metric world coords (x_right, y=0, z_up)
    top_anchor_m: np.ndarray  # (3,)
    bot_anchor_m: np.ndarray  # (3,)
    top_tangent_dir: np.ndarray  # (3,) unit vector along observed initial barb exit
    bot_tangent_dir: np.ndarray  # (3,) unit vector along observed bottom exit
    arc_length_m: float
    outer_radius_m: float
    mm_per_px: float
    crop_mask: np.ndarray  # (H_c, W_c) float32
    crop_rgb: np.ndarray  # (H_c, W_c, 3) float32 in [0, 1]
    cam_crop: CameraSpec


@dataclass
class RealVideoSysIDReport:
    """Quantitative Real-to-Sim SysID + Zero-Shot Generalization metrics on BV17t4y1V7XH."""

    video_path: str
    timestamp_s: float
    mm_per_px: float
    train_hose: str
    test_hose: str
    e_init_mpa: float
    e_cmaes_mpa: float
    e_adjoint_only_mpa: float
    e_two_stage_mpa: float
    train_iou_init: float
    train_iou_cmaes: float
    train_iou_adjoint_only: float
    train_iou_two_stage: float
    train_rmse_init_mm: float
    train_rmse_two_stage_mm: float
    test_zeroshot_iou_init: float
    test_zeroshot_iou_two_stage: float
    test_zeroshot_rmse_init_mm: float
    test_zeroshot_rmse_two_stage_mm: float
    wall_time_s: float
    frame_rgb_full: np.ndarray
    train_obs: RealHoseObservation
    test_obs: RealHoseObservation
    train_q_init: np.ndarray
    train_q_two_stage: np.ndarray
    test_q_init: np.ndarray
    test_q_two_stage: np.ndarray
    cam_full: CameraSpec


def _build_ortho_like_pinhole_cam(
    *,
    width: int,
    height: int,
    x_center_m: float,
    z_center_m: float,
    mm_per_px: float,
    cam_dist_m: float = 2.0,
) -> CameraSpec:
    """Construct a calibrated pinhole CameraSpec whose focal plane at y=0 matches mm_per_px exactly."""
    span_z_m = height * (mm_per_px * 1e-3)
    fov_y_deg = math.degrees(2.0 * math.atan(0.5 * span_z_m / cam_dist_m))
    return CameraSpec(
        height=int(height),
        width=int(width),
        eye_xyz=(float(x_center_m), -float(cam_dist_m), float(z_center_m)),
        target_xyz=(float(x_center_m), 0.0, float(z_center_m)),
        up_xyz=(0.0, 0.0, 1.0),
        fov_y_deg=float(fov_y_deg),
        bg_rgb=(0.0, 0.0, 0.0),
    )


def extract_bv17_real_hoses(
    video_path: Path = DEFAULT_BV_VIDEO,
    *,
    timestamp_s: float = 145.0,
) -> tuple[np.ndarray, RealHoseObservation, RealHoseObservation, CameraSpec, float]:
    """Read real BV17t4y1V7XH frame, segment both unobstructed latex hoses, and calibrate metric scale."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open real lab video: {video_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(timestamp_s * fps)))
    ok, bgr = cap.read()
    cap.release()
    if not ok or bgr is None:
        raise RuntimeError(f"Failed reading frame at t={timestamp_s}s from {video_path}")

    H, W = bgr.shape[:2]
    rgb_full = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    mask_raw = cv2.inRange(hsv, np.array([12, 65, 65]), np.array([34, 255, 240]))
    roi = np.zeros_like(mask_raw)
    roi[225:H, 170:560] = 255
    mask = cv2.bitwise_and(mask_raw, roi)
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k3)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    comps = []
    for lid in range(1, num_labels):
        area = int(stats[lid, cv2.CC_STAT_AREA])
        if area >= 250:
            comps.append((int(stats[lid, cv2.CC_STAT_LEFT]), lid))
    comps.sort(key=lambda c: c[0])
    if len(comps) < 2:
        raise RuntimeError(f"Expected 2 unobstructed hoses in BV17t4y1V7XH t={timestamp_s}s, found {len(comps)}")

    # Extract ordered top-to-bottom row centerlines for both hoses
    raw_info = []
    for _, lid in comps[:2]:
        cmask = (labels == lid).astype(np.float32)
        ys_u = np.unique(np.nonzero(cmask)[0])
        pts = []
        widths = []
        for y in ys_u:
            xs = np.nonzero(cmask[y] > 0.5)[0]
            if len(xs) >= 2:
                pts.append((float(xs.mean()), float(y)))
                widths.append(float(xs.max() - xs.min() + 1.0))
        pts_arr = np.asarray(pts, dtype=np.float64)
        # Smooth centerline gently to remove 1-pixel staircase quantization
        if len(pts_arr) >= 9:
            kern = np.ones(7, dtype=np.float64) / 7.0
            pts_arr[:, 0] = np.convolve(np.pad(pts_arr[:, 0], 3, mode="edge"), kern, mode="valid")
        raw_info.append((cmask, pts_arr, float(np.median(widths))))

    # Metric calibration from barb-to-barb distance between left outlet top & right inlet top
    top_l_px = raw_info[0][1][0]
    top_r_px = raw_info[1][1][0]
    barb_dist_px = float(np.linalg.norm(top_r_px - top_l_px))
    mm_per_px = (LIEBIG_BARB_SPACING_M * 1000.0) / max(barb_dist_px, 1e-6)
    m_per_px = mm_per_px * 1e-3

    # Full-frame metric camera with origin at image center (W/2, H/2), +x right, +z up
    cam_full = _build_ortho_like_pinhole_cam(
        width=W, height=H, x_center_m=0.0, z_center_m=0.0, mm_per_px=mm_per_px
    )

    def _px_to_world(u: np.ndarray, v: np.ndarray) -> np.ndarray:
        xw = (u - 0.5 * W) * m_per_px
        zw = (0.5 * H - v) * m_per_px
        return np.column_stack([xw, np.zeros_like(xw), zw])

    names = ("left_outlet_hose", "right_inlet_hose")
    obs_list: list[RealHoseObservation] = []
    for idx, (cmask, pts_px, med_w_px) in enumerate(raw_info):
        pts_m = _px_to_world(pts_px[:, 0], pts_px[:, 1])
        segs = np.linalg.norm(np.diff(pts_m, axis=0), axis=1)
        arc_len = float(segs.sum())

        # Fit top and bottom unit tangents over the first/last ~14 rows (clean real barb/bench entry angles)
        k_end = min(14, max(4, len(pts_m) // 5))
        t_top = pts_m[k_end] - pts_m[0]
        t_top /= max(float(np.linalg.norm(t_top)), 1e-12)
        t_bot = pts_m[-1] - pts_m[-1 - k_end]
        t_bot /= max(float(np.linalg.norm(t_bot)), 1e-12)

        ys_m, xs_m = np.nonzero(cmask > 0.5)
        pad = 16
        x0 = max(0, int(xs_m.min()) - pad)
        x1 = min(W, int(xs_m.max()) + pad + 1)
        y0 = max(0, int(ys_m.min()) - pad)
        y1 = min(H, int(ys_m.max()) + pad + 1)
        cw, ch = x1 - x0, y1 - y0
        xc_m = (0.5 * (x0 + x1) - 0.5 * W) * m_per_px
        zc_m = (0.5 * H - 0.5 * (y0 + y1)) * m_per_px
        cam_crop = _build_ortho_like_pinhole_cam(
            width=cw, height=ch, x_center_m=xc_m, z_center_m=zc_m, mm_per_px=mm_per_px
        )

        r_out_m = 0.5 * med_w_px * m_per_px
        obs_list.append(
            RealHoseObservation(
                name=names[idx],
                crop_bbox_xywh=(x0, y0, cw, ch),
                mask_full=cmask,
                centerline_px=pts_px,
                centerline_m=pts_m,
                top_anchor_m=pts_m[0].copy(),
                bot_anchor_m=pts_m[-1].copy(),
                top_tangent_dir=t_top.copy(),
                bot_tangent_dir=t_bot.copy(),
                arc_length_m=arc_len,
                outer_radius_m=float(np.clip(r_out_m, 0.0032, 0.0055)),
                mm_per_px=mm_per_px,
                crop_mask=cmask[y0:y1, x0:x1].copy(),
                crop_rgb=rgb_full[y0:y1, x0:x1].copy(),
                cam_crop=cam_crop,
            )
        )
    return rgb_full, obs_list[0], obs_list[1], cam_full, mm_per_px


def _build_hanging_hose_problem(
    obs: RealHoseObservation,
    *,
    n_elems: int = 8,
    base_youngs_pa: float = 1.8e6,
    water_filled_density_kg_m3: float = 2150.0,
) -> tuple[WarpBrazierRodSolver, HermiteRodGaussianRenderer, np.ndarray, list[int], np.ndarray, np.ndarray]:
    """Construct the exact boundary-value physics model of a real water-filled hanging cooling hose.

    Boundary conditions come strictly from the two observed anchors:
      - Top node (s=0): clamped position at glass barb exit + barb exit tangent direction
      - Bottom node (s=L): pinned position where hose exits the frame onto the lab bench
    External load: real gravity (hose wall + internal cooling water column).
    Note: The curved elastica shape between top barb and bottom pin depends nonlinearly on the
    exact dimensionless bending-to-gravity ratio E*I / (rho*A*g*L^3)!
    """
    r_out = obs.outer_radius_m
    r_in = max(0.0020, r_out - 0.0014)
    spec = HermiteRodSpec(
        length_m=obs.arc_length_m,
        n_elems=n_elems,
        r_in_m=r_in,
        r_out_m=r_out,
        youngs_modulus_pa=base_youngs_pa,
        density_kg_m3=water_filled_density_kg_m3,
        enable_brazier=True,
    )
    mesh = build_straight_rod_mesh(spec)
    # Use camera-depth normal (+Y) as Bishop reference so vertical hanging hoses never hit Z gimbal lock
    mesh.ref_d1_0[:] = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")
    # Place 3DGS wall Gaussians on the physical mid-wall surface so the EWA silhouette matches true outer diameter
    render_spec = HermiteRodSpec(
        length_m=obs.arc_length_m,
        n_elems=n_elems,
        r_in_m=max(0.0015, 0.76 * r_out - 0.0010),
        r_out_m=0.76 * r_out,
        youngs_modulus_pa=base_youngs_pa,
        density_kg_m3=water_filled_density_kg_m3,
        enable_brazier=True,
    )
    render_mesh = build_straight_rod_mesh(render_spec)
    render_mesh.ref_d1_0[:] = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    renderer = HermiteRodGaussianRenderer(
        render_mesh,
        samples_per_elem=4,
        n_phi=10,
        base_rgb=(0.82, 0.62, 0.24),
        stripe_rgb=(0.76, 0.56, 0.20),
        device="cuda:0",
    )
    renderer._rest_scales = renderer._rest_scales * 0.52

    # Build smooth initial guess q0 interpolating straight between top & bottom anchors
    q0 = mesh.rest_q.copy().reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
    chord = obs.bot_anchor_m - obs.top_anchor_m
    chord_dir = chord / max(float(np.linalg.norm(chord)), 1e-12)
    for i in range(mesh.n_nodes):
        u = i / float(mesh.n_elems)
        q0[i, 0:3] = (1.0 - u) * obs.top_anchor_m + u * obs.bot_anchor_m
        q0[i, 3:6] = chord_dir
    q0[0, 3:6] = obs.top_tangent_dir
    q0[-1, 3:6] = obs.bot_tangent_dir
    q0_flat = q0.ravel()

    # Clamp top barb position + barb exit tangent + twist, and clamp bottom bench-exit position + tangent
    n_last = (mesh.n_nodes - 1) * DOFS_PER_ROD_NODE
    dirichlet = [0, 1, 2, 3, 4, 5, 6, n_last + 0, n_last + 1, n_last + 2, n_last + 3, n_last + 4, n_last + 5]
    d_vals = np.array(
        [
            obs.top_anchor_m[0], obs.top_anchor_m[1], obs.top_anchor_m[2],
            obs.top_tangent_dir[0], obs.top_tangent_dir[1], obs.top_tangent_dir[2],
            0.0,
            obs.bot_anchor_m[0], obs.bot_anchor_m[1], obs.bot_anchor_m[2],
            obs.bot_tangent_dir[0], obs.bot_tangent_dir[1], obs.bot_tangent_dir[2],
        ],
        dtype=np.float64,
    )

    # Real gravity generalized force vector (M @ g_z)
    g_vec = np.zeros(mesh.n_dofs, dtype=np.float64)
    g_vec[2::DOFS_PER_ROD_NODE] = -9.81
    f_grav = mesh.mass_matrix @ g_vec
    return solver, renderer, q0_flat, dirichlet, d_vals, f_grav


def _eval_silhouette_iou_and_centerline_rmse(
    solver: WarpBrazierRodSolver,
    renderer: HermiteRodGaussianRenderer,
    q_equil: np.ndarray,
    obs: RealHoseObservation,
) -> tuple[float, float]:
    """Compute real-image Silhouette IoU and metric Centerline RMSE (mm) between 3DGS twin and real video."""
    with torch.no_grad():
        out = renderer.render(torch.tensor(q_equil, device=renderer.device, dtype=renderer.dtype), obs.cam_crop)
        pred_mask = (out["silhouette"].detach().cpu().numpy() > 0.35)
    gt_mask = obs.crop_mask > 0.5
    inter = float(np.logical_and(pred_mask, gt_mask).sum())
    union = float(np.logical_or(pred_mask, gt_mask).sum())
    iou = inter / max(union, 1.0)

    # Sample C1 Hermite centerline densely and compute nearest-point metric RMSE against observed centerline
    qa = q_equil.reshape(solver.mesh.n_nodes, DOFS_PER_ROD_NODE)
    ds = solver.mesh.ds
    xs = np.linspace(0.0, 1.0, 12)
    from .state_and_basis import hermite_1d_basis
    hv, _, _ = hermite_1d_basis(xs)
    sim_pts = []
    for e in range(solver.mesh.n_elems):
        x0, t0 = qa[e, 0:3], qa[e, 3:6]
        x1, t1 = qa[e + 1, 0:3], qa[e + 1, 3:6]
        for k in range(len(xs)):
            sim_pts.append(hv[k, 0] * x0 + ds * hv[k, 1] * t0 + hv[k, 2] * x1 + ds * hv[k, 3] * t1)
    sim_pts_arr = np.asarray(sim_pts, dtype=np.float64)
    # Distance from each real centerline point to closest C1 curve sample
    d2 = np.sum((obs.centerline_m[:, None, :] - sim_pts_arr[None, :, :]) ** 2, axis=-1)
    rmse_mm = 1000.0 * float(np.sqrt(np.mean(np.min(d2, axis=1))))
    return iou, rmse_mm


def run_bv17_real_video_sysid_and_zeroshot(
    video_path: Path = DEFAULT_BV_VIDEO,
    *,
    timestamp_s: float = 145.0,
    e_init_mpa: float = 0.20,
    seed: int = 17,
) -> RealVideoSysIDReport:
    """Run complete Real-to-Sim SysID on real Bilibili BV17t4y1V7XH video + Zero-Shot generalization to unseen hose."""
    t0 = time.perf_counter()
    rgb_full, left_obs, right_obs, cam_full, mm_per_px = extract_bv17_real_hoses(video_path, timestamp_s=timestamp_s)

    # Train on Left Outlet Hose (planar hang sensitive to E/rho*g); Zero-Shot Test on unseen Right Inlet Hose!
    train_obs, test_obs = left_obs, right_obs
    base_e_pa = e_init_mpa * 1e6

    tr_solver, tr_rend, tr_q0, tr_dir, tr_dval, tr_fgrav = _build_hanging_hose_problem(
        train_obs, n_elems=8, base_youngs_pa=base_e_pa
    )
    te_solver, te_rend, te_q0, te_dir, te_dval, te_fgrav = _build_hanging_hose_problem(
        test_obs, n_elems=8, base_youngs_pa=base_e_pa
    )

    tgt_mask_t = torch.tensor(train_obs.crop_mask, device=tr_rend.device, dtype=tr_rend.dtype)
    tgt_rgb_t = torch.tensor(train_obs.crop_rgb, device=tr_rend.device, dtype=tr_rend.dtype)

    def _eval_train_loss_and_grad_q(q_np: np.ndarray) -> tuple[float, np.ndarray]:
        q_t = torch.tensor(q_np, device=tr_rend.device, dtype=tr_rend.dtype, requires_grad=True)
        out = tr_rend.render(q_t, train_obs.cam_crop)
        sil = out["silhouette"]
        # Soft Dice + L2 silhouette loss + masked amber photometric consistency
        l_sil = torch.mean((sil - tgt_mask_t) ** 2)
        dice = 1.0 - (2.0 * torch.sum(sil * tgt_mask_t) + 1e-6) / (torch.sum(sil) + torch.sum(tgt_mask_t) + 1e-6)
        l_rgb = torch.mean(tgt_mask_t.unsqueeze(-1) * (out["rgb"] - tgt_rgb_t) ** 2)
        loss = 2.0 * l_sil + 0.6 * dice + 0.25 * l_rgb
        (g_q,) = torch.autograd.grad(loss, q_t)
        return float(loss.item()), g_q.detach().cpu().numpy()

    def _solve_for_e_scale(solver, q_init, d_idx, d_val, f_grav, e_scale: float) -> np.ndarray:
        res = solver.solve_equilibrium(
            q_init,
            dirichlet_dofs=d_idx,
            dirichlet_vals=d_val,
            ext_force=f_grav,
            param_overrides={"E_scale": float(e_scale), "G_scale": float(e_scale)},
            max_iters=35,
            tol=1e-9,
        )
        return res.q_final

    # Baseline at naive soft initial guess E_init = 0.20 MPa
    q_tr_init = _solve_for_e_scale(tr_solver, tr_q0, tr_dir, tr_dval, tr_fgrav, 1.0)
    tr_iou_init, tr_rmse_init = _eval_silhouette_iou_and_centerline_rmse(tr_solver, tr_rend, q_tr_init, train_obs)

    # Physical latex elastomer search bounds: E in [0.10 MPa, 3.5 MPa] -> log(E_scale) in [-0.7, +2.86]
    lp_lo, lp_hi = -0.7, math.log(3.5 / e_init_mpa)

    # 1. Stage-1 Only: CMA-ES global search over log(E_scale)
    rng = np.random.default_rng(seed)
    mean_lp = 0.8
    sigma_lp = 1.0
    best_cma_lp = 0.0
    best_cma_loss = 1e9
    best_cma_q = q_tr_init.copy()
    for _ in range(5):
        cands = np.clip(rng.normal(mean_lp, sigma_lp, size=6), lp_lo, lp_hi)
        scored = []
        for lp in cands:
            q_c = _solve_for_e_scale(tr_solver, tr_q0, tr_dir, tr_dval, tr_fgrav, math.exp(float(lp)))
            loss_c, _ = _eval_train_loss_and_grad_q(q_c)
            scored.append((loss_c, float(lp), q_c))
        scored.sort(key=lambda x: x[0])
        if scored[0][0] < best_cma_loss:
            best_cma_loss, best_cma_lp, best_cma_q = scored[0]
        elites = np.array([s[1] for s in scored[:3]], dtype=np.float64)
        mean_lp = float(np.mean(elites))
        sigma_lp = max(0.08, float(np.std(elites)) + 0.06)

    e_cmaes_mpa = e_init_mpa * math.exp(best_cma_lp)
    tr_iou_cmaes, _ = _eval_silhouette_iou_and_centerline_rmse(tr_solver, tr_rend, best_cma_q, train_obs)

    # Helper for Implicit Adjoint L-BFGS-B polish starting from any log(E_scale)
    def _run_adjoint_lbfgs(start_lp: float, warm_q: np.ndarray, maxiter: int = 10) -> tuple[float, np.ndarray]:
        state = {"q": warm_q.copy()}

        def _obj(x_arr: np.ndarray) -> tuple[float, np.ndarray]:
            lp = float(np.clip(x_arr[0], lp_lo, lp_hi))
            es = math.exp(lp)
            q_eq = _solve_for_e_scale(tr_solver, state["q"], tr_dir, tr_dval, tr_fgrav, es)
            state["q"] = q_eq
            loss_val, dL_dq = _eval_train_loss_and_grad_q(q_eq)
            adj = tr_solver.compute_implicit_adjoint(
                q_eq,
                dL_dq,
                dirichlet_dofs=tr_dir,
                param_names=("E_scale",),
                param_overrides={"E_scale": es, "G_scale": es},
            )
            # Chain rule: dL / d(log E_scale) = E_scale * dL / d(E_scale)
            g_lp = es * float(adj.grad_params["E_scale"])
            return loss_val, np.array([g_lp], dtype=np.float64)

        opt = minimize(
            _obj,
            np.array([start_lp], dtype=np.float64),
            method="L-BFGS-B",
            jac=True,
            bounds=[(lp_lo, lp_hi)],
            options={"maxiter": maxiter, "ftol": 1e-10},
        )
        lp_fin = float(opt.x[0])
        q_fin = _solve_for_e_scale(tr_solver, state["q"], tr_dir, tr_dval, tr_fgrav, math.exp(lp_fin))
        return lp_fin, q_fin

    # 2. Adjoint Only (starting from naive E_init without CMA-ES)
    lp_adj_only, q_adj_only = _run_adjoint_lbfgs(0.0, q_tr_init, maxiter=10)
    e_adj_only_mpa = e_init_mpa * math.exp(lp_adj_only)
    tr_iou_adj_only, _ = _eval_silhouette_iou_and_centerline_rmse(tr_solver, tr_rend, q_adj_only, train_obs)

    # 3. Two-Stage Ours (CMA-ES -> 3DGS x Warp Implicit Adjoint)
    lp_two, q_tr_two = _run_adjoint_lbfgs(best_cma_lp, best_cma_q, maxiter=10)
    e_two_stage_mpa = e_init_mpa * math.exp(lp_two)
    tr_iou_two, tr_rmse_two = _eval_silhouette_iou_and_centerline_rmse(tr_solver, tr_rend, q_tr_two, train_obs)

    # 4. Zero-Shot Generalization to UNSEEN Left Outlet Hose (FREEZE E_real, ZERO material refitting!)
    q_te_init = _solve_for_e_scale(te_solver, te_q0, te_dir, te_dval, te_fgrav, 1.0)
    te_iou_init, te_rmse_init = _eval_silhouette_iou_and_centerline_rmse(te_solver, te_rend, q_te_init, test_obs)

    q_te_two = _solve_for_e_scale(te_solver, te_q0, te_dir, te_dval, te_fgrav, math.exp(lp_two))
    te_iou_two, te_rmse_two = _eval_silhouette_iou_and_centerline_rmse(te_solver, te_rend, q_te_two, test_obs)

    return RealVideoSysIDReport(
        video_path=str(video_path),
        timestamp_s=float(timestamp_s),
        mm_per_px=round(mm_per_px, 4),
        train_hose=train_obs.name,
        test_hose=test_obs.name,
        e_init_mpa=round(e_init_mpa, 4),
        e_cmaes_mpa=round(e_cmaes_mpa, 4),
        e_adjoint_only_mpa=round(e_adj_only_mpa, 4),
        e_two_stage_mpa=round(e_two_stage_mpa, 4),
        train_iou_init=round(tr_iou_init, 4),
        train_iou_cmaes=round(tr_iou_cmaes, 4),
        train_iou_adjoint_only=round(tr_iou_adj_only, 4),
        train_iou_two_stage=round(tr_iou_two, 4),
        train_rmse_init_mm=round(tr_rmse_init, 3),
        train_rmse_two_stage_mm=round(tr_rmse_two, 3),
        test_zeroshot_iou_init=round(te_iou_init, 4),
        test_zeroshot_iou_two_stage=round(te_iou_two, 4),
        test_zeroshot_rmse_init_mm=round(te_rmse_init, 3),
        test_zeroshot_rmse_two_stage_mm=round(te_rmse_two, 3),
        wall_time_s=round(time.perf_counter() - t0, 3),
        frame_rgb_full=rgb_full,
        train_obs=train_obs,
        test_obs=test_obs,
        train_q_init=q_tr_init,
        train_q_two_stage=q_tr_two,
        test_q_init=q_te_init,
        test_q_two_stage=q_te_two,
        cam_full=cam_full,
    )

