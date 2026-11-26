"""Modular bimanual/single-arm URDF assembler for cross-embodiment SimReady robots.

Combines arbitrary arm URDFs (e.g., FR3, Flexiv Rizon 4S) and arbitrary end-effector
URDFs (e.g., Robotiq 2F-85, Flexiv Grav GN01, Wuji 20-DoF Dexterous Hand) onto a
shared pedestal base with clean left_/right_ namespacing, resolved mesh paths,
preserved mimic couplings, and standardized `{side}_grasp_frame` TCP links.
"""
from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


DEFAULT_MODULAR_ROBOTS_ROOT = Path("/mnt/data/wangyukai/gitee/GenManip-isaaclab/assets/robots/robots")


@dataclass(frozen=True)
class ArmMountSpec:
    """One arm + end-effector branch mounted onto the shared robot base."""

    side: str  # "left" or "right"
    arm_urdf: str
    arm_root_link: str
    arm_flange_link: str
    ee_urdf: str
    ee_root_link: str
    mount_xyz: tuple[float, float, float]
    mount_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ee_mount_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ee_mount_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0)
    grasp_frame_xyz: tuple[float, float, float] = (0.0, 0.0, 0.14)
    grasp_frame_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ee_type: str = "parallel_gripper"  # "parallel_gripper" or "dexterous_hand"
    strip_arm_links: tuple[str, ...] = ("world",)


@dataclass(frozen=True)
class BimanualAssemblySpec:
    """Declarative specification for assembling a bimanual (or single-arm) robot."""

    robot_id: str
    arms: tuple[ArmMountSpec, ...]
    pedestal_height_m: float = 0.78
    pedestal_width_y_m: float = 0.56
    pedestal_depth_x_m: float = 0.24
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RobotAssemblyResult:
    """Paths and structured kinematic metadata produced by `assemble_bimanual_urdf`."""

    robot_id: str
    urdf_path: str
    meta_path: str
    arm_joints: dict[str, list[str]]
    ee_joints: dict[str, list[str]]
    ee_driver_joints: dict[str, list[str]]
    mimic_joints: dict[str, dict[str, dict[str, Any]]]
    grasp_frames: dict[str, str]
    flange_frames: dict[str, str]
    joint_limits: dict[str, dict[str, float]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _fmt_vec3(v: tuple[float, float, float]) -> str:
    return f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}"


def _resolve_mesh_paths(elem: ET.Element, urdf_dir: Path) -> None:
    for mesh in elem.iter("mesh"):
        fname = mesh.attrib.get("filename", "")
        if not fname:
            continue
        if fname.startswith("package://"):
            continue
        p = Path(fname)
        if not p.is_absolute():
            resolved = (urdf_dir / p).resolve()
            mesh.attrib["filename"] = str(resolved)


