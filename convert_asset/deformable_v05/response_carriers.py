"""MorphTwin Relaxable Response Carriers, reduced-energy calibration, and explicit fracture dynamics.

Implements Sections 4.2-4.4 of MorphTwin (arXiv:2611.25963):
- Augments irregular 4-node tetrahedral cells with relaxable auxiliary nodes:
  * Bulk carrier: centroid auxiliary node connected to cell vertices.
  * Shear carrier: paired symmetric auxiliary nodes on the cell circumsphere.
- Evaluates reduced elastic energy E_bar(E) = min_z 1/2 sum_e Y_e L_e [n_e^T E n_e + n_e^T (z_j - z_i) / L_e]^2
  under unit volumetric strain E_vol = I / sqrt(3) and 5 orthonormal deviatoric strains.
- Computes 2x2 sensitivity Jacobian A = d[log kappa, log mu]^T / d[u_B, u_S]^T.
- Provides explicit forward integration with irreversible strain-based spring fracture and
  surviving-edge Gaussian frame binding export (gs_binding.npz).
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import numpy as np

from .contracts_v05 import MorphCalibrationRecord


def _orthonormal_strain_basis() -> tuple[np.ndarray, list[np.ndarray]]:
    """Return unit volumetric strain E_vol and 5 orthonormal deviatoric strain tensors in 3D."""
    e_vol = np.eye(3, dtype=np.float64) / math.sqrt(3.0)
    s2 = 1.0 / math.sqrt(2.0)
    s6 = 1.0 / math.sqrt(6.0)
    dev = [
        np.array([[s2, 0.0, 0.0], [0.0, -s2, 0.0], [0.0, 0.0, 0.0]], dtype=np.float64),
        np.array([[s6, 0.0, 0.0], [0.0, s6, 0.0], [0.0, 0.0, -2.0 * s6]], dtype=np.float64),
        np.array([[0.0, s2, 0.0], [s2, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float64),
        np.array([[0.0, 0.0, s2], [0.0, 0.0, 0.0], [s2, 0.0, 0.0]], dtype=np.float64),
        np.array([[0.0, 0.0, 0.0], [0.0, 0.0, s2], [0.0, s2, 0.0]], dtype=np.float64),
    ]
    return e_vol, dev


E_VOL, E_DEV_BASIS = _orthonormal_strain_basis()


@dataclass
class RelaxableSpringGraph:
    """Explicit mass-spring graph augmented with MorphTwin bulk and shear response carriers."""

    rest_positions: np.ndarray  # (N_total, 3)
    n_physical: int  # first n_physical nodes are physical; rest are auxiliary carriers
    edges: np.ndarray  # (M, 2) int32
    rest_lengths: np.ndarray  # (M,) float64
    base_stiffness: np.ndarray  # (M,) float64 Y_e(b, 0)
    edge_labels: np.ndarray  # (M, 2) float64 in {(0,0) backbone, (1,0) bulk, (0,1) shear}
    masses: np.ndarray  # (N_total,) float64
    reference_volume_m3: float
    backbone_cells: np.ndarray  # (C, 4) int32 tetrahedral cells

    def stiffness_for_controls(self, u_bs: tuple[float, float] | np.ndarray) -> np.ndarray:
        """Eq. (3): log Y_e(b, u) = log Y_e(b, 0) + w_e^T u."""
        u = np.asarray(u_bs, dtype=np.float64).reshape(2)
        offsets = self.edge_labels @ u
        return self.base_stiffness * np.exp(np.clip(offsets, -12.0, 12.0))

    def save_npz(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            out,
            rest_positions=self.rest_positions,
            n_physical=np.int32(self.n_physical),
            edges=self.edges,
            rest_lengths=self.rest_lengths,
            base_stiffness=self.base_stiffness,
            edge_labels=self.edge_labels,
            masses=self.masses,
            reference_volume_m3=np.float64(self.reference_volume_m3),
            backbone_cells=self.backbone_cells,
        )
        return out

    @classmethod
    def load_npz(cls, path: str | Path) -> RelaxableSpringGraph:
        with np.load(path, allow_pickle=False) as z:
            return cls(
                rest_positions=np.asarray(z["rest_positions"], dtype=np.float64),
                n_physical=int(z["n_physical"]),
                edges=np.asarray(z["edges"], dtype=np.int32),
                rest_lengths=np.asarray(z["rest_lengths"], dtype=np.float64),
                base_stiffness=np.asarray(z["base_stiffness"], dtype=np.float64),
                edge_labels=np.asarray(z["edge_labels"], dtype=np.float64),
                masses=np.asarray(z["masses"], dtype=np.float64),
                reference_volume_m3=float(z["reference_volume_m3"]),
                backbone_cells=np.asarray(z["backbone_cells"], dtype=np.int32),
            )


def _circumcenter_and_radius(pts4: np.ndarray) -> tuple[np.ndarray, float]:
    """Compute circumsphere center and radius for a 4-vertex tetrahedron (fallback to centroid)."""
    p0 = pts4[0]
    a = pts4[1:] - p0
    b = 0.5 * np.sum(a * a, axis=1)
    try:
        rel = np.linalg.solve(a, b)
        center = p0 + rel
        radius = float(np.linalg.norm(rel))
        if np.isfinite(radius) and 1e-6 < radius < 10.0 * float(np.linalg.norm(a)):
            return center, radius
    except np.linalg.LinAlgError:
        pass
    center = pts4.mean(axis=0)
    radius = float(np.mean(np.linalg.norm(pts4 - center, axis=1)))
    return center, max(radius, 1e-4)


def build_box_tet_grid(
    dimensions_xyz_m: tuple[float, float, float],
    subdiv_xyz: tuple[int, int, int] = (2, 2, 2),
) -> tuple[np.ndarray, np.ndarray]:
    """Build a watertight 3D tetrahedral mesh for a rectangular block (5 tets per hex cell)."""
    sx, sy, sz = (float(dimensions_xyz_m[0]), float(dimensions_xyz_m[1]), float(dimensions_xyz_m[2]))
    nx, ny, nz = (int(subdiv_xyz[0]), int(subdiv_xyz[1]), int(subdiv_xyz[2]))
    xs = np.linspace(-0.5 * sx, 0.5 * sx, nx + 1)
    ys = np.linspace(-0.5 * sy, 0.5 * sy, ny + 1)
    zs = np.linspace(0.0, sz, nz + 1)
    verts: list[list[float]] = []
    idx_map: dict[tuple[int, int, int], int] = {}
    for ix in range(nx + 1):
        for iy in range(ny + 1):
            for iz in range(nz + 1):
                idx_map[(ix, iy, iz)] = len(verts)
                verts.append([float(xs[ix]), float(ys[iy]), float(zs[iz])])

    tets: list[list[int]] = []
    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                v000 = idx_map[(ix, iy, iz)]
                v100 = idx_map[(ix + 1, iy, iz)]
                v010 = idx_map[(ix, iy + 1, iz)]
                v110 = idx_map[(ix + 1, iy + 1, iz)]
                v001 = idx_map[(ix, iy, iz + 1)]
                v101 = idx_map[(ix + 1, iy, iz + 1)]
                v011 = idx_map[(ix, iy + 1, iz + 1)]
                v111 = idx_map[(ix + 1, iy + 1, iz + 1)]
                if (ix + iy + iz) % 2 == 0:
                    tets.extend(
                        [
                            [v000, v100, v110, v101],
                            [v000, v110, v010, v011],
                            [v000, v001, v101, v011],
                            [v111, v110, v101, v011],
                            [v000, v110, v101, v011],
                        ]
                    )
                else:
                    tets.extend(
                        [
                            [v100, v110, v010, v111],
                            [v000, v100, v010, v001],
                            [v100, v101, v111, v001],
                            [v010, v011, v111, v001],
                            [v100, v010, v111, v001],
                        ]
                    )
    return np.asarray(verts, dtype=np.float64), np.asarray(tets, dtype=np.int32)


def build_relaxable_carrier_graph(
    physical_points: np.ndarray,
    tet_cells: np.ndarray,
    *,
    youngs_modulus_pa: float,
    total_mass_kg: float,
    enable_carriers: bool = True,
    bulk_spoke_scale: float = 1.6,
    shear_spoke_scale: float = 1.4,
    aux_mass_ratio: float = 0.05,
) -> RelaxableSpringGraph:
    """Construct an explicit MorphTwin spring graph with bulk and paired shear response carriers."""
    pts0 = np.asarray(physical_points, dtype=np.float64)
    tets = np.asarray(tet_cells, dtype=np.int32)
    n_phys = len(pts0)
    if n_phys < 4 or len(tets) == 0:
        raise ValueError("Need at least 4 physical nodes and 1 tetrahedral cell")

    # Reference volume from signed tet volumes
    vols = []
    for c in tets:
        p = pts0[c]
        v = abs(float(np.linalg.det(np.stack([p[1] - p[0], p[2] - p[0], p[3] - p[0]], axis=-1)))) / 6.0
        vols.append(v)
    ref_vol = max(float(sum(vols)), 1e-9)

    # Deduplicate backbone edges from tetrahedral cells
    edge_set: set[tuple[int, int]] = set()
    for c in tets:
        for a_i in range(4):
            for b_i in range(a_i + 1, 4):
                u, v = int(c[a_i]), int(c[b_i])
                if u > v:
                    u, v = v, u
                edge_set.add((u, v))
    backbone_edges = sorted(edge_set)

    # Scale backbone spring constant Y_e so continuum modulus matches order of youngs_modulus_pa
    mean_len = float(
        np.mean([np.linalg.norm(pts0[v] - pts0[u]) for u, v in backbone_edges])
    )
    # In a 3D central-force network, E_eff ~ (1/V) * sum Y_e L_e / 5 => Y_base ~ 2.5 * E * V / (M * mean_len)
    y_base = (2.5 * float(youngs_modulus_pa) * ref_vol) / max(len(backbone_edges) * mean_len, 1e-9)

    nodes_list = [p.copy() for p in pts0]
    edges_list: list[tuple[int, int]] = list(backbone_edges)
    stiff_list: list[float] = [y_base] * len(backbone_edges)
    label_list: list[tuple[float, float]] = [(0.0, 0.0)] * len(backbone_edges)

    if enable_carriers:
        for cell_idx, c in enumerate(tets):
            p = pts0[c]
            # 1. Bulk carrier: centroid auxiliary node connected to all 4 vertices
            centroid = p.mean(axis=0)
            b_idx = len(nodes_list)
            nodes_list.append(centroid)
            for v_id in c:
                edges_list.append((int(v_id), b_idx))
                stiff_list.append(y_base * bulk_spoke_scale)
                label_list.append((1.0, 0.0))

            # 2. Paired shear carrier: two symmetric auxiliary nodes offset along a cell-dependent
            # principal axis on the circumsphere, linked asymmetrically to opposite vertex pairs
            # + an internal shear brace so auxiliary relaxation selectively lowers shear vs bulk energy.
            center, radius = _circumcenter_and_radius(p)
            # Pick deterministic axis from edge pair (v0-v1) x (v2-v3)
            axis = np.cross(p[1] - p[0], p[3] - p[2])
            norm = float(np.linalg.norm(axis))
            if norm < 1e-8:
                axis = np.array([1.0, 0.0, 0.0], dtype=np.float64)
            else:
                axis = axis / norm
            offset = 0.65 * radius * axis
            s_plus = len(nodes_list)
            nodes_list.append(center + offset)
            s_minus = len(nodes_list)
            nodes_list.append(center - offset)

            # Connect each shear carrier node to all 4 vertices with opposite-pair emphasis
            for v_id in (int(c[0]), int(c[1]), int(c[2]), int(c[3])):
                edges_list.append((v_id, s_plus))
                stiff_list.append(y_base * shear_spoke_scale)
                label_list.append((0.0, 1.0))
                edges_list.append((v_id, s_minus))
                stiff_list.append(y_base * shear_spoke_scale)
                label_list.append((0.0, 1.0))
            # Cross-brace between paired shear nodes
            edges_list.append((s_plus, s_minus))
            stiff_list.append(y_base * shear_spoke_scale * 1.5)
            label_list.append((0.0, 1.0))

    rest_positions = np.asarray(nodes_list, dtype=np.float64)
    edges = np.asarray(edges_list, dtype=np.int32)
    diffs = rest_positions[edges[:, 1]] - rest_positions[edges[:, 0]]
    rest_lengths = np.maximum(np.linalg.norm(diffs, axis=1), 1e-7)
    base_stiffness = np.asarray(stiff_list, dtype=np.float64)
    edge_labels = np.asarray(label_list, dtype=np.float64)

    n_total = len(rest_positions)
    n_aux = n_total - n_phys
    masses = np.zeros(n_total, dtype=np.float64)
    if n_aux > 0:
        phys_mass = float(total_mass_kg) * (1.0 - aux_mass_ratio)
        aux_mass = float(total_mass_kg) * aux_mass_ratio
        masses[:n_phys] = phys_mass / n_phys
        masses[n_phys:] = aux_mass / n_aux
    else:
        masses[:] = float(total_mass_kg) / n_phys

    return RelaxableSpringGraph(
        rest_positions=rest_positions,
        n_physical=n_phys,
        edges=edges,
        rest_lengths=rest_lengths,
        base_stiffness=base_stiffness,
        edge_labels=edge_labels,
        masses=masses,
        reference_volume_m3=ref_vol,
        backbone_cells=tets,
    )


def evaluate_reduced_bulk_shear_energy(
    graph: RelaxableSpringGraph,
    u_bs: tuple[float, float] | np.ndarray = (0.0, 0.0),
) -> tuple[float, float, np.ndarray]:
    """Evaluate MorphTwin Eq. (4)-(5) reduced bulk (kappa) and shear (mu) moduli after auxiliary relaxation.

    Returns (kappa_continuum, mu_continuum, q=[log(kappa_continuum), log(mu_continuum)]).
    """
    y_e = graph.stiffness_for_controls(u_bs)
    n_phys = graph.n_physical
    n_total = len(graph.rest_positions)
    n_aux = n_total - n_phys

    edges = graph.edges
    lengths = graph.rest_lengths
    dirs = (graph.rest_positions[edges[:, 1]] - graph.rest_positions[edges[:, 0]]) / lengths[:, None]

    # Assemble auxiliary Hessian H_zz (3*n_aux x 3*n_aux) once for all 6 strain modes
    if n_aux > 0:
        dim = 3 * n_aux
        h_zz = np.zeros((dim, dim), dtype=np.float64)
        for e_idx in range(len(edges)):
            i, j = int(edges[e_idx, 0]), int(edges[e_idx, 1])
            n_vec = dirs[e_idx]
            k_e = float(y_e[e_idx] / lengths[e_idx])
            outer = k_e * np.outer(n_vec, n_vec)
            i_aux = i - n_phys
            j_aux = j - n_phys
            if i_aux >= 0:
                sl_i = slice(3 * i_aux, 3 * i_aux + 3)
                h_zz[sl_i, sl_i] += outer
            if j_aux >= 0:
                sl_j = slice(3 * j_aux, 3 * j_aux + 3)
                h_zz[sl_j, sl_j] += outer
            if i_aux >= 0 and j_aux >= 0:
                sl_i = slice(3 * i_aux, 3 * i_aux + 3)
                sl_j = slice(3 * j_aux, 3 * j_aux + 3)
                h_zz[sl_i, sl_j] -= outer
                h_zz[sl_j, sl_i] -= outer
        # Tiny Tikhonov stabilization for any unconstrained auxiliary DOF
        h_zz += 1e-9 * float(np.max(np.diag(h_zz)) + 1.0) * np.eye(dim, dtype=np.float64)
    else:
        h_zz = None

    def _reduced_energy(strain_e: np.ndarray) -> float:
        # Affine projection per edge: alpha_e = n_e^T E n_e
        alpha = np.einsum("ei,ij,ej->e", dirs, strain_e, dirs)
        if n_aux == 0 or h_zz is None:
            return float(0.5 * np.sum(y_e * lengths * (alpha * alpha)))

        # RHS g = -d/dz [1/2 sum Y_e L_e (alpha_e + n_e^T (z_j - z_i)/L_e)^2]
        rhs = np.zeros(3 * n_aux, dtype=np.float64)
        for e_idx in range(len(edges)):
            i, j = int(edges[e_idx, 0]), int(edges[e_idx, 1])
            coeff = float(y_e[e_idx] * alpha[e_idx])
            vec = coeff * dirs[e_idx]
            i_aux = i - n_phys
            j_aux = j - n_phys
            if i_aux >= 0:
                rhs[3 * i_aux : 3 * i_aux + 3] += vec
            if j_aux >= 0:
                rhs[3 * j_aux : 3 * j_aux + 3] -= vec
        z_aux = np.linalg.solve(h_zz, rhs).reshape(n_aux, 3)

        # Evaluate relaxed total strain per edge
        z_full = np.zeros((n_total, 3), dtype=np.float64)
        z_full[n_phys:] = z_aux
        dz_edge = z_full[edges[:, 1]] - z_full[edges[:, 0]]
        nonaffine = np.einsum("ei,ei->e", dirs, dz_edge) / lengths
        total_strain = alpha + nonaffine
        return float(0.5 * np.sum(y_e * lengths * (total_strain * total_strain)))

    e_vol_val = _reduced_energy(E_VOL)
    e_dev_vals = [_reduced_energy(ed) for ed in E_DEV_BASIS]
    kappa_int = (2.0 / 3.0) * e_vol_val
    mu_int = (1.0 / 5.0) * sum(e_dev_vals)
    kappa_cont = max(kappa_int / graph.reference_volume_m3, 1e-6)
    mu_cont = max(mu_int / graph.reference_volume_m3, 1e-6)
    q_vec = np.array([math.log(kappa_cont), math.log(mu_cont)], dtype=np.float64)
    return kappa_cont, mu_cont, q_vec


def calibrate_carrier_graph(
    graph: RelaxableSpringGraph,
    *,
    u0: tuple[float, float] = (0.0, 0.0),
    eps: float = 0.05,
) -> MorphCalibrationRecord:
    """Compute MorphTwin Eq. (6) offline sensitivity Jacobian A = dq / du for a carrier graph."""
    _, _, q0 = evaluate_reduced_bulk_shear_energy(graph, u0)
    a_mat = np.zeros((2, 2), dtype=np.float64)
    for col in range(2):
        u_plus = np.array(u0, dtype=np.float64)
        u_minus = np.array(u0, dtype=np.float64)
        u_plus[col] += eps
        u_minus[col] -= eps
        _, _, q_plus = evaluate_reduced_bulk_shear_energy(graph, u_plus)
        _, _, q_minus = evaluate_reduced_bulk_shear_energy(graph, u_minus)
        a_mat[:, col] = (q_plus - q_minus) / (2.0 * eps)

    cond = float(np.linalg.cond(a_mat)) if np.all(np.isfinite(a_mat)) else float("inf")
    return MorphCalibrationRecord(
        control_names=("u_bulk", "u_shear"),
        u0=(float(u0[0]), float(u0[1])),
        q0_log_kappa_mu=(float(q0[0]), float(q0[1])),
        jacobian_A_2x2=(
            (float(a_mat[0, 0]), float(a_mat[0, 1])),
            (float(a_mat[1, 0]), float(a_mat[1, 1])),
        ),
        condition_number=cond,
    )


def simulate_explicit_with_fracture(
    graph: RelaxableSpringGraph,
    *,
    u_bs: tuple[float, float] = (0.0, 0.0),
    steps: int = 40,
    dt_s: float = 5e-4,
    damping: float = 8.0,
    fracture_strain_threshold: float = 0.50,
    external_force_fn: Any | None = None,
) -> dict[str, Any]:
    """Run explicit central-force spring dynamics with irreversible strain-based fracture."""
    y_e = graph.stiffness_for_controls(u_bs)
    pos = graph.rest_positions.copy()
    vel = np.zeros_like(pos)
    edges = graph.edges
    l0 = graph.rest_lengths
    alive = np.ones(len(edges), dtype=bool)
    inv_mass = 1.0 / np.maximum(graph.masses, 1e-9)

    phys_traj = np.zeros((steps + 1, graph.n_physical, 3), dtype=np.float64)
    phys_traj[0] = pos[: graph.n_physical]
    max_edge_strain = 0.0

    for step in range(steps):
        forces = np.zeros_like(pos)
        diff = pos[edges[:, 1]] - pos[edges[:, 0]]
        dist = np.maximum(np.linalg.norm(diff, axis=1), 1e-9)
        strain = (dist - l0) / l0
        abs_strain = np.abs(strain)
        if np.any(alive):
            max_edge_strain = max(max_edge_strain, float(np.max(abs_strain[alive])))
        # Irreversible fracture when active edge exceeds threshold
        newly_broken = alive & (abs_strain > fracture_strain_threshold)
        if np.any(newly_broken):
            alive[newly_broken] = False

        active_idx = np.nonzero(alive)[0]
        if len(active_idx) > 0:
            dirs = diff[active_idx] / dist[active_idx, None]
            f_mag = y_e[active_idx] * strain[active_idx]
            f_vec = f_mag[:, None] * dirs
            np.add.at(forces, edges[active_idx, 0], f_vec)
            np.add.at(forces, edges[active_idx, 1], -f_vec)

        if external_force_fn is not None:
            forces[: graph.n_physical] += np.asarray(
                external_force_fn(step, pos[: graph.n_physical], vel[: graph.n_physical]),
                dtype=np.float64,
            )

        forces -= damping * vel
        vel += dt_s * (forces * inv_mass[:, None])
        pos += dt_s * vel
        phys_traj[step + 1] = pos[: graph.n_physical]

    fractured_ratio = float(1.0 - np.mean(alive))
    return {
        "physical_positions_seq": phys_traj,
        "alive_edge_mask": alive,
        "fractured_edge_count": int(np.sum(~alive)),
        "fractured_edge_ratio": fractured_ratio,
        "max_edge_strain": max_edge_strain,
        "finite_ok": bool(np.all(np.isfinite(phys_traj))),
    }


def export_gaussian_binding_npz(
    graph: RelaxableSpringGraph,
    out_path: str | Path,
    *,
    base_rgb: tuple[float, float, float] = (0.78, 0.56, 0.34),
) -> Path:
    """Export canonical Gaussian-to-node binding with surviving-edge local frames (gs_binding.npz)."""
    n_phys = graph.n_physical
    pts = graph.rest_positions[:n_phys]
    # Pick up to 3 neighbor indices per physical node from backbone edges
    backbone_mask = (graph.edge_labels[:, 0] == 0.0) & (graph.edge_labels[:, 1] == 0.0)
    b_edges = graph.edges[backbone_mask]
    neighbors = np.full((n_phys, 3), -1, dtype=np.int32)
    adj: list[list[int]] = [[] for _ in range(n_phys)]
    for u, v in b_edges:
        if u < n_phys and v < n_phys:
            adj[int(u)].append(int(v))
            adj[int(v)].append(int(u))
    for i in range(n_phys):
        nbrs = sorted(set(adj[i]))[:3]
        for k, nb in enumerate(nbrs):
            neighbors[i, k] = nb

    # One Gaussian centered at each physical node + one at each backbone edge midpoint
    midpoints = 0.5 * (pts[b_edges[:, 0]] + pts[b_edges[:, 1]])
    n_g = n_phys + len(b_edges)
    anchor_nodes = np.full((n_g, 2), -1, dtype=np.int32)
    anchor_nodes[:n_phys, 0] = np.arange(n_phys, dtype=np.int32)
    anchor_nodes[:n_phys, 1] = np.arange(n_phys, dtype=np.int32)
    anchor_nodes[n_phys:, 0] = b_edges[:, 0]
    anchor_nodes[n_phys:, 1] = b_edges[:, 1]

    rest_centers = np.vstack([pts, midpoints])
    # Estimate isotropic splat scale from median edge length
    mean_edge = float(np.median(graph.rest_lengths[backbone_mask])) if np.any(backbone_mask) else 0.01
    scales = np.full((n_g, 3), 0.45 * mean_edge, dtype=np.float64)
    colors = np.tile(np.asarray(base_rgb, dtype=np.float64)[None, :], (n_g, 1))
    opacities = np.full(n_g, 0.92, dtype=np.float64)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        rest_centers=rest_centers,
        anchor_nodes=anchor_nodes,
        node_neighbors=neighbors,
        backbone_edges=b_edges,
        scales=scales,
        colors=colors,
        opacities=opacities,
    )
    return out

