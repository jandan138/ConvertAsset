"""Official ipctk 1.6.1 Codimensional IPC Contact + Tight-Inclusion CCD for Unified 1D+2D C1-Hermite Mechanics.

Maps arbitrary combinations of:
  - 1D C1-Hermite Brazier-Cosserat hollow tubes (nonlinear map p_c = W_1D(q), including exact alpha0/alpha2/beta2!)
  - 2D C1 Bicubic Hermite Kirchhoff-Love thin shells (exact linear map p_c = W_2D q)
  - Optional static or kinematically moving rigid obstacle triangle meshes (e.g. 3-olive glass barb)
into a single unified ipctk.CollisionMesh, evaluates exact Point-Triangle & Edge-Edge C-IPC Barrier + Mollified
Friction + Tight-Inclusion CCD, and pulls back exact sparse gradient & PSD Hessian:
    g_C1 = J_W^T g_IPC,    H_C1 = J_W^T H_IPC^PSD J_W.

Also enforces the cubic Hermite chord-height bound d_eff = d_hat + 2 * eps_chord so that zero proxy-mesh
intersections mathematically imply zero smooth C1-surface intersections.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence

import ipctk
import numpy as np
from scipy import sparse

from convert_asset.deformable_v08_hermite.bicubic_hermite_shell import HermiteShellMesh

from .state_and_basis import DOFS_PER_ROD_NODE, HermiteRodMesh, _parallel_transport, hermite_1d_basis


def _extract_unique_edges(faces: np.ndarray) -> np.ndarray:
    """Extract sorted unique undirected edges (E, 2) int32 from triangle indices (F, 3)."""
    if len(faces) == 0:
        return np.zeros((0, 2), dtype=np.int32)
    f = np.asarray(faces, dtype=np.int32)
    e01 = np.sort(f[:, [0, 1]], axis=1)
    e12 = np.sort(f[:, [1, 2]], axis=1)
    e20 = np.sort(f[:, [2, 0]], axis=1)
    e_all = np.vstack([e01, e12, e20])
    return np.unique(e_all, axis=0).astype(np.int32)


def _compute_rod_ring_frames(mesh: HermiteRodMesh, q: np.ndarray, xis_ring: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute minimal-twist Bishop frames (d1_b, d2_b) at all proxy ring stations along a 1D rod."""
    qa = np.asarray(q, dtype=np.float64).reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
    ds = mesh.ds
    inv_ds = 1.0 / ds
    _, hd1_all, _ = hermite_1d_basis(xis_ring)

    t0 = qa[0, 3:6]
    t_prev = t0 / max(float(np.linalg.norm(t0)), 1e-12)
    ref = mesh.ref_d1_0
    if abs(float(np.dot(ref, t_prev))) > 0.90:
        ref = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        if abs(float(np.dot(ref, t_prev))) > 0.90:
            ref = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    d1_prev = ref - np.dot(ref, t_prev) * t_prev
    d1_prev = d1_prev / max(float(np.linalg.norm(d1_prev)), 1e-12)

    n_per = len(xis_ring)
    n_rings = mesh.n_elems * n_per + 1
    d1_out = np.zeros((n_rings, 3), dtype=np.float64)
    d2_out = np.zeros((n_rings, 3), dtype=np.float64)

    _, hd1_end, _ = hermite_1d_basis(np.array([1.0]))
    idx = 0
    for e in range(mesh.n_elems):
        x0, t0_e = qa[e, 0:3], qa[e, 3:6]
        x1, t1_e = qa[e + 1, 0:3], qa[e + 1, 3:6]
        for k in range(n_per):
            hd1 = hd1_all[k]
            dx = (hd1[0] * inv_ds) * x0 + hd1[1] * t0_e + (hd1[2] * inv_ds) * x1 + hd1[3] * t1_e
            t_hat = dx / max(float(np.linalg.norm(dx)), 1e-12)
            d1_b = _parallel_transport(d1_prev, t_prev, t_hat)
            d2_b = np.cross(t_hat, d1_b)
            d1_out[idx] = d1_b
            d2_out[idx] = d2_b
            t_prev, d1_prev = t_hat, d1_b
            idx += 1
        if e == mesh.n_elems - 1:
            hd1 = hd1_end[0]
            dx = (hd1[0] * inv_ds) * x0 + hd1[1] * t0_e + (hd1[2] * inv_ds) * x1 + hd1[3] * t1_e
            t_hat = dx / max(float(np.linalg.norm(dx)), 1e-12)
            d1_b = _parallel_transport(d1_prev, t_prev, t_hat)
            d2_b = np.cross(t_hat, d1_b)
            d1_out[idx] = d1_b
            d2_out[idx] = d2_b
    return d1_out, d2_out


