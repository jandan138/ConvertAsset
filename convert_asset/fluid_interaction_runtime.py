"""USD-aware proposal and package production for fluid-interaction assets."""

from __future__ import annotations

from hashlib import sha256
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import yaml

from .fluid_interaction_asset import (
    PROPOSAL_SCHEMA,
    PROFILE_SCHEMA,
    file_sha256,
    evaluate_qualification_runs,
    load_approved_proposal,
    normalized_collision_presets,
    qualification_policy,
)
from .liquid_recipe import (
    liquid_recipe_sha256,
    load_liquid_recipe,
    validate_liquid_recipe,
)
from .asset_application_normalizer.visual_material_profile import (
    _mdl_overlay_text,
    load_visual_material_profile,
)


_SOLID_HINTS = ("bottom", "base", "connector", "foot", "pedestal", "spout")
_RIM_HINTS = ("rim", "lip")
_WALL_HINTS = ("hollow", "wall", "body", "shell")


def _existing_interaction_profile(source: Path, scope_prim: str) -> dict[str, Any] | None:
    path = source.parent / "interaction/profile.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("asset_entry_prim") != scope_prim:
        return None
    return payload


def _slug(value: str) -> str:
    return "_".join(part for part in value.lower().replace("-", "_").split("_") if part)


def _suggest_behavior(scope_prim: str) -> str:
    name = scope_prim.rsplit("/", 1)[-1].lower()
    if "funnel" in name:
        return "conduit"
    if "rod" in name or "stick" in name:
        return "surface_guide"
    return "reservoir"


