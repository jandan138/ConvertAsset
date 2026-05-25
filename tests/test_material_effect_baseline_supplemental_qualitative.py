import importlib.util
from pathlib import Path
from types import SimpleNamespace

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_qualitative_render_manifest.py"
)
RUNNER_SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/run_supplemental_qualitative_renders.py"
)
FIGURE_SCRIPT = ROOT / "paper/shared/figures/gen_material_effect_qualitative.py"
QA_SCRIPT = (
    ROOT / "paper/shared/evidence/experiments/08_material_effect_baseline/review_supplemental_qualitative_renders.py"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_image(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 12), color=color).save(path)


def make_supplemental_conversion_manifest(tmp_path: Path) -> dict:
    original_clearcoat = tmp_path / "fixtures/clearcoat.usda"
    no_mdl_clearcoat = tmp_path / "fixtures/clearcoat_noMDL.usda"
    nvidia_clearcoat = tmp_path / "nvidia/clearcoat.usd"
    original_procedural = tmp_path / "fixtures/procedural.usda"
    no_mdl_procedural = tmp_path / "fixtures/procedural_noMDL.usda"
    nvidia_procedural = tmp_path / "nvidia/procedural.usd"
    for path in (
        original_clearcoat,
        no_mdl_clearcoat,
        nvidia_clearcoat,
        original_procedural,
        no_mdl_procedural,
        nvidia_procedural,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#usda 1.0\n", encoding="utf-8")

    return {
        "schema_version": 1,
        "summary": {"nvidia_static_gate_failed_count": 1},
        "samples": [
            {
                "sample_id": "supplemental_clearcoat_omnipbr",
                "target_category": "supplemental_material_fixture",
                "present_effects": ["clearcoat"],
                "target_prim_path": "/World/ClearcoatTarget",
                "conditions": {
                    "original_MDL": {
                        "status": "available",
                        "usd_path": str(original_clearcoat),
                        "static_gate_passed": True,
                    },
                    "existing_noMDL": {
                        "status": "available",
                        "usd_path": str(no_mdl_clearcoat),
                        "static_gate_passed": True,
                    },
                    "nvidia_asset_converter_preview_or_bake": {
                        "status": "static_gate_failed",
                        "usd_path": str(nvidia_clearcoat),
                        "static_gate_passed": False,
                    },
                },
            },
            {
                "sample_id": "supplemental_procedural_checker",
                "target_category": "supplemental_material_fixture",
                "present_effects": ["procedural_texture"],
                "target_prim_path": "/World/ProceduralTarget",
                "conditions": {
                    "original_MDL": {
                        "status": "available",
                        "usd_path": str(original_procedural),
                        "static_gate_passed": True,
                    },
                    "existing_noMDL": {
                        "status": "available",
                        "usd_path": str(no_mdl_procedural),
                        "static_gate_passed": True,
                    },
                    "nvidia_asset_converter_preview_or_bake": {
                        "status": "available",
                        "usd_path": str(nvidia_procedural),
                        "static_gate_passed": True,
                    },
                },
            },
        ],
    }


def test_build_supplemental_qualitative_manifest_records_all_conditions(tmp_path: Path) -> None:
    module = load_module(MANIFEST_SCRIPT, "supplemental_qualitative_manifest")
    conversion_manifest = make_supplemental_conversion_manifest(tmp_path)

    manifest = module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=tmp_path / "supplemental_qualitative_renders",
        width=600,
        height=450,
        wait_frames=8,
    )

    assert manifest["summary"]["selected_case_count"] == 2
    assert manifest["summary"]["condition_record_count"] == 6
    assert manifest["summary"]["ready_image_record_count"] == 0
    assert manifest["summary"]["render_pending_count"] == 6
    assert manifest["summary"]["nvidia_static_gate_failed_count"] == 1
    assert manifest["summary"]["ready_for_visual_review"] is False
    assert "supplemental_qualitative_renders_missing" in manifest["summary"]["blockers"]
    assert "supplemental_nvidia_static_gate_failed" in manifest["summary"]["blockers"]

    records = {(record["sample_id"], record["condition"]): record for record in manifest["records"]}
    original = records[("supplemental_clearcoat_omnipbr", "original_MDL")]
    assert original["camera_prim_path"] == "/World/Camera"
    assert original["render_command"][original["render_command"].index("--camera") + 1] == "/World/Camera"
    assert original["image"]["path"].endswith("/supplemental_clearcoat_omnipbr/original_MDL/original_0000.png")

    nvidia_failed = records[("supplemental_clearcoat_omnipbr", "nvidia_asset_converter_preview_or_bake")]
    assert nvidia_failed["source_condition_status"] == "static_gate_failed"
    assert nvidia_failed["static_gate_passed"] is False
    assert nvidia_failed["camera_prim_path"] == "/World/Camera/Camera"
    assert nvidia_failed["render_command"][nvidia_failed["render_command"].index("--prefix") + 1] == "nvidia"


