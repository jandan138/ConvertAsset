import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/project_target_bboxes.py"


def load_projection_module():
    spec = importlib.util.spec_from_file_location("grscenes_project_target_bboxes", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def camera() -> dict:
    return {
        "position_world": [0.0, 0.0, 0.0],
        "look_at": [10.0, 0.0, 0.0],
        "up_world": [0.0, 0.0, 1.0],
        "fov_h_deg": 90.0,
    }


def bbox(min_xyz, max_xyz) -> dict:
    return {"min": list(min_xyz), "max": list(max_xyz), "center": [10.0, 0.0, 0.0]}


def test_project_point_places_look_at_at_image_center() -> None:
    module = load_projection_module()

    point = module.project_world_point(camera(), [10.0, 0.0, 0.0], image_width=100, image_height=100)

    assert point["pixel_xy"] == [50.0, 50.0]
    assert point["in_front"] is True


def test_project_point_respects_screen_orientation_and_aspect() -> None:
    module = load_projection_module()

    right = module.project_world_point(camera(), [10.0, -1.0, 0.0], image_width=600, image_height=450)
    left = module.project_world_point(camera(), [10.0, 1.0, 0.0], image_width=600, image_height=450)
    up = module.project_world_point(camera(), [10.0, 0.0, 1.0], image_width=600, image_height=450)
    down = module.project_world_point(camera(), [10.0, 0.0, -1.0], image_width=600, image_height=450)

    assert right["pixel_xy"][0] > 300.0
    assert left["pixel_xy"][0] < 300.0
    assert up["pixel_xy"][1] < 225.0
    assert down["pixel_xy"][1] > 225.0
    assert right["pixel_xy"] == [330.0, 225.0]
    assert up["pixel_xy"] == [300.0, 195.0]


def test_project_bbox_returns_clipped_image_box_and_area() -> None:
    module = load_projection_module()

    result = module.project_world_bbox(
        camera(),
        bbox([9.0, -1.0, -1.0], [11.0, 1.0, 1.0]),
        image_width=100,
        image_height=100,
        min_area_px=25.0,
    )

    assert result["status"] == "projection_ok"
    assert result["bbox_xyxy"][0] < 50.0 < result["bbox_xyxy"][2]
    assert result["bbox_xyxy"][1] < 50.0 < result["bbox_xyxy"][3]
    assert result["bbox_area_px"] > 25.0
    assert result["center_pixel_xy"] == [50.0, 50.0]


def test_project_bbox_rejects_box_behind_camera() -> None:
    module = load_projection_module()

    result = module.project_world_bbox(
        camera(),
        bbox([-11.0, -1.0, -1.0], [-9.0, 1.0, 1.0]),
        image_width=100,
        image_height=100,
    )

    assert result["status"] == "projection_failed_no_front_corners"
    assert result["bbox_xyxy"] is None


def test_build_projection_report_uses_recommended_pairs_only() -> None:
    module = load_projection_module()
    render_manifest = {
        "renderer_settings": {"image_width": 100, "image_height": 100},
        "render_pairs": [
            {
                "pair_id": "target.view_000",
                "target_id": "target",
                "source_scene_id": "scene",
                "target_prim_path": "/Root/Target",
                "view": {"view_id": "view_000", "camera": camera()},
                "conditions": [
                    {
                        "sample_id": "target.view_000.original",
                        "material_condition": "original",
                        "world_bbox": bbox([9.0, -1.0, -1.0], [11.0, 1.0, 1.0]),
                        "output_image": "/renders/original.png",
                        "task": "s1_referred_object_localization",
                        "target": {"category": "cup", "expected_answers": ["cup"]},
                    },
                    {
                        "sample_id": "target.view_000.converted",
                        "material_condition": "converted",
                        "world_bbox": bbox([9.0, -1.0, -1.0], [11.0, 1.0, 1.0]),
                        "output_image": "/renders/converted.png",
                        "target": {"category": "cup", "expected_answers": ["cup"]},
                    },
                ],
            },
            {"pair_id": "target.view_001", "conditions": []},
        ],
    }
    preflight_report = {"recommended_pairs_by_target": {"target": {"pair_id": "target.view_000"}}}
    render_summary = {"pairs": [{"pair_id": "target.view_000", "render_smoke_pass": True}]}

    report = module.build_projection_report(
        render_manifest,
        preflight_report=preflight_report,
        render_summary=render_summary,
        min_area_px=25.0,
    )

    assert report["summary"]["recommended_pair_count"] == 1
    assert report["summary"]["projection_ok_pair_count"] == 1
    assert len(report["pairs"]) == 1
    assert len(report["scoring_records"]) == 2
    assert report["scoring_records"][0]["target"]["bbox_xyxy"] == report["pairs"][0]["projection"]["bbox_xyxy"]


def test_build_projection_report_can_use_explicit_pair_ids() -> None:
    module = load_projection_module()
    render_manifest = {
        "renderer_settings": {"image_width": 100, "image_height": 100},
        "render_pairs": [
            {"pair_id": "target.view_000", "conditions": []},
            {
                "pair_id": "target.view_001",
                "target_id": "target",
                "source_scene_id": "scene",
                "target_prim_path": "/Root/Target",
                "view": {"view_id": "view_001", "camera": camera()},
                "conditions": [
                    {
                        "sample_id": "target.view_001.original",
                        "material_condition": "original",
                        "world_bbox": bbox([9.0, -1.0, -1.0], [11.0, 1.0, 1.0]),
                        "output_image": "/renders/view_001_original.png",
                        "target": {"category": "cup", "expected_answers": ["cup"]},
                    }
                ],
            },
            {
                "pair_id": "target.view_002",
                "target_id": "target",
                "source_scene_id": "scene",
                "target_prim_path": "/Root/Target",
                "view": {"view_id": "view_002", "camera": camera()},
                "conditions": [
                    {
                        "sample_id": "target.view_002.original",
                        "material_condition": "original",
                        "world_bbox": bbox([9.0, -1.0, -1.0], [11.0, 1.0, 1.0]),
                        "output_image": "/renders/view_002_original.png",
                        "target": {"category": "cup", "expected_answers": ["cup"]},
                    }
                ],
            },
        ],
    }
    preflight_report = {"recommended_pairs_by_target": {"target": {"pair_id": "target.view_000"}}}
    render_summary = {
        "pairs": [
            {"pair_id": "target.view_001", "render_smoke_pass": True},
            {"pair_id": "target.view_002", "render_smoke_pass": True},
        ]
    }

    report = module.build_projection_report(
        render_manifest,
        preflight_report=preflight_report,
        render_summary=render_summary,
        pair_ids=["target.view_001", "target.view_002"],
        min_area_px=25.0,
    )

    assert report["summary"]["selection_mode"] == "explicit_pair_ids"
    assert report["summary"]["selected_pair_count"] == 2
    assert report["summary"]["recommended_pair_count"] == 1
    assert report["pairs"][0]["pair_id"] == "target.view_001"
    assert report["pairs"][1]["pair_id"] == "target.view_002"
    assert len(report["scoring_records"]) == 2


def test_main_writes_projection_report(tmp_path: Path) -> None:
    module = load_projection_module()
    render_manifest = {
        "renderer_settings": {"image_width": 100, "image_height": 100},
        "render_pairs": [
            {
                "pair_id": "target.view_000",
                "target_id": "target",
                "source_scene_id": "scene",
                "target_prim_path": "/Root/Target",
                "view": {"view_id": "view_000", "camera": camera()},
                "conditions": [
                    {
                        "sample_id": "target.view_000.original",
                        "material_condition": "original",
                        "world_bbox": bbox([9.0, -1.0, -1.0], [11.0, 1.0, 1.0]),
                        "output_image": "/renders/original.png",
                        "target": {"category": "cup", "expected_answers": ["cup"]},
                    }
                ],
            }
        ],
    }
    preflight_report = {"recommended_pairs_by_target": {"target": {"pair_id": "target.view_000"}}}
    render_summary = {"pairs": [{"pair_id": "target.view_000", "render_smoke_pass": True}]}
    render_manifest_path = tmp_path / "render_manifest.json"
    preflight_path = tmp_path / "visibility_preflight_report.json"
    render_summary_path = tmp_path / "recommended_paired_render_summary.json"
    out = tmp_path / "target_projection_qa_report.json"
    render_manifest_path.write_text(json.dumps(render_manifest), encoding="utf-8")
    preflight_path.write_text(json.dumps(preflight_report), encoding="utf-8")
    render_summary_path.write_text(json.dumps(render_summary), encoding="utf-8")

    status = module.main(
        [
            "--render-manifest",
            str(render_manifest_path),
            "--preflight-report",
            str(preflight_path),
            "--render-summary",
            str(render_summary_path),
            "--out",
            str(out),
            "--min-area-px",
            "25",
        ]
    )

    assert status == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["summary"]["projection_ok_pair_count"] == 1
    assert len(written["render_manifest"]["hash_sha256"]) == 64
