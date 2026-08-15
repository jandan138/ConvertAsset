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


@dataclass(frozen=True)
class UnifiedCylindricalVesselSpec:
    """Source-measured dimensions for an 0812-style unified vessel surface."""

    outer_radius: float
    inner_radius: float
    bottom_z: float
    floor_z: float
    rim_center_z: float
    rim_major_radius: float
    rim_radial_radius: float
    rim_vertical_radius: float
    outer_top_radius: float | None = None
    inner_top_radius: float | None = None
    sides: int = 96
    rim_arc_segments: int = 8
    body_axial_segments: int = 1
    rim_style: str = "rolled"


@dataclass(frozen=True)
class UnifiedCylindricalVesselMesh:
    """One render-visible, all-triangle glass surface with an open cavity."""

    points: tuple[tuple[float, float, float], ...]
    face_vertex_counts: tuple[int, ...]
    face_vertex_indices: tuple[int, ...]
    cross_section: tuple[tuple[float, float], ...]
    radial_side_count: int
    cavity_radius: float
    cavity_floor_z: float
    maximum_rim_chord_error_m: float


@dataclass(frozen=True)
class ConvexVesselPiece:
    """One closed, low-vertex convex candidate derived from the vessel surface."""

    name: str
    role: str
    points: tuple[tuple[float, float, float], ...]
    face_vertex_counts: tuple[int, ...]
    face_vertex_indices: tuple[int, ...]
    rotation_z_degrees: float = 0.0


@dataclass(frozen=True)
class GPUConvexVesselPartition:
    pieces: tuple[ConvexVesselPiece, ...]
    wall_piece_count: int
    bottom_piece_count: int
    maximum_surface_error_m: float


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


def _validate_unified_vessel_spec(spec: UnifiedCylindricalVesselSpec) -> None:
    outer_top_radius = spec.outer_top_radius or spec.outer_radius
    inner_top_radius = spec.inner_top_radius or spec.inner_radius
    dimensions = (
        spec.outer_radius,
        spec.inner_radius,
        spec.bottom_z,
        spec.floor_z,
        spec.rim_center_z,
        spec.rim_major_radius,
        spec.rim_radial_radius,
        spec.rim_vertical_radius,
        outer_top_radius,
        inner_top_radius,
    )
    if not all(math.isfinite(value) for value in dimensions):
        raise ContainerTopologyError("vessel dimensions must be finite")
    if spec.inner_radius <= 0.0 or spec.inner_radius >= spec.outer_radius:
        raise ContainerTopologyError(
            "inner radius must be positive and smaller than outer radius"
        )
    if inner_top_radius <= 0.0 or inner_top_radius >= outer_top_radius:
        raise ContainerTopologyError(
            "top inner radius must be positive and smaller than top outer radius"
        )
    if spec.floor_z <= spec.bottom_z or spec.rim_center_z <= spec.floor_z:
        raise ContainerTopologyError(
            "vessel floor and rim heights must be strictly increasing"
        )
    if spec.rim_radial_radius <= 0.0 or spec.rim_vertical_radius <= 0.0:
        raise ContainerTopologyError("rim radii must be positive")
    if spec.sides < 12 or spec.sides % 4:
        raise ContainerTopologyError(
            "radial side count must be a multiple of four and at least twelve"
        )
    if spec.rim_arc_segments < 4:
        raise ContainerTopologyError("rim arc requires at least four segments")
    if spec.body_axial_segments < 1:
        raise ContainerTopologyError("body axial segments must be positive")
    if spec.rim_style not in ("rolled", "flat_join"):
        raise ContainerTopologyError("rim style must be rolled or flat_join")


def _linear_profile(
    start: tuple[float, float],
    end: tuple[float, float],
    segments: int,
) -> tuple[tuple[float, float], ...]:
    return tuple(
        (
            start[0] + (end[0] - start[0]) * index / segments,
            start[1] + (end[1] - start[1]) * index / segments,
        )
        for index in range(segments + 1)
    )


