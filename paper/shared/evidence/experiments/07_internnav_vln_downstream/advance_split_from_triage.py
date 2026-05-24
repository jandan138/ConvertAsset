#!/usr/bin/env python3
"""Advance an InternNav split from a watchdog runtime-hang triage record."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
PREPARE_SCRIPT = SCRIPT_DIR / "prepare_minipair.py"
PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_PREVIOUS_MANIFEST = (
    PROJECT_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_v10_prep_manifest.json"
)
DEFAULT_TRIAGE = (
    PROJECT_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_v10_runtime_hang_triage.json"
)
DEFAULT_EXCLUSION_REASON = "simulator_hang_reset_warmup_no_terminal_metrics"
VERSION_SUFFIX_RE = re.compile(r"_v(\d+)$")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _next_versioned_name(value: str) -> str:
    match = VERSION_SUFFIX_RE.search(value)
    if not match:
        return f"{value}_v2"
    return f"{value[: match.start()]}_v{int(match.group(1)) + 1}"


def _next_manifest_path(previous_manifest_path: Path, *, previous_split: str, next_split: str) -> Path:
    filename = previous_manifest_path.name
    if previous_split in filename:
        return previous_manifest_path.with_name(filename.replace(previous_split, next_split))
    return previous_manifest_path.with_name(f"{next_split}_prep_manifest.json")


def _next_work_root(previous_work_root: Path) -> Path:
    name = previous_work_root.name
    next_name = _next_versioned_name(name)
    return previous_work_root.with_name(next_name)


def _load_prepare_minipair() -> Callable[..., dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("internnav_vln_prepare_minipair", PREPARE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prepare_minipair.py from {PREPARE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.prepare_minipair


def _merged_excludes(existing: list[str], new_key: str) -> list[str]:
    merged = list(existing)
    if new_key not in merged:
        merged.append(new_key)
    return merged


def _validate_triage(triage: dict[str, Any]) -> str:
    status = triage.get("status")
    if status != "runtime_hang":
        raise ValueError(f"triage status must be status=runtime_hang, got {status!r}")
    exclude_path_key = triage.get("exclude_path_key")
    if not isinstance(exclude_path_key, str) or not exclude_path_key:
        raise ValueError("runtime_hang triage must contain a non-empty exclude_path_key")
    return exclude_path_key


def _triage_source_record(
    triage_path: Path,
    triage: dict[str, Any],
    exclude_path_key: str,
    *,
    already_requested: bool,
) -> dict[str, Any]:
    return {
        "path": str(triage_path.resolve()),
        "hash_sha256": _sha256_file(triage_path),
        "status": triage.get("status"),
        "reason": triage.get("reason"),
        "trajectory_id": triage.get("trajectory_id"),
        "exclude_path_key": exclude_path_key,
        "already_requested": already_requested,
    }


def _validate_manifest_after_prepare(
    manifest: dict[str, Any],
    *,
    previous_excluded_episode_count: int | None,
    already_requested: bool,
) -> None:
    selection = manifest.get("selection", {})
    unmatched = selection.get("unmatched_excluded_path_keys") or []
    if unmatched:
        raise ValueError(f"unmatched_excluded_path_keys must be empty, got {unmatched!r}")
    if previous_excluded_episode_count is None:
        return
    expected = previous_excluded_episode_count + (0 if already_requested else 1)
    actual = selection.get("excluded_episode_count")
    if actual is not None and actual != expected:
        raise ValueError(f"excluded_episode_count expected {expected}, got {actual}")


def advance_from_triage(
    *,
    previous_manifest_path: Path,
    triage_path: Path,
    prepare_func: Callable[..., dict[str, Any]] | None = None,
    next_split_name: str | None = None,
    work_root: Path | None = None,
    repo_manifest_path: Path | None = None,
) -> dict[str, Any]:
    previous_manifest_path = previous_manifest_path.resolve()
    triage_path = triage_path.resolve()
    previous = _read_json(previous_manifest_path)
    triage = _read_json(triage_path)
    exclude_path_key = _validate_triage(triage)

    previous_split = previous["dataset"]["split"]
    next_split_name = next_split_name or _next_versioned_name(previous_split)
    work_root = work_root or _next_work_root(Path(previous["work_root"]))
    repo_manifest_path = repo_manifest_path or _next_manifest_path(
        previous_manifest_path,
        previous_split=previous_split,
        next_split=next_split_name,
    )
    selection = previous.get("selection", {})
    existing_excluded_path_keys = list(selection.get("requested_excluded_path_keys") or [])
    already_requested = exclude_path_key in existing_excluded_path_keys
    excluded_path_keys = _merged_excludes(
        existing_excluded_path_keys,
        exclude_path_key,
    )
    prepare = prepare_func or _load_prepare_minipair()
    manifest = prepare(
        source_root=Path(previous["source"]["grscenes_root"]),
        nomdl_root=Path(previous["source"]["nomdl_work_root"]),
        work_root=work_root,
        repo_manifest_path=repo_manifest_path,
        max_episodes=int(previous["dataset"]["episode_count"]),
        split_name=next_split_name,
        link_mode="symlink",
        scene_ids=previous.get("source", {}).get("requested_scene_ids") or None,
        ready_only=bool(selection.get("ready_only", False)),
        min_scenes=int(selection.get("min_scenes", 0)),
        selection_strategy=selection.get("selection_strategy", "sequential"),
        excluded_path_keys=excluded_path_keys,
        exclusion_reason=DEFAULT_EXCLUSION_REASON,
        supersedes_manifest_path=previous_manifest_path,
        max_reference_z_delta=selection.get("max_reference_z_delta"),
    )
    _validate_manifest_after_prepare(
        manifest,
        previous_excluded_episode_count=selection.get("excluded_episode_count"),
        already_requested=already_requested,
    )
    manifest.setdefault("selection", {})["runtime_triage_source"] = _triage_source_record(
        triage_path,
        triage,
        exclude_path_key,
        already_requested=already_requested,
    )
    _write_json(repo_manifest_path, manifest)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-manifest", type=Path, default=DEFAULT_PREVIOUS_MANIFEST)
    parser.add_argument("--triage", type=Path, default=DEFAULT_TRIAGE)
    parser.add_argument("--next-split-name", default=None)
    parser.add_argument("--work-root", type=Path, default=None)
    parser.add_argument("--repo-manifest-path", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = advance_from_triage(
        previous_manifest_path=args.previous_manifest,
        triage_path=args.triage,
        next_split_name=args.next_split_name,
        work_root=args.work_root,
        repo_manifest_path=args.repo_manifest_path,
    )
    print(
        json.dumps(
            {
                "claim_gate": manifest.get("claim_gate"),
                "dataset": manifest.get("dataset"),
                "selection": {
                    "excluded_episode_count": manifest.get("selection", {}).get("excluded_episode_count"),
                    "replacement_episode_count": manifest.get("selection", {}).get("replacement_episode_count"),
                    "unmatched_excluded_path_keys": manifest.get("selection", {}).get("unmatched_excluded_path_keys"),
                    "runtime_triage_source": manifest.get("selection", {}).get("runtime_triage_source"),
                },
                "work_root": manifest.get("work_root"),
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
