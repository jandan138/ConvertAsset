"""Canonical `/Instance` layout for final articulated-object packages."""

from __future__ import annotations

from typing import Any


INSTANCE_NAME = "Instance"


def _retarget(path: Any, root: Any, instance: Any) -> Any:
    if path.HasPrefix(instance) or not path.HasPrefix(root) or path == root:
        return path
    return path.ReplacePrefix(root, instance)


def move_asset_contents_under_instance(
    stage: Any,
    asset_root: str,
    *,
    instance_type: str = "xform",
) -> str:
    """Move the complete root-owned asset subtree under an identity Instance.

    New packages use an identity ``Xform`` because downstream scene processors
    need a transformable assembly boundary. ``Scope`` remains available only
    for rebuilding the historical r15 package.
    """

    from pxr import Sdf, UsdGeom

    root_path = Sdf.Path(asset_root)
    instance_path = root_path.AppendChild(INSTANCE_NAME)
    root = stage.GetPrimAtPath(root_path)
    if not root:
        raise ValueError(f"articulated asset root is missing: {asset_root}")
    if stage.GetPrimAtPath(instance_path):
        raise ValueError(f"articulated Instance already exists: {instance_path}")
    if instance_type == "xform":
        UsdGeom.Xform.Define(stage, instance_path)
    elif instance_type == "scope":
        UsdGeom.Scope.Define(stage, instance_path)
    else:
        raise ValueError(f"unsupported articulated Instance type: {instance_type}")
    stage.GetRootLayer().Save()
    layer = stage.GetRootLayer()
    edits = Sdf.BatchNamespaceEdit()
    children = [
        child.GetPath()
        for child in root.GetChildren()
        if child.GetName() != INSTANCE_NAME
    ]
    for child in children:
        edits.Add(child, instance_path.AppendChild(child.name))
    if not layer.Apply(edits):
        raise RuntimeError("could not move articulated subtree under Instance")
    layer.Save()
    for prim in stage.Traverse():
        for relationship in prim.GetRelationships():
            targets = relationship.GetTargets()
            rewritten = [
                _retarget(target, root_path, instance_path) for target in targets
            ]
            if rewritten != targets:
                relationship.SetTargets(rewritten)
        for attribute in prim.GetAttributes():
            connections = attribute.GetConnections()
            rewritten = [
                _retarget(target, root_path, instance_path) for target in connections
            ]
            if rewritten != connections:
                attribute.SetConnections(rewritten)
    root.SetCustomDataByKey(
        "aan:articulatedInstanceLayout",
        "v2" if instance_type == "xform" else "v1",
    )
    root.SetCustomDataByKey("aan:instancePrimPath", str(instance_path))
    layer.Save()
    return str(instance_path)


def author_fixed_base_articulation(
    stage: Any,
    asset_root: str,
    *,
    base_link: str,
    fixed_joint: str | None = None,
) -> dict[str, Any]:
    """Author a real fixed-base articulation without changing existing link paths."""

    from pxr import Gf, Sdf, UsdPhysics

    root = stage.GetPrimAtPath(asset_root)
    base = stage.GetPrimAtPath(base_link)
    instance_path = asset_root.rstrip("/") + "/Instance"
    instance = stage.GetPrimAtPath(instance_path)
    if not root:
        raise ValueError(f"articulated asset root is missing: {asset_root}")
    if not instance:
        raise ValueError(f"articulated Instance is missing: {instance_path}")
    if not base or not base.HasAPI(UsdPhysics.RigidBodyAPI):
        raise ValueError(f"fixed base rigid link is missing: {base_link}")

    UsdPhysics.ArticulationRootAPI.Apply(root)
    # PhysxSchema is registered only after Kit starts in some Isaac installs.
    # Applying the registered schema token and its real schema property through
    # core USD keeps package authoring usable in the portable pxr environment.
    api_schemas = root.GetMetadata("apiSchemas") or Sdf.TokenListOp()
    authored_tokens = [
        *list(api_schemas.explicitItems),
        *list(api_schemas.prependedItems),
        *list(api_schemas.appendedItems),
    ]
    for token in [*root.GetAppliedSchemas(), "PhysxArticulationAPI"]:
        if token not in authored_tokens:
            authored_tokens.append(token)
    root.SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(authored_tokens))
    root.CreateAttribute(
        "physxArticulation:articulationEnabled",
        Sdf.ValueTypeNames.Bool,
        custom=False,
    ).Set(True)
    root.CreateAttribute(
        "physxArticulation:enabledSelfCollisions",
        Sdf.ValueTypeNames.Bool,
        custom=False,
    ).Set(False)

    for prim in stage.Traverse():
        if prim.GetPath().HasPrefix(instance.GetPath()) and prim.HasAPI(
            UsdPhysics.RigidBodyAPI
        ):
            UsdPhysics.RigidBodyAPI(prim).CreateKinematicEnabledAttr(False)

    joint_path = fixed_joint or instance_path + "/Joints/BaseFixed"
    joint = UsdPhysics.FixedJoint.Define(stage, joint_path)
    joint.CreateBody0Rel().SetTargets([root.GetPath()])
    joint.CreateBody1Rel().SetTargets([base.GetPath()])
    joint.CreateLocalPos0Attr(Gf.Vec3f(0.0))
    joint.CreateLocalPos1Attr(Gf.Vec3f(0.0))
    joint.CreateLocalRot0Attr(Gf.Quatf(1.0))
    joint.CreateLocalRot1Attr(Gf.Quatf(1.0))
    joint.CreateCollisionEnabledAttr(False)
    joint.CreateExcludeFromArticulationAttr(False)
    root.SetCustomDataByKey("aan:fixedBaseArticulation", "v1")
    root.SetCustomDataByKey("aan:fixedBaseLink", base_link)
    root.SetCustomDataByKey("aan:fixedBaseJoint", joint_path)
    stage.GetRootLayer().Save()
    return audit_fixed_base_articulation_layout(
        stage,
        asset_root,
        base_link=base_link,
        fixed_joint=joint_path,
    )


