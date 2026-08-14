from __future__ import annotations

import math

import pytest

from convert_asset.asset_application_normalizer.container_topology import (
    ContainerTopologyError,
    analyze_mesh_topology,
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
