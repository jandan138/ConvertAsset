"""Unified 1D C1-Hermite + Cosserat + Brazier state space, basis functions, and hollow-wall kinematics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np


# 10 scalar DOFs per 1D C1-Hermite Brazier-Cosserat node:
#   [0:3] x      (centerline position, m)
#   [3:6] t      (centerline arc-length tangent dx/ds, dimensionless ~ unit vector)
#   [6]   theta  (Cosserat material twist angle relative to Bishop frame, rad)
#   [7]   alpha0 (isotropic radial hoop expansion delta_R / R0, dimensionless)
#   [8]   alpha2 (quadrupole Brazier ovalization cos(2*phi) mode, dimensionless)
#   [9]   beta2  (quadrupole Brazier ovalization sin(2*phi) mode, dimensionless)
DOFS_PER_ROD_NODE = 10


def hermite_1d_basis(xi: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate 1D cubic Hermite basis [h00, h10, h01, h11] and 1st/2nd d/dxi derivatives on xi in [0, 1]."""
    t = np.asarray(xi, dtype=np.float64)
    t2 = t * t
    t3 = t2 * t

    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2

    dh00 = 6.0 * t2 - 6.0 * t
    dh10 = 3.0 * t2 - 4.0 * t + 1.0
    dh01 = -6.0 * t2 + 6.0 * t
    dh11 = 3.0 * t2 - 2.0 * t

    ddh00 = 12.0 * t - 6.0
    ddh10 = 6.0 * t - 4.0
    ddh01 = -12.0 * t + 6.0
    ddh11 = 6.0 * t - 2.0

    val = np.stack([h00, h10, h01, h11], axis=-1)
    d1 = np.stack([dh00, dh10, dh01, dh11], axis=-1)
    d2 = np.stack([ddh00, ddh10, ddh01, ddh11], axis=-1)
    return val, d1, d2


def gauss_legendre_01(n_quad: int = 4) -> tuple[np.ndarray, np.ndarray]:
    """Return Gauss-Legendre quadrature nodes and weights mapped to [0, 1]."""
    pts, wts = np.polynomial.legendre.leggauss(int(n_quad))
    return 0.5 * (pts + 1.0), 0.5 * wts


