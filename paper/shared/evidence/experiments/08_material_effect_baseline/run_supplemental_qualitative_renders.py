#!/usr/bin/env python3
"""Run supplemental material-effect qualitative render commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
DEFAULT_MANIFEST = RAW_DIR / "supplemental_qualitative_render_manifest.json"
DEFAULT_LOG_ROOT = RAW_DIR / "supplemental_qualitative_render_logs"
DEFAULT_OUTPUT = RAW_DIR / "supplemental_qualitative_render_run_manifest.json"
DEFAULT_TIMEOUT_SECONDS = 900


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "unknown"


def _git_status_porcelain() -> list[str]:
    try:
        tracked_output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        untracked_output = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    lines = [line for line in tracked_output.splitlines() if line]
    untracked_count = len([line for line in untracked_output.splitlines() if line])
    if untracked_count:
        lines.append(f"?? {untracked_count} untracked files omitted from provenance")
    return lines


def _safe_log_part(value: Any) -> str:
    return str(value or "unknown").replace("/", "_").replace(" ", "_")


def _log_summary(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    return {
        "path": str(path),
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "hash_sha256": _sha256_file(path) if path.exists() else None,
        "contains_saved_frame": "Saved frame" in text or "Saved image" in text,
        "contains_traceback": "Traceback" in text,
    }


def _normalize_text_log(path: Path) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line.rstrip() for line in text.splitlines()]
    normalized = ("\n".join(lines).rstrip() + "\n") if lines else ""
    if normalized != text:
        path.write_text(normalized, encoding="utf-8")


def _render_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return list(manifest.get("records") or [])


def run_supplemental_qualitative_renders(
    manifest: dict[str, Any],
    *,
    log_root: Path,
    force: bool = False,
    runner: Callable[..., Any] = subprocess.run,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    log_root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    attempted = 0
    skipped = 0
    failed = 0
    ready = 0
    missing_source = 0
    for record in _render_records(manifest):
        sample_id = str(record.get("sample_id") or "")
        condition = str(record.get("condition") or "")
        image_path = Path(str((record.get("image") or {}).get("path") or ""))
        stdout_path = log_root / f"{_safe_log_part(sample_id)}.{_safe_log_part(condition)}.stdout.txt"
        stderr_path = log_root / f"{_safe_log_part(sample_id)}.{_safe_log_part(condition)}.stderr.txt"
        source_exists = bool(record.get("usd_exists"))
        output_preexisted = image_path.is_file()
        if output_preexisted and not force:
            _normalize_text_log(stdout_path)
            _normalize_text_log(stderr_path)
            skipped += 1
            ready += 1
            records.append(
                {
                    "sample_id": sample_id,
                    "condition": condition,
                    "status": "skipped_existing",
                    "exit_code": None,
                    "output_image": str(image_path),
                    "output_exists": True,
                    "output_hash_sha256": _sha256_file(image_path),
                    "stdout_summary": _log_summary(stdout_path),
                    "stderr_summary": _log_summary(stderr_path),
                }
            )
            continue
        if not source_exists:
            _normalize_text_log(stdout_path)
            _normalize_text_log(stderr_path)
            missing_source += 1
            failed += 1
            records.append(
                {
                    "sample_id": sample_id,
                    "condition": condition,
                    "status": "source_missing",
                    "exit_code": None,
                    "output_image": str(image_path),
                    "output_exists": False,
                    "output_hash_sha256": None,
                    "stdout_summary": _log_summary(stdout_path),
                    "stderr_summary": _log_summary(stderr_path),
                }
            )
            continue

        attempted += 1
        image_path.parent.mkdir(parents=True, exist_ok=True)
        command = [str(item) for item in record.get("render_command") or []]
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            completed = runner(
                command,
                cwd=str(PROJECT_ROOT),
                stdout=stdout,
                stderr=stderr,
                text=True,
                timeout=int(timeout_seconds),
            )
        _normalize_text_log(stdout_path)
        _normalize_text_log(stderr_path)
        output_exists = image_path.is_file()
        exit_code = int(completed.returncode)
        if output_exists and exit_code == 0:
            ready += 1
            status = "rendered"
        else:
            failed += 1
            status = "failed"
        records.append(
            {
                "sample_id": sample_id,
                "condition": condition,
                "status": status,
                "exit_code": exit_code,
                "render_command": command,
                "output_image": str(image_path),
                "output_exists": output_exists,
                "output_hash_sha256": _sha256_file(image_path) if output_exists else None,
                "stdout_summary": _log_summary(stdout_path),
                "stderr_summary": _log_summary(stderr_path),
            }
        )

    return {
        "schema_version": 1,
        "status": "supplemental_material_effect_qualitative_render_run",
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/run_supplemental_qualitative_renders.py",
        "summary": {
            "render_record_count": len(_render_records(manifest)),
            "attempted_count": attempted,
            "skipped_existing_count": skipped,
            "failed_count": failed,
            "ready_output_count": ready,
            "missing_source_count": missing_source,
            "force": bool(force),
            "all_outputs_ready": ready == len(_render_records(manifest)) and failed == 0,
        },
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    manifest = _load_json(args.manifest)
    result = run_supplemental_qualitative_renders(
        manifest,
        log_root=args.log_root,
        force=args.force,
        timeout_seconds=args.timeout_seconds,
    )
    result["inputs"] = {
        "manifest": {"path": str(args.manifest), "hash_sha256": _sha256_file(args.manifest)},
    }
    result["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} attempted={result['summary']['attempted_count']} "
        f"skipped={result['summary']['skipped_existing_count']} "
        f"ready={result['summary']['ready_output_count']} failed={result['summary']['failed_count']}"
    )
    return 0 if result["summary"]["all_outputs_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
