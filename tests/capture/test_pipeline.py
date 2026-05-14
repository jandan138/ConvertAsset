# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from convert_asset.camera.bounds import Bounds3D
from convert_asset.capture import pipeline
from tests.capture.test_targets import fake_grscenes_stage


def _bounds_for_target(target):
    if target.name == "model_chairhash_0":
        return Bounds3D(
            min=(0.0, 0.0, 0.0),
            max=(2.0, 2.0, 2.0),
            center=(1.0, 1.0, 1.0),
            size=(2.0, 2.0, 2.0),
        )
    return None


def test_run_target_list_writes_targets_json(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(pipeline, "_open_usd_stage", lambda _path: fake_grscenes_stage())
    monkeypatch.setattr(pipeline, "_safe_bounds", lambda _stage, target: _bounds_for_target(target))
    out_path = tmp_path / "targets.json"

    code = pipeline.run_target_list(
        scene_usd_path="/tmp/layout.usd",
        output_path=str(out_path),
        target_scope="auto",
        target_level="object",
        limit=1,
    )

    captured = capsys.readouterr()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert code == 0
    assert "[target-list] targets=1" in captured.out
    assert len(payload) == 1
    assert payload[0]["category"] == "chair"
    assert payload[0]["mesh_count"] == 2


def test_run_target_list_excludes_targets_without_bounds(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(pipeline, "_open_usd_stage", lambda _path: fake_grscenes_stage())
    monkeypatch.setattr(pipeline, "_safe_bounds", lambda _stage, target: _bounds_for_target(target))
    out_path = tmp_path / "targets.json"

    code = pipeline.run_target_list(
        scene_usd_path="/tmp/layout.usd",
        output_path=str(out_path),
        target_scope="auto",
        target_level="object",
        limit=2,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert code == 0
    assert [item["name"] for item in payload] == ["model_chairhash_0"]

