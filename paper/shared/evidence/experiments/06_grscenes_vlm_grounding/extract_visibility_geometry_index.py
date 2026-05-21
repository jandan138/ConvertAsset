#!/usr/bin/env python3
"""Extract scene obstacle bboxes for GRScenes visibility preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_RENDER_MANIFEST = RAW_DIR / "render_manifest.json"
DEFAULT_OUTPUT = RAW_DIR / "visibility_geometry_index.json"
DEFAULT_MAX_DIAGONAL = 1000.0
DEFAULT_MAX_ABS_COORDINATE = 1_000_000.0


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _dedupe_sorted(items: list[str]) -> list[str]:
    return sorted(set(str(item) for item in items if item))


def is_target_or_descendant(prim_path: str, target_prim_paths: list[str]) -> bool:
    path = str(prim_path)
    for target in target_prim_paths:
        target_path = str(target).rstrip("/")
        if path == target_path or path.startswith(f"{target_path}/"):
            return True
    return False


def _original_usd_path(pair: dict[str, Any]) -> str:
    conditions = pair.get("conditions") or []
    for condition in conditions:
        if condition.get("material_condition") == "original" and condition.get("usd_path"):
            return str(condition["usd_path"])
    for condition in conditions:
        if condition.get("usd_path"):
            return str(condition["usd_path"])
    raise KeyError(f"usd_path missing for pair {pair.get('pair_id')}")


def scene_geometry_jobs(render_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    by_scene: dict[str, dict[str, Any]] = {}
    for pair in render_manifest.get("render_pairs", []):
        scene_id = str(pair.get("source_scene_id"))
        if not scene_id:
            continue
        entry = by_scene.setdefault(
            scene_id,
            {
                "source_scene_id": scene_id,
                "usd_path": _original_usd_path(pair),
                "target_prim_paths": [],
            },
        )
        target_path = pair.get("target_prim_path")
        if target_path:
            entry["target_prim_paths"].append(str(target_path))
    return [
        {**entry, "target_prim_paths": _dedupe_sorted(entry["target_prim_paths"])}
        for _, entry in sorted(by_scene.items())
    ]


def _finite_triplet(values: Any) -> list[float] | None:
    try:
        out = [float(values[0]), float(values[1]), float(values[2])]
    except Exception:
        return None
    return out if all(math.isfinite(value) for value in out) else None


def _bbox_record(
    prim_path: str,
    type_name: str,
    min_corner: Any,
    max_corner: Any,
    *,
    max_diagonal: float | None = DEFAULT_MAX_DIAGONAL,
    max_abs_coordinate: float = DEFAULT_MAX_ABS_COORDINATE,
) -> dict[str, Any] | None:
    lo = _finite_triplet(min_corner)
    hi = _finite_triplet(max_corner)
    if lo is None or hi is None:
        return None
    if any(abs(value) > float(max_abs_coordinate) for value in [*lo, *hi]):
        return None
    bbox_min = [min(lo[i], hi[i]) for i in range(3)]
    bbox_max = [max(lo[i], hi[i]) for i in range(3)]
    size = [bbox_max[i] - bbox_min[i] for i in range(3)]
    diagonal = math.sqrt(sum(value * value for value in size))
    if not math.isfinite(diagonal):
        return None
    if max_diagonal is not None and diagonal > float(max_diagonal):
        return None
    return {
        "prim_path": prim_path,
        "type_name": type_name,
        "bbox": {
            "min": [round(value, 6) for value in bbox_min],
            "max": [round(value, 6) for value in bbox_max],
            "size": [round(value, 6) for value in size],
            "diagonal": round(diagonal, 6),
        },
    }


def collect_scene_obstacles_from_usd(
    *,
    usd_path: str,
    target_prim_paths: list[str],
    min_diagonal: float,
    max_diagonal: float | None = DEFAULT_MAX_DIAGONAL,
    max_abs_coordinate: float = DEFAULT_MAX_ABS_COORDINATE,
) -> list[dict[str, Any]]:
    from pxr import Usd, UsdGeom  # type: ignore

    stage = Usd.Stage.Open(str(usd_path))
    if stage is None:
        raise RuntimeError(f"failed to open USD stage: {usd_path}")
    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
        useExtentsHint=True,
    )
    obstacles: list[dict[str, Any]] = []
    for prim in stage.Traverse():
        prim_path = str(prim.GetPath())
        if is_target_or_descendant(prim_path, target_prim_paths):
            continue
        if not prim.IsA(UsdGeom.Boundable):
            continue
        imageable = UsdGeom.Imageable(prim)
        if imageable and imageable.ComputeVisibility() == UsdGeom.Tokens.invisible:
            continue
        aligned = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        record = _bbox_record(
            prim_path,
            str(prim.GetTypeName()),
            aligned.GetMin(),
            aligned.GetMax(),
            max_diagonal=max_diagonal,
            max_abs_coordinate=max_abs_coordinate,
        )
        if record is None:
            continue
        if record["bbox"]["diagonal"] < float(min_diagonal):
            continue
        obstacles.append(record)
    return sorted(obstacles, key=lambda item: str(item["prim_path"]))


def build_geometry_index_report(
    render_manifest: dict[str, Any],
    *,
    collector: Callable[..., list[dict[str, Any]]] = collect_scene_obstacles_from_usd,
    min_diagonal: float = 0.05,
    max_diagonal: float | None = DEFAULT_MAX_DIAGONAL,
    max_abs_coordinate: float = DEFAULT_MAX_ABS_COORDINATE,
    limit_scenes: int | None = None,
) -> dict[str, Any]:
    jobs = scene_geometry_jobs(render_manifest)
    if limit_scenes is not None:
        jobs = jobs[: int(limit_scenes)]
    geometry_index: dict[str, list[dict[str, Any]]] = {}
    failures: list[dict[str, Any]] = []
    for job in jobs:
        try:
            geometry_index[job["source_scene_id"]] = collector(
                usd_path=job["usd_path"],
                target_prim_paths=job["target_prim_paths"],
                min_diagonal=float(min_diagonal),
                max_diagonal=max_diagonal,
                max_abs_coordinate=float(max_abs_coordinate),
            )
        except Exception as exc:
            geometry_index[job["source_scene_id"]] = []
            failures.append(
                {
                    "source_scene_id": job["source_scene_id"],
                    "usd_path": job["usd_path"],
                    "error": str(exc),
                }
            )
    obstacle_count = sum(len(items) for items in geometry_index.values())
    return {
        "schema_version": 1,
        "status": "visibility_geometry_index",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/extract_visibility_geometry_index.py",
        "generated_at_utc": _utc_now(),
        "summary": {
            "scene_count": len(jobs),
            "obstacle_count": obstacle_count,
            "failed_scene_count": len(failures),
            "min_diagonal": float(min_diagonal),
            "max_diagonal": None if max_diagonal is None else float(max_diagonal),
            "max_abs_coordinate": float(max_abs_coordinate),
            "geometry_contract": "scene_id_to_non_target_obstacle_aabbs",
        },
        "scene_jobs": jobs,
        "failures": failures,
        "geometry_index": geometry_index,
    }


def main(
    argv: list[str] | None = None,
    *,
    collector: Callable[..., list[dict[str, Any]]] = collect_scene_obstacles_from_usd,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-manifest", type=Path, default=DEFAULT_RENDER_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-diagonal", type=float, default=0.05)
    parser.add_argument("--max-diagonal", type=float, default=DEFAULT_MAX_DIAGONAL)
    parser.add_argument("--max-abs-coordinate", type=float, default=DEFAULT_MAX_ABS_COORDINATE)
    parser.add_argument("--limit-scenes", type=int, default=None)
    args = parser.parse_args(argv)

    render_manifest = _load_json(args.render_manifest)
    report = build_geometry_index_report(
        render_manifest,
        collector=collector,
        min_diagonal=args.min_diagonal,
        max_diagonal=args.max_diagonal,
        max_abs_coordinate=args.max_abs_coordinate,
        limit_scenes=args.limit_scenes,
    )
    report["render_manifest"] = {
        "path": str(args.render_manifest),
        "hash_sha256": _sha256_file(args.render_manifest),
    }
    report["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} scenes={report['summary']['scene_count']} "
        f"obstacles={report['summary']['obstacle_count']} failures={report['summary']['failed_scene_count']}"
    )
    return 0 if report["summary"]["failed_scene_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
