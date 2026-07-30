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


def test_facade_can_promote_one_source_root_and_override_dome_format(tmp_path) -> None:
    Usd = pytest.importorskip("pxr.Usd")
    raw = tmp_path / "room.usda"
    raw.write_text(
        """#usda 1.0
(
    defaultPrim = "Room"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "Room"
{
    def DomeLight "env_light"
    {
        asset inputs:texture:file = @./textures/gray.hdr@
        token inputs:texture:format = "automatic"
    }
    def Xform "Zone__North_Workbench" {}
}
""",
        encoding="utf-8",
    )
    textures = tmp_path / "textures"
    textures.mkdir()
    (textures / "gray.hdr").write_bytes(b"#?RADIANCE\n")

    result = build_consumer_facade(
        raw,
        tmp_path / "facade",
        mounts=[NamespaceMount(raw_namespace="/Room", mount_path="/World")],
        consumer_scope="/World",
        dome_latlong_prims=["/Room/env_light"],
    )

    stage = Usd.Stage.Open(str(result.facade_path))
    assert stage.GetDefaultPrim().GetPath().pathString == "/World"
    assert stage.GetPrimAtPath("/World/Zone__North_Workbench").IsValid()
    assert not stage.GetPrimAtPath("/World/World").IsValid()
    dome = stage.GetPrimAtPath("/World/env_light")
    assert dome.GetAttribute("inputs:texture:format").Get() == "latlong"
    assert result.dome_latlong_override_count == 1
    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    assert provenance["namespace_mapping"] == {"/Room": "/World"}
    assert provenance["dome_latlong_overrides"] == [
        {
            "source_prim": "/Room/env_light",
            "consumer_prim": "/World/env_light",
            "source_texture_format": "automatic",
            "consumer_texture_format": "latlong",
        }
    ]
