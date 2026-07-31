from __future__ import annotations

import hashlib
import json
from pathlib import Path

from convert_asset.asset_application_normalizer.visual_material_profile import (
    apply_visual_material_profile,
    load_visual_material_profile,
)
from convert_asset.asset_application_normalizer.package_layout import TargetPackageLayout


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_profile(path: Path, source: Path, mdl: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "aan.visual_material_profile.v1",
                "profile_id": "scientific_workbench.beaker.transparent_glass",
                "revision": "r1",
                "source_binding": {"sha256": _sha256(source)},
                "override": {
                    "kind": "mdl_glass",
                    "source_mdl": str(mdl),
                    "source_sub_identifier": "OmniGlass",
                    "material_name": "TransparentGlass",
                    "binding_targets": ["/World/Beaker/Visual/Source/mesh"],
                    "claim_boundary": "Intentional visual compatibility override; physics is unchanged.",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_loads_source_bound_transparent_glass_profile(tmp_path: Path) -> None:
    source = tmp_path / "beaker.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\n", encoding="utf-8")
    profile = tmp_path / "transparent_glass.json"
    _write_profile(profile, source, mdl)

    resolution = load_visual_material_profile(profile, source)

    assert resolution.status == "pass"
    assert resolution.profile_id == "scientific_workbench.beaker.transparent_glass"
    assert resolution.source_mdl == mdl
    assert resolution.material_name == "TransparentGlass"
    assert resolution.binding_targets == ("/World/Beaker/Visual/Source/mesh",)
    assert resolution.profile_sha256 == _sha256(profile)


def test_rejects_visual_profile_when_source_binding_is_stale(tmp_path: Path) -> None:
    source = tmp_path / "beaker.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\n", encoding="utf-8")
    profile = tmp_path / "transparent_glass.json"
    _write_profile(profile, source, mdl)
    source.write_text("#usda 1.0\n# changed\n", encoding="utf-8")

    resolution = load_visual_material_profile(profile, source)

    assert resolution.status == "blocked"
    assert "source sha256" in resolution.reason.lower()


def test_profile_writes_a_package_local_mdl_overlay_and_mesh_binding(tmp_path: Path) -> None:
    source = tmp_path / "beaker.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\nexport material OmniGlass() = material();\n", encoding="utf-8")
    profile = tmp_path / "transparent_glass.json"
    _write_profile(profile, source, mdl)

    layout = TargetPackageLayout(tmp_path / "package")
    layout.root.mkdir()
    (layout.root / "base.usda").write_text(
        """#usda 1.0
def Xform \"World\"
{
    def Xform \"Beaker\"
    {
        def Xform \"Visual\"
        {
            def Xform \"Source\"
            {
                def Mesh \"mesh\" {}
            }
        }
    }
}
""",
        encoding="utf-8",
    )
    layout.root_usd.write_text(
        "#usda 1.0\n( subLayers = [ @overlays/visual_material.usda@, @base.usda@ ] )\n",
        encoding="utf-8",
    )

    result = apply_visual_material_profile(
        layout,
        profile,
        source,
        ["/World/Beaker"],
    )

    assert result.overall_status == "pass"
    assert layout.visual_material_mdl("OmniGlass.mdl").is_file()
    assert layout.visual_material_profile_json.is_file()
    from pxr import Usd  # type: ignore

    stage = Usd.Stage.Open(str(layout.root_usd))
    assert stage is not None
    mesh = stage.GetPrimAtPath("/World/Beaker/Visual/Source/mesh")
    assert mesh.GetRelationship("material:binding").GetTargets() == [
        "/World/Beaker/__aan_visual_materials/TransparentGlass"
    ]
