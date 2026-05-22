#!/usr/bin/env python3
"""Plan full GRScenes USD composition closure and recursive no-MDL outputs.

This script is read-only. It consumes `full_nomdl_scratch_plan.json`, scans the
authored USD composition dependency graph, maps source dependencies to the
planned scratch tree, and reports the recursive `_noMDL` write set that a
shared Processor would produce later. It does not copy, hardlink, convert,
render, or write into the source/scratch asset roots.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper" / "shared" / "evidence" / "raw" / "grscene_vlm_grounding"
DEFAULT_PLAN = RAW_DIR / "full_nomdl_scratch_plan.json"
DEFAULT_OUTPUT = RAW_DIR / "full_dependency_closure_report.json"
DEFAULT_MAX_REPORT_RECORDS = 2000
USD_EXTENSIONS = {".usd", ".usda", ".usdc", ".usdz"}
RESOURCE_NAMES = ("models", "Materials")
SCAN_MISSING_BLOCKERS = {
    "whole_scene_dependency_closure_not_scanned",
    "recursive_nomdl_output_collision_scan_missing",
}
SOURCE_RUNNER_MISSING_BLOCKER = "single_process_multi_root_runner_missing"
RUNNER_CLOSURE_REPORT_NOT_CONSUMED_BLOCKER = "single_process_multi_root_runner_closure_report_not_consumed"
TIMESTAMP_PATTERN_EXTENSIONS = (".usd", ".usda", ".usdc", ".usdz")

DependencyProvider = Callable[[Path], list[dict[str, Any]]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_maybe_missing(path: Path) -> Path:
    return path.resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        _resolve_maybe_missing(path).relative_to(_resolve_maybe_missing(parent))
    except ValueError:
        return False
    return True


def _relative_to(path: Path, parent: Path) -> str:
    return _resolve_maybe_missing(path).relative_to(_resolve_maybe_missing(parent)).as_posix()


def _assert_root_safety(source_root: Path, scratch_root: Path) -> tuple[Path, Path]:
    source_root = source_root.resolve()
    scratch_root = _resolve_maybe_missing(scratch_root)
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")
    return source_root, scratch_root


def _plan_roots(plan: dict[str, Any]) -> tuple[Path, Path]:
    source_root = Path(str(plan.get("source_root") or ""))
    scratch_root = Path(str(plan.get("scratch_root") or ""))
    if not str(source_root) or not str(scratch_root):
        raise ValueError("plan must define source_root and scratch_root")
    return _assert_root_safety(source_root, scratch_root)


def validate_output_path(output_path: Path, *, plan: dict[str, Any]) -> Path:
    source_root, scratch_root = _plan_roots(plan)
    output_path = _resolve_maybe_missing(output_path)
    if _is_relative_to(output_path, source_root):
        raise ValueError("output path must not be inside source_root")
    if _is_relative_to(output_path, scratch_root):
        raise ValueError("output path must not be inside scratch_root")
    return output_path


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _closure_plan_blockers(plan_blockers: Iterable[str]) -> list[str]:
    blockers: list[str] = []
    for blocker in plan_blockers:
        if blocker == SOURCE_RUNNER_MISSING_BLOCKER:
            blockers.append(RUNNER_CLOSURE_REPORT_NOT_CONSUMED_BLOCKER)
        else:
            blockers.append(blocker)
    return _dedupe_preserve_order(blockers)


def _limit_records(records: list[Any], max_records: int | None) -> list[Any]:
    if max_records is None or max_records < 0:
        return records
    return records[:max_records]


def _sidecar_path(path: Path) -> Path:
    suffix = path.suffix or ".usd"
    return path.with_name(f"{path.stem}_noMDL{suffix}")


def _timestamped_siblings(expected_output: Path) -> list[str]:
    parent = expected_output.parent
    if not parent.exists():
        return []
    siblings: list[str] = []
    for ext in TIMESTAMP_PATTERN_EXTENSIONS:
        pattern = f"{expected_output.stem}_*{ext}"
        siblings.extend(str(path) for path in parent.glob(pattern) if path.name != expected_output.name)
    return sorted(set(siblings))


def _source_to_scratch(path: Path, *, source_root: Path, scratch_root: Path) -> Path:
    resolved = _resolve_maybe_missing(path)
    if not _is_relative_to(resolved, source_root):
        raise ValueError(f"path must be inside source_root: {path}")
    return _resolve_maybe_missing(scratch_root / resolved.relative_to(source_root))


def _selected_jobs(plan: dict[str, Any], *, limit_jobs: int | None = None) -> list[dict[str, Any]]:
    jobs = list(plan.get("conversion_jobs") or [])
    if limit_jobs is not None:
        if limit_jobs < 0:
            raise ValueError("limit_jobs must be non-negative")
        jobs = jobs[:limit_jobs]
    return jobs


def _validate_job(job: dict[str, Any], *, source_root: Path, scratch_root: Path) -> dict[str, Any]:
    source_usd = _resolve_maybe_missing(Path(str(job.get("source_usd") or "")))
    scratch_input = _resolve_maybe_missing(Path(str(job.get("scratch_input_usd") or "")))
    expected_top_output = _resolve_maybe_missing(Path(str(job.get("expected_top_output_usd") or "")))
    if not _is_relative_to(source_usd, source_root):
        raise ValueError(f"source_usd must be inside source_root: {source_usd}")
    if not _is_relative_to(scratch_input, scratch_root):
        raise ValueError(f"scratch_input_usd must be inside scratch_root: {scratch_input}")
    if not _is_relative_to(expected_top_output, scratch_root):
        raise ValueError(f"expected_top_output_usd must be inside scratch_root: {expected_top_output}")
    return {
        **job,
        "source_usd": str(source_usd),
        "scratch_input_usd": str(scratch_input),
        "expected_top_output_usd": str(expected_top_output),
        "source_usd_exists": source_usd.exists(),
        "scratch_input_exists": scratch_input.exists(),
    }


def _split_root_for_path(path: Path, *, source_root: Path) -> Path | None:
    resolved = _resolve_maybe_missing(path)
    grscenes_root = source_root / "scenes" / "GRScenes-100"
    if not _is_relative_to(resolved, grscenes_root):
        return None
    relative_parts = resolved.relative_to(grscenes_root).parts
    if not relative_parts:
        return None
    return _resolve_maybe_missing(grscenes_root / relative_parts[0])


def _asset_ref_to_candidate(asset_path: str, *, layer_dir: Path) -> Path | None:
    text = asset_path.strip()
    if not text or "://" in text or text.startswith("anon:"):
        return None
    path = Path(text)
    if path.is_absolute():
        return _resolve_maybe_missing(path)
    return _resolve_maybe_missing(layer_dir / path)


def _split_resource_candidate(asset_path: str, *, layer_dir: Path, source_root: Path) -> Path | None:
    text = asset_path.strip()
    if not text or Path(text).is_absolute():
        return None
    normalized = Path(text)
    parts = normalized.parts
    if not parts or parts[0] not in RESOURCE_NAMES:
        return None
    split_root = _split_root_for_path(layer_dir, source_root=source_root)
    if split_root is None:
        return None
    return _resolve_maybe_missing(split_root / normalized)


def _dependency_kind_from_path(path: Path) -> str:
    return "usd" if path.suffix.lower() in USD_EXTENSIONS else "asset"


def _dependency_record_key(record: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(record.get("declaring_layer") or ""),
        str(record.get("kind") or ""),
        str(record.get("asset_path") or ""),
        str(record.get("prim_path") or ""),
    )


def _resolve_dependency_record(
    record: dict[str, Any],
    *,
    source_root: Path,
) -> dict[str, Any]:
    layer_dir = _resolve_maybe_missing(Path(str(record.get("layer_dir") or "")))
    asset_path = str(record.get("asset_path") or "")
    candidate = _asset_ref_to_candidate(asset_path, layer_dir=layer_dir)
    if candidate is None:
        return {
            **record,
            "resolution_status": "ignored_non_filesystem_asset_ref",
            "dependency_kind": "ignored",
        }

    recovered = _split_resource_candidate(asset_path, layer_dir=layer_dir, source_root=source_root)
    if candidate.exists():
        resolved = _resolve_maybe_missing(candidate)
        if not _is_relative_to(resolved, source_root):
            return {
                **record,
                "computed_asset_path": str(candidate),
                "resolved_path": str(resolved),
                "resolution_status": "outside_source_root",
                "dependency_kind": _dependency_kind_from_path(resolved),
            }
        return {
            **record,
            "computed_asset_path": str(candidate),
            "source_path": str(resolved),
            "source_relative_path": _relative_to(resolved, source_root),
            "resolution_status": "resolved",
            "dependency_kind": _dependency_kind_from_path(resolved),
        }

    if recovered is not None and recovered.exists():
        return {
            **record,
            "computed_asset_path": str(candidate),
            "source_path": str(recovered),
            "source_relative_path": _relative_to(recovered, source_root),
            "resolution_status": "recovered_split_resource",
            "dependency_kind": _dependency_kind_from_path(recovered),
        }

    missing_path = recovered or candidate
    status = "missing_recovered_split_resource" if recovered is not None else "missing"
    return {
        **record,
        "computed_asset_path": str(candidate),
        "missing_path": str(missing_path),
        "missing_relative_path": _relative_to(missing_path, source_root)
        if _is_relative_to(missing_path, source_root)
        else None,
        "resolution_status": status,
        "dependency_kind": _dependency_kind_from_path(missing_path),
    }


def _listop_items(listop: Any) -> list[Any]:
    if not listop:
        return []
    items: list[Any] = []
    for name in ("explicitItems", "addedItems", "prependedItems", "appendedItems"):
        items.extend(list(getattr(listop, name, []) or []))
    for name in ("GetExplicitItems", "GetAddedItems", "GetPrependedItems", "GetAppendedItems"):
        if hasattr(listop, name):
            items.extend(list(getattr(listop, name)() or []))
    return items


def _variant_prim_specs(pspec: Any) -> list[Any]:
    specs: list[Any] = []
    try:
        variant_sets = getattr(pspec, "variantSets", {}) or {}
        values = variant_sets.values() if hasattr(variant_sets, "values") else []
        for variant_set in values:
            variants = getattr(variant_set, "variants", {}) or {}
            variant_values = variants.values() if hasattr(variants, "values") else []
            for variant in variant_values:
                variant_pspec = getattr(variant, "primSpec", None)
                if variant_pspec is not None:
                    specs.append(variant_pspec)
    except Exception:
        return specs
    return specs


def _clip_asset_records(pspec: Any, *, layer_path: Path, layer_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        if not pspec.HasInfo("clips"):
            return records
        clips = pspec.GetInfo("clips")
    except Exception:
        return records
    if not isinstance(clips, dict):
        return records
    clip_asset_paths = clips.get("clipAssetPaths")
    if isinstance(clip_asset_paths, list):
        for asset_path in clip_asset_paths:
            records.append(
                {
                    "kind": "clip_asset",
                    "declaring_layer": str(layer_path),
                    "layer_dir": str(layer_dir),
                    "asset_path": str(asset_path),
                    "prim_path": str(getattr(pspec, "path", "")),
                }
            )
    manifest = clips.get("manifestAssetPath")
    if manifest:
        records.append(
            {
                "kind": "clip_manifest",
                "declaring_layer": str(layer_path),
                "layer_dir": str(layer_dir),
                "asset_path": str(manifest),
                "prim_path": str(getattr(pspec, "path", "")),
            }
        )
    return records


def _scan_sdf_dependency_records(layer_path: Path) -> list[dict[str, Any]]:
    # Lazy import keeps normal tests and module import independent of Isaac/PXR.
    from pxr import Sdf  # type: ignore

    resolved_layer_path = _resolve_maybe_missing(layer_path)
    layer = Sdf.Layer.FindOrOpen(str(resolved_layer_path))
    if not layer:
        return []
    identifier = str(getattr(layer, "realPath", None) or getattr(layer, "identifier", resolved_layer_path))
    layer_file = _resolve_maybe_missing(Path(identifier))
    layer_dir = layer_file.parent
    records: list[dict[str, Any]] = []

    # This C++ helper is much faster than Python-recursing every PrimSpec in
    # large GRScenes root layers, and it covers composition arcs authored in the
    # layer. Keep the slower helpers above available for future targeted
    # diagnostics, but use the Sdf production path here.
    for asset_path in layer.GetCompositionAssetDependencies():
        records.append(
            {
                "kind": "composition_dependency",
                "declaring_layer": str(layer_file),
                "layer_dir": str(layer_dir),
                "asset_path": str(asset_path),
                "prim_path": None,
            }
        )

    return records


def _provider_from_records(records_by_layer: dict[str, list[dict[str, Any]]]) -> DependencyProvider:
    normalized = {
        str(_resolve_maybe_missing(Path(layer_path))): records
        for layer_path, records in records_by_layer.items()
    }

    def provider(layer_path: Path) -> list[dict[str, Any]]:
        return list(normalized.get(str(_resolve_maybe_missing(layer_path)), []))

    return provider


def _provider_for_backend(backend: str, records_by_layer: dict[str, list[dict[str, Any]]] | None) -> DependencyProvider:
    if records_by_layer is not None:
        return _provider_from_records(records_by_layer)
    if backend == "sdf":
        return _scan_sdf_dependency_records
    raise ValueError(f"unsupported dependency backend without injected records: {backend}")


def _collect_closure(
    *,
    jobs: list[dict[str, Any]],
    source_root: Path,
    dependency_provider: DependencyProvider,
    max_usd_layers: int | None = None,
    progress_every: int | None = None,
) -> dict[str, Any]:
    root_paths = [_resolve_maybe_missing(Path(str(job["source_usd"]))) for job in jobs]
    root_sources = {str(path) for path in root_paths}
    queue: deque[Path] = deque()
    queued_usd: set[str] = set()
    duplicate_usd_dependency_enqueue_count = 0
    for root_path in root_paths:
        root_key = str(root_path)
        if root_key in queued_usd:
            duplicate_usd_dependency_enqueue_count += 1
            continue
        queued_usd.add(root_key)
        queue.append(root_path)
    unique_usd_enqueue_count = len(queued_usd)
    max_usd_queue_depth = len(queue)
    visited_usd: set[str] = set()
    reachable_usds: dict[str, dict[str, Any]] = {}
    resolved_dependencies: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    missing_dependencies: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    outside_dependencies: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    ignored_dependency_count = 0
    direct_scan_counts: dict[str, int] = {}
    scan_truncated = False
    unscanned_usd_queue: list[str] = []

    while queue:
        current = _resolve_maybe_missing(queue.popleft())
        current_key = str(current)
        if current_key in visited_usd:
            continue
        if max_usd_layers is not None and len(visited_usd) >= max_usd_layers:
            scan_truncated = True
            unscanned_usd_queue = [current_key, *[str(_resolve_maybe_missing(path)) for path in queue]]
            break
        visited_usd.add(current_key)
        if progress_every and len(visited_usd) % progress_every == 0:
            print(
                f"[dependency-closure] scanned_usd_layers={len(visited_usd)} "
                f"queue_depth={len(queue)} unique_enqueued={unique_usd_enqueue_count} "
                f"duplicate_enqueues={duplicate_usd_dependency_enqueue_count}",
                file=sys.stderr,
                flush=True,
            )
        reachable_usds[current_key] = {
            "source_usd": current_key,
            "source_relative_path": _relative_to(current, source_root),
            "is_root_input": current_key in root_sources,
            "source_exists": current.exists(),
        }
        if not current.exists():
            missing_dependencies.setdefault(
                ("root", current_key, current_key, ""),
                {
                    "kind": "root_input",
                    "asset_path": current_key,
                    "missing_path": current_key,
                    "resolution_status": "missing_root_usd",
                    "dependency_kind": "usd",
                },
            )
            continue

        direct_records = dependency_provider(current)
        direct_scan_counts[current_key] = len(direct_records)
        for record in direct_records:
            resolved = _resolve_dependency_record(record, source_root=source_root)
            status = str(resolved.get("resolution_status") or "")
            if status == "ignored_non_filesystem_asset_ref":
                ignored_dependency_count += 1
                continue
            key = _dependency_record_key(resolved)
            if status == "outside_source_root":
                outside_dependencies.setdefault(key, resolved)
                continue
            if status.startswith("missing"):
                missing_dependencies.setdefault(key, resolved)
                continue
            resolved_dependencies.setdefault(key, resolved)
            if resolved.get("dependency_kind") == "usd":
                child = _resolve_maybe_missing(Path(str(resolved["source_path"])))
                child_key = str(child)
                if child_key in visited_usd or child_key in queued_usd:
                    duplicate_usd_dependency_enqueue_count += 1
                else:
                    queued_usd.add(child_key)
                    queue.append(child)
                    unique_usd_enqueue_count += 1
                    max_usd_queue_depth = max(max_usd_queue_depth, len(queue))

    return {
        "reachable_usds": sorted(reachable_usds.values(), key=lambda item: item["source_usd"]),
        "resolved_dependencies": sorted(resolved_dependencies.values(), key=lambda item: (item.get("source_path", ""), item.get("asset_path", ""))),
        "missing_dependencies": sorted(missing_dependencies.values(), key=lambda item: item.get("missing_path", "")),
        "outside_dependencies": sorted(outside_dependencies.values(), key=lambda item: item.get("resolved_path", "")),
        "ignored_dependency_count": ignored_dependency_count,
        "direct_scan_counts": direct_scan_counts,
        "unique_usd_enqueue_count": unique_usd_enqueue_count,
        "duplicate_usd_dependency_enqueue_count": duplicate_usd_dependency_enqueue_count,
        "max_usd_queue_depth": max_usd_queue_depth,
        "scan_truncated": scan_truncated,
        "unscanned_usd_queue": sorted(set(unscanned_usd_queue)),
    }


def _expected_output_record(source_usd: Path, *, source_root: Path, scratch_root: Path) -> dict[str, Any]:
    scratch_input = _source_to_scratch(source_usd, source_root=source_root, scratch_root=scratch_root)
    expected_output = _sidecar_path(scratch_input)
    timestamped = _timestamped_siblings(expected_output)
    return {
        "source_usd": str(_resolve_maybe_missing(source_usd)),
        "source_relative_path": _relative_to(source_usd, source_root),
        "scratch_input_usd": str(scratch_input),
        "expected_output_usd": str(expected_output),
        "scratch_input_exists": scratch_input.exists(),
        "expected_output_exists": expected_output.exists(),
        "timestamped_output_siblings": timestamped,
    }


def _build_output_scan(
    *,
    reachable_usds: list[dict[str, Any]],
    root_source_paths: set[str],
    source_root: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    records = [
        _expected_output_record(Path(str(item["source_usd"])), source_root=source_root, scratch_root=scratch_root)
        for item in reachable_usds
        if item.get("source_exists")
    ]
    output_counts = Counter(record["expected_output_usd"] for record in records)
    duplicate_outputs = sorted(path for path, count in output_counts.items() for _ in range(max(0, count - 1)))
    existing_outputs = sorted(record["expected_output_usd"] for record in records if record["expected_output_exists"])
    timestamped_outputs = sorted(
        sibling for record in records for sibling in record["timestamped_output_siblings"]
    )
    top_outputs = [record for record in records if record["source_usd"] in root_source_paths]
    recursive_outputs = [record for record in records if record["source_usd"] not in root_source_paths]
    return {
        "all_expected_outputs": records,
        "expected_top_outputs": top_outputs,
        "expected_recursive_outputs": recursive_outputs,
        "existing_expected_outputs": existing_outputs,
        "existing_timestamped_outputs": timestamped_outputs,
        "duplicate_expected_outputs": duplicate_outputs,
        "collision_count": len(existing_outputs) + len(timestamped_outputs) + len(duplicate_outputs),
    }


def build_full_dependency_closure_report(
    plan: dict[str, Any],
    *,
    dependency_records_by_layer: dict[str, list[dict[str, Any]]] | None = None,
    dependency_backend: str = "sdf",
    limit_jobs: int | None = None,
    max_usd_layers: int | None = None,
    max_report_records: int | None = DEFAULT_MAX_REPORT_RECORDS,
    progress_every: int | None = None,
) -> dict[str, Any]:
    """Build a read-only full-scene dependency/output closure report."""

    if plan.get("status") != "planned_full_grscenes_nomdl_scratch":
        raise ValueError("plan status must be planned_full_grscenes_nomdl_scratch")
    source_root, scratch_root = _plan_roots(plan)
    jobs = [_validate_job(job, source_root=source_root, scratch_root=scratch_root) for job in _selected_jobs(plan, limit_jobs=limit_jobs)]
    provider = _provider_for_backend(dependency_backend, dependency_records_by_layer)
    closure = _collect_closure(
        jobs=jobs,
        source_root=source_root,
        dependency_provider=provider,
        max_usd_layers=max_usd_layers,
        progress_every=progress_every,
    )
    root_source_paths = {job["source_usd"] for job in jobs}
    output_scan = _build_output_scan(
        reachable_usds=closure["reachable_usds"],
        root_source_paths=root_source_paths,
        source_root=source_root,
        scratch_root=scratch_root,
    )
    top_level_scratch_input_missing_count = sum(
        1 for record in output_scan["expected_top_outputs"] if not record["scratch_input_exists"]
    )
    recursive_scratch_input_missing_count = sum(
        1 for record in output_scan["expected_recursive_outputs"] if not record["scratch_input_exists"]
    )
    scratch_input_missing_count = top_level_scratch_input_missing_count + recursive_scratch_input_missing_count

    plan_blockers = _closure_plan_blockers((plan.get("safety") or {}).get("apply_blockers") or [])
    if closure["scan_truncated"]:
        satisfied_blockers: list[str] = []
        remaining_blockers = list(plan_blockers)
        remaining_blockers.append("dependency_closure_scan_truncated")
    else:
        satisfied_blockers = [blocker for blocker in plan_blockers if blocker in SCAN_MISSING_BLOCKERS]
        remaining_blockers = [blocker for blocker in plan_blockers if blocker not in SCAN_MISSING_BLOCKERS]
    if closure["missing_dependencies"]:
        remaining_blockers.append("dependency_closure_has_missing_dependencies")
    if closure["outside_dependencies"]:
        remaining_blockers.append("dependency_closure_has_outside_source_refs")
    if output_scan["collision_count"]:
        remaining_blockers.append("recursive_nomdl_output_collisions_present")
    if not scratch_root.exists():
        remaining_blockers.append("scratch_root_missing")
    if scratch_input_missing_count:
        remaining_blockers.append("scratch_inputs_missing")
    remaining_blockers = _dedupe_preserve_order(remaining_blockers)
    report_jobs = [
        {
            **job,
            "source_plan_blocked_by": list(job.get("blocked_by") or []),
            "blocked_by": list(remaining_blockers),
            "safe_to_execute_now": not remaining_blockers,
        }
        for job in jobs
    ]

    resolved_usd_dependencies = [
        item for item in closure["resolved_dependencies"] if item.get("dependency_kind") == "usd"
    ]
    resolved_non_usd_dependencies = [
        item for item in closure["resolved_dependencies"] if item.get("dependency_kind") != "usd"
    ]
    summary = {
        "conversion_job_count": len(jobs),
        "dependency_backend": dependency_backend if dependency_records_by_layer is None else "injected",
        "reachable_source_usd_count": len(closure["reachable_usds"]),
        "resolved_dependency_count": len(closure["resolved_dependencies"]),
        "resolved_usd_dependency_count": len(resolved_usd_dependencies),
        "resolved_non_usd_dependency_count": len(resolved_non_usd_dependencies),
        "missing_dependency_count": len(closure["missing_dependencies"]),
        "outside_source_root_ref_count": len(closure["outside_dependencies"]),
        "ignored_dependency_count": closure["ignored_dependency_count"],
        "unique_usd_enqueue_count": closure["unique_usd_enqueue_count"],
        "duplicate_usd_dependency_enqueue_count": closure["duplicate_usd_dependency_enqueue_count"],
        "max_usd_queue_depth": closure["max_usd_queue_depth"],
        "expected_output_count": len(output_scan["all_expected_outputs"]),
        "expected_top_output_count": len(output_scan["expected_top_outputs"]),
        "expected_recursive_nomdl_output_count": len(output_scan["expected_recursive_outputs"]),
        "existing_expected_output_count": len(output_scan["existing_expected_outputs"]),
        "existing_timestamped_output_count": len(output_scan["existing_timestamped_outputs"]),
        "duplicate_expected_output_count": len(output_scan["duplicate_expected_outputs"]),
        "output_collision_count": output_scan["collision_count"],
        "scratch_root_exists": scratch_root.exists(),
        "top_level_scratch_input_missing_count": top_level_scratch_input_missing_count,
        "recursive_scratch_input_missing_count": recursive_scratch_input_missing_count,
        "scratch_input_missing_count": scratch_input_missing_count,
        "usd_layer_scan_limit": max_usd_layers,
        "scan_truncated": closure["scan_truncated"],
        "unscanned_usd_queue_count": len(closure["unscanned_usd_queue"]),
        "safe_to_run_multi_root_nomdl": not remaining_blockers,
    }
    reported_resolved_dependencies = _limit_records(closure["resolved_dependencies"], max_report_records)
    reported_missing_dependencies = _limit_records(closure["missing_dependencies"], max_report_records)
    reported_outside_dependencies = _limit_records(closure["outside_dependencies"], max_report_records)
    reported_reachable_usds = _limit_records(closure["reachable_usds"], max_report_records)
    reported_unscanned_queue = _limit_records(closure["unscanned_usd_queue"], max_report_records)
    reported_recursive_outputs = _limit_records(output_scan["expected_recursive_outputs"], max_report_records)
    report_limits = {
        "max_report_records": max_report_records,
        "reachable_source_usds_reported": len(reported_reachable_usds),
        "reachable_source_usds_total": len(closure["reachable_usds"]),
        "resolved_dependencies_reported": len(reported_resolved_dependencies),
        "resolved_dependencies_total": len(closure["resolved_dependencies"]),
        "missing_dependencies_reported": len(reported_missing_dependencies),
        "missing_dependencies_total": len(closure["missing_dependencies"]),
        "outside_source_root_refs_reported": len(reported_outside_dependencies),
        "outside_source_root_refs_total": len(closure["outside_dependencies"]),
        "unscanned_usd_queue_reported": len(reported_unscanned_queue),
        "unscanned_usd_queue_total": len(closure["unscanned_usd_queue"]),
        "expected_recursive_outputs_reported": len(reported_recursive_outputs),
        "expected_recursive_outputs_total": len(output_scan["expected_recursive_outputs"]),
    }
    return {
        "schema_version": 1,
        "status": "planned_full_grscenes_dependency_closure",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_dependency_closure.py",
        "generated_at_utc": _utc_now(),
        "source_plan_status": plan.get("status"),
        "source_plan_generated_at_utc": plan.get("generated_at_utc"),
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "summary": summary,
        "report_limits": report_limits,
        "safety": {
            "source_root_immutable": True,
            "satisfied_apply_blockers": satisfied_blockers,
            "remaining_apply_blockers": remaining_blockers,
            "safe_to_run_multi_root_nomdl": not remaining_blockers,
        },
        "jobs": report_jobs,
        "reachable_source_usds": reported_reachable_usds,
        "resolved_dependencies": reported_resolved_dependencies,
        "missing_dependencies": reported_missing_dependencies,
        "outside_source_root_refs": reported_outside_dependencies,
        "unscanned_usd_queue": reported_unscanned_queue,
        "expected_recursive_nomdl_outputs": reported_recursive_outputs,
        "output_collision_scan": {
            "scan_scope": "all_reachable_source_usds_mapped_to_planned_scratch",
            "expected_top_outputs": output_scan["expected_top_outputs"],
            "existing_expected_outputs": output_scan["existing_expected_outputs"],
            "existing_timestamped_outputs": output_scan["existing_timestamped_outputs"],
            "duplicate_expected_outputs": output_scan["duplicate_expected_outputs"],
        },
        "notes": [
            "This report is read-only and does not convert assets.",
            "Large record lists are capped by report_limits; use summary totals for complete counts.",
            "Scene-local models/Materials references are recovered to the split-level GRScenes resource roots before scratch mapping when they appear as composition dependencies.",
            "The Sdf backend scans authored composition dependencies; material shader and texture asset attributes remain separate material-closure evidence unless they are surfaced as composition arcs.",
            "Recursive outputs are based on ConvertAsset's base *_noMDL sidecar naming; timestamped siblings are conservatively treated as collisions.",
            "This report alone is not permission to run --apply while scratch materialization, scratch cleanliness, and runner closure-report consumption gates remain unresolved.",
        ],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dependency-backend", choices=("sdf",), default="sdf")
    parser.add_argument("--limit-jobs", type=int, default=None)
    parser.add_argument(
        "--max-usd-layers",
        type=int,
        default=0,
        help="Bound recursive USD layer scans; default 0 means no limit",
    )
    parser.add_argument(
        "--max-report-records",
        type=int,
        default=DEFAULT_MAX_REPORT_RECORDS,
        help="Cap large JSON record lists while preserving complete summary counts; use -1 for no cap",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=1000,
        help="Print scan progress to stderr every N visited USD layers; use 0 to disable",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    plan = _load_json(args.plan)
    output_path = validate_output_path(args.out, plan=plan)
    report = build_full_dependency_closure_report(
        plan,
        dependency_backend=args.dependency_backend,
        limit_jobs=args.limit_jobs,
        max_usd_layers=None if args.max_usd_layers == 0 else args.max_usd_layers,
        max_report_records=None if args.max_report_records < 0 else args.max_report_records,
        progress_every=None if args.progress_every == 0 else args.progress_every,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {output_path} with {report['summary']['conversion_job_count']} jobs, "
        f"reachable_usds={report['summary']['reachable_source_usd_count']}, "
        f"missing={report['summary']['missing_dependency_count']}, "
        f"collisions={report['summary']['output_collision_count']}, "
        f"safe_to_run={report['summary']['safe_to_run_multi_root_nomdl']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
