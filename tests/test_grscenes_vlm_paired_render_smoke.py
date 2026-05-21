import importlib.util
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_paired_render_smoke.py"


def load_smoke_module():
    spec = importlib.util.spec_from_file_location("grscenes_run_paired_render_smoke", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_png(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (4, 3), color=color).save(path)


def test_build_smoke_report_runs_manifest_commands_and_hashes_artifacts(tmp_path: Path) -> None:
    module = load_smoke_module()
    renderer_script = tmp_path / "scripts/render.py"
    renderer_script.parent.mkdir(parents=True)
    renderer_script.write_text("print('render')\n", encoding="utf-8")
    original_png = tmp_path / "renders/original/original_0000.png"
    converted_png = tmp_path / "renders/converted/converted_0000.png"
    _write_png(original_png, (200, 0, 0))
    _write_png(converted_png, (20, 20, 20))
    manifest = {
        "schema_version": 1,
        "renderer_settings": {"renderer": "RayTracedLighting", "image_width": 4, "image_height": 3},
        "render_pairs": [
            {
                "pair_id": "pair.view_001",
                "source_scene_id": "scene_usd",
                "view": {"view_id": "view_001"},
                "conditions": [
                    {
                        "sample_id": "pair.view_001.original",
                        "material_condition": "original",
                        "object_category": "bottle",
                        "output_image": str(original_png),
                        "render_command": ["python", str(renderer_script), "original", "--wait-frames", "8"],
                    },
                    {
                        "sample_id": "pair.view_001.converted",
                        "material_condition": "converted",
                        "object_category": "bottle",
                        "output_image": str(converted_png),
                        "render_command": ["python", str(renderer_script), "converted", "--wait-frames", "8"],
                    },
                ],
            }
        ],
    }
    manifest_path = tmp_path / "render_manifest.json"
    report_path = tmp_path / "paired_render_smoke_report.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    calls = []

    class Completed:
        returncode = 0

    def fake_runner(cmd, *, cwd, stdout, stderr, text, timeout):
        calls.append(cmd)
        stdout.write("Saved frame\n")
        if "original" in cmd:
            stderr.write("KooPbr KooPbr_maps Failed to create MDL shade node\n")
        return Completed()

    report = module.build_smoke_report(
        manifest,
        pair_id="pair.view_001",
        render_manifest_path=manifest_path,
        report_path=report_path,
        log_dir=tmp_path / "logs",
        runner=fake_runner,
    )

    assert calls == [
        ["python", str(renderer_script), "original", "--wait-frames", "8"],
        ["python", str(renderer_script), "converted", "--wait-frames", "8"],
    ]
    assert report["render_manifest"]["path"] == str(manifest_path)
    assert len(report["render_manifest"]["hash_sha256"]) == 64
    assert report["pair_id"] == "pair.view_001"
    assert report["summary"]["both_commands_exit_zero"] is True
    assert report["summary"]["both_images_exist"] is True
    assert report["summary"]["original_mdl_error_signal"] == 2
    assert report["summary"]["converted_mdl_error_signal"] == 0
    assert "all-black" not in report["summary"]["interpretation"]
    assert report["records"][0]["render_command"] == ["python", str(renderer_script), "original", "--wait-frames", "8"]
    assert report["records"][0]["renderer_script"]["path"] == str(renderer_script)
    assert len(report["records"][0]["renderer_script"]["hash_sha256"]) == 64
    assert len(report["records"][0]["image"]["hash_sha256"]) == 64
    assert len(report["records"][0]["stdout_summary"]["hash_sha256"]) == 64
    assert report["records"][0]["stdout_summary"]["path"].endswith(".stdout.txt")
    assert report["records"][0]["stderr_summary"]["path"].endswith(".stderr.txt")
    assert report["records"][0]["image"]["non_dark_pixel_count"] == 12
