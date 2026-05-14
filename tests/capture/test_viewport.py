# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import types

from convert_asset.render.viewport import _wait_for_capture_result, open_stage


class _FutureLikeCapture:
    def __init__(self) -> None:
        self.completion_frames = None

    def wait_for_result(self, completion_frames=0):
        self.completion_frames = completion_frames
        return True


class _AsyncFutureLikeCapture:
    async def wait_for_result(self, completion_frames=0):
        return True


def test_wait_for_capture_result_uses_future_wait_method() -> None:
    capture = _FutureLikeCapture()

    assert _wait_for_capture_result(capture, completion_frames=30) is True
    assert capture.completion_frames == 30


def test_wait_for_capture_result_closes_coroutine_wait_method() -> None:
    assert _wait_for_capture_result(_AsyncFutureLikeCapture(), completion_frames=30) is True


def test_open_stage_waits_for_get_stage_loading_status(monkeypatch) -> None:
    stage = object()

    class _FakeApp:
        def __init__(self) -> None:
            self.updates = 0

        def update(self) -> None:
            self.updates += 1

    class _FakeContext:
        def __init__(self) -> None:
            self.status_calls = 0

        def open_stage(self, usd_path: str) -> bool:
            assert usd_path == "/tmp/scene.usd"
            return True

        def get_stage_loading_status(self):
            self.status_calls += 1
            if self.status_calls <= 3:
                return (0, 0, 1)
            return (0, 0, 0)

        def get_stage(self):
            return stage

    ctx = _FakeContext()
    omni_module = types.ModuleType("omni")
    usd_module = types.ModuleType("omni.usd")
    usd_module.get_context = lambda: ctx
    omni_module.usd = usd_module
    monkeypatch.setitem(sys.modules, "omni", omni_module)
    monkeypatch.setitem(sys.modules, "omni.usd", usd_module)

    app = _FakeApp()

    assert open_stage(app, "/tmp/scene.usd", max_wait_frames=5) is stage
    assert app.updates == 3
