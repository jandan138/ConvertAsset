from __future__ import annotations

from pathlib import Path

from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.pipeline import validate_request


def _request(
    source: Path,
    *,
    role: str,
    source_runtime: str = "blender44",
    physics_profile: Path | None = None,
    support_relations: Path | None = None,
) -> NormalizeAssetRequest:
    return NormalizeAssetRequest(
        source_usd=source,
        out_dir=source.parent / "package",
        asset_id="scientific_environment_code_room_example4_v1",
        asset_class="auto",
        asset_role=role,
        source_runtime=source_runtime,
        target_runtime="isaac41",
        target_benchmark="scenario-forge",
        task_id="scientific_workbench_bimanual_pour",
        asset_scope_prims=["/World"],
        gates=["static", "runtime"],
        physics_profile=physics_profile,
        support_relations=support_relations,
    )


def test_blender44_source_runtime_is_allowed_for_visual_static_environment(
    tmp_path: Path,
) -> None:
    source = tmp_path / "facade.usda"
    source.write_text('#usda 1.0\ndef Xform "World" {}\n', encoding="utf-8")
    support_relations = tmp_path / "support_relations.json"
    support_relations.write_text("{}\n", encoding="utf-8")

    assert (
        validate_request(
            _request(
                source,
                role="visual_static_environment",
                support_relations=support_relations,
            )
        )
        is None
    )


def test_blender44_environment_requires_support_relations(tmp_path: Path) -> None:
    source = tmp_path / "facade.usda"
    source.write_text('#usda 1.0\ndef Xform "World" {}\n', encoding="utf-8")

    result = validate_request(_request(source, role="visual_static_environment"))

    assert result is not None
    assert result.overall_status == "invalid"


def test_blender44_source_runtime_is_not_allowed_for_dynamic_assets(
    tmp_path: Path,
) -> None:
    source = tmp_path / "facade.usda"
    source.write_text('#usda 1.0\ndef Xform "World" {}\n', encoding="utf-8")

    result = validate_request(_request(source, role="dynamic"))

    assert result is not None
    assert result.return_code == 2
    assert result.overall_status == "invalid"


def test_generic_usd_source_runtime_is_allowed_for_profiled_dynamic_assets(
    tmp_path: Path,
) -> None:
    source = tmp_path / "facade.usda"
    source.write_text('#usda 1.0\ndef Xform "World" {}\n', encoding="utf-8")
    physics_profile = tmp_path / "physics.json"
    physics_profile.write_text("{}\n", encoding="utf-8")

    assert (
        validate_request(
            _request(
                source,
                role="dynamic",
                source_runtime="generic_usd",
                physics_profile=physics_profile,
            )
        )
        is None
    )
