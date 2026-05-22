#!/usr/bin/env python3
"""Author USD camera stages for GRScenes paired render jobs.

The module is import-clean outside Isaac/PXR. It imports `pxr` only when
`--apply` writes camera stage files.
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
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_RENDER_MANIFEST = RAW_DIR / "render_manifest.json"
DEFAULT_OUTPUT = RAW_DIR / "camera_stage_authoring_report.json"
DEFAULT_RENDER_LIGHTING = {
    "enabled": True,
    "dome_light_path": "/World/GRScenesRenderDomeLight",
    "distant_light_path": "/World/GRScenesRenderDistantLight",
    "dome_intensity": 1000.0,
    "distant_intensity": 3000.0,
    "distant_angle": 1.0,
    "distant_rotation_xyz": [-45.0, 30.0, 0.0],
}


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


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _vec3(values: Any, *, field: str) -> list[float]:
    if not isinstance(values, list | tuple) or len(values) != 3:
        raise ValueError(f"{field} must contain exactly three numeric values")
    out = [float(value) for value in values]
    if not all(math.isfinite(value) for value in out):
        raise ValueError(f"{field} values must be finite")
    return out


def _sub(a: list[float], b: list[float]) -> list[float]:
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _dot(a: list[float], b: list[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _norm(a: list[float]) -> float:
    return math.sqrt(_dot(a, a))


def _normalize(a: list[float], *, field: str) -> list[float]:
    length = _norm(a)
    if not math.isfinite(length) or length <= 1.0e-9:
        raise ValueError(f"{field} vector is degenerate")
    return [a[0] / length, a[1] / length, a[2] / length]


def camera_transform_rows(camera: dict[str, Any]) -> list[list[float]]:
    """Build a USD camera local-to-world transform from manifest camera fields.

    USD cameras look down local -Z. Rows are authored as right, up, back, and
    translation, matching existing camera helpers in this repository.
    """

    eye = _vec3(camera.get("position_world"), field="camera.position_world")
    target = _vec3(camera.get("look_at") or camera.get("target_world"), field="camera.look_at")
    up_hint = _normalize(_vec3(camera.get("up_world", [0.0, 0.0, 1.0]), field="camera.up_world"), field="camera.up_world")
    forward = _normalize(_sub(target, eye), field="camera forward")
    right = _cross(forward, up_hint)
    if _norm(right) <= 1.0e-9:
        fallback = [1.0, 0.0, 0.0] if abs(forward[0]) < 0.9 else [0.0, 1.0, 0.0]
        right = _cross(forward, fallback)
    right = _normalize(right, field="camera right")
    up = _normalize(_cross(right, forward), field="camera up")
    back = [-forward[0], -forward[1], -forward[2]]
    return [
        [right[0], right[1], right[2], 0.0],
        [up[0], up[1], up[2], 0.0],
        [back[0], back[1], back[2], 0.0],
        [eye[0], eye[1], eye[2], 1.0],
    ]


def _selected_records(
    render_manifest: dict[str, Any],
    *,
    limit_records: int | None = None,
    material_condition: str | None = None,
    include_existing: bool = False,
) -> list[dict[str, Any]]:
    records = []
    for record in render_manifest.get("records", []):
        if material_condition and record.get("material_condition") != material_condition:
            continue
        camera_stage_path = Path(str(record.get("camera_stage_path", "")))
        if not include_existing and camera_stage_path.is_file():
            continue
        records.append(record)
        if limit_records is not None and len(records) >= limit_records:
            break
    return records


def _render_lighting_spec(*, enabled: bool = True) -> dict[str, Any]:
    return {**DEFAULT_RENDER_LIGHTING, "enabled": bool(enabled)}


def _job_from_record(
    record: dict[str, Any],
    *,
    overwrite: bool = False,
    auto_lights: bool = True,
) -> dict[str, Any]:
    input_usd = Path(str(record.get("usd_path", ""))).resolve(strict=False)
    camera_stage_path = Path(str(record.get("camera_stage_path", ""))).resolve(strict=False)
    camera = dict(record.get("camera") or {})
    blocked_by: list[str] = []
    if not input_usd.is_file():
        blocked_by.append("input_usd_missing")
    if not camera_stage_path.name:
        blocked_by.append("camera_stage_path_missing")
    if camera_stage_path.exists() and not overwrite:
        blocked_by.append("camera_stage_exists")
    try:
        rows = camera_transform_rows(camera)
    except Exception as exc:
        rows = None
        blocked_by.append(f"invalid_camera:{exc}")
    return {
        "sample_id": record.get("sample_id"),
        "pair_id": record.get("pair_id"),
        "material_condition": record.get("material_condition"),
        "input_usd": str(input_usd),
        "camera_stage_path": str(camera_stage_path),
        "camera_prim_path": camera.get("camera_prim_path"),
        "camera": camera,
        "camera_transform_rows": rows,
        "render_lighting": _render_lighting_spec(enabled=auto_lights),
        "overwrite": overwrite,
        "blocked_by": _dedupe_preserve_order(blocked_by),
        "status": "blocked" if blocked_by else "planned",
    }


def write_camera_stage(job: dict[str, Any]) -> None:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux  # type: ignore

    out_path = Path(job["camera_stage_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not job.get("overwrite"):
        raise FileExistsError(f"camera stage already exists: {out_path}")

    stage = Usd.Stage.CreateNew(str(out_path))
    root_layer = stage.GetRootLayer()
    root_layer.subLayerPaths.append(str(Path(job["input_usd"])))
    camera = job["camera"]
    cam_path = str(job["camera_prim_path"])
    if not cam_path.startswith("/"):
        raise ValueError(f"camera_prim_path must be absolute: {cam_path}")
    cam = UsdGeom.Camera.Define(stage, Sdf.Path(cam_path))
    cam.GetFocalLengthAttr().Set(float(camera.get("focal_length_mm", 9.0)))
    cam.GetHorizontalApertureAttr().Set(float(camera.get("horizontal_aperture_mm", 20.955)))
    cam.GetVerticalApertureAttr().Set(float(camera.get("vertical_aperture_mm", 15.71625)))
    clip = camera.get("clipping_range") or [0.01, 100.0]
    cam.GetClippingRangeAttr().Set(Gf.Vec2f(float(clip[0]), float(clip[1])))

    rows = job["camera_transform_rows"]
    matrix = Gf.Matrix4d(1.0)
    for idx, row in enumerate(rows):
        matrix.SetRow(idx, Gf.Vec4d(float(row[0]), float(row[1]), float(row[2]), float(row[3])))
    xform = UsdGeom.Xformable(cam)
    xform.AddTransformOp().Set(matrix)

    stage.SetStartTimeCode(float(camera.get("start_frame", 0)))
    stage.SetEndTimeCode(float(camera.get("end_frame", 0)))
    stage.SetTimeCodesPerSecond(float(camera.get("time_codes_per_second", 24)))
    lighting = job.get("render_lighting") or {}
    if lighting.get("enabled"):
        dome = UsdLux.DomeLight.Define(stage, Sdf.Path(str(lighting["dome_light_path"])))
        dome.GetIntensityAttr().Set(float(lighting["dome_intensity"]))
        distant = UsdLux.DistantLight.Define(stage, Sdf.Path(str(lighting["distant_light_path"])))
        distant.GetIntensityAttr().Set(float(lighting["distant_intensity"]))
        distant.GetAngleAttr().Set(float(lighting["distant_angle"]))
        light_xform = UsdGeom.Xformable(distant.GetPrim())
        rotation = lighting["distant_rotation_xyz"]
        light_xform.AddRotateXYZOp().Set(Gf.Vec3f(float(rotation[0]), float(rotation[1]), float(rotation[2])))
    stage.Save()


def build_authoring_report(
    render_manifest: dict[str, Any],
    *,
    apply: bool = False,
    overwrite: bool = False,
    limit_records: int | None = None,
    material_condition: str | None = None,
    include_existing: bool = False,
    auto_lights: bool = True,
    writer: Callable[[dict[str, Any]], None] = write_camera_stage,
) -> dict[str, Any]:
    records = _selected_records(
        render_manifest,
        limit_records=limit_records,
        material_condition=material_condition,
        include_existing=include_existing,
    )
    jobs = [_job_from_record(record, overwrite=overwrite, auto_lights=auto_lights) for record in records]
    authored = 0
    failed = 0
    if apply:
        for job in jobs:
            if job["blocked_by"]:
                continue
            try:
                writer(job)
            except Exception as exc:
                failed += 1
                job["blocked_by"] = [f"write_failed:{exc}"]
                job["status"] = "failed"
                continue
            authored += 1
            job["status"] = "authored"

    blocked = [job for job in jobs if job["blocked_by"]]
    return {
        "schema_version": 1,
        "status": "camera_stage_authoring_report",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/author_render_camera_stages.py",
        "generated_at_utc": _utc_now(),
        "dry_run": not apply,
        "render_manifest_status": render_manifest.get("status"),
        "summary": {
            "selected_record_count": len(records),
            "planned_camera_stage_count": len([job for job in jobs if not job["blocked_by"]]),
            "blocked_camera_stage_count": len(blocked),
            "authored_camera_stage_count": authored,
            "failed_camera_stage_count": failed,
            "auto_lights_enabled": bool(auto_lights),
        },
        "jobs": jobs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-manifest", type=Path, default=DEFAULT_RENDER_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit-records", type=int, default=None)
    parser.add_argument("--material-condition", choices=["original", "converted"], default=None)
    parser.add_argument("--include-existing", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-auto-lights", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    render_manifest = _load_json(args.render_manifest)

    report = build_authoring_report(
        render_manifest,
        apply=args.apply,
        overwrite=args.overwrite,
        limit_records=args.limit_records,
        material_condition=args.material_condition,
        include_existing=args.include_existing,
        auto_lights=not args.no_auto_lights,
    )
    report["render_manifest"] = {
        "path": str(args.render_manifest),
        "hash_sha256": _sha256_file(args.render_manifest),
    }
    source_manifest = render_manifest.get("target_manifest")
    if isinstance(source_manifest, dict) and source_manifest.get("path"):
        source_path = Path(str(source_manifest["path"]))
        report["target_manifest"] = {
            "path": str(source_path),
            "hash_sha256": _sha256_file(source_path) if source_path.exists() else source_manifest.get("hash_sha256"),
        }
    else:
        report["target_manifest"] = None
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
        f"Wrote {args.out} selected={report['summary']['selected_record_count']} "
        f"authored={report['summary']['authored_camera_stage_count']} "
        f"blocked={report['summary']['blocked_camera_stage_count']} dry_run={report['dry_run']}"
    )
    summary = report["summary"]
    if args.apply and (
        summary["blocked_camera_stage_count"] > 0
        or summary["failed_camera_stage_count"] > 0
    ):
        return 1
    return 0 if summary["failed_camera_stage_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
