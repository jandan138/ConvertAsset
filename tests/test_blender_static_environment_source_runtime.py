from __future__ import annotations

from pathlib import Path

from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.pipeline import validate_request


def _request(
    source: Path,
    *,
    role: str,
) -> NormalizeAssetRequest:
    return NormalizeAssetRequest(
        source_usd=source,
        out_dir=source.parent / "package",
        asset_id="scientific_environment_code_room_example4_v1",
        asset_class="auto",
        asset_role=role,
        source_runtime="blender44",
        target_runtime="isaac41",
        target_benchmark="scenario-forge",
        task_id="scientific_workbench_bimanual_pour",
        asset_scope_prims=["/World"],
        gates=["static", "runtime"],
    )


def test_blender44_source_runtime_is_allowed_for_visual_static_environment(
    tmp_path: Path,
) -> None:
    source = tmp_path / "facade.usda"
    source.write_text('#usda 1.0\ndef Xform "World" {}\n', encoding="utf-8")

    assert validate_request(_request(source, role="visual_static_environment")) is None


def test_blender44_source_runtime_is_not_allowed_for_dynamic_assets(
    tmp_path: Path,
) -> None:
    source = tmp_path / "facade.usda"
    source.write_text('#usda 1.0\ndef Xform "World" {}\n', encoding="utf-8")

    result = validate_request(_request(source, role="dynamic"))

    assert result is not None
    assert result.return_code == 2
    assert result.overall_status == "invalid"
