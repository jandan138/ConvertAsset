"""Hash-bound batch admission driver.

Consumes a batch admission request (candidate list with pinned source
SHA-256), verifies every source hash before any processing, runs the AAN
pipeline per candidate, and writes an aggregate summary.  Sources whose
hash does not match are never run.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Callable

import yaml


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_batch_admission(
    request_path: Path,
    out_root: Path,
    *,
    runner: Callable[[dict[str, Any], Path], Any],
    only: set[str] | None = None,
) -> dict[str, Any]:
    """Run a hash-bound batch admission request.

    ``runner`` receives one request item and its output directory and returns
    an object with ``return_code``, ``manifest_path``, and
    ``overall_status`` attributes (the NormalizeAssetResult shape).
    """
    request = yaml.safe_load(Path(request_path).read_text(encoding="utf-8"))
    out_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for item in request.get("items", []):
        candidate_id = item["candidate_id"]
        if only and candidate_id not in only:
            continue
        record: dict[str, Any] = {
            "candidate_id": candidate_id,
            "source_usd": item.get("source_usd"),
            "pinned_sha256": item.get("source_sha256"),
        }
        source = Path(item["source_usd"])
        if not source.is_file():
            record["status"] = "missing_source"
            results.append(record)
            continue
        actual = sha256_file(source)
        record["actual_sha256"] = actual
        record["sha256_match"] = actual == item.get("source_sha256")
        if not record["sha256_match"]:
            record["status"] = "sha256_mismatch"
            results.append(record)
            continue
        started = time.time()
        result = runner(item, out_root / candidate_id)
        record["elapsed_seconds"] = round(time.time() - started, 1)
        record["return_code"] = int(getattr(result, "return_code", 1))
        record["overall_status"] = getattr(result, "overall_status", None)
        manifest_path = getattr(result, "manifest_path", None)
        record["manifest_path"] = str(manifest_path) if manifest_path else None
        record["status"] = "done"
        results.append(record)
    return {
        "request_id": request.get("request_id"),
        "catalog_digest": request.get("catalog_digest"),
        "results": results,
    }
