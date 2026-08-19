"""Pure contracts and the pinned Task 02 r10.3 GPU-PBD liquid recipe.

USD and Isaac Sim imports deliberately live in :mod:`liquid_autofill_runtime`.
This module remains importable by ordinary Python tests and downstream contract
loaders.
"""

from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Mapping


AUTOFILL_REQUEST_SCHEMA = "aan.gpu_pbd_autofill_request.v1"
AUTOFILL_RESULT_SCHEMA = "aan.gpu_pbd_autofill_result.v1"
AUTOFILL_RECIPE_ID = "task02_r10_3_blue_gpu_pbd_v1"
MINIMUM_FILL = 0.10
MAXIMUM_FILL = 0.80
MAXIMUM_PARTICLES = 10_000
PARTICLE_SPACING_M = 0.00582


class LiquidAutofillError(ValueError):
    """Raised when a source cannot be promoted without guessing."""


def recipe_payload() -> dict[str, Any]:
    """Return the immutable effective recipe used by Task 02 r10.3.

    The r10.3 scene carries two stronger opinions over the older component:
    effective particle rest offset 9 mm and isosurface smoothing 5 mm.  They
    are recorded here as final composed values so consumers cannot accidentally
    copy the weaker r10.2 layer.
    """

    return {
        "schema_version": "aan.gpu_pbd_liquid_recipe.v1",
        "recipe_id": AUTOFILL_RECIPE_ID,
        "runtime": "isaac41",
        "particle_system": {
            "max_velocity_m_s": 0.3,
            "particle_contact_offset_m": 0.005,
            "effective_rest_offset_m": 0.009,
            "grid_filtering_passes": 1,
            "grid_smoothing_radius_m": 0.005,
            "mesh_smoothing_passes": 1,
            "surface_distance_m": 0.008,
        },
        "particle_set": {
            "width_m": 0.00594,
            "spacing_m": PARTICLE_SPACING_M,
            "mass_kg": 0.00045,
            "maximum_count": MAXIMUM_PARTICLES,
            "fluid": True,
            "self_collision": True,
        },
        "material": {
            "shader": "UsdPreviewSurface",
            "diffuse_color": [0.32, 0.72, 0.95],
            "ior": 1.333,
            "opacity": 0.34,
            "roughness": 0.02,
        },
        "collision": {
            "wall_and_rim": "sdf",
            "solid_base_and_connector": "convexHull",
            "hidden_closed_proxy_fallback": False,
            "parameter_search": False,
        },
        "evidence": {
            "particle_readback_attribute": "points",
            "authored_rest_state_attribute": "physxParticle:simulationPoints",
            "required_cold_runs": 3,
            "minimum_retention_ratio": 0.99,
            "settled_fill_ratio_tolerance": 0.05,
            "maximum_below_floor_count": 0,
            "maximum_translation_drift_m": 0.002,
            "maximum_tilt_drift_deg": 2.0,
        },
    }


def recipe_sha256() -> str:
    encoded = json.dumps(recipe_payload(), sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def build_request(*, scene: Path, container: str, fill: float) -> dict[str, Any]:
    return {
        "schema_version": AUTOFILL_REQUEST_SCHEMA,
        "scene": str(Path(scene).resolve()),
        "container_prim": str(container),
        "target_settled_fill_ratio": float(fill),
        "recipe_id": AUTOFILL_RECIPE_ID,
        "recipe_sha256": recipe_sha256(),
        "runtime": "isaac41",
        "limits": {
            "maximum_upright_error_deg": 15.0,
            "minimum_dominant_cavity_volume_ratio": 2.0,
            "maximum_particle_count": MAXIMUM_PARTICLES,
        },
    }


def validate_request(request: Mapping[str, Any]) -> None:
    if request.get("schema_version") != AUTOFILL_REQUEST_SCHEMA:
        raise LiquidAutofillError("unsupported autofill request schema")
    scene = Path(str(request.get("scene", "")))
    if not scene.is_file():
        raise LiquidAutofillError(f"source scene does not exist: {scene}")
    container = str(request.get("container_prim", ""))
    if not container.startswith("/") or container == "/" or "//" in container:
        raise LiquidAutofillError("container must be an absolute USD prim path")
    fill = float(request.get("target_settled_fill_ratio", -1.0))
    if not MINIMUM_FILL <= fill <= MAXIMUM_FILL:
        raise LiquidAutofillError("fill must be 0.10 through 0.80")
    if request.get("recipe_id") != AUTOFILL_RECIPE_ID:
        raise LiquidAutofillError("request does not select the pinned Task 02 recipe")
    if request.get("recipe_sha256") != recipe_sha256():
        raise LiquidAutofillError("request recipe hash does not match producer recipe")
    if request.get("runtime") != "isaac41":
        raise LiquidAutofillError("liquid autofill v1 supports Isaac Sim 4.1 only")


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise LiquidAutofillError("particle state is empty")
    index = (len(ordered) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def settled_fill_ratio(
    points: list[list[float]], cavity: Mapping[str, Any]
) -> float:
    floor = float(cavity["floor_m"])
    rim = float(cavity["rim_m"])
    if rim <= floor:
        raise LiquidAutofillError("cavity rim must be above its floor")
    return (_quantile([float(point[2]) for point in points], 0.95) - floor) / (
        rim - floor
    )


def build_particle_lattice(
    cavity: Mapping[str, Any], *, fill: float
) -> list[list[float]]:
    """Build one deterministic local-metre seed and align its q95 to ``fill``."""

    if not MINIMUM_FILL <= float(fill) <= MAXIMUM_FILL:
        raise LiquidAutofillError("fill must be 0.10 through 0.80")
    center_x, center_y = [float(value) for value in cavity["center_xy_m"]]
    radius_x = float(cavity["radius_x_m"])
    radius_y = float(cavity["radius_y_m"])
    floor = float(cavity["floor_m"])
    rim = float(cavity["rim_m"])
    spacing = PARTICLE_SPACING_M
    margin = 0.55 * spacing
    usable_x = radius_x - margin
    usable_y = radius_y - margin
    target_surface = floor + float(fill) * (rim - floor)
    if usable_x <= spacing or usable_y <= spacing or target_surface <= floor + spacing:
        raise LiquidAutofillError("detected cavity is too small for the Task 02 particle scale")

    points: list[list[float]] = []
    x = -usable_x
    layer = 0
    while x <= usable_x + 1e-9:
        y = -usable_y
        while y <= usable_y + 1e-9:
            if (x / usable_x) ** 2 + (y / usable_y) ** 2 <= 1.0:
                z = floor + 0.5 * spacing
                while z <= target_surface + 1e-9:
                    points.append(
                        [
                            round(center_x + x, 7),
                            round(center_y + y, 7),
                            round(z, 7),
                        ]
                    )
                    if len(points) > MAXIMUM_PARTICLES:
                        raise LiquidAutofillError(
                            "Task 02 particle scale would exceed the 10,000 particle budget"
                        )
                    z += spacing
                    layer += 1
            y += spacing
        x += spacing
    if not points:
        raise LiquidAutofillError("no particles fit inside the detected cavity")

    desired_q95 = target_surface
    shift = desired_q95 - _quantile([point[2] for point in points], 0.95)
    minimum = min(point[2] + shift for point in points)
    if minimum < floor:
        shift += floor - minimum
    return [
        [point[0], point[1], round(point[2] + shift, 7)] for point in points
    ]
