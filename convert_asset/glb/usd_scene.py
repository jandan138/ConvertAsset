# -*- coding: utf-8 -*-
"""
USD scene graph extraction for GLB export.

This module keeps geometry extraction and scene-graph extraction separate:
- `usd_mesh.py` stays focused on mesh-local geometry payloads.
- this file decides which USD prims become glTF nodes and how parent/child
  relationships and local matrices are represented.
"""
from __future__ import annotations

from dataclasses import dataclass

from pxr import Gf, Usd, UsdGeom


SYNTHETIC_ROOT_KEY = "__synthetic_root__"
SYNTHETIC_ROOT_NAME = "__RootTransform__"


@dataclass(frozen=True)
class SceneNodeDesc:
    """Descriptor for one exported glTF node."""

    key: str
    name: str
    prim_path: str | None
    parent_key: str | None
    matrix: list[float] | None
    is_mesh: bool


class UsdSceneGraphBuilder:
    """Build a glTF-oriented node tree from a USD stage."""

    @staticmethod
    def build(stage, root_transform=Gf.Matrix4d(1.0)):
        """
        Build an ordered list of scene nodes for export.

        The returned descriptors are topologically ordered: parents always
        appear before their children.
        """
        mesh_prims = list(UsdSceneGraphBuilder._iter_exportable_mesh_prims(stage))
        export_prims = UsdSceneGraphBuilder._collect_export_prims(stage, mesh_prims)
        ordered_prims = sorted(
            export_prims.values(),
            key=lambda prim: (prim.GetPath().pathElementCount, prim.GetPath().pathString),
        )

        nodes = []
        has_synthetic_root = root_transform != Gf.Matrix4d(1.0)
        if has_synthetic_root:
            nodes.append(
                SceneNodeDesc(
                    key=SYNTHETIC_ROOT_KEY,
                    name=SYNTHETIC_ROOT_NAME,
                    prim_path=None,
                    parent_key=None,
                    matrix=UsdSceneGraphBuilder.gf_matrix_to_gltf_matrix(root_transform),
                    is_mesh=False,
                )
            )

        export_keys = set(export_prims.keys())
        for prim in ordered_prims:
            prim_path = prim.GetPath().pathString
            xformable = UsdGeom.Xformable(prim)
            local_matrix = xformable.GetLocalTransformation()
            matrix = None
            if local_matrix != Gf.Matrix4d(1.0):
                matrix = UsdSceneGraphBuilder.gf_matrix_to_gltf_matrix(local_matrix)

            parent_key = UsdSceneGraphBuilder._find_parent_key(prim, export_keys)
            if parent_key is None and has_synthetic_root:
                parent_key = SYNTHETIC_ROOT_KEY

            nodes.append(
                SceneNodeDesc(
                    key=prim_path,
                    name=prim.GetName(),
                    prim_path=prim_path,
                    parent_key=parent_key,
                    matrix=matrix,
                    is_mesh=(prim.GetTypeName() == "Mesh"),
                )
            )

        return nodes

    @staticmethod
    def gf_matrix_to_gltf_matrix(matrix):
        """
        Convert a USD `Gf.Matrix4d` into the flat array expected by glTF.

        USD matrices here are consumed in row-vector form; glTF stores matrices
        in column-major order. Flattening the USD matrix row-by-row yields the
        equivalent glTF JSON array.
        """
        return [float(matrix[row][col]) for row in range(4) for col in range(4)]

    @staticmethod
    def _iter_exportable_mesh_prims(stage):
        for prim in Usd.PrimRange(stage.GetPseudoRoot()):
            if not prim.IsActive() or prim.IsInstanceProxy():
                continue
            if prim.GetTypeName() == "Mesh":
                yield prim

    @staticmethod
    def _collect_export_prims(stage, mesh_prims):
        export_prims = {}
        pseudo_root = stage.GetPseudoRoot().GetPath()
        for mesh_prim in mesh_prims:
            prim = mesh_prim
            while prim and prim.IsValid() and prim.GetPath() != pseudo_root:
                xformable = UsdGeom.Xformable(prim)
                if xformable.GetPrim().IsValid():
                    export_prims[prim.GetPath().pathString] = prim
                prim = prim.GetParent()
        return export_prims

    @staticmethod
    def _find_parent_key(prim, export_keys):
        parent = prim.GetParent()
        while parent and parent.IsValid():
            parent_path = parent.GetPath().pathString
            if parent_path in export_keys:
                return parent_path
            parent = parent.GetParent()
        return None