def audit_instance_layout(stage: Any, asset_root: str) -> dict[str, Any]:
    from pxr import Gf, UsdGeom, UsdPhysics

    root_path = stage.GetPrimAtPath(asset_root).GetPath()
    instance_path = root_path.AppendChild(INSTANCE_NAME)
    instance = stage.GetPrimAtPath(instance_path)
    links = [
        str(prim.GetPath())
        for prim in stage.Traverse()
        if prim.HasAPI(UsdPhysics.RigidBodyAPI) and prim.GetPath().HasPrefix(root_path)
    ]
    outside = [
        path
        for path in links
        if not stage.GetPrimAtPath(path).GetPath().HasPrefix(instance_path)
    ]
    invalid_joint_targets = []
    for prim in stage.Traverse():
        if not prim.IsA(UsdPhysics.Joint):
            continue
        for relationship_name in ("physics:body0", "physics:body1"):
            for target in prim.GetRelationship(relationship_name).GetTargets():
                if target.HasPrefix(root_path) and (
                    not target.HasPrefix(instance_path)
                    or not stage.GetPrimAtPath(target)
                ):
                    invalid_joint_targets.append(
                        {
                            "joint": str(prim.GetPath()),
                            "relationship": relationship_name,
                            "target": str(target),
                        }
                    )
    identity = bool(instance) and (
        instance.IsA(UsdGeom.Scope)
        or Gf.IsClose(
            UsdGeom.Xformable(instance).GetLocalTransformation(),
            Gf.Matrix4d(1.0),
            1.0e-9,
        )
    )
    passed = (
        bool(instance)
        and identity
        and bool(links)
        and not outside
        and not invalid_joint_targets
    )
    return {
        "schema_version": "aan.articulated_instance_layout_audit.v1",
        "status": "pass" if passed else "blocked",
        "asset_root": str(root_path),
        "instance_prim_path": str(instance_path),
        "instance_identity": identity,
        "link_prim_paths": links,
        "links_outside_instance": outside,
        "invalid_joint_targets": invalid_joint_targets,
    }


def audit_fixed_base_articulation_layout(
    stage: Any,
    asset_root: str,
    *,
    base_link: str,
    fixed_joint: str | None = None,
) -> dict[str, Any]:
    """Audit the v2 identity-Xform and fixed-base articulation contract."""

    from pxr import Gf, UsdGeom, UsdPhysics

    root = stage.GetPrimAtPath(asset_root)
    instance_path = asset_root.rstrip("/") + "/Instance"
    instance = stage.GetPrimAtPath(instance_path)
    base = stage.GetPrimAtPath(base_link)
    joint_path = fixed_joint or instance_path + "/Joints/BaseFixed"
    joint = stage.GetPrimAtPath(joint_path)
    links = (
        [
            prim
            for prim in stage.Traverse()
            if prim.GetPath().HasPrefix(instance.GetPath())
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
        ]
        if instance
        else []
    )
    kinematic_links = [
        str(prim.GetPath())
        for prim in links
        if bool(prim.GetAttribute("physics:kinematicEnabled").Get())
    ]
    identity_xform = (
        bool(instance)
        and instance.IsA(UsdGeom.Xform)
        and Gf.IsClose(
            UsdGeom.Xformable(instance).GetLocalTransformation(),
            Gf.Matrix4d(1.0),
            1.0e-9,
        )
    )
    body0 = (
        [str(path) for path in joint.GetRelationship("physics:body0").GetTargets()]
        if joint
        else []
    )
    body1 = (
        [str(path) for path in joint.GetRelationship("physics:body1").GetTargets()]
        if joint
        else []
    )
    checks = {
        "root_has_articulation_api": bool(root)
        and root.HasAPI(UsdPhysics.ArticulationRootAPI),
        "articulation_enabled": bool(root)
        and root.GetAttribute("physxArticulation:articulationEnabled").Get() is True,
        "instance_is_identity_xform": identity_xform,
        "base_is_rigid_link": bool(base) and base.HasAPI(UsdPhysics.RigidBodyAPI),
        "all_links_nonkinematic": bool(links) and not kinematic_links,
        "fixed_joint_exists": bool(joint) and joint.IsA(UsdPhysics.FixedJoint),
        "fixed_joint_body0_is_root": body0 == [asset_root],
        "fixed_joint_body1_is_base": body1 == [base_link],
    }
    return {
        "schema_version": "aan.fixed_base_articulation_layout_audit.v1",
        "status": "pass" if all(checks.values()) else "blocked",
        "asset_root": asset_root,
        "instance_prim_path": instance_path,
        "base_link_prim_path": base_link,
        "fixed_joint_prim_path": joint_path,
        "link_prim_paths": [str(prim.GetPath()) for prim in links],
        "kinematic_link_prim_paths": kinematic_links,
        "checks": checks,
    }
