#!/usr/bin/env python3
"""Record a conservative runtime-log observation for a fluid candidate."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from convert_asset.asset_application_normalizer.interactive_fluid_scene import (
    classify_interactive_fluid_runtime_log,
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def finalize_package(package: Path, report_path: Path) -> None:
    """Bind a conservative runtime observation into the immutable package receipt."""

    package = package.resolve()
    report_path = report_path.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest_path = package / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["overall_status"] = report["overall_status"]
    manifest["blocked_reasons"] = report.get("blocked_reasons", [])
    manifest["producer_revision"] = "2026-08-13-task02-fluid-r8-measured-no-go"
    manifest["runtime_qualification"] = {
        "status": report["overall_status"],
        "report": report_path.relative_to(package).as_posix(),
        "sha256": _sha(report_path),
    }
    manifest["closure"] = {
        "files": [
            {"path": path.relative_to(package).as_posix(), "sha256": _sha(path)}
            for path in sorted(candidate for candidate in package.rglob("*") if candidate.is_file())
            if path != manifest_path
        ]
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    payload = classify_interactive_fluid_runtime_log(
        args.log.read_text(encoding="utf-8", errors="replace")
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.package is not None:
        finalize_package(args.package, args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
