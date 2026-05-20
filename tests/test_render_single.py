import subprocess
import sys
from types import ModuleType
from pathlib import Path

import numpy as np


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


def test_render_single_rejects_nonfinite_bbox_thresholds_before_starting_isaac(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from convert_asset.render.single import run_render_single

    calls: list[str] = []

    class TrackingSimulationApp:
        def __init__(self, *_args, **_kwargs) -> None:
            calls.append("started")

    fake_isaacsim = ModuleType("isaacsim")
    fake_isaacsim.SimulationApp = TrackingSimulationApp
    monkeypatch.setitem(sys.modules, "isaacsim", fake_isaacsim)

    usd_path = tmp_path / "asset.usd"
    usd_path.write_text("#usda 1.0\n", encoding="utf-8")

    for kwargs in (
        {"extent_fallback_ratio": float("nan")},
        {"center_offset_threshold": float("inf")},
    ):
        code = run_render_single(
            usd_path=usd_path,
            output_root=tmp_path / "renders",
            **kwargs,
        )
        assert code == 2

    assert calls == []


def test_render_single_help_exposes_background_and_bbox_controls() -> None:
    output = run_probe(
        "from convert_asset.cli import main\n"
        "try:\n"
        "    main(['render-single', '--help'])\n"
        "except SystemExit:\n"
        "    pass\n"
    )

    assert "--background-color" in output
    assert "--extent-fallback-ratio" in output
    assert "--center-offset-threshold" in output


def test_rgba_to_rgb_uses_configurable_background_color() -> None:
    from convert_asset.render.single import _rgba_to_rgb

    rgba = np.array(
        [
            [
                [200, 100, 50, 255],
                [200, 100, 50, 0],
            ]
        ],
        dtype=np.uint8,
    )

    rgb = _rgba_to_rgb(rgba, background_color=(10, 20, 30))

    assert rgb.tolist() == [[[200, 100, 50], [10, 20, 30]]]


def test_choose_bbox_falls_back_to_mesh_when_authored_center_is_shifted() -> None:
    from convert_asset.render.single import _choose_bbox

    authored = np.array([[100.0, 100.0, 100.0], [101.0, 101.0, 101.0]])
    mesh = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])

    bbox, source = _choose_bbox(
        authored,
        mesh,
        extent_fallback_ratio=5.0,
        center_offset_threshold=1.0,
    )

    np.testing.assert_allclose(bbox, mesh)
    assert source == "mesh_center_offset"


def test_configure_background_zero_alpha_sets_required_rtx_flags() -> None:
    from convert_asset.render.single import _configure_background_zero_alpha

    class FakeSettings:
        def __init__(self) -> None:
            self.values: dict[str, object] = {}

        def set(self, key: str, value: object) -> None:
            self.values[key] = value

    settings = FakeSettings()

    _configure_background_zero_alpha(settings)

    assert settings.values == {
        "/rtx/post/backgroundZeroAlpha/enabled": True,
        "/rtx/post/backgroundZeroAlpha/backgroundComposite": False,
        "/rtx/post/backgroundZeroAlpha/outputAlphaInComposite": True,
        "/app/captureFrame/setAlphaTo1": False,
    }


def test_find_builtin_hdri_uses_isaacsim_extscache(monkeypatch, tmp_path: Path) -> None:
    from convert_asset.render.single import _find_builtin_hdri

    package_dir = tmp_path / "site-packages" / "isaacsim"
    hdri = (
        package_dir
        / "extscache"
        / "omni.kit.widget.material_preview-1.0.16"
        / "data"
        / "photo_studio_01_4k.hdr"
    )
    hdri.parent.mkdir(parents=True)
    hdri.write_bytes(b"fake-hdri")

    fake_isaacsim = ModuleType("isaacsim")
    fake_isaacsim.__file__ = str(package_dir / "__init__.py")
    monkeypatch.setitem(sys.modules, "isaacsim", fake_isaacsim)

    assert _find_builtin_hdri() == str(hdri)


def test_find_builtin_hdri_uses_isaac_sim_root(monkeypatch, tmp_path: Path) -> None:
    from convert_asset.render.single import _find_builtin_hdri

    hdri = (
        tmp_path
        / "extscache"
        / "omni.kit.widget.material_preview-1.0.16"
        / "data"
        / "photo_studio_01_4k.hdr"
    )
    hdri.parent.mkdir(parents=True)
    hdri.write_bytes(b"fake-hdri")
    monkeypatch.setenv("ISAAC_SIM_ROOT", str(tmp_path))
    monkeypatch.delitem(sys.modules, "isaacsim", raising=False)

    assert _find_builtin_hdri() == str(hdri)


def test_mesh_point_bbox_ignores_invisible_mesh() -> None:
    from pxr import Gf, Usd, UsdGeom

    from convert_asset.render.single import _mesh_point_bbox

    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/Root")
    mesh = UsdGeom.Mesh.Define(stage, "/Root/HiddenMesh")
    mesh.CreatePointsAttr([Gf.Vec3f(0, 0, 0), Gf.Vec3f(1, 1, 1)])
    mesh.CreateFaceVertexCountsAttr([3])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 1])
    mesh.MakeInvisible()

    assert _mesh_point_bbox(root.GetPrim()) is None


def test_mesh_point_bbox_ignores_non_default_purpose_mesh() -> None:
    from pxr import Gf, Usd, UsdGeom

    from convert_asset.render.single import _mesh_point_bbox

    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/Root")
    mesh = UsdGeom.Mesh.Define(stage, "/Root/ProxyMesh")
    mesh.CreatePointsAttr([Gf.Vec3f(0, 0, 0), Gf.Vec3f(1, 1, 1)])
    mesh.CreateFaceVertexCountsAttr([3])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 1])
    mesh.CreatePurposeAttr(UsdGeom.Tokens.proxy)

    assert _mesh_point_bbox(root.GetPrim()) is None


def test_mesh_point_bbox_includes_visible_default_boundable() -> None:
    from pxr import Usd, UsdGeom

    from convert_asset.render.single import _mesh_point_bbox

    stage = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(stage, "/Root")
    cube = UsdGeom.Cube.Define(stage, "/Root/Cube")
    cube.CreateSizeAttr(2.0)

    bbox = _mesh_point_bbox(root.GetPrim())

    np.testing.assert_allclose(bbox, [[-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]])