@dataclass(frozen=True)
class HermiteRodSpec:
    """Physical and geometric specification for a 1D hollow Brazier-Cosserat C1-Hermite tube."""

    length_m: float = 0.24
    n_elems: int = 12
    r_in_m: float = 0.0030  # 6 mm ID lab latex hose
    r_out_m: float = 0.0045  # 9 mm OD lab latex hose
    youngs_modulus_pa: float = 1.65e6
    poissons_ratio: float = 0.45
    density_kg_m3: float = 1150.0
    rayleigh_damping: float = 0.008
    enable_brazier: bool = True
    brazier_model: str = "spd_exact"  # "spd_exact" (Phase 0-4) or "kink_exact" (exact Brazier + Calladine grad + bore barrier)
    n_quad: int = 4

    @property
    def wall_thickness_m(self) -> float:
        return max(1e-5, float(self.r_out_m - self.r_in_m))

    @property
    def mean_radius_m(self) -> float:
        return 0.5 * float(self.r_out_m + self.r_in_m)

    @property
    def cross_section_area_m2(self) -> float:
        return math.pi * (self.r_out_m**2 - self.r_in_m**2)

    @property
    def second_moment_i0_m4(self) -> float:
        return 0.25 * math.pi * (self.r_out_m**4 - self.r_in_m**4)

    @property
    def polar_moment_j0_m4(self) -> float:
        return 2.0 * self.second_moment_i0_m4

    @property
    def shear_modulus_pa(self) -> float:
        return float(self.youngs_modulus_pa) / (2.0 * (1.0 + float(self.poissons_ratio)))

    @property
    def ea_n(self) -> float:
        return float(self.youngs_modulus_pa) * self.cross_section_area_m2

    @property
    def ei0_nm2(self) -> float:
        return float(self.youngs_modulus_pa) * self.second_moment_i0_m4

    @property
    def gj0_nm2(self) -> float:
        return self.shear_modulus_pa * self.polar_moment_j0_m4

    @property
    def k_hoop_n(self) -> float:
        """Isotropic radial expansion stiffness K_hoop = 2*pi*E*R0*h_w / (1 - nu^2) [N/m * m = N]."""
        nu = float(self.poissons_ratio)
        return (2.0 * math.pi * float(self.youngs_modulus_pa) * self.mean_radius_m * self.wall_thickness_m) / (1.0 - nu * nu)

    @property
    def k_oval_n(self) -> float:
        """Exact Brazier (1927) inextensional quadrupole ovalization stiffness K_oval = 3*pi*E*h_w^3 / (4*R0*(1-nu^2))."""
        nu = float(self.poissons_ratio)
        hw = self.wall_thickness_m
        r0 = self.mean_radius_m
        return (3.0 * math.pi * float(self.youngs_modulus_pa) * (hw**3)) / (4.0 * r0 * (1.0 - nu * nu))

    @property
    def brazier_critical_curvature_inv_m(self) -> float:
        """Classical Brazier (1927) critical buckling curvature kappa_crit = (sqrt(2)/3) * h_w / (R0^2 * sqrt(1 - nu^2))."""
        nu = float(self.poissons_ratio)
        return (math.sqrt(2.0) / 3.0) * self.wall_thickness_m / ((self.mean_radius_m**2) * math.sqrt(1.0 - nu * nu))

    @property
    def brazier_critical_moment_nm(self) -> float:
        """Classical Brazier (1927) peak bending moment M_crit = (2*sqrt(2)/9) * E*pi*R0*h_w^2 / sqrt(1 - nu^2)."""
        nu = float(self.poissons_ratio)
        return (2.0 * math.sqrt(2.0) / 9.0) * float(self.youngs_modulus_pa) * math.pi * self.mean_radius_m * (self.wall_thickness_m**2) / math.sqrt(1.0 - nu * nu)

    @property
    def k_grad_oval_nm2(self) -> float:
        """Calladine longitudinal shell-bending gradient coupling K_g2 = E*pi*R0*h_w^3 / (12*(1-nu^2)) [N*m^2]."""
        nu = float(self.poissons_ratio)
        return (float(self.youngs_modulus_pa) * math.pi * self.mean_radius_m * (self.wall_thickness_m**3)) / (12.0 * (1.0 - nu * nu))

    @property
    def k_grad_hoop_nm2(self) -> float:
        """Longitudinal hoop-gradient stiffness K_g0 = 2 * K_g2 [N*m^2]."""
        return 2.0 * self.k_grad_oval_nm2


@dataclass
class HermiteRodMesh:
    """Discretized 1D C1-Hermite Brazier-Cosserat rod mesh and precomputed quadrature/mass matrices."""

    spec: HermiteRodSpec
    n_nodes: int
    n_elems: int
    n_dofs: int
    ds: float
    rest_q: np.ndarray  # (n_dofs,) float64
    quad_xi: np.ndarray  # (n_quad,)
    quad_w: np.ndarray  # (n_quad,)
    h_val: np.ndarray  # (n_quad, 4)
    h_d1: np.ndarray  # (n_quad, 4)
    h_d2: np.ndarray  # (n_quad, 4)
    mass_matrix: np.ndarray  # (n_dofs, n_dofs) consistent SPD mass matrix
    ref_d1_0: np.ndarray  # (3,) initial Bishop normal at s=0
    total_mass_kg: float


