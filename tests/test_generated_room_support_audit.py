from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.support_audit import audit_support_relations


def _write_scene(path: Path, *, item_x: float = 0.0) -> None:
    path.write_text(
        f'''#usda 1.0
(
    defaultPrim = "Room"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "Room" {{
    def Cube "Bench" {{
        double size = 1
        double3 xformOp:scale = (1, 1, 0.1)
        double3 xformOp:translate = (0, 0, 0.8)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }}
    def Cube "Bottle" {{
        double size = 1
        double3 xformOp:scale = (0.1, 0.1, 0.2)
        double3 xformOp:translate = ({item_x}, 0, 0.95)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }}
}}
''',
        encoding="utf-8",
    )


def _write_sidecar(path: Path, source: Path, *, source_hash: str | None = None) -> None:
    payload = {
        "schema_version": "room-support-relations-v1",
        "source_usd": {
            "path": source.name,
            "sha256": source_hash or hashlib.sha256(source.read_bytes()).hexdigest(),
        },
        "margin_m": 0.02,
        "vertical_tolerance_m": 0.005,
        "review": {"status": "pass", "reviewer": "producer"},
        "relations": [
            {
                "object_name": "Bottle",
                "object_prim": "/Room/Bottle",
                "support_name": "Bench",
                "support_prim": "/Room/Bench",
                "relation_kind": "rests_on",
                "audit_status": "pass",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_support_audit_passes_and_emits_closure(tmp_path: Path) -> None:
    pytest.importorskip("pxr")
    source = tmp_path / "room.usda"
    sidecar = tmp_path / "support_relations.json"
    _write_scene(source)
    _write_sidecar(sidecar, source)

    report = audit_support_relations(sidecar)

    assert report["overall_status"] == "pass"
    assert report["support_closure"] == {"/Room/Bench": ["/Room/Bottle"]}
    assert report["blocked_reasons"] == []


def test_support_audit_rejects_stale_source_hash(tmp_path: Path) -> None:
    pytest.importorskip("pxr")
    source = tmp_path / "room.usda"
    sidecar = tmp_path / "support_relations.json"
    _write_scene(source)
    _write_sidecar(sidecar, source, source_hash="0" * 64)

    report = audit_support_relations(sidecar)

    assert report["overall_status"] == "blocked"
    assert any("SHA-256" in reason for reason in report["blocked_reasons"])


def test_support_audit_rejects_forged_edge_support(tmp_path: Path) -> None:
    pytest.importorskip("pxr")
    source = tmp_path / "room.usda"
    sidecar = tmp_path / "support_relations.json"
    _write_scene(source, item_x=0.96)
    _write_sidecar(sidecar, source)

    report = audit_support_relations(sidecar)

    assert report["overall_status"] == "blocked"
    assert any("footprint" in reason for reason in report["blocked_reasons"])


def test_support_audit_rejects_missing_sidecar(tmp_path: Path) -> None:
    report = audit_support_relations(tmp_path / "missing.json")

    assert report["overall_status"] == "blocked"
    assert "sidecar is unavailable" in report["blocked_reasons"][0]
