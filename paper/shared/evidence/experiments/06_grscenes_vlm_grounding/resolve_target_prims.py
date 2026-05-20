#!/usr/bin/env python3
"""Resolve GRScenes VLM episode targets to USD prims and world bboxes.

This script is read-only with respect to the benchmark source dataset. It opens
source USD stages, matches manifest metadata model paths to authored USD
reference/payload asset paths, computes target world-space bounds, and writes a
separate target manifest for later rendering.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_INPUT = (
    PROJECT_ROOT
    / "paper"
    / "shared"
    / "evidence"
    / "raw"
    / "grscene_vlm_grounding"
    / "source_manifest.json"
)
DEFAULT_OUTPUT = DEFAULT_INPUT.with_name("target_manifest.json")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_status_porcelain() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    return [line for line in output.splitlines() if line]


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


def _normalize_asset_path(path: str) -> str:
    parts: list[str] = []
    for part in str(path).replace("\\", "/").split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts).lower()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def validate_output_path(out_path: Path, manifest: dict[str, Any]) -> None:
    benchmark = (manifest.get("dataset_roles") or {}).get("benchmark_source_dataset") or {}
    source_root_text = benchmark.get("local_root")
    if not source_root_text:
        return
    source_root = Path(source_root_text)
    if _is_relative_to(out_path, source_root):
        raise ValueError("output path must not be inside benchmark source root")


def asset_path_matches_metadata_path(asset_path: str, metadata_path: str) -> bool:
    """Return True when an authored USD asset path points at a metadata model."""

    normalized_asset = _normalize_asset_path(asset_path)
    normalized_metadata = _normalize_asset_path(metadata_path)
    if not normalized_asset or not normalized_metadata:
        return False
    return normalized_asset == normalized_metadata or normalized_asset.endswith(f"/{normalized_metadata}")


def _candidate_matches_metadata(prim_record: dict[str, Any], metadata_paths: list[str]) -> bool:
    asset_paths = [str(path) for path in prim_record.get("asset_paths", [])]
    for asset_path in asset_paths:
        for metadata_path in metadata_paths:
            if asset_path_matches_metadata_path(asset_path, metadata_path):
                return True
    return False


def _prim_suffix_for_episode(episode_record: dict[str, Any]) -> str | None:
    object_instance_id = str(episode_record.get("object_instance_id") or "")
    category, sep, model_instance = object_instance_id.partition("/")
    if not sep or not category or not model_instance:
        return None
    return f"/{category}/{model_instance}".lower()


def _candidate_matches_prim_suffix(prim_record: dict[str, Any], episode_record: dict[str, Any]) -> bool:
    suffix = _prim_suffix_for_episode(episode_record)
    if not suffix:
        return False
    prim_path = str(prim_record.get("prim_path") or "").lower()
    return prim_path.endswith(suffix)


def _stable_candidate_records(prim_records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(prim_records, key=lambda item: str(item.get("prim_path", "")))


def _reference_candidates(
    episode_record: dict[str, Any], prim_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    metadata_paths = [str(path) for path in episode_record.get("metadata_model_paths", [])]
    return _stable_candidate_records(
        record for record in prim_records if _candidate_matches_metadata(record, metadata_paths)
    )


def _suffix_candidates(
    episode_record: dict[str, Any], prim_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return _stable_candidate_records(
        record for record in prim_records if _candidate_matches_prim_suffix(record, episode_record)
    )


def _selected_candidate(
    candidates: list[dict[str, Any]], episode_record: dict[str, Any]
) -> tuple[dict[str, Any] | None, str]:
    exact_suffix = _prim_suffix_for_episode(episode_record)
    if exact_suffix:
        exact_matches = [
            candidate
            for candidate in candidates
            if str(candidate.get("prim_path") or "").lower().endswith(exact_suffix)
        ]
        if len(exact_matches) == 1:
            return exact_matches[0], "high_exact_suffix"
    instance_index = episode_record.get("instance_index")
    if isinstance(instance_index, int):
        if instance_index < 0 or instance_index >= len(candidates):
            return None, "out_of_range"
        selected = candidates[instance_index]
        confidence = "high_single_candidate" if len(candidates) == 1 else "medium_instance_index"
        return selected, confidence
    if len(candidates) == 1:
        return candidates[0], "high_single_candidate"
    return None, "ambiguous"


def resolve_episode_record(episode_record: dict[str, Any], prim_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve one source-manifest episode record against collected USD prim records."""

    metadata_paths = [str(path) for path in episode_record.get("metadata_model_paths", [])]
    base = {
        **episode_record,
        "mapping_method": "metadata_model_path_to_authored_reference",
        "mapping_confidence": "none",
        "target_prim_path": None,
        "candidate_prim_paths": [],
        "candidate_prim_records": [],
        "world_bbox": None,
    }
    if not metadata_paths:
        return {**base, "mapping_status": "unresolved_no_metadata_model_path"}

    candidates = _reference_candidates(episode_record, prim_records)
    mapping_method = "metadata_model_path_to_authored_reference"
    mapping_status = "resolved_metadata_reference_to_prim"
    if not candidates:
        candidates = _suffix_candidates(episode_record, prim_records)
        mapping_method = "prim_suffix_exact"
        mapping_status = "resolved_prim_suffix_to_prim"

    candidate_paths = [str(record["prim_path"]) for record in candidates]
    if not candidates:
        return {**base, "mapping_status": "unresolved_no_matching_prim"}

    selected, confidence = _selected_candidate(candidates, episode_record)
    if selected is None:
        if confidence == "out_of_range":
            return {
                **base,
                "mapping_status": "unresolved_instance_index_out_of_range",
                "candidate_prim_paths": candidate_paths,
                "candidate_prim_records": candidates,
            }
        return {
            **base,
            "mapping_status": "unresolved_ambiguous_prim_candidates",
            "candidate_prim_paths": candidate_paths,
            "candidate_prim_records": candidates,
        }
    if mapping_method == "prim_suffix_exact" and confidence in {"high_single_candidate", "high_exact_suffix"}:
        confidence = "medium"

    return {
        **base,
        "mapping_status": mapping_status,
        "mapping_method": mapping_method,
        "mapping_confidence": confidence,
        "target_prim_path": selected.get("prim_path"),
        "candidate_prim_paths": candidate_paths,
        "candidate_prim_records": candidates,
        "world_bbox": selected.get("world_bbox"),
        "resolved_model_path": selected.get("resolved_model_path"),
        "reference_asset_path": selected.get("reference_asset_path"),
        "bbox_method": selected.get("bbox_method"),
    }


