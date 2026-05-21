import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/render_with_viewport_capture.py"


def load_render_module():
    spec = importlib.util.spec_from_file_location("render_with_viewport_capture", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeApp:
    def __init__(self, path: Path | None = None, write_on_update: int | None = None):
        self.path = path
        self.write_on_update = write_on_update
        self.update_count = 0

    def update(self) -> None:
        self.update_count += 1
        if self.path and self.write_on_update == self.update_count:
            self.path.write_bytes(b"png")


def test_module_imports_without_isaacsim() -> None:
    module = load_render_module()

    assert hasattr(module, "_wait_for_capture_result")


def test_wait_for_capture_result_awaits_helper_before_checking_file(tmp_path: Path) -> None:
    module = load_render_module()
    out_path = tmp_path / "frame.png"

    class Helper:
        waited = False

        async def wait_for_result(self):
            self.waited = True
            out_path.write_bytes(b"png")

    helper = Helper()

    module._wait_for_capture_result(FakeApp(), helper, str(out_path), max_update_checks=1)

    assert helper.waited is True
    assert out_path.exists()


def test_wait_for_capture_result_uses_app_updates_until_file_exists(tmp_path: Path) -> None:
    module = load_render_module()
    out_path = tmp_path / "frame.png"
    app = FakeApp(out_path, write_on_update=2)

    module._wait_for_capture_result(app, object(), str(out_path), max_update_checks=3)

    assert out_path.exists()
    assert app.update_count == 2
