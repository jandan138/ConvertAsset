"""C1 Bogner-Fox-Schmit Bicubic Hermite Shell with Kirchhoff-Love mechanics (HermiteTwin v0.8).

Implements:
- Tensor-product 2D bicubic Hermite basis on structured quad grids (4 vector DOFs/node: x, xu, xv, xuv).
- Exact SO(3)-invariant Kirchhoff-Love membrane + bending strain energies and analytical nodal gradients.
- Consistent mass matrix + regularized Gauss-Newton implicit backward-Euler stepping (fast & stiff-safe).
- High-resolution smooth surface & mean-curvature evaluation for rendering and 3DGS anchoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from .contracts_v08 import HermiteShellSpec


def _hermite_1d_basis(xi: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate 1D cubic Hermite functions H = [h00, h10, h01, h11] and 1st/2nd d/dxi derivatives."""
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


def _local_bf_element_matrices(
    xi: np.ndarray,
    eta: np.ndarray,
    du: float,
    dv: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate 16 Bogner-Fox-Schmit bicubic Hermite basis functions at local points (xi, eta) in [0,1]^2.

    Element local DOF ordering (16 scalar DOFs per coordinate axis):
      node (a in {0,1}, b in {0,1}), dof k in {0:x, 1:xu, 2:xv, 3:xuv}:
      corner_idx = (2*a + b) -> local_idx = 4*corner_idx + k
      where corner order is: (0,0)=0, (0,1)=1, (1,0)=2, (1,1)=3.
    """
    h_u, dhu, ddhu = _hermite_1d_basis(xi)
    h_v, dhv, ddhv = _hermite_1d_basis(eta)

    n_pts = len(xi)
    N = np.zeros((n_pts, 16), dtype=np.float64)
    Nu = np.zeros((n_pts, 16), dtype=np.float64)
    Nv = np.zeros((n_pts, 16), dtype=np.float64)
    Nuu = np.zeros((n_pts, 16), dtype=np.float64)
    Nuv = np.zeros((n_pts, 16), dtype=np.float64)
    Nvv = np.zeros((n_pts, 16), dtype=np.float64)

    inv_du = 1.0 / du
    inv_dv = 1.0 / dv
    inv_du2 = inv_du * inv_du
    inv_dv2 = inv_dv * inv_dv
    inv_duv = inv_du * inv_dv

    for a in (0, 1):
        for b in (0, 1):
            c_idx = 2 * a + b
            # k=0: val, k=1: dx/du (*du), k=2: dx/dv (*dv), k=3: d2x/dudv (*du*dv)
            u_pairs = [(0, 1.0, 2 * a), (1, du, 2 * a + 1)]
            v_pairs = [(0, 1.0, 2 * b), (1, dv, 2 * b + 1)]
            for ku, su, iu in u_pairs:
                for kv, sv, iv in v_pairs:
                    scale = su * sv
                    col = 4 * c_idx + (ku + 2 * kv)
                    N[:, col] = scale * h_u[:, iu] * h_v[:, iv]
                    Nu[:, col] = scale * inv_du * dhu[:, iu] * h_v[:, iv]
                    Nv[:, col] = scale * inv_dv * h_u[:, iu] * dhv[:, iv]
                    Nuu[:, col] = scale * inv_du2 * ddhu[:, iu] * h_v[:, iv]
                    Nuv[:, col] = scale * inv_duv * dhu[:, iu] * dhv[:, iv]
                    Nvv[:, col] = scale * inv_dv2 * h_u[:, iu] * ddhv[:, iv]

    return N, Nu, Nv, Nuu, Nuv, Nvv


@dataclass
class HermiteShellMesh:
    """Structured quad mesh & precomputed C1 Bogner-Fox-Schmit quadrature operators."""

    nx: int
    ny: int
    length_u_m: float
    length_v_m: float
    du: float
    dv: float
    n_nodes: int
    n_vec_dofs: int  # 4 * n_nodes
    elem_dof_indices: np.ndarray  # (n_elems, 16) indices into vector DOFs [0..4*n_nodes)
    rest_q: np.ndarray  # (4*n_nodes, 3)
    quad_weights: np.ndarray  # (n_quad,) area-weighted Gauss weights
    N_q: np.ndarray  # (n_quad, 16)
    Nu_q: np.ndarray  # (n_quad, 16)
    Nv_q: np.ndarray  # (n_quad, 16)
    Nuu_q: np.ndarray  # (n_quad, 16)
    Nuv_q: np.ndarray  # (n_quad, 16)
    Nvv_q: np.ndarray  # (n_quad, 16)
    mass_matrix: np.ndarray  # (n_vec_dofs, n_vec_dofs) consistent SPD mass matrix (per axis)
    total_mass_kg: float
    w_p: np.ndarray  # (E*Q,) pre-broadcast quadrature weights
    Nu_p: np.ndarray  # (E*Q, 16)
    Nv_p: np.ndarray  # (E*Q, 16)
    Nuu_p: np.ndarray  # (E*Q, 16)
    Nuv_p: np.ndarray  # (E*Q, 16)
    Nvv_p: np.ndarray  # (E*Q, 16)
    flat_k_idx: np.ndarray  # (E*48*48,) flat scatter indices into (3*n_vec_dofs)^2

    def build_sample_matrix(self, uv_coords: np.ndarray) -> np.ndarray:
        """Build sparse-ready interpolation matrix W (M, n_vec_dofs) such that x(u,v) = W @ q."""
        uv = np.asarray(uv_coords, dtype=np.float64)
        u = np.clip(uv[:, 0], 0.0, self.length_u_m)
        v = np.clip(uv[:, 1], 0.0, self.length_v_m)
        m = len(u)
        W = np.zeros((m, self.n_vec_dofs), dtype=np.float64)

        ix = np.minimum((u / self.du).astype(np.int64), self.nx - 1)
        iy = np.minimum((v / self.dv).astype(np.int64), self.ny - 1)
        xi = np.clip((u - ix * self.du) / self.du, 0.0, 1.0)
        eta = np.clip((v - iy * self.dv) / self.dv, 0.0, 1.0)
        elem_idx = ix * self.ny + iy

        for s in range(m):
            e = int(elem_idx[s])
            N_s, _, _, _, _, _ = _local_bf_element_matrices(
                xi[s : s + 1], eta[s : s + 1], self.du, self.dv
            )
            dofs = self.elem_dof_indices[e]
            W[s, dofs] = N_s[0]
        return W


def build_hermite_shell_mesh(
    *,
    nx: int,
    ny: int,
    length_u_m: float,
    length_v_m: float,
    area_density_kg_m2: float,
    origin_xyz: tuple[float, float, float] = (0.0, 0.0, 0.755),
) -> HermiteShellMesh:
    """Build a flat resting C1 bicubic Hermite shell centered in XY at z=origin_xyz[2]."""
    du = float(length_u_m) / float(nx)
    dv = float(length_v_m) / float(ny)
    n_nodes = (nx + 1) * (ny + 1)
    n_vec_dofs = 4 * n_nodes

    rest_q = np.zeros((n_vec_dofs, 3), dtype=np.float64)
    ox, oy, oz = origin_xyz
    for i in range(nx + 1):
        for j in range(ny + 1):
            nid = i * (ny + 1) + j
            u = i * du - 0.5 * length_u_m
            v = j * dv - 0.5 * length_v_m
            base = 4 * nid
            rest_q[base + 0] = [ox + u, oy + v, oz]
            rest_q[base + 1] = [1.0, 0.0, 0.0]  # dx/du
            rest_q[base + 2] = [0.0, 1.0, 0.0]  # dx/dv
            rest_q[base + 3] = [0.0, 0.0, 0.0]  # d2x/dudv

    n_elems = nx * ny
    elem_dof_indices = np.zeros((n_elems, 16), dtype=np.int64)
    for ix in range(nx):
        for iy in range(ny):
            e = ix * ny + iy
            corners = [
                ix * (ny + 1) + iy,
                ix * (ny + 1) + (iy + 1),
                (ix + 1) * (ny + 1) + iy,
                (ix + 1) * (ny + 1) + (iy + 1),
            ]
            idx = []
            for c in corners:
                idx.extend([4 * c + 0, 4 * c + 1, 4 * c + 2, 4 * c + 3])
            elem_dof_indices[e] = np.asarray(idx, dtype=np.int64)

    # 3x3 Gauss-Legendre rule on [0, 1]^2
    gp_1d = np.array([
        0.5 * (1.0 - np.sqrt(3.0 / 5.0)),
        0.5,
        0.5 * (1.0 + np.sqrt(3.0 / 5.0)),
    ], dtype=np.float64)
    gw_1d = np.array([5.0 / 18.0, 8.0 / 18.0, 5.0 / 18.0], dtype=np.float64)
    xi_list, eta_list, w_list = [], [], []
    for a in range(3):
        for b in range(3):
            xi_list.append(gp_1d[a])
            eta_list.append(gp_1d[b])
            w_list.append(gw_1d[a] * gw_1d[b] * du * dv)
    xi_arr = np.asarray(xi_list, dtype=np.float64)
    eta_arr = np.asarray(eta_list, dtype=np.float64)
    quad_weights = np.asarray(w_list, dtype=np.float64)

    N_q, Nu_q, Nv_q, Nuu_q, Nuv_q, Nvv_q = _local_bf_element_matrices(xi_arr, eta_arr, du, dv)

    # Assemble consistent scalar mass matrix M (n_vec_dofs, n_vec_dofs)
    # Use 4x4 Gauss rule for exact integration of degree-6 polynomial mass products
    gl4_x, gl4_w = np.polynomial.legendre.leggauss(4)
    g4_p = 0.5 * (gl4_x + 1.0)
    g4_w = 0.5 * gl4_w
    xi4, eta4, w4 = [], [], []
    for a in range(4):
        for b in range(4):
            xi4.append(g4_p[a])
            eta4.append(g4_p[b])
            w4.append(g4_w[a] * g4_w[b] * du * dv)
    N_m, _, _, _, _, _ = _local_bf_element_matrices(
        np.asarray(xi4), np.asarray(eta4), du, dv
    )
    m_local = area_density_kg_m2 * (N_m.T @ (np.asarray(w4)[:, None] * N_m))
    M = np.zeros((n_vec_dofs, n_vec_dofs), dtype=np.float64)
    for e in range(n_elems):
        dofs = elem_dof_indices[e]
        M[np.ix_(dofs, dofs)] += m_local

    # Tiny rotational inertia regularization if derivative DOFs on coarse grids are near-singular
    diag_floor = 1e-6 * area_density_kg_m2 * du * dv
    M[np.arange(n_vec_dofs), np.arange(n_vec_dofs)] += diag_floor

    n_q = len(quad_weights)
    w_p = np.tile(quad_weights, n_elems)
    Nu_p = np.broadcast_to(Nu_q[None, :, :], (n_elems, n_q, 16)).reshape(n_elems * n_q, 16).copy()
    Nv_p = np.broadcast_to(Nv_q[None, :, :], (n_elems, n_q, 16)).reshape(n_elems * n_q, 16).copy()
    Nuu_p = np.broadcast_to(Nuu_q[None, :, :], (n_elems, n_q, 16)).reshape(n_elems * n_q, 16).copy()
    Nuv_p = np.broadcast_to(Nuv_q[None, :, :], (n_elems, n_q, 16)).reshape(n_elems * n_q, 16).copy()
    Nvv_p = np.broadcast_to(Nvv_q[None, :, :], (n_elems, n_q, 16)).reshape(n_elems * n_q, 16).copy()
    n_sdof = 3 * n_vec_dofs
    elem_sdofs = (3 * elem_dof_indices[:, :, None] + np.arange(3)[None, None, :]).reshape(n_elems, 48)
    flat_k_idx = (elem_sdofs[:, :, None] * n_sdof + elem_sdofs[:, None, :]).ravel()

    return HermiteShellMesh(
        nx=nx,
        ny=ny,
        length_u_m=float(length_u_m),
        length_v_m=float(length_v_m),
        du=du,
        dv=dv,
        n_nodes=n_nodes,
        n_vec_dofs=n_vec_dofs,
        elem_dof_indices=elem_dof_indices,
        rest_q=rest_q,
        quad_weights=quad_weights,
        N_q=N_q,
        Nu_q=Nu_q,
        Nv_q=Nv_q,
        Nuu_q=Nuu_q,
        Nuv_q=Nuv_q,
        Nvv_q=Nvv_q,
        mass_matrix=M,
        total_mass_kg=float(area_density_kg_m2 * length_u_m * length_v_m),
        w_p=w_p,
        Nu_p=Nu_p,
        Nv_p=Nv_p,
        Nuu_p=Nuu_p,
        Nuv_p=Nuv_p,
        Nvv_p=Nvv_p,
        flat_k_idx=flat_k_idx,
    )


def compute_shell_energy_and_grad(
    mesh: HermiteShellMesh,
    q: np.ndarray,
    *,
    membrane_rigidity: float,
    bending_rigidity: float,
    poissons_ratio: float,
    compute_stiffness: bool = True,
) -> tuple[float, np.ndarray, np.ndarray | None, dict[str, float]]:
    """Evaluate Kirchhoff-Love membrane + bending energies, exact analytical gradient, and SPD GN stiffness."""
    q_arr = np.asarray(q, dtype=np.float64)
    # q_elem: (E, 16, 3)
    q_elem = q_arr[mesh.elem_dof_indices]
    n_elems = q_elem.shape[0]
    n_q = mesh.N_q.shape[0]
    nu = float(poissons_ratio)
    cm = float(membrane_rigidity)
    cb = float(bending_rigidity)

    # Derivatives at all (E, Q, 3)
    a1 = np.einsum("qi,eic->eqc", mesh.Nu_q, q_elem)
    a2 = np.einsum("qi,eic->eqc", mesh.Nv_q, q_elem)
    xuu = np.einsum("qi,eic->eqc", mesh.Nuu_q, q_elem)
    xuv = np.einsum("qi,eic->eqc", mesh.Nuv_q, q_elem)
    xvv = np.einsum("qi,eic->eqc", mesh.Nvv_q, q_elem)

    # First fundamental form vs flat rest I_2
    a11 = np.einsum("eqc,eqc->eq", a1, a1)
    a22 = np.einsum("eqc,eqc->eq", a2, a2)
    a12 = np.einsum("eqc,eqc->eq", a1, a2)
    E11 = 0.5 * (a11 - 1.0)
    E22 = 0.5 * (a22 - 1.0)
    E12 = 0.5 * a12

    w_eq = mesh.quad_weights[None, :]  # (1, Q)
    w_mem_density = 0.5 * cm * (
        E11 * E11 + E22 * E22 + 2.0 * nu * E11 * E22 + 2.0 * (1.0 - nu) * E12 * E12
    )
    energy_mem = float(np.sum(w_eq * w_mem_density))

    # Membrane gradients wrt a1, a2
    S11 = cm * (E11 + nu * E22)
    S22 = cm * (E22 + nu * E11)
    S12 = cm * (1.0 - nu) * E12
    dWm_da1 = (S11[:, :, None] * a1 + S12[:, :, None] * a2) * w_eq[:, :, None]
    dWm_da2 = (S22[:, :, None] * a2 + S12[:, :, None] * a1) * w_eq[:, :, None]

    # Unit normal & second fundamental form
    n_tilde = np.cross(a1, a2)
    J = np.linalg.norm(n_tilde, axis=-1)
    J_safe = np.maximum(J, 1e-10)
    n_hat = n_tilde / J_safe[:, :, None]

    k11 = np.einsum("eqc,eqc->eq", xuu, n_hat)
    k22 = np.einsum("eqc,eqc->eq", xvv, n_hat)
    k12 = np.einsum("eqc,eqc->eq", xuv, n_hat)

    w_bend_density = 0.5 * cb * (
        k11 * k11 + k22 * k22 + 2.0 * nu * k11 * k22 + 2.0 * (1.0 - nu) * k12 * k12
    )
    energy_bend = float(np.sum(w_eq * w_bend_density))

    # Bending moments M
    M11 = cb * (k11 + nu * k22) * w_eq
    M22 = cb * (k22 + nu * k11) * w_eq
    M12 = cb * (1.0 - nu) * k12 * w_eq

    dWb_dxuu = M11[:, :, None] * n_hat
    dWb_dxvv = M22[:, :, None] * n_hat
    dWb_dxuv = 2.0 * M12[:, :, None] * n_hat

    # Chain rule through n_hat = n_tilde / ||n_tilde||, n_tilde = a1 x a2
    dWb_dn = M11[:, :, None] * xuu + M22[:, :, None] * xvv + 2.0 * M12[:, :, None] * xuv
    dot_nd = np.einsum("eqc,eqc->eq", n_hat, dWb_dn)
    dWb_dntilde = (dWb_dn - dot_nd[:, :, None] * n_hat) / J_safe[:, :, None]
    dWb_da1 = np.cross(a2, dWb_dntilde)
    dWb_da2 = np.cross(dWb_dntilde, a1)

    g_a1 = dWm_da1 + dWb_da1
    g_a2 = dWm_da2 + dWb_da2

    # Project element quadrature gradients back to element DOFs: (E, 16, 3)
    grad_elem = (
        np.einsum("qi,eqc->eic", mesh.Nu_q, g_a1)
        + np.einsum("qi,eqc->eic", mesh.Nv_q, g_a2)
        + np.einsum("qi,eqc->eic", mesh.Nuu_q, dWb_dxuu)
        + np.einsum("qi,eqc->eic", mesh.Nuv_q, dWb_dxuv)
        + np.einsum("qi,eqc->eic", mesh.Nvv_q, dWb_dxvv)
    )
    grad = np.zeros_like(q_arr)
    np.add.at(grad, mesh.elem_dof_indices, grad_elem)

    if not compute_stiffness:
        return energy_mem + energy_bend, grad, None, {
            "energy_membrane": energy_mem,
            "energy_bending": energy_bend,
        }

    # Assemble SPD Gauss-Newton stiffness matrix K_gn (3*n_vec_dofs, 3*n_vec_dofs) via precomputed operators
    n_sdof = 3 * mesh.n_vec_dofs
    D_voigt = np.array(
        [
            [1.0, nu, 0.0],
            [nu, 1.0, 0.0],
            [0.0, 0.0, 0.5 * (1.0 - nu)],
        ],
        dtype=np.float64,
    )
    Dm = cm * D_voigt
    Db = cb * D_voigt

    P = n_elems * n_q
    w_p = mesh.w_p
    a1_p = a1.reshape(P, 3)
    a2_p = a2.reshape(P, 3)
    n_p = n_hat.reshape(P, 3)

    Nu_p = mesh.Nu_p
    Nv_p = mesh.Nv_p
    Nuu_p = mesh.Nuu_p
    Nuv_p = mesh.Nuv_p
    Nvv_p = mesh.Nvv_p

    B_m = np.empty((P, 3, 48), dtype=np.float64)
    B_m[:, 0, :] = (Nu_p[:, :, None] * a1_p[:, None, :]).reshape(P, 48)
    B_m[:, 1, :] = (Nv_p[:, :, None] * a2_p[:, None, :]).reshape(P, 48)
    B_m[:, 2, :] = (Nu_p[:, :, None] * a2_p[:, None, :] + Nv_p[:, :, None] * a1_p[:, None, :]).reshape(P, 48)

    B_b = np.empty((P, 3, 48), dtype=np.float64)
    B_b[:, 0, :] = (Nuu_p[:, :, None] * n_p[:, None, :]).reshape(P, 48)
    B_b[:, 1, :] = (Nvv_p[:, :, None] * n_p[:, None, :]).reshape(P, 48)
    B_b[:, 2, :] = (2.0 * Nuv_p[:, :, None] * n_p[:, None, :]).reshape(P, 48)

    Dm_Bm = np.matmul(Dm[None, :, :], B_m)
    Db_Bb = np.matmul(Db[None, :, :], B_b)
    Ke_m = np.matmul(B_m.swapaxes(1, 2), Dm_Bm)
    Ke_b = np.matmul(B_b.swapaxes(1, 2), Db_Bb)
    Ke_all = ((Ke_m + Ke_b) * w_p[:, None, None]).reshape(n_elems, n_q, 48, 48).sum(axis=1)

    s11_pos = np.maximum(S11, 0.0).reshape(P) * w_p
    s22_pos = np.maximum(S22, 0.0).reshape(P) * w_p
    Ke_g_elem = (
        (
            s11_pos[:, None, None] * (Nu_p[:, :, None] * Nu_p[:, None, :])
            + s22_pos[:, None, None] * (Nv_p[:, :, None] * Nv_p[:, None, :])
        )
        .reshape(n_elems, n_q, 16, 16)
        .sum(axis=1)
    )
    for c in range(3):
        Ke_all[:, c::3, c::3] += Ke_g_elem

    K_gn = np.bincount(
        mesh.flat_k_idx, weights=Ke_all.ravel(), minlength=n_sdof * n_sdof
    ).reshape(n_sdof, n_sdof)

    return energy_mem + energy_bend, grad, K_gn, {
        "energy_membrane": energy_mem,
        "energy_bending": energy_bend,
    }


class DenseSurfaceOperator:
    """Precomputed vectorized operator evaluating C1 positions, normals & curvature in <0.1 ms."""

    def __init__(self, mesh: HermiteShellMesh, eval_nu: int = 25, eval_nv: int = 25) -> None:
        self.eval_nu = int(eval_nu)
        self.eval_nv = int(eval_nv)
        u_vals = np.linspace(0.0, mesh.length_u_m, self.eval_nu)
        v_vals = np.linspace(0.0, mesh.length_v_m, self.eval_nv)
        m = self.eval_nu * self.eval_nv
        self.W = np.zeros((m, mesh.n_vec_dofs), dtype=np.float64)
        self.Wu = np.zeros((m, mesh.n_vec_dofs), dtype=np.float64)
        self.Wv = np.zeros((m, mesh.n_vec_dofs), dtype=np.float64)
        self.Wuu = np.zeros((m, mesh.n_vec_dofs), dtype=np.float64)
        self.Wuv = np.zeros((m, mesh.n_vec_dofs), dtype=np.float64)
        self.Wvv = np.zeros((m, mesh.n_vec_dofs), dtype=np.float64)

        idx = 0
        for u in u_vals:
            ix = min(int(u / mesh.du), mesh.nx - 1)
            xi = np.array([np.clip((u - ix * mesh.du) / mesh.du, 0.0, 1.0)], dtype=np.float64)
            for v in v_vals:
                iy = min(int(v / mesh.dv), mesh.ny - 1)
                eta = np.array([np.clip((v - iy * mesh.dv) / mesh.dv, 0.0, 1.0)], dtype=np.float64)
                e = ix * mesh.ny + iy
                N, Nu, Nv, Nuu, Nuv, Nvv = _local_bf_element_matrices(xi, eta, mesh.du, mesh.dv)
                dofs = mesh.elem_dof_indices[e]
                self.W[idx, dofs] = N[0]
                self.Wu[idx, dofs] = Nu[0]
                self.Wv[idx, dofs] = Nv[0]
                self.Wuu[idx, dofs] = Nuu[0]
                self.Wuv[idx, dofs] = Nuv[0]
                self.Wvv[idx, dofs] = Nvv[0]
                idx += 1

    def evaluate(self, q: np.ndarray) -> dict[str, np.ndarray]:
        q_arr = np.asarray(q, dtype=np.float64)
        verts = (self.W @ q_arr).reshape(self.eval_nu, self.eval_nv, 3)
        a1 = self.Wu @ q_arr
        a2 = self.Wv @ q_arr
        xuu = self.Wuu @ q_arr
        xuv = self.Wuv @ q_arr
        xvv = self.Wvv @ q_arr

        nt = np.cross(a1, a2)
        j = np.maximum(np.linalg.norm(nt, axis=-1, keepdims=True), 1e-10)
        nh = nt / j

        E_g = np.sum(a1 * a1, axis=-1)
        F_g = np.sum(a1 * a2, axis=-1)
        G_g = np.sum(a2 * a2, axis=-1)
        L_b = np.sum(xuu * nh, axis=-1)
        M_b = np.sum(xuv * nh, axis=-1)
        N_b = np.sum(xvv * nh, axis=-1)
        denom = np.maximum(2.0 * (E_g * G_g - F_g * F_g), 1e-10)
        H = (E_g * N_b - 2.0 * F_g * M_b + G_g * L_b) / denom

        return {
            "vertices": verts,
            "normals": nh.reshape(self.eval_nu, self.eval_nv, 3),
            "mean_curvature": H.reshape(self.eval_nu, self.eval_nv),
        }


def evaluate_dense_surface(
    mesh: HermiteShellMesh,
    q: np.ndarray,
    eval_nu: int = 25,
    eval_nv: int = 25,
) -> dict[str, np.ndarray]:
    """Evaluate C1-smooth positions, analytical unit normals, and mean curvature on a dense grid."""
    return DenseSurfaceOperator(mesh, eval_nu=eval_nu, eval_nv=eval_nv).evaluate(q)


def build_eval_grid_faces(eval_nu: int, eval_nv: int) -> np.ndarray:
    """Build triangle indices (2*(nu-1)*(nv-1), 3) for a regular grid."""
    faces = []
    for i in range(eval_nu - 1):
        for j in range(eval_nv - 1):
            a = i * eval_nv + j
            b = (i + 1) * eval_nv + j
            c = (i + 1) * eval_nv + (j + 1)
            d = i * eval_nv + (j + 1)
            faces.append((a, b, c))
            faces.append((a, c, d))
    return np.asarray(faces, dtype=np.int32)


class HermiteShellSimulator:
    """Implicit Gauss-Newton backward-Euler simulator for C1 bicubic Hermite shells."""

    def __init__(
        self,
        spec: HermiteShellSpec,
        *,
        origin_xyz: tuple[float, float, float] = (0.0, 0.0, 0.755),
    ) -> None:
        self.spec = spec
        self.mesh = build_hermite_shell_mesh(
            nx=spec.nx,
            ny=spec.ny,
            length_u_m=spec.length_u_m,
            length_v_m=spec.length_v_m,
            area_density_kg_m2=spec.area_density_kg_m2,
            origin_xyz=origin_xyz,
        )
        self.q = self.mesh.rest_q.copy()
        self.v = np.zeros_like(self.q)

        n_vd = self.mesh.n_vec_dofs
        # Expand scalar M into 3*n_vd block matrix
        self.M3 = np.zeros((3 * n_vd, 3 * n_vd), dtype=np.float64)
        for c in range(3):
            self.M3[c::3, c::3] = self.mesh.mass_matrix
        self._area_mass_diag = np.diag(self.M3).copy()

    def reset(self, *, seed_noise_m: float = 0.0, seed: int = 0) -> None:
        self.q = self.mesh.rest_q.copy()
        self.v = np.zeros_like(self.q)
        if seed_noise_m > 0.0:
            rng = np.random.default_rng(seed)
            pos_idx = np.arange(0, self.mesh.n_vec_dofs, 4)
            self.q[pos_idx, :2] += rng.normal(0.0, seed_noise_m, size=(len(pos_idx), 2))

    def step(
        self,
        dt_s: float,
        *,
        contact_force_and_stiffness_fn: Callable[
            ..., tuple[np.ndarray, np.ndarray | None, dict[str, Any]]
        ]
        | None = None,
        post_step_projection_fn: Callable[
            [np.ndarray, np.ndarray, float], tuple[np.ndarray, np.ndarray, dict[str, Any]]
        ]
        | None = None,
        gravity_z: float = -9.81,
        max_newton_iters: int = 2,
        substeps: int = 1,
    ) -> dict[str, Any]:
        """Advance damped implicit backward-Euler step with backtracking Newton-Gauss line search."""
        dt = float(dt_s) / float(substeps)
        inv_dt = 1.0 / dt
        inv_dt2 = inv_dt * inv_dt
        alpha_m = float(self.spec.rayleigh_mass_damp)
        beta_k = float(self.spec.rayleigh_stiff_damp)
        contact_meta: dict[str, Any] = {}
        last_energies: dict[str, float] = {}
        diag_idx = np.arange(self.M3.shape[0])

        def _eval_contact(q_val: np.ndarray, v_val: np.ndarray, need_k: bool) -> tuple[np.ndarray, np.ndarray | None, dict[str, Any]]:
            if contact_force_and_stiffness_fn is None:
                z = np.zeros_like(q_val)
                return z, (np.zeros_like(self.M3) if need_k else None), {}
            try:
                return contact_force_and_stiffness_fn(q_val, v_val, dt, compute_stiffness=need_k)
            except TypeError:
                return contact_force_and_stiffness_fn(q_val, v_val, dt)

        for _sub in range(substeps):
            q_prev = self.q.copy()
            v_prev = self.v.copy()
            q_pred = q_prev + dt * v_prev

            g_vec = np.zeros_like(q_prev)
            g_vec[0::4, 2] = gravity_z
            f_grav = self.mesh.mass_matrix @ g_vec

            q_cur = q_pred.copy()
            M_eff = self.M3 * inv_dt2
            c_factor = None

            for it in range(max_newton_iters):
                need_k = (it == 0)
                _, grad_shell, K_shell_new, last_energies = compute_shell_energy_and_grad(
                    self.mesh,
                    q_cur,
                    membrane_rigidity=self.spec.membrane_rigidity,
                    bending_rigidity=self.spec.bending_rigidity,
                    poissons_ratio=self.spec.poissons_ratio,
                    compute_stiffness=need_k,
                )
                if need_k and K_shell_new is not None:
                    K_shell = K_shell_new
                    C_mat = alpha_m * self.M3 + beta_k * K_shell

                f_contact, K_c_new, contact_meta = _eval_contact(
                    q_cur, (q_cur - q_prev) * inv_dt, need_k=need_k
                )
                if need_k:
                    K_contact = K_c_new if K_c_new is not None else np.zeros_like(K_shell)
                    H_sys = M_eff + K_shell + K_contact + inv_dt * C_mat
                    H_sym = 0.5 * (H_sys + H_sys.T)
                    reg_scale = max(1e-6 * float(np.max(np.diag(H_sym))), 1e-8)
                    H_sym[diag_idx, diag_idx] += reg_scale + 1e-4 * self._area_mass_diag
                    c_factor = cho_factor(H_sym, lower=True, check_finite=False)

                dq_pred = (q_cur - q_pred).reshape(-1)
                dq_step = (q_cur - q_prev).reshape(-1)
                res_vec = (
                    M_eff @ dq_pred
                    + grad_shell.reshape(-1)
                    + inv_dt * (C_mat @ dq_step)
                    - f_grav.reshape(-1)
                    - f_contact.reshape(-1)
                )
                res_norm = float(np.linalg.norm(res_vec))
                if res_norm < 1e-4:
                    break

                delta = -cho_solve(c_factor, res_vec, check_finite=False).reshape(q_cur.shape)
                max_d = float(np.max(np.abs(delta[0::4])))
                if max_d > 0.015:
                    delta *= 0.015 / max_d

                step_scale = 1.0
                accepted = False
                res_trial_val = res_norm
                for _ls in range(3):
                    q_next = q_cur + step_scale * delta
                    if np.all(np.isfinite(q_next)):
                        _, g_trial, _, last_energies = compute_shell_energy_and_grad(
                            self.mesh,
                            q_next,
                            membrane_rigidity=self.spec.membrane_rigidity,
                            bending_rigidity=self.spec.bending_rigidity,
                            poissons_ratio=self.spec.poissons_ratio,
                            compute_stiffness=False,
                        )
                        f_ct, _, contact_meta = _eval_contact(q_next, (q_next - q_prev) * inv_dt, need_k=False)
                        res_trial = (
                            M_eff @ (q_next - q_pred).reshape(-1)
                            + g_trial.reshape(-1)
                            + inv_dt * (C_mat @ (q_next - q_prev).reshape(-1))
                            - f_grav.reshape(-1)
                            - f_ct.reshape(-1)
                        )
                        res_trial_val = float(np.linalg.norm(res_trial))
                        if res_trial_val <= res_norm * 1.05 + 1e-5:
                            q_cur = q_next
                            accepted = True
                            break
                    step_scale *= 0.5

                if not accepted:
                    q_cur = q_cur + 0.125 * delta
                    break
                if res_trial_val < 0.25 * res_norm or max_d * step_scale < 1e-3:
                    break

            v_cur = (q_cur - q_prev) * inv_dt
            if post_step_projection_fn is not None:
                q_cur, v_cur, proj_meta = post_step_projection_fn(q_cur, v_cur, dt)
                contact_meta = {**contact_meta, **proj_meta}

            self.v = v_cur
            self.q = q_cur

        return {
            "finite_ok": bool(np.all(np.isfinite(self.q)) and np.all(np.isfinite(self.v))),
            **last_energies,
            **contact_meta,
        }
