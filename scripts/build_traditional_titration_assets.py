#!/usr/bin/env python3
"""Build source-bound burette, stand, and fixed-base titration station packages."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Sequence
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.asset_application_normalizer.articulated_instance_layout import (  # noqa: E402
    audit_fixed_base_articulation_layout,
    author_fixed_base_articulation,
)


DEFAULT_ARCHIVE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_xinyu/traditional_titration_v1_v1.1.zip"
)
DEFAULT_REFERENCE_DOC = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_xinyu/Traditional_Titration_Burette_and_Stand_Asset_Reference.docx"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/traditional_titration_assets_r1_20260904"
OMNI_GLASS = Path(
    "/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/"
    "embodied-eval-os-sim-isaacsim41-genmanip-py310/lib/python3.10/"
    "site-packages/omni/mdl/core/Base/OmniGlass.mdl"
)
OMNI_GLASS_OPACITY = OMNI_GLASS.with_name("OmniGlass_Opacity.mdl")
STATION_ROOT = "/World/TitrationStation"
INSTANCE = STATION_ROOT + "/Instance"
BASE_LINK = INSTANCE + "/Body"
BASE_FIXED = INSTANCE + "/Joints/BaseFixed"


@dataclass(frozen=True)
class ReceiverColor:
    phase: str
    color: tuple[float, float, float]
    opacity: float


@dataclass(frozen=True)
class TitrationAssetsResult:
    output: Path
    burette_asset: Path
    stand_asset: Path
    station_asset: Path
    station_manifest: Path
    manifests: tuple[Path, ...]


def _lerp(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
    alpha: float,
) -> tuple[float, float, float]:
    return tuple(
        float(first[index] + (second[index] - first[index]) * alpha)
        for index in range(3)
    )


def receiver_liquid_color(dispensed_ml: float) -> ReceiverColor:
    colorless = (0.92, 0.97, 1.0)
    pale = (1.0, 0.48, 0.65)
    deep = (0.75, 0.02, 0.2)
    value = max(0.0, float(dispensed_ml))
    if value < 14.7:
        return ReceiverColor("colorless", colorless, 0.36)
    if value < 15.0:
        alpha = (value - 14.7) / 0.3
        return ReceiverColor(
            "transition", _lerp(colorless, pale, alpha), 0.36 + 0.32 * alpha
        )
    if value <= 15.3:
        return ReceiverColor("endpoint_pale_pink", pale, 0.68)
    alpha = min(1.0, (value - 15.3) / 1.0)
    return ReceiverColor("overshoot", _lerp(pale, deep, alpha), 0.68 + 0.10 * alpha)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _retarget_subtree(stage: Any, old_prefix: str, new_prefix: str) -> None:
    from pxr import Sdf

    old = Sdf.Path(old_prefix)
    new = Sdf.Path(new_prefix)
    for prim in stage.Traverse():
        for relationship in prim.GetRelationships():
            targets = relationship.GetTargets()
            rewritten = [
                target.ReplacePrefix(old, new) if target.HasPrefix(old) else target
                for target in targets
            ]
            if rewritten != targets:
                relationship.SetTargets(rewritten)
        for attribute in prim.GetAttributes():
            targets = attribute.GetConnections()
            rewritten = [
                target.ReplacePrefix(old, new) if target.HasPrefix(old) else target
                for target in targets
            ]
            if rewritten != targets:
                attribute.SetConnections(rewritten)


def _wrapper_asset(
    source: Path, source_prim: str, target_prim: str, destination: Path
) -> None:
    from pxr import Sdf, Usd, UsdGeom

    source_stage = Usd.Stage.Open(str(source))
    stage = Usd.Stage.CreateNew(str(destination))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    stage.GetRootLayer().Save()
    Sdf.CopySpec(
        source_stage.GetRootLayer(),
        source_prim,
        stage.GetRootLayer(),
        target_prim,
    )
    stage.GetRootLayer().Save()
    reopened = Usd.Stage.Open(str(destination))
    _retarget_subtree(reopened, source_prim, target_prim)
    reopened.GetRootLayer().Save()


def _copy_glass_dependencies(package: Path) -> None:
    destination = package / "deps/mdl"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OMNI_GLASS, destination / OMNI_GLASS.name)
    shutil.copy2(OMNI_GLASS_OPACITY, destination / OMNI_GLASS_OPACITY.name)


def _author_glass(stage: Any, package: Path, root: str) -> None:
    from pxr import Gf, Sdf, UsdShade

    _copy_glass_dependencies(package)
    material = UsdShade.Material.Define(stage, root + "/Materials/WebStandardGlass")
    shader = UsdShade.Shader.Define(stage, root + "/Materials/WebStandardGlass/Shader")
    shader.SetSourceAsset(Sdf.AssetPath("deps/mdl/OmniGlass.mdl"), "mdl")
    shader.SetSourceAssetSubIdentifier("OmniGlass", "mdl")
    for name, value, value_type in (
        ("cutout_opacity", 0.0, Sdf.ValueTypeNames.Float),
        ("depth", 0.002, Sdf.ValueTypeNames.Float),
        ("enable_opacity", False, Sdf.ValueTypeNames.Bool),
        ("frosting_roughness", 0.035, Sdf.ValueTypeNames.Float),
        ("glass_color", Gf.Vec3f(0.99, 0.998, 1.0), Sdf.ValueTypeNames.Color3f),
        ("glass_ior", 1.47, Sdf.ValueTypeNames.Float),
        ("reflection_color", Gf.Vec3f(1.0), Sdf.ValueTypeNames.Color3f),
        ("roughness_texture_influence", 1.0, Sdf.ValueTypeNames.Float),
        ("thin_walled", False, Sdf.ValueTypeNames.Bool),
    ):
        shader.CreateInput(name, value_type).Set(value)
    shader.CreateOutput("out", Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput("mdl").ConnectToSource(shader.ConnectableAPI(), "out")
    for suffix in (
        "/body_link/Visual/tube",
        "/body_link/Visual/glass_valve_neck",
        "/body_link/Visual/glass_outlet",
        "/body_link/Visual/delivery_tip",
    ):
        prim = stage.GetPrimAtPath(root + suffix)
        if prim:
            UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)


def _controller_source() -> str:
    return """import contextvars