def build_unified_cylindrical_vessel_mesh(
    spec: UnifiedCylindricalVesselSpec,
) -> UnifiedCylindricalVesselMesh:
    """Build a source-measured unified vessel in the style of liquid_0812.

    The generated surface represents the glass solid, not the liquid cavity:
    the underside and interior floor are capped while the top remains open.
    Its only faces are triangles, and the thickened rim is part of the same
    connected mesh as the wall and floor.
    """

    _validate_unified_vessel_spec(spec)
    outer_top_radius = spec.outer_top_radius or spec.outer_radius
    inner_top_radius = spec.inner_top_radius or spec.inner_radius
    if spec.rim_style == "rolled":
        arc_start = -math.pi / 6.0
        arc_span = 4.0 * math.pi / 3.0
        arc_step = arc_span / spec.rim_arc_segments
        join_z = spec.rim_center_z + spec.rim_vertical_radius * math.sin(arc_start)
        lip = tuple(
            (
                spec.rim_major_radius
                + spec.rim_radial_radius * math.cos(arc_start + index * arc_step),
                spec.rim_center_z
                + spec.rim_vertical_radius * math.sin(arc_start + index * arc_step),
            )
            for index in range(spec.rim_arc_segments + 1)
        )
        if lip[0][0] <= outer_top_radius or lip[-1][0] <= inner_top_radius:
            raise ContainerTopologyError(
                "rim profile must connect outside both measured vessel walls"
            )
        chord_error = max(spec.rim_radial_radius, spec.rim_vertical_radius) * (
            1.0 - math.cos(arc_step / 2.0)
        )
    else:
        join_z = spec.rim_center_z + spec.rim_vertical_radius
        lip = ()
        chord_error = 0.0
    outer_body = _linear_profile(
        (spec.outer_radius, spec.bottom_z),
        (
            spec.rim_major_radius + spec.rim_radial_radius
            if spec.rim_style == "flat_join"
            else outer_top_radius,
            join_z,
        ),
        spec.body_axial_segments,
    )
    inner_body = _linear_profile(
        (inner_top_radius, join_z),
        (spec.inner_radius, spec.floor_z),
        spec.body_axial_segments,
    )
    cross_section = (*outer_body, *lip, *inner_body)

    points: list[tuple[float, float, float]] = []
    for radius, height in cross_section:
        for index in range(spec.sides):
            angle = 2.0 * math.pi * index / spec.sides
            points.append(
                (radius * math.cos(angle), radius * math.sin(angle), height)
            )
    bottom_center = len(points)
    points.append((0.0, 0.0, spec.bottom_z))
    floor_center = len(points)
    points.append((0.0, 0.0, spec.floor_z))

    faces: list[tuple[int, int, int]] = []
    for ring in range(len(cross_section) - 1):
        left = ring * spec.sides
        right = (ring + 1) * spec.sides
        for index in range(spec.sides):
            nxt = (index + 1) % spec.sides
            faces.append((left + index, left + nxt, right + nxt))
            faces.append((left + index, right + nxt, right + index))
    first_ring = 0
    last_ring = (len(cross_section) - 1) * spec.sides
    for index in range(spec.sides):
        nxt = (index + 1) % spec.sides
        faces.append((bottom_center, first_ring + nxt, first_ring + index))
        faces.append((floor_center, last_ring + index, last_ring + nxt))

    counts = tuple(3 for _ in faces)
    indices = tuple(vertex for face in faces for vertex in face)
    audit = analyze_mesh_topology(counts, indices)
    if audit.boundary_edge_count or audit.non_manifold_edge_count:
        raise ContainerTopologyError(
            "unified vessel generation did not produce a closed manifold"
        )
    return UnifiedCylindricalVesselMesh(
        points=tuple(points),
        face_vertex_counts=counts,
        face_vertex_indices=indices,
        cross_section=tuple(cross_section),
        radial_side_count=spec.sides,
        cavity_radius=spec.inner_radius,
        cavity_floor_z=spec.floor_z,
        maximum_rim_chord_error_m=chord_error,
    )


def _triangulated_prism_faces(vertex_count_per_cap: int) -> tuple[int, ...]:
    if vertex_count_per_cap < 3:
        raise ContainerTopologyError("convex prism caps require at least three vertices")
    faces: list[tuple[int, int, int]] = []
    top = vertex_count_per_cap
    for index in range(1, vertex_count_per_cap - 1):
        faces.append((0, index + 1, index))
        faces.append((top, top + index, top + index + 1))
    for index in range(vertex_count_per_cap):
        nxt = (index + 1) % vertex_count_per_cap
        faces.append((index, nxt, top + nxt))
        faces.append((index, top + nxt, top + index))
    return tuple(vertex for face in faces for vertex in face)


