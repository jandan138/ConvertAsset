"""Tests for convert_asset.asset_application_normalizer.facade."""

from __future__ import annotations

import json

import pytest

from convert_asset.asset_application_normalizer.facade import (
    NamespaceMount,
    build_consumer_facade,
)

RAW_USDA = """#usda 1.0
(
    defaultPrim = "world"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "world"
{
    def Scope "Looks"
    {
        def Material "Mat" {}
    }
}
def Xform "Root"
{
    def Xform "Geom"
    {
        rel material:binding = </world/Looks/Mat>
        def Mesh "mesh"
        {
            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
            int[] faceVertexCounts = [3]
            int[] faceVertexIndices = [0, 1, 2]
        }
    }
}
def Scope "Render"
{
}
"""


def test_facade_mounts_namespaces_and_retargets_bindings(tmp_path) -> None:
    Usd = pytest.importorskip("pxr.Usd")
    raw = tmp_path / "world.usda"
    raw.write_text(RAW_USDA, encoding="utf-8")
    out_dir = tmp_path / "facade"

    result = build_consumer_facade(
        raw,
        out_dir,
        mounts=[
            NamespaceMount(raw_namespace="/world", mount_path="/World/world"),
            NamespaceMount(raw_namespace="/Root", mount_path="/World/Root"),
            NamespaceMount(raw_namespace="/Render", mount_path="/World/Render"),
        ],
        consumer_scope="/World",
    )

    assert result.status == "pass"
    assert result.binding_retarget_count == 1
    stage = Usd.Stage.Open(str(result.facade_path))
    assert stage.GetDefaultPrim().GetPath().pathString == "/World"
    assert stage.GetPrimAtPath("/World/world/Looks/Mat").IsValid()
    geom = stage.GetPrimAtPath("/World/Root/Geom")
    targets = geom.GetRelationship("material:binding").GetTargets()
    assert [t.pathString for t in targets] == ["/World/world/Looks/Mat"]
    assert stage.GetPrimAtPath("/World/Render").IsValid()
    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    assert provenance["namespace_mapping"]["/world"] == "/World/world"
    assert provenance["binding_retarget_rule"].startswith("prefix")


def test_facade_preserves_unrelated_binding_targets(tmp_path) -> None:
    Usd = pytest.importorskip("pxr.Usd")
    raw = tmp_path / "world.usda"
    raw.write_text(
        """#usda 1.0
(
    defaultPrim = "Root"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "Root"
{
    def Scope "Materials"
    {
        def Material "Local" {}
    }
    def Xform "Geom"
    {
        rel material:binding = </Root/Materials/Local>
        def Mesh "mesh"
        {
            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
            int[] faceVertexCounts = [3]
            int[] faceVertexIndices = [0, 1, 2]
        }
    }
}
""",
        encoding="utf-8",
    )
    out_dir = tmp_path / "facade"

    result = build_consumer_facade(
        raw,
        out_dir,
        mounts=[NamespaceMount(raw_namespace="/Root", mount_path="/World/Root")],
        consumer_scope="/World",
    )

    stage = Usd.Stage.Open(str(result.facade_path))
    targets = stage.GetPrimAtPath("/World/Root/Geom").GetRelationship("material:binding").GetTargets()
    assert [t.pathString for t in targets] == ["/World/Root/Materials/Local"]
    assert stage.GetPrimAtPath("/World/Root/Materials/Local").IsValid()