def _parse_component(
    urdf_path: Path,
    prefix: str,
    strip_links: tuple[str, ...] = (),
) -> tuple[list[ET.Element], list[ET.Element], dict[str, dict[str, float]], dict[str, dict[str, Any]]]:
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    urdf_dir = urdf_path.parent
    strip_set = set(strip_links)

    links: list[ET.Element] = []
    joints: list[ET.Element] = []
    limits: dict[str, dict[str, float]] = {}
    mimics: dict[str, dict[str, Any]] = {}

    for link in root.findall("link"):
        orig_name = link.attrib["name"]
        if orig_name in strip_set:
            continue
        cloned = copy.deepcopy(link)
        cloned.attrib["name"] = f"{prefix}{orig_name}"
        _resolve_mesh_paths(cloned, urdf_dir)
        # Ensure every link has a valid non-singular inertial block so PhysX URDFImporter never stalls
        inertial = cloned.find("inertial")
        if inertial is None:
            inertial = ET.SubElement(cloned, "inertial")
            ET.SubElement(inertial, "origin", {"xyz": "0 0 0", "rpy": "0 0 0"})
            ET.SubElement(inertial, "mass", {"value": "0.02"})
            ET.SubElement(
                inertial,
                "inertia",
                {"ixx": "2e-5", "ixy": "0", "ixz": "0", "iyy": "2e-5", "iyz": "0", "izz": "2e-5"},
            )
        else:
            mass_el = inertial.find("mass")
            if mass_el is None:
                ET.SubElement(inertial, "mass", {"value": "0.02"})
            else:
                try:
                    mval = float(mass_el.attrib.get("value", "0"))
                except ValueError:
                    mval = 0.0
                if mval < 0.01:
                    mass_el.attrib["value"] = "0.02"
            iner_el = inertial.find("inertia")
            if iner_el is None:
                ET.SubElement(
                    inertial,
                    "inertia",
                    {"ixx": "2e-5", "ixy": "0", "ixz": "0", "iyy": "2e-5", "iyz": "0", "izz": "2e-5"},
                )
            else:
                for diag in ("ixx", "iyy", "izz"):
                    try:
                        dval = float(iner_el.attrib.get(diag, "0"))
                    except ValueError:
                        dval = 0.0
                    if dval < 2e-5:
                        iner_el.attrib[diag] = "2e-5"
        links.append(cloned)

    for joint in root.findall("joint"):
        parent_el = joint.find("parent")
        child_el = joint.find("child")
        if parent_el is None or child_el is None:
            continue
        if parent_el.attrib["link"] in strip_set or child_el.attrib["link"] in strip_set:
            continue
        cloned = copy.deepcopy(joint)
        jname = f"{prefix}{cloned.attrib['name']}"
        cloned.attrib["name"] = jname
        cloned.find("parent").attrib["link"] = f"{prefix}{parent_el.attrib['link']}"  # type: ignore[union-attr]
        cloned.find("child").attrib["link"] = f"{prefix}{child_el.attrib['link']}"  # type: ignore[union-attr]

        mimic_el = cloned.find("mimic")
        if mimic_el is not None:
            ref_joint = f"{prefix}{mimic_el.attrib['joint']}"
            mimics[jname] = {
                "joint": ref_joint,
                "multiplier": float(mimic_el.attrib.get("multiplier", "1.0")),
                "offset": float(mimic_el.attrib.get("offset", "0.0")),
            }
            # Remove <mimic> from URDF XML so PhysX URDFImporter never creates cyclic
            # PhysxMimicJointAPI constraints (e.g. Flexiv 4-bar linkage); the runtime
            # drives mimic couplings deterministically via robot_assembly_meta.json.
            cloned.remove(mimic_el)

        jtype = cloned.attrib.get("type", "fixed")
        if jtype in ("revolute", "prismatic", "continuous"):
            lim_el = cloned.find("limit")
            if lim_el is not None:
                vel_val = float(lim_el.attrib.get("velocity", "2.0"))
                # Realistic gripper/hand closing speed (e.g. Robotiq 2F-85 URDF ships with
                # an overly slow 0.5 rad/s limit that prevents closing within 40 sim steps).
                if prefix.endswith("_ee_") and jtype == "revolute" and vel_val < 2.0:
                    vel_val = 2.0
                    lim_el.attrib["velocity"] = f"{vel_val:.3f}"
                limits[jname] = {
                    "lower": float(lim_el.attrib.get("lower", "-3.14159")),
                    "upper": float(lim_el.attrib.get("upper", "3.14159")),
                    "effort": float(lim_el.attrib.get("effort", "50.0")),
                    "velocity": vel_val,
                }
            else:
                limits[jname] = {"lower": -3.14159, "upper": 3.14159, "effort": 50.0, "velocity": 2.0}
        joints.append(cloned)

    return links, joints, limits, mimics


def _add_fixed_joint(
    parent_robot: ET.Element,
    name: str,
    parent_link: str,
    child_link: str,
    xyz: tuple[float, float, float],
    rpy: tuple[float, float, float],
) -> None:
    j = ET.SubElement(parent_robot, "joint", {"name": name, "type": "fixed"})
    ET.SubElement(j, "origin", {"xyz": _fmt_vec3(xyz), "rpy": _fmt_vec3(rpy)})
    ET.SubElement(j, "parent", {"link": parent_link})
    ET.SubElement(j, "child", {"link": child_link})


