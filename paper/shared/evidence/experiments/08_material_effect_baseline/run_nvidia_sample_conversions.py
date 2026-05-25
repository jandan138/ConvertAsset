#!/usr/bin/env python3
"""Run NVIDIA Asset Converter over selected material-effect source scenes."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_CONVERSION_MANIFEST = (
    PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/baseline_conversion_manifest.json"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/nvidia_sample_conversion_manifest.json"
)
CONDITION_ORIGINAL = "original_MDL"
CONDITION_NVIDIA = "nvidia_asset_converter_preview_or_bake"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_size(path: Path) -> int | None:
    return path.stat().st_size if path.exists() and path.is_file() else None


def _scene_sample_effects(samples: list[dict[str, Any]]) -> list[str]:
    effects = {
        str(effect)
        for sample in samples
        for effect in sample.get("present_effects", [])
    }
    return sorted(effects)


def build_scene_conversion_jobs(
    conversion_manifest: dict[str, Any],
    *,
    force: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    samples_by_scene: dict[str, list[dict[str, Any]]] = {}
    for sample in conversion_manifest.get("samples", []):
        scene_id = str(sample.get("source_scene_id") or "")
        if scene_id:
            samples_by_scene.setdefault(scene_id, []).append(sample)

    jobs: list[dict[str, Any]] = []
    for scene_id in sorted(samples_by_scene):
        samples = samples_by_scene[scene_id]
        first = samples[0]
        original = (first.get("conditions") or {}).get(CONDITION_ORIGINAL) or {}
        nvidia = (first.get("conditions") or {}).get(CONDITION_NVIDIA) or {}
        input_usd = Path(str(original.get("usd_path") or ""))
        output_usd = Path(str(nvidia.get("usd_path") or ""))
        skip_reason = None
        if not input_usd.exists():
            skip_reason = "input_missing"
        elif output_usd.exists() and not force:
            skip_reason = "output_exists"
        jobs.append(
            {
                "source_scene_id": scene_id,
                "sample_ids": [str(sample.get("sample_id")) for sample in samples],
                "sample_count": len(samples),
                "present_effects": _scene_sample_effects(samples),
                "input_usd": str(input_usd),
                "input_hash_sha256": _sha256(input_usd),
                "input_size_bytes": _file_size(input_usd),
                "output_usd": str(output_usd),
                "context_flags": dict(nvidia.get("context_flags") or {}),
                "preferred_smoke_attempt": nvidia.get("preferred_smoke_attempt"),
                "skip_reason": skip_reason,
            }
        )
        if limit is not None and len(jobs) >= limit:
            break
    return jobs


def build_attempt_record(
    job: dict[str, Any],
    *,
    conversion_success: bool,
    error_message: str | None,
    started_at_utc: str,
    finished_at_utc: str,
) -> dict[str, Any]:
    output_path = Path(str(job["output_usd"]))
    output_exists = output_path.exists()
    return {
        "source_scene_id": job["source_scene_id"],
        "sample_ids": job["sample_ids"],
        "sample_count": job.get("sample_count", len(job.get("sample_ids", []))),
        "present_effects": job.get("present_effects", []),
        "input_usd": job["input_usd"],
        "input_hash_sha256": job.get("input_hash_sha256"),
        "input_size_bytes": job.get("input_size_bytes"),
        "output_usd": job["output_usd"],
        "output_exists": output_exists,
        "output_hash_sha256": _sha256(output_path),
        "output_size_bytes": _file_size(output_path),
        "context_flags": job.get("context_flags") or {},
        "preferred_smoke_attempt": job.get("preferred_smoke_attempt"),
        "conversion_success": bool(conversion_success),
        "error_message": error_message,
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
    }


def build_sample_conversion_manifest(
    *,
    jobs: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    generated_at_utc: str | None = None,
    generator_git_commit: str | None = None,
) -> dict[str, Any]:
    attempted_scene_ids = {attempt["source_scene_id"] for attempt in attempts}
    skipped_jobs = [job for job in jobs if job.get("skip_reason")]
    reusable_existing_output_count = sum(
        1
        for job in skipped_jobs
        if job.get("skip_reason") == "output_exists" and Path(str(job.get("output_usd"))).exists()
    )
    status_counts = Counter()
    for job in skipped_jobs:
        status_counts[f"skipped:{job['skip_reason']}"] += 1
    for attempt in attempts:
        status = "success" if attempt.get("conversion_success") else "failed"
        status_counts[status] += 1
    output_exists_count = (
        sum(1 for attempt in attempts if attempt.get("output_exists"))
        + reusable_existing_output_count
    )
    blockers: list[str] = []
    if any(job.get("skip_reason") == "input_missing" for job in jobs):
        blockers.append("input_missing")
    if any(not attempt.get("conversion_success") for attempt in attempts):
        blockers.append("conversion_failed")
    if attempts and output_exists_count < len(attempts):
        blockers.append("converted_output_missing")
    if not attempts and not skipped_jobs:
        blockers.append("no_jobs")
    non_missing_output_jobs = sum(1 for job in jobs if job.get("skip_reason") != "input_missing")
    return {
        "schema_version": 1,
        "status": "nvidia_sample_conversion_manifest",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_sample_conversions.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "generator_git_commit": generator_git_commit or _git_commit(),
        "summary": {
            "scene_job_count": len(jobs),
            "attempted_scene_count": len(attempted_scene_ids),
            "skipped_scene_count": len(skipped_jobs),
            "reusable_existing_output_count": reusable_existing_output_count,
            "successful_scene_count": sum(1 for attempt in attempts if attempt.get("conversion_success")),
            "failed_scene_count": sum(1 for attempt in attempts if not attempt.get("conversion_success")),
            "output_exists_count": output_exists_count,
            "status_counts": dict(sorted(status_counts.items())),
            "ready_for_baseline_manifest_regeneration": output_exists_count == non_missing_output_jobs
            and not blockers,
            "blockers": blockers,
        },
        "jobs": jobs,
        "attempts": attempts,
        "claim_boundary": {
            "allowed": [
                "This manifest records NVIDIA sample-scene conversion attempts and output paths."
            ],
            "forbidden": [
                "Do not claim material baseline comparison until baseline_conversion_manifest is regenerated and static gates inspect NVIDIA outputs.",
                "Do not treat converter success alone as render or visual quality success.",
            ],
        },
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


async def _convert_asset(input_path: Path, output_path: Path, context_flags: dict[str, Any]) -> tuple[bool, str | None]:
    import omni.kit.asset_converter

    def progress_callback(_progress: int, _total_steps: int) -> None:
        return None

    context = omni.kit.asset_converter.AssetConverterContext()
    for key, value in context_flags.items():
        if hasattr(context, key):
            setattr(context, key, value)
    instance = omni.kit.asset_converter.get_instance()
    task = instance.create_converter_task(str(input_path), str(output_path), progress_callback, context)
    success = await task.wait_until_finished()
    return bool(success), None if success else task.get_error_message()


def _enable_asset_converter_extension() -> None:
    import omni.kit.app

    try:
        from isaacsim.core.utils.extensions import enable_extension

        enable_extension("omni.kit.asset_converter")
    except Exception:
        manager = omni.kit.app.get_app().get_extension_manager()
        manager.set_extension_enabled_immediate("omni.kit.asset_converter", True)
    omni.kit.app.get_app().update()


def run_jobs(jobs: list[dict[str, Any]], manifest_path: Path) -> list[dict[str, Any]]:
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True})
    attempts: list[dict[str, Any]] = []
    try:
        _enable_asset_converter_extension()
        for job in jobs:
            if job.get("skip_reason"):
                write_manifest(
                    manifest_path,
                    build_sample_conversion_manifest(jobs=jobs, attempts=attempts),
                )
                continue
            input_path = Path(str(job["input_usd"]))
            output_path = Path(str(job["output_usd"]))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            started = _utc_now()
            try:
                if output_path.exists():
                    output_path.unlink()
                success, error = asyncio.get_event_loop().run_until_complete(
                    _convert_asset(input_path, output_path, job.get("context_flags") or {})
                )
            except Exception as exc:
                success = False
                error = f"exception:{type(exc).__name__}:{exc}"
            attempts.append(
                build_attempt_record(
                    job,
                    conversion_success=success,
                    error_message=error,
                    started_at_utc=started,
                    finished_at_utc=_utc_now(),
                )
            )
            write_manifest(
                manifest_path,
                build_sample_conversion_manifest(jobs=jobs, attempts=attempts),
            )
        return attempts
    finally:
        app.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conversion-manifest", type=Path, default=DEFAULT_CONVERSION_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conversion_manifest = _load_json(args.conversion_manifest)
    jobs = build_scene_conversion_jobs(conversion_manifest, force=args.force, limit=args.limit)
    if args.dry_run:
        attempts: list[dict[str, Any]] = []
    else:
        attempts = run_jobs(jobs, args.out)
    manifest = build_sample_conversion_manifest(jobs=jobs, attempts=attempts)
    write_manifest(args.out, manifest)
    print(
        f"Wrote {args.out} scene_jobs={manifest['summary']['scene_job_count']} "
        f"attempted={manifest['summary']['attempted_scene_count']} "
        f"success={manifest['summary']['successful_scene_count']} "
        f"outputs={manifest['summary']['output_exists_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
