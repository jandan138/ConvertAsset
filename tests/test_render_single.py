import subprocess
import sys
from types import ModuleType
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_probe(code: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def test_cli_import_does_not_load_runtime_modules() -> None:
    output = run_probe(
        "import sys; import convert_asset.cli; "
        "loaded = [name for name in sys.modules "
        "if name == 'pxr' or name == 'omni' or name == 'isaacsim' "
        "or name.startswith(('pxr.', 'omni.', 'isaacsim.'))]; "
        "print(loaded)"
    )
    assert output == "[]"


def test_thumbnails_missing_input_returns_before_runtime_imports() -> None:
    output = run_probe(
        "import sys; from convert_asset.cli import main; "
        "code = main(['thumbnails', '/missing/scene.usd']); "
        "loaded = [name for name in sys.modules "
        "if name == 'pxr' or name == 'omni' or name == 'isaacsim' "
        "or name.startswith(('pxr.', 'omni.', 'isaacsim.'))]; "
        "print(f'code={code} loaded={loaded}')"
    )
    assert output.endswith("code=2 loaded=[]")


def test_render_single_module_import_is_runtime_clean() -> None:
    output = run_probe(
        "import sys; import convert_asset.render.single; "
        "loaded = [name for name in sys.modules "
        "if name == 'pxr' or name == 'omni' or name == 'isaacsim' "
        "or name.startswith(('pxr.', 'omni.', 'isaacsim.'))]; "
        "print(loaded)"
    )
    assert output == "[]"


def test_plan_output_paths_uses_view_names(tmp_path: Path) -> None:
    from convert_asset.render.single import plan_output_paths

    usd_path = tmp_path / "asset.usd"
    usd_path.write_text("#usda 1.0\n", encoding="utf-8")

    planned = plan_output_paths(
        usd_path=usd_path,
        output_root=tmp_path / "renders",
        sample_number=4,
        naming_style="view",
    )

    assert [item.name for item in planned] == [
        "front.png",
        "left.png",
        "back.png",
        "right.png",
    ]
    assert planned[0].parent == tmp_path / "renders" / "asset"


def test_render_single_returns_runtime_error_when_simulation_app_startup_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from convert_asset.render.single import run_render_single

    class FailingSimulationApp:
        def __init__(self, *_args, **_kwargs) -> None:
            raise ValueError("startup failed")

    fake_isaacsim = ModuleType("isaacsim")
    fake_isaacsim.SimulationApp = FailingSimulationApp
    monkeypatch.setitem(sys.modules, "isaacsim", fake_isaacsim)

    usd_path = tmp_path / "asset.usd"
    usd_path.write_text("#usda 1.0\n", encoding="utf-8")

    code = run_render_single(
        usd_path=usd_path,
        output_root=tmp_path / "renders",
    )

    assert code == 3
