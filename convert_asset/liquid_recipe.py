"""Portable, hash-bound GPU-PBD liquid recipe loading."""

from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Mapping


RECIPE_SCHEMA = "aan.gpu_pbd_liquid_recipe.v1"


class LiquidRecipeError(ValueError):
    """Raised when a liquid recipe is incomplete or unsafe to reproduce."""


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LiquidRecipeError(f"{label} must be a mapping")
    return value


def _positive(value: object, label: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or float(value) <= 0
    ):
        raise LiquidRecipeError(f"{label} must be positive")
    return float(value)


def validate_liquid_recipe(value: Mapping[str, Any]) -> dict[str, Any]:
    payload = json.loads(json.dumps(value))
    if payload.get("schema_version") != RECIPE_SCHEMA:
        raise LiquidRecipeError("unsupported liquid recipe schema")
    if not str(payload.get("recipe_id", "")).strip():
        raise LiquidRecipeError("recipe_id is required")
    if payload.get("runtime") != "isaac41":
        raise LiquidRecipeError("liquid recipe runtime must be isaac41")
    system = _mapping(payload.get("particle_system"), "particle_system")
    particles = _mapping(payload.get("particle_set"), "particle_set")
    material = _mapping(payload.get("material"), "material")
    for key in (
        "max_velocity_m_s",
        "particle_contact_offset_m",
        "effective_rest_offset_m",
    ):
        _positive(system.get(key), f"particle_system.{key}")
    for key in ("spacing_m", "width_m", "mass_kg"):
        _positive(particles.get(key), f"particle_set.{key}")
    if int(particles.get("maximum_count", 0)) <= 0:
        raise LiquidRecipeError("particle_set.maximum_count must be positive")
    if material.get("shader") != "UsdPreviewSurface":
        raise LiquidRecipeError("only UsdPreviewSurface liquid material is supported")
    return payload


def load_liquid_recipe(path: str | Path) -> dict[str, Any]:
    recipe_path = Path(path)
    try:
        payload = json.loads(recipe_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiquidRecipeError(f"cannot read liquid recipe: {recipe_path}") from exc
    return validate_liquid_recipe(_mapping(payload, "liquid recipe"))


def liquid_recipe_sha256(recipe: Mapping[str, Any]) -> str:
    payload = validate_liquid_recipe(recipe)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()