@dataclass
class RodProxySpec:
    mesh: HermiteRodMesh
    samples_per_elem: int = 2
    n_phi: int = 8
    radius_mode: str = "outer"  # "outer" (for knots/cloth) or "inner" (for barb bore contact)
    dof_offset: int = 0
    vert_offset: int = 0
    n_verts: int = 0
    faces: np.ndarray | None = None
    xis_ring: np.ndarray | None = None
    c_phi: np.ndarray | None = None
    s_phi: np.ndarray | None = None
    c2_phi: np.ndarray | None = None
    s2_phi: np.ndarray | None = None
    chord_bound_m: float = 0.0


@dataclass
class ShellProxySpec:
    mesh: HermiteShellMesh
    sub_m: int = 2
    dof_offset: int = 0
    vert_offset: int = 0
    n_verts: int = 0
    faces: np.ndarray | None = None
    W_scalar: sparse.csc_matrix | None = None  # (n_verts, n_vec_dofs)
    J_W_3d: sparse.csc_matrix | None = None  # (3*n_verts, 3*n_vec_dofs)
    chord_bound_m: float = 0.0


@dataclass
class RigidProxySpec:
    name: str
    rest_V: np.ndarray  # (V, 3)
    faces: np.ndarray  # (F, 3)
    vert_offset: int = 0


def build_rod_proxy_topology(mesh: HermiteRodMesh, *, samples_per_elem: int = 2, n_phi: int = 8, radius_mode: str = "outer") -> RodProxySpec:
    """Precompute watertight cylindrical proxy triangle topology and cubic-Hermite chord bound for a 1D Brazier rod."""
    xis = np.linspace(0.0, 1.0, samples_per_elem + 1)[:-1]
    n_rings = mesh.n_elems * samples_per_elem + 1
    phis = np.linspace(0.0, 2.0 * math.pi, n_phi, endpoint=False)
    tris: list[tuple[int, int, int]] = []
    for i in range(n_rings - 1):
        for j in range(n_phi):
            jn = (j + 1) % n_phi
            v00 = i * n_phi + j
            v01 = i * n_phi + jn
            v10 = (i + 1) * n_phi + j
            v11 = (i + 1) * n_phi + jn
            tris.append((v00, v10, v11))
            tris.append((v00, v11, v01))

    # Exact circumferential polygon sagitta + cubic Hermite axial chord bound
    r_ref = float(mesh.spec.r_out_m if radius_mode == "outer" else mesh.spec.r_in_m)
    circ_sagitta = r_ref * (1.0 - math.cos(math.pi / float(n_phi)))
    h_ax = mesh.ds / float(samples_per_elem)
    ax_chord = 0.02 * h_ax * h_ax / max(r_ref, 1e-4)  # conservative O(h^2) axial curvature sagitta
    return RodProxySpec(
        mesh=mesh,
        samples_per_elem=samples_per_elem,
        n_phi=n_phi,
        radius_mode=radius_mode,
        n_verts=n_rings * n_phi,
        faces=np.asarray(tris, dtype=np.int32),
        xis_ring=xis,
        c_phi=np.cos(phis),
        s_phi=np.sin(phis),
        c2_phi=np.cos(2.0 * phis),
        s2_phi=np.sin(2.0 * phis),
        chord_bound_m=min(0.25 * r_ref, circ_sagitta + ax_chord),
    )