import math
import omni.isaac.dynamic_control._dynamic_control as dynamic_control
import omni.usd
from pxr import Gf, UsdGeom

_ROOT = contextvars.ContextVar("titration_station_root", default="/World/TitrationStation")
_SUFFIX = "/Instance/Runtime/TitrationFlowGraph/FlowController"

class _Path:
    def __init__(self, suffix=""):
        self.suffix = suffix
    def __str__(self):
        return _ROOT.get() + self.suffix
    def __add__(self, suffix):
        return self.__class__(self.suffix + str(suffix))

ROOT = _Path()
INSTANCE = ROOT + "/Instance"
BODY = INSTANCE + "/Burette/body_link"
HANDLE = INSTANCE + "/Burette/stopcock_handle_link"
GRAPH = INSTANCE + "/Runtime/TitrationFlowGraph"
COLUMN = INSTANCE + "/Burette/body_link/Visual/liquid_column"
MENISCUS = INSTANCE + "/Burette/body_link/Visual/liquid_meniscus"

def _bind(db):
    node = str(db.node.get_prim_path())
    if not node.endswith(_SUFFIX):
        raise RuntimeError("unexpected titration controller path: " + node)
    _ROOT.set(node[:-len(_SUFFIX)])

def _prim(stage, path):
    return stage.GetPrimAtPath(str(path))

def _get(stage, path, name, default=None):
    prim = _prim(stage, path)
    attr = prim.GetAttribute(name) if prim else None
    value = attr.Get() if attr else None
    return default if value is None else value