def build_straight_rod_mesh(
    spec: HermiteRodSpec,
    *,
    origin_xyz: Sequence[float] = (0.0, 0.0, 0.0),
    axis_xyz: Sequence[float] = (1.0, 0.0, 0.0),
    ref_normal_xyz: Sequence[float] = (0.0, 0.0, 1.0),
) -> HermiteRodMesh:
    """Build a straight 1D C1-Hermite Brazier-Cosserat rod mesh with consistent SPD mass matrix."""
    n_elems = int(spec.n_elems)
    n_nodes = n_elems + 1
    n_dofs = n_nodes * DOFS_PER_ROD_NODE
    ds = float(spec.length_m) / float(n_elems)

    orig = np.asarray(origin_xyz, dtype=np.float64)
    ax = np.asarray(axis_xyz, dtype=np.float64)
    ax = ax / max(float(np.linalg.norm(ax)), 1e-12)
    ref_n = np.asarray(ref_normal_xyz, dtype=np.float64)
    ref_n = ref_n - np.dot(ref_n, ax) * ax
    if np.linalg.norm(ref_n) < 1e-8:
        ref_n = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        ref_n = ref_n - np.dot(ref_n, ax) * ax
    ref_n = ref_n / max(float(np.linalg.norm(ref_n)), 1e-12)

    rest_q = np.zeros(n_dofs, dtype=np.float64)
    for i in range(n_nodes):
        base = i * DOFS_PER_ROD_NODE
        rest_q[base : base + 3] = orig + (i * ds) * ax
        rest_q[base + 3 : base + 6] = ax
        # theta=0, alpha0=0, alpha2=0, beta2=0 at stress-free rest configuration

    q_xi, q_w = gauss_legendre_01(spec.n_quad)
    h_val, h_d1, h_d2 = hermite_1d_basis(q_xi)

    # Consistent SPD mass matrix integrated over each element:
    # - Translational + tangent DOFs (x, t): rho * A * int N_x^T N_x ds
    # - Twist DOF (theta): rho * J0 * int N_lin^T N_lin ds
    # - Cross-sectional radial/ovalization DOFs (alpha0, alpha2, beta2): rho * A * R0^2 * int N_lin^T N_lin ds
    rho = float(spec.density_kg_m3)
    rho_a = rho * spec.cross_section_area_m2
    rho_j = rho * spec.polar_moment_j0_m4
    rho_sec = rho_a * (spec.mean_radius_m**2)

    M = np.zeros((n_dofs, n_dofs), dtype=np.float64)
    # 4-term local Hermite shape vector for 1 coordinate: [h00, ds*h10, h01, ds*h11]
    h_scaled = np.stack([h_val[:, 0], ds * h_val[:, 1], h_val[:, 2], ds * h_val[:, 3]], axis=-1)
    m_herm = (h_scaled.T * (q_w * ds * rho_a)) @ h_scaled  # (4, 4)
    # Linear shape vector for scalar fields (theta, alpha0, alpha2, beta2): [1-xi, xi]
    lin = np.stack([1.0 - q_xi, q_xi], axis=-1)
    m_lin_base = (lin.T * (q_w * ds)) @ lin  # (2, 2)

    for e in range(n_elems):
        b0 = e * DOFS_PER_ROD_NODE
        b1 = (e + 1) * DOFS_PER_ROD_NODE
        for comp in range(3):
            idx = [b0 + comp, b0 + 3 + comp, b1 + comp, b1 + 3 + comp]
            M[np.ix_(idx, idx)] += m_herm
        # theta
        idx_th = [b0 + 6, b1 + 6]
        M[np.ix_(idx_th, idx_th)] += rho_j * m_lin_base
        # alpha0, alpha2, beta2 (note: ovalization mode cos(2phi) has 0.5 circumferential mean-square factor)
        for off, fac in ((7, 1.0), (8, 0.5), (9, 0.5)):
            idx_a = [b0 + off, b1 + off]
            M[np.ix_(idx_a, idx_a)] += (fac * rho_sec) * m_lin_base

    total_mass = rho_a * float(spec.length_m)
    return HermiteRodMesh(
        spec=spec,
        n_nodes=n_nodes,
        n_elems=n_elems,
        n_dofs=n_dofs,
        ds=ds,
        rest_q=rest_q,
        quad_xi=q_xi,
        quad_w=q_w,
        h_val=h_val,
        h_d1=h_d1,
        h_d2=h_d2,
        mass_matrix=M,
        ref_d1_0=ref_n,
        total_mass_kg=total_mass,
    )


