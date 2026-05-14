# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import math

from convert_asset.camera.bounds import Bounds3D
from convert_asset.camera.poses import CameraPoseSpec, plan_orbit_poses
from convert_asset.capture.manifest import CaptureRecord, append_capture_record
from convert_asset.capture.targets import TargetSpec


def test_plan_orbit_poses_returns_finite_positions() -> None:
    bounds = Bounds3D(
        min=(0.0, 0.0, 0.0),
        max=(2.0, 2.0, 2.0),
        center=(1.0, 1.0, 1.0),
        size=(2.0, 2.0, 2.0),
    )

    poses = plan_orbit_poses(bounds, views=4)

    assert len(poses) == 4
    assert {pose.view_index for pose in poses} == {0, 1, 2, 3}
    assert [pose.elevation_deg for pose in poses] == [35.0, 35.0, -35.0, -35.0]
    assert all(math.isfinite(value) for pose in poses for value in pose.position)
    assert all(pose.target == bounds.center for pose in poses)


def test_plan_orbit_poses_uses_even_view_count() -> None:
    bounds = Bounds3D(
        min=(-1.0, -1.0, -1.0),
        max=(1.0, 1.0, 1.0),
        center=(0.0, 0.0, 0.0),
        size=(2.0, 2.0, 2.0),
    )

    poses = plan_orbit_poses(bounds, views=5)

    assert len(poses) == 6
    assert poses[-1].view_index == 5


def test_manifest_writer_outputs_jsonl_records(tmp_path) -> None:
    target = TargetSpec(
        prim_path="/Root/Meshes/Furnitures/chair/model_chairhash_0",
        target_id="Root_Meshes_Furnitures_chair_model_chairhash_0",
        name="model_chairhash_0",
        category="chair",
        level="object",
        mesh_count=2,
        type_name="Xform",
    )
    bounds = Bounds3D(
        min=(0.0, 0.0, 0.0),
        max=(2.0, 2.0, 2.0),
        center=(1.0, 1.0, 1.0),
        size=(2.0, 2.0, 2.0),
    )
    pose = CameraPoseSpec(
        view_index=0,
        azimuth_deg=30.0,
        elevation_deg=35.0,
        distance=3.5,
        position=(4.0, 1.0, 3.0),
        target=(1.0, 1.0, 1.0),
    )
    record = CaptureRecord(
        scene_usd_path="/tmp/layout.usd",
        target=target,
        bounds=bounds,
        pose=pose,
        output_path="/tmp/out/view_000.png",
        status="ok",
        error=None,
    )
    manifest_path = tmp_path / "manifest.jsonl"

    append_capture_record(manifest_path, record)

    loaded = json.loads(manifest_path.read_text(encoding="utf-8").strip())
    assert loaded["scene_usd_path"] == "/tmp/layout.usd"
    assert loaded["target_id"] == target.target_id
    assert loaded["category"] == "chair"
    assert loaded["bbox"]["center"] == [1.0, 1.0, 1.0]
    assert loaded["camera"]["view_index"] == 0
    assert loaded["status"] == "ok"