def _set(stage, path, name, value):
    prim = _prim(stage, path)
    attr = prim.GetAttribute(name) if prim else None
    if attr and attr.Get() != value:
        attr.Set(value)

def _angle(stage, state):
    dc = state.dc or dynamic_control.acquire_dynamic_control_interface()
    state.dc = dc
    articulation = dc.get_articulation(str(ROOT))
    if articulation == dynamic_control.INVALID_HANDLE:
        _set(stage, ROOT, "titration:controller_pose_valid", False)
        return float(_get(stage, ROOT, "titration:stopcock_angle_deg", 0.0))
    dof = dc.find_articulation_dof(articulation, "stopcock_joint")
    if dof == dynamic_control.INVALID_HANDLE:
        _set(stage, ROOT, "titration:controller_pose_valid", False)
        return float(_get(stage, ROOT, "titration:stopcock_angle_deg", 0.0))
    _set(stage, ROOT, "titration:controller_pose_valid", True)
    angle = abs(math.degrees(float(dc.get_dof_position(dof))))
    return max(0.0, min(90.0, angle))

def _color(dispensed):
    colorless = (0.92, 0.97, 1.0)
    pale = (1.0, 0.48, 0.65)
    deep = (0.75, 0.02, 0.2)
    if dispensed < 14.7:
        return "colorless", colorless, 0.36
    if dispensed < 15.0:
        alpha = (dispensed - 14.7) / 0.3
        return "transition", tuple(colorless[i] + (pale[i]-colorless[i])*alpha for i in range(3)), 0.36 + 0.32*alpha
    if dispensed <= 15.3:
        return "endpoint_pale_pink", pale, 0.68
    alpha = min(1.0, (dispensed - 15.3) / 1.0)
    return "overshoot", tuple(pale[i] + (deep[i]-pale[i])*alpha for i in range(3)), 0.68 + 0.10*alpha

def _sync_column(stage, remaining, initial):
    height = 0.32 * max(0.0, min(1.0, remaining / initial))
    column = _prim(stage, COLUMN)
    meniscus = _prim(stage, MENISCUS)
    if column:
        UsdGeom.Cylinder(column).GetHeightAttr().Set(max(0.0001, height))
        column.GetAttribute("xformOp:translate").Set(Gf.Vec3d(0.0, 0.0, -0.09 + height/2.0))
        UsdGeom.Imageable(column).GetVisibilityAttr().Set("inherited" if height > 0.0001 else "invisible")
    if meniscus:
        meniscus.GetAttribute("xformOp:translate").Set(Gf.Vec3d(0.0, 0.0, -0.09 + height))
        UsdGeom.Imageable(meniscus).GetVisibilityAttr().Set("inherited" if height > 0.0001 else "invisible")

def _sync_receiver(stage, dispensed):
    root = _prim(stage, ROOT)
    targets = root.GetRelationship("titration:receiverLiquidShader").GetTargets() if root else []
    phase, color, opacity = _color(dispensed)
    _set(stage, ROOT, "titration:indicator_phase", phase)
    for target in targets:
        shader = stage.GetPrimAtPath(target)
        if not shader:
            continue
        for name in ("inputs:diffuseColor", "inputs:baseColor"):
            attr = shader.GetAttribute(name)
            if attr:
                attr.Set(Gf.Vec3f(*color))
        attr = shader.GetAttribute("inputs:opacity")
        if attr:
            attr.Set(float(opacity))
        attr = shader.GetAttribute("inputs:emissiveColor")
        if attr:
            attr.Set(Gf.Vec3f(*(float(channel) * 0.20 for channel in color)))
    visuals = root.GetRelationship("titration:receiverLiquidVisuals").GetTargets() if root else []
    for target in visuals:
        visual = stage.GetPrimAtPath(target)
        authored_phase = visual.GetAttribute("titration:phase").Get() if visual else None
        if visual:
            UsdGeom.Imageable(visual).GetVisibilityAttr().Set(
                "inherited" if authored_phase == phase else "invisible"
            )

