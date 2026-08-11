#!/usr/bin/env python3
"""Build the measured 2000 x 800 x 755 mm LabUtopia table facade/profile."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.asset_application_normalizer.component_facade import (  # noqa: E402
    build_component_facade,
)


def build(source: Path, profile: Path, out: Path) -> tuple[Path, Path]:
    result = build_component_facade(source, out / "facade", profile)
    facade_sha = sha256(result.facade_path.read_bytes()).hexdigest()
    support = {
        "schema_version": "aan.static_support_profile.v1",
        "profile_id": "scientific_workbench.lab001.table.2000x800x755.static_support",
        "revision": "r1",
        "source_binding": {"sha256": facade_sha},
        "asset_entry_prim": "/World/table",
        "collider_policy": "prefer_source_then_proxy",
        "source_collider_prim": None,
        "proxy": {
            "prim_path": "/World/table/__aan_static_support_proxy",
            "center_xyz": [0.0, 0.0, 0.735],
            "size_xyz": [2.0, 0.8, 0.04],
        },
        "support_surface": {
            "top_z": 0.755,
            "x_range": [-1.0, 1.0],
            "y_range": [-0.4, 0.4],
            "edge_band_m": 0.05,
        },
        "physics_material": {
            "prim_path": "/World/table/__aan_static_support_material",
            "static_friction": 0.5,
            "dynamic_friction": 0.5,
            "restitution": 0.0,
            "friction_combine_mode": "max",
            "restitution_combine_mode": "multiply",
            "calibration_status": "provisional_unmeasured",
        },
    }
    support_path = out / "static_support_profile.json"
    support_path.write_text(json.dumps(support, indent=2) + "\n", encoding="utf-8")
    return result.facade_path, support_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    facade, support = build(args.source, args.profile, args.out)
    print(f"facade: {facade}")
    print(f"static support profile: {support}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