def build_curved_rod_mesh_and_q0(
    spec: HermiteRodSpec,
    centerline_pts: np.ndarray,
    *,
    ref_normal_xyz: Sequence[float] = (0.0, 0.0, 1.0),
) -> tuple[HermiteRodMesh, np.ndarray]:
    """Build a stress-free straight-rest HermiteRodMesh plus an arc-length-resampled curved C1 initial state q0."""
    pts = np.asarray(centerline_pts, dtype=np.float64)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    total_len = float(arc[-1])
    if total_len < 1e-9:
        raise ValueError("centerline_pts must have positive arc length")
    spec_len = HermiteRodSpec(
        length_m=total_len,
        n_elems=spec.n_elems,
        r_in_m=spec.r_in_m,
        r_out_m=spec.r_out_m,
        youngs_modulus_pa=spec.youngs_modulus_pa,
        poissons_ratio=spec.poissons_ratio,
        density_kg_m3=spec.density_kg_m3,
        rayleigh_damping=spec.rayleigh_damping,
        enable_brazier=spec.enable_brazier,
        brazier_model=spec.brazier_model,
        n_quad=spec.n_quad,
    )
    n_nodes = spec_len.n_elems + 1
    s_nodes = np.linspace(0.0, total_len, n_nodes)
    x_nodes = np.column_stack([np.interp(s_nodes, arc, pts[:, c]) for c in range(3)])
    # Smooth C1 tangents via central finite differences in arc length
    t_nodes = np.zeros_like(x_nodes)
    for i in range(n_nodes):
        if i == 0:
            v = x_nodes[1] - x_nodes[0]
        elif i == n_nodes - 1:
            v = x_nodes[-1] - x_nodes[-2]
        else:
            v = x_nodes[i + 1] - x_nodes[i - 1]
        t_nodes[i] = v / max(float(np.linalg.norm(v)), 1e-12)

    mesh = build_straight_rod_mesh(spec_len, origin_xyz=x_nodes[0], axis_xyz=t_nodes[0], ref_normal_xyz=ref_normal_xyz)
    q0 = np.zeros(mesh.n_dofs, dtype=np.float64)
    for i in range(n_nodes):
        b = i * DOFS_PER_ROD_NODE
        q0[b : b + 3] = x_nodes[i]
        q0[b + 3 : b + 6] = t_nodes[i]
    return mesh, q0


def _parallel_transport(d1_prev: np.ndarray, t_prev: np.ndarray, t_curr: np.ndarray) -> np.ndarray:
    """Minimal-twist parallel transport of unit normal d1_prev from unit tangent t_prev to t_curr."""
    v = np.cross(t_prev, t_curr)
    c = float(np.dot(t_prev, t_curr))
    s2 = float(np.dot(v, v))
    if s2 < 1e-18:
        d1_new = d1_prev - np.dot(d1_prev, t_curr) * t_curr
        return d1_new / max(float(np.linalg.norm(d1_new)), 1e-12)
    # Rodrigues formula for rotation carrying t_prev -> t_curr
    k = v / math.sqrt(s2)
    ang = math.atan2(math.sqrt(s2), max(-1.0, min(1.0, c)))
    ca, sa = math.cos(ang), math.sin(ang)
    d1_rot = d1_prev * ca + np.cross(k, d1_prev) * sa + k * (np.dot(k, d1_prev) * (1.0 - ca))
    d1_rot = d1_rot - np.dot(d1_rot, t_curr) * t_curr
    return d1_rot / max(float(np.linalg.norm(d1_rot)), 1e-12)


