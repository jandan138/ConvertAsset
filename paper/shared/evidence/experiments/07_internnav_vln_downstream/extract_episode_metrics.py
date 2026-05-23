#!/usr/bin/env python3
"""Extract per-episode InternNav metrics from LMDB into JSONL.

The module keeps `lmdb` and `msgpack_numpy` as lazy imports so the pure
normalization helpers remain testable in the repository Python environment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_INFO_KEYS = ("TL", "NE", "osr", "success", "spl", "steps")


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if hasattr(value, "item"):
        value = value.item()
    return float(value)


def _as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if hasattr(value, "item"):
        value = value.item()
    return int(value)


def _non_negative_metric(value: Any) -> float:
    numeric = _as_float(value)
    return 0.0 if numeric < 0.0 else numeric


def record_to_episode_row(*, condition: str, path_key: str, record: dict[str, Any]) -> dict[str, Any]:
    info = record.get("info", {})
    missing = [key for key in EXPECTED_INFO_KEYS if key not in info]
    if missing:
        raise KeyError(f"missing InternNav metric keys: {', '.join(missing)}")
    success = _as_float(info.get("success"))
    failure_reason = record.get("fail_reason") or ("success" if success > 0 else record.get("finish_status", "unknown"))
    return {
        "condition": condition,
        "path_key": path_key,
        "finish_status": str(record.get("finish_status", "unknown")),
        "failure_reason": str(failure_reason),
        "metrics": {
            "TL": _as_float(info.get("TL")),
            "NE": _non_negative_metric(info.get("NE")),
            "OS": _non_negative_metric(info.get("osr")),
            "SR": success,
            "SPL": _as_float(info.get("spl")),
            "steps": _as_int(info.get("steps")),
        },
    }


def read_lmdb_episode_rows(*, condition: str, lmdb_dir: Path) -> list[dict[str, Any]]:
    import lmdb
    import msgpack_numpy

    rows: list[dict[str, Any]] = []
    env = lmdb.open(str(lmdb_dir), readonly=True, lock=False, max_readers=256)
    try:
        with env.begin() as txn:
            cursor = txn.cursor()
            for raw_key, raw_value in cursor:
                key = raw_key.decode("utf-8")
                if key.startswith("timestamp_"):
                    continue
                record = msgpack_numpy.unpackb(raw_value)
                rows.append(record_to_episode_row(condition=condition, path_key=key, record=record))
    finally:
        env.close()
    return sorted(rows, key=lambda row: row["path_key"])


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", required=True, choices=("original", "modified", "converted", "nomdl"))
    parser.add_argument("--lmdb-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_lmdb_episode_rows(condition=args.condition, lmdb_dir=args.lmdb_dir)
    write_jsonl(args.output, rows)
    print(json.dumps({"condition": args.condition, "episode_count": len(rows), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
