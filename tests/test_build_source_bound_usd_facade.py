from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from pxr import Usd


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/build_source_bound_usd_facade.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location("source_bound_facade", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_facade_is_package_local_identity_and_preserves_source(tmp_path: Path) -> None:
    source_dir = tmp_path / "producer"
    source_dir.mkdir()
    source = source_dir / "source.usda"
    source.write_text('#usda 1.0\n(defaultPrim="root")\ndef Xform "root" {}\n')
    before = source.read_bytes()

    out = _module().build(
        source=source,
        out=tmp_path / "package",
        entry_name="ExampleAsset",
    )

    assert source.read_bytes() == before
    text = (out / "asset.usd").read_text()
    assert "@deps/source/source.usda@</root>" in text
    assert "@/" not in text
    stage = Usd.Stage.Open(str(out / "asset.usd"))
    assert stage.GetPrimAtPath("/World/ExampleAsset").IsValid()
    manifest = json.loads((out / "evidence/manifest.json").read_text())
    assert manifest["identity_entry_transform"] is True
