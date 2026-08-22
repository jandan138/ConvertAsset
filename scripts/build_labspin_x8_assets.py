#!/usr/bin/env python3
"""Build source-bound LABSPIN X8 centrifuge and native closed-tube packages.

The intake archive contains exported OBJ/GLB/URDF/USD assets, not generator
source.  This builder preserves every consumed source member byte-for-byte and
authors a package facade with interaction physics.  The visual meshes are never
used as a monolithic rotor collider: each of the 24 openings receives an open
eight-panel sleeve and a physical floor.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import Any
import zipfile


CENTRIFUGE_ENTRY = "/World/Centrifuge"
NATIVE_TUBE_ENTRY = "/World/NativeCentrifugeTube15mlClosed"
EXISTING_TUBE_ENTRY = "/World/CentrifugeTube15mlClosed"
DEFAULT_EXISTING_15ML_PACKAGE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "scientific_workbench_r7_task_assets_20260813/packages/"
    "centrifuge_tube_15ml_closed"
)
SOURCE_CENTRIFUGE = "assets/usd/centrifuge.usd"
SOURCE_ARTICULATION = "assets/usd/centrifuge_articulated.usda"
SOURCE_TUBE_BODY = "assets/usd/tube_body.usd"
SOURCE_TUBE_CAP = "assets/usd/tube_cap.usd"
SOURCE_ENV = "assets/usd/textures/color_020306.exr"
SOCKET_COUNT = 24
SOCKET_INNER_RADIUS_M = 0.0095
SOCKET_OUTER_RADIUS_M = 0.0131
SOCKET_WALL_PANELS = 8
SOCKET_FLOOR_THICKNESS_M = 0.003
LOW_SPEED_TARGET_RAD_S = 5.0
INTERACTION_CONTACT_OFFSET_M = 0.0001
INTERACTION_REST_OFFSET_M = 0.0


def _sha_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _extract_member(archive: zipfile.ZipFile, member: str, destination: Path) -> str:
    value = archive.read(member)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(value)
    return _sha_bytes(value)


def _vec(value: Any) -> list[float]:
    return [float(value[0]), float(value[1]), float(value[2])]


def _center(bounds: Any) -> Any:
    return (bounds.GetMin() + bounds.GetMax()) * 0.5


def _normalise(values: list[float]) -> list[float]:
    length = math.sqrt(sum(value * value for value in values))
    if length <= 1.0e-12:
        raise ValueError("zero-length socket axis")
    return [value / length for value in values]


def _socket_measurements(source_usd: Path) -> list[dict[str, Any]]:
    from pxr import Usd, UsdGeom

    stage = Usd.Stage.Open(str(source_usd))
    if not stage:
        raise RuntimeError(f"cannot open source USD: {source_usd}")
    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render]
    )
    sockets: list[dict[str, Any]] = []
    for index in range(1, SOCKET_COUNT + 1):
        suffix = f"{index:02d}"
        mouth_prim = stage.GetPrimAtPath(
            f"/LabSpinX8/rotor_link/CavityMouthRing_{suffix}"
        )
        stop_prim = stage.GetPrimAtPath(
            f"/LabSpinX8/rotor_link/CavityStop_{suffix}"
        )
        if not mouth_prim or not stop_prim:
            raise ValueError(f"source rotor is missing socket geometry {suffix}")
        aperture = _vec(_center(cache.ComputeWorldBound(mouth_prim).ComputeAlignedRange()))
        bottom = _vec(_center(cache.ComputeWorldBound(stop_prim).ComputeAlignedRange()))
        axis_up = _normalise([aperture[i] - bottom[i] for i in range(3)])
        length = math.dist(aperture, bottom)
        sockets.append(
            {
                "id": f"tube_socket_{index - 1:02d}",
                "source_index": index,
                "aperture_rotor_local_m": aperture,
                "inserted_bottom_rotor_local_m": [
                    bottom[i] + axis_up[i] * SOCKET_FLOOR_THICKNESS_M
                    for i in range(3)
                ],
                "axis_out_rotor_local": axis_up,
                "qualified_sleeve_length_m": length,
                "inner_radius_m": SOCKET_INNER_RADIUS_M,
            }
        )
    return sockets


def _apply_mass(prim: Any, mass: float, com: tuple[float, float, float], inertia: tuple[float, float, float]) -> None:
    from pxr import Gf, UsdPhysics

    api = UsdPhysics.MassAPI.Apply(prim)
    api.CreateMassAttr(mass)
    api.CreateCenterOfMassAttr(Gf.Vec3f(*com))
    api.CreateDiagonalInertiaAttr(Gf.Vec3f(*inertia))


def _apply_physx_offsets(prim: Any) -> None:
    from pxr import Sdf

    schemas = list(prim.GetAppliedSchemas())
    if "PhysxCollisionAPI" not in schemas:
        schemas.append("PhysxCollisionAPI")
    prim.SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(schemas))
    prim.CreateAttribute(
        "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
    ).Set(INTERACTION_CONTACT_OFFSET_M)
    prim.CreateAttribute(
        "physxCollision:restOffset", Sdf.ValueTypeNames.Float
    ).Set(INTERACTION_REST_OFFSET_M)


def _cube_collider(stage: Any, path: str, translation: tuple[float, float, float], size: tuple[float, float, float], orient: Any | None = None) -> Any:
    from pxr import Gf, UsdGeom, UsdPhysics

    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    xform = UsdGeom.Xformable(cube)
    xform.AddTranslateOp().Set(Gf.Vec3d(*translation))
    if orient is not None:
        xform.AddOrientOp(UsdGeom.XformOp.PrecisionFloat).Set(orient)
    xform.AddScaleOp().Set(Gf.Vec3f(*size))
    cube.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    _apply_physx_offsets(cube.GetPrim())
    return cube.GetPrim()


def _build_visual_facade(source_usd: Path, destination: Path) -> Path:
    """Copy the visual stage and remove Blender link animation from the copy.

    The raw source remains byte-identical in ``deps/source``.  Dynamic control
    belongs to PhysX joints in the stronger package, so retaining the producer's
    presentation animation on those same rigid links would create competing
    motion authorities.
    """
    from pxr import Usd

    source = Usd.Stage.Open(str(source_usd))
    if not source:
        raise RuntimeError(f"cannot open source USD: {source_usd}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.Export(str(destination))
    facade = Usd.Stage.Open(str(destination))
    for link in (
        "lid_link",
        "rotor_link",
        "encoder_link",
        "start_button_link",
        "stop_button_link",
    ):
        prim = facade.GetPrimAtPath(f"/LabSpinX8/{link}")
        for property_name in (
            "xformOp:translate",
            "xformOp:rotateXYZ",
            "xformOp:scale",
            "xformOpOrder",
        ):
            prim.RemoveProperty(property_name)
    facade.GetRootLayer().Save()
    return destination


def _cylinder_collider(stage: Any, path: str, translation: tuple[float, float, float], radius: float, height: float, axis: str = "Z") -> Any:
    from pxr import Gf, UsdGeom, UsdPhysics

    cylinder = UsdGeom.Cylinder.Define(stage, path)
    cylinder.CreateRadiusAttr(radius)
    cylinder.CreateHeightAttr(height)
    cylinder.CreateAxisAttr(axis)
    UsdGeom.Xformable(cylinder).AddTranslateOp().Set(Gf.Vec3d(*translation))
    cylinder.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
    UsdPhysics.CollisionAPI.Apply(cylinder.GetPrim())
    _apply_physx_offsets(cylinder.GetPrim())
    return cylinder.GetPrim()


def _orient_z_to(axis: list[float]) -> Any:
    from pxr import Gf

    rotation = Gf.Rotation(Gf.Vec3d(0, 0, 1), Gf.Vec3d(*axis))
    quat = rotation.GetQuat()
    imag = quat.GetImaginary()
    return Gf.Quatf(float(quat.GetReal()), Gf.Vec3f(float(imag[0]), float(imag[1]), float(imag[2])))


def _author_identity_link_xform(prim: Any) -> None:
    from pxr import Gf, UsdGeom

    xform = UsdGeom.Xformable(prim)
    xform.SetXformOpOrder([])
    xform.AddTranslateOp(UsdGeom.XformOp.PrecisionFloat).Set(Gf.Vec3f(0, 0, 0))
    xform.AddOrientOp(UsdGeom.XformOp.PrecisionFloat).Set(
        Gf.Quatf(1.0, Gf.Vec3f(0, 0, 0))
    )
    xform.AddScaleOp(UsdGeom.XformOp.PrecisionFloat).Set(Gf.Vec3f(1, 1, 1))


def _author_joint(stage: Any, name: str, kind: str, body1: str, axis: str, local_pos0: tuple[float, float, float], lower: float | None = None, upper: float | None = None) -> Any:
    from pxr import Gf, Sdf, UsdPhysics

    path = f"{CENTRIFUGE_ENTRY}/{name}"
    if kind == "revolute":
        joint = UsdPhysics.RevoluteJoint.Define(stage, path)
        joint.CreateAxisAttr(axis)
        if lower is not None:
            joint.CreateLowerLimitAttr(lower)
        if upper is not None:
            joint.CreateUpperLimitAttr(upper)
    elif kind == "prismatic":
        joint = UsdPhysics.PrismaticJoint.Define(stage, path)
        joint.CreateAxisAttr(axis)
        if lower is not None:
            joint.CreateLowerLimitAttr(lower)
        if upper is not None:
            joint.CreateUpperLimitAttr(upper)
    else:
        raise ValueError(f"unsupported joint kind: {kind}")
    joint.CreateBody0Rel().SetTargets([Sdf.Path(f"{CENTRIFUGE_ENTRY}/base_link")])
    joint.CreateBody1Rel().SetTargets([Sdf.Path(body1)])
    joint.CreateLocalPos0Attr(Gf.Vec3f(*local_pos0))
    joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
    joint.CreateCollisionEnabledAttr(False)
    return joint


def _build_centrifuge_stage(package: Path, sockets: list[dict[str, Any]]) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    asset = package / "asset.usd"
    stage = Usd.Stage.CreateNew(str(asset))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    root = UsdGeom.Xform.Define(stage, CENTRIFUGE_ENTRY).GetPrim()
    root.GetReferences().AddReference("deps/facade/centrifuge_visual.usd", "/LabSpinX8")
    UsdPhysics.ArticulationRootAPI.Apply(root)

    # The source carries a 1x1 environment light.  It is provenance, not part
    # of the reusable device; review scenes own their lights.
    stage.OverridePrim(f"{CENTRIFUGE_ENTRY}/env_light").SetActive(False)

    base = stage.OverridePrim(f"{CENTRIFUGE_ENTRY}/base_link")
    _author_identity_link_xform(base)
    base_rb = UsdPhysics.RigidBodyAPI.Apply(base)
    base_rb.CreateKinematicEnabledAttr(False)
    _apply_mass(base, 18.5, (0.0, 0.0, 0.13), (0.38, 0.46, 0.68))
    base_fixed = UsdPhysics.FixedJoint.Define(
        stage, f"{CENTRIFUGE_ENTRY}/base_link/base_fixed_joint"
    )
    base_fixed.CreateBody0Rel().SetTargets([Sdf.Path(CENTRIFUGE_ENTRY)])
    base_fixed.CreateBody1Rel().SetTargets(
        [Sdf.Path(f"{CENTRIFUGE_ENTRY}/base_link")]
    )
    base_fixed.CreateCollisionEnabledAttr(False)

    lid = stage.OverridePrim(f"{CENTRIFUGE_ENTRY}/lid_link")
    _author_identity_link_xform(lid)
    UsdPhysics.RigidBodyAPI.Apply(lid)
    _apply_mass(lid, 2.2, (0.0, -0.19, 0.025), (0.030, 0.041, 0.067))

    rotor = stage.OverridePrim(f"{CENTRIFUGE_ENTRY}/rotor_link")
    _author_identity_link_xform(rotor)
    UsdPhysics.RigidBodyAPI.Apply(rotor)
    _apply_mass(rotor, 1.45, (0.0, 0.0, 0.0), (0.0082, 0.0082, 0.0150))

    for link, mass in (("encoder_link", 0.08), ("start_button_link", 0.02), ("stop_button_link", 0.02)):
        prim = stage.OverridePrim(f"{CENTRIFUGE_ENTRY}/{link}")
        _author_identity_link_xform(prim)
        UsdPhysics.RigidBodyAPI.Apply(prim)
        _apply_mass(prim, mass, (0.0, 0.0, 0.0), (0.000018, 0.000018, 0.000018))

    base_proxy = f"{CENTRIFUGE_ENTRY}/base_link/__aan_collision_proxy"
    UsdGeom.Xform.Define(stage, base_proxy)
    for name, translation, size in (
        ("lower", (0.0, 0.0, 0.105), (0.54, 0.47, 0.17)),
        ("left", (-0.251, 0.0, 0.251), (0.038, 0.422, 0.12)),
        ("right", (0.2195, 0.0, 0.251), (0.101, 0.422, 0.12)),
        ("front", (-0.03, -0.213, 0.251), (0.44, 0.044, 0.12)),
        ("rear", (-0.03, 0.216, 0.251), (0.44, 0.038, 0.12)),
    ):
        _cube_collider(stage, f"{base_proxy}/{name}", translation, size)

    lid_proxy = f"{CENTRIFUGE_ENTRY}/lid_link/__aan_collision_proxy"
    UsdGeom.Xform.Define(stage, lid_proxy)
    _cube_collider(stage, f"{lid_proxy}/front_shell", (0.0, -0.157, 0.021), (0.452, 0.074, 0.040))
    _cube_collider(stage, f"{lid_proxy}/main_shell", (0.0, -0.046, 0.021), (0.490, 0.250, 0.040))
    _cube_collider(stage, f"{lid_proxy}/handle_grip", (0.0, -0.416, 0.051), (0.190, 0.025, 0.027))
    _cube_collider(stage, f"{lid_proxy}/handle_post_left", (-0.081, -0.382, 0.044), (0.024, 0.075, 0.040))
    _cube_collider(stage, f"{lid_proxy}/handle_post_right", (0.081, -0.382, 0.044), (0.024, 0.075, 0.040))

    rotor_proxy = f"{CENTRIFUGE_ENTRY}/rotor_link/__aan_collision_proxy"
    UsdGeom.Xform.Define(stage, rotor_proxy)
    _cylinder_collider(stage, f"{rotor_proxy}/hub", (0.0, 0.0, -0.005), 0.038, 0.09)
    wall_radius = (SOCKET_INNER_RADIUS_M + SOCKET_OUTER_RADIUS_M) * 0.5
    wall_thickness = SOCKET_OUTER_RADIUS_M - SOCKET_INNER_RADIUS_M
    tangent_width = 2.0 * SOCKET_OUTER_RADIUS_M * math.tan(math.pi / SOCKET_WALL_PANELS)
    for index, socket in enumerate(sockets):
        aperture = socket["aperture_rotor_local_m"]
        bottom = socket["inserted_bottom_rotor_local_m"]
        axis = socket["axis_out_rotor_local"]
        length = socket["qualified_sleeve_length_m"]
        centre = [(aperture[i] + bottom[i]) * 0.5 for i in range(3)]
        socket_path = f"{rotor_proxy}/socket_{index:02d}"
        socket_xform = UsdGeom.Xform.Define(stage, socket_path)
        socket_xform.AddTranslateOp().Set(Gf.Vec3d(*centre))
        socket_xform.AddOrientOp(UsdGeom.XformOp.PrecisionFloat).Set(_orient_z_to(axis))
        for panel in range(SOCKET_WALL_PANELS):
            angle = 2.0 * math.pi * panel / SOCKET_WALL_PANELS
            orient = Gf.Quatf(math.cos(angle * 0.5), Gf.Vec3f(0, 0, math.sin(angle * 0.5)))
            _cube_collider(
                stage,
                f"{socket_path}/wall_{panel:02d}",
                (wall_radius * math.cos(angle), wall_radius * math.sin(angle), 0.0),
                (wall_thickness, tangent_width, length),
                orient,
            )
        _cylinder_collider(
            stage,
            f"{socket_path}/floor",
            (0.0, 0.0, -length * 0.5 + SOCKET_FLOOR_THICKNESS_M * 0.5),
            SOCKET_INNER_RADIUS_M,
            SOCKET_FLOOR_THICKNESS_M,
        )

    # Small control colliders are retained for later task expansion.
    _cylinder_collider(stage, f"{CENTRIFUGE_ENTRY}/encoder_link/__aan_collision_proxy/knob", (0, 0, 0), 0.018, 0.012, "Y")
    _cylinder_collider(stage, f"{CENTRIFUGE_ENTRY}/start_button_link/__aan_collision_proxy/button", (0, 0, 0), 0.016, 0.010, "Y")
    _cylinder_collider(stage, f"{CENTRIFUGE_ENTRY}/stop_button_link/__aan_collision_proxy/button", (0, 0, 0), 0.016, 0.010, "Y")

    lid_joint = _author_joint(stage, "lid_hinge_joint", "revolute", f"{CENTRIFUGE_ENTRY}/lid_link", "X", (0.0, 0.205, 0.326), -78.0, 0.0)
    lid_drive = UsdPhysics.DriveAPI.Apply(lid_joint.GetPrim(), "angular")
    lid_drive.CreateTypeAttr("force")
    lid_drive.CreateStiffnessAttr(0.0)
    lid_drive.CreateDampingAttr(1.0)
    lid_drive.CreateMaxForceAttr(48.0)

    rotor_joint = _author_joint(stage, "rotor_spin_joint", "revolute", f"{CENTRIFUGE_ENTRY}/rotor_link", "Z", (-0.03, 0.005, 0.27))
    rotor_drive = UsdPhysics.DriveAPI.Apply(rotor_joint.GetPrim(), "angular")
    rotor_drive.CreateTypeAttr("force")
    rotor_drive.CreateStiffnessAttr(0.0)
    rotor_drive.CreateDampingAttr(0.018)
    rotor_drive.CreateMaxForceAttr(12.0)
    rotor_drive.CreateTargetVelocityAttr(0.0)

    encoder_joint = _author_joint(stage, "encoder_joint", "revolute", f"{CENTRIFUGE_ENTRY}/encoder_link", "Y", (0.074, -0.267, 0.145))
    encoder_drive = UsdPhysics.DriveAPI.Apply(encoder_joint.GetPrim(), "angular")
    encoder_drive.CreateStiffnessAttr(0.0)
    encoder_drive.CreateDampingAttr(0.06)
    encoder_drive.CreateMaxForceAttr(0.7)
    for name, x in (("start_button_joint", 0.151), ("stop_button_joint", 0.205)):
        joint = _author_joint(stage, name, "prismatic", f"{CENTRIFUGE_ENTRY}/{name.replace('_joint', '_link')}", "Y", (x, -0.2675, 0.145), 0.0, 0.0025)
        drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "linear")
        drive.CreateStiffnessAttr(120.0)
        drive.CreateDampingAttr(2.0)
        drive.CreateMaxForceAttr(4.0)
        drive.CreateTargetPositionAttr(0.0)

    stage.GetRootLayer().Save()
    return asset


def _build_native_tube_stage(package: Path) -> Path:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    asset = package / "asset.usd"
    stage = Usd.Stage.CreateNew(str(asset))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    root = UsdGeom.Xform.Define(stage, NATIVE_TUBE_ENTRY).GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(root)
    _apply_mass(root, 0.016, (0.0, 0.0, 0.053), (0.000018, 0.000018, 0.000004))
    visual = UsdGeom.Xform.Define(stage, f"{NATIVE_TUBE_ENTRY}/Visual")
    body = UsdGeom.Xform.Define(stage, f"{NATIVE_TUBE_ENTRY}/Visual/Body")
    body.GetPrim().GetReferences().AddReference("deps/source/tube_body.usd", "/TubeBody")
    UsdGeom.Xformable(body).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.057))
    cap = UsdGeom.Xform.Define(stage, f"{NATIVE_TUBE_ENTRY}/Visual/Cap")
    cap.GetPrim().GetReferences().AddReference("deps/source/tube_cap.usd", "/TubeCap")
    UsdGeom.Xformable(cap).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.057))
    stage.OverridePrim(f"{NATIVE_TUBE_ENTRY}/Visual/Body/env_light").SetActive(False)
    stage.OverridePrim(f"{NATIVE_TUBE_ENTRY}/Visual/Cap/env_light").SetActive(False)
    proxy = f"{NATIVE_TUBE_ENTRY}/__aan_collision_proxy"
    UsdGeom.Xform.Define(stage, proxy)
    _cylinder_collider(stage, f"{proxy}/body", (0, 0, 0.050), 0.00830, 0.100)
    _cylinder_collider(stage, f"{proxy}/cap", (0, 0, 0.104), 0.01170, 0.016)
    stage.GetRootLayer().Save()
    return asset


def _build_existing_tube_compatibility_package(
    source_package: Path, package: Path
) -> tuple[Path, Path]:
    """Bind the admitted r7 tube to small-clearance contact offsets.

    The source package is copied byte-for-byte under ``deps/source_package``.
    Geometry, mass and collider dimensions remain inherited; only PhysX
    contact/rest offsets are stronger in this device-compatibility facade.
    """
    from pxr import Sdf, Usd, UsdGeom, UsdShade

    source_copy = package / "deps/source_package"
    shutil.copytree(source_package, source_copy)
    asset = package / "asset.usd"
    stage = Usd.Stage.CreateNew(str(asset))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    root = UsdGeom.Xform.Define(stage, EXISTING_TUBE_ENTRY).GetPrim()
    root.GetReferences().AddReference(
        "deps/source_package/asset.usd", EXISTING_TUBE_ENTRY
    )
    for collider in ("body", "cap"):
        prim = stage.OverridePrim(
            f"{EXISTING_TUBE_ENTRY}/__aan_collision_proxy/{collider}"
        )
        _apply_physx_offsets(prim)
    material = UsdShade.Material.Define(
        stage, f"{EXISTING_TUBE_ENTRY}/__aan_labspin_insert_material"
    )
    material_prim = material.GetPrim()
    material_prim.SetMetadata(
        "apiSchemas",
        Sdf.TokenListOp.Create(
            prependedItems=["PhysicsMaterialAPI", "PhysxMaterialAPI"]
        ),
    )
    material_prim.CreateAttribute(
        "physics:staticFriction", Sdf.ValueTypeNames.Float
    ).Set(0.05)
    material_prim.CreateAttribute(
        "physics:dynamicFriction", Sdf.ValueTypeNames.Float
    ).Set(0.05)
    material_prim.CreateAttribute(
        "physics:restitution", Sdf.ValueTypeNames.Float
    ).Set(0.0)
    material_prim.CreateAttribute(
        "physxMaterial:frictionCombineMode", Sdf.ValueTypeNames.Token
    ).Set("min")
    for collider in ("body", "cap"):
        prim = stage.GetPrimAtPath(
            f"{EXISTING_TUBE_ENTRY}/__aan_collision_proxy/{collider}"
        )
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(
            material, materialPurpose="physics"
        )
    stage.GetRootLayer().Save()
    profile = package / "interaction/profile.json"
    source_asset = source_package / "asset.usd"
    _write_json(
        profile,
        {
            "schema_version": "aan.interaction_contract.v1",
            "profile_id": "scientific_workbench.centrifuge_tube_15ml_closed.labspin_x8_compat.r1",
            "asset_entry_prim": EXISTING_TUBE_ENTRY,
            "source_package_asset_usd_sha256": _sha_file(source_asset),
            "geometry_and_mass_inherited_unchanged": True,
            "contact_offset_m": INTERACTION_CONTACT_OFFSET_M,
            "rest_offset_m": INTERACTION_REST_OFFSET_M,
            "insertion_material": {
                "static_friction": 0.05,
                "dynamic_friction": 0.05,
                "friction_combine_mode": "min",
            },
            "device_compatibility": "labspin_x8_24_socket_rotor",
        },
    )
    return asset, profile


def _device_profile(sockets: list[dict[str, Any]], asset_sha: str) -> dict[str, Any]:
    return {
        "schema_version": "aan.articulated_device_profile.v1",
        "profile_id": "labspin_x8.centrifuge.r1",
        "revision": "r1-source-bound-candidate",
        "asset_entry_prim": CENTRIFUGE_ENTRY,
        "articulation_root_prim": CENTRIFUGE_ENTRY,
        "asset_usd_sha256": asset_sha,
        "capacity": SOCKET_COUNT,
        "mounting": {"motion_mode": "fixed_base", "support_frame_root_local_m": [0.0, 0.0, 0.0]},
        "joints": {
            "lid": {
                "joint_prim": f"{CENTRIFUGE_ENTRY}/lid_hinge_joint",
                "part_prim": f"{CENTRIFUGE_ENTRY}/lid_link",
                "states": {"closed": [-0.05, 0.0], "open": [-1.361356817, -1.20]},
                "robot_contact_drive_mode": "passive_damped",
            },
            "rotor": {
                "joint_prim": f"{CENTRIFUGE_ENTRY}/rotor_spin_joint",
                "part_prim": f"{CENTRIFUGE_ENTRY}/rotor_link",
                "low_speed_target_rad_s": LOW_SPEED_TARGET_RAD_S,
            },
        },
        "named_frames": {
            "lid_handle_grasp": {
                "parent_prim": f"{CENTRIFUGE_ENTRY}/lid_link",
                "translation_parent_local_m": [0.0, -0.416, 0.051],
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            }
        },
        "tube_sockets": sockets,
        "balanced_pairs": [
            [f"tube_socket_{index:02d}", f"tube_socket_{index + 12:02d}"]
            for index in range(12)
        ],
        "required_runtime_task_gates": [
            "load_render_step_reset",
            "lid_contact_cycle",
            "socket_insertion_native_24",
            "socket_insertion_existing_15ml_24",
            "lid_close_with_inserted_tube",
            "balanced_pair_low_speed_spin",
        ],
    }


def build_labspin_x8_assets(
    source_archive: Path,
    output_root: Path,
    existing_15ml_package: Path = DEFAULT_EXISTING_15ML_PACKAGE,
) -> dict[str, Path]:
    source_archive = source_archive.resolve()
    output_root = output_root.resolve()
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)
    centrifuge_package = output_root / "centrifuge/package"
    tube_package = output_root / "native_tube_closed/package"
    existing_compat_package = output_root / "existing_15ml_compatible/package"
    centrifuge_source = centrifuge_package / "deps/source/centrifuge.usd"
    tube_body_source = tube_package / "deps/source/tube_body.usd"
    tube_cap_source = tube_package / "deps/source/tube_cap.usd"
    with zipfile.ZipFile(source_archive) as archive:
        member_hashes = {
            SOURCE_CENTRIFUGE: _extract_member(archive, SOURCE_CENTRIFUGE, centrifuge_source),
            SOURCE_ARTICULATION: _extract_member(archive, SOURCE_ARTICULATION, centrifuge_package / "deps/source/centrifuge_articulated.usda"),
            SOURCE_ENV: _extract_member(archive, SOURCE_ENV, centrifuge_package / "deps/source/textures/color_020306.exr"),
            SOURCE_TUBE_BODY: _extract_member(archive, SOURCE_TUBE_BODY, tube_body_source),
            SOURCE_TUBE_CAP: _extract_member(archive, SOURCE_TUBE_CAP, tube_cap_source),
        }
        # The two referenced source USDs each expect the same package-relative
        # 1x1 environment texture even though the facade disables those lights.
        env = archive.read(SOURCE_ENV)
        for target in (
            tube_package / "deps/source/textures/color_020306.exr",
        ):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(env)

    sockets = _socket_measurements(centrifuge_source)
    visual_facade = _build_visual_facade(
        centrifuge_source,
        centrifuge_package / "deps/facade/centrifuge_visual.usd",
    )
    facade_texture = centrifuge_package / "deps/facade/textures/color_020306.exr"
    facade_texture.parent.mkdir(parents=True, exist_ok=True)
    facade_texture.write_bytes(
        (centrifuge_package / "deps/source/textures/color_020306.exr").read_bytes()
    )
    centrifuge_asset = _build_centrifuge_stage(centrifuge_package, sockets)
    native_tube_asset = _build_native_tube_stage(tube_package)
    existing_compat_asset: Path | None = None
    existing_compat_profile: Path | None = None
    if (existing_15ml_package / "asset.usd").is_file():
        existing_compat_asset, existing_compat_profile = (
            _build_existing_tube_compatibility_package(
                existing_15ml_package.resolve(), existing_compat_package
            )
        )
    device_profile = centrifuge_package / "articulation/device_profile.json"
    _write_json(device_profile, _device_profile(sockets, _sha_file(centrifuge_asset)))
    native_tube_profile = tube_package / "interaction/profile.json"
    _write_json(
        native_tube_profile,
        {
            "schema_version": "aan.interaction_contract.v1",
            "profile_id": "labspin_x8.native_15ml_closed.r1",
            "asset_entry_prim": NATIVE_TUBE_ENTRY,
            "asset_usd_sha256": _sha_file(native_tube_asset),
            "closure_type": "snap_lip_non_threaded",
            "threaded_closure": False,
            "named_frames": {
                "support": {"translation_body_local_m": [0.0, 0.0, 0.0]},
                "grasp": {"translation_body_local_m": [0.0, 0.0, 0.065]},
            },
        },
    )
    manifest = centrifuge_package / "evidence/manifest.json"
    _write_json(
        manifest,
        {
            "schema_version": "asset_application_normalizer.v1",
            "package_id": "labspin_x8_centrifuge_r1_scenario-forge_isaac41",
            "asset_id": "labspin_x8_centrifuge",
            "asset_role": "articulated_object",
            "overall_status": "candidate_static_built",
            "blocked_reasons": ["isaac41_runtime_qualification_not_run"],
            "source": {
                "archive_path": str(source_archive),
                "archive_sha256": _sha_file(source_archive),
                "raw_files_unchanged": True,
                "member_sha256": member_hashes,
                "source_kind": "exported_asset_bundle_not_generator_source",
                "license": "LicenseRef-Internal-Restricted",
                "derived_visual_facade": {
                    "path": "deps/facade/centrifuge_visual.usd",
                    "sha256": _sha_file(visual_facade),
                    "change": "remove_blender_link_animation_for_physx_joint_authority",
                },
            },
            "entrypoints": {
                "root_usd": "asset.usd",
                "default_prim": "World",
                "asset_entry_prim": CENTRIFUGE_ENTRY,
                "asset_scope_prims": [CENTRIFUGE_ENTRY],
                "consumer_profile": "scenario-forge",
            },
            "capabilities": {
                "visual_materials": "authored_parameter_materials_with_1x1_environment_texture",
                "tube_capacity_geometry": 24,
                "native_tube_closure": "snap_lip_non_threaded",
            },
            "claims": {
                "robot_policy_success": False,
                "rated_high_speed_spin": False,
                "canonical_task_10_success": False,
                "threaded_tube_closure": False,
            },
        },
    )
    tube_manifest = tube_package / "evidence/manifest.json"
    _write_json(
        tube_manifest,
        {
            "schema_version": "asset_application_normalizer.v1",
            "package_id": "labspin_x8_native_15ml_closed_r1_scenario-forge_isaac41",
            "asset_id": "labspin_x8_native_15ml_closed",
            "asset_role": "rigid_object",
            "overall_status": "candidate_static_built",
            "blocked_reasons": ["isaac41_runtime_qualification_not_run"],
            "source": {
                "archive_path": str(source_archive),
                "archive_sha256": _sha_file(source_archive),
                "raw_files_unchanged": True,
                "member_sha256": {
                    SOURCE_TUBE_BODY: member_hashes[SOURCE_TUBE_BODY],
                    SOURCE_TUBE_CAP: member_hashes[SOURCE_TUBE_CAP],
                },
            },
            "entrypoints": {
                "root_usd": "asset.usd",
                "default_prim": "World",
                "asset_entry_prim": NATIVE_TUBE_ENTRY,
                "asset_scope_prims": [NATIVE_TUBE_ENTRY],
                "consumer_profile": "scenario-forge",
            },
            "claims": {"threaded_tube_closure": False, "robot_policy_success": False},
        },
    )
    result = {
        "centrifuge_asset": centrifuge_asset,
        "native_tube_asset": native_tube_asset,
        "device_profile": device_profile,
        "native_tube_profile": native_tube_profile,
        "manifest": manifest,
        "native_tube_manifest": tube_manifest,
    }
    if existing_compat_asset is not None and existing_compat_profile is not None:
        existing_manifest = existing_compat_package / "evidence/manifest.json"
        _write_json(
            existing_manifest,
            {
                "schema_version": "asset_application_normalizer.v1",
                "package_id": "scientific_workbench_15ml_closed_labspin_x8_compat_r1",
                "asset_id": "scientific_workbench_centrifuge_tube_15ml_closed_r7",
                "asset_role": "rigid_object",
                "overall_status": "candidate_static_built",
                "blocked_reasons": ["labspin_x8_runtime_qualification_not_run"],
                "source": {
                    "package_path": str(existing_15ml_package.resolve()),
                    "asset_usd_sha256": _sha_file(existing_15ml_package / "asset.usd"),
                    "geometry_and_mass_inherited_unchanged": True,
                },
                "entrypoints": {
                    "root_usd": "asset.usd",
                    "default_prim": "World",
                    "asset_entry_prim": EXISTING_TUBE_ENTRY,
                    "asset_scope_prims": [EXISTING_TUBE_ENTRY],
                    "consumer_profile": "scenario-forge",
                },
                "compatibility_override": {
                    "contact_offset_m": INTERACTION_CONTACT_OFFSET_M,
                    "rest_offset_m": INTERACTION_REST_OFFSET_M,
                    "static_friction": 0.05,
                    "dynamic_friction": 0.05,
                    "friction_combine_mode": "min",
                },
            },
        )
        result.update(
            {
                "existing_15ml_compat_asset": existing_compat_asset,
                "existing_15ml_compat_profile": existing_compat_profile,
                "existing_15ml_compat_manifest": existing_manifest,
            }
        )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--existing-15ml-package",
        type=Path,
        default=DEFAULT_EXISTING_15ML_PACKAGE,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_labspin_x8_assets(
        args.source_archive, args.out, args.existing_15ml_package
    )
    print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