def test_supplemental_qualitative_manifest_becomes_review_ready_after_images_exist(tmp_path: Path) -> None:
    module = load_module(MANIFEST_SCRIPT, "supplemental_qualitative_manifest_ready")
    conversion_manifest = make_supplemental_conversion_manifest(tmp_path)
    output_root = tmp_path / "supplemental_qualitative_renders"

    first = module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=output_root,
    )
    for record in first["records"]:
        write_image(Path(record["image"]["path"]), (30, 80, 140))

    manifest = module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=output_root,
    )

    assert manifest["summary"]["ready_image_record_count"] == 6
    assert manifest["summary"]["ready_case_count"] == 2
    assert manifest["summary"]["render_pending_count"] == 0
    assert manifest["summary"]["ready_for_contact_sheet"] is True
    assert manifest["summary"]["ready_for_visual_review"] is True
    assert manifest["summary"]["ready_for_visual_quality_claim"] is False
    assert "supplemental_qualitative_renders_missing" not in manifest["summary"]["blockers"]
    assert "supplemental_nvidia_static_gate_failed" in manifest["summary"]["blockers"]


def test_supplemental_runner_skips_existing_outputs(tmp_path: Path) -> None:
    manifest_module = load_module(MANIFEST_SCRIPT, "supplemental_qualitative_manifest_for_runner")
    runner_module = load_module(RUNNER_SCRIPT, "supplemental_qualitative_runner")
    conversion_manifest = make_supplemental_conversion_manifest(tmp_path)
    manifest = manifest_module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=tmp_path / "supplemental_qualitative_renders",
    )
    for record in manifest["records"]:
        write_image(Path(record["image"]["path"]), (90, 20, 160))

    def fail_if_called(*args, **kwargs):
        raise AssertionError("runner should not be called for existing outputs")

    run_manifest = runner_module.run_supplemental_qualitative_renders(
        manifest,
        log_root=tmp_path / "logs",
        runner=fail_if_called,
    )

    assert run_manifest["summary"]["skipped_existing_count"] == 6
    assert run_manifest["summary"]["attempted_count"] == 0
    assert run_manifest["summary"]["ready_output_count"] == 6
    assert run_manifest["summary"]["all_outputs_ready"] is True


def test_supplemental_runner_records_failed_attempt(tmp_path: Path) -> None:
    manifest_module = load_module(MANIFEST_SCRIPT, "supplemental_qualitative_manifest_for_failed_runner")
    runner_module = load_module(RUNNER_SCRIPT, "supplemental_qualitative_runner_failed")
    conversion_manifest = make_supplemental_conversion_manifest(tmp_path)
    manifest = manifest_module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=tmp_path / "supplemental_qualitative_renders",
    )

    def fake_runner(command, cwd, stdout, stderr, text, timeout):
        stdout.write("started\n")
        stderr.write("failed\n")
        return SimpleNamespace(returncode=9)

    run_manifest = runner_module.run_supplemental_qualitative_renders(
        manifest,
        log_root=tmp_path / "logs",
        runner=fake_runner,
        timeout_seconds=12,
    )

    assert run_manifest["summary"]["attempted_count"] == 6
    assert run_manifest["summary"]["failed_count"] == 6
    assert run_manifest["summary"]["ready_output_count"] == 0
    assert run_manifest["records"][0]["exit_code"] == 9