def build_gpu_convex_vessel_partition(
    spec: UnifiedCylindricalVesselSpec,
    *,
    support_bottom_z: float | None = None,
    wall_segments: int = 31,
    wall_vertical_segments: int = 8,
    bottom_segments: int = 1,
    bottom_arc_subdivisions: int = 32,
    angular_phase_fraction: float = 0.25,
    reuse_rotated_wall_geometry: bool = False,
) -> GPUConvexVesselPartition:
    """Partition the measured vessel into deterministic GPU-convex pieces.

    This is a collision topology derived from the canonical visible surface,
    not a primitive proxy. Wall pieces use eight vertices and are split along
    height to avoid the GPU cooker's thin/tall convex failure. The default
    single bottom piece uses 64 vertices. Every authored face is a triangle.
    """

    _validate_unified_vessel_spec(spec)
    if support_bottom_z is None:
        support_bottom_z = spec.bottom_z
    if not math.isfinite(support_bottom_z) or support_bottom_z > spec.bottom_z:
        raise ContainerTopologyError(
            "support bottom must be finite and no higher than the vessel bottom"
        )
    if (
        wall_segments < 8
        or wall_vertical_segments < 1
        or bottom_segments < 1
        or bottom_arc_subdivisions < 3
    ):
        raise ContainerTopologyError("convex partition resolution is too low")
    if not 0.0 <= angular_phase_fraction < 1.0:
        raise ContainerTopologyError("angular phase fraction must be in [0, 1)")
    pieces: list[ConvexVesselPiece] = []
    wall_step = 2.0 * math.pi / wall_segments
    body_outer_top_radius = spec.outer_top_radius or spec.outer_radius
    inner_top_radius = spec.inner_top_radius or spec.inner_radius
    outer_top_radius = spec.rim_major_radius + spec.rim_radial_radius
    outer_top_z = spec.rim_center_z + spec.rim_vertical_radius
    wall_indices = _triangulated_prism_faces(4)
    wall_counts = tuple(3 for _ in range(len(wall_indices) // 3))
    phase = angular_phase_fraction * wall_step
    usable_height = outer_top_z - spec.floor_z
    for segment in range(wall_segments):
        if reuse_rotated_wall_geometry:
            angles = (-wall_step / 2.0, wall_step / 2.0)
            rotation = math.degrees(
                phase + (segment + 0.5) * wall_step
            )
            rotation = (rotation + 180.0) % 360.0 - 180.0
        else:
            angles = (
                phase + segment * wall_step,
                phase + (segment + 1) * wall_step,
            )
            rotation = 0.0
        for vertical in range(wall_vertical_segments):
            inner_lower_z = (
                spec.floor_z + usable_height * vertical / wall_vertical_segments
            )
            outer_lower_z = spec.bottom_z if vertical == 0 else inner_lower_z
            upper_z = (
                spec.floor_z
                + usable_height * (vertical + 1) / wall_vertical_segments
            )

            def outer_radius_at(z: float) -> float:
                fraction = (z - spec.bottom_z) / (outer_top_z - spec.bottom_z)
                body_fraction = min(
                    1.0,
                    fraction
                    * (outer_top_z - spec.bottom_z)
                    / (spec.rim_center_z - spec.bottom_z),
                )
                body_radius = spec.outer_radius + body_fraction * (
                    body_outer_top_radius - spec.outer_radius
                )
                if z <= spec.rim_center_z:
                    return body_radius
                rim_fraction = (z - spec.rim_center_z) / (
                    outer_top_z - spec.rim_center_z
                )
                return body_outer_top_radius + rim_fraction * (
                    outer_top_radius - body_outer_top_radius
                )

            def inner_radius_at(z: float) -> float:
                fraction = (z - spec.floor_z) / (outer_top_z - spec.floor_z)
                return spec.inner_radius + fraction * (
                    inner_top_radius - spec.inner_radius
                )

            cross_section = (
                (outer_radius_at(outer_lower_z), outer_lower_z),
                (outer_radius_at(upper_z), upper_z),
                (inner_radius_at(upper_z), upper_z),
                (inner_radius_at(inner_lower_z), inner_lower_z),
            )
            points = tuple(
                (
                    round(radius * math.cos(angle), 7),
                    round(radius * math.sin(angle), 7),
                    round(height, 7),
                )
                for angle in angles
                for radius, height in cross_section
            )
            pieces.append(
                ConvexVesselPiece(
                    name=f"wall_{segment:02d}_{vertical:02d}",
                    role="wall",
                    points=points,
                    face_vertex_counts=wall_counts,
                    face_vertex_indices=wall_indices,
                    rotation_z_degrees=rotation,
                )
            )

    bottom_step = 2.0 * math.pi / bottom_segments
    cap_vertex_count = (
        bottom_arc_subdivisions
        if bottom_segments == 1
        else bottom_arc_subdivisions + 2
    )
    bottom_indices = _triangulated_prism_faces(cap_vertex_count)
    bottom_counts = tuple(3 for _ in range(len(bottom_indices) // 3))
    for segment in range(bottom_segments):
        start = angular_phase_fraction * bottom_step + segment * bottom_step
        sample_count = (
            bottom_arc_subdivisions
            if bottom_segments == 1
            else bottom_arc_subdivisions + 1
        )
        angles = tuple(
            start + bottom_step * index / bottom_arc_subdivisions
            for index in range(sample_count)
        )
        perimeter = tuple(
            (
                spec.inner_radius * math.cos(angle),
                spec.inner_radius * math.sin(angle),
            )
            for angle in angles
        )
        cap_xy = perimeter if bottom_segments == 1 else ((0.0, 0.0),) + perimeter
        points = tuple(
            (round(x, 7), round(y, 7), round(height, 7))
            for height in (support_bottom_z, spec.floor_z)
            for x, y in cap_xy
        )
        pieces.append(
            ConvexVesselPiece(
                name=f"bottom_{segment:02d}",
                role="bottom",
                points=points,
                face_vertex_counts=bottom_counts,
                face_vertex_indices=bottom_indices,
            )
        )

    inner_wall_error = max(spec.inner_radius, inner_top_radius) * (
        1.0 - math.cos(wall_step / 2.0)
    )
    bottom_interval = bottom_step / bottom_arc_subdivisions
    bottom_error = spec.inner_radius * (1.0 - math.cos(bottom_interval / 2.0))
    return GPUConvexVesselPartition(
        pieces=tuple(pieces),
        wall_piece_count=wall_segments * wall_vertical_segments,
        bottom_piece_count=bottom_segments,
        maximum_surface_error_m=max(inner_wall_error, bottom_error),
    )
