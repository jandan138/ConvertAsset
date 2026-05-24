#!/usr/bin/env python3
"""Audit InternNav episodes against the official height-jump filter."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any


DEFAULT_HEIGHT_THRESHOLD = 0.3


def max_adjacent_z_delta(reference_path: list[list[float]]) -> float:
    if len(reference_path) < 2:
        return 0.0
    return max(abs(float(reference_path[index + 1][2]) - float(reference_path[index][2])) for index in range(len(reference_path) - 1))


def instruction_mentions_stair(episode: dict[str, Any]) -> bool:
    instruction = episode.get("instruction", {})
    text = instruction.get("instruction_text", "") if isinstance(instruction, dict) else ""
    return "stair" in text.lower()


def episode_summary(
    episode: dict[str, Any],
    *,
    threshold: float = DEFAULT_HEIGHT_THRESHOLD,
    hang_path_keys: set[str] | None = None,
) -> dict[str, Any]:
    reference_path = episode.get("reference_path") or []
    delta = max_adjacent_z_delta(reference_path)
    trajectory_id = str(episode["trajectory_id"])
    episode_id = int(episode["episode_id"])
    runtime_path_key = f"{trajectory_id}_{episode_id}"
    source = episode.get("source") if isinstance(episode.get("source"), dict) else {}
    mentions_stair = instruction_mentions_stair(episode)
    would_filter_stairs = delta > threshold or (mentions_stair and delta >= threshold)
    return {
        "episode_id": episode_id,
        "trajectory_id": trajectory_id,
        "runtime_path_key": runtime_path_key,
        "scan": episode.get("scan"),
        "instruction_text": (episode.get("instruction") or {}).get("instruction_text"),
        "object_instance_id": source.get("object_instance_id"),
        "reference_path_length": len(reference_path),
        "start_z": float(reference_path[0][2]) if reference_path else None,
        "target_z": float(reference_path[-1][2]) if reference_path else None,
        "max_adjacent_z_delta": delta,
        "instruction_mentions_stair": mentions_stair,
        "would_filter_stairs": would_filter_stairs,
        "is_known_hang": runtime_path_key in (hang_path_keys or set()),
    }


def audit_episodes(
    episodes: list[dict[str, Any]],
    *,
    threshold: float = DEFAULT_HEIGHT_THRESHOLD,
    hang_path_keys: set[str] | None = None,
) -> dict[str, Any]:
    rows = [episode_summary(episode, threshold=threshold, hang_path_keys=hang_path_keys) for episode in episodes]
    rows.sort(key=lambda row: (-float(row["max_adjacent_z_delta"]), str(row["runtime_path_key"])))
    would_filter = [row for row in rows if row["would_filter_stairs"]]
    known_hangs = [row for row in rows if row["is_known_hang"]]
    known_hang_filtered = [row for row in known_hangs if row["would_filter_stairs"]]
    return {
        "height_threshold": threshold,
        "episode_count": len(rows),
        "would_filter_stairs_count": len(would_filter),
        "known_hang_count": len(known_hangs),
        "known_hang_would_filter_stairs_count": len(known_hang_filtered),
        "known_hang_unmatched_count": len(hang_path_keys or set()) - len(known_hangs),
        "known_hang_unmatched_path_keys": sorted((hang_path_keys or set()) - {row["runtime_path_key"] for row in known_hangs}),
        "episodes": rows,
    }


def combined_audit_payload(
    datasets: list[list[dict[str, Any]]],
    *,
    dataset_names: list[str],
    threshold: float = DEFAULT_HEIGHT_THRESHOLD,
    hang_path_keys: set[str] | None = None,
) -> dict[str, Any]:
    if len(datasets) != len(dataset_names):
        raise ValueError("datasets and dataset_names must have the same length")
    hang_path_keys = set(hang_path_keys or set())
    audits = []
    covered_hang_keys: set[str] = set()
    filtered_hang_keys: set[str] = set()
    for dataset, dataset_name in zip(datasets, dataset_names):
        audit = audit_episodes(dataset, threshold=threshold, hang_path_keys=hang_path_keys)
        audit["dataset"] = dataset_name
        for row in audit["episodes"]:
            if row["is_known_hang"]:
                covered_hang_keys.add(row["runtime_path_key"])
                if row["would_filter_stairs"]:
                    filtered_hang_keys.add(row["runtime_path_key"])
        audits.append(audit)
    return {
        "height_threshold": threshold,
        "dataset_count": len(audits),
        "known_hang_count": len(hang_path_keys),
        "known_hang_covered_count": len(covered_hang_keys),
        "known_hang_would_filter_stairs_covered_count": len(filtered_hang_keys),
        "known_hang_unmatched_count": len(hang_path_keys - covered_hang_keys),
        "known_hang_unmatched_path_keys": sorted(hang_path_keys - covered_hang_keys),
        "datasets": audits,
    }


def read_dataset(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    episodes = payload.get("episodes") if isinstance(payload, dict) else payload
    if not isinstance(episodes, list):
        raise ValueError(f"dataset must contain an episodes list: {path}")
    return episodes


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", action="append", type=Path, required=True)
    parser.add_argument("--hang-path-key", action="append", default=[])
    parser.add_argument("--threshold", type=float, default=DEFAULT_HEIGHT_THRESHOLD)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    hang_path_keys = set(args.hang_path_key)
    datasets = [read_dataset(path) for path in args.dataset]
    dataset_names = [str(path) for path in args.dataset]
    if len(datasets) == 1:
        text_payload: dict[str, Any] = audit_episodes(
            datasets[0],
            threshold=args.threshold,
            hang_path_keys=hang_path_keys,
        )
        text_payload["dataset"] = dataset_names[0]
    else:
        text_payload = combined_audit_payload(
            datasets,
            dataset_names=dataset_names,
            threshold=args.threshold,
            hang_path_keys=hang_path_keys,
        )
    text = json.dumps(text_payload, ensure_ascii=True, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
