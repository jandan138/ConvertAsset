"""Dense material-space gripper & tabletop contact model decoupled from coarse Hermite shell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from .bicubic_hermite_shell import HermiteShellMesh


@dataclass(frozen=True)
class RigidObstacleBox:
    """Axis-aligned rigid obstacle on tabletop (e.g., calibration book/box for draping)."""

    obstacle_id: str
    center_xyz: tuple[float, float, float]
    half_extents_xyz: tuple[float, float, float]

    def signed_distance_and_normal(self, pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        c = np.asarray(self.center_xyz, dtype=np.float64)[None, :]
        h = np.asarray(self.half_extents_xyz, dtype=np.float64)[None, :]
        rel = pts - c
        d = np.abs(rel) - h
        outside = np.maximum(d, 0.0)
        dist_out = np.linalg.norm(outside, axis=1)
        inside_max = np.max(d, axis=1)
        phi = np.where(inside_max > 0.0, dist_out, inside_max)

        normals = np.zeros_like(pts)
        # Outside gradient
        out_mask = inside_max > 0.0
        if np.any(out_mask):
            n_out = outside[out_mask] * np.sign(rel[out_mask])
            norms = np.maximum(np.linalg.norm(n_out, axis=1, keepdims=True), 1e-10)
            normals[out_mask] = n_out / norms
        # Inside closest-face normal
        in_mask = ~out_mask
        if np.any(in_mask):
            face_idx = np.argmax(d[in_mask], axis=1)
            row_idx = np.nonzero(in_mask)[0]
            for k, r in enumerate(row_idx):
                ax = int(face_idx[k])
                normals[r, ax] = 1.0 if rel[r, ax] >= 0.0 else -1.0
        return phi, normals


class MaterialSpaceContactModel:
    """HermiteTwin material-space grasp (FREE/CAPTURED/CLAMPED/RELEASED) & unilateral contact.

    Contact forces are evaluated on dense material samples (contact_nu x contact_nv) and projected
    back onto the coarse bicubic Hermite nodal DOFs via W^T (preserving total linear force).
    """

    def __init__(
        self,
        mesh: HermiteShellMesh,
        *,
        contact_nu: int = 24,
        contact_nv: int = 24,
        capture_radius_m: float = 0.020,
        clamp_stiffness_n_m: float = 3800.0,
        coulomb_friction_mu: float = 0.85,
        release_clearance_m: float = 0.012,
        thickness_m: float = 0.002,
        table_z_m: float = 0.755,
        table_stiffness_n_m: float = 6500.0,
        obstacles: Sequence[RigidObstacleBox] = (),
    ) -> None:
        self.mesh = mesh
        self.contact_nu = int(contact_nu)
        self.contact_nv = int(contact_nv)
        self.capture_radius_m = float(capture_radius_m)
        self.clamp_stiffness_n_m = float(clamp_stiffness_n_m)
        self.coulomb_friction_mu = float(coulomb_friction_mu)
        self.release_clearance_m = float(release_clearance_m)
        self.thickness_m = float(thickness_m)
        self.table_z_m = float(table_z_m)
        self.table_stiffness_n_m = float(table_stiffness_n_m)
        self.obstacles = list(obstacles)

        u = np.linspace(0.0, mesh.length_u_m, self.contact_nu)
        v = np.linspace(0.0, mesh.length_v_m, self.contact_nv)
        uu, vv = np.meshgrid(u, v, indexing="ij")
        self.sample_uv = np.column_stack([uu.ravel(), vv.ravel()])
        self.n_samples = len(self.sample_uv)
        self.W = mesh.build_sample_matrix(self.sample_uv)  # (M, n_vec_dofs)

        self.sample_states = np.zeros(self.n_samples, dtype=np.int32)
        self.local_anchor_offsets = np.zeros((self.n_samples, 3), dtype=np.float64)
        self.gripper_pos = np.zeros(3, dtype=np.float64)
        self.gripper_rot = np.eye(3, dtype=np.float64)
        self.gripper_gap_m = 0.06
        self.prev_gripper_gap_m = 0.06
        self.prev_gripper_pos = np.zeros(3, dtype=np.float64)
        self.prev_gripper_rot = np.eye(3, dtype=np.float64)
        self._W_T = self.W.T
        self._m_sample = self.mesh.total_mass_kg / max(self.n_samples, 1)

    def reset(self) -> None:
        self.sample_states.fill(0)
        self.local_anchor_offsets.fill(0.0)
        self.prev_gripper_gap_m = 0.06

    def update_gripper(
        self,
        *,
        q_cur: np.ndarray,
        gripper_pos_xyz: np.ndarray,
        gripper_rot_3x3: np.ndarray,
        gripper_gap_m: float,
    ) -> None:
        """Update FREE/CAPTURED/CLAMPED/RELEASED state machine in material space."""
        self.prev_gripper_pos = self.gripper_pos.copy()
        self.prev_gripper_rot = self.gripper_rot.copy()
        self.prev_gripper_gap_m = float(self.gripper_gap_m)
        self.gripper_pos = np.asarray(gripper_pos_xyz, dtype=np.float64).reshape(3)
        self.gripper_rot = np.asarray(gripper_rot_3x3, dtype=np.float64).reshape(3, 3)
        self.gripper_gap_m = float(gripper_gap_m)

        pts = self.W @ q_cur  # (M, 3)
        rel_local = (pts - self.gripper_pos[None, :]) @ self.gripper_rot
        r_xy = np.linalg.norm(rel_local[:, :2], axis=1)
        dz = np.abs(rel_local[:, 2])
        in_capture_zone = (r_xy <= self.capture_radius_m) & (dz <= 0.018 + 0.5 * self.thickness_m)

        clamp_threshold = self.thickness_m + 0.010
        release_threshold = self.thickness_m + self.release_clearance_m

        # Only capture/clamp during jaw closure (or if nothing clamped yet while closing) so jaws never vacuum mid-air
        has_clamped = bool(np.any(self.sample_states == 2))
        is_closing = (self.gripper_gap_m < self.prev_gripper_gap_m - 1e-4) or (not has_clamped)

        if self.gripper_gap_m <= clamp_threshold:
            if is_closing:
                newly_clamped = in_capture_zone & (self.sample_states != 2)
                if np.any(newly_clamped):
                    self.sample_states[newly_clamped] = 2
                    self.local_anchor_offsets[newly_clamped] = rel_local[newly_clamped]
        elif self.gripper_gap_m <= release_threshold:
            if is_closing:
                newly_cap = in_capture_zone & (self.sample_states == 0)
                self.sample_states[newly_cap] = 1
        else:
            was_held = (self.sample_states == 1) | (self.sample_states == 2)
            self.sample_states[was_held] = 3

    def evaluate_forces_and_stiffness(
        self,
        q_cur: np.ndarray,
        v_est: np.ndarray,
        dt_s: float,
        *,
        compute_stiffness: bool = True,
    ) -> tuple[np.ndarray, np.ndarray | None, dict[str, Any]]:
        """Evaluate sample forces & project to nodal generalized forces and SPD stiffness."""
        pts = self.W @ q_cur  # (M, 3)
        vels = self.W @ v_est  # (M, 3)
        f_sample = np.zeros((self.n_samples, 3), dtype=np.float64)
        k_sample_diag = np.zeros((self.n_samples, 3), dtype=np.float64)

        peak_grasp_normal_n = 0.0
        peak_grasp_shear_n = 0.0
        clamped_mask = self.sample_states == 2
        n_clamped = int(np.sum(clamped_mask))

        dt_safe = max(float(dt_s), 1e-4)
        c_clamp = 0.25 * self._m_sample * (self.n_samples / max(n_clamped, 1)) / dt_safe
        c_table_n = 0.25 * self._m_sample / dt_safe
        c_table_t = 0.30 * self._m_sample / dt_safe

        # 1. Gripper material-space grasp & Coulomb friction
        if n_clamped > 0:
            squeeze = max(0.0, (self.thickness_m + 0.010) - self.gripper_gap_m)
            f_normal_total = max(6.0, 2800.0 * squeeze)
            f_n_per_sample = f_normal_total / n_clamped
            peak_grasp_normal_n = float(f_normal_total)

            target_world = (
                self.gripper_pos[None, :]
                + self.local_anchor_offsets[clamped_mask] @ self.gripper_rot.T
            )
            disp = target_world - pts[clamped_mask]
            k_eff = self.clamp_stiffness_n_m / max(n_clamped, 1)
            f_raw = k_eff * disp - c_clamp * vels[clamped_mask]

            # Decompose relative to gripper jaw normal (local X axis of gripper_rot)
            jaw_n = self.gripper_rot[:, 0]
            fn_comp = np.sum(f_raw * jaw_n[None, :], axis=1, keepdims=True) * jaw_n[None, :]
            ft_comp = f_raw - fn_comp
            ft_norm = np.linalg.norm(ft_comp, axis=1, keepdims=True)

            # Enforce Coulomb friction cone ||f_t|| <= mu_c * f_n
            f_max_t = self.coulomb_friction_mu * f_n_per_sample
            scale_t = np.where(ft_norm > f_max_t, f_max_t / np.maximum(ft_norm, 1e-12), 1.0)
            f_clamped = fn_comp + scale_t * ft_comp
            f_sample[clamped_mask] += f_clamped
            peak_grasp_shear_n = float(np.sum(np.linalg.norm(scale_t * ft_comp, axis=1)))
            if self.coulomb_friction_mu > 1e-6:
                k_sample_diag[clamped_mask] += k_eff

        # 2. Unilateral tabletop plane contact (z >= table_z_m)
        pen_table = self.table_z_m - pts[:, 2]
        table_hit = pen_table > 0.0
        max_pen_mm = float(max(0.0, np.max(pen_table)) * 1000.0) if np.any(table_hit) else 0.0
        if np.any(table_hit):
            k_t = 3200.0 / max(self.n_samples ** 0.5, 1.0)
            vz = vels[table_hit, 2]
            fz = np.maximum(k_t * pen_table[table_hit] - c_table_n * np.minimum(vz, 0.0), 0.0)
            f_sample[table_hit, 2] += fz
            v_xy = vels[table_hit, :2]
            f_fric_xy = -np.clip(c_table_t * v_xy, -self.coulomb_friction_mu * fz[:, None], self.coulomb_friction_mu * fz[:, None])
            f_sample[table_hit, :2] += f_fric_xy
            k_sample_diag[table_hit, 2] += k_t

        # 3. Rigid obstacle contact (e.g., calibration book for draping)
        for obs in self.obstacles:
            phi, n_obs = obs.signed_distance_and_normal(pts)
            obs_hit = phi < 0.0015
            if np.any(obs_hit):
                pen_o = np.maximum(0.0015 - phi[obs_hit], 0.0)
                k_o = 3200.0 / max(self.n_samples ** 0.5, 1.0)
                n_h = n_obs[obs_hit]
                vn = np.sum(vels[obs_hit] * n_h, axis=1)
                fn_o = np.maximum(k_o * pen_o - c_table_n * np.minimum(vn, 0.0), 0.0)
                f_sample[obs_hit] += fn_o[:, None] * n_h
                v_t = vels[obs_hit] - vn[:, None] * n_h
                vt_norm = np.linalg.norm(v_t, axis=1, keepdims=True)
                f_t_o = -np.minimum(c_table_t * vt_norm, self.coulomb_friction_mu * fn_o[:, None]) * (
                    v_t / np.maximum(vt_norm, 1e-10)
                )
                f_sample[obs_hit] += f_t_o
                k_sample_diag[obs_hit] += k_o * (n_h * n_h)

        f_node = self._W_T @ f_sample

        if not compute_stiffness:
            return f_node, None, {
                "n_clamped_samples": n_clamped,
                "peak_grasp_normal_n": peak_grasp_normal_n,
                "peak_grasp_shear_n": peak_grasp_shear_n,
                "max_table_penetration_mm": max_pen_mm,
            }

        n_vd = self.mesh.n_vec_dofs
        K_contact = np.zeros((3 * n_vd, 3 * n_vd), dtype=np.float64)
        for c in range(3):
            kc = k_sample_diag[:, c]
            if np.any(kc > 0.0):
                K_contact[c::3, c::3] = self._W_T @ (kc[:, None] * self.W)

        return f_node, K_contact, {
            "n_clamped_samples": n_clamped,
            "peak_grasp_normal_n": peak_grasp_normal_n,
            "peak_grasp_shear_n": peak_grasp_shear_n,
            "max_table_penetration_mm": max_pen_mm,
        }

    def project_unilateral_contacts(
        self,
        q: np.ndarray,
        v: np.ndarray,
        dt_s: float,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
        """Post-step unilateral tabletop & rigid-obstacle position/velocity projection."""
        q_out = q.copy()
        v_out = v.copy()
        pos = q_out[0::4]
        vel = v_out[0::4]

        # 1. Node-level hard clamp z >= table_z_m + Coulomb xy velocity damping
        pen_n = self.table_z_m - pos[:, 2]
        hit_n = pen_n > 0.0
        if np.any(hit_n):
            pos[hit_n, 2] = self.table_z_m
            vz_old = vel[hit_n, 2].copy()
            dv_z = np.maximum(-vz_old, 0.0)
            vel[hit_n, 2] = np.maximum(vz_old, 0.0)
            vxy = vel[hit_n, :2]
            vxy_norm = np.linalg.norm(vxy, axis=1, keepdims=True)
            scale = np.maximum(
                0.0,
                1.0 - self.coulomb_friction_mu * dv_z[:, None] / np.maximum(vxy_norm, 1e-9),
            )
            vel[hit_n, :2] = vxy * np.where(vxy_norm > 1e-8, scale, 0.0)

        # 2. Node-level rigid obstacle pushout
        for obs in self.obstacles:
            phi, n_obs = obs.signed_distance_and_normal(pos)
            hit_o = phi < 0.001
            if np.any(hit_o):
                pos[hit_o] += (0.001 - phi[hit_o])[:, None] * n_obs[hit_o]
                vn = np.sum(vel[hit_o] * n_obs[hit_o], axis=1)
                inward = vn < 0.0
                if np.any(inward):
                    idx_in = np.nonzero(hit_o)[0][inward]
                    vn_in = vn[inward]
                    n_in = n_obs[idx_in]
                    vt = vel[idx_in] - vn_in[:, None] * n_in
                    vt_norm = np.linalg.norm(vt, axis=1, keepdims=True)
                    sc = np.maximum(
                        0.0,
                        1.0 - self.coulomb_friction_mu * (-vn_in[:, None]) / np.maximum(vt_norm, 1e-9),
                    )
                    vel[idx_in] = vt * np.where(vt_norm > 1e-8, sc, 0.0)

        # 3. Check dense sample penetration between nodes and gently project downward overshoot
        pts = self.W @ q_out
        pen_s = self.table_z_m - pts[:, 2]
        if np.any(pen_s > 0.0005):
            # Distribute vertical correction cleanly onto nodal z via normalized transpose weights
            corr_z = np.maximum(pen_s, 0.0)
            w_row_sum = np.maximum(np.sum(self.W[:, 0::4], axis=0), 1e-8)
            q_out[0::4, 2] += (self.W[:, 0::4].T @ corr_z) / w_row_sum
            q_out[0::4, 2] = np.maximum(q_out[0::4, 2], self.table_z_m)
            pts = self.W @ q_out

        max_pen_mm = float(max(0.0, np.max(self.table_z_m - pts[:, 2])) * 1000.0)
        return q_out, v_out, {"max_table_penetration_mm": max_pen_mm}