def resolve_model_path(source_root: Path, scene_split: str, metadata_model_path: str) -> Path:
    metadata_path = Path(metadata_model_path)
    if metadata_path.is_absolute():
        return metadata_path.resolve()
    return (Path(source_root) / "scenes" / "GRScenes-100" / scene_split / metadata_path).resolve()


def target_uniqueness_summary(records: list[dict[str, Any]]) -> dict[str, int]:
    keys = [
        (
            str(record.get("source_scene_id")),
            str(record.get("object_instance_id")),
            str(record.get("target_prim_path")),
        )
        for record in records
        if record.get("target_prim_path")
    ]
    unique_keys = set(keys)
    counts: dict[tuple[str, str, str], int] = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    return {
        "unique_target_prim_count": len(unique_keys),
        "duplicate_episode_target_count": len(keys) - len(unique_keys),
        "max_episode_records_per_unique_target": max(counts.values(), default=0),
    }


def _list_op_items(list_op: Any) -> list[Any]:
    if list_op is None:
        return []
    items: list[Any] = []
    for attr in ("explicitItems", "addedItems", "prependedItems", "appendedItems"):
        values = getattr(list_op, attr, None)
        if values:
            items.extend(list(values))
    try:
        values = list_op.GetAddedOrExplicitItems()
        if values:
            items.extend(list(values))
    except Exception:
        pass
    return items


def _asset_paths_from_list_op(list_op: Any) -> list[str]:
    paths = []
    for item in _list_op_items(list_op):
        asset_path = getattr(item, "assetPath", None)
        if asset_path:
            paths.append(str(asset_path))
    return paths


def _authored_asset_paths(prim: Any) -> list[str]:
    paths: list[str] = []
    for metadata_name in ("references", "payload"):
        try:
            paths.extend(_asset_paths_from_list_op(prim.GetMetadata(metadata_name)))
        except Exception:
            pass
    try:
        prim_stack = prim.GetPrimStack()
    except Exception:
        prim_stack = []
    for spec in prim_stack:
        for attr in ("referenceList", "payloadList"):
            try:
                paths.extend(_asset_paths_from_list_op(getattr(spec, attr, None)))
            except Exception:
                pass
    return sorted(set(paths))


