# -*- coding: utf-8 -*-
"""Headless regressions for hierarchy-preserving GLB export."""
from __future__ import annotations

import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np
from pxr import Gf, Usd, UsdGeom

from convert_asset.glb.converter import UsdToGlbConverter


REPO_ROOT = Path(__file__).resolve().parents[2]
IDENTITY_4 = np.eye(4, dtype=np.float64)


def _gf_matrix_to_numpy(matrix: Gf.Matrix4d) -> np.ndarray:
    return np.array(
        [[float(matrix[row][col]) for col in range(4)] for row in range(4)],
        dtype=np.float64,
    )


def _transform_point_row(point, matrix: np.ndarray) -> np.ndarray:
    point4 = np.array([float(point[0]), float(point[1]), float(point[2]), 1.0], dtype=np.float64)
    return point4 @ matrix


def _transform_bbox(min_corner, max_corner, matrix: np.ndarray):
    corners = []
    for x in (min_corner[0], max_corner[0]):
        for y in (min_corner[1], max_corner[1]):
            for z in (min_corner[2], max_corner[2]):
                corners.append(_transform_point_row((x, y, z), matrix)[:3])
    corners_np = np.array(corners, dtype=np.float64)
    return corners_np.min(axis=0), corners_np.max(axis=0)


def _load_gltf_json(path: Path):
    data = path.read_bytes()
    magic, version, _ = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67 or version != 2:
        raise AssertionError(f"Not a GLB 2.0 file: {path}")
    json_len, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise AssertionError(f"Missing JSON chunk: {path}")
    payload = data[20 : 20 + json_len]
    return json.loads(payload.decode("utf-8").rstrip(" "))


def _node_local_matrix(node) -> np.ndarray:
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape((4, 4))
    matrix = IDENTITY_4.copy()
    if "translation" in node:
        tx, ty, tz = [float(v) for v in node["translation"]]
        matrix[3, 0] = tx
        matrix[3, 1] = ty
        matrix[3, 2] = tz
    if "scale" in node:
        sx, sy, sz = [float(v) for v in node["scale"]]
        matrix = matrix @ np.diag([sx, sy, sz, 1.0])
    return matrix


def _gltf_bbox(path: Path):
    gltf = _load_gltf_json(path)
    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    accessors = gltf.get("accessors", [])
    roots = gltf.get("scenes", [{}])[gltf.get("scene", 0)].get("nodes", [])

    world_matrices = {}

    def visit(node_index: int, parent_world: np.ndarray):
        local = _node_local_matrix(nodes[node_index])
        world = local @ parent_world
        world_matrices[node_index] = world
        for child in nodes[node_index].get("children", []):
            visit(child, world)

    for root in roots:
        visit(root, IDENTITY_4)

    agg_min = np.array([math.inf, math.inf, math.inf], dtype=np.float64)
    agg_max = np.array([-math.inf, -math.inf, -math.inf], dtype=np.float64)
    transform_nodes = 0
    for node in nodes:
        if any(key in node for key in ("matrix", "translation", "rotation", "scale")):
            transform_nodes += 1
    for node_index, node in enumerate(nodes):
        mesh_index = node.get("mesh")
        if mesh_index is None:
            continue
        primitive = meshes[mesh_index]["primitives"][0]
        pos_accessor = accessors[primitive["attributes"]["POSITION"]]
        local_min = pos_accessor["min"]
        local_max = pos_accessor["max"]
        bbox_min, bbox_max = _transform_bbox(local_min, local_max, world_matrices[node_index])
        agg_min = np.minimum(agg_min, bbox_min)
        agg_max = np.maximum(agg_max, bbox_max)

    return {
        "bbox_min": agg_min,
        "bbox_max": agg_max,
        "nodes": len(nodes),
        "meshes": len(meshes),
        "materials": len(gltf.get("materials", [])),
        "transform_nodes": transform_nodes,
    }


