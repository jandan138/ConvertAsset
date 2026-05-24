#!/usr/bin/env python3
"""Classify InternNav run logs for runtime hangs before paper evidence use."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any


START_RE = re.compile(r"start sampling trajectory_id:\s*(\S+)")
FINISH_RE = re.compile(r"\[(\d+)/(\d+)\].*finish:\s*\[trajectory_id:([^\]]+)\].*\[result:([^\]]+)\]")
TIMESTAMP_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\]")
DEFAULT_STALE_SECONDS = 600


class LogEvent:
    def __init__(
        self,
        *,
        event_type: str,
        line: str,
        sort_key: tuple[str, int],
        trajectory_id: str | None = None,
        finish_index: int | None = None,
        total_path: int | None = None,
        result: str | None = None,
    ) -> None:
        self.event_type = event_type
        self.line = line
        self.sort_key = sort_key
        self.trajectory_id = trajectory_id
        self.finish_index = finish_index
        self.total_path = total_path
        self.result = result


def _event_sort_key(line: str, sequence: int) -> tuple[str, int]:
    match = TIMESTAMP_RE.match(line)
    timestamp = match.group(1) if match else ""
    return (timestamp, sequence)


def _timestamp_key(event: LogEvent) -> str:
    return event.sort_key[0]


def _parse_log_events(log_paths: list[Path]) -> list[LogEvent]:
    events: list[LogEvent] = []
    sequence = 0
    for path in log_paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            sequence += 1
            sort_key = _event_sort_key(line, sequence)
            start_match = START_RE.search(line)
            if start_match:
                events.append(
                    LogEvent(
                        event_type="start",
                        line=line,
                        sort_key=sort_key,
                        trajectory_id=start_match.group(1),
                    )
                )
                continue

            finish_match = FINISH_RE.search(line)
            if finish_match:
                events.append(
                    LogEvent(
                        event_type="finish",
                        line=line,
                        sort_key=sort_key,
                        finish_index=int(finish_match.group(1)),
                        total_path=int(finish_match.group(2)),
                        trajectory_id=finish_match.group(3),
                        result=finish_match.group(4),
                    )
                )
                continue

            if "states switch to WARM UP" in line:
                events.append(LogEvent(event_type="warmup", line=line, sort_key=sort_key))
                continue

            if "Env Reset time:" in line:
                events.append(LogEvent(event_type="env_reset", line=line, sort_key=sort_key))
                continue

            if "now action" in line or "Env Step" in line:
                events.append(LogEvent(event_type="action", line=line, sort_key=sort_key))

    return sorted(events, key=lambda event: event.sort_key)


def _read_result_count(result_path: Path | None, split_name: str | None = None) -> int | None:
    if result_path is None or not result_path.exists():
        return None
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    if split_name is not None:
        metrics = payload.get(split_name)
        return metrics.get("Count") if isinstance(metrics, dict) else None
    for metrics in payload.values():
        if isinstance(metrics, dict) and "Count" in metrics:
            return metrics["Count"]
    return None


def _max_mtime_epoch(paths: list[Path], result_path: Path | None) -> float | None:
    existing_paths = [path for path in paths if path.exists()]
    if result_path is not None and result_path.exists():
        existing_paths.append(result_path)
    if not existing_paths:
        return None
    return max(path.stat().st_mtime for path in existing_paths)


def _last_finish(events: list[LogEvent]) -> LogEvent | None:
    finish_events = [event for event in events if event.event_type == "finish"]
    return finish_events[-1] if finish_events else None


def _latest_start(events: list[LogEvent]) -> LogEvent | None:
    start_events = [event for event in events if event.event_type == "start"]
    return start_events[-1] if start_events else None


def _event_line(events: list[LogEvent], event_type: str) -> str | None:
    for event in events:
        if event.event_type == event_type:
            return event.line
    return None


def _base_triage(
    *,
    status: str,
    reason: str,
    trajectory_id: str | None,
    exclude_path_key: str | None,
    last_finish: LogEvent | None,
    result_count: int | None,
    latest_events: list[LogEvent],
    stale_age_seconds: float | None,
    stale_seconds: int,
) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "trajectory_id": trajectory_id,
        "exclude_path_key": exclude_path_key,
        "last_finish_index": last_finish.finish_index if last_finish else None,
        "last_finish_trajectory_id": last_finish.trajectory_id if last_finish else None,
        "result_count": result_count,
        "stale_age_seconds": stale_age_seconds,
        "stale_seconds": stale_seconds,
        "evidence": {
            "saw_warmup_after_latest_start": any(event.event_type == "warmup" for event in latest_events),
            "saw_env_reset_after_latest_start": any(event.event_type == "env_reset" for event in latest_events),
            "saw_action_after_latest_start": any(event.event_type == "action" for event in latest_events),
            "saw_finish_after_latest_start": any(event.event_type == "finish" for event in latest_events),
            "latest_start_line": _event_line(latest_events, "start"),
            "warmup_line": _event_line(latest_events, "warmup"),
            "env_reset_line": _event_line(latest_events, "env_reset"),
            "action_line": _event_line(latest_events, "action"),
            "finish_line": _event_line(latest_events, "finish"),
        },
    }


def triage_run(
    *,
    log_paths: list[Path],
    result_path: Path | None = None,
    split_name: str | None = None,
    now_epoch: float | None = None,
    stale_seconds: int = DEFAULT_STALE_SECONDS,
    log_mtime_epoch: float | None = None,
) -> dict[str, Any]:
    events = _parse_log_events(log_paths)
    result_count = _read_result_count(result_path, split_name)
    latest_start = _latest_start(events)
    last_finish = _last_finish(events)
    now_epoch = time.time() if now_epoch is None else now_epoch
    if log_mtime_epoch is None:
        log_mtime_epoch = _max_mtime_epoch(log_paths, result_path)
    stale_age_seconds = None if log_mtime_epoch is None else max(0.0, now_epoch - log_mtime_epoch)

    if latest_start is None:
        return _base_triage(
            status="unknown",
            reason="no_started_episode_found",
            trajectory_id=None,
            exclude_path_key=None,
            last_finish=last_finish,
            result_count=result_count,
            latest_events=[],
            stale_age_seconds=stale_age_seconds,
            stale_seconds=stale_seconds,
        )

    latest_start_index = events.index(latest_start)
    latest_timestamp = _timestamp_key(latest_start)
    if latest_timestamp:
        latest_events = [
            event
            for index, event in enumerate(events)
            if _timestamp_key(event) >= latest_timestamp or index >= latest_start_index
        ]
    else:
        latest_events = events[latest_start_index:]
    trajectory_id = latest_start.trajectory_id
    finishes_after_start = [
        event
        for event in latest_events
        if event.event_type == "finish" and event.trajectory_id == trajectory_id
    ]
    if finishes_after_start:
        return _base_triage(
            status="terminal",
            reason="latest_episode_has_terminal_finish",
            trajectory_id=trajectory_id,
            exclude_path_key=None,
            last_finish=finishes_after_start[-1],
            result_count=result_count,
            latest_events=latest_events,
            stale_age_seconds=stale_age_seconds,
            stale_seconds=stale_seconds,
        )

    saw_action = any(event.event_type == "action" for event in latest_events)
    if saw_action:
        return _base_triage(
            status="active",
            reason="latest_episode_has_started_actions_or_steps",
            trajectory_id=trajectory_id,
            exclude_path_key=None,
            last_finish=last_finish,
            result_count=result_count,
            latest_events=latest_events,
            stale_age_seconds=stale_age_seconds,
            stale_seconds=stale_seconds,
        )

    saw_warmup = any(event.event_type == "warmup" for event in latest_events)
    saw_env_reset = any(event.event_type == "env_reset" for event in latest_events)
    result_not_advanced = (
        result_count is None
        or last_finish is None
        or last_finish.finish_index is None
        or result_count <= last_finish.finish_index
    )
    stale = stale_age_seconds is not None and stale_age_seconds >= stale_seconds
    if saw_warmup and saw_env_reset and result_not_advanced and stale:
        return _base_triage(
            status="runtime_hang",
            reason="warmup_reset_without_first_action_or_terminal_metric",
            trajectory_id=trajectory_id,
            exclude_path_key=trajectory_id,
            last_finish=last_finish,
            result_count=result_count,
            latest_events=latest_events,
            stale_age_seconds=stale_age_seconds,
            stale_seconds=stale_seconds,
        )

    return _base_triage(
        status="waiting_for_first_action",
        reason="latest_episode_started_but_watchdog_gate_not_met",
        trajectory_id=trajectory_id,
        exclude_path_key=None,
        last_finish=last_finish,
        result_count=result_count,
        latest_events=latest_events,
        stale_age_seconds=stale_age_seconds,
        stale_seconds=stale_seconds,
    )


def discover_log_paths(log_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern in (
        "progress/*.log",
        "common/*.log",
        "stdout_stderr.log",
        "video/*.log",
    ):
        candidates.extend(sorted(log_dir.glob(pattern)))
    return candidates


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", action="append", dest="log_paths", type=Path, default=None)
    parser.add_argument("--log-dir", type=Path, default=None, help="Discover InternNav progress/common/stdout logs under this task log directory.")
    parser.add_argument("--result", type=Path, default=None, help="InternNav result.json path.")
    parser.add_argument("--split-name", default=None, help="Optional result.json split key.")
    parser.add_argument("--stale-seconds", type=int, default=DEFAULT_STALE_SECONDS)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_paths = list(args.log_paths or [])
    if args.log_dir is not None:
        log_paths.extend(discover_log_paths(args.log_dir))
    triage = triage_run(
        log_paths=log_paths,
        result_path=args.result,
        split_name=args.split_name,
        stale_seconds=args.stale_seconds,
    )
    text = json.dumps(triage, ensure_ascii=True, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
