"""Build M1 Blender 4.4.3 ART-001 Keck clip & calibrated thermometer unit for distillation_v08."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.distillation_v08.blender_v08_taper_joints_and_keck import build_v08_blender_assets  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "external_artifacts" / "distillation_v08_assets")
    parser.add_argument("--cycles-device", type=str, default="CPU")
    args = parser.parse_args()
    manifest = build_v08_blender_assets(args.out_dir, cycles_device=args.cycles_device)
    print(json.dumps({"studio_sheet": manifest["studio_sheet"], "blender": manifest["blender_version"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