def _add_pedestal_base(robot_el: ET.Element, spec: BimanualAssemblySpec) -> str:
    base_name = "pedestal_base_link"
    link = ET.SubElement(robot_el, "link", {"name": base_name})
    h = spec.pedestal_height_m
    w = spec.pedestal_width_y_m
    d = spec.pedestal_depth_x_m

    inertial = ET.SubElement(link, "inertial")
    ET.SubElement(inertial, "origin", {"xyz": f"0 0 {h * 0.5:.4f}", "rpy": "0 0 0"})
    ET.SubElement(inertial, "mass", {"value": "35.0"})
    ET.SubElement(
        inertial,
        "inertia",
        {"ixx": "1.2", "ixy": "0", "ixz": "0", "iyy": "1.2", "iyz": "0", "izz": "0.8"},
    )

    vis = ET.SubElement(link, "visual")
    ET.SubElement(vis, "origin", {"xyz": f"0 0 {h * 0.5:.4f}", "rpy": "0 0 0"})
    geom = ET.SubElement(vis, "geometry")
    ET.SubElement(geom, "box", {"size": f"{d:.4f} {w:.4f} {h:.4f}"})
    mat = ET.SubElement(vis, "material", {"name": "pedestal_matte_dark"})
    ET.SubElement(mat, "color", {"rgba": "0.18 0.20 0.22 1.0"})

    col = ET.SubElement(link, "collision")
    ET.SubElement(col, "origin", {"xyz": f"0 0 {h * 0.5:.4f}", "rpy": "0 0 0"})
    cgeom = ET.SubElement(col, "geometry")
    ET.SubElement(cgeom, "box", {"size": f"{d:.4f} {w:.4f} {h:.4f}"})

    return base_name


