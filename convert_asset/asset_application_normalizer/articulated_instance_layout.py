"""Canonical `/Instance` layout for final articulated-object packages."""

from __future__ import annotations

from typing import Any


INSTANCE_NAME = "Instance"


def _retarget(path: Any, root: Any, instance: Any) -> Any:
    if path.HasPrefix(instance) or not path.HasPrefix(root) or path == root:
        return path
    return path.ReplacePrefix(root, instance)


def move_asset_contents_under_instance(stage: Any, asset_root: str) -> str:
    """Move the complete root-owned asset subtree under an identity Instance."""

    from pxr import Sdf, UsdGeom

    root_path = Sdf.Path(asset_root)
    instance_path = root_path.AppendChild(INSTANCE_NAME)
    root = stage.GetPrimAtPath(root_path)
    if not root:
        raise ValueError(f"articulated asset root is missing: {asset_root}")
    if stage.GetPrimAtPath(instance_path):
        raise ValueError(f"articulated Instance already exists: {instance_path}")
    UsdGeom.Scope.Define(stage, instance_path)
    stage.GetRootLayer().Save()
    layer = stage.GetRootLayer()
    edits = Sdf.BatchNamespaceEdit()
    children = [child.GetPath() for child in root.GetChildren() if child.GetName() != INSTANCE_NAME]
    for child in children:
        edits.Add(child, instance_path.AppendChild(child.name))
    if not layer.Apply(edits):
        raise RuntimeError("could not move articulated subtree under Instance")
    layer.Save()
    for prim in stage.Traverse():
        for relationship in prim.GetRelationships():
            targets = relationship.GetTargets()
            rewritten = [_retarget(target, root_path, instance_path) for target in targets]
            if rewritten != targets:
                relationship.SetTargets(rewritten)
        for attribute in prim.GetAttributes():
            connections = attribute.GetConnections()
            rewritten = [_retarget(target, root_path, instance_path) for target in connections]
            if rewritten != connections:
                attribute.SetConnections(rewritten)
    root.SetCustomDataByKey("aan:articulatedInstanceLayout", "v1")
    root.SetCustomDataByKey("aan:instancePrimPath", str(instance_path))
    layer.Save()
    return str(instance_path)


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
    outside = [path for path in links if not stage.GetPrimAtPath(path).GetPath().HasPrefix(instance_path)]
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
                        {"joint": str(prim.GetPath()), "relationship": relationship_name, "target": str(target)}
                    )
    identity = bool(instance) and (
        instance.IsA(UsdGeom.Scope)
        or Gf.IsClose(
            UsdGeom.Xformable(instance).GetLocalTransformation(),
            Gf.Matrix4d(1.0),
            1.0e-9,
        )
    )
    passed = bool(instance) and identity and bool(links) and not outside and not invalid_joint_targets
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