def _mesh_records(
    source: Path, scope_prim: str, *, axis_local: list[float]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from pxr import Gf, Usd, UsdGeom  # type: ignore

    stage = Usd.Stage.Open(str(source))
    if stage is None:
        raise ValueError(f"cannot open USD: {source}")
    target = stage.GetPrimAtPath(scope_prim)
    if not target.IsValid() or not target.IsActive():
        raise ValueError(f"scope prim does not exist or is inactive: {scope_prim}")
    cache = UsdGeom.XformCache()
    target_world = cache.GetLocalToWorldTransform(target)
    target_inverse = target_world.GetInverse()
    points: list[tuple[float, float, float]] = []
    meshes: list[dict[str, Any]] = []
    cavity_candidates: list[dict[str, Any]] = []
    dominant = max(range(3), key=lambda index: abs(axis_local[index]))
    radial_axes = [index for index in range(3) if index != dominant]
    direction = 1.0 if axis_local[dominant] >= 0 else -1.0
    for prim in Usd.PrimRange(target):
        if not prim.IsActive() or not prim.IsA(UsdGeom.Mesh):
            continue
        mesh = UsdGeom.Mesh(prim)
        local = mesh.GetPointsAttr().Get() or []
        to_target = cache.GetLocalToWorldTransform(prim) * target_inverse
        transformed = [to_target.Transform(Gf.Vec3d(item)) for item in local]
        if not transformed:
            continue
        points.extend((float(item[0]), float(item[1]), float(item[2])) for item in transformed)
        name = prim.GetName().lower()
        if any(hint in name for hint in _RIM_HINTS):
            role, approximation = "rim", "sdf"
        elif any(hint in name for hint in _SOLID_HINTS):
            role, approximation = next(
                ((hint, "convexHull") for hint in _SOLID_HINTS if hint in name),
                ("base", "convexHull"),
            )
        elif any(hint in name for hint in _WALL_HINTS):
            role, approximation = "wall", "sdf"
        else:
            role, approximation = "ignore", "none"
        meshes.append(
            {
                "prim_path": prim.GetPath().pathString,
                "role": role,
                "approximation": approximation,
                "point_count": len(transformed),
            }
        )
        canonical = [
            [
                float(item[radial_axes[0]]),
                float(item[radial_axes[1]]),
                float(item[dominant]) * direction,
            ]
            for item in transformed
        ]
        try:
            from .liquid_autofill_runtime import _mesh_cavity_candidate

            candidate = _mesh_cavity_candidate(
                canonical, prim_path=prim.GetPath().pathString
            )
        except Exception:
            candidate = None
        if candidate is not None:
            cavity_candidates.append(candidate)
    if not points:
        # A transform-only source is still useful for proposal and contract
        # tests, but cannot claim measured geometry.
        bounds = {"minimum_m": [-0.005, -0.005, 0.0], "maximum_m": [0.005, 0.005, 0.1]}
        minimum_radius = 0.005
    else:
        minimum = [min(point[index] for point in points) for index in range(3)]
        maximum = [max(point[index] for point in points) for index in range(3)]
        spans = [maximum[index] - minimum[index] for index in range(3)]
        minimum_radius = max(0.001, 0.42 * min(spans[0], spans[1]) * 0.5)
        bounds = {"minimum_m": minimum, "maximum_m": maximum}
    summary: dict[str, Any] = {
        "axis_local": axis_local,
        "bounds": bounds,
        "minimum_clearance_radius_m": round(minimum_radius, 7),
    }
    semantic_candidates = [
        item
        for item in cavity_candidates
        if any(hint in str(item["prim_path"]).lower() for hint in _WALL_HINTS)
    ]
    if len(semantic_candidates) == 1:
        summary["cavity"] = semantic_candidates[0]
    elif cavity_candidates:
        summary["cavity"] = max(
            cavity_candidates, key=lambda item: float(item["estimated_volume_m3"])
        )
    if "cavity" in summary:
        summary["minimum_clearance_radius_m"] = round(
            min(
                float(summary["cavity"]["radius_x_m"]),
                float(summary["cavity"]["radius_y_m"]),
            ),
            7,
        )
    # Reuse the already proven hollow-wall analyzer whenever the package axis
    # is Z.  It independently separates inner and outer wall samples and is
    # substantially more accurate than an outer bbox estimate.
    if axis_local == [0.0, 0.0, 1.0]:
        try:
            from .liquid_autofill_runtime import analyze_container

            cavity = analyze_container(source, scope_prim)["cavity"]
        except Exception:
            cavity = None
        if cavity is not None:
            summary["cavity"] = cavity
            summary["minimum_clearance_radius_m"] = round(
                min(float(cavity["radius_x_m"]), float(cavity["radius_y_m"])), 7
            )
    return meshes, summary


def _lower_throat_radius(source: Path, scope_prim: str, axis_local: list[float]) -> float | None:
    """Measure the lower-quarter inner wall radius of a straight conduit."""

    from pxr import Gf, Usd, UsdGeom  # type: ignore

    stage = Usd.Stage.Open(str(source))
    target = stage.GetPrimAtPath(scope_prim) if stage is not None else None
    if target is None or not target.IsValid():
        return None
    cache = UsdGeom.XformCache()
    inverse = cache.GetLocalToWorldTransform(target).GetInverse()
    dominant = max(range(3), key=lambda index: abs(axis_local[index]))
    other = [index for index in range(3) if index != dominant]
    samples: list[tuple[float, float]] = []
    for prim in Usd.PrimRange(target):
        if not prim.IsA(UsdGeom.Mesh) or not prim.IsActive():
            continue
        matrix = cache.GetLocalToWorldTransform(prim) * inverse
        for raw in UsdGeom.Mesh(prim).GetPointsAttr().Get() or []:
            point = matrix.Transform(Gf.Vec3d(raw))
            axial = float(point[dominant]) * (1.0 if axis_local[dominant] >= 0 else -1.0)
            radius = math.hypot(float(point[other[0]]), float(point[other[1]]))
            samples.append((axial, radius))
    if not samples:
        return None
    lower, upper = min(item[0] for item in samples), max(item[0] for item in samples)
    radii = sorted(
        radius
        for axial, radius in samples
        if lower <= axial <= lower + 0.25 * (upper - lower) and radius > 1e-6
    )
    if not radii:
        return None
    return radii[len(radii) // 4]


def _svg(path: Path, *, title: str, lines: list[str], colors: list[str]) -> None:
    height = 90 + 34 * len(lines)
    rows = []
    for index, line in enumerate(lines):
        y = 72 + 34 * index
        color = colors[index % len(colors)]
        rows.append(
            f'<rect x="24" y="{y - 19}" width="18" height="18" rx="3" fill="{color}"/>'
            f'<text x="54" y="{y - 4}" font-size="14" fill="#dce7f3">{line}</text>'
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" '
        f'viewBox="0 0 900 {height}"><rect width="900" height="{height}" fill="#101820"/>'
        f'<text x="24" y="36" font-size="22" font-family="sans-serif" fill="#ffffff">{title}</text>'
        f'<g font-family="monospace">{"".join(rows)}</g></svg>\n',
        encoding="utf-8",
    )


def propose_fluid_interaction(*, source: Path, scope_prim: str, output: Path) -> Path:
    source = Path(source).resolve()
    output = Path(output).resolve()
    if not source.is_file():
        raise ValueError(f"source USD does not exist: {source}")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite proposal: {output}")
    behavior = _suggest_behavior(scope_prim)
    existing_profile = _existing_interaction_profile(source, scope_prim)
    declared_axis = (
        existing_profile.get("open_top", {}).get("axis_body_local")
        if existing_profile is not None
        else None
    )
    axis_local = (
        [float(value) for value in declared_axis]
        if isinstance(declared_axis, list) and len(declared_axis) == 3
        else [0.0, 0.0, 1.0]
    )
    meshes, geometry_summary = _mesh_records(
        source, scope_prim, axis_local=axis_local
    )
    if behavior == "conduit":
        throat = _lower_throat_radius(source, scope_prim, axis_local)
        if throat is not None:
            geometry_summary["minimum_clearance_radius_m"] = round(throat, 7)
            geometry_summary["conduit_throat_radius_m"] = round(throat, 7)
            from .liquid_autofill import recipe_payload

            effective_diameter = 2.0 * float(
                recipe_payload()["particle_system"]["effective_rest_offset_m"]
            )
            geometry_summary["recipe_compatibility"] = {
                "recipe_id": "task02_r10_3_blue_gpu_pbd_v1",
                "measured_throat_diameter_m": round(2.0 * throat, 7),
                "minimum_effective_particle_diameter_m": round(
                    effective_diameter, 7
                ),
                "status": (
                    "compatible" if 2.0 * throat >= effective_diameter else "blocked"
                ),
                "blocked_reason": (
                    None
                    if 2.0 * throat >= effective_diameter
                    else "particle_throat_incompatible"
                ),
            }
    elif behavior == "surface_guide":
        bounds = geometry_summary["bounds"]
        dominant = max(range(3), key=lambda index: abs(axis_local[index]))
        radial_spans = [
            bounds["maximum_m"][index] - bounds["minimum_m"][index]
            for index in range(3)
            if index != dominant
        ]
        geometry_summary["minimum_clearance_radius_m"] = round(
            0.5 * min(radial_spans), 7
        )
    if behavior == "surface_guide":
        for item in meshes:
            item.update({"role": "guide_surface", "approximation": "sdf"})
    elif meshes and not any(item["role"] != "ignore" for item in meshes):
        # Monolithic visual geometry starts with a direct SDF fast path.  If
        # qualification fails, the review report requests a derived partition.
        meshes[0].update({"role": "wall", "approximation": "sdf"})
    output.mkdir(parents=True)
    dominant_index = max(range(3), key=lambda index: abs(axis_local[index]))
    direction = 1.0 if axis_local[dominant_index] >= 0 else -1.0
    axis_values = [
        geometry_summary["bounds"][key][dominant_index] * direction
        for key in ("minimum_m", "maximum_m")
    ]
    zmin, zmax = min(axis_values), max(axis_values)
    named_frames = (
        existing_profile.get("named_frames", {}) if existing_profile is not None else {}
    )
    def _frame_position(name: str, fallback: list[float]) -> list[float]:
        record = named_frames.get(name)
        if isinstance(record, dict):
            values = record.get("translation_body_local_usd")
            if isinstance(values, list) and len(values) == 3:
                return [float(value) for value in values]
        return fallback
    frames: dict[str, Any]
    if behavior == "conduit":
        frames = {
            "inlet": {"position_m": _frame_position("opening", [0.0, 0.0, zmax])},
            "outlet": {"position_m": _frame_position("outlet", [0.0, 0.0, zmin])},
        }
    elif behavior == "surface_guide":
        frames = {
            "guide_start": {"position_m": [0.0, 0.0, zmax]},
            "guide_end": {"position_m": [0.0, 0.0, zmin]},
        }
    else:
        frames = {
            "opening": {
                "position_m": _frame_position(
                    "opening", _frame_position("mouth", [0.0, 0.0, zmax])
                )
            },
            "floor": {"position_m": _frame_position("support", [0.0, 0.0, zmin])},
        }
    proposal = {
        "schema_version": PROPOSAL_SCHEMA,
        "source_binding": {
            "source_usd": str(source),
            "source_sha256": file_sha256(source),
            "scope_prim": scope_prim,
        },
        "behavior": {"suggested": behavior, "confirmed": None},
        "geometry": {
            **geometry_summary,
            "model": (
                "straight_external_surface"
                if behavior == "surface_guide"
                else "single_axis_single_connected_cavity"
            ),
            "roles": meshes,
            "frames": frames,
            "fallback": {
                "on_fast_path_failure": "derive_package_local_collision_partitions",
                "requires_second_review": True,
            },
        },
        "collision_parameter_presets": normalized_collision_presets(
            geometry_summary["minimum_clearance_radius_m"]
        ),
        "physics": {
            "material_class": "glass",
            "mass_source": "provisional_geometry",
            "density_kg_m3": 2500.0,
        },
        "qualification_policy": qualification_policy(behavior),
        "review": {"status": "pending", "reviewer": None, "notes": None},
    }
    proposal_path = output / "proposal.yaml"
    proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
    role_lines = [
        f'{item["role"]:14s} {item["approximation"]:10s} {item["prim_path"]}'
        for item in meshes
    ] or ["no authored mesh found — review required"]
    _svg(
        output / "evidence/geometry_roles.svg",
        title="Fluid interaction geometry roles",
        lines=role_lines,
        colors=["#3ec6e0", "#f5b642", "#ef6f6c", "#7bd389"],
    )
    _svg(
        output / "evidence/axial_sections.svg",
        title="Single-axis cavity / guide review",
        lines=[
            f"behavior suggestion: {behavior}",
            f"z range: {zmin:.6f} m .. {zmax:.6f} m",
            f'minimum clearance radius: {geometry_summary["minimum_clearance_radius_m"]:.6f} m',
            "human confirmation required before qualification",
        ],
        colors=["#3ec6e0"],
    )
    report = {
        "schema_version": "aan.fluid_interaction_proposal_report.v1",
        "status": "review_required",
        "proposal": "proposal.yaml",
        "evidence": ["evidence/geometry_roles.svg", "evidence/axial_sections.svg"],
    }
    (output / "proposal_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return proposal_path


def _radial_partition_stations(
    source: Path, scope_prim: str, axis_local: list[float]
) -> list[dict[str, float]]:
    """Recover conservative inner/outer radii for an axisymmetric shell."""

    from pxr import Gf, Usd, UsdGeom  # type: ignore

    stage = Usd.Stage.Open(str(source))
    target = stage.GetPrimAtPath(scope_prim) if stage is not None else None
    if target is None or not target.IsValid():
        raise ValueError("cannot open source scope for partition derivation")
    cache = UsdGeom.XformCache()
    inverse = cache.GetLocalToWorldTransform(target).GetInverse()
    dominant = max(range(3), key=lambda index: abs(axis_local[index]))
    radial = [index for index in range(3) if index != dominant]
    direction = 1.0 if axis_local[dominant] >= 0 else -1.0
    samples: list[tuple[float, float]] = []
    for prim in Usd.PrimRange(target):
        if not prim.IsActive() or not prim.IsA(UsdGeom.Mesh):
            continue
        matrix = cache.GetLocalToWorldTransform(prim) * inverse
        for raw in UsdGeom.Mesh(prim).GetPointsAttr().Get() or []:
            point = matrix.Transform(Gf.Vec3d(raw))
            samples.append(
                (
                    float(point[dominant]) * direction,
                    math.hypot(float(point[radial[0]]), float(point[radial[1]])),
                )
            )
    if len(samples) < 16:
        raise ValueError("not enough source samples for derived partitions")
    lower = min(item[0] for item in samples)
    upper = max(item[0] for item in samples)
    stations: list[dict[str, float]] = []
    for index in range(13):
        center = lower + (upper - lower) * index / 12.0
        half_band = max((upper - lower) / 24.0, 1e-6)
        radii = sorted(
            radius for axial, radius in samples if abs(axial - center) <= half_band
        )
        if len(radii) < 4:
            continue
        inner = radii[max(0, int(0.20 * (len(radii) - 1)))]
        outer = radii[min(len(radii) - 1, int(0.80 * (len(radii) - 1)))]
        if outer <= inner + 0.0002:
            outer = max(radii)
        if outer <= inner + 0.0002:
            continue
        stations.append(
            {
                "z_m": round(center, 7),
                "inner_radius_m": round(inner, 7),
                "outer_radius_m": round(outer, 7),
            }
        )
    if len(stations) < 3:
        raise ValueError("could not recover a usable axial shell profile")
    return stations


def derive_partition_proposal(*, proposal_path: Path, output: Path) -> Path:
    """Create a second-review proposal with package-local convex wall pieces."""

    approved = load_approved_proposal(proposal_path)
    destination = Path(output).resolve()
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite proposal: {destination}")
    payload = yaml.safe_load(Path(proposal_path).read_text(encoding="utf-8"))
    axis = [float(value) for value in payload["geometry"]["axis_local"]]
    stations = _radial_partition_stations(
        approved.source_usd, approved.scope_prim, axis
    )
    payload["geometry"]["partition_model"] = {
        "kind": "axisymmetric_convex_wall_segments",
        "angular_segments": 24,
        "stations": stations,
        "source_visual_mesh_unchanged": True,
    }
    payload["geometry"]["fallback"]["selected"] = "derived_partitions"
    payload["geometry"]["roles"] = [
        {
            "prim_path": "/FluidInteractionAsset/__aan_fluid_collision_partitions",
            "role": "partition_wall",
            "approximation": "convexHull",
            "derived": True,
        }
    ]
    payload["review"] = {
        "status": "pending",
        "reviewer": None,
        "notes": "Second review: inspect derived axial stations before qualification.",
        "round": 2,
        "parent_proposal_sha256": file_sha256(Path(proposal_path)),
    }
    destination.mkdir(parents=True)
    derived = destination / "proposal.yaml"
    derived.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    _svg(
        destination / "evidence/derived_partition_stations.svg",
        title="Derived convex wall partition stations",
        lines=[
            f'z={item["z_m"]:.5f} inner={item["inner_radius_m"]:.5f} outer={item["outer_radius_m"]:.5f}'
            for item in stations
        ],
        colors=["#f5b642", "#3ec6e0"],
    )
    return derived


def build_unqualified_asset_package(
    *,
    proposal_path: Path,
    output: Path,
    liquid_recipe_path: Path | None = None,
    visual_material_profile_path: Path | None = None,
) -> Path:
    """Build a diagnostics-only package; formal pass requires runtime evidence."""

    proposal = load_approved_proposal(proposal_path)
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite package: {output}")
    output.mkdir(parents=True)
    source_dir = output / "deps/source_package"
    if proposal.source_usd.name == "asset.usd" and (
        proposal.source_usd.parent / "evidence/manifest.json"
    ).is_file():
        shutil.copytree(proposal.source_usd.parent, source_dir)
        source_copy = source_dir / "asset.usd"
    else:
        from .asset_application_normalizer.model import NormalizeAssetRequest
        from .asset_application_normalizer.usd_closure import (
            build_usd_closure_package,
        )

        closure = build_usd_closure_package(
            NormalizeAssetRequest(
                source_usd=proposal.source_usd,
                out_dir=source_dir,
                asset_id="FluidInteractionSourceClosure",
                asset_class="fluid_interaction_source",
                source_runtime="generic_usd",
                target_runtime="isaac41",
                target_benchmark="scenario-forge",
                task_id="scenario_forge.fluid_interaction_asset",
                asset_role="dynamic",
                required_prims=[proposal.scope_prim],
                asset_scope_prims=[proposal.scope_prim],
                gates=["static"],
            )
        )
        if closure.overall_status != "pass":
            raise ValueError(
                f"raw USD dependency closure blocked: {closure.blocked_reasons}"
            )
        source_copy = Path(closure.root_usd_package_path)
        if not source_copy.is_absolute():
            source_copy = source_dir / source_copy
    source_relative = source_copy.relative_to(output).as_posix()
    if liquid_recipe_path is None:
        from .liquid_autofill import recipe_payload

        recipe = validate_liquid_recipe(recipe_payload())
    else:
        recipe = load_liquid_recipe(liquid_recipe_path)
    selected = normalized_collision_presets(proposal.minimum_clearance_radius_m)[1]
    if float(recipe["particle_set"]["width_m"]) <= 0.002:
        selected = dict(selected)
        collision_limit = 0.5 * float(
            recipe["particle_system"]["particle_contact_offset_m"]
        )
        selected["contact_offset_m"] = min(
            float(selected["contact_offset_m"]), collision_limit
        )
        selected["rest_offset_m"] = min(
            float(selected["rest_offset_m"]), 0.5 * collision_limit
        )
        selected["sdf_margin_m"] = min(
            float(selected["sdf_margin_m"]), collision_limit
        )
        selected["sdf_narrow_band_m"] = min(
            float(selected["sdf_narrow_band_m"]), collision_limit
        )
        selected["selection"] = "small_recipe_half_particle_contact_cap"
    interaction = output / "interaction"
    interaction.mkdir()
    recipe_path = interaction / "liquid_recipe.json"
    recipe_path.write_text(json.dumps(recipe, indent=2, sort_keys=True) + "\n")
    recipe_record = {
        "id": recipe["recipe_id"],
        "path": "interaction/liquid_recipe.json",
        "sha256": liquid_recipe_sha256(recipe),
    }
    profile = {
        "schema_version": PROFILE_SCHEMA,
        "profile_id": f"{_slug(proposal.scope_prim.rsplit('/', 1)[-1])}.fluid_interaction.candidate.v1",
        "behavior": proposal.behavior,
        "asset_root_prim": "/FluidInteractionAsset",
        "source_binding": {
            "source_sha256": proposal.source_sha256,
            "source_package_path": source_relative,
        },
        "geometry": proposal.payload["geometry"],
        "collision_parameters": selected,
        "physics": proposal.payload["physics"],
        "qualification_policy": qualification_policy(proposal.behavior),
        "liquid_recipe": recipe_record,
        "claim": None,
        "robot_policy_success": False,
        "benchmark_success": False,
    }
    profile_path = interaction / "fluid_profile.json"
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")
    # The entrypoint contains only a source reference plus collision opinions;
    # no visual mesh is rewritten and no particles are shipped.
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics  # type: ignore

    entry = output / "asset.usda"
    stage = Usd.Stage.CreateNew(str(entry))
    root = stage.DefinePrim("/FluidInteractionAsset", "Xform")
    stage.SetDefaultPrim(root)
    root.GetReferences().AddReference(source_relative, proposal.scope_prim)
    partition_model = proposal.payload["geometry"].get("partition_model")
    selected_source_paths = {
        str(item["prim_path"])
        for item in proposal.payload["geometry"]["roles"]
        if item["role"] != "ignore" and not item.get("derived")
    }
    source_stage = Usd.Stage.Open(str(proposal.source_usd))
    source_scope = source_stage.GetPrimAtPath(proposal.scope_prim) if source_stage else None
    if source_scope is None or not source_scope.IsValid():
        raise ValueError("cannot reopen approved source scope")
    existing_colliders = {
        prim.GetPath().pathString
        for prim in Usd.PrimRange(source_scope)
        if "PhysicsCollisionAPI" in set(prim.GetAppliedSchemas())
    }

    def _remap(path: str) -> str:
        return "/FluidInteractionAsset" + path[len(proposal.scope_prim) :]

    disabled_colliders = existing_colliders if partition_model else existing_colliders - selected_source_paths
    for path in sorted(disabled_colliders):
        stage.OverridePrim(_remap(path)).CreateAttribute(
            "physics:collisionEnabled", Sdf.ValueTypeNames.Bool
        ).Set(False)
    for item in proposal.payload["geometry"]["roles"]:
        if item["role"] == "ignore" or item.get("derived"):
            continue
        prim = stage.OverridePrim(_remap(str(item["prim_path"])))
        UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True).Set(True)
        source_prim = source_stage.GetPrimAtPath(str(item["prim_path"]))
        is_mesh = source_prim.IsA(UsdGeom.Mesh)
        schemas = ["PhysicsCollisionAPI", "PhysxCollisionAPI"]
        if is_mesh:
            UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(
                str(item["approximation"])
            )
            schemas.append("PhysicsMeshCollisionAPI")
        if is_mesh and item["approximation"] == "sdf":
            schemas.append("PhysxSDFMeshCollisionAPI")
        prim.SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(schemas))
        prim.CreateAttribute(
            "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
        ).Set(selected["contact_offset_m"])
        prim.CreateAttribute(
            "physxCollision:restOffset", Sdf.ValueTypeNames.Float
        ).Set(selected["rest_offset_m"])
        if item["approximation"] == "sdf":
            prim.CreateAttribute(
                "physxSDFMeshCollision:sdfResolution", Sdf.ValueTypeNames.UInt
            ).Set(selected["sdf_resolution"])
            prim.CreateAttribute(
                "physxSDFMeshCollision:sdfSubgridResolution", Sdf.ValueTypeNames.UInt
            ).Set(selected["sdf_subgrid_resolution"])
            prim.CreateAttribute(
                "physxSDFMeshCollision:sdfMargin", Sdf.ValueTypeNames.Float
            ).Set(selected["sdf_margin_m"])
            prim.CreateAttribute(
                "physxSDFMeshCollision:sdfNarrowBandThickness", Sdf.ValueTypeNames.Float
            ).Set(selected["sdf_narrow_band_m"])
            prim.CreateAttribute(
                "physxSDFMeshCollision:sdfBitsPerSubgridPixel", Sdf.ValueTypeNames.Token
            ).Set(selected["sdf_bits_per_subgrid_pixel"])
            prim.CreateAttribute(
                "physxSDFMeshCollision:sdfEnableRemeshing", Sdf.ValueTypeNames.Bool
            ).Set(selected["sdf_enable_remeshing"])
    if isinstance(partition_model, dict):
        partition_axis = [
            float(value) for value in proposal.payload["geometry"]["axis_local"]
        ]
        partition_root = stage.DefinePrim(
            "/FluidInteractionAsset/__aan_fluid_collision_partitions", "Scope"
        )
        stations = partition_model["stations"]
        angular_segments = int(partition_model["angular_segments"])
        for axial_index, (lower_station, upper_station) in enumerate(
            zip(stations, stations[1:])
        ):
            for angular_index in range(angular_segments):
                theta0 = 2.0 * math.pi * angular_index / angular_segments
                theta1 = 2.0 * math.pi * (angular_index + 1) / angular_segments
                z0, z1 = float(lower_station["z_m"]), float(upper_station["z_m"])
                i0, o0 = (
                    float(lower_station["inner_radius_m"]),
                    float(lower_station["outer_radius_m"]),
                )
                i1, o1 = (
                    float(upper_station["inner_radius_m"]),
                    float(upper_station["outer_radius_m"]),
                )
                points = [
                    Gf.Vec3f(
                        *_source_position(
                            (
                                radius * math.cos(theta),
                                radius * math.sin(theta),
                                z,
                            ),
                            partition_axis,
                        )
                    )
                    for z, radius, theta in (
                        (z0, i0, theta0), (z0, i0, theta1),
                        (z0, o0, theta0), (z0, o0, theta1),
                        (z1, i1, theta0), (z1, i1, theta1),
                        (z1, o1, theta0), (z1, o1, theta1),
                    )
                ]
                mesh = UsdGeom.Mesh.Define(
                    stage,
                    partition_root.GetPath().AppendChild(
                        f"wall_{axial_index:02d}_{angular_index:02d}"
                    ),
                )
                mesh.CreatePointsAttr(points)
                mesh.CreateFaceVertexCountsAttr([4] * 6)
                mesh.CreateFaceVertexIndicesAttr(
                    [
                        0, 2, 3, 1, 4, 5, 7, 6, 0, 1, 5, 4,
                        2, 6, 7, 3, 0, 4, 6, 2, 1, 3, 7, 5,
                    ]
                )
                mesh.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
                prim = mesh.GetPrim()
                UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True).Set(True)
                UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("convexHull")
                prim.SetMetadata(
                    "apiSchemas",
                    Sdf.TokenListOp.CreateExplicit(
                        ["PhysicsCollisionAPI", "PhysxCollisionAPI", "PhysicsMeshCollisionAPI"]
                    ),
                )
                prim.CreateAttribute(
                    "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
                ).Set(selected["contact_offset_m"])
                prim.CreateAttribute(
                    "physxCollision:restOffset", Sdf.ValueTypeNames.Float
                ).Set(selected["rest_offset_m"])
        if proposal.behavior == "reservoir":
            from .liquid_autofill import recipe_payload

            first = stations[0]
            particle_radius = 0.5 * float(
                recipe_payload()["particle_set"]["width_m"]
            )
            support_station = next(
                (
                    item
                    for item in stations
                    if float(item["z_m"])
                    >= float(proposal.payload["geometry"]["cavity"]["floor_m"])
                    + particle_radius
                ),
                stations[0],
            )
            thickness = max(0.002, 0.5 * (float(stations[1]["z_m"]) - float(first["z_m"])))
            bottom = UsdGeom.Mesh.Define(
                stage, partition_root.GetPath().AppendChild("bottom")
            )
            radius = float(support_station["outer_radius_m"])
            top_z = float(first["z_m"])
            bottom_z = top_z - thickness
            sides = 24
            bottom.CreatePointsAttr(
                [
                    Gf.Vec3f(
                        *_source_position(
                            (
                                radius * math.cos(2.0 * math.pi * index / sides),
                                radius * math.sin(2.0 * math.pi * index / sides),
                                z,
                            ),
                            partition_axis,
                        )
                    )
                    for z in (bottom_z, top_z)
                    for index in range(sides)
                ]
            )
            bottom.CreateFaceVertexCountsAttr([sides, sides] + [4] * sides)
            face_indices = list(reversed(range(sides))) + list(
                range(sides, 2 * sides)
            )
            for index in range(sides):
                following = (index + 1) % sides
                face_indices.extend(
                    [index, following, sides + following, sides + index]
                )
            bottom.CreateFaceVertexIndicesAttr(face_indices)
            bottom.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
            bottom_prim = bottom.GetPrim()
            UsdPhysics.CollisionAPI.Apply(bottom_prim).CreateCollisionEnabledAttr(True).Set(True)
            UsdPhysics.MeshCollisionAPI.Apply(bottom_prim).CreateApproximationAttr(
                "convexHull"
            )
            bottom_prim.SetMetadata(
                "apiSchemas",
                Sdf.TokenListOp.CreateExplicit(
                    [
                        "PhysicsCollisionAPI",
                        "PhysxCollisionAPI",
                        "PhysicsMeshCollisionAPI",
                    ]
                ),
            )
            bottom_prim.CreateAttribute(
                "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
            ).Set(selected["contact_offset_m"])
            bottom_prim.CreateAttribute(
                "physxCollision:restOffset", Sdf.ValueTypeNames.Float
            ).Set(selected["rest_offset_m"])
    stage.GetRootLayer().Save()
    visual_record = _apply_fluid_visual_material_profile(
        output=output,
        entry=entry,
        source_usd=proposal.source_usd,
        source_scope=proposal.scope_prim,
        profile_path=visual_material_profile_path,
    )
    profile["visual_material_profile"] = visual_record
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")
    manifest = {
        "schema_version": "aan.fluid_interaction_asset_result.v1",
        "overall_status": "candidate",
        "blocked_reasons": ["runtime_qualification_not_run"],
        "entrypoints": {"root_usd": "asset.usda", "asset_entry_prim": "/FluidInteractionAsset"},
        "profile": {
            "path": "interaction/fluid_profile.json",
            "sha256": sha256(profile_path.read_bytes()).hexdigest(),
        },
        "source_binding": {
            "source_sha256": proposal.source_sha256,
            "scope_prim": proposal.scope_prim,
        },
        "qualification": {"status": "not_run"},
        "liquid_recipe": recipe_record,
        "visual_material_profile": visual_record,
        "claim": None,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path


def _apply_fluid_visual_material_profile(
    *,
    output: Path,
    entry: Path,
    source_usd: Path,
    source_scope: str,
    profile_path: Path | None,
) -> dict[str, Any]:
    if profile_path is None:
        return {"status": "not_requested"}
    resolution = load_visual_material_profile(profile_path, source_usd)
    if resolution.status != "pass":
        raise ValueError(
            "fluid visual material profile blocked: "
            + str(resolution.reason or "unknown reason")
        )
    if resolution.override_kind != "mdl_glass":
        raise ValueError("fluid visual material profile must use mdl_glass")
    assert resolution.source_mdl is not None
    assert resolution.source_sub_identifier is not None
    assert resolution.material_name is not None
    assert resolution.profile_id is not None
    assert resolution.profile_sha256 is not None
    assert resolution.profile_bytes is not None
    assert resolution.mdl_inputs is not None
    from pxr import Usd  # type: ignore

    source_stage = Usd.Stage.Open(str(source_usd))
    for target in resolution.binding_targets:
        if not target.startswith(source_scope + "/") or not source_stage.GetPrimAtPath(
            target
        ):
            raise ValueError(f"fluid visual material target is invalid: {target}")
    mdl_dir = output / "deps/mdl"
    mdl_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(resolution.source_mdl, mdl_dir / resolution.source_mdl.name)
    for dependency in resolution.source_mdl_dependencies:
        shutil.copy2(dependency, mdl_dir / dependency.name)
    remapped = tuple(
        "/FluidInteractionAsset" + target[len(source_scope) :]
        for target in resolution.binding_targets
    )
    overlay = output / "overlays/visual_material.usda"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    overlay.write_text(
        _mdl_overlay_text(
            scope="/FluidInteractionAsset",
            material_name=resolution.material_name,
            mdl_relpath="../deps/mdl/" + resolution.source_mdl.name,
            source_sub_identifier=resolution.source_sub_identifier,
            profile_id=resolution.profile_id,
            profile_sha256=resolution.profile_sha256,
            binding_targets=remapped,
            mdl_inputs=resolution.mdl_inputs,
        ),
        encoding="utf-8",
    )
    profile_copy = output / "visual/profile.json"
    profile_copy.parent.mkdir(parents=True, exist_ok=True)
    profile_copy.write_bytes(resolution.profile_bytes)
    stage = Usd.Stage.Open(str(entry))
    stage.GetRootLayer().subLayerPaths.insert(0, "overlays/visual_material.usda")
    stage.GetRootLayer().Save()
    return {
        "status": "pass",
        "profile_id": resolution.profile_id,
        "profile_sha256": resolution.profile_sha256,
        "path": "visual/profile.json",
        "overlay": "overlays/visual_material.usda",
        "binding_targets": list(remapped),
    }


def _canonical_rotation(axis: list[float]) -> tuple[float, float, float]:
    dominant = max(range(3), key=lambda index: abs(axis[index]))
    positive = axis[dominant] >= 0
    if dominant == 2:
        return (0.0 if positive else 180.0, 0.0, 0.0)
    if dominant == 1:
        return (90.0 if positive else -90.0, 0.0, 0.0)
    return (0.0, -90.0 if positive else 90.0, 0.0)


def _canonical_position(point: list[float], axis: list[float]) -> list[float]:
    dominant = max(range(3), key=lambda index: abs(axis[index]))
    radial = [index for index in range(3) if index != dominant]
    direction = 1.0 if axis[dominant] >= 0 else -1.0
    # Match the axis-alignment Xform used by _canonical_rotation.  The sign of
    # the second radial coordinate is immaterial for axial fixtures but is
    # preserved for receiver placement.
    second_sign = -1.0 if dominant == 1 and direction > 0 else 1.0
    return [
        float(point[radial[0]]),
        float(point[radial[1]]) * second_sign,
        float(point[dominant]) * direction,
    ]


def _source_position(point: tuple[float, float, float], axis: list[float]) -> tuple[float, float, float]:
    dominant = max(range(3), key=lambda index: abs(axis[index]))
    radial = [index for index in range(3) if index != dominant]
    direction = 1.0 if axis[dominant] >= 0 else -1.0
    second_sign = -1.0 if dominant == 1 and direction > 0 else 1.0
    result = [0.0, 0.0, 0.0]
    result[radial[0]] = point[0]
    result[radial[1]] = point[1] * second_sign
    result[dominant] = point[2] * direction
    return (result[0], result[1], result[2])


def _seed_cylinder(
    *, center: list[float], radius: float, z0: float, z1: float, spacing: float
) -> list[list[float]]:
    points: list[list[float]] = []
    x = -radius
    while x <= radius + 1e-9:
        y = -radius
        while y <= radius + 1e-9:
            if x * x + y * y <= radius * radius:
                z = z0
                while z <= z1 + 1e-9:
                    points.append([center[0] + x, center[1] + y, z])
                    z += spacing
            y += spacing
        x += spacing
    if not points:
        points = [[center[0], center[1], 0.5 * (z0 + z1)]]
    return points


def _station_radius(stations: list[dict[str, Any]], z: float, key: str) -> float:
    if z <= float(stations[0]["z_m"]):
        return float(stations[0][key])
    for lower, upper in zip(stations, stations[1:]):
        z0, z1 = float(lower["z_m"]), float(upper["z_m"])
        if z0 <= z <= z1:
            alpha = (z - z0) / max(z1 - z0, 1e-9)
            return (1.0 - alpha) * float(lower[key]) + alpha * float(upper[key])
    return float(stations[-1][key])


def _conduit_outlet_outer_radius(geometry: dict[str, Any]) -> float:
    wall_profile = geometry.get("partition_model", {}).get("stations", [])
    if wall_profile:
        return float(wall_profile[0]["outer_radius_m"])
    inner = float(geometry["minimum_clearance_radius_m"])
    ratio = float(geometry.get("cavity", {}).get("inner_outer_radial_ratio", 0.0))
    return inner / ratio if 0.0 < ratio <= 1.0 else inner


def _seed_profiled_reservoir(
    *,
    stations: list[dict[str, Any]],
    floor: float,
    rim: float,
    fill: float,
    spacing: float,
) -> list[list[float]]:
    top = floor + fill * (rim - floor)
    maximum = max(float(item["inner_radius_m"]) for item in stations)
    points: list[list[float]] = []
    z = floor + 0.55 * spacing
    while z <= top + 1e-9:
        allowed = max(0.0, _station_radius(stations, z, "inner_radius_m") - 0.55 * spacing)
        x = -maximum
        while x <= maximum + 1e-9:
            y = -maximum
            while y <= maximum + 1e-9:
                if x * x + y * y <= allowed * allowed:
                    points.append([x, y, z])
                y += spacing
            x += spacing
        z += spacing
    return points or [[0.0, 0.0, floor + 0.55 * spacing]]


def _runtime_fixture(
    *, package: Path, proposal_path: Path, root: Path, guide_enabled: bool = True
) -> tuple[Path, Path]:
    """Build a temporary liquid fixture around the empty package."""

    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics  # type: ignore

    from .liquid_autofill import build_particle_lattice
    from .liquid_autofill_runtime import _define_overlay, _qualification_scene

    proposal = load_approved_proposal(proposal_path)
    recipe = load_liquid_recipe(package / "interaction/liquid_recipe.json")
    spacing = float(recipe["particle_set"]["spacing_m"])
    geometry = proposal.payload["geometry"]
    behavior = proposal.behavior
    root.mkdir(parents=True, exist_ok=True)
    source = root / "fixture_source.usda"
    stage = Usd.Stage.CreateNew(str(source))
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)
    target = stage.DefinePrim("/World/Container", "Xform")
    target.GetReferences().AddReference(
        str((package / "asset.usda").resolve()), "/FluidInteractionAsset"
    )
    xform = UsdGeom.Xformable(target)
    xform.AddTranslateOp(opSuffix="motion").Set(Gf.Vec3d(0.0))
    xform.AddRotateXOp(opSuffix="pour").Set(0.0)
    axis_alignment = xform.AddRotateXYZOp(opSuffix="axis_alignment")
    axis_alignment.Set(
        Gf.Vec3f(*_canonical_rotation([float(value) for value in geometry["axis_local"]]))
    )
    UsdPhysics.RigidBodyAPI.Apply(target).CreateRigidBodyEnabledAttr(True).Set(True)
    target.CreateAttribute("physics:kinematicEnabled", Sdf.ValueTypeNames.Bool).Set(True)
    physics_path = "/World/PhysicsScene"
    physics = UsdPhysics.Scene.Define(stage, physics_path)
    physics.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
    physics.CreateGravityMagnitudeAttr(9.81)
    stage.GetRootLayer().Save()

    role_paths = []
    for item in geometry["roles"]:
        if item["role"] == "ignore" or (behavior == "surface_guide" and not guide_enabled):
            continue
        authored_path = str(item["prim_path"])
        prefix = "/FluidInteractionAsset" if item.get("derived") else proposal.scope_prim
        suffix = authored_path[len(prefix) :]
        role_paths.append(
            {
                "prim_path": "/World/Container" + suffix,
                "approximation": item["approximation"],
            }
        )
    composed = Usd.Stage.Open(str(source))
    existing = [
        prim.GetPath().pathString
        for prim in composed.Traverse()
        if "PhysicsCollisionAPI" in set(prim.GetAppliedSchemas())
    ]
    axis = [float(value) for value in geometry["axis_local"]]
    if behavior == "reservoir":
        cavity = dict(geometry["cavity"])
        reservoir_profile = geometry.get("partition_model", {}).get("stations", [])
        points = (
            _seed_profiled_reservoir(
                stations=reservoir_profile,
                floor=float(cavity["floor_m"]),
                rim=float(cavity["rim_m"]),
                fill=0.40,
                spacing=spacing,
            )
            if reservoir_profile
            else build_particle_lattice(
                cavity,
                fill=0.40,
                spacing_m=spacing,
                maximum_particles=int(recipe["particle_set"]["maximum_count"]),
            )
        )
        receiver = None
    elif behavior == "conduit":
        inlet = _canonical_position(
            [float(value) for value in geometry["frames"]["inlet"]["position_m"]], axis
        )
        outlet = _canonical_position(
            [float(value) for value in geometry["frames"]["outlet"]["position_m"]], axis
        )
        radius = min(0.012, 0.42 * float(geometry["cavity"]["radius_x_m"]))
        points = _seed_cylinder(
            center=inlet,
            radius=radius,
            z0=inlet[2] + 0.008,
            z1=inlet[2] + 0.032,
            spacing=spacing,
        )
        cavity = geometry["cavity"]
        receiver = {
            "center_m": [outlet[0], outlet[1], outlet[2] - 0.06],
            "radius_m": max(0.05, 1.5 * float(geometry["cavity"]["radius_x_m"])),
            "height_m": 0.07,
        }
    else:
        length = float(geometry["bounds"]["maximum_m"][2]) - float(
            geometry["bounds"]["minimum_m"][2]
        )
        angle = math.radians(20.0)
        # Tilt only the guide geometry. Particles start above its upper end;
        # the paired no-guide fixture therefore misses the receiver unless the
        # real surface redirects the flow.
        axis_alignment.Set(Gf.Vec3f(0.0, 20.0, 0.0))
        stage.GetRootLayer().Save()
        upper = [math.sin(angle) * length, 0.0, math.cos(angle) * length]
        points = _seed_cylinder(
            center=upper,
            radius=0.008,
            z0=upper[2] + 0.008,
            z1=upper[2] + 0.026,
            spacing=spacing,
        )
        cavity = {
            "center_xy_m": [0.0, 0.0],
            "radius_x_m": 0.01,
            "radius_y_m": 0.01,
            "floor_m": 0.0,
            "rim_m": max(length, 0.01),
        }
        receiver = {
            "center_m": [0.0, 0.0, -0.05],
            "radius_m": 0.035,
            "height_m": 0.06,
        }
    analysis = {
        "container_prim": "/World/Container",
        "up_axis": "Z",
        "meters_per_unit": 1.0,
        "instanceable_target": False,
        "collision_prims": role_paths,
        "existing_collider_prims": existing,
        "physics_scene_path": physics_path,
    }
    overlay, _, particle_path, _ = _define_overlay(
        scene=source,
        output=root,
        analysis=analysis,
        points_m=points,
        recipe_override=recipe,
    )
    scene = root / "fixture.usda"
    _qualification_scene(source, overlay, scene)
    bounds = geometry["bounds"]
    fixture: dict[str, Any] = {
        "schema_version": "aan.fluid_interaction_runtime_fixture.v1",
        "behavior": behavior,
        "target_prim": "/World/Container",
        "particle_set_prim": particle_path,
        "particle_count": len(points),
        "physics_scene_path": physics_path,
        "liquid_recipe": {
            "id": recipe["recipe_id"],
            "sha256": liquid_recipe_sha256(recipe),
        },
        "cavity": cavity,
        "retention_profile": (
            geometry.get("partition_model", {}).get("stations", [])
            if behavior == "reservoir"
            else []
        ),
    }
    if receiver is not None:
        fixture["receiver"] = receiver
    if behavior == "conduit":
        wall_profile = geometry.get("partition_model", {}).get("stations", [])
        outlet_outer_radius = _conduit_outlet_outer_radius(geometry)
        fixture.update(
            {
                "inlet_z_m": inlet[2],
                "outlet_z_m": outlet[2],
                "outlet_radius_m": outlet_outer_radius
                + 0.5 * float(recipe["particle_set"]["width_m"])
                + float(recipe["particle_system"]["max_velocity_m_s"]) / 120.0,
                "outlet_crossing_tolerance": (
                    "outer_spout_radius + particle_radius + one_max_velocity_timestep"
                ),
                "wall_profile": wall_profile,
                "outer_radius_m": 0.5
                * max(
                    float(bounds["maximum_m"][0]) - float(bounds["minimum_m"][0]),
                    float(bounds["maximum_m"][1]) - float(bounds["minimum_m"][1]),
                ),
            }
        )
    fixture_path = root / "fixture.json"
    fixture_path.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n")
    return scene, fixture_path


