import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_visibility_aware_views.py"


def load_visibility_module():
    spec = importlib.util.spec_from_file_location("grscenes_plan_visibility_aware_views", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bbox(min_xyz, max_xyz):
    return {"min": list(min_xyz), "max": list(max_xyz)}


def camera(position, look_at=(10.0, 0.0, 0.0)):
    return {
        "camera_prim_path": "/World/GRScenesVLMTargetCamera",
        "position_world": list(position),
        "look_at": list(look_at),
    }


def test_segment_aabb_interval_reports_hit_range() -> None:
    module = load_visibility_module()

    hit = module.segment_aabb_interval([0.0, 0.0, 0.0], [10.0, 0.0, 0.0], bbox([4.0, -1.0, -1.0], [6.0, 1.0, 1.0]))

    assert hit == {"t_enter": 0.4, "t_exit": 0.6}


def test_classify_candidate_blocks_camera_inside_non_target_obstacle() -> None:
    module = load_visibility_module()

    result = module.classify_visibility_candidate(
        camera=camera([0.0, 0.0, 0.0]),
        target_bbox=bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5]),
        obstacles=[
            {"prim_path": "/Room/Wall", "bbox": bbox([-1.0, -1.0, -1.0], [1.0, 1.0, 1.0])},
        ],
    )

    assert result["status"] == "blocked_camera_inside_obstacle_aabb"
    assert result["blocker_prim_path"] == "/Room/Wall"


def test_classify_candidate_blocks_obstacle_before_target() -> None:
    module = load_visibility_module()

    result = module.classify_visibility_candidate(
        camera=camera([0.0, 0.0, 0.0]),
        target_bbox=bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5]),
        obstacles=[
            {"prim_path": "/Room/Table", "bbox": bbox([4.0, -1.0, -1.0], [5.0, 1.0, 1.0])},
        ],
    )

    assert result["status"] == "blocked_centerline_aabb"
    assert result["blocker_prim_path"] == "/Room/Table"
    assert result["blocker_interval"]["t_enter"] < result["target_interval"]["t_enter"]


def test_classify_candidate_keeps_obstacle_behind_target_clear() -> None:
    module = load_visibility_module()

    result = module.classify_visibility_candidate(
        camera=camera([0.0, 0.0, 0.0]),
        target_bbox=bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5]),
        obstacles=[
            {"prim_path": "/Room/BackWall", "bbox": bbox([12.0, -1.0, -1.0], [13.0, 1.0, 1.0])},
        ],
    )

    assert result["status"] == "centerline_clear"
    assert result["blocker_prim_path"] is None


def test_build_visibility_report_selects_first_clear_view_for_target() -> None:
    module = load_visibility_module()
    manifest = {
        "records": [],
        "render_pairs": [
            {
                "pair_id": "target_a.view_000",
                "target_id": "target_a",
                "source_scene_id": "scene_usd",
                "view": {"view_id": "view_000", "camera": camera([0.0, 0.0, 0.0])},
                "conditions": [
                    {"world_bbox": bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5])},
                    {"world_bbox": bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5])},
                ],
            },
            {
                "pair_id": "target_a.view_001",
                "target_id": "target_a",
                "source_scene_id": "scene_usd",
                "view": {"view_id": "view_001", "camera": camera([0.0, 3.0, 0.0])},
                "conditions": [
                    {"world_bbox": bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5])},
                    {"world_bbox": bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5])},
                ],
            },
        ],
    }
    geometry_index = {
        "scene_usd": [
            {"prim_path": "/Room/Table", "bbox": bbox([4.0, -1.0, -1.0], [5.0, 1.0, 1.0])},
        ]
    }

    report = module.build_visibility_report(manifest, geometry_index=geometry_index)

    assert report["summary"]["visibility_method"] == "single_centerline_vs_non_target_aabb_preflight"
    assert report["summary"]["centerline_clear_pair_count"] == 1
    assert report["summary"]["blocked_pair_count"] == 1
    assert report["recommended_pairs_by_target"]["target_a"]["pair_id"] == "target_a.view_001"


def test_build_visibility_report_unwraps_geometry_index_report_schema() -> None:
    module = load_visibility_module()
    manifest = {
        "render_pairs": [
            {
                "pair_id": "target_a.view_000",
                "target_id": "target_a",
                "source_scene_id": "scene_usd",
                "view": {"view_id": "view_000", "camera": camera([0.0, 0.0, 0.0])},
                "conditions": [
                    {"world_bbox": bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5])},
                    {"world_bbox": bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5])},
                ],
            }
        ],
    }
    geometry_report = {
        "status": "visibility_geometry_index",
        "geometry_index": {
            "scene_usd": [
                {"prim_path": "/Room/Table", "bbox": bbox([4.0, -1.0, -1.0], [5.0, 1.0, 1.0])},
            ]
        },
    }

    report = module.build_visibility_report(manifest, geometry_index=geometry_report)

    assert report["summary"]["geometry_source_schema"] == "visibility_geometry_index_report"
    assert report["pair_reviews"][0]["visibility_status"] == "blocked_centerline_aabb"


def test_build_visibility_report_rejects_missing_scene_geometry() -> None:
    module = load_visibility_module()
    manifest = {
        "render_pairs": [
            {
                "pair_id": "target_a.view_000",
                "target_id": "target_a",
                "source_scene_id": "scene_usd",
                "view": {"view_id": "view_000", "camera": camera([0.0, 0.0, 0.0])},
                "conditions": [
                    {"world_bbox": bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5])},
                    {"world_bbox": bbox([9.5, -0.5, -0.5], [10.5, 0.5, 0.5])},
                ],
            }
        ],
    }

    try:
        module.build_visibility_report(manifest, geometry_index={})
    except ValueError as exc:
        assert "missing geometry scenes" in str(exc)
    else:
        raise AssertionError("missing scene geometry should not silently clear views")