def test_supplemental_runner_normalizes_text_logs_before_hashing(tmp_path: Path) -> None:
    manifest_module = load_module(MANIFEST_SCRIPT, "supplemental_qualitative_manifest_for_log_norm")
    runner_module = load_module(RUNNER_SCRIPT, "supplemental_qualitative_runner_log_norm")
    conversion_manifest = make_supplemental_conversion_manifest(tmp_path)
    manifest = manifest_module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=tmp_path / "supplemental_qualitative_renders",
    )

    def fake_runner(command, cwd, stdout, stderr, text, timeout):
        output_dir = Path(command[command.index("--output-dir") + 1])
        prefix = command[command.index("--prefix") + 1]
        write_image(output_dir / f"{prefix}_0000.png", (20, 30, 40))
        stdout.write("saved frame   \n\n")
        stderr.write("kit/default found packages   \n\n")
        return SimpleNamespace(returncode=0)

    run_manifest = runner_module.run_supplemental_qualitative_renders(
        manifest,
        log_root=tmp_path / "logs",
        runner=fake_runner,
    )

    assert run_manifest["summary"]["ready_output_count"] == 6
    for record in run_manifest["records"]:
        for summary_key in ("stdout_summary", "stderr_summary"):
            log_path = Path(record[summary_key]["path"])
            text = log_path.read_text(encoding="utf-8")
            assert text.endswith("\n")
            assert not text.endswith("\n\n")
            assert all(not line.endswith(" ") for line in text.splitlines())


def test_existing_contact_sheet_generator_accepts_supplemental_manifest(tmp_path: Path) -> None:
    manifest_module = load_module(MANIFEST_SCRIPT, "supplemental_qualitative_manifest_for_figure")
    figure_module = load_module(FIGURE_SCRIPT, "supplemental_contact_sheet")
    conversion_manifest = make_supplemental_conversion_manifest(tmp_path)
    output_root = tmp_path / "supplemental_qualitative_renders"
    manifest = manifest_module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=output_root,
    )
    for record in manifest["records"]:
        write_image(Path(record["image"]["path"]), (40, 160, 80))
    manifest = manifest_module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=output_root,
    )

    output_path = tmp_path / "figures/supplemental.png"
    report = figure_module.build_material_effect_contact_sheet(manifest, output_path=output_path)

    assert report["summary"]["ready_case_count"] == 2
    assert report["summary"]["figure_written"] is True
    assert output_path.exists()


def test_supplemental_visual_qa_flags_static_failed_near_black_render(tmp_path: Path) -> None:
    manifest_module = load_module(MANIFEST_SCRIPT, "supplemental_qualitative_manifest_for_qa")
    qa_module = load_module(QA_SCRIPT, "supplemental_visual_qa")
    conversion_manifest = make_supplemental_conversion_manifest(tmp_path)
    output_root = tmp_path / "supplemental_qualitative_renders"
    manifest = manifest_module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=output_root,
    )
    for record in manifest["records"]:
        color = (0, 0, 0) if (
            record["sample_id"] == "supplemental_clearcoat_omnipbr"
            and record["condition"] == "nvidia_asset_converter_preview_or_bake"
        ) else (120, 180, 220)
        write_image(Path(record["image"]["path"]), color)
    manifest = manifest_module.build_supplemental_qualitative_render_manifest(
        conversion_manifest,
        output_root=output_root,
    )

    report = qa_module.build_supplemental_qualitative_visual_qa(manifest)

    assert report["summary"]["image_record_count"] == 6
    assert report["summary"]["machine_fail_count"] == 1
    assert report["summary"]["ready_for_failure_case_writeup"] is True
    failure = report["failure_cases"][0]
    assert failure["sample_id"] == "supplemental_clearcoat_omnipbr"
    assert failure["condition"] == "nvidia_asset_converter_preview_or_bake"
    assert failure["reason"] == "near_black_render"
