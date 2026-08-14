"""Simulator-neutral topology checks and conservative vessel-wall repair."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
from typing import Iterable, Sequence


class ContainerTopologyError(ValueError):
    """Raised when a mesh does not satisfy a conservative repair contract."""


@dataclass(frozen=True)
class MeshTopologyAudit:
    edge_count: int
    boundary_edge_count: int
    boundary_loop_count: int
    non_manifold_edge_count: int
    boundary_loops: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class AnnularRimRepair:
    points: tuple[tuple[float, float, float], ...]
    face_vertex_counts: tuple[int, ...]
    face_vertex_indices: tuple[int, ...]
    added_face_count: int
    outer_loop: tuple[int, ...]
    inner_loop: tuple[int, ...]


def _faces(
    face_vertex_counts: Sequence[int], face_vertex_indices: Sequence[int]
) -> Iterable[tuple[int, ...]]:
    offset = 0
    for count in face_vertex_counts:
        if count < 3:
            raise ContainerTopologyError(
                "mesh contains a face with fewer than three vertices"
            )
        end = offset + int(count)
        face = tuple(int(value) for value in face_vertex_indices[offset:end])
        if len(face) != count:
            raise ContainerTopologyError(
                "faceVertexCounts and faceVertexIndices disagree"
            )
        yield face
        offset = end
    if offset != len(face_vertex_indices):
        raise ContainerTopologyError("faceVertexCounts and faceVertexIndices disagree")


def _boundary_loops(
    boundary_edges: Sequence[tuple[int, int]],
) -> tuple[tuple[int, ...], ...]:
    adjacency: dict[int, list[int]] = defaultdict(list)
    for left, right in boundary_edges:
        adjacency[left].append(right)
        adjacency[right].append(left)
    if any(len(neighbours) != 2 for neighbours in adjacency.values()):
        raise ContainerTopologyError("boundary edges do not form disjoint closed loops")

    remaining = {tuple(sorted(edge)) for edge in boundary_edges}
    loops: list[tuple[int, ...]] = []
    while remaining:
        first_edge = min(remaining)
        start, current = first_edge
        previous = start
        loop = [start, current]
        remaining.remove(first_edge)
        while current != start:
            choices = [vertex for vertex in adjacency[current] if vertex != previous]
            if len(choices) != 1:
                raise ContainerTopologyError("boundary loop traversal is ambiguous")
            nxt = choices[0]
            edge = tuple(sorted((current, nxt)))
            if nxt != start and edge not in remaining:
                raise ContainerTopologyError(
                    "boundary loop closes through a reused edge"
                )
            if edge in remaining:
                remaining.remove(edge)
            previous, current = current, nxt
            if current != start:
                loop.append(current)
            if len(loop) > len(adjacency) + 1:
                raise ContainerTopologyError(
                    "boundary loop traversal did not terminate"
                )
        loops.append(tuple(loop))
    return tuple(sorted(loops, key=lambda item: (len(item), item)))


def analyze_mesh_topology(
    face_vertex_counts: Sequence[int], face_vertex_indices: Sequence[int]
) -> MeshTopologyAudit:
    edge_counts: Counter[tuple[int, int]] = Counter()
    for face in _faces(face_vertex_counts, face_vertex_indices):
        for left, right in zip(face, face[1:] + face[:1]):
            if left == right:
                raise ContainerTopologyError(
                    "mesh contains a zero-length topology edge"
                )
            edge_counts[tuple(sorted((left, right)))] += 1
    boundary = tuple(edge for edge, count in edge_counts.items() if count == 1)
    loops = _boundary_loops(boundary) if boundary else ()
    return MeshTopologyAudit(
        edge_count=len(edge_counts),
        boundary_edge_count=len(boundary),
        boundary_loop_count=len(loops),
        non_manifold_edge_count=sum(count > 2 for count in edge_counts.values()),
        boundary_loops=loops,
    )


def _loop_geometry(
    points: Sequence[Sequence[float]], loop: Sequence[int]
) -> tuple[tuple[float, float], float, float, float]:
    coordinates = [points[index] for index in loop]
    center = (
        sum(float(point[0]) for point in coordinates) / len(coordinates),
        sum(float(point[1]) for point in coordinates) / len(coordinates),
    )
    mean_z = sum(float(point[2]) for point in coordinates) / len(coordinates)
    max_z_error = max(abs(float(point[2]) - mean_z) for point in coordinates)
    mean_radius = sum(
        math.hypot(float(point[0]) - center[0], float(point[1]) - center[1])
        for point in coordinates
    ) / len(coordinates)
    return center, mean_z, max(max_z_error, 0.0), mean_radius


def _angular_order(
    points: Sequence[Sequence[float]], loop: Sequence[int], center: tuple[float, float]
) -> tuple[int, ...]:
    return tuple(
        sorted(
            loop,
            key=lambda index: math.atan2(
                float(points[index][1]) - center[1],
                float(points[index][0]) - center[0],
            ),
        )
    )


def close_annular_wall_rim(
    points: Sequence[Sequence[float]],
    face_vertex_counts: Sequence[int],
    face_vertex_indices: Sequence[int],
    *,
    tolerance: float = 1.0e-5,
) -> AnnularRimRepair:
    """Close a vessel wall, not its cavity, by bridging two coplanar rim loops.

    Existing points and faces are retained byte-for-byte at the sequence level.
    The function refuses general hole filling: exactly two concentric loops with
    matching vertex counts are required.
    """

    if tolerance <= 0.0 or not math.isfinite(tolerance):
        raise ContainerTopologyError("tolerance must be finite and positive")
    audit = analyze_mesh_topology(face_vertex_counts, face_vertex_indices)
    if audit.non_manifold_edge_count:
        raise ContainerTopologyError("mesh contains non-manifold edges")
    if audit.boundary_loop_count != 2:
        raise ContainerTopologyError(
            "annular repair requires exactly two boundary loops"
        )
    first, second = audit.boundary_loops
    if len(first) != len(second) or len(first) < 8:
        raise ContainerTopologyError(
            "annular boundary loops must have matching resolution"
        )

    first_geometry = _loop_geometry(points, first)
    second_geometry = _loop_geometry(points, second)
    if first_geometry[2] > tolerance or second_geometry[2] > tolerance:
        raise ContainerTopologyError("annular boundary loops must each be coplanar")
    if abs(first_geometry[1] - second_geometry[1]) > tolerance:
        raise ContainerTopologyError("annular boundary loops must be coplanar")
    center_error = math.hypot(
        first_geometry[0][0] - second_geometry[0][0],
        first_geometry[0][1] - second_geometry[0][1],
    )
    if center_error > tolerance:
        raise ContainerTopologyError("annular boundary loops must be concentric")
    if abs(first_geometry[3] - second_geometry[3]) <= tolerance:
        raise ContainerTopologyError("annular boundary loops must have different radii")

    if first_geometry[3] > second_geometry[3]:
        outer_loop, inner_loop = first, second
        center = first_geometry[0]
    else:
        outer_loop, inner_loop = second, first
        center = second_geometry[0]
    outer = _angular_order(points, outer_loop, center)
    inner = _angular_order(points, inner_loop, center)

    new_counts = list(int(value) for value in face_vertex_counts)
    new_indices = list(int(value) for value in face_vertex_indices)
    for index in range(len(outer)):
        nxt = (index + 1) % len(outer)
        new_counts.append(4)
        new_indices.extend((outer[index], outer[nxt], inner[nxt], inner[index]))

    repaired_audit = analyze_mesh_topology(new_counts, new_indices)
    if repaired_audit.boundary_edge_count or repaired_audit.non_manifold_edge_count:
        raise ContainerTopologyError("annular repair did not produce a closed manifold")
    return AnnularRimRepair(
        points=tuple(tuple(float(value) for value in point) for point in points),
        face_vertex_counts=tuple(new_counts),
        face_vertex_indices=tuple(new_indices),
        added_face_count=len(outer),
        outer_loop=outer,
        inner_loop=inner,
    )