def _run_observation(
    *, launcher: Path, worker: Path, scene: Path, fixture: Path, run_index: int, output: Path
) -> dict[str, Any]:
    log = output.with_suffix(".log")
    command = [
        str(launcher),
        str(worker),
        "--scene",
        str(scene),
        "--fixture",
        str(fixture),
        "--run-index",
        str(run_index),
        "--out",
        str(output),
    ]
    environment = dict(os.environ)
    for name in (
        "PYTHONPATH",
        "LD_LIBRARY_PATH",
        "CARB_APP_PATH",
        "EXP_PATH",
        "ISAAC_PATH",
        "ISAAC_SIM_ROOT",
    ):
        environment.pop(name, None)
    environment["ACCEPT_EULA"] = "Y"
    environment.setdefault("PRIVACY_CONSENT", "Y")
    with log.open("w", encoding="utf-8") as stream:
        completed = subprocess.run(
            command,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
            env=environment,
        )
    if completed.returncode or not output.is_file():
        raise RuntimeError(f"fluid interaction worker failed; see {log}")
    return json.loads(output.read_text(encoding="utf-8"))


def qualify_asset_package(
    *, output: Path, proposal_path: Path, launcher: Path, worker: Path
) -> dict[str, Any]:
    """Run three fresh Isaac processes and promote only the exact passing package."""

    output = Path(output).resolve()
    proposal = load_approved_proposal(proposal_path)
    recipe = load_liquid_recipe(output / "interaction/liquid_recipe.json")
    recipe_record = {
        "id": recipe["recipe_id"],
        "sha256": liquid_recipe_sha256(recipe),
    }
    evidence = output / "evidence/qualification"
    evidence.mkdir(parents=True, exist_ok=True)
    runs: list[dict[str, Any]] = []
    for index in range(3):
        if proposal.behavior == "surface_guide":
            enabled_root = evidence / f"run_{index:02d}_with_guide"
            baseline_root = evidence / f"run_{index:02d}_without_guide"
            enabled_scene, enabled_fixture = _runtime_fixture(
                package=output,
                proposal_path=proposal_path,
                root=enabled_root,
                guide_enabled=True,
            )
            baseline_scene, baseline_fixture = _runtime_fixture(
                package=output,
                proposal_path=proposal_path,
                root=baseline_root,
                guide_enabled=False,
            )
            observed = _run_observation(
                launcher=launcher,
                worker=worker,
                scene=enabled_scene,
                fixture=enabled_fixture,
                run_index=index,
                output=enabled_root / "observation.json",
            )
            baseline = _run_observation(
                launcher=launcher,
                worker=worker,
                scene=baseline_scene,
                fixture=baseline_fixture,
                run_index=index,
                output=baseline_root / "observation.json",
            )
            observed["baseline_capture_ratio"] = baseline["capture_ratio"]
            observed["hard_errors"] = list(observed["hard_errors"]) + list(
                baseline["hard_errors"]
            )
            runs.append(observed)
        else:
            run_root = evidence / f"run_{index:02d}"
            scene, fixture = _runtime_fixture(
                package=output,
                proposal_path=proposal_path,
                root=run_root,
            )
            runs.append(
                _run_observation(
                    launcher=launcher,
                    worker=worker,
                    scene=scene,
                    fixture=fixture,
                    run_index=index,
                    output=run_root / "observation.json",
                )
            )
    if any(item.get("liquid_recipe") != recipe_record for item in runs):
        raise RuntimeError("cold observation liquid recipe disagrees with package")
    report = evaluate_qualification_runs(proposal.behavior, runs)
    report["liquid_recipe"] = recipe_record
    report_path = evidence / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest_path = output / "manifest.json"
    profile_path = output / "interaction/fluid_profile.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    status = report["overall_status"]
    if status == "pass":
        claim = "qualified_fluid_interaction_asset"
        manifest["overall_status"] = "pass"
        manifest["blocked_reasons"] = []
        manifest["claim"] = claim
        profile["claim"] = claim
    else:
        manifest["overall_status"] = status
        manifest["blocked_reasons"] = report["blocked_reasons"]
        manifest["claim"] = None
        profile["claim"] = None
    profile["qualification"] = {
        "status": status,
        "report": "evidence/qualification/report.json",
        "report_sha256": sha256(report_path.read_bytes()).hexdigest(),
    }
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")
    manifest["profile"]["sha256"] = sha256(profile_path.read_bytes()).hexdigest()
    manifest["qualification"] = {
        "status": status,
        "report": "evidence/qualification/report.json",
        "report_sha256": sha256(report_path.read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report
