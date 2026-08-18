from __future__ import annotations

import json
from pathlib import Path

from convert_asset.asset_application_normalizer.visual_material_audit import (
    audit_visual_material_only_package,
)


def _write_package(root: Path, overlay: str) -> tuple[Path, Path, Path]:
    package = root / "package"
    (package / "evidence").mkdir(parents=True)
    (package / "overlays").mkdir()
    (package / "physics").mkdir()
    (package / "interaction").mkdir()
    (package / "evidence/manifest.json").write_text(
        json.dumps(
            {
                "overall_status": "pass",
                "blocked_reasons": [],
                "source": {"sha256": "a" * 64},
                "visual_material_profile": {
                    "status": "pass",
                    "schema_version": "aan.visual_material_profile.v2",
                    "binding_targets": ["/World/Object/Visual"],
                    "mdl_inputs": {"frosting_roughness": {"type": "float", "value": 0.0}},
                },
                "runtime_evidence": {"status": "pass"},
            }
        ),
        encoding="utf-8",
    )
    (package / "overlays/visual_material.usda").write_text(overlay, encoding="utf-8")
    physics = root / "physics.json"
    interaction = root / "interaction.json"
    physics.write_text('{"mass": 0.2}\n', encoding="utf-8")
    interaction.write_text('{"grasp": "side"}\n', encoding="utf-8")
    (package / "physics/profile.json").write_bytes(physics.read_bytes())
    (package / "interaction/profile.json").write_bytes(interaction.read_bytes())
    return package, physics, interaction


def test_visual_material_only_audit_accepts_material_binding_delta(tmp_path: Path) -> None:
    package, physics, interaction = _write_package(
        tmp_path,
        """#usda 1.0
over \"World\" {
    over \"Object\" {
        def Material \"Glass\" { def Shader \"Shader\" { float inputs:frosting_roughness = 0 } }
        over \"Visual\" { rel material:binding = </World/Object/Glass> }
    }
}
""",
    )

    report = audit_visual_material_only_package(
        package,
        expected_physics_profile=physics,
        expected_interaction_profile=interaction,
    )

    assert report["status"] == "pass"
    assert report["physics_profile"]["byte_identical"] is True
    assert report["interaction_profile"]["byte_identical"] is True
    assert report["visual_overlay"]["forbidden_authored_tokens"] == []


def test_visual_material_only_audit_rejects_physics_or_geometry_authoring(tmp_path: Path) -> None:
    package, physics, interaction = _write_package(
        tmp_path,
        '#usda 1.0\nover "World" { float physics:mass = 1\n point3f[] points = [(0,0,0)] }\n',
    )

    report = audit_visual_material_only_package(
        package,
        expected_physics_profile=physics,
        expected_interaction_profile=interaction,
    )

    assert report["status"] == "blocked"
    assert "physics:" in report["visual_overlay"]["forbidden_authored_tokens"]
    assert "points" in report["visual_overlay"]["forbidden_authored_tokens"]