def _usd_export_space_bbox(path: Path):
    stage = Usd.Stage.Open(str(path))
    if not stage:
        raise AssertionError(f"Failed to open USD stage: {path}")
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    root_transform = Gf.Matrix4d(1.0)
    if UsdGeom.GetStageUpAxis(stage) == "Z":
        root_transform = Gf.Matrix4d(Gf.Rotation(Gf.Vec3d(1, 0, 0), -90), Gf.Vec3d(0))
    root_np = _gf_matrix_to_numpy(root_transform)

    agg_min = np.array([math.inf, math.inf, math.inf], dtype=np.float64)
    agg_max = np.array([-math.inf, -math.inf, -math.inf], dtype=np.float64)
    mesh_count = 0
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if not prim.IsActive() or prim.IsInstanceProxy():
            continue
        if prim.GetTypeName() != "Mesh":
            continue
        mesh_count += 1
        world = _gf_matrix_to_numpy(cache.GetLocalToWorldTransform(prim))
        total = world @ root_np
        points = UsdGeom.Mesh(prim).GetPointsAttr().Get() or []
        for point in points:
            p = _transform_point_row(point, total)[:3]
            agg_min = np.minimum(agg_min, p)
            agg_max = np.maximum(agg_max, p)

    return {
        "bbox_min": agg_min,
        "bbox_max": agg_max,
        "mesh_count": mesh_count,
    }


def _assert_bbox_close(testcase, glb_stats, usd_stats, tol=1e-3):
    testcase.assertTrue(
        np.allclose(glb_stats["bbox_min"], usd_stats["bbox_min"], atol=tol),
        msg=f"bbox min mismatch: glb={glb_stats['bbox_min']} usd={usd_stats['bbox_min']}",
    )
    testcase.assertTrue(
        np.allclose(glb_stats["bbox_max"], usd_stats["bbox_max"], atol=tol),
        msg=f"bbox max mismatch: glb={glb_stats['bbox_max']} usd={usd_stats['bbox_max']}",
    )


def _export_glb(src: Path, out: Path):
    conv = UsdToGlbConverter()
    conv.process_stage(str(src), str(out))


class HierarchyExportTests(unittest.TestCase):
    def _export_and_compare(self, src: Path):
        with tempfile.TemporaryDirectory(prefix="glb_hierarchy_") as tmp_dir:
            out = Path(tmp_dir) / "out.glb"
            _export_glb(src, out)
            glb_stats = _gltf_bbox(out)
            usd_stats = _usd_export_space_bbox(src)
            self.assertEqual(glb_stats["meshes"], usd_stats["mesh_count"])
            self.assertGreater(glb_stats["nodes"], 0)
            _assert_bbox_close(self, glb_stats, usd_stats)
            return glb_stats

    def test_zup_fixture_uses_synthetic_root_and_preserves_bbox(self):
        fixture = """#usda 1.0
(
    upAxis = "Z"
)

def Xform "World"
{
    double3 xformOp:translate = (1, 2, 3)
    quatd xformOp:orient = (0.7071067811865476, 0, 0, 0.7071067811865475)
    float3 xformOp:scale = (2, 3, 1)
    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]

    def Mesh "Tri"
    {
        int[] faceVertexCounts = [3]
        int[] faceVertexIndices = [0, 1, 2]
        point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    }
}
"""
        with tempfile.TemporaryDirectory(prefix="glb_fixture_") as tmp_dir:
            usd_path = Path(tmp_dir) / "fixture.usda"
            usd_path.write_text(fixture, encoding="utf-8")
            glb_stats = self._export_and_compare(usd_path)
            self.assertGreaterEqual(glb_stats["transform_nodes"], 2)

    def test_articulated_direct_export_preserves_bbox(self):
        src = REPO_ROOT / "assets/usd/chestofdrawers_nomdl/chestofdrawers_0004/instance_noMDL.usd"
        glb_stats = self._export_and_compare(src)
        self.assertGreater(glb_stats["transform_nodes"], 0)

    def test_articulated_without_negative_scale_preserves_bbox(self):
        src = REPO_ROOT / "assets/usd/chestofdrawers_nomdl/chestofdrawers_0011/instance_noMDL.usd"
        glb_stats = self._export_and_compare(src)
        self.assertGreater(glb_stats["transform_nodes"], 0)

    def test_rigid_control_preserves_bbox(self):
        src = REPO_ROOT / "reports/faces_90pct_compare/instance_90_py.usd"
        glb_stats = self._export_and_compare(src)
        self.assertGreaterEqual(glb_stats["transform_nodes"], 0)


if __name__ == "__main__":
    unittest.main()
