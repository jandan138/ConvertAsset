"""Headless Isaac Sim 4.1 URDF -> SimReady USD exporter for assembled robots.

Run with the Isaac Sim 4.1 Python environment (SIM_PY), e.g.:
    $SIM_PY -m convert_asset.robot_urdf.usd_exporter \
        --robot-id all \
        --out-root /cpfs/user/zhuzihou/dev/ConvertAsset/external_artifacts/cross_embodiment_robots_v1 \
        --qualify
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .assembler import (
    DEFAULT_MODULAR_ROBOTS_ROOT,
    RobotAssemblyResult,
    assemble_bimanual_urdf,
    builtin_starbucks_specs,
)


def export_urdf_to_simready_usd(
    assembly: RobotAssemblyResult,
    *,
    usd_out_path: str | Path | None = None,
    arm_stiffness: float = 400.0,
    arm_damping: float = 40.0,
    ee_stiffness: float = 120.0,
    ee_damping: float = 12.0,
    finger_static_friction: float = 1.4,
    finger_dynamic_friction: float = 1.2,
) -> dict[str, Any]:
    """Convert an assembled URDF into a SimReady Isaac Sim 4.1 USD articulation.

    Must be called inside an active Isaac Sim `SimulationApp` process.
    """
    import omni.kit.commands  # type: ignore
    from omni.importer.urdf import _urdf  # type: ignore
    from pxr import PhysxSchema, Usd, UsdPhysics, UsdShade  # type: ignore

    urdf_path = Path(assembly.urdf_path).resolve()
    out_usd = Path(usd_out_path).resolve() if usd_out_path else urdf_path.with_suffix(".usd")
    out_usd.parent.mkdir(parents=True, exist_ok=True)

    import_config = _urdf.ImportConfig()
    import_config.merge_fixed_joints = False
    import_config.convex_decomp = False
    import_config.import_inertia_tensor = True
    import_config.fix_base = True
    import_config.make_default_prim = True
    import_config.self_collision = False
    import_config.create_physics_scene = False
    import_config.default_drive_type = _urdf.UrdfJointTargetType.JOINT_DRIVE_POSITION
    import_config.default_drive_strength = arm_stiffness
    import_config.default_position_drive_damping = arm_damping
    import_config.distance_scale = 1.0

    ok, prim_path = omni.kit.commands.execute(
        "URDFParseAndImportFile",
        urdf_path=str(urdf_path),
        import_config=import_config,
        dest_path=str(out_usd),
    )
    if not ok or not out_usd.is_file():
        raise RuntimeError(f"URDFParseAndImportFile failed for {urdf_path} -> {out_usd}")

    # Post-process drives and finger friction directly in the exported USD
    stage = Usd.Stage.Open(str(out_usd))
    arm_joint_set = {jn for joints in assembly.arm_joints.values() for jn in joints}
    ee_joint_set = {jn for joints in assembly.ee_joints.values() for jn in joints}

    # Author high-friction silicone pad material for end-effector links
    mat_path = f"{prim_path}/Looks/HighFrictionFingerPad"
    mat = UsdShade.Material.Define(stage, mat_path)
    pmat = UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
    pmat.CreateStaticFrictionAttr(finger_static_friction)
    pmat.CreateDynamicFrictionAttr(finger_dynamic_friction)
    pmat.CreateRestitutionAttr(0.0)
    physx_mat = PhysxSchema.PhysxMaterialAPI.Apply(mat.GetPrim())
    physx_mat.CreateFrictionCombineModeAttr("max")

    tuned_arm = 0
    tuned_ee = 0
    bound_ee_colliders = 0
    for prim in stage.Traverse():
        name = prim.GetName()
        if prim.HasAPI(UsdPhysics.DriveAPI):
            # Angular or linear drive
            drive = UsdPhysics.DriveAPI.Get(prim, "angular")
            if not drive:
                drive = UsdPhysics.DriveAPI.Get(prim, "linear")
            if drive:
                if name in arm_joint_set:
                    drive.GetStiffnessAttr().Set(arm_stiffness)
                    drive.GetDampingAttr().Set(arm_damping)
                    drive.GetMaxForceAttr().Set(150.0)
                    tuned_arm += 1
                elif name in ee_joint_set:
                    drive.GetStiffnessAttr().Set(ee_stiffness)
                    drive.GetDampingAttr().Set(ee_damping)
                    drive.GetMaxForceAttr().Set(40.0)
                    tuned_ee += 1

        if prim.HasAPI(UsdPhysics.CollisionAPI):
            path_str = str(prim.GetPath())
            if "_ee_" in path_str:
                UsdShade.MaterialBindingAPI.Apply(prim).Bind(
                    mat, UsdShade.Tokens.weakerThanDescendants, "physics"
                )
                bound_ee_colliders += 1

    stage.GetRootLayer().Save()

    report = {
        "robot_id": assembly.robot_id,
        "urdf_path": str(urdf_path),
        "usd_path": str(out_usd),
        "prim_path": str(prim_path),
        "tuned_arm_drives": tuned_arm,
        "tuned_ee_drives": tuned_ee,
        "bound_ee_colliders": bound_ee_colliders,
        "meta_path": assembly.meta_path,
    }
    report_path = out_usd.parent / "usd_export_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble modular URDFs and export SimReady Isaac Sim 4.1 USDs.")
    parser.add_argument("--robot-id", default="all", help="Robot ID or 'all'")
    parser.add_argument("--robots-root", default=str(DEFAULT_MODULAR_ROBOTS_ROOT))
    parser.add_argument(
        "--out-root",
        default="/cpfs/user/zhuzihou/dev/ConvertAsset/external_artifacts/cross_embodiment_robots_v1",
    )
    parser.add_argument(
        "--qualify",
        action="store_true",
        help="Run L0+L1+L2 SimReady robot qualification gate immediately after export.",
    )
    args = parser.parse_args()

    specs = builtin_starbucks_specs(args.robots_root)
    targets = list(specs.keys()) if args.robot_id == "all" else [args.robot_id]

    from isaacsim import SimulationApp  # type: ignore

    app = SimulationApp({"headless": True})
    try:
        results = []
        for rid in targets:
            spec = specs[rid]
            out_dir = Path(args.out_root) / rid
            assembly = assemble_bimanual_urdf(spec, out_dir)
            rep = export_urdf_to_simready_usd(assembly)
            if args.qualify:
                from .qualifier import run_sim_qualification

                qrep = run_sim_qualification(assembly.meta_path, usd_path=rep["usd_path"])
                rep["qualification_passed"] = qrep["passed"]
            results.append(rep)
            print(
                f"[EXPORTED] {rid} -> {rep['usd_path']} "
                f"(arm={rep['tuned_arm_drives']}, ee={rep['tuned_ee_drives']}, "
                f"qual={rep.get('qualification_passed', 'skipped')})"
            )
    finally:
        app.close()


if __name__ == "__main__":
    main()