def _reset(stage):
    for name, value in (
        ("titration:stopcock_angle_deg", 0.0),
        ("titration:valve_open_fraction", 0.0),
        ("titration:flow_rate_ml_s", 0.0),
        ("titration:burette_liquid_volume_ml", 25.0),
        ("titration:burette_liquid_level", 1.0),
        ("titration:dispensed_volume_ml", 0.0),
        ("titration:spilled_volume_ml", 0.0),
        ("titration:endpoint_hold_seconds", 0.0),
        ("titration:visited_open", False),
        ("titration:visited_fine", False),
        ("titration:visited_drip", False),
        ("titration:overshoot", False),
        ("titration:task_success", False),
        ("titration:indicator_phase", "colorless"),
        ("titration:reset_requested", False),
    ):
        _set(stage, ROOT, name, value)
    _sync_column(stage, 25.0, 25.0)
    _sync_receiver(stage, 0.0)

def setup(db):
    _bind(db)
    db.per_instance_state.dc = None

def compute(db):
    _bind(db)
    stage = omni.usd.get_context().get_stage()
    if stage is None or not _prim(stage, ROOT):
        return True
    if bool(_get(stage, ROOT, "titration:reset_requested", False)):
        _reset(stage)
        return True
    angle = _angle(stage, db.per_instance_state)
    if angle < 5.0:
        state, rate = "CLOSED", 0.0
    elif angle < 15.0:
        state, rate = "DRIP", 0.05
    elif angle < 40.0:
        state, rate = "FINE", 0.4
    else:
        state, rate = "OPEN", 2.0
    initial = 25.0
    remaining = max(0.0, float(_get(stage, ROOT, "titration:burette_liquid_volume_ml", initial)))
    dt = max(0.0, min(0.1, float(db.inputs.deltaSeconds)))
    dv = min(rate * dt, remaining)
    target = bool(_get(stage, ROOT, "titration:target_container_inside", False))
    dispensed = float(_get(stage, ROOT, "titration:dispensed_volume_ml", 0.0)) + (dv if target else 0.0)
    spilled = float(_get(stage, ROOT, "titration:spilled_volume_ml", 0.0)) + (0.0 if target else dv)
    remaining -= dv
    visited_open = bool(_get(stage, ROOT, "titration:visited_open", False)) or state == "OPEN"
    visited_fine = bool(_get(stage, ROOT, "titration:visited_fine", False)) or (visited_open and state == "FINE")
    visited_drip = bool(_get(stage, ROOT, "titration:visited_drip", False)) or (visited_fine and state == "DRIP")
    overshoot = bool(_get(stage, ROOT, "titration:overshoot", False)) or dispensed > 15.3
    in_window = 14.7 <= dispensed <= 15.3
    hold = float(_get(stage, ROOT, "titration:endpoint_hold_seconds", 0.0))
    hold = hold + dt if state == "CLOSED" and in_window and visited_drip and not overshoot else 0.0
    success = hold >= 3.0 and visited_open and visited_fine and visited_drip and not overshoot
    for name, value in (
        ("titration:stopcock_angle_deg", angle),
        ("titration:valve_open_fraction", angle/90.0),
        ("titration:valve_state", state),
        ("titration:flow_rate_ml_s", 0.0 if remaining <= 0.0 else rate),
        ("titration:burette_liquid_volume_ml", remaining),
        ("titration:burette_liquid_level", remaining/initial),
        ("titration:dispensed_volume_ml", dispensed),
        ("titration:spilled_volume_ml", spilled),
        ("titration:visited_open", visited_open),
        ("titration:visited_fine", visited_fine),
        ("titration:visited_drip", visited_drip),
        ("titration:endpoint_hold_seconds", hold),
        ("titration:overshoot", overshoot),
        ("titration:task_success", success),
    ):
        _set(stage, ROOT, name, value)
    _sync_column(stage, remaining, initial)
    _sync_receiver(stage, dispensed)
    return True