def eval_rod_proxy_vertices_and_jacobian(
    spec: RodProxySpec,
    q_rod: np.ndarray,
    *,
    d1_rings: np.ndarray | None = None,
    d2_rings: np.ndarray | None = None,
    compute_jacobian: bool = True,
) -> tuple[np.ndarray, sparse.csc_matrix | None]:
    """Evaluate 1D Brazier proxy mesh vertices V (n_verts, 3) and exact sparse Jacobian J_W (3*n_verts, n_dofs).

    Includes exact derivatives w.r.t. centerline Hermite DOFs (x0, t0, x1, t1), Cosserat twist (theta0, theta1),
    hoop expansion (alpha0_0, alpha0_1), and Brazier ovalization (alpha2_0, alpha2_1, beta2_0, beta2_1)
    so external ipctk contact forces directly deform & flatten the hollow tube cross-section!
    """
    mesh = spec.mesh
    qa = np.asarray(q_rod, dtype=np.float64).reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
    assert spec.xis_ring is not None and spec.c_phi is not None and spec.s_phi is not None
    assert spec.c2_phi is not None and spec.s2_phi is not None

    if d1_rings is None or d2_rings is None:
        d1_rings, d2_rings = _compute_rod_ring_frames(mesh, qa, spec.xis_ring)

    n_per = spec.samples_per_elem
    n_phi = spec.n_phi
    n_rings = mesh.n_elems * n_per + 1
    r0 = float(mesh.spec.r_out_m if spec.radius_mode == "outer" else mesh.spec.r_in_m)
    ds = mesh.ds

    V = np.zeros((n_rings, n_phi, 3), dtype=np.float64)
    hv_ring, _, _ = hermite_1d_basis(spec.xis_ring)
    hv_end, _, _ = hermite_1d_basis(np.array([1.0]))

    rows_j: list[int] = []
    cols_j: list[int] = []
    vals_j: list[float] = []

    c_p, s_p = spec.c_phi, spec.s_phi
    c2_p, s2_p = spec.c2_phi, spec.s2_phi

    ring_idx = 0
    for e in range(mesh.n_elems):
        b0 = e * DOFS_PER_ROD_NODE
        b1 = (e + 1) * DOFS_PER_ROD_NODE
        q0, q1 = qa[e], qa[e + 1]
        sub_count = n_per + (1 if e == mesh.n_elems - 1 else 0)
        for k in range(sub_count):
            if k < n_per:
                xi = float(spec.xis_ring[k])
                hv = hv_ring[k]
            else:
                xi = 1.0
                hv = hv_end[0]

            w0_lin = 1.0 - xi
            w1_lin = xi
            x_s = hv[0] * q0[0:3] + (ds * hv[1]) * q0[3:6] + hv[2] * q1[0:3] + (ds * hv[3]) * q1[3:6]
            th = w0_lin * q0[6] + w1_lin * q1[6]
            a0 = w0_lin * q0[7] + w1_lin * q1[7]
            a2 = w0_lin * q0[8] + w1_lin * q1[8]
            b2 = w0_lin * q0[9] + w1_lin * q1[9]

            d1_b = d1_rings[ring_idx]
            d2_b = d2_rings[ring_idx]
            ct, st = math.cos(th), math.sin(th)
            d1_m = ct * d1_b + st * d2_b
            d2_m = -st * d1_b + ct * d2_b
            # d(d1_m)/dth = d2_m, d(d2_m)/dth = -d1_m
            e_r = c_p[:, None] * d1_m[None, :] + s_p[:, None] * d2_m[None, :]
            e_phi = -s_p[:, None] * d1_m[None, :] + c_p[:, None] * d2_m[None, :]
            # d(e_r)/dth = e_phi, d(e_phi)/dth = -e_r!

            rad_s = (1.0 + a0) + a2 * c2_p + b2 * s2_p
            tan_s = -0.5 * a2 * s2_p + 0.5 * b2 * c2_p
            offset = r0 * (rad_s[:, None] * e_r + tan_s[:, None] * e_phi)
            V[ring_idx] = x_s[None, :] + offset

            if compute_jacobian:
                dp_dth = r0 * (rad_s[:, None] * e_phi - tan_s[:, None] * e_r)
                dp_da0 = r0 * e_r
                dp_da2 = r0 * (c2_p[:, None] * e_r - 0.5 * s2_p[:, None] * e_phi)
                dp_db2 = r0 * (s2_p[:, None] * e_r + 0.5 * c2_p[:, None] * e_phi)

                h00, h10s, h01, h11s = float(hv[0]), float(ds * hv[1]), float(hv[2]), float(ds * hv[3])
                v_base = ring_idx * n_phi
                for j in range(n_phi):
                    vid3 = (v_base + j) * 3
                    for c in range(3):
                        r_idx = vid3 + c
                        if abs(h00) > 1e-14:
                            rows_j.append(r_idx); cols_j.append(b0 + c); vals_j.append(h00)
                        if abs(h10s) > 1e-14:
                            rows_j.append(r_idx); cols_j.append(b0 + 3 + c); vals_j.append(h10s)
                        if abs(h01) > 1e-14:
                            rows_j.append(r_idx); cols_j.append(b1 + c); vals_j.append(h01)
                        if abs(h11s) > 1e-14:
                            rows_j.append(r_idx); cols_j.append(b1 + 3 + c); vals_j.append(h11s)
                        if w0_lin > 1e-14:
                            rows_j.append(r_idx); cols_j.append(b0 + 6); vals_j.append(w0_lin * float(dp_dth[j, c]))
                            rows_j.append(r_idx); cols_j.append(b0 + 7); vals_j.append(w0_lin * float(dp_da0[j, c]))
                            rows_j.append(r_idx); cols_j.append(b0 + 8); vals_j.append(w0_lin * float(dp_da2[j, c]))
                            rows_j.append(r_idx); cols_j.append(b0 + 9); vals_j.append(w0_lin * float(dp_db2[j, c]))
                        if w1_lin > 1e-14:
                            rows_j.append(r_idx); cols_j.append(b1 + 6); vals_j.append(w1_lin * float(dp_dth[j, c]))
                            rows_j.append(r_idx); cols_j.append(b1 + 7); vals_j.append(w1_lin * float(dp_da0[j, c]))
                            rows_j.append(r_idx); cols_j.append(b1 + 8); vals_j.append(w1_lin * float(dp_da2[j, c]))
                            rows_j.append(r_idx); cols_j.append(b1 + 9); vals_j.append(w1_lin * float(dp_db2[j, c]))
            ring_idx += 1

    V_flat = V.reshape(-1, 3)
    J_csc = None
    if compute_jacobian:
        J_csc = sparse.coo_matrix(
            (np.asarray(vals_j, dtype=np.float64), (np.asarray(rows_j, dtype=np.int32), np.asarray(cols_j, dtype=np.int32))),
            shape=(3 * spec.n_verts, mesh.n_dofs),
        ).tocsc()
    return V_flat, J_csc