def _vec3_to_list(value: Any) -> list[float]:
    return [float(value[0]), float(value[1]), float(value[2])]


def _bbox_dict_from_range(rng: Any) -> dict[str, Any]:
    mn, mx = rng.GetMin(), rng.GetMax()
    center = (mn + mx) * 0.5
    size = mx - mn
    return {
        "min": _vec3_to_list(mn),
        "max": _vec3_to_list(mx),
        "center": _vec3_to_list(center),
        "size": _vec3_to_list(size),
        "diagonal": float(size.GetLength()),
    }


def _range_is_sane(rng: Any) -> bool:
    if rng.IsEmpty():
        return False
    mn, mx = rng.GetMin(), rng.GetMax()
    vals = [mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]]
    if not all(math.isfinite(v) for v in vals):
        return False
    diag = (mx - mn).GetLength()
    return math.isfinite(diag) and 0.0 < diag <= 1.0e9


def _bbox_range_for_prim(prim: Any) -> Any | None:
    from pxr import Usd, UsdGeom  # type: ignore

    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
        useExtentsHint=True,
    )
    rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    if _range_is_sane(rng):
        return rng
    return None


def compute_model_local_bbox(model_path: Path) -> dict[str, Any] | None:
    from pxr import Usd  # type: ignore

    stage = Usd.Stage.Open(str(model_path))
    if stage is None:
        return None
    prim = stage.GetDefaultPrim()
    if not prim or not prim.IsValid():
        prim = stage.GetPseudoRoot()
    rng = _bbox_range_for_prim(prim)
    if rng is None:
        return None
    return _bbox_dict_from_range(rng)


def transform_bbox_by_matrix(local_bbox: dict[str, Any], matrix: Any) -> dict[str, Any]:
    from pxr import Gf  # type: ignore

    mn = local_bbox["min"]
    mx = local_bbox["max"]
    corners = [
        Gf.Vec3d(x, y, z)
        for x in (mn[0], mx[0])
        for y in (mn[1], mx[1])
        for z in (mn[2], mx[2])
    ]
    transformed = [matrix.Transform(corner) for corner in corners]
    mins = [min(point[axis] for point in transformed) for axis in range(3)]
    maxs = [max(point[axis] for point in transformed) for axis in range(3)]
    size = [maxs[axis] - mins[axis] for axis in range(3)]
    center = [(mins[axis] + maxs[axis]) * 0.5 for axis in range(3)]
    diagonal = math.sqrt(sum(value * value for value in size))
    return {"min": mins, "max": maxs, "center": center, "size": size, "diagonal": diagonal}


def compute_target_bbox_from_model(stage: Any, prim_path: str, model_path: Path) -> dict[str, Any] | None:
    from pxr import Sdf, Usd, UsdGeom  # type: ignore

    prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
    if not prim or not prim.IsValid():
        return None
    local_bbox = compute_model_local_bbox(model_path)
    if local_bbox is None:
        return None
    if prim.IsA(UsdGeom.Xformable):
        matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    else:
        from pxr import Gf  # type: ignore

        matrix = Gf.Matrix4d(1.0)
    return transform_bbox_by_matrix(local_bbox, matrix)


def _should_ignore_for_bbox(node: Any, usd_lux: Any) -> bool:
    path_token = node.GetPath().pathString.lower()
    if "__default_setting" in path_token:
        return True
    if "hdr" in path_token and "sphere" in path_token:
        return True
    if "skydome" in path_token or "environment" in path_token:
        return True
    try:
        dome = usd_lux.DomeLight(node)
        if dome and dome.GetPrim().IsValid():
            return True
    except Exception:
        pass
    return False


