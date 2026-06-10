import importlib.util
from types import SimpleNamespace
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/build_qualitative_render_manifest.py"
)
FIGURE_SCRIPT = ROOT / "paper/shared/figures/gen_material_effect_qualitative.py"
RUNNER_SCRIPT = (
    ROOT / "paper/shared/evidence/experiments/08_material_effect_baseline/run_qualitative_nvidia_renders.py"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_image(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (12, 8), color=color).save(path)


def make_synthetic_inputs(tmp_path: Path) -> tuple[dict, dict, dict, Path, Path]:
    original_image = tmp_path / "renders/scene_a/target_1/zoom_016/original/original_0000.png"
    converted_image = tmp_path / "renders/scene_a/target_1/zoom_016/converted/converted_0000.png"
    write_image(original_image, (220, 40, 40))
    write_image(converted_image, (40, 220, 40))
    original_usd = tmp_path / "scene_a/start_result_raw.usd"
    converted_usd = tmp_path / "scene_a/start_result_raw_noMDL.usd"
    nvidia_usd = tmp_path / "nvidia/scene_a/start_result_raw_nvidia.usd"
    for path in (original_usd, converted_usd, nvidia_usd):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#usda 1.0\n", encoding="utf-8")

    camera = {
        "view_id": "zoom_016",
        "camera_prim_path": "/World/GRScenesVLMTargetCamera",
        "position_world": [4.0, 0.0, 2.0],
        "target_world": [0.0, 0.0, 0.5],
        "look_at": [0.0, 0.0, 0.5],
        "up_world": [0.0, 0.0, 1.0],
        "focal_length_mm": 18.0,
        "horizontal_aperture_mm": 20.955,
        "vertical_aperture_mm": 15.71625,
        "clipping_range": [0.01, 100.0],
        "start_frame": 0,
        "end_frame": 0,
        "time_codes_per_second": 24,
    }
    stress_render_manifest = {
        "renderer_settings": {
            "image_width": 600,
            "image_height": 450,
            "renderer": "RayTracedLighting",
            "wait_frames": 8,
        },
        "records": [
            {
                "sample_id": "target_1.zoom_016.original",
                "pair_id": "target_1.zoom_016",
                "source_scene_id": "scene_a",
                "target_id": "target_1",
                "object_category": "cup",
                "material_condition": "original",
                "usd_path": str(original_usd),
                "camera": camera,
                "camera_stage_path": str(tmp_path / "renders/original_camera.usd"),
                "output_image": str(original_image),
                "image": {"path": str(original_image), "width": 600, "height": 450},
            },
            {
                "sample_id": "target_1.zoom_016.converted",
                "pair_id": "target_1.zoom_016",
                "source_scene_id": "scene_a",
                "target_id": "target_1",
                "object_category": "cup",
                "material_condition": "converted",
                "usd_path": str(converted_usd),
                "camera": camera,
                "camera_stage_path": str(tmp_path / "renders/converted_camera.usd"),
                "output_image": str(converted_image),
                "image": {"path": str(converted_image), "width": 600, "height": 450},
            },
        ],
    }
    effect_manifest = {
        "summary": {"effect_gaps": ["clearcoat", "procedural_texture"]},
        "effect_order": [
            "clearcoat",
            "opacity_transparency",
            "emission",
            "procedural_texture",
            "normal_bump",
            "displacement_height",
        ],
        "samples": [
            {
                "sample_id": "target_1.zoom_016",
                "pair_id": "target_1.zoom_016",
                "source_scene_id": "scene_a",
                "target_category": "cup",
                "target_id": "target_1",
                "present_effects": [
                    "opacity_transparency",
                    "emission",
                    "normal_bump",
                    "displacement_height",
                ],
                "visual_review": {"verdict": "PASS"},
            }
        ],
    }
    baseline_manifest = {
        "summary": {"effect_gaps": ["clearcoat", "procedural_texture"]},
        "samples": [
            {
                "sample_id": "target_1.zoom_016",
                "source_scene_id": "scene_a",
                "target_category": "cup",
                "target_prim_path": "/Root/Cup",
                "present_effects": [
                    "opacity_transparency",
                    "emission",
                    "normal_bump",
                    "displacement_height",
                ],
                "conditions": {
                    "original_MDL": {"status": "available", "usd_path": str(original_usd)},
                    "existing_noMDL": {"status": "available", "usd_path": str(converted_usd)},
                    "nvidia_asset_converter_preview_or_bake": {
                        "status": "available",
                        "usd_path": str(nvidia_usd),
                        "preferred_smoke_attempt": "usd_to_usd_preview",
                    },
                },
            }
        ],
    }
    return effect_manifest, baseline_manifest, stress_render_manifest, original_image, converted_image


def test_build_qualitative_manifest_reuses_pair_images_and_plans_nvidia_render(tmp_path: Path) -> None:
    module = load_module(MANIFEST_SCRIPT, "material_effect_qualitative_manifest")
    effect_manifest, baseline_manifest, stress_manifest, original_image, converted_image = make_synthetic_inputs(tmp_path)

    manifest = module.build_qualitative_render_manifest(
        effect_manifest,
        baseline_manifest,
        stress_manifest,
        output_root=tmp_path / "qualitative_renders",
        max_cases=4,
    )

    assert manifest["summary"]["selected_case_count"] == 1
    assert manifest["summary"]["condition_record_count"] == 3
    assert manifest["summary"]["ready_image_record_count"] == 2
    assert manifest["summary"]["nvidia_render_pending_count"] == 1
    assert "nvidia_qualitative_renders_missing" in manifest["summary"]["blockers"]
    assert manifest["selected_cases"][0]["covered_effects"] == [
        "opacity_transparency",
        "emission",
        "normal_bump",
        "displacement_height",
    ]

    records = {record["condition"]: record for record in manifest["records"]}
    assert records["original_MDL"]["image"]["path"] == str(original_image)
    assert records["original_MDL"]["image"]["status"] == "ready"
    assert records["existing_noMDL"]["image"]["path"] == str(converted_image)
    assert records["existing_noMDL"]["image"]["status"] == "ready"
    nvidia = records["nvidia_asset_converter_preview_or_bake"]
    assert nvidia["status"] == "render_pending"
    assert nvidia["camera"] == records["original_MDL"]["camera"]
    assert nvidia["camera_stage_path"].endswith("/nvidia/nvidia_camera.usd")
    assert nvidia["image"]["path"].endswith("/nvidia/nvidia_0000.png")
    assert "--prefix" in nvidia["render_command"]
    assert "nvidia" in nvidia["render_command"]


def test_build_qualitative_manifest_marks_ready_after_nvidia_image_exists(tmp_path: Path) -> None:
    module = load_module(MANIFEST_SCRIPT, "material_effect_qualitative_manifest_ready")
    effect_manifest, baseline_manifest, stress_manifest, _, _ = make_synthetic_inputs(tmp_path)
    output_root = tmp_path / "qualitative_renders"
    nvidia_image = output_root / "scene_a/target_1/zoom_016/nvidia/nvidia_0000.png"
    write_image(nvidia_image, (40, 40, 220))

    manifest = module.build_qualitative_render_manifest(
        effect_manifest,
        baseline_manifest,
        stress_manifest,
        output_root=output_root,
        max_cases=4,
    )

    assert manifest["summary"]["ready_case_count"] == 1
    assert manifest["summary"]["ready_for_contact_sheet"] is True
    assert "nvidia_qualitative_renders_missing" not in manifest["summary"]["blockers"]


def test_select_representative_cases_prefers_target_category_diversity(tmp_path: Path) -> None:
    module = load_module(MANIFEST_SCRIPT, "material_effect_qualitative_manifest_diverse")
    effect_manifest, baseline_manifest, stress_manifest, _, _ = make_synthetic_inputs(tmp_path)

    def add_case(sample_id: str, category: str, effects: list[str], verdict: str) -> None:
        effect_manifest["samples"].append(
            {
                "sample_id": sample_id,
                "pair_id": sample_id,
                "source_scene_id": "scene_a",
                "target_category": category,
                "target_id": sample_id.split(".")[0],
                "present_effects": effects,
                "visual_review": {"verdict": verdict},
            }
        )
        baseline_manifest["samples"].append(
            {
                "sample_id": sample_id,
                "source_scene_id": "scene_a",
                "target_category": category,
                "target_prim_path": "/Root/Target",
                "present_effects": effects,
                "conditions": baseline_manifest["samples"][0]["conditions"],
            }
        )
        for condition in ("original", "converted"):
            base = dict(stress_manifest["records"][0 if condition == "original" else 1])
            base["sample_id"] = f"{sample_id}.{condition}"
            base["pair_id"] = sample_id
            base["target_id"] = sample_id.split(".")[0]
            base["object_category"] = category
            stress_manifest["records"].append(base)

    add_case("clock_a.zoom_016", "clock", ["emission", "normal_bump", "displacement_height"], "PASS")
    add_case("clock_b.zoom_016", "clock", ["emission", "normal_bump", "displacement_height"], "PASS")
    add_case("faucet_a.zoom_016", "faucet", ["normal_bump"], "WARN")

    selected = module.select_representative_cases(
        effect_manifest,
        baseline_manifest,
        stress_manifest,
        max_cases=3,
        min_cases=3,
    )

    assert [case["target_category"] for case in selected] == ["cup", "clock", "faucet"]


def test_contact_sheet_is_blocked_until_all_three_condition_images_exist(tmp_path: Path) -> None:
    module = load_module(FIGURE_SCRIPT, "material_effect_qualitative_figure")
    effect_manifest, baseline_manifest, stress_manifest, _, _ = make_synthetic_inputs(tmp_path)
    manifest_module = load_module(MANIFEST_SCRIPT, "material_effect_qualitative_manifest_for_figure")
    manifest = manifest_module.build_qualitative_render_manifest(
        effect_manifest,
        baseline_manifest,
        stress_manifest,
        output_root=tmp_path / "qualitative_renders",
        max_cases=4,
    )

    report = module.build_material_effect_contact_sheet(
        manifest,
        output_path=tmp_path / "figures/qualitative.png",
    )

    assert report["summary"]["ready_case_count"] == 0
    assert report["summary"]["figure_written"] is False
    assert report["summary"]["blockers"] == ["no_complete_qualitative_cases"]


def test_contact_sheet_writes_three_condition_panel_for_ready_cases(tmp_path: Path) -> None:
    module = load_module(FIGURE_SCRIPT, "material_effect_qualitative_figure_ready")
    effect_manifest, baseline_manifest, stress_manifest, _, _ = make_synthetic_inputs(tmp_path)
    output_root = tmp_path / "qualitative_renders"
    write_image(output_root / "scene_a/target_1/zoom_016/nvidia/nvidia_0000.png", (40, 40, 220))
    manifest_module = load_module(MANIFEST_SCRIPT, "material_effect_qualitative_manifest_for_ready_figure")
    manifest = manifest_module.build_qualitative_render_manifest(
        effect_manifest,
        baseline_manifest,
        stress_manifest,
        output_root=output_root,
        max_cases=4,
    )
    output_path = tmp_path / "figures/qualitative.png"

    report = module.build_material_effect_contact_sheet(manifest, output_path=output_path)

    assert report["summary"]["ready_case_count"] == 1
    assert report["summary"]["figure_written"] is True
    assert output_path.exists()
    with Image.open(output_path) as image:
        assert image.width > image.height


def test_contact_sheet_uses_pdf_readable_row_headers_instead_of_tiny_footers(tmp_path: Path) -> None:
    module = load_module(FIGURE_SCRIPT, "material_effect_qualitative_figure_pdf_readable")
    effect_manifest, baseline_manifest, stress_manifest, _, _ = make_synthetic_inputs(tmp_path)
    output_root = tmp_path / "qualitative_renders"
    write_image(output_root / "scene_a/target_1/zoom_016/nvidia/nvidia_0000.png", (40, 40, 220))
    manifest_module = load_module(MANIFEST_SCRIPT, "material_effect_qualitative_manifest_for_pdf_readable_figure")
    manifest = manifest_module.build_qualitative_render_manifest(
        effect_manifest,
        baseline_manifest,
        stress_manifest,
        output_root=output_root,
        max_cases=4,
    )

    report = module.build_material_effect_contact_sheet(
        manifest,
        output_path=tmp_path / "figures/qualitative.png",
    )

    layout = report["summary"]["layout"]
    assert layout["caption_h"] == 0
    assert layout["case_label_font_size"] >= 16
    assert layout["condition_label_font_size"] >= 18
    assert layout["header_h"] >= 40


def test_qualitative_nvidia_runner_skips_existing_outputs(tmp_path: Path) -> None:
    manifest_module = load_module(MANIFEST_SCRIPT, "material_effect_qualitative_manifest_for_runner")
    runner_module = load_module(RUNNER_SCRIPT, "material_effect_qualitative_runner")
    effect_manifest, baseline_manifest, stress_manifest, _, _ = make_synthetic_inputs(tmp_path)
    output_root = tmp_path / "qualitative_renders"
    write_image(output_root / "scene_a/target_1/zoom_016/nvidia/nvidia_0000.png", (40, 40, 220))
    manifest = manifest_module.build_qualitative_render_manifest(
        effect_manifest,
        baseline_manifest,
        stress_manifest,
        output_root=output_root,
        max_cases=4,
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("runner should not be called for existing outputs")

    run_manifest = runner_module.run_qualitative_nvidia_renders(
        manifest,
        log_root=tmp_path / "logs",
        runner=fail_if_called,
    )

    assert run_manifest["summary"]["skipped_existing_count"] == 1
    assert run_manifest["summary"]["attempted_count"] == 0
    assert run_manifest["summary"]["ready_output_count"] == 1


def test_qualitative_nvidia_runner_records_failed_attempt(tmp_path: Path) -> None:
    manifest_module = load_module(MANIFEST_SCRIPT, "material_effect_qualitative_manifest_for_failed_runner")
    runner_module = load_module(RUNNER_SCRIPT, "material_effect_qualitative_runner_failed")
    effect_manifest, baseline_manifest, stress_manifest, _, _ = make_synthetic_inputs(tmp_path)
    manifest = manifest_module.build_qualitative_render_manifest(
        effect_manifest,
        baseline_manifest,
        stress_manifest,
        output_root=tmp_path / "qualitative_renders",
        max_cases=4,
    )

    def fake_runner(command, cwd, stdout, stderr, text, timeout):
        stdout.write("started\n")
        stderr.write("failed\n")
        return SimpleNamespace(returncode=7)

    run_manifest = runner_module.run_qualitative_nvidia_renders(
        manifest,
        log_root=tmp_path / "logs",
        runner=fake_runner,
        timeout_seconds=12,
    )

    assert run_manifest["summary"]["attempted_count"] == 1
    assert run_manifest["summary"]["failed_count"] == 1
    assert run_manifest["summary"]["ready_output_count"] == 0
    assert run_manifest["records"][0]["exit_code"] == 7
    assert run_manifest["records"][0]["output_exists"] is False
