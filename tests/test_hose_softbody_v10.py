"""Unit tests for ConvertAsset hose_softbody_v10 (Route A D6-DER compiler + Route B adaptive hollow FEM mesh)."""

from __future__ import annotations

import math
import numpy as np

from convert_asset.hose_softbody_v10 import (
    HoseMaterialSpecV10,
    build_adaptive_hollow_tube_tet_mesh,
    build_cosserat_twist_stripe_tube,
    compile_d6_der_rod_spec,
    compute_cuff_hoop_and_pinch_strain,
    extract_twist_angles_from_link_frames,
)


def test_d6_der_rod_compiler_physical_scaling() -> None:
    mat = HoseMaterialSpecV10()
    spec = compile_d6_der_rod_spec(mat, total_length_m=0.48, n_links=24)
    assert spec.n_links == 24
    assert math.isclose(spec.segment_length_m, 0.020, rel_tol=1e-6)
    assert 0.005 < spec.bend_stiffness_nm_per_rad < 0.15
    assert 0.005 < spec.twist_stiffness_nm_per_rad < 0.15
    assert spec.twist_stiffness_nm_per_rad < spec.bend_stiffness_nm_per_rad  # 2G/E = 1/(1+nu) < 1
    assert spec.cuff_spec.cuff_rest_inner_radius_m < spec.cuff_spec.barb_bead_outer_radius_m


def test_adaptive_hollow_tet_mesh_positive_volumes_and_strain_metrics() -> None:
    ctrl = np.column_stack([np.linspace(0.0, 0.36, 12), np.zeros(12), np.full(12, 0.85)])
    mesh = build_adaptive_hollow_tube_tet_mesh(
        ctrl,
        r_in=0.0031,
        r_out=0.0049,
        n_theta=10,
        cuff_length_m=0.045,
        cuff_ds_m=0.0045,
        body_ds_m=0.016,
    )
    assert mesh.min_tet_volume_m3 > 0.0
    assert len(mesh.cuff_ring_indices) >= 10
    assert 1200 <= len(mesh.tets) <= 3200
    # Verify non-uniform grading: cuff spacing < body spacing
    ds = np.diff(mesh.ring_s)
    assert float(np.mean(ds[:5])) < 0.5 * float(np.mean(ds[-5:]))

    # Simulate 25% radial barb expansion on cuff rings -> hoop strain metric should detect ~25%
    deformed = mesh.rest_points.copy()
    for ri in mesh.cuff_ring_indices[:6]:
        in_ids = mesh.ring_inner_vertex_indices(int(ri))
        out_ids = mesh.ring_outer_vertex_indices(int(ri))
        c = np.mean(deformed[in_ids], axis=0)
        deformed[in_ids] = c + 1.25 * (deformed[in_ids] - c)
        deformed[out_ids] = c + 1.18 * (deformed[out_ids] - c)
    st = compute_cuff_hoop_and_pinch_strain(mesh, deformed)
    assert 22.0 <= st["max_cuff_hoop_strain_pct"] <= 28.0


def test_cosserat_twist_extraction_and_stripe_mesh() -> None:
    n = 16
    pos = np.column_stack([np.linspace(0.0, 0.30, n), np.zeros(n), np.full(n, 0.85)])
    rots = []
    for i in range(n):
        ang = math.radians(90.0) * (i / float(n - 1))
        c, s = math.cos(ang), math.sin(ang)
        rots.append(np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64))
    tw = extract_twist_angles_from_link_frames(pos, rots, local_material_axis=1)
    assert abs(math.degrees(tw[-1]) - 90.0) < 1e-3
    verts, nrms, tris, cols = build_cosserat_twist_stripe_tube(pos, tw)
    assert verts.shape == (n * 24, 3)
    assert nrms.shape == verts.shape
    assert len(tris) == (n - 1) * 24 * 2
    assert cols.shape == verts.shape

