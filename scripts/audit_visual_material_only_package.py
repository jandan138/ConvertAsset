#!/usr/bin/env python3
"""Write a visual-only delta audit into an admitted ConvertAsset package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.asset_application_normalizer.visual_material_audit import (
    audit_visual_material_only_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--expected-physics-profile", type=Path, required=True)
    parser.add_argument("--expected-interaction-profile", type=Path, required=True)
    args = parser.parse_args()
    report = audit_visual_material_only_package(
        args.package_dir,
        expected_physics_profile=args.expected_physics_profile,
        expected_interaction_profile=args.expected_interaction_profile,
    )
    output = args.package_dir / "evidence/visual_material_only_audit.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