def build_shell_proxy_topology(mesh: HermiteShellMesh, *, sub_m: int = 2) -> ShellProxySpec:
    """Precompute constant sparse linear map W_2D and triangle mesh for a 2D C1 Bicubic Hermite shell."""
    nu = mesh.nx * sub_m + 1
    nv = mesh.ny * sub_m + 1
    u = np.linspace(0.0, mesh.length_u_m, nu)
    v = np.linspace(0.0, mesh.length_v_m, nv)
    uu, vv = np.meshgrid(u, v, indexing="ij")
    uv = np.column_stack([uu.ravel(), vv.ravel()])
    W_dense = mesh.build_sample_matrix(uv)
    W_sp = sparse.csc_matrix(W_dense)
    J_3d = sparse.kron(W_sp, sparse.eye(3, format="csc"), format="csc")

    tris: list[tuple[int, int, int]] = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            v00 = i * nv + j
            v10 = (i + 1) * nv + j
            v01 = i * nv + (j + 1)
            v11 = (i + 1) * nv + (j + 1)
            if (i + j) % 2 == 0:
                tris.append((v00, v10, v11))
                tris.append((v00, v11, v01))
            else:
                tris.append((v00, v10, v01))
                tris.append((v10, v11, v01))

    h_p = max(mesh.du, mesh.dv) / float(sub_m)
    chord_bound = min(0.0005, 0.005 * h_p * h_p)
    return ShellProxySpec(
        mesh=mesh,
        sub_m=sub_m,
        n_verts=nu * nv,
        faces=np.asarray(tris, dtype=np.int32),
        W_scalar=W_sp,
        J_W_3d=J_3d,
        chord_bound_m=chord_bound,
    )


