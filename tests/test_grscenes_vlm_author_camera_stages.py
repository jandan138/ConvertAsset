import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/author_render_camera_stages.py"


def load_author_module():
    spec = importlib.util.spec_from_file_location("grscenes_author_render_camera_stages", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_render_manifest(tmp_path: Path) -> dict:
    input_usd = tmp_path / "inputs/scene.usd"
    input_usd.parent.mkdir(parents=True)
    input_usd.write_text("#usda 1.0\n", encoding="utf-8")
    stage_path = tmp_path / "renders/scene/target/view/original/original_camera.usd"
    camera = {
        "camera_prim_path": "/World/GRScenesVLMTargetCamera",
        "position_world": [3.0, 0.0, 1.0],
        "target_world": [0.0, 0.0, 0.5],
        "look_at": [0.0, 0.0, 0.5],
        "up_world": [0.0, 0.0, 1.0],
        "focal_length_mm": 9.0,
        "horizontal_aperture_mm": 20.955,
        "vertical_aperture_mm": 15.71625,
        "clipping_range": [0.01, 100.0],
        "start_frame": 0,
        "end_frame": 0,
        "time_codes_per_second": 24,
    }
    return {
        "schema_version": 1,
        "status": "planned_render_manifest",
        "records": [
            {
                "sample_id": "pair.original",
                "pair_id": "pair",
                "material_condition": "original",
                "usd_path": str(input_usd),
                "camera_stage_path": str(stage_path),
                "camera_stage_exists": False,
                "camera": camera,
            }
        ],
    }


def test_module_imports_without_pxr() -> None:
    module = load_author_module()

    assert hasattr(module, "build_authoring_report")


def test_build_authoring_report_dry_run_plans_pending_camera_stage(tmp_path: Path) -> None:
    module = load_author_module()
    manifest = make_render_manifest(tmp_path)

    report = module.build_authoring_report(manifest, apply=False)

    assert report["dry_run"] is True
    assert report["summary"]["planned_camera_stage_count"] == 1
    assert report["summary"]["authored_camera_stage_count"] == 0
    assert report["jobs"][0]["camera_stage_path"].endswith("original_camera.usd")
    assert report["jobs"][0]["blocked_by"] == []
    assert report["jobs"][0]["render_lighting"] == {
        "enabled": True,
        "dome_light_path": "/World/GRScenesRenderDomeLight",
        "distant_light_path": "/World/GRScenesRenderDistantLight",
        "dome_intensity": 1000.0,
        "distant_intensity": 3000.0,
        "distant_angle": 1.0,
        "distant_rotation_xyz": [-45.0, 30.0, 0.0],
    }


def test_build_authoring_report_does_not_trust_stale_manifest_camera_exists(tmp_path: Path) -> None:
    module = load_author_module()
    manifest = make_render_manifest(tmp_path)
    manifest["records"][0]["camera_stage_exists"] = True
    assert not Path(manifest["records"][0]["camera_stage_path"]).exists()

    report = module.build_authoring_report(manifest, apply=False)

    assert report["summary"]["selected_record_count"] == 1
    assert report["summary"]["planned_camera_stage_count"] == 1
    assert report["jobs"][0]["blocked_by"] == []


def test_build_authoring_report_apply_uses_writer_and_records_created_stage(tmp_path: Path) -> None:
    module = load_author_module()
    manifest = make_render_manifest(tmp_path)
    calls = []

    def fake_writer(job):
        calls.append(job)
        Path(job["camera_stage_path"]).parent.mkdir(parents=True)
        Path(job["camera_stage_path"]).write_text("# camera\n", encoding="utf-8")

    report = module.build_authoring_report(manifest, apply=True, writer=fake_writer)

    assert len(calls) == 1
    assert report["dry_run"] is False
    assert report["summary"]["authored_camera_stage_count"] == 1
    assert report["jobs"][0]["status"] == "authored"
    assert Path(report["jobs"][0]["camera_stage_path"]).exists()


def test_build_authoring_report_blocks_missing_input(tmp_path: Path) -> None:
    module = load_author_module()
    manifest = make_render_manifest(tmp_path)
    Path(manifest["records"][0]["usd_path"]).unlink()

    report = module.build_authoring_report(manifest, apply=False)

    assert report["summary"]["blocked_camera_stage_count"] == 1
    assert report["jobs"][0]["blocked_by"] == ["input_usd_missing"]


def test_camera_transform_rows_look_at_target(tmp_path: Path) -> None:
    module = load_author_module()
    camera = make_render_manifest(tmp_path)["records"][0]["camera"]

    rows = module.camera_transform_rows(camera)

    assert len(rows) == 4
    assert rows[3] == [3.0, 0.0, 1.0, 1.0]
    assert rows[2][3] == 0.0


def test_main_writes_report(tmp_path: Path) -> None:
    module = load_author_module()
    manifest = make_render_manifest(tmp_path)
    manifest_path = tmp_path / "render_manifest.json"
    report_path = tmp_path / "author_report.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    status = module.main(["--render-manifest", str(manifest_path), "--out", str(report_path)])

    assert status == 0
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert written["summary"]["planned_camera_stage_count"] == 1
    assert written["render_manifest"]["path"] == str(manifest_path)
    assert len(written["render_manifest"]["hash_sha256"]) == 64
    assert written["generator_provenance"]["command"][-4:] == [
        "--render-manifest",
        str(manifest_path),
        "--out",
        str(report_path),
    ]
    assert len(written["generator_provenance"]["script_hash_sha256"]) == 64


def test_main_apply_returns_nonzero_when_selected_job_is_blocked(tmp_path: Path) -> None:
    module = load_author_module()
    manifest = make_render_manifest(tmp_path)
    Path(manifest["records"][0]["usd_path"]).unlink()
    manifest_path = tmp_path / "render_manifest.json"
    report_path = tmp_path / "author_report.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    status = module.main([
        "--render-manifest",
        str(manifest_path),
        "--out",
        str(report_path),
        "--apply",
    ])

    assert status == 1
