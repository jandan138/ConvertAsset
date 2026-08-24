"""Pure contracts for the reviewed simple-SDF and multi-set liquid route.

USD and PhysX authoring deliberately live in ``simple_sdf_liquid_runtime`` so
ordinary schema tests do not import simulator modules.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import yaml


COLLISION_SCHEMA = "aan.simple_sdf_collision_spec.v1"
MULTI_LIQUID_SCHEMA = "aan.multi_liquid_sample_request.v1"
MULTI_LIQUID_SCHEMA_V2 = "aan.multi_liquid_sample_request.v2"
MULTI_LIQUID_SCHEMA_V3 = "aan.multi_liquid_sample_request.v3"
RESULT_SCHEMA = "aan.multi_liquid_sample_result.v1"
RESULT_SCHEMA_V2 = "aan.multi_liquid_sample_result.v2"
RESULT_SCHEMA_V3 = "aan.multi_liquid_sample_result.v3"
FLUID_ROOT = "/__ScenarioForgeFluid"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_SCALES = {"task02_compatible", "small_required"}
_AUTO_MODES = {"inside_fill", "mouth_drop"}


class SimpleSdfLiquidError(ValueError):
    """Raised when the simple path would need an unreviewed guess."""


@dataclass(frozen=True)
class BottomPlug:
    mode: str
    size_m: tuple[float, float, float] | None = None
    translate_local_m: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class CollisionContainer:
    container_id: str
    container_prim: str
    visual_mesh_prim: str
    particle_scale: str
    bottom_plug: BottomPlug


@dataclass(frozen=True)
class CollisionSpec:
    path: Path
    source_scene: Path
    containers: tuple[CollisionContainer, ...]


@dataclass(frozen=True)
class LiquidSet:
    set_id: str
    container_prim: str
    sampler_mesh_prim: str | None
    sampler_usd: Path | None
    sampler_mode: str
    fill_ratio: float | None
    visual_mesh_prim: str | None
    particle_scale: str
    preview_color: tuple[float, float, float] | None
    particle_group: int
    editable_axis: str | None = None

    @property
    def particle_prim(self) -> str:
        return f"{FLUID_ROOT}/ParticleSets/{self.set_id}"


@dataclass(frozen=True)
class MultiLiquidRequest:
    path: Path
    schema_version: str
    scene: Path
    validation: str
    sets: tuple[LiquidSet, ...]
    delivery_mode: str = "frozen_only"


@dataclass(frozen=True)
class AutoCylinderProfile:
    """Container-local metre dimensions for one generated sampler mesh."""

    mode: str
    center_xy_m: tuple[float, float]
    radius_x_m: float
    radius_y_m: float
    bottom_m: float
    top_m: float
    rim_m: float
    target_fill_ratio: float
    target_volume_m3: float
    initially_above_rim: bool

    @property
    def height_m(self) -> float:
        return self.top_m - self.bottom_m


def target_particle_count(*, target_volume_m3: float, spacing_m: float, limit: int) -> int:
    """Convert requested liquid volume to the established lattice count."""

    if min(float(target_volume_m3), float(spacing_m)) <= 0.0 or limit <= 0:
        raise SimpleSdfLiquidError("target volume, spacing, and particle limit must be positive")
    count = max(1, round(float(target_volume_m3) / float(spacing_m) ** 3))
    if count > limit:
        raise SimpleSdfLiquidError(
            f"automatic liquid needs {count} particles, above the per-set limit {limit}"
        )
    return count


def auto_cylinder_profile(
    cavity: Mapping[str, Any], *, mode: str, fill_ratio: float, spacing_m: float,
    opening: Mapping[str, Any] | None = None, particle_rest_offset_m: float = 0.0,
    capacity: Mapping[str, Any] | None = None,
) -> AutoCylinderProfile:
    """Turn one reviewed axial cavity into a safe closed sampler cylinder."""

    if mode not in _AUTO_MODES:
        raise SimpleSdfLiquidError(f"unsupported automatic sampler mode: {mode}")
    if not 0.10 <= float(fill_ratio) <= 0.80:
        raise SimpleSdfLiquidError("automatic fill_ratio must be 0.10 through 0.80")
    source = opening if mode == "mouth_drop" and opening is not None else cavity
    center = tuple(float(value) for value in source["center_xy_m"])
    radius_x = float(source["radius_x_m"])
    radius_y = float(source["radius_y_m"])
    floor = float(cavity["floor_m"])
    rim = float(source["rim_m"])
    if len(center) != 2 or min(radius_x, radius_y, spacing_m) <= 0.0 or rim <= floor:
        raise SimpleSdfLiquidError("detected cavity cannot define an automatic cylinder")

    # The volume sampler applies another 1.2-spacing inset to particle centres.
    # Shrinking the authored mouth projection by one spacing also keeps the
    # source column clear of imperfect visual/SDF rim estimates.
    if mode == "mouth_drop":
        # The authored mesh bounds particle centres, while the opening must
        # admit each particle's effective physical radius as well.
        clearance = max(float(spacing_m), float(particle_rest_offset_m))
        safe_x = radius_x - clearance
        safe_y = radius_y - clearance
    else:
        # The proven 15 mL sampler uses a two-spacing radial inset. Its source
        # points then receive the sampler's additional 1.2-spacing boundary
        # margin, keeping the initial lattice away from the SDF wall.
        safe_x = radius_x - 2.0 * float(spacing_m)
        safe_y = radius_y - 2.0 * float(spacing_m)
    if min(safe_x, safe_y) <= 1.2 * float(spacing_m):
        raise SimpleSdfLiquidError("container opening is too small for the selected particle scale")
    cavity_rim = float(cavity["rim_m"])
    target_surface = floor + float(fill_ratio) * (cavity_rim - floor)
    capacity_source = capacity or cavity
    target_volume = (
        math.pi
        * float(capacity_source["radius_x_m"])
        * float(capacity_source["radius_y_m"])
        * (target_surface - floor)
    )
    if mode == "inside_fill":
        # Match the proven narrow-tube loaded start: suspend a short column in
        # the upper cavity and let it settle, rather than authoring particles
        # against the floor. When the 5 mm effective rest radius dominates the
        # 1 mm lattice, apply the established 0.72 loaded-height correction.
        dense_small_regime = particle_rest_offset_m / spacing_m >= 4.0
        settling_scale = 0.72 if dense_small_regime else 1.0
        requested_height = (target_surface - floor) * settling_scale
        top = cavity_rim - max(float(particle_rest_offset_m), float(spacing_m))
        bottom = top - requested_height
        minimum_bottom = floor + max(float(particle_rest_offset_m), 1.2 * float(spacing_m))
        if bottom < minimum_bottom:
            bottom = minimum_bottom
        if top <= bottom:
            raise SimpleSdfLiquidError(
                "container is too short for a safely inset inside-fill sampler"
            )
        above = False
    else:
        bottom = rim + 1.2 * float(spacing_m)
        height = target_volume / (math.pi * safe_x * safe_y)
        top = bottom + height
        above = True
    return AutoCylinderProfile(
        mode=mode,
        center_xy_m=(center[0], center[1]),
        radius_x_m=safe_x,
        radius_y_m=safe_y,
        bottom_m=bottom,
        top_m=top,
        rim_m=rim,
        target_fill_ratio=float(fill_ratio),
        target_volume_m3=target_volume,
        initially_above_rim=above,
    )


def _load(path: Path) -> Mapping[str, Any]:
    source = Path(path).expanduser().resolve()
    try:
        value = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError, json.JSONDecodeError) as error:
        raise SimpleSdfLiquidError(f"cannot read request: {source}") from error
    if not isinstance(value, Mapping):
        raise SimpleSdfLiquidError("request must be a mapping")
    return value


def _prim(value: object, label: str) -> str:
    result = str(value or "")
    if not result.startswith("/") or result == "/" or "//" in result:
        raise SimpleSdfLiquidError(f"{label} must be an exact absolute prim path")
    return result


def _identifier(value: object, seen: set[str]) -> str:
    result = str(value or "")
    if not _ID.fullmatch(result) or result in seen:
        raise SimpleSdfLiquidError("ids must be unique USD-safe identifiers")
    seen.add(result)
    return result


def _scale(value: object) -> str:
    result = str(value or "task02_compatible")
    if result not in _SCALES:
        raise SimpleSdfLiquidError(f"unsupported particle_scale: {result}")
    return result


def _vec3(value: object, label: str, *, positive: bool = False) -> tuple[float, float, float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 3:
        raise SimpleSdfLiquidError(f"{label} must have exactly three numbers")
    result = tuple(float(item) for item in value)
    if positive and any(item <= 0 for item in result):
        raise SimpleSdfLiquidError(f"{label} values must be positive")
    return result


def load_approved_collision_spec(path: Path) -> CollisionSpec:
    spec_path = Path(path).expanduser().resolve()
    raw = _load(spec_path)
    if raw.get("schema_version") != COLLISION_SCHEMA:
        raise SimpleSdfLiquidError("unsupported simple-SDF collision schema")
    scene = Path(str(raw.get("source_scene", "")))
    if not scene.is_absolute():
        scene = spec_path.parent / scene
    scene = scene.resolve()
    if not scene.is_file():
        raise SimpleSdfLiquidError(f"source scene does not exist: {scene}")
    values = raw.get("containers")
    if not isinstance(values, list) or not values:
        raise SimpleSdfLiquidError("containers must not be empty")
    seen: set[str] = set()
    containers: list[CollisionContainer] = []
    for value in values:
        if not isinstance(value, Mapping):
            raise SimpleSdfLiquidError("container entry must be a mapping")
        plug_raw = value.get("bottom_plug", {"mode": "none"})
        if not isinstance(plug_raw, Mapping):
            raise SimpleSdfLiquidError("bottom_plug must be a mapping")
        mode = str(plug_raw.get("mode", "none"))
        if mode == "none":
            plug = BottomPlug(mode="none")
        elif mode == "approved_cube":
            if plug_raw.get("approved") is not True:
                raise SimpleSdfLiquidError("bottom plug must be explicitly approved")
            plug = BottomPlug(
                mode=mode,
                size_m=_vec3(plug_raw.get("size_m"), "bottom plug size", positive=True),
                translate_local_m=_vec3(
                    plug_raw.get("translate_local_m"), "bottom plug translation"
                ),
            )
        else:
            raise SimpleSdfLiquidError(f"unsupported bottom plug mode: {mode}")
        containers.append(
            CollisionContainer(
                container_id=_identifier(value.get("id"), seen),
                container_prim=_prim(value.get("container_prim"), "container_prim"),
                visual_mesh_prim=_prim(value.get("visual_mesh_prim"), "visual_mesh_prim"),
                particle_scale=_scale(value.get("particle_scale")),
                bottom_plug=plug,
            )
        )
    return CollisionSpec(spec_path, scene, tuple(containers))


def load_multi_liquid_request(path: Path) -> MultiLiquidRequest:
    request_path = Path(path).expanduser().resolve()
    raw = _load(request_path)
    schema_version = str(raw.get("schema_version", ""))
    if schema_version not in {
        MULTI_LIQUID_SCHEMA,
        MULTI_LIQUID_SCHEMA_V2,
        MULTI_LIQUID_SCHEMA_V3,
    }:
        raise SimpleSdfLiquidError("unsupported multi-liquid request schema")
    delivery_mode = str(raw.get("delivery_mode", "frozen_only"))
    if schema_version == MULTI_LIQUID_SCHEMA_V3:
        if delivery_mode != "dual_editable_frozen":
            raise SimpleSdfLiquidError(
                "v3 delivery_mode must be dual_editable_frozen"
            )
    elif delivery_mode != "frozen_only":
        raise SimpleSdfLiquidError("editable delivery requires the v3 request schema")
    scene = Path(str(raw.get("scene", "")))
    if not scene.is_absolute():
        scene = request_path.parent / scene
    scene = scene.resolve()
    if not scene.is_file():
        raise SimpleSdfLiquidError(f"source scene does not exist: {scene}")
    validation = str(raw.get("validation", "quick"))
    if validation not in {"quick", "qualified"}:
        raise SimpleSdfLiquidError("validation must be quick or qualified")
    values = raw.get("sets")
    if not isinstance(values, list) or not values:
        raise SimpleSdfLiquidError("sets must not be empty")
    seen: set[str] = set()
    sets: list[LiquidSet] = []
    samplers: set[tuple[str, str]] = set()
    for group, value in enumerate(values):
        if not isinstance(value, Mapping):
            raise SimpleSdfLiquidError("set entry must be a mapping")
        set_id = _identifier(value.get("id"), seen)
        sampler_mode = "explicit_mesh"
        fill_ratio = None
        visual_mesh_prim = None
        sampler_prim: str | None = None
        sampler_raw = value.get("sampler")
        if sampler_raw is not None:
            if schema_version not in {
                MULTI_LIQUID_SCHEMA_V2,
                MULTI_LIQUID_SCHEMA_V3,
            } or not isinstance(sampler_raw, Mapping):
                raise SimpleSdfLiquidError(
                    "automatic sampler requires the v2 or v3 request schema"
                )
            sampler_mode = str(sampler_raw.get("mode", ""))
            if sampler_mode not in _AUTO_MODES:
                raise SimpleSdfLiquidError(f"unsupported automatic sampler mode: {sampler_mode}")
            fill_ratio = float(sampler_raw.get("fill_ratio", -1.0))
            if not 0.10 <= fill_ratio <= 0.80:
                raise SimpleSdfLiquidError("automatic fill_ratio must be 0.10 through 0.80")
            visual_value = sampler_raw.get("visual_mesh_prim")
            if visual_value is not None:
                visual_mesh_prim = _prim(visual_value, "visual_mesh_prim")
            editable_axis = sampler_raw.get("editable_axis")
            if schema_version == MULTI_LIQUID_SCHEMA_V3:
                if editable_axis != "height_z":
                    raise SimpleSdfLiquidError(
                        "v3 automatic sampler editable_axis must be height_z"
                    )
            elif editable_axis is not None:
                raise SimpleSdfLiquidError(
                    "editable_axis requires the v3 request schema"
                )
        else:
            sampler_prim = _prim(value.get("sampler_mesh_prim"), "sampler_mesh_prim")
            editable_axis = None
        sampler_usd_value = value.get("sampler_usd")
        sampler_usd = None
        if sampler_mode != "explicit_mesh" and sampler_usd_value:
            raise SimpleSdfLiquidError("automatic sampler cannot also provide sampler_usd")
        if sampler_usd_value:
            sampler_usd = Path(str(sampler_usd_value))
            if not sampler_usd.is_absolute():
                sampler_usd = request_path.parent / sampler_usd
            sampler_usd = sampler_usd.resolve()
            if not sampler_usd.is_file():
                raise SimpleSdfLiquidError(f"sampler USD does not exist: {sampler_usd}")
        if sampler_prim is not None:
            key = (str(sampler_usd or scene), sampler_prim)
            if key in samplers:
                raise SimpleSdfLiquidError("each sampler mesh must map to exactly one ParticleSet")
            samplers.add(key)
        color_value = value.get("preview_color")
        color = _vec3(color_value, "preview_color") if color_value is not None else None
        sets.append(
            LiquidSet(
                set_id=set_id,
                container_prim=_prim(value.get("container_prim"), "container_prim"),
                sampler_mesh_prim=sampler_prim,
                sampler_usd=sampler_usd,
                sampler_mode=sampler_mode,
                fill_ratio=fill_ratio,
                visual_mesh_prim=visual_mesh_prim,
                particle_scale=_scale(value.get("particle_scale")),
                preview_color=color,
                particle_group=group,
                editable_axis=(str(editable_axis) if editable_axis else None),
            )
        )
    return MultiLiquidRequest(
        request_path,
        schema_version,
        scene,
        validation,
        tuple(sets),
        delivery_mode,
    )


def select_shared_recipe(sets: Sequence[LiquidSet]) -> dict[str, Any]:
    if any(item.particle_scale == "small_required" for item in sets):
        recipe = {
            "schema_version": "aan.gpu_pbd_liquid_recipe.v1",
            "recipe_id": "colleague_small_gpu_pbd_v1",
            "runtime": "isaac41",
            "particle_system": {
                "max_velocity_m_s": 0.2,
                "particle_contact_offset_m": 0.001,
                "effective_rest_offset_m": 0.005,
                "grid_filtering_passes": 1,
                "grid_smoothing_radius_m": 0.005,
                "mesh_smoothing_passes": 1,
                "surface_distance_m": 0.008,
            },
            "particle_set": {
                "spacing_m": 0.001,
                "width_m": 0.001188,
                "mass_kg": 0.00045 * (0.001 / 0.00582) ** 3,
                "maximum_count_per_set": 50_000,
                "maximum_count_total": 100_000,
                "fluid": True,
                "self_collision": True,
            },
            "material": {
                "shader": "UsdPreviewSurface",
                "diffuse_color": [0.32, 0.72, 0.95],
                "emissive_color": [0.02, 0.12, 0.28],
                "ior": 1.333,
                "opacity": 0.34,
                "roughness": 0.02,
            },
        }
        if any(item.sampler_mode == "mouth_drop" for item in sets):
            recipe["recipe_id"] = "colleague_small_gpu_pbd_mouth_drop_v1"
            recipe["particle_system"]["max_velocity_m_s"] = 0.05
        return recipe
    from .liquid_autofill import recipe_payload

    recipe = recipe_payload()
    recipe["material"]["emissive_color"] = [0.02, 0.12, 0.28]
    recipe["particle_set"]["maximum_count_per_set"] = recipe["particle_set"].pop(
        "maximum_count"
    )
    recipe["particle_set"]["maximum_count_total"] = 100_000
    if any(item.sampler_mode == "mouth_drop" for item in sets):
        recipe["recipe_id"] = "task02_r10_3_blue_gpu_pbd_mouth_drop_v1"
        recipe["particle_system"]["max_velocity_m_s"] = 0.05
    return recipe


def evaluate_multi_set_runs(
    runs: Sequence[Mapping[str, Any]], *, set_ids: Sequence[str], mode: str,
    target_fill_ratios: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    required = 1 if mode == "quick" else 3
    blockers: list[str] = []
    if len(runs) != required:
        blockers.append(f"expected_{required}_cold_runs")
    for index, run in enumerate(runs):
        if run.get("hard_errors"):
            blockers.append(f"run_{index}:hard_runtime_error")
        observed = run.get("sets")
        if not isinstance(observed, Mapping):
            blockers.append(f"run_{index}:missing_per_set_readback")
            continue
        for set_id in set_ids:
            item = observed.get(set_id)
            if not isinstance(item, Mapping):
                blockers.append(f"{set_id}:missing_readback")
                continue
            if float(item.get("retention_ratio", 0.0)) < 0.99:
                blockers.append(f"{set_id}:retention_below_0.99")
            if int(item.get("below_floor_count", 1)) != 0:
                blockers.append(f"{set_id}:below_floor_or_leak")
            if target_fill_ratios and set_id in target_fill_ratios:
                measured = item.get("settled_fill_ratio")
                if measured is None or abs(float(measured) - target_fill_ratios[set_id]) > 0.05:
                    blockers.append(f"{set_id}:settled_fill_ratio_outside_0.05")
    blockers = list(dict.fromkeys(blockers))
    return {
        "overall_status": "pass" if not blockers else "blocked",
        "blocked_reasons": blockers,
        "validation": mode,
        "claim": (
            "qualified_gpu_pbd_loaded_start"
            if not blockers and mode == "qualified"
            else "provisional_gpu_pbd_loaded_start"
            if not blockers
            else None
        ),
        "robot_policy_success": False,
        "benchmark_success": False,
    }