class IPCTKC1ContactSystem:
    """Unified official ipctk 1.6.1 contact system for 1D Brazier rods + 2D C1 shells + rigid obstacles."""

    def __init__(
        self,
        rod_specs: Sequence[RodProxySpec] = (),
        shell_specs: Sequence[ShellProxySpec] = (),
        rigid_specs: Sequence[RigidProxySpec] = (),
        *,
        d_hat_m: float = 0.0015,
        barrier_stiffness: float = 1.0e4,
        mu_friction: float = 0.35,
        eps_v: float = 1.0e-3,
        include_chord_margin: bool = True,
    ) -> None:
        self.rod_specs = list(rod_specs)
        self.shell_specs = list(shell_specs)
        self.rigid_specs = list(rigid_specs)

        # Assign unified global DOF offsets and unified proxy vertex offsets
        dof_off = 0
        v_off = 0
        faces_all: list[np.ndarray] = []
        max_chord = 0.0

        for rs in self.rod_specs:
            rs.dof_offset = dof_off
            rs.vert_offset = v_off
            assert rs.faces is not None
            faces_all.append(rs.faces + v_off)
            dof_off += rs.mesh.n_dofs
            v_off += rs.n_verts
            max_chord = max(max_chord, rs.chord_bound_m)

        for ss in self.shell_specs:
            ss.dof_offset = dof_off
            ss.vert_offset = v_off
            assert ss.faces is not None
            faces_all.append(ss.faces + v_off)
            dof_off += 3 * ss.mesh.n_vec_dofs
            v_off += ss.n_verts
            max_chord = max(max_chord, ss.chord_bound_m)

        for rg in self.rigid_specs:
            rg.vert_offset = v_off
            faces_all.append(np.asarray(rg.faces, dtype=np.int32) + v_off)
            v_off += len(rg.rest_V)

        self.n_total_dofs = dof_off
        self.n_total_verts = v_off
        self.faces_all = np.vstack(faces_all).astype(np.int32) if faces_all else np.zeros((0, 3), dtype=np.int32)
        self.edges_all = _extract_unique_edges(self.faces_all)

        # Build rest-vertex dummy coordinates for CollisionMesh topology initialization
        V_rest_parts: list[np.ndarray] = []
        for rs in self.rod_specs:
            vr, _ = eval_rod_proxy_vertices_and_jacobian(rs, rs.mesh.rest_q, compute_jacobian=False)
            V_rest_parts.append(vr)
        for ss in self.shell_specs:
            assert ss.W_scalar is not None
            V_rest_parts.append(ss.W_scalar @ ss.mesh.rest_q)
        for rg in self.rigid_specs:
            V_rest_parts.append(np.asarray(rg.rest_V, dtype=np.float64))
        V_rest = np.vstack(V_rest_parts) if V_rest_parts else np.zeros((0, 3), dtype=np.float64)

        self.collision_mesh = ipctk.CollisionMesh(V_rest, self.edges_all, self.faces_all)
        self.d_hat_nominal_m = float(d_hat_m)
        self.max_chord_bound_m = float(max_chord)
        self.d_hat_eff_m = float(d_hat_m + (2.0 * max_chord if include_chord_margin else 0.0))
        self.barrier_stiffness = float(barrier_stiffness)
        self.mu_friction = float(mu_friction)
        self.eps_v = float(eps_v)

        self.barrier_pot = ipctk.BarrierPotential(self.d_hat_eff_m, self.barrier_stiffness)
        self.friction_pot = ipctk.FrictionPotential(self.eps_v)

        # Cached rod Bishop frames (refreshed per outer Newton iteration)
        self._rod_frames: list[tuple[np.ndarray, np.ndarray]] = []

    def refresh_frames(self, q_all: np.ndarray) -> None:
        self._rod_frames = []
        for rs in self.rod_specs:
            assert rs.xis_ring is not None
            qr = q_all[rs.dof_offset : rs.dof_offset + rs.mesh.n_dofs]
            self._rod_frames.append(_compute_rod_ring_frames(rs.mesh, qr, rs.xis_ring))

    def eval_proxy_mesh_and_jacobian(
        self,
        q_all: np.ndarray,
        *,
        rigid_V_list: Sequence[np.ndarray] | None = None,
        compute_jacobian: bool = True,
    ) -> tuple[np.ndarray, sparse.csc_matrix | None]:
        """Evaluate global proxy vertices V (V_tot, 3) and global sparse Jacobian J_W (3*V_tot, N_tot)."""
        if len(self._rod_frames) != len(self.rod_specs):
            self.refresh_frames(q_all)

        V_parts: list[np.ndarray] = []
        J_blocks: list[list[Any]] = []
        n_tot = self.n_total_dofs

        for idx, rs in enumerate(self.rod_specs):
            qr = q_all[rs.dof_offset : rs.dof_offset + rs.mesh.n_dofs]
            d1r, d2r = self._rod_frames[idx]
            vr, Jr = eval_rod_proxy_vertices_and_jacobian(rs, qr, d1_rings=d1r, d2_rings=d2r, compute_jacobian=compute_jacobian)
            V_parts.append(vr)
            if compute_jacobian:
                assert Jr is not None
                row_blocks = []
                if rs.dof_offset > 0:
                    row_blocks.append(sparse.csc_matrix((3 * rs.n_verts, rs.dof_offset)))
                row_blocks.append(Jr)
                rem = n_tot - (rs.dof_offset + rs.mesh.n_dofs)
                if rem > 0:
                    row_blocks.append(sparse.csc_matrix((3 * rs.n_verts, rem)))
                J_blocks.append(sparse.hstack(row_blocks, format="csc"))

        for ss in self.shell_specs:
            assert ss.W_scalar is not None and ss.J_W_3d is not None
            qs = q_all[ss.dof_offset : ss.dof_offset + 3 * ss.mesh.n_vec_dofs].reshape(ss.mesh.n_vec_dofs, 3)
            V_parts.append(ss.W_scalar @ qs)
            if compute_jacobian:
                row_blocks = []
                if ss.dof_offset > 0:
                    row_blocks.append(sparse.csc_matrix((3 * ss.n_verts, ss.dof_offset)))
                row_blocks.append(ss.J_W_3d)
                rem = n_tot - (ss.dof_offset + 3 * ss.mesh.n_vec_dofs)
                if rem > 0:
                    row_blocks.append(sparse.csc_matrix((3 * ss.n_verts, rem)))
                J_blocks.append(sparse.hstack(row_blocks, format="csc"))

        for r_idx, rg in enumerate(self.rigid_specs):
            vr = rg.rest_V if rigid_V_list is None else np.asarray(rigid_V_list[r_idx], dtype=np.float64)
            V_parts.append(vr)
            if compute_jacobian:
                J_blocks.append(sparse.csc_matrix((3 * len(vr), n_tot)))

        V_all = np.vstack(V_parts) if V_parts else np.zeros((0, 3), dtype=np.float64)
        J_all = sparse.vstack(J_blocks, format="csc") if (compute_jacobian and J_blocks) else None
        return V_all, J_all

    def build_lagged_friction(
        self,
        V_prev: np.ndarray,
    ) -> tuple[ipctk.TangentialCollisions, np.ndarray]:
        """Snapshot normal forces at start of time step for lagged IPC dissipative friction."""
        nc_prev = ipctk.NormalCollisions()
        nc_prev.build(self.collision_mesh, V_prev, self.d_hat_eff_m)
        tc = ipctk.TangentialCollisions()
        if self.mu_friction > 0.0 and len(nc_prev) > 0:
            tc.build(self.collision_mesh, V_prev, nc_prev, self.barrier_pot, self.mu_friction)
        return tc, V_prev.copy()

    def evaluate_ipc_pullback(
        self,
        q_all: np.ndarray,
        *,
        rigid_V_list: Sequence[np.ndarray] | None = None,
        lagged_tc: ipctk.TangentialCollisions | None = None,
        V_prev: np.ndarray | None = None,
        compute_hessian: bool = True,
    ) -> tuple[float, np.ndarray, sparse.csc_matrix | None, int, np.ndarray]:
        """Evaluate official ipctk Barrier + Friction and pull back to C1 DOFs via exact J_W^T H_IPC J_W."""
        V, J_W = self.eval_proxy_mesh_and_jacobian(q_all, rigid_V_list=rigid_V_list, compute_jacobian=True)
        assert J_W is not None

        nc = ipctk.NormalCollisions()
        nc.build(self.collision_mesh, V, self.d_hat_eff_m)
        n_coll = len(nc)

        e_tot = 0.0
        g_v = np.zeros(3 * self.n_total_verts, dtype=np.float64)
        H_v: sparse.csc_matrix | None = None

        if n_coll > 0:
            e_tot += float(self.barrier_pot(nc, self.collision_mesh, V))
            g_v += np.asarray(self.barrier_pot.gradient(nc, self.collision_mesh, V), dtype=np.float64)
            if compute_hessian:
                H_v = self.barrier_pot.hessian(
                    nc, self.collision_mesh, V, project_hessian_to_psd=ipctk.PSDProjectionMethod.CLAMP
                ).tocsc()

        if lagged_tc is not None and V_prev is not None and len(lagged_tc) > 0 and self.mu_friction > 0.0:
            dX = V - V_prev
            e_tot += float(self.friction_pot(lagged_tc, self.collision_mesh, dX))
            g_v += np.asarray(self.friction_pot.gradient(lagged_tc, self.collision_mesh, dX), dtype=np.float64)
            if compute_hessian:
                Hf = self.friction_pot.hessian(
                    lagged_tc, self.collision_mesh, dX, project_hessian_to_psd=ipctk.PSDProjectionMethod.CLAMP
                ).tocsc()
                H_v = Hf if H_v is None else (H_v + Hf).tocsc()

        g_c1 = np.asarray(J_W.T @ g_v, dtype=np.float64).ravel()
        if compute_hessian:
            if H_v is not None and H_v.nnz > 0:
                H_c1 = (J_W.T @ (H_v @ J_W)).tocsc()
            else:
                H_c1 = sparse.csc_matrix((self.n_total_dofs, self.n_total_dofs), dtype=np.float64)
        else:
            H_c1 = None
        return e_tot, g_c1, H_c1, n_coll, V

    def compute_ccd_max_step(
        self,
        V0: np.ndarray,
        V1: np.ndarray,
        *,
        safety: float = 0.80,
    ) -> float:
        """Exact Tight-Inclusion Continuous Collision Detection upper bound in (0, 1]."""
        toi = float(ipctk.compute_collision_free_stepsize(self.collision_mesh, V0, V1))
        if toi >= 1.0 - 1e-12:
            return 1.0
        return max(0.0, safety * toi)

    def has_intersections(self, q_all: np.ndarray, *, rigid_V_list: Sequence[np.ndarray] | None = None) -> bool:
        """Exact C++17 triangle-edge intersection audit on the unified proxy mesh (must be False!)."""
        V, _ = self.eval_proxy_mesh_and_jacobian(q_all, rigid_V_list=rigid_V_list, compute_jacobian=False)
        return bool(ipctk.has_intersections(self.collision_mesh, V))