def cleanup(db):
    db.per_instance_state.dc = None
"""


def _author_state_interface(stage: Any) -> None:
    from pxr import Sdf

    root = stage.GetPrimAtPath(STATION_ROOT)
    for name, value, value_type in (
        ("titration:stopcock_angle_deg", 0.0, Sdf.ValueTypeNames.Float),
        ("titration:valve_open_fraction", 0.0, Sdf.ValueTypeNames.Float),
        ("titration:flow_rate_ml_s", 0.0, Sdf.ValueTypeNames.Float),
        ("titration:burette_liquid_volume_ml", 25.0, Sdf.ValueTypeNames.Float),
        ("titration:burette_liquid_level", 1.0, Sdf.ValueTypeNames.Float),
        ("titration:target_container_inside", False, Sdf.ValueTypeNames.Bool),
        ("titration:dispensed_volume_ml", 0.0, Sdf.ValueTypeNames.Float),
        ("titration:spilled_volume_ml", 0.0, Sdf.ValueTypeNames.Float),
        ("titration:endpoint_hold_seconds", 0.0, Sdf.ValueTypeNames.Float),
        ("titration:visited_open", False, Sdf.ValueTypeNames.Bool),
        ("titration:visited_fine", False, Sdf.ValueTypeNames.Bool),
        ("titration:visited_drip", False, Sdf.ValueTypeNames.Bool),
        ("titration:overshoot", False, Sdf.ValueTypeNames.Bool),
        ("titration:task_success", False, Sdf.ValueTypeNames.Bool),
        ("titration:controller_pose_valid", False, Sdf.ValueTypeNames.Bool),
        ("titration:reset_requested", False, Sdf.ValueTypeNames.Bool),
        ("titration:valve_state", "CLOSED", Sdf.ValueTypeNames.Token),
        ("titration:indicator_phase", "colorless", Sdf.ValueTypeNames.Token),
    ):
        root.CreateAttribute(name, value_type, custom=True).Set(value)
    root.CreateRelationship("titration:receiverLiquidShader", custom=True)
    root.CreateRelationship("titration:receiverLiquidVisuals", custom=True)


def _author_graph(stage: Any) -> None:
    from pxr import Gf, Sdf

    graph_path = INSTANCE + "/Runtime/TitrationFlowGraph"
    graph = stage.DefinePrim(graph_path, "OmniGraph")
    graph.CreateAttribute("evaluationMode", Sdf.ValueTypeNames.Token, custom=True).Set(
        "Automatic"
    )
    graph.CreateAttribute("evaluator:type", Sdf.ValueTypeNames.Token, custom=True).Set(
        "push"
    )
    graph.CreateAttribute(
        "fabricCacheBacking", Sdf.ValueTypeNames.Token, custom=True
    ).Set("Shared")
    graph.CreateAttribute(
        "fileFormatVersion", Sdf.ValueTypeNames.Int2, custom=True
    ).Set(Gf.Vec2i(1, 9))
    graph.CreateAttribute("pipelineStage", Sdf.ValueTypeNames.Token, custom=True).Set(
        "pipelineStageOnDemand"
    )
    tick = stage.DefinePrim(graph_path + "/OnPhysicsStep", "OmniGraphNode")
    tick.CreateAttribute("node:type", Sdf.ValueTypeNames.Token, custom=True).Set(
        "isaacsim.core.nodes.OnPhysicsStep"
    )
    tick.CreateAttribute("node:typeVersion", Sdf.ValueTypeNames.Int, custom=True).Set(1)
    tick.CreateAttribute("outputs:step", Sdf.ValueTypeNames.UInt, custom=True)
    tick.CreateAttribute(
        "outputs:deltaSimulationTime", Sdf.ValueTypeNames.Double, custom=True
    )
    controller = stage.DefinePrim(graph_path + "/FlowController", "OmniGraphNode")
    controller.CreateAttribute("node:type", Sdf.ValueTypeNames.Token, custom=True).Set(
        "omni.graph.scriptnode.ScriptNode"
    )
    controller.CreateAttribute(
        "node:typeVersion", Sdf.ValueTypeNames.Int, custom=True
    ).Set(2)
    controller.CreateAttribute(
        "inputs:script", Sdf.ValueTypeNames.String, custom=True
    ).Set(_controller_source())
    controller.CreateAttribute(
        "inputs:usePath", Sdf.ValueTypeNames.Bool, custom=True
    ).Set(False)
    controller.CreateAttribute(
        "inputs:scriptPath", Sdf.ValueTypeNames.Token, custom=True
    ).Set("")
    controller.CreateAttribute(
        "inputs:execIn", Sdf.ValueTypeNames.UInt, custom=True
    ).SetConnections([tick.GetPath().AppendProperty("outputs:step")])
    controller.CreateAttribute(
        "inputs:deltaSeconds", Sdf.ValueTypeNames.Double, custom=True
    ).SetConnections([tick.GetPath().AppendProperty("outputs:deltaSimulationTime")])


def _extend_station_clamp_for_stirrer(stage: Any) -> None:
    """Extend the station clamp over a separate stirrer on the work surface."""

    from pxr import Gf

    def set_z(path: str, z: float) -> None:
        prim = stage.GetPrimAtPath(path)
        attribute = prim.GetAttribute("xformOp:translate")
        value = attribute.Get()
        attribute.Set(Gf.Vec3d(float(value[0]), float(value[1]), z))

    def set_xyz(path: str, xyz: tuple[float, float, float]) -> None:
        stage.GetPrimAtPath(path).GetAttribute("xformOp:translate").Set(Gf.Vec3d(*xyz))

    for suffix in ("Visual/rod", "Collision/rod_proxy"):
        prim = stage.GetPrimAtPath(BASE_LINK + "/" + suffix)
        prim.GetAttribute("height").Set(0.56)
        set_z(BASE_LINK + "/" + suffix, 0.325)
    arm = stage.GetPrimAtPath(BASE_LINK + "/Visual/clamp_arm")
    arm.GetAttribute("xformOp:translate").Set(Gf.Vec3d(0.11, 0.0, 0.515))
    arm.GetAttribute("xformOp:scale").Set(Gf.Vec3f(0.22, 0.022, 0.018))
    set_xyz(BASE_LINK + "/Visual/single_clamp", (0.1825, 0.0, 0.515))
    set_xyz(BASE_LINK + "/Visual/clamp_cheek_left", (0.205, -0.024, 0.515))
    set_xyz(BASE_LINK + "/Visual/clamp_cheek_right", (0.205, 0.024, 0.515))
    set_xyz(BASE_LINK + "/Visual/clamp_fastener", (0.19, 0.0, 0.515))
    set_xyz(BASE_LINK + "/Collision/single_clamp_proxy", (0.1975, 0.0, 0.515))
    for scope in ("Visual", "Collision"):
        set_xyz(BASE_LINK + f"/{scope}/pad_left_upper", (0.223, -0.009, 0.524))
        set_xyz(BASE_LINK + f"/{scope}/pad_left_lower", (0.223, -0.009, 0.506))
        set_xyz(BASE_LINK + f"/{scope}/pad_right_upper", (0.223, 0.009, 0.524))
        set_xyz(BASE_LINK + f"/{scope}/pad_right_lower", (0.223, 0.009, 0.506))
    set_xyz(INSTANCE + "/Burette", (0.22, 0.0, 0.515))


def _build_station(source: Path, package: Path) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    package.mkdir(parents=True)
    asset = package / "asset.usd"
    source_stage = Usd.Stage.Open(str(source))
    stage = Usd.Stage.CreateNew(str(asset))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    root = UsdGeom.Xform.Define(stage, STATION_ROOT).GetPrim()
    xform = UsdGeom.Xformable(root)
    xform.AddTranslateOp().Set(Gf.Vec3d(0.0))
    xform.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(1.0))
    xform.AddScaleOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(1.0))
    UsdGeom.Xform.Define(stage, INSTANCE)
    UsdGeom.Scope.Define(stage, INSTANCE + "/StandMaterials")
    UsdGeom.Scope.Define(stage, INSTANCE + "/Frames")
    stage.GetRootLayer().Save()

    copies = (
        ("/World/BuretteStand/base", BASE_LINK),
        ("/World/BuretteStand/Materials", INSTANCE + "/StandMaterials"),
        (
            "/World/BuretteStand/burette_mount_frame",
            INSTANCE + "/Frames/burette_mount_frame",
        ),
        (
            "/World/BuretteStand/tip_clearance_zone",
            INSTANCE + "/Frames/tip_clearance_zone",
        ),
        ("/World/BuretteStand/support_plane", INSTANCE + "/Frames/support_plane"),
        ("/World/Burette", INSTANCE + "/Burette"),
    )
    for source_path, target_path in copies:
        Sdf.CopySpec(
            source_stage.GetRootLayer(),
            source_path,
            stage.GetRootLayer(),
            target_path,
        )
    stage.GetRootLayer().Save()
    stage = Usd.Stage.Open(str(asset))
    _retarget_subtree(stage, "/World/Burette", INSTANCE + "/Burette")
    _retarget_subtree(
        stage, "/World/BuretteStand/Materials", INSTANCE + "/StandMaterials"
    )
    _extend_station_clamp_for_stirrer(stage)
    burette_body = stage.GetPrimAtPath(INSTANCE + "/Burette/body_link")
    burette_body.RemoveAPI(UsdPhysics.ArticulationRootAPI)
    for prop in list(stage.GetPrimAtPath(INSTANCE + "/Burette").GetProperties()):
        if prop.GetName().startswith("titration:"):
            stage.GetPrimAtPath(INSTANCE + "/Burette").RemoveProperty(prop.GetName())
    author_fixed_base_articulation(
        stage,
        STATION_ROOT,
        base_link=BASE_LINK,
        fixed_joint=BASE_FIXED,
    )
    mount = UsdPhysics.FixedJoint.Define(stage, INSTANCE + "/Joints/StandToBurette")
    mount.CreateBody0Rel().SetTargets([BASE_LINK])
    mount.CreateBody1Rel().SetTargets([INSTANCE + "/Burette/body_link"])
    # The station-only stand extension places the source burette above and
    # beside the stand base without scaling the source 40 mm handle.
    mount.CreateLocalPos0Attr(Gf.Vec3f(0.22, 0.0, 0.515))
    mount.CreateLocalPos1Attr(Gf.Vec3f(0.0))
    mount.CreateLocalRot0Attr(Gf.Quatf(1.0))
    mount.CreateLocalRot1Attr(Gf.Quatf(1.0))
    mount.CreateCollisionEnabledAttr(False)
    mount.CreateExcludeFromArticulationAttr(False)
    _author_state_interface(stage)
    _author_graph(stage)
    _author_glass(stage, package, INSTANCE + "/Burette")
    root = stage.GetPrimAtPath(STATION_ROOT)
    root.SetCustomDataByKey("aan:assetRole", "articulated_object")
    root.SetCustomDataByKey("aan:controllerRevision", "titration-r1")
    stage.GetRootLayer().Save()
    audit = audit_fixed_base_articulation_layout(
        stage,
        STATION_ROOT,
        base_link=BASE_LINK,
        fixed_joint=BASE_FIXED,
    )
    if audit["status"] != "pass":
        raise RuntimeError(f"fixed-base station audit blocked: {audit}")
    _write_json(package / "evidence/fixed_base_articulation_audit.json", audit)
    return asset


def _base_manifest(
    *,
    package_id: str,
    role: str,
    entry_prim: str,
    archive: Path,
    reference_doc: Path,
    source_member: str,
) -> dict[str, Any]:
    return {
        "schema_version": "aan.traditional_titration_asset.v1",
        "package_id": package_id,
        "asset_role": role,
        "overall_status": "candidate_runtime_qualification_pending",
        "blocked_reasons": ["runtime qualification pending"],
        "entrypoints": {
            "root_usd": "asset.usd",
            "default_prim": "World",
            "asset_entry_prim": entry_prim,
        },
        "source": {
            "archive_path": str(archive),
            "archive_sha256": _sha(archive),
            "reference_doc_path": str(reference_doc),
            "reference_doc_sha256": _sha(reference_doc),
            "source_member": source_member,
            "source_unchanged": True,
        },
        "claims": {
            "isaac45_runtime_qualified": False,
            "isaac41_compatibility_checked": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }


def build(
    output: Path = DEFAULT_OUTPUT,
    *,
    archive: Path = DEFAULT_ARCHIVE,
    reference_doc: Path = DEFAULT_REFERENCE_DOC,
) -> TitrationAssetsResult:
    output = output.resolve()
    archive = archive.resolve()
    reference_doc = reference_doc.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    extracted = output / "input/source_archive"
    with zipfile.ZipFile(archive) as source_zip:
        source_zip.extractall(extracted)
    source_root = extracted / "traditional_titration_v1"
    shutil.copy2(
        reference_doc,
        output / "input/Traditional_Titration_Burette_and_Stand_Asset_Reference.docx",
    )

    packages = output / "packages"
    burette_package = packages / "burette"
    stand_package = packages / "stand"
    station_package = packages / "station"
    burette_package.mkdir(parents=True)
    stand_package.mkdir(parents=True)
    burette_asset = burette_package / "asset.usd"
    stand_asset = stand_package / "asset.usd"
    _wrapper_asset(
        source_root / "usd/burette.usd", "/Burette", "/World/Burette", burette_asset
    )
    _wrapper_asset(
        source_root / "usd/burette_stand.usd",
        "/BuretteStand",
        "/World/BuretteStand",
        stand_asset,
    )
    from pxr import Usd

    burette_stage = Usd.Stage.Open(str(burette_asset))
    _author_glass(burette_stage, burette_package, "/World/Burette")
    burette_stage.GetRootLayer().Save()
    station_asset = _build_station(
        source_root / "usd/titration_station_test.usd", station_package
    )

    manifests = []
    specs = (
        (
            burette_package,
            "traditional_titration_burette_r1",
            "floating_articulated_component",
            "/World/Burette",
            "traditional_titration_v1/usd/burette.usd",
        ),
        (
            stand_package,
            "traditional_titration_stand_r1",
            "static_support_component",
            "/World/BuretteStand",
            "traditional_titration_v1/usd/burette_stand.usd",
        ),
        (
            station_package,
            "traditional_titration_station_r1",
            "articulated_object",
            STATION_ROOT,
            "traditional_titration_v1/usd/titration_station_test.usd",
        ),
    )
    for package, package_id, role, entry, member in specs:
        manifest = _base_manifest(
            package_id=package_id,
            role=role,
            entry_prim=entry,
            archive=archive,
            reference_doc=reference_doc,
            source_member=member,
        )
        if role == "articulated_object":
            manifest["claims"].update(
                {
                    "fixed_base_articulation_authored": True,
                    "relocatable_controller_authored": True,
                    "falling_liquid_visuals_removed": True,
                }
            )
        path = package / "evidence/manifest.json"
        _write_json(path, manifest)
        manifests.append(path)
    return TitrationAssetsResult(
        output=output,
        burette_asset=burette_asset,
        stand_asset=stand_asset,
        station_asset=station_asset,
        station_manifest=station_package / "evidence/manifest.json",
        manifests=tuple(manifests),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--reference-doc", type=Path, default=DEFAULT_REFERENCE_DOC)
    args = parser.parse_args(argv)
    print(
        build(
            args.output, archive=args.archive, reference_doc=args.reference_doc
        ).station_asset
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