def compute_world_bbox(stage: Any, prim_path: str) -> dict[str, Any] | None:
    """Compute a serializable world bbox for a prim, using lazy pxr imports."""

    from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux  # type: ignore

    prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
    if not prim or not prim.IsValid():
        return None

    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
        useExtentsHint=True,
    )
    rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    top_rng = rng if _range_is_sane(rng) else None

    bounds = []
    stack = [prim]
    while stack:
        node = stack.pop()
        if not node or not node.IsValid():
            continue
        if _should_ignore_for_bbox(node, UsdLux):
            continue
        stack.extend(list(node.GetChildren()))
        if not node.IsA(UsdGeom.Imageable):
            continue
        local_rng = cache.ComputeWorldBound(node).ComputeAlignedRange()
        if not _range_is_sane(local_rng):
            continue
        local_min, local_max = local_rng.GetMin(), local_rng.GetMax()
        bounds.append(((local_max - local_min).GetLength(), local_min, local_max))

    if bounds:
        if len(bounds) > 1:
            diags = sorted(item[0] for item in bounds)
            typical = diags[len(diags) // 2]
            if math.isfinite(typical) and typical > 0.0:
                limit = max(typical * 20.0, typical + 10.0)
                filtered = [item for item in bounds if item[0] <= limit]
                if filtered:
                    bounds = filtered
        mins = [math.inf, math.inf, math.inf]
        maxs = [-math.inf, -math.inf, -math.inf]
        for _, mn, mx in bounds:
            for axis in range(3):
                mins[axis] = min(mins[axis], mn[axis])
                maxs[axis] = max(maxs[axis], mx[axis])
        if all(math.isfinite(v) for v in mins + maxs):
            agg_rng = Gf.Range3d(Gf.Vec3d(*mins), Gf.Vec3d(*maxs))
        else:
            agg_rng = None
    else:
        agg_rng = None

    chosen_rng = agg_rng or top_rng
    if chosen_rng is None:
        return None
    if top_rng is not None and agg_rng is not None:
        top_size = top_rng.GetMax() - top_rng.GetMin()
        agg_size = agg_rng.GetMax() - agg_rng.GetMin()
        diag_top = top_size.GetLength()
        diag_agg = agg_size.GetLength()
        if not (math.isfinite(diag_agg) and diag_agg > 0 and (diag_agg * 2.0 <= diag_top or diag_agg <= diag_top * 0.25)):
            chosen_rng = top_rng

    return _bbox_dict_from_range(chosen_rng)


def collect_prim_asset_records(stage: Any) -> list[dict[str, Any]]:
    """Collect candidate object prims, without computing bboxes."""

    records: list[dict[str, Any]] = []
    for prim in stage.Traverse():
        asset_paths = _authored_asset_paths(prim)
        prim_name = prim.GetName()
        if not asset_paths and not prim_name.startswith("model_"):
            continue
        records.append(
            {
                "prim_path": prim.GetPath().pathString,
                "prim_name": prim_name,
                "type_name": prim.GetTypeName(),
                "asset_paths": asset_paths,
                "reference_asset_path": asset_paths[0] if asset_paths else None,
                "resolved_model_path": None,
                "world_bbox": None,
                "bbox_method": None,
                "bbox_status": "pending",
            }
        )
    return records


def _reference_asset_for_metadata(prim_record: dict[str, Any], metadata_paths: list[str]) -> str | None:
    for asset_path in prim_record.get("asset_paths", []):
        for metadata_path in metadata_paths:
            if asset_path_matches_metadata_path(str(asset_path), str(metadata_path)):
                return str(asset_path)
    return None


def _episode_candidates(
    episode_record: dict[str, Any], prim_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    candidates = _reference_candidates(episode_record, prim_records)
    if candidates:
        return candidates
    return _suffix_candidates(episode_record, prim_records)


def _attach_candidate_bboxes(
    stage: Any,
    scene_entry: dict[str, Any],
    episode_records: list[dict[str, Any]],
    prim_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_root = Path(scene_entry["source_dataset_root"])
    scene_split = str(scene_entry["source_scene_split"])
    updates_by_path: dict[str, dict[str, Any]] = {}

    for episode_record in episode_records:
        metadata_paths = [str(path) for path in episode_record.get("metadata_model_paths", [])]
        if not metadata_paths:
            continue
        model_path = resolve_model_path(source_root, scene_split, metadata_paths[0])
        for candidate in _episode_candidates(episode_record, prim_records):
            prim_path = str(candidate["prim_path"])
            if prim_path in updates_by_path:
                continue
            reference_asset_path = _reference_asset_for_metadata(candidate, metadata_paths)
            if model_path.exists():
                world_bbox = compute_target_bbox_from_model(stage, prim_path, model_path)
                bbox_method = "model_local_bbox_x_scene_xform" if world_bbox is not None else "model_local_bbox_x_scene_xform_failed"
            else:
                world_bbox = compute_world_bbox(stage, prim_path)
                bbox_method = "scene_composed_bbox_fallback" if world_bbox is not None else "unresolved_missing_model_file"
            updates_by_path[prim_path] = {
                "reference_asset_path": reference_asset_path or candidate.get("reference_asset_path"),
                "resolved_model_path": str(model_path),
                "world_bbox": world_bbox,
                "bbox_method": bbox_method,
                "bbox_status": "resolved" if world_bbox is not None else "unresolved",
            }

    enriched = []
    for record in prim_records:
        prim_path = str(record["prim_path"])
        if prim_path in updates_by_path:
            enriched.append({**record, **updates_by_path[prim_path]})
        else:
            enriched.append(record)
    return enriched


def _open_stage(path: Path) -> Any:
    from pxr import Usd  # type: ignore

    stage = Usd.Stage.Open(str(path), Usd.Stage.LoadNone)
    if stage is None:
        raise RuntimeError(f"Failed to open USD stage: {path}")
    return stage


def resolve_manifest(
    manifest: dict[str, Any],
    *,
    limit_scenes: int | None = None,
) -> dict[str, Any]:
    scene_entries = {scene["source_scene_id"]: scene for scene in manifest.get("scenes", [])}
    records_by_scene: dict[str, list[dict[str, Any]]] = {}
    for record in manifest.get("episode_records", []):
        records_by_scene.setdefault(record["source_scene_id"], []).append(record)

    scene_order = [scene["source_scene_id"] for scene in manifest.get("scenes", []) if scene["source_scene_id"] in records_by_scene]
    if limit_scenes is not None:
        scene_order = scene_order[: max(0, limit_scenes)]

    resolved_records: list[dict[str, Any]] = []
    resolved_scenes: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}

    for scene_id in scene_order:
        scene = scene_entries[scene_id]
        stage = _open_stage(Path(scene["source_usd"]))
        prim_records = collect_prim_asset_records(stage)
        scene_records = records_by_scene[scene_id]
        prim_records = _attach_candidate_bboxes(stage, scene, scene_records, prim_records)

        scene_status_counts: dict[str, int] = {}
        for record in scene_records:
            resolved = resolve_episode_record(record, prim_records)
            status = resolved["mapping_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            scene_status_counts[status] = scene_status_counts.get(status, 0) + 1
            resolved_records.append(resolved)

        resolved_scenes.append(
            {
                **scene,
                "target_resolution": {
                    "episode_records": len(scene_records),
                    "prim_asset_records": len(prim_records),
                    "status_counts": scene_status_counts,
                },
            }
        )

    return {
        "schema_version": 1,
        "status": "target_resolved_manifest",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py",
        "generator_git_commit": _git_commit(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_manifest_status": manifest.get("status"),
        "dataset_roles": manifest.get("dataset_roles", {}),
        "selection": manifest.get("selection", {}),
        "paper_claim_gate": manifest.get("paper_claim_gate", {}),
        "resolution_summary": {
            "scenes_attempted": len(scene_order),
            "episode_records_attempted": len(resolved_records),
            "status_counts": status_counts,
            **target_uniqueness_summary(resolved_records),
        },
        "scenes": resolved_scenes,
        "episode_records": resolved_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit-scenes", type=int, default=None)
    parser.add_argument("--fail-on-unresolved", action="store_true")
    args = parser.parse_args()

    manifest = _load_json(args.manifest)
    validate_output_path(args.out, manifest)
    result = resolve_manifest(manifest, limit_scenes=args.limit_scenes)
    result["source_manifest"] = {
        "path": str(args.manifest),
        "hash_sha256": _sha256_file(args.manifest),
    }
    result["generator_provenance"] = {
        "command": [sys.executable, *sys.argv],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_status_porcelain": _git_status_porcelain(),
    }
    unresolved = {
        status: count
        for status, count in result["resolution_summary"]["status_counts"].items()
        if not status.startswith("resolved_")
    }
    result["resolution_summary"]["unresolved_status_counts"] = unresolved

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} with {result['resolution_summary']['episode_records_attempted']} "
        f"records across {result['resolution_summary']['scenes_attempted']} scenes"
    )
    if args.fail_on_unresolved and unresolved:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
