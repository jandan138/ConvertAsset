#!/usr/bin/env python3
"""Extract the pinned producer USD and invoke generic articulated relocation."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.asset_application_normalizer.articulated_relocation import (  # noqa: E402
    normalize_articulated,
)


DEFAULT_ARCHIVE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_xinyu/ika_oven_125_interactive_v3.7z"
)
DEFAULT_PROFILE = (
    REPO_ROOT / "profiles/articulated/ika_oven_125_identity_root.v1.json"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_identity_root_r1_20260831"
ARCHIVE_SHA256 = "c3549ad1ed967e79b5ec3612e04da1acb70479d6528a8a0b144ad93acf379de1"
USD_MEMBER = (
    "ika_oven_125_interactive_v3/ika_oven_125_control_dry_interactive_v3.usd"
)
PHYSICS_SMOKE_MEMBER = (
    "ika_oven_125_interactive_v3/scripts/physics_smoke_oven125_v2.py"
)


def _extract_member(archive: Path, member: str) -> bytes:
    result = subprocess.run(
        ["7z", "x", "-so", str(archive), member],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def build(
    output: Path = DEFAULT_OUTPUT,
    *,
    archive: Path = DEFAULT_ARCHIVE,
    profile: Path = DEFAULT_PROFILE,
) -> Path:
    archive = archive.resolve()
    output = output.resolve()
    if sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("source archive SHA-256 mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    source = output.parent / f".{output.name}.source.usd"
    if source.exists():
        raise FileExistsError(f"refusing to replace extracted source: {source}")
    source.write_bytes(_extract_member(archive, USD_MEMBER))
    try:
        result = normalize_articulated(source, output, profile)
    finally:
        source.unlink(missing_ok=True)
    evidence = output / "package/evidence"
    (evidence / "producer_physics_smoke.py").write_bytes(
        _extract_member(archive, PHYSICS_SMOKE_MEMBER)
    )
    return result.manifest_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    print(build(args.output, archive=args.archive, profile=args.profile))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
