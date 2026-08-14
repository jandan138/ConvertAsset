#!/usr/bin/env python3
"""Attach a measured batch stage-update baseline without promoting role candidates."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def attach(*, batch: Path, report: Path) -> dict[str, object]:
    batch = batch.resolve()
    report = report.resolve()
    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    evidence = json.loads(report.read_text(encoding="utf-8"))
    manifest["baseline_stage_update"] = {
        "status": evidence.get("overall_status"),
        "required_cold_runs": evidence.get("required_cold_runs"),
        "report": report.relative_to(batch).as_posix(),
        "sha256": _sha(report),
    }
    manifest["overall_status"] = "candidate_role_gates_pending"
    manifest["promotion"] = {
        "allowed": False,
        "reason": "role_specific_runtime_gates_not_run",
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    result = attach(batch=args.batch, report=args.report)
    print(json.dumps(result["promotion"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
