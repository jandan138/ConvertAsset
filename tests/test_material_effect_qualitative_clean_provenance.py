import importlib.util
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("material_effect_clean_provenance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 12), color=(128, 128, 128)).save(path)


def make_manifest(tmp_path: Path) -> dict:
    sample_id = "target_1.zoom_016"
    records = []
    for condition, subdir, filename in (
        ("original_MDL", "original", "original_0000.png"),
        ("existing_noMDL", "converted", "converted_0000.png"),
        ("nvidia_asset_converter_preview_or_bake", "nvidia", "nvidia_0000.png"),
    ):
        image_path = tmp_path / "renders" / sample_id / subdir / filename
        write_image(image_path)
        records.append(
            {
                "sample_id": sample_id,
                "pair_id": sample_id,
                "condition": condition,
                "status": "image_ready",
                "image": {
                    "path": str(image_path),
                    "exists": True,
                    "status": "ready",
                },
            }
        )
    return {
        "selected_cases": [{"sample_id": sample_id, "pair_id": sample_id}],
        "records": records,
    }


def write_original_log(tmp_path: Path, sample_id: str, text: str) -> Path:
    path = tmp_path / "logs" / sample_id / f"{sample_id}.original.stderr.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_clean_original_mdl_log_allows_clean_material_effect_panel(tmp_path: Path) -> None:
    module = load_module()
    manifest = make_manifest(tmp_path)
    write_original_log(tmp_path, "target_1.zoom_016", "[Info] render completed\n")

    report = module.check_qualitative_clean_provenance(
        manifest,
        log_roots=[tmp_path / "logs"],
    )

    assert report["ok"] is True
    assert report["status"] == "clean_material_effect_panel_ready"
    assert report["summary"]["complete_case_count"] == 1
    assert report["summary"]["checked_original_mdl_log_count"] == 1
    assert report["summary"]["blockers"] == []


def test_original_mdl_koo_pbr_error_blocks_clean_material_effect_panel(tmp_path: Path) -> None:
    module = load_module()
    manifest = make_manifest(tmp_path)
    write_original_log(
        tmp_path,
        "target_1.zoom_016",
        "C120 could not find module '::KooPbr' in module path\n"
        "Failed to create MDL shade node\n",
    )

    report = module.check_qualitative_clean_provenance(
        manifest,
        log_roots=[tmp_path / "logs"],
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_material_effect_panel"
    assert "original_mdl_error_signal" in report["summary"]["blockers"]
    assert report["summary"]["original_mdl_error_signal_count"] == 1
    assert report["violations"][0]["sample_id"] == "target_1.zoom_016"
    assert report["violations"][0]["matched_error_terms"] == [
        "C120",
        "Failed to create MDL shade node",
        "KooPbr",
        "could not find module",
    ]
