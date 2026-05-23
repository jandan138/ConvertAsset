#!/usr/bin/env python3
"""Collect paired InternNav result.json files into paper evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_PREP_MANIFEST = PROJECT_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/prep_manifest.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json"
METRIC_KEYS = ("TL", "NE", "FR", "StR", "OS", "SR", "SPL", "Count")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _split_metrics(result: dict[str, Any], split: str) -> dict[str, float]:
    if split not in result:
        raise KeyError(f"split not found in result.json: {split}")
    metrics = result[split]
    missing = [key for key in METRIC_KEYS if key not in metrics]
    if missing:
        raise KeyError(f"missing metrics for split {split}: {', '.join(missing)}")
    return {key: float(metrics[key]) for key in METRIC_KEYS}


def _metric_deltas(original: dict[str, float], converted: dict[str, float]) -> dict[str, float]:
    return {key: round(converted[key] - original[key], 10) for key in METRIC_KEYS}


def _path_has_suffix(path: Path, expected_suffix: str) -> bool:
    suffix_parts = Path(expected_suffix).parts
    return len(path.parts) >= len(suffix_parts) and path.parts[-len(suffix_parts) :] == suffix_parts


def _validate_result_paths(prep_manifest: dict[str, Any], original_path: Path, converted_path: Path) -> None:
    expected = prep_manifest.get("internnav_eval_commands", {}).get("expected_result_jsons", [])
    if len(expected) != 2:
        raise ValueError("prep manifest must contain two expected InternNav result paths")
    for label, path, expected_suffix in (
        ("original", original_path, expected[0]),
        ("converted", converted_path, expected[1]),
    ):
        if not _path_has_suffix(path, str(expected_suffix)):
            raise ValueError(
                f"{label} result path does not match expected InternNav result suffix: {expected_suffix}"
            )


def _validate_counts(
    *,
    expected_count: int,
    original_metrics: dict[str, float],
    converted_metrics: dict[str, float],
) -> None:
    for label, metrics in (("original", original_metrics), ("converted", converted_metrics)):
        if metrics["Count"] != float(expected_count):
            raise ValueError(
                f"{label} Count does not match prep manifest episode_count: "
                f"{metrics['Count']} != {expected_count}"
            )


def collect_results(
    *,
    prep_manifest_path: Path,
    original_result_path: Path,
    converted_result_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    prep_manifest_path = prep_manifest_path.resolve()
    original_result_path = original_result_path.resolve()
    converted_result_path = converted_result_path.resolve()
    output_path = output_path.resolve()
    prep_manifest = _load_json(prep_manifest_path)
    split = str(prep_manifest["dataset"]["split"])
    expected_count = int(prep_manifest["dataset"]["episode_count"])
    _validate_result_paths(prep_manifest, original_result_path, converted_result_path)
    original_metrics = _split_metrics(_load_json(original_result_path), split)
    converted_metrics = _split_metrics(_load_json(converted_result_path), split)
    _validate_counts(
        expected_count=expected_count,
        original_metrics=original_metrics,
        converted_metrics=converted_metrics,
    )
    summary = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "claim_boundary": "actual_internnav_metrics_from_supplied_result_jsons",
        "project_git_commit": _git_commit(),
        "prep_manifest": {
            "path": str(prep_manifest_path),
            "hash_sha256": _sha256_file(prep_manifest_path),
        },
        "input_results": {
            "original": {
                "path": str(original_result_path),
                "hash_sha256": _sha256_file(original_result_path),
            },
            "converted": {
                "path": str(converted_result_path),
                "hash_sha256": _sha256_file(converted_result_path),
            },
        },
        "split": split,
        "episode_count": expected_count,
        "scene_records": prep_manifest.get("scene_records", []),
        "metrics": {
            "original": original_metrics,
            "converted": converted_metrics,
        },
        "metric_deltas": _metric_deltas(original_metrics, converted_metrics),
        "interpretation_guardrail": (
            "This file is valid only if the supplied InternNav result.json files "
            "come from the matching prep_manifest original and converted configs."
        ),
    }
    _write_json(output_path, summary)
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prep-manifest", type=Path, default=DEFAULT_PREP_MANIFEST)
    parser.add_argument("--original-result", type=Path, required=True)
    parser.add_argument("--converted-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = collect_results(
        prep_manifest_path=args.prep_manifest,
        original_result_path=args.original_result,
        converted_result_path=args.converted_result,
        output_path=args.output,
    )
    print(json.dumps({"split": summary["split"], "metric_deltas": summary["metric_deltas"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
