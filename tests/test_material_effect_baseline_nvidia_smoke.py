import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_asset_converter_smoke.py"
)


def load_smoke_module():
    spec = importlib.util.spec_from_file_location("material_effect_nvidia_smoke", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_discover_asset_converter_fixture_prefers_official_mdl_usd(tmp_path: Path) -> None:
    module = load_smoke_module()
    fixture = tmp_path / "extscache/omni.kit.asset_converter-1.0/data/MDL_to_glTF.usd"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("#usda 1.0\n", encoding="utf-8")

    assert module.discover_asset_converter_fixture(tmp_path) == fixture


def test_build_attempt_record_contains_claim_gate_fields(tmp_path: Path) -> None:
    module = load_smoke_module()
    input_usd = tmp_path / "in.usd"
    output_usd = tmp_path / "out.usd"
    input_usd.write_text("#usda 1.0\n", encoding="utf-8")

    record = module.build_attempt_record(
        name="usd_to_usd_preview",
        input_path=input_usd,
        output_path=output_usd,
        context_flags={"export_preview_surface": True},
        conversion_success=False,
        error_message="not supported",
        stage_counts=None,
    )

    assert record["name"] == "usd_to_usd_preview"
    assert record["input_usd"] == str(input_usd)
    assert record["output_path"] == str(output_usd)
    assert record["context_flags"] == {"export_preview_surface": True}
    assert record["conversion_success"] is False
    assert record["stage_opened"] is False
    assert record["preview_surface_count"] is None
    assert record["active_mdl_shader_count"] is None
    assert record["claimable_as_baseline"] is False
    assert record["error_message"] == "not supported"


def test_build_smoke_manifest_marks_baseline_ready_only_when_usd_attempt_is_claimable(tmp_path: Path) -> None:
    module = load_smoke_module()
    input_usd = tmp_path / "in.usd"
    output_usd = tmp_path / "out.usd"
    input_usd.write_text("#usda 1.0\n", encoding="utf-8")
    output_usd.write_text("#usda 1.0\n", encoding="utf-8")
    attempt = module.build_attempt_record(
        name="usd_to_usd_preview",
        input_path=input_usd,
        output_path=output_usd,
        context_flags={"export_preview_surface": True},
        conversion_success=True,
        error_message=None,
        stage_counts={
            "stage_opened": True,
            "preview_surface_count": 2,
            "active_mdl_shader_count": 0,
        },
    )

    manifest = module.build_smoke_manifest(
        fixture_path=input_usd,
        attempts=[attempt],
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["status"] == "nvidia_asset_converter_smoke"
    assert manifest["summary"]["attempt_count"] == 1
    assert manifest["summary"]["usable_usd_baseline_attempts"] == ["usd_to_usd_preview"]
    assert manifest["summary"]["ready_for_sample_baseline"] is True
    assert manifest["claim_boundary"]["allowed"][0].startswith("This smoke only validates")


def test_write_smoke_manifest_creates_parent_directory(tmp_path: Path) -> None:
    module = load_smoke_module()
    out = tmp_path / "nested/smoke_manifest.json"
    manifest = module.build_smoke_manifest(
        fixture_path=None,
        attempts=[],
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    module.write_smoke_manifest(out, manifest)

    assert out.exists()
    assert '"status": "nvidia_asset_converter_smoke"' in out.read_text(encoding="utf-8")