def evaluate_brazier_tube_surface(
    mesh: HermiteRodMesh,
    q: np.ndarray,
    *,
    samples_per_elem: int = 4,
    n_phi: int = 24,
) -> dict[str, np.ndarray]:
    """Evaluate smooth C1 outer wall 3D surface, material frames, curvature, and ovalization field.

    Uses exact Brazier inextensional ring kinematics:
        p(s, phi) = x(s) + R_out * [((1 + alpha0) + alpha2*cos(2phi) + beta2*sin(2phi))*e_r
                                    + (-0.5*alpha2*sin(2phi) + 0.5*beta2*cos(2phi))*e_phi]
    """
    q_arr = np.asarray(q, dtype=np.float64).reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
    n_s = mesh.n_elems * samples_per_elem + 1
    phis = np.linspace(0.0, 2.0 * math.pi, n_phi, endpoint=False)
    c_phi, s_phi = np.cos(phis), np.sin(phis)
    c2_phi, s2_phi = np.cos(2.0 * phis), np.sin(2.0 * phis)

    centerline = np.zeros((n_s, 3), dtype=np.float64)
    tangents = np.zeros((n_s, 3), dtype=np.float64)
    curvatures = np.zeros((n_s,), dtype=np.float64)
    oval_mag = np.zeros((n_s,), dtype=np.float64)
    hoop_exp = np.zeros((n_s,), dtype=np.float64)
    vertices = np.zeros((n_s, n_phi, 3), dtype=np.float64)

    r_out = float(mesh.spec.r_out_m)
    ds = mesh.ds

    # Precompute initial tangent at s=0 (with automatic gimbal-lock safeguard for vertical rods)
    t0 = q_arr[0, 3:6]
    t_prev = t0 / max(float(np.linalg.norm(t0)), 1e-12)
    ref = mesh.ref_d1_0
    if abs(float(np.dot(ref, t_prev))) > 0.90:
        ref = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        if abs(float(np.dot(ref, t_prev))) > 0.90:
            ref = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    d1_prev = ref - np.dot(ref, t_prev) * t_prev
    d1_prev = d1_prev / max(float(np.linalg.norm(d1_prev)), 1e-12)

    idx_out = 0
    for e in range(mesh.n_elems):
        q0, q1 = q_arr[e], q_arr[e + 1]
        sub_k = samples_per_elem + (1 if e == mesh.n_elems - 1 else 0)
        xis = np.linspace(0.0, 1.0, samples_per_elem + 1)[:sub_k]
        hv, hd1, hd2 = hermite_1d_basis(xis)
        for k in range(sub_k):
            xi = float(xis[k])
            x_s = hv[k, 0] * q0[0:3] + ds * hv[k, 1] * q0[3:6] + hv[k, 2] * q1[0:3] + ds * hv[k, 3] * q1[3:6]
            dx_ds = (hd1[k, 0] / ds) * q0[0:3] + hd1[k, 1] * q0[3:6] + (hd1[k, 2] / ds) * q1[0:3] + hd1[k, 3] * q1[3:6]
            d2x_ds2 = (hd2[k, 0] / (ds * ds)) * q0[0:3] + (hd2[k, 1] / ds) * q0[3:6] + (hd2[k, 2] / (ds * ds)) * q1[0:3] + (hd2[k, 3] / ds) * q1[3:6]

            norm_t = max(float(np.linalg.norm(dx_ds)), 1e-12)
            t_hat = dx_ds / norm_t
            kappa_vec = np.cross(dx_ds, d2x_ds2) / (norm_t**3)

            d1_b = _parallel_transport(d1_prev, t_prev, t_hat)
            d2_b = np.cross(t_hat, d1_b)
            t_prev, d1_prev = t_hat, d1_b

            theta = (1.0 - xi) * q0[6] + xi * q1[6]
            a0 = (1.0 - xi) * q0[7] + xi * q1[7]
            a2 = (1.0 - xi) * q0[8] + xi * q1[8]
            b2 = (1.0 - xi) * q0[9] + xi * q1[9]

            ct, st = math.cos(theta), math.sin(theta)
            d1_m = ct * d1_b + st * d2_b
            d2_m = -st * d1_b + ct * d2_b

            # Unit radial e_r and circumferential e_phi vectors around the tube wall
            e_r = c_phi[:, None] * d1_m[None, :] + s_phi[:, None] * d2_m[None, :]
            e_phi = -s_phi[:, None] * d1_m[None, :] + c_phi[:, None] * d2_m[None, :]

            rad_scale = (1.0 + a0) + a2 * c2_phi + b2 * s2_phi
            tan_shift = -0.5 * a2 * s2_phi + 0.5 * b2 * c2_phi
            vertices[idx_out] = x_s[None, :] + r_out * (rad_scale[:, None] * e_r + tan_shift[:, None] * e_phi)

            centerline[idx_out] = x_s
            tangents[idx_out] = t_hat
            curvatures[idx_out] = float(np.linalg.norm(kappa_vec))
            oval_mag[idx_out] = math.hypot(a2, b2)
            hoop_exp[idx_out] = float(a0)
            idx_out += 1

    # Build triangle indices for watertight surface visualization
    tris: list[tuple[int, int, int]] = []
    for i in range(n_s - 1):
        for j in range(n_phi):
            jn = (j + 1) % n_phi
            v00 = i * n_phi + j
            v01 = i * n_phi + jn
            v10 = (i + 1) * n_phi + j
            v11 = (i + 1) * n_phi + jn
            tris.append((v00, v10, v11))
            tris.append((v00, v11, v01))

    return {
        "vertices": vertices.reshape(-1, 3),
        "triangles": np.asarray(tris, dtype=np.int64),
        "centerline": centerline,
        "tangents": tangents,
        "curvatures": curvatures,
        "ovalization": oval_mag,
        "hoop_expansion": hoop_exp,
    }