def assemble_bimanual_urdf(spec: BimanualAssemblySpec, output_dir: str | Path) -> RobotAssemblyResult:
    """Assemble modular arm + end-effector URDFs into a unified bimanual URDF + metadata."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    robot_el = ET.Element("robot", {"name": spec.robot_id})
    base_link = _add_pedestal_base(robot_el, spec)

    arm_joints: dict[str, list[str]] = {}
    ee_joints: dict[str, list[str]] = {}
    ee_driver_joints: dict[str, list[str]] = {}
    all_mimics: dict[str, dict[str, dict[str, Any]]] = {}
    grasp_frames: dict[str, str] = {}
    flange_frames: dict[str, str] = {}
    all_limits: dict[str, dict[str, float]] = {}

    for arm in spec.arms:
        side = arm.side
        arm_prefix = f"{side}_arm_"
        ee_prefix = f"{side}_ee_"

        a_links, a_joints, a_limits, a_mimics = _parse_component(
            Path(arm.arm_urdf), prefix=arm_prefix, strip_links=arm.strip_arm_links
        )
        e_links, e_joints, e_limits, e_mimics = _parse_component(
            Path(arm.ee_urdf), prefix=ee_prefix, strip_links=()
        )

        for el in a_links:
            robot_el.append(el)
        for el in a_joints:
            robot_el.append(el)

        # Mount arm root onto pedestal
        _add_fixed_joint(
            robot_el,
            name=f"{side}_pedestal_to_arm",
            parent_link=base_link,
            child_link=f"{arm_prefix}{arm.arm_root_link}",
            xyz=arm.mount_xyz,
            rpy=arm.mount_rpy,
        )

        for el in e_links:
            robot_el.append(el)
        for el in e_joints:
            robot_el.append(el)

        flange_link = f"{arm_prefix}{arm.arm_flange_link}"
        flange_frames[side] = flange_link

        # Mount EE root onto arm flange
        _add_fixed_joint(
            robot_el,
            name=f"{side}_flange_to_ee",
            parent_link=flange_link,
            child_link=f"{ee_prefix}{arm.ee_root_link}",
            xyz=arm.ee_mount_xyz,
            rpy=arm.ee_mount_rpy,
        )

        # Inject standardized grasp_frame TCP link
        grasp_link_name = f"{side}_grasp_frame"
        g_link = ET.SubElement(robot_el, "link", {"name": grasp_link_name})
        g_in = ET.SubElement(g_link, "inertial")
        ET.SubElement(g_in, "origin", {"xyz": "0 0 0", "rpy": "0 0 0"})
        ET.SubElement(g_in, "mass", {"value": "0.001"})
        ET.SubElement(
            g_in,
            "inertia",
            {"ixx": "1e-6", "ixy": "0", "ixz": "0", "iyy": "1e-6", "iyz": "0", "izz": "1e-6"},
        )
        _add_fixed_joint(
            robot_el,
            name=f"{side}_flange_to_grasp_frame",
            parent_link=flange_link,
            child_link=grasp_link_name,
            xyz=arm.grasp_frame_xyz,
            rpy=arm.grasp_frame_rpy,
        )
        grasp_frames[side] = grasp_link_name

        a_actuated = [
            j.attrib["name"]
            for j in a_joints
            if j.attrib.get("type", "fixed") in ("revolute", "prismatic", "continuous")
            and j.attrib["name"] not in a_mimics
        ]
        e_actuated_all = [
            j.attrib["name"]
            for j in e_joints
            if j.attrib.get("type", "fixed") in ("revolute", "prismatic", "continuous")
        ]
        e_drivers = [jn for jn in e_actuated_all if jn not in e_mimics]

        arm_joints[side] = a_actuated
        ee_joints[side] = e_actuated_all
        ee_driver_joints[side] = e_drivers
        all_mimics[side] = {**a_mimics, **e_mimics}
        all_limits.update(a_limits)
        all_limits.update(e_limits)

    ET.indent(robot_el, space="  ")
    urdf_path = out_dir / f"{spec.robot_id}.urdf"
    ET.ElementTree(robot_el).write(urdf_path, encoding="utf-8", xml_declaration=True)

    meta_path = out_dir / "robot_assembly_meta.json"
    result = RobotAssemblyResult(
        robot_id=spec.robot_id,
        urdf_path=str(urdf_path.resolve()),
        meta_path=str(meta_path.resolve()),
        arm_joints=arm_joints,
        ee_joints=ee_joints,
        ee_driver_joints=ee_driver_joints,
        mimic_joints=all_mimics,
        grasp_frames=grasp_frames,
        flange_frames=flange_frames,
        joint_limits=all_limits,
    )
    meta_payload = result.to_dict()
    meta_payload["spec"] = asdict(spec)
    meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    return result


def builtin_starbucks_specs(
    robots_root: str | Path = DEFAULT_MODULAR_ROBOTS_ROOT,
) -> dict[str, BimanualAssemblySpec]:
    """Return the 3 Phase-1 bimanual Starbucks robot assembly specs (ADR-20261126)."""
    root = Path(robots_root)
    fr3_urdf = str(root / "franka_fr3/urdf/fr3.urdf")
    rizon_urdf = str(root / "flexiv_rizon4s/urdf/rizon4s.urdf")
    robotiq_urdf = str(root / "robotiq_85/urdf/robotiq_85.urdf")
    flexiv_g_urdf = str(root / "flexiv_gripper/urdf/flexiv_gripper.urdf")
    wuji_l_urdf = str(root / "wuji_hand/urdf/wuji_hand_left.urdf")
    wuji_r_urdf = str(root / "wuji_hand/urdf/wuji_hand_right.urdf")

    # Pedestal height 0.78m puts arm bases right at Starbucks bar counter height (0.755m)
    # Left shoulder at y=+0.22m, right shoulder at y=-0.22m so both arms easily reach
    # the entire bar workspace (x in [-0.25, +0.42], y in [-0.36, +0.36], z in [0.76, 1.05]).
    return {
        "bimanual_fr3_robotiq85": BimanualAssemblySpec(
            robot_id="bimanual_fr3_robotiq85",
            pedestal_height_m=0.78,
            pedestal_width_y_m=0.56,
            pedestal_depth_x_m=0.22,
            arms=(
                ArmMountSpec(
                    side="left",
                    arm_urdf=fr3_urdf,
                    arm_root_link="fr3_link0",
                    arm_flange_link="fr3_link8",
                    ee_urdf=robotiq_urdf,
                    ee_root_link="flange",
                    mount_xyz=(0.0, 0.22, 0.78),
                    grasp_frame_xyz=(0.0, 0.0, 0.132),
                    grasp_frame_rpy=(0.0, 0.0, 1.5707963267948966),
                    ee_type="parallel_gripper",
                ),
                ArmMountSpec(
                    side="right",
                    arm_urdf=fr3_urdf,
                    arm_root_link="fr3_link0",
                    arm_flange_link="fr3_link8",
                    ee_urdf=robotiq_urdf,
                    ee_root_link="flange",
                    mount_xyz=(0.0, -0.22, 0.78),
                    grasp_frame_xyz=(0.0, 0.0, 0.132),
                    grasp_frame_rpy=(0.0, 0.0, 1.5707963267948966),
                    ee_type="parallel_gripper",
                ),
            ),
            metadata={"family": "franka_fr3", "ee_family": "robotiq_85"},
        ),
        "bimanual_rizon4s_flexiv": BimanualAssemblySpec(
            robot_id="bimanual_rizon4s_flexiv",
            pedestal_height_m=0.78,
            pedestal_width_y_m=0.56,
            pedestal_depth_x_m=0.22,
            arms=(
                ArmMountSpec(
                    side="left",
                    arm_urdf=rizon_urdf,
                    arm_root_link="base_link",
                    arm_flange_link="flange",
                    ee_urdf=flexiv_g_urdf,
                    ee_root_link="flange",
                    mount_xyz=(0.0, 0.22, 0.78),
                    grasp_frame_xyz=(0.0, 0.0, 0.195),
                    ee_type="parallel_gripper",
                    strip_arm_links=("world",),
                ),
                ArmMountSpec(
                    side="right",
                    arm_urdf=rizon_urdf,
                    arm_root_link="base_link",
                    arm_flange_link="flange",
                    ee_urdf=flexiv_g_urdf,
                    ee_root_link="flange",
                    mount_xyz=(0.0, -0.22, 0.78),
                    grasp_frame_xyz=(0.0, 0.0, 0.195),
                    ee_type="parallel_gripper",
                    strip_arm_links=("world",),
                ),
            ),
            metadata={"family": "flexiv_rizon4s", "ee_family": "flexiv_gripper"},
        ),
        "bimanual_fr3_wuji_hand": BimanualAssemblySpec(
            robot_id="bimanual_fr3_wuji_hand",
            pedestal_height_m=0.78,
            pedestal_width_y_m=0.56,
            pedestal_depth_x_m=0.22,
            arms=(
                ArmMountSpec(
                    side="left",
                    arm_urdf=fr3_urdf,
                    arm_root_link="fr3_link0",
                    arm_flange_link="fr3_link8",
                    ee_urdf=wuji_l_urdf,
                    ee_root_link="left_palm_link",
                    mount_xyz=(0.0, 0.22, 0.78),
                    grasp_frame_xyz=(0.045, 0.0, 0.095),
                    ee_type="dexterous_hand",
                ),
                ArmMountSpec(
                    side="right",
                    arm_urdf=fr3_urdf,
                    arm_root_link="fr3_link0",
                    arm_flange_link="fr3_link8",
                    ee_urdf=wuji_r_urdf,
                    ee_root_link="right_palm_link",
                    mount_xyz=(0.0, -0.22, 0.78),
                    grasp_frame_xyz=(0.045, 0.0, 0.095),
                    ee_type="dexterous_hand",
                ),
            ),
            metadata={"family": "franka_fr3", "ee_family": "wuji_hand_20dof"},
        ),
    }
