from __future__ import annotations

import math

import pytest

from convert_asset.asset_application_normalizer.container_topology import (
    ContainerTopologyError,
    UnifiedCylindricalVesselSpec,
    analyze_mesh_topology,
    build_gpu_convex_vessel_partition,
    build_unified_cylindrical_vessel_mesh,
    close_annular_wall_rim,
)


def _open_annular_wall(sides: int = 12):
    points: list[tuple[float, float, float]] = []
    for z in (0.0, 1.0):
        for radius in (2.0, 1.5):
            for index in range(sides):
                angle = 2.0 * math.pi * index / sides
                points.append((radius * math.cos(angle), radius * math.sin(angle), z))
    ob, ib, ot, it = 0, sides, 2 * sides, 3 * sides
    faces: list[tuple[int, ...]] = []
    for index in range(sides):
        nxt = (index + 1) % sides
        faces.append((ob + index, ob + nxt, ot + nxt, ot + index))
        faces.append((ib + nxt, ib + index, it + index, it + nxt))
        faces.append((ob + nxt, ob + index, ib + index, ib + nxt))
    counts = [len(face) for face in faces]
    indices = [vertex for face in faces for vertex in face]
    return points, counts, indices


def test_closes_only_annular_wall_rim_and_preserves_source_geometry() -> None:
    points, counts, indices = _open_annular_wall()

    before = analyze_mesh_topology(counts, indices)
    repaired = close_annular_wall_rim(points, counts, indices)
    after = analyze_mesh_topology(
        repaired.face_vertex_counts, repaired.face_vertex_indices
    )

    assert before.boundary_edge_count == 24
    assert before.boundary_loop_count == 2
    assert repaired.points == tuple(points)
    assert repaired.face_vertex_counts[: len(counts)] == tuple(counts)
    assert repaired.face_vertex_indices[: len(indices)] == tuple(indices)
    assert repaired.added_face_count == 12
    assert after.boundary_edge_count == 0
    assert after.non_manifold_edge_count == 0


def test_rejects_single_open_boundary_instead_of_capping_a_container() -> None:
    points, counts, indices = _open_annular_wall()
    counts = counts[:-12]
    indices = indices[: sum(counts)]

    with pytest.raises(ContainerTopologyError, match="exactly two boundary loops"):
        close_annular_wall_rim(points, counts, indices)


def test_rejects_non_coplanar_boundary_loops() -> None:
    points, counts, indices = _open_annular_wall()
    points = list(points)
    x, y, z = points[-1]
    points[-1] = (x, y, z + 0.1)

    with pytest.raises(ContainerTopologyError, match="coplanar"):
        close_annular_wall_rim(points, counts, indices)


def test_builds_one_closed_all_triangle_unified_vessel_surface() -> None:
    mesh = build_unified_cylindrical_vessel_mesh(
        UnifiedCylindricalVesselSpec(
            outer_radius=0.02099,
            inner_radius=0.019185,
            bottom_z=0.0099,
            floor_z=0.011705,
            rim_center_z=0.27659,
            rim_major_radius=0.020825,
            rim_radial_radius=0.0011,
            rim_vertical_radius=0.00165,
            sides=96,
            rim_arc_segments=8,
        )
    )

    audit = analyze_mesh_topology(
        mesh.face_vertex_counts, mesh.face_vertex_indices
    )

    assert set(mesh.face_vertex_counts) == {3}
    assert audit.boundary_edge_count == 0
    assert audit.non_manifold_edge_count == 0
    assert mesh.radial_side_count == 96
    assert mesh.maximum_rim_chord_error_m <= 0.0001
    radii = [math.hypot(point[0], point[1]) for point in mesh.points]
    heights = [point[2] for point in mesh.points]
    assert max(radii) == pytest.approx(0.021925)
    assert min(heights) == pytest.approx(0.0099)
    assert max(heights) == pytest.approx(0.27824)
    assert mesh.cavity_radius == pytest.approx(0.019185)
    assert mesh.cavity_floor_z == pytest.approx(0.011705)


def test_unified_vessel_rejects_invalid_dimensions() -> None:
    with pytest.raises(ContainerTopologyError, match="inner radius"):
        build_unified_cylindrical_vessel_mesh(
            UnifiedCylindricalVesselSpec(
                outer_radius=0.02,
                inner_radius=0.02,
                bottom_z=0.0,
                floor_z=0.002,
                rim_center_z=0.2,
                rim_major_radius=0.02,
                rim_radial_radius=0.001,
                rim_vertical_radius=0.001,
            )
        )


def test_builds_low_vertex_source_derived_gpu_convex_partition() -> None:
    spec = UnifiedCylindricalVesselSpec(
        outer_radius=0.02099,
        inner_radius=0.019185,
        bottom_z=0.0099,
        floor_z=0.011705,
        rim_center_z=0.27659,
        rim_major_radius=0.020825,
        rim_radial_radius=0.0011,
        rim_vertical_radius=0.00165,
    )

    partition = build_gpu_convex_vessel_partition(spec, support_bottom_z=0.0)

    assert len(partition.pieces) == 249
    assert partition.wall_piece_count == 248
    assert partition.bottom_piece_count == 1
    assert partition.maximum_surface_error_m <= 0.0001
    first_wall = partition.pieces[0]
    assert all(abs(point[1]) > 1.0e-12 for point in first_wall.points)
    assert partition.pieces[1].points != first_wall.points
    assert all(piece.rotation_z_degrees == 0.0 for piece in partition.pieces)
    bottom = next(piece for piece in partition.pieces if piece.role == "bottom")
    assert min(point[2] for point in bottom.points) == pytest.approx(0.0)
    assert max(point[2] for point in bottom.points) == pytest.approx(spec.floor_z)
    assert all(
        coordinate == round(coordinate, 7)
        for piece in partition.pieces
        for point in piece.points
        for coordinate in point
    )
    for piece in partition.pieces:
        assert len(piece.points) <= 64
        assert set(piece.face_vertex_counts) == {3}
        audit = analyze_mesh_topology(
            piece.face_vertex_counts, piece.face_vertex_indices
        )
        assert audit.boundary_edge_count == 0
        assert audit.non_manifold_edge_count == 0


def test_reuses_one_full_height_wall_hull_with_source_exact_rotations() -> None:
    spec = UnifiedCylindricalVesselSpec(
        outer_radius=0.02099,
        inner_radius=0.019185,
        bottom_z=0.0099,
        floor_z=0.011705,
        rim_center_z=0.27659,
        rim_major_radius=0.020825,
        rim_radial_radius=0.0011,
        rim_vertical_radius=0.00165,
    )

    partition = build_gpu_convex_vessel_partition(
        spec,
        support_bottom_z=0.0,
        wall_vertical_segments=1,
        reuse_rotated_wall_geometry=True,
    )

    walls = [piece for piece in partition.pieces if piece.role == "wall"]
    assert len(partition.pieces) == 32
    assert len({piece.points for piece in walls}) == 1
    assert len({piece.rotation_z_degrees for piece in walls}) == 31
    assert min(
        point[2]
        for piece in partition.pieces
        if piece.role == "bottom"
        for point in piece.points
    ) == pytest.approx(0.0)
