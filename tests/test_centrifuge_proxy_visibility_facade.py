from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_centrifuge_proxy_visibility_facade import (
    LEGACY_PROXY_PRIMS,
    PROFILE_REVISION,
    build,
    visibility_overlay_text,
)


def test_overlay_covers_every_legacy_proxy_scope() -> None:
    text = visibility_overlay_text()
    total = sum(len(names) for names in LEGACY_PROXY_PRIMS.values())
    assert total == 15
    assert text.count('token visibility = "invisible"') == total
    for group, names in LEGACY_PROXY_PRIMS.items():
        assert f'over "{group}"' in text
        for name in names:
            assert f'over "{name}"' in text
    # Display-only: no shape/mass/drive content is redefined.
    assert "xformOp" not in text
    assert "PhysicsCollisionAPI" not in text


def test_build_writes_facade_and_rebound_physics(tmp_path: Path) -> None:
    r10_dir = tmp_path / "r10"
    facade_dir = r10_dir / "facade"
    facade_dir.mkdir(parents=True)
    r10_facade = facade_dir / "facade.usda"
    r10_facade.write_text(
        "#usda 1.0\n(\n    defaultPrim = \"World\"\n)\n\ndef Xform \"World\" {}\n",
        encoding="utf-8",
    )
    r10_physics = r10_dir / "centrifuge.physics.json"
    r10_physics.write_text(
        json.dumps(
            {
                "profile_id": "hci955350.centrifuge.physics.cup-colliders-r10",
                "revision": "r3-cup-colliders",
                "source_binding": {"sha256": "e" * 64},
            }
        ),
        encoding="utf-8",
    )
    before = r10_facade.read_bytes()

    result = build(r10_facade=r10_facade, r10_physics=r10_physics, out_root=tmp_path / "r10v2")

    assert r10_facade.read_bytes() == before
    facade_text = result["facade"].read_text(encoding="utf-8")
    assert "subLayers" in facade_text
    physics = json.loads(result["physics"].read_text(encoding="utf-8"))
    assert physics["source_binding"]["sha256"] != "e" * 64
    assert physics["profile_id"].endswith(".proxy-invisible")
    assert ".cup-colliders-r10.cup-colliders-r10" not in physics["profile_id"]
    assert physics["revision"] == PROFILE_REVISION
    provenance = json.loads(result["provenance"].read_text(encoding="utf-8"))
    assert sum(len(v) for v in provenance["visibility_overrides"].values()) == 15
    with pytest.raises(FileExistsError):
        build(r10_facade=r10_facade, r10_physics=r10_physics, out_root=tmp_path / "r10v2")
