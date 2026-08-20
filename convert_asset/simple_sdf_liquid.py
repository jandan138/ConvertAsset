"""Pure contracts for the reviewed simple-SDF and multi-set liquid route.

USD and PhysX authoring deliberately live in ``simple_sdf_liquid_runtime`` so
ordinary schema tests do not import simulator modules.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import yaml


COLLISION_SCHEMA = "aan.simple_sdf_collision_spec.v1"
MULTI_LIQUID_SCHEMA = "aan.multi_liquid_sample_request.v1"
RESULT_SCHEMA = "aan.multi_liquid_sample_result.v1"
FLUID_ROOT = "/__ScenarioForgeFluid"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_SCALES = {"task02_compatible", "small_required"}


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
    sampler_mesh_prim: str
    sampler_usd: Path | None
    particle_scale: str
    preview_color: tuple[float, float, float] | None
    particle_group: int

    @property
    def particle_prim(self) -> str:
        return f"{FLUID_ROOT}/ParticleSets/{self.set_id}"


@dataclass(frozen=True)
class MultiLiquidRequest:
    path: Path
    scene: Path
    validation: str
    sets: tuple[LiquidSet, ...]


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
    if raw.get("schema_version") != MULTI_LIQUID_SCHEMA:
        raise SimpleSdfLiquidError("unsupported multi-liquid request schema")
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
        sampler_prim = _prim(value.get("sampler_mesh_prim"), "sampler_mesh_prim")
        sampler_usd_value = value.get("sampler_usd")
        sampler_usd = None
        if sampler_usd_value:
            sampler_usd = Path(str(sampler_usd_value))
            if not sampler_usd.is_absolute():
                sampler_usd = request_path.parent / sampler_usd
            sampler_usd = sampler_usd.resolve()
            if not sampler_usd.is_file():
                raise SimpleSdfLiquidError(f"sampler USD does not exist: {sampler_usd}")
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
                particle_scale=_scale(value.get("particle_scale")),
                preview_color=color,
                particle_group=group,
            )
        )
    return MultiLiquidRequest(request_path, scene, validation, tuple(sets))


def select_shared_recipe(sets: Sequence[LiquidSet]) -> dict[str, Any]:
    if any(item.particle_scale == "small_required" for item in sets):
        return {
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
                "ior": 1.333,
                "opacity": 0.34,
                "roughness": 0.02,
            },
        }
    from .liquid_autofill import recipe_payload

    recipe = recipe_payload()
    recipe["particle_set"]["maximum_count_per_set"] = recipe["particle_set"].pop(
        "maximum_count"
    )
    recipe["particle_set"]["maximum_count_total"] = 100_000
    return recipe


def evaluate_multi_set_runs(
    runs: Sequence[Mapping[str, Any]], *, set_ids: Sequence[str], mode: str
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
