"""Controlled 'Old Method' single-resolution particle/spring-mass thin-sheet baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from .material_space_grasp import RigidObstacleBox


@dataclass(frozen=True)
class SpringMassShellConfig:
    """Single-resolution spring-mass baseline config comparable in DOF budget to coarse Hermite."""

    grid_nu: int = 10
    grid_nv: int = 10
    length_u_m: float = 0.30
    length_v_m: float = 0.30
    thickness_m: float = 0.002
    area_density_kg_m2: float = 0.25
    k_stretch: float = 420.0
    k_shear: float = 280.0
    k_bend: float = 35.0
    damping: float = 3.2
    clamp_stiffness_n_m: float = 2200.0
    coulomb_friction_mu: float = 0.85
    capture_radius_m: float = 0.022
    release_clearance_m: float = 0.012
    table_z_m: float = 0.755


class SpringMassShellBaseline:
    """Single-resolution particle set modeling bending + gripper contact simultaneously (PhysTwin-like).

    Unlike HermiteTwin, a single particle grid couples coarse bending with coarse particle-gripper
    attachment and relies on 2-hop dihedral/positional bending springs rather than Kirchhoff-Love
    C1 shell bending, leading to crease blurring, stiff-foam sagging, and coarse contact drift.
    """

    def __init__(
        self,
        cfg: SpringMassShellConfig,
        *,
        origin_xyz: tuple[float, float, float] = (0.0, 0.0, 0.755),
        obstacles: Sequence[RigidObstacleBox] = (),
    ) -> None:
        self.cfg = cfg
        self.obstacles = list(obstacles)
        self.nu = int(cfg.grid_nu)
        self.nv = int(cfg.grid_nv)
        self.n_pts = self.nu * self.nv

        u = np.linspace(-0.5 * cfg.length_u_m, 0.5 * cfg.length_u_m, self.nu)
        v = np.linspace(-0.5 * cfg.length_v_m, 0.5 * cfg.length_v_m, self.nv)
        uu, vv = np.meshgrid(u, v, indexing="ij")
        ox, oy, oz = origin_xyz
        self.rest_pos = np.column_stack([ox + uu.ravel(), oy + vv.ravel(), np.full(self.n_pts, oz)])
        self.pos = self.rest_pos.copy()
        self.vel = np.zeros_like(self.pos)

        total_mass = cfg.area_density_kg_m2 * cfg.length_u_m * cfg.length_v_m
        self.mass_per_pt = total_mass / self.n_pts

        # Build spring topology: structural, shear, and 2-hop bending springs
        edges_i, edges_j, kinds = [], [], []

        def _idx(i: int, j: int) -> int:
            return i * self.nv + j

        def _add_edge(a: int, b: int, kind: int) -> None:
            edges_i.append(a)
            edges_j.append(b)
            kinds.append(kind)

        for i in range(self.nu):
            for j in range(self.nv):
                if i + 1 < self.nu:
                    _add_edge(_idx(i, j), _idx(i + 1, j), 0)
                if j + 1 < self.nv:
                    _add_edge(_idx(i, j), _idx(i, j + 1), 0)
                if i + 1 < self.nu and j + 1 < self.nv:
                    _add_edge(_idx(i, j), _idx(i + 1, j + 1), 1)
                    _add_edge(_idx(i + 1, j), _idx(i, j + 1), 1)
                if i + 2 < self.nu:
                    _add_edge(_idx(i, j), _idx(i + 2, j), 2)
                if j + 2 < self.nv:
                    _add_edge(_idx(i, j), _idx(i, j + 2), 2)

        self.edge_i = np.asarray(edges_i, dtype=np.int64)
        self.edge_j = np.asarray(edges_j, dtype=np.int64)
        self.edge_kind = np.asarray(kinds, dtype=np.int32)
        self.rest_len = np.linalg.norm(self.rest_pos[self.edge_j] - self.rest_pos[self.edge_i], axis=1)

        self.clamped = np.zeros(self.n_pts, dtype=bool)
        self.local_anchor = np.zeros((self.n_pts, 3), dtype=np.float64)
        self.prev_gap_m = 0.06

    def reset(self, *, seed_noise_m: float = 0.0, seed: int = 0) -> None:
        self.pos = self.rest_pos.copy()
        self.vel = np.zeros_like(self.pos)
        self.clamped.fill(False)
        self.local_anchor.fill(0.0)
        self.prev_gap_m = 0.06
        if seed_noise_m > 0.0:
            rng = np.random.default_rng(seed)
            self.pos[:, :2] += rng.normal(0.0, seed_noise_m, size=(self.n_pts, 2))

    def _spring_stiffness_array(self) -> np.ndarray:
        k_arr = np.empty(len(self.edge_kind), dtype=np.float64)
        k_arr[self.edge_kind == 0] = self.cfg.k_stretch
        k_arr[self.edge_kind == 1] = self.cfg.k_shear
        k_arr[self.edge_kind == 2] = self.cfg.k_bend
        return k_arr

    def step(
        self,
        dt_s: float,
        *,
        gripper_pos_xyz: np.ndarray,
        gripper_rot_3x3: np.ndarray,
        gripper_gap_m: float,
        substeps: int = 12,
        gravity_z: float = -9.81,
    ) -> dict[str, Any]:
        """Sub-stepped semi-implicit symplectic Euler spring-mass integrator with unilateral projection."""
        g_pos = np.asarray(gripper_pos_xyz, dtype=np.float64).reshape(3)
        g_rot = np.asarray(gripper_rot_3x3, dtype=np.float64).reshape(3, 3)
        gap = float(gripper_gap_m)
        prev_gap = self.prev_gap_m
        self.prev_gap_m = gap

        # Single-resolution particle-gripper capture/release (only capture on closure)
        clamp_thr = self.cfg.thickness_m + 0.010
        rel_thr = self.cfg.thickness_m + self.cfg.release_clearance_m
        is_closing = (gap < prev_gap - 1e-4) or (not np.any(self.clamped))
        if gap <= clamp_thr:
            if is_closing:
                rel_local = (self.pos - g_pos[None, :]) @ g_rot
                r_xy = np.linalg.norm(rel_local[:, :2], axis=1)
                dz = np.abs(rel_local[:, 2])
                hit = (r_xy <= self.cfg.capture_radius_m) & (dz <= 0.018 + 0.5 * self.cfg.thickness_m) & (~self.clamped)
                if np.any(hit):
                    self.clamped[hit] = True
                    self.local_anchor[hit] = rel_local[hit]
        elif gap > rel_thr:
            self.clamped.fill(False)

        k_arr = self._spring_stiffness_array()
        max_k = max(4.0 * float(np.max(k_arr)), 1.0)
        min_sub = int(np.ceil(float(dt_s) * np.sqrt(max_k / max(self.mass_per_pt, 1e-7)) * 1.2))
        eff_substeps = min(max(int(substeps), min_sub), 48)
        h_sub = float(dt_s) / float(eff_substeps)
        k_cfl_cap = 0.35 * self.mass_per_pt / (h_sub * h_sub)
        k_arr_safe = np.minimum(k_arr, 0.20 * k_cfl_cap)
        c_clamp = 0.25 * self.mass_per_pt / h_sub
        peak_fn = 0.0

        for _ in range(eff_substeps):
            forces = np.zeros_like(self.pos)
            forces[:, 2] = self.mass_per_pt * gravity_z
            forces -= self.cfg.damping * self.mass_per_pt * self.vel

            # Spring forces (mass-safe damping + CFL cap)
            d_vec = self.pos[self.edge_j] - self.pos[self.edge_i]
            cur_l = np.linalg.norm(d_vec, axis=1)
            dir_v = d_vec / np.maximum(cur_l[:, None], 1e-10)
            ext = cur_l - self.rest_len
            v_rel = np.sum((self.vel[self.edge_j] - self.vel[self.edge_i]) * dir_v, axis=1)
            f_mag = k_arr_safe * ext + 0.02 * np.sqrt(k_arr_safe * self.mass_per_pt) * v_rel
            f_e = f_mag[:, None] * dir_v
            np.add.at(forces, self.edge_i, f_e)
            np.add.at(forces, self.edge_j, -f_e)

            # Single-resolution particle gripper contact
            n_cl = int(np.sum(self.clamped))
            if n_cl > 0:
                squeeze = max(0.0, clamp_thr - gap)
                f_n_tot = max(6.0, 2800.0 * squeeze)
                peak_fn = max(peak_fn, f_n_tot)
                f_n_pt = f_n_tot / n_cl
                tgt = g_pos[None, :] + self.local_anchor[self.clamped] @ g_rot.T
                k_cl_safe = min(self.cfg.clamp_stiffness_n_m / max(n_cl, 1), 0.35 * k_cfl_cap)
                f_raw = k_cl_safe * (tgt - self.pos[self.clamped]) - c_clamp * self.vel[self.clamped]
                jaw_n = g_rot[:, 0]
                fn_c = np.sum(f_raw * jaw_n[None, :], axis=1, keepdims=True) * jaw_n[None, :]
                ft_c = f_raw - fn_c
                ft_norm = np.linalg.norm(ft_c, axis=1, keepdims=True)
                f_max = self.cfg.coulomb_friction_mu * f_n_pt
                sc = np.where(ft_norm > f_max, f_max / np.maximum(ft_norm, 1e-12), 1.0)
                forces[self.clamped] += fn_c + sc * ft_c

            self.vel += (h_sub / self.mass_per_pt) * forces
            self.pos += h_sub * self.vel

            # Exact unilateral tabletop projection + Coulomb friction impulse
            pen_t = self.cfg.table_z_m - self.pos[:, 2]
            t_hit = pen_t > 0.0
            if np.any(t_hit):
                self.pos[t_hit, 2] = self.cfg.table_z_m
                vz_old = self.vel[t_hit, 2].copy()
                dv_z = np.maximum(-vz_old, 0.0)
                self.vel[t_hit, 2] = np.maximum(vz_old, 0.0)
                vxy = self.vel[t_hit, :2]
                vxy_n = np.linalg.norm(vxy, axis=1, keepdims=True)
                sc_f = np.maximum(0.0, 1.0 - self.cfg.coulomb_friction_mu * dv_z[:, None] / np.maximum(vxy_n, 1e-9))
                self.vel[t_hit, :2] = vxy * np.where(vxy_n > 1e-8, sc_f, 0.0)

            for obs in self.obstacles:
                phi, n_obs = obs.signed_distance_and_normal(self.pos)
                o_hit = phi < 0.001
                if np.any(o_hit):
                    self.pos[o_hit] += (0.001 - phi[o_hit])[:, None] * n_obs[o_hit]
                    vn = np.sum(self.vel[o_hit] * n_obs[o_hit], axis=1)
                    inw = vn < 0.0
                    if np.any(inw):
                        idx_in = np.nonzero(o_hit)[0][inw]
                        vn_in = vn[inw]
                        n_in = n_obs[idx_in]
                        vt = self.vel[idx_in] - vn_in[:, None] * n_in
                        vt_n = np.linalg.norm(vt, axis=1, keepdims=True)
                        sc_o = np.maximum(0.0, 1.0 - self.cfg.coulomb_friction_mu * (-vn_in[:, None]) / np.maximum(vt_n, 1e-9))
                        self.vel[idx_in] = vt * np.where(vt_n > 1e-8, sc_o, 0.0)

        max_pen_mm = float(max(0.0, np.max(self.cfg.table_z_m - self.pos[:, 2])) * 1000.0)
        return {
            "finite_ok": bool(np.all(np.isfinite(self.pos)) and np.all(np.isfinite(self.vel))),
            "n_clamped_particles": int(np.sum(self.clamped)),
            "peak_grasp_normal_n": peak_fn,
            "max_table_penetration_mm": max_pen_mm,
        }

    def evaluate_grid(self, eval_nu: int = 25, eval_nv: int = 25) -> dict[str, np.ndarray]:
        """Bilinearly upsample spring-mass particle positions onto the common comparison grid."""
        p_grid = self.pos.reshape(self.nu, self.nv, 3)
        u_t = np.linspace(0.0, self.nu - 1.0, eval_nu)
        v_t = np.linspace(0.0, self.nv - 1.0, eval_nv)
        i0 = np.minimum(np.floor(u_t).astype(np.int64), self.nu - 2)
        j0 = np.minimum(np.floor(v_t).astype(np.int64), self.nv - 2)
        wu = (u_t - i0)[:, None, None]
        wv = (v_t - j0)[None, :, None]

        # Separable bilinear interpolation
        tmp = (1.0 - wu) * p_grid[i0, :, :] + wu * p_grid[i0 + 1, :, :]
        verts = (1.0 - wv) * tmp[:, j0, :] + wv * tmp[:, j0 + 1, :]

        # Finite-difference normals
        du_vec = np.gradient(verts, axis=0)
        dv_vec = np.gradient(verts, axis=1)
        nt = np.cross(du_vec, dv_vec)
        norms = np.maximum(np.linalg.norm(nt, axis=-1, keepdims=True), 1e-10)
        normals = nt / norms
        return {
            "vertices": verts,
            "normals": normals,
        }
