#!/usr/bin/env python3
"""Extract the Wangshuai funnel/tube scene into exact-source reusable packages."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any


DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_wangshuai/lixinguan_funnel_liquid.usd"
)
DEFAULT_OUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "wangshuai_funnel_tube15_exact_asset_set_20260826"
)
OMNIGLASS = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "funnel_15ml_small_particle_small_v2_glass_v1_20260825/deps/mdl/OmniGlass.mdl"
)
ISAAC41_MDL_BASE = Path(
    "/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/"
    "embodied-eval-os-sim-isaacsim41-genmanip-py310/lib/python3.10/"
    "site-packages/omni/mdl/core/Base"
)


ASSETS: dict[str, dict[str, Any]] = {
    "tube15_threaded_liquid_ready": {
        "source_prim": "/World/shiguan",
        "entry_prim": "/Tube15ThreadedLiquidReady",
        "role": "liquid_ready_container",
        "mesh_paths": ("/node_/mesh_", "/node_/Cone"),
        "material": "glass_external_copy",
        "claims": {"threaded_body_geometry": True, "liquid_interactive_geometry": True},
    },
    "tube15_threaded_closed_cap": {
        "source_prim": "/World/cap",
        "entry_prim": "/Tube15ThreadedClosedCap",
        "role": "threaded_closure",
        "mesh_paths": ("/node_/mesh_",),
        "material": "internal_omnipbr",
        "claims": {"threaded_cap_geometry": True, "closed_top_geometry": True},
    },
    "funnel_small_v2_liquid_ready": {
        "source_prim": "/World/funnel",
        "entry_prim": "/FunnelSmallV2LiquidReady",
        "role": "liquid_conduit",
        "mesh_paths": ("/Visual",),
        "material": "internal_omniglass",
        "claims": {"liquid_interactive_geometry": True, "conduit_geometry": True},
    },
    "small_v2_liquid_seed_1948": {
        "source_prim": "/World/{Cone,ParticleSystem,ParticleSet}",
        "entry_prim": "/SmallV2LiquidSeed1948",
        "role": "pbd_liquid_seed_overlay",
        "mesh_paths": ("/Sampler",),
        "material": "none",
        "claims": {"particle_count": 1948, "contains_physics_scene": False},
    },
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _normal(value: Any) -> Any:
    from pxr import Sdf

    if isinstance(value, Sdf.AssetPath):
        return value.path
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        values = list(value)
    except TypeError:
        return repr(value)
    if len(values) > 64:
        return {
            "length": len(values),
            "sha256": sha256(repr(values).encode()).hexdigest(),
        }
    return [_normal(item) for item in values]


def _xform_record(prim: Any) -> list[dict[str, Any]]:
    from pxr import UsdGeom

    return [
        {"op": op.GetOpName(), "value": _normal(op.Get())}
        for op in UsdGeom.Xformable(prim).GetOrderedXformOps()
    ]


def _mesh_record(prim: Any) -> dict[str, Any]:
    from pxr import UsdGeom

    mesh = UsdGeom.Mesh(prim)
    digest = sha256()
    arrays = (
        list(mesh.GetPointsAttr().Get()),
        list(mesh.GetFaceVertexCountsAttr().Get()),
        list(mesh.GetFaceVertexIndicesAttr().Get()),
    )
    for value in arrays:
        digest.update(repr(value).encode())
    return {
        "sha256": digest.hexdigest(),
        "points": len(arrays[0]),
        "faces": len(arrays[1]),
        "indices": len(arrays[2]),
    }


def _physics_signature(stage: Any, root_path: str) -> dict[str, Any]:
    result = {}
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        if path != root_path and not path.startswith(root_path + "/"):
            continue
        relative = path[len(root_path) :] or "/"
        attrs = {}
        for attr in prim.GetAttributes():
            name = attr.GetName()
            if name.startswith(("physics:", "physx")) and attr.HasAuthoredValueOpinion():
                attrs[name] = _normal(attr.Get())
        schemas = [
            name
            for name in prim.GetAppliedSchemas()
            if name.startswith(("Physics", "Physx"))
        ]
        relationships = {}
        for rel in prim.GetRelationships():
            if not rel.GetName().startswith(("physics:", "physx")):
                continue
            targets = []
            for target in rel.GetTargets():
                text = str(target)
                targets.append(text[len(root_path) :] if text.startswith(root_path) else text)
            if targets:
                relationships[rel.GetName()] = targets
        if attrs or schemas or relationships:
            result[relative] = {
                "schemas": schemas,
                "attributes": attrs,
                "relationships": relationships,
            }
    return result


def _clear_root_xform(prim: Any) -> None:
    from pxr import UsdGeom

    for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
        prim.RemoveProperty(op.GetOpName())
    prim.RemoveProperty("xformOpOrder")


def _copy_mdl(package: Path, kind: str) -> list[dict[str, str]]:
    destination = package / "deps/mdl"
    destination.mkdir(parents=True, exist_ok=True)
    sources = []
    if kind in {"glass_external_copy", "internal_omniglass"}:
        sources.append(OMNIGLASS)
    if kind == "internal_omnipbr" or kind == "glass_external_copy":
        sources.extend(
            ISAAC41_MDL_BASE / name
            for name in ("OmniPBR.mdl", "OmniPBR_ClearCoat.mdl", "OmniPBRBase.mdl")
        )
    records = []
    for source in sources:
        target = destination / source.name
        shutil.copy2(source, target)
        records.append(
            {
                "path": target.relative_to(package).as_posix(),
                "sha256": _sha(target),
                "source": str(source),
            }
        )
    return records


def _localize_materials(stage: Any) -> list[dict[str, str]]:
    from pxr import Sdf, UsdShade

    records = []
    for prim in stage.Traverse():
        if not prim.IsA(UsdShade.Shader):
            continue
        shader = UsdShade.Shader(prim)
        asset = shader.GetSourceAsset("mdl")
        if not asset:
            continue
        name = Path(asset.path.replace("\\", "/")).name
        if name not in {"OmniGlass.mdl", "OmniPBR.mdl"}:
            raise RuntimeError(f"unexpected MDL dependency: {asset.path}")
        localized = f"deps/mdl/{name}"
        shader.SetSourceAsset(Sdf.AssetPath(localized), "mdl")
        records.append(
            {
                "shader": str(prim.GetPath()),
                "source": asset.path,
                "localized": localized,
            }
        )
    return records


def _repair_material(stage: Any, material_path: str) -> None:
    from pxr import UsdShade

    material = UsdShade.Material(stage.GetPrimAtPath(material_path))
    shaders = [
        UsdShade.Shader(prim)
        for prim in stage.Traverse()
        if str(prim.GetPath()).startswith(material_path + "/")
        and prim.IsA(UsdShade.Shader)
    ]
    if len(shaders) != 1:
        raise RuntimeError(f"expected one shader below {material_path}, got {len(shaders)}")
    for output in material.GetOutputs():
        output.GetAttr().ClearConnections()
        output.ConnectToSource(shaders[0].ConnectableAPI(), "out")


def _set_binding(stage: Any, prim_path: str, material_path: str) -> None:
    prim = stage.GetPrimAtPath(prim_path)
    relationship = prim.GetRelationship("material:binding")
    if not relationship:
        relationship = prim.CreateRelationship("material:binding")
    relationship.SetTargets([material_path])


def _build_rigid_asset(
    source: Any, asset_id: str, spec: dict[str, Any], package: Path
) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdGeom

    package.mkdir(parents=True, exist_ok=True)
    asset_path = package / "asset.usda"
    stage = Usd.Stage.CreateNew(str(asset_path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    Sdf.CopySpec(
        source.GetRootLayer(),
        spec["source_prim"],
        stage.GetRootLayer(),
        spec["entry_prim"],
    )
    root = stage.GetPrimAtPath(spec["entry_prim"])
    stage.SetDefaultPrim(root)
    source_root = source.GetPrimAtPath(spec["source_prim"])
    source_xform = _xform_record(source_root)
    _clear_root_xform(root)

    if asset_id == "tube15_threaded_liquid_ready":
        material_path = spec["entry_prim"] + "/__source_materials/WebStandardClearBorosilicate"
        UsdGeom.Scope.Define(stage, spec["entry_prim"] + "/__source_materials")
        Sdf.CopySpec(
            source.GetRootLayer(),
            "/World/funnel/__aan_visual_materials/WebStandardClearBorosilicate",
            stage.GetRootLayer(),
            material_path,
        )
        _repair_material(stage, material_path)
        _set_binding(stage, spec["entry_prim"] + "/node_/mesh_", material_path)
        _repair_material(stage, spec["entry_prim"] + "/Looks/DefaultMaterial")
    elif asset_id == "tube15_threaded_closed_cap":
        material_path = spec["entry_prim"] + "/Looks/DefaultMaterial"
        _repair_material(stage, material_path)
        _set_binding(stage, spec["entry_prim"] + "/node_/mesh_", material_path)
    else:
        material_path = spec["entry_prim"] + "/__aan_visual_materials/WebStandardClearBorosilicate"
        _repair_material(stage, material_path)
        _set_binding(stage, spec["entry_prim"] + "/Visual", material_path)
    localization = _localize_materials(stage)
    stage.GetRootLayer().Save()
    mdl_files = _copy_mdl(package, spec["material"])

    verified = Usd.Stage.Open(str(asset_path))
    source_physics = _physics_signature(source, spec["source_prim"])
    package_physics = _physics_signature(verified, spec["entry_prim"])
    forbidden = [] if source_physics == package_physics else ["physics_signature_changed"]
    mesh_records = []
    for relative in spec["mesh_paths"]:
        source_mesh = _mesh_record(source.GetPrimAtPath(spec["source_prim"] + relative))
        package_mesh = _mesh_record(verified.GetPrimAtPath(spec["entry_prim"] + relative))
        if source_mesh != package_mesh:
            forbidden.append(f"mesh_changed:{relative}")
        mesh_records.append({"relative_prim": relative, **source_mesh})
    manifest = {
        "schema_version": "aan.exact_source_subtree_package.v1",
        "package_id": f"wangshuai_{asset_id}_v1",
        "overall_status": "candidate",
        "blocked_reasons": ["runtime_recomposition_qualification_pending"],
        "source": {
            "scene": str(source.GetRootLayer().realPath),
            "scene_sha256": _sha(Path(source.GetRootLayer().realPath)),
            "prim": spec["source_prim"],
            "scene_placement_xform": source_xform,
        },
        "entrypoints": {
            "root_usd": "asset.usda",
            "default_prim": spec["entry_prim"].lstrip("/"),
            "asset_entry_prim": spec["entry_prim"],
        },
        "role": spec["role"],
        "mesh_fingerprints": mesh_records,
        "physics_signature_sha256": sha256(
            json.dumps(source_physics, sort_keys=True).encode()
        ).hexdigest(),
        "material_dependency_localization": localization,
        "mdl_files": mdl_files,
        "forbidden_changes_detected": forbidden,
        "claims": {
            **spec["claims"],
            "identity_entry_root": True,
            "physics_parameters_unchanged": not forbidden,
            "contains_liquid": False,
            "robot_policy_success": False,
            "task_success": False,
            "benchmark_success": False,
        },
    }
    evidence = package / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    if forbidden:
        raise RuntimeError(f"exact extraction audit blocked for {asset_id}: {forbidden}")
    return manifest


def _build_liquid_overlay(source: Any, package: Path) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdGeom

    spec = ASSETS["small_v2_liquid_seed_1948"]
    package.mkdir(parents=True, exist_ok=True)
    asset_path = package / "asset.usda"
    stage = Usd.Stage.CreateNew(str(asset_path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    root = UsdGeom.Xform.Define(stage, spec["entry_prim"]).GetPrim()
    stage.SetDefaultPrim(root)
    for source_path, name in (
        ("/World/Cone", "Sampler"),
        ("/World/ParticleSystem", "ParticleSystem"),
        ("/World/ParticleSet", "ParticleSet"),
    ):
        Sdf.CopySpec(
            source.GetRootLayer(),
            source_path,
            stage.GetRootLayer(),
            spec["entry_prim"] + f"/{name}",
        )
    sampler = stage.GetPrimAtPath(spec["entry_prim"] + "/Sampler")
    particle_set = stage.GetPrimAtPath(spec["entry_prim"] + "/ParticleSet")
    sampler.GetRelationship("physxParticleSampling:particles").SetTargets(
        [spec["entry_prim"] + "/ParticleSet"]
    )
    particle_set.GetRelationship("physxParticle:particleSystem").SetTargets(
        [spec["entry_prim"] + "/ParticleSystem"]
    )
    stage.GetRootLayer().Save()
    verified = Usd.Stage.Open(str(asset_path))
    destination_set = verified.GetPrimAtPath(spec["entry_prim"] + "/ParticleSet")
    source_set = source.GetPrimAtPath("/World/ParticleSet")
    source_system = source.GetPrimAtPath("/World/ParticleSystem")
    destination_system = verified.GetPrimAtPath(spec["entry_prim"] + "/ParticleSystem")
    forbidden = []
    for name in ("points", "velocities", "widths"):
        if repr(list(source_set.GetAttribute(name).Get())) != repr(
            list(destination_set.GetAttribute(name).Get())
        ):
            forbidden.append(f"particle_array_changed:{name}")
    for name in ("maxVelocity", "particleContactOffset", "restOffset"):
        if source_system.GetAttribute(name).Get() != destination_system.GetAttribute(name).Get():
            forbidden.append(f"particle_system_parameter_changed:{name}")
    if any(prim.GetTypeName() == "PhysicsScene" for prim in verified.Traverse()):
        forbidden.append("physics_scene_copied_into_overlay")
    particle_count = len(destination_set.GetAttribute("points").Get())
    if particle_count != 1948:
        forbidden.append("particle_count_changed")
    manifest = {
        "schema_version": "aan.exact_source_particle_overlay.v1",
        "package_id": "wangshuai_small_v2_liquid_seed_1948_v1",
        "overall_status": "candidate",
        "blocked_reasons": ["runtime_recomposition_qualification_pending"],
        "source": {
            "scene": str(source.GetRootLayer().realPath),
            "scene_sha256": _sha(Path(source.GetRootLayer().realPath)),
            "prims": ["/World/Cone", "/World/ParticleSystem", "/World/ParticleSet"],
        },
        "entrypoints": {
            "root_usd": "asset.usda",
            "default_prim": spec["entry_prim"].lstrip("/"),
            "asset_entry_prim": spec["entry_prim"],
        },
        "role": spec["role"],
        "particle_count": particle_count,
        "particle_arrays": {
            name: sha256(repr(list(destination_set.GetAttribute(name).Get())).encode()).hexdigest()
            for name in ("points", "velocities", "widths")
        },
        "particle_system": {
            name: destination_system.GetAttribute(name).Get()
            for name in ("maxVelocity", "particleContactOffset", "restOffset")
        },
        "required_runtime": {"gpu_dynamics": True, "physics_scene_owned_by_consumer": True},
        "forbidden_changes_detected": forbidden,
        "claims": {
            "identity_entry_root": True,
            "physics_parameters_unchanged": not forbidden,
            "contains_physics_scene": False,
            "robot_policy_success": False,
            "task_success": False,
            "benchmark_success": False,
        },
    }
    evidence = package / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    if forbidden:
        raise RuntimeError(f"exact liquid extraction audit blocked: {forbidden}")
    return manifest


def build_asset_set(source_path: Path, output: Path) -> dict[str, Any]:
    from pxr import Usd

    source_path = source_path.resolve()
    output = output.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    staging = output.parent / f".{output.name}.staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    source = Usd.Stage.Open(str(source_path), Usd.Stage.LoadAll)
    if not source:
        raise RuntimeError(f"cannot open source: {source_path}")
    manifests = {}
    try:
        for asset_id, spec in ASSETS.items():
            package = staging / "packages" / asset_id
            manifests[asset_id] = (
                _build_liquid_overlay(source, package)
                if asset_id == "small_v2_liquid_seed_1948"
                else _build_rigid_asset(source, asset_id, spec, package)
            )
        index = {
            "schema_version": "aan.wangshuai_funnel_tube15_asset_set.v1",
            "status": "candidate_runtime_pending",
            "source": str(source_path),
            "source_sha256": _sha(source_path),
            "assets": [
                {
                    "id": asset_id,
                    "package": f"packages/{asset_id}",
                    "entry_usd": f"packages/{asset_id}/asset.usda",
                    "entry_prim": spec["entry_prim"],
                    "role": spec["role"],
                    "overall_status": manifests[asset_id]["overall_status"],
                }
                for asset_id, spec in ASSETS.items()
            ],
            "excluded_scene_fixture_prims": [
                "/World/GroundPlane",
                "/World/PhysicsScene",
                "/PhysicsScene",
                "/Environment",
                "/Render",
            ],
            "claims": {
                "physics_parameters_unchanged": True,
                "runtime_recomposition_qualified": False,
                "robot_policy_success": False,
                "task_success": False,
                "benchmark_success": False,
            },
        }
        (staging / "asset_set_manifest.json").write_text(
            json.dumps(index, indent=2, sort_keys=True) + "\n"
        )
        if output.exists():
            shutil.rmtree(output)
        staging.rename(output)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return {
        "root": output,
        "manifest": output / "asset_set_manifest.json",
        "packages": {asset_id: output / "packages" / asset_id for asset_id in ASSETS},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = build_asset_set(args.source, args.out)
    print(json.dumps({key: str(value) for key, value in result.items() if key != "packages"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
