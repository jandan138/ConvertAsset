import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/extract_visibility_geometry_index.py"


def load_geometry_module():
    spec = importlib.util.spec_from_file_location("grscenes_extract_visibility_geometry_index", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_imports_without_pxr() -> None:
    module = load_geometry_module()

    assert hasattr(module, "scene_geometry_jobs")


def test_target_path_descendant_filter() -> None:
    module = load_geometry_module()

    assert module.is_target_or_descendant("/Root/Object", ["/Root/Object"])
    assert module.is_target_or_descendant("/Root/Object/Mesh", ["/Root/Object"])
    assert not module.is_target_or_descendant("/Root/ObjectSibling", ["/Root/Object"])


def test_bbox_record_rejects_usd_extreme_bounds() -> None:
    module = load_geometry_module()

    record = module._bbox_record(
        "/Root/BadCeiling",
        "Mesh",
        [-3.4028234663852886e38, -3.4028234663852886e38, -3.4028234663852886e38],
        [3.4028234663852886e38, 3.4028234663852886e38, 3.4028234663852886e38],
        max_diagonal=1000.0,
        max_abs_coordinate=1_000_000.0,
    )

    assert record is None


def test_bbox_record_rejects_overlarge_scene_component() -> None:
    module = load_geometry_module()

    record = module._bbox_record(
        "/Root/OverlargeComponent",
        "Mesh",
        [-2000.0, -2000.0, -5.0],
        [2000.0, 2000.0, 5.0],
        max_diagonal=1000.0,
        max_abs_coordinate=1_000_000.0,
    )

    assert record is None


def test_scene_geometry_jobs_groups_unique_scene_inputs() -> None:
    module = load_geometry_module()
    manifest = {
        "render_pairs": [
            {
                "source_scene_id": "scene_a",
                "target_prim_path": "/Root/TargetA",
                "conditions": [
                    {"material_condition": "original", "usd_path": "/scratch/scene_a/start_result_raw.usd"},
                    {"material_condition": "converted", "usd_path": "/scratch/scene_a/start_result_raw_noMDL.usd"},
                ],
            },
            {
                "source_scene_id": "scene_a",
                "target_prim_path": "/Root/TargetB",
                "conditions": [
                    {"material_condition": "original", "usd_path": "/scratch/scene_a/start_result_raw.usd"},
                    {"material_condition": "converted", "usd_path": "/scratch/scene_a/start_result_raw_noMDL.usd"},
                ],
            },
        ],
    }

    jobs = module.scene_geometry_jobs(manifest)

    assert jobs == [
        {
            "source_scene_id": "scene_a",
            "usd_path": "/scratch/scene_a/start_result_raw.usd",
            "target_prim_paths": ["/Root/TargetA", "/Root/TargetB"],
        }
    ]


def test_build_geometry_index_uses_injected_collector_once_per_scene() -> None:
    module = load_geometry_module()
    manifest = {
        "render_pairs": [
            {
                "source_scene_id": "scene_a",
                "target_prim_path": "/Root/TargetA",
                "conditions": [
                    {"material_condition": "original", "usd_path": "/scratch/scene_a/start_result_raw.usd"},
                ],
            }
        ],
    }
    calls = []

    def fake_collector(*, usd_path, target_prim_paths, min_diagonal, max_diagonal, max_abs_coordinate):
        calls.append((usd_path, target_prim_paths, min_diagonal, max_diagonal, max_abs_coordinate))
        return [{"prim_path": "/Room/Wall", "bbox": {"min": [0, 0, 0], "max": [1, 1, 1]}}]

    report = module.build_geometry_index_report(
        manifest,
        collector=fake_collector,
        min_diagonal=0.25,
        max_diagonal=1000.0,
        max_abs_coordinate=1_000_000.0,
    )

    assert calls == [("/scratch/scene_a/start_result_raw.usd", ["/Root/TargetA"], 0.25, 1000.0, 1_000_000.0)]
    assert report["summary"]["scene_count"] == 1
    assert report["summary"]["obstacle_count"] == 1
    assert report["summary"]["max_diagonal"] == 1000.0
    assert report["summary"]["max_abs_coordinate"] == 1_000_000.0
    assert report["geometry_index"]["scene_a"][0]["prim_path"] == "/Room/Wall"


def test_main_writes_geometry_index_with_injected_collector(tmp_path: Path) -> None:
    module = load_geometry_module()
    manifest = {
        "render_pairs": [
            {
                "source_scene_id": "scene_a",
                "target_prim_path": "/Root/TargetA",
                "conditions": [
                    {"material_condition": "original", "usd_path": "/scratch/scene_a/start_result_raw.usd"},
                ],
            }
        ],
    }
    manifest_path = tmp_path / "render_manifest.json"
    out_path = tmp_path / "visibility_geometry_index.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    status = module.main(
        [
            "--render-manifest",
            str(manifest_path),
            "--out",
            str(out_path),
        ],
        collector=lambda **_: [],
    )

    assert status == 0
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["render_manifest"]["path"] == str(manifest_path)
    assert len(written["render_manifest"]["hash_sha256"]) == 64
