#!/usr/bin/env python3
"""Smoke-test NVIDIA Asset Converter as a material baseline candidate."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_ISAAC_ROOT = Path("/isaac-sim")
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke"
DEFAULT_OUTPUT = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke_manifest.json"


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


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_asset_converter_fixture(isaac_root: Path = DEFAULT_ISAAC_ROOT) -> Path | None:
    """Find NVIDIA's own Asset Converter MDL USD fixture in the local install."""

    extscache = isaac_root / "extscache"
    candidates = sorted(extscache.glob("omni.kit.asset_converter-*/data/MDL_to_glTF.usd"))
    if candidates:
        return candidates[-1]
    cube_candidates = sorted(extscache.glob("omni.kit.asset_converter-*/data/cube.obj"))
    return cube_candidates[-1] if cube_candidates else None


def _context_dict(context_flags: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in sorted(context_flags.items())}


def build_attempt_record(
    *,
    name: str,
    input_path: Path,
    output_path: Path,
    context_flags: dict[str, Any],
    conversion_success: bool,
    error_message: str | None,
    stage_counts: dict[str, Any] | None,
) -> dict[str, Any]:
    counts = stage_counts or {}
    output_exists = output_path.exists()
    stage_opened = bool(counts.get("stage_opened", False))
    preview_surface_count = counts.get("preview_surface_count")
    active_mdl_shader_count = counts.get("active_mdl_shader_count")
    claimable = bool(
        conversion_success
        and output_exists
        and output_path.suffix.lower() in {".usd", ".usda", ".usdc"}
        and stage_opened
        and (preview_surface_count or 0) > 0
        and active_mdl_shader_count == 0
    )
    return {
        "name": name,
        "input_usd": str(input_path),
        "input_hash_sha256": _sha256(input_path),
        "output_path": str(output_path),
        "output_hash_sha256": _sha256(output_path),
        "output_exists": output_exists,
        "context_flags": _context_dict(context_flags),
        "conversion_success": bool(conversion_success),
        "stage_opened": stage_opened,
        "preview_surface_count": preview_surface_count,
        "active_mdl_shader_count": active_mdl_shader_count,
        "claimable_as_baseline": claimable,
        "error_message": error_message,
    }


def build_smoke_manifest(
    *,
    fixture_path: Path | None,
    attempts: list[dict[str, Any]],
    generated_at_utc: str | None = None,
    generator_git_commit: str | None = None,
) -> dict[str, Any]:
    usable = [attempt["name"] for attempt in attempts if attempt.get("claimable_as_baseline")]
    blockers: list[str] = []
    if fixture_path is None:
        blockers.append("asset_converter_fixture_not_found")
    if not usable:
        blockers.append("no_claimable_usd_baseline_attempt")
    return {
        "schema_version": 1,
        "status": "nvidia_asset_converter_smoke",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_asset_converter_smoke.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "generator_git_commit": generator_git_commit or _git_commit(),
        "fixture_path": str(fixture_path) if fixture_path else None,
        "summary": {
            "attempt_count": len(attempts),
            "successful_attempt_count": sum(1 for attempt in attempts if attempt.get("conversion_success")),
            "usable_usd_baseline_attempts": usable,
            "ready_for_sample_baseline": bool(usable),
            "blockers": blockers,
        },
        "attempts": attempts,
        "claim_boundary": {
            "allowed": [
                "This smoke only validates whether the installed NVIDIA Asset Converter route can produce a USD baseline candidate."
            ],
            "forbidden": [
                "Do not compare ConvertAsset against NVIDIA from this smoke alone.",
                "Do not run full sample baselines unless ready_for_sample_baseline is true.",
            ],
        },
    }


def write_smoke_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def inspect_usd_material_counts(path: Path) -> dict[str, Any]:
    """Inspect output USD counts with lazy pxr import."""

    try:
        from pxr import Usd
    except Exception as exc:  # pragma: no cover - exercised only in Isaac/PXR env
        return {
            "stage_opened": False,
            "preview_surface_count": None,
            "active_mdl_shader_count": None,
            "error": f"pxr_import_failed:{exc}",
        }
    try:
        stage = Usd.Stage.Open(str(path))
    except Exception as exc:
        return {
            "stage_opened": False,
            "preview_surface_count": None,
            "active_mdl_shader_count": None,
            "error": f"stage_open_failed:{exc}",
        }
    if stage is None:
        return {
            "stage_opened": False,
            "preview_surface_count": None,
            "active_mdl_shader_count": None,
            "error": "stage_open_returned_none",
        }
    preview = 0
    active_mdl = 0
    for prim in stage.Traverse():
        if prim.GetTypeName() != "Shader":
            continue
        id_attr = prim.GetAttribute("info:id")
        shader_id = id_attr.Get() if id_attr else None
        if shader_id == "UsdPreviewSurface":
            preview += 1
        source_attr = prim.GetAttribute("info:implementationSource")
        source_value = source_attr.Get() if source_attr else None
        if source_value == "sourceAsset":
            source_asset = prim.GetAttribute("info:mdl:sourceAsset")
            if source_asset and source_asset.Get():
                active_mdl += 1
    return {
        "stage_opened": True,
        "preview_surface_count": preview,
        "active_mdl_shader_count": active_mdl,
    }


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


def run_smoke(
    fixture_path: Path,
    output_root: Path,
    checkpoint_manifest_path: Path | None = None,
) -> list[dict[str, Any]]:
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True})
    try:
        import omni.kit.app

        try:
            from isaacsim.core.utils.extensions import enable_extension

            enable_extension("omni.kit.asset_converter")
        except Exception:
            manager = omni.kit.app.get_app().get_extension_manager()
            manager.set_extension_enabled_immediate("omni.kit.asset_converter", True)
        omni.kit.app.get_app().update()
        attempts_spec = [
            (
                "usd_to_usd_preview",
                output_root / "MDL_to_glTF_preview.usd",
                {"ignore_materials": False, "export_preview_surface": True, "keep_all_materials": True},
            ),
            (
                "usd_to_usd_bake_flag",
                output_root / "MDL_to_glTF_bake.usd",
                {
                    "ignore_materials": False,
                    "export_preview_surface": True,
                    "bake_mdl_material": True,
                    "keep_all_materials": True,
                },
            ),
            (
                "usd_to_gltf_bake_flag",
                output_root / "MDL_to_glTF_bake.gltf",
                {
                    "ignore_materials": False,
                    "bake_mdl_material": True,
                    "keep_all_materials": True,
                    "export_separate_gltf": True,
                },
            ),
        ]
        output_root.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, Any]] = []
        for name, output_path, flags in attempts_spec:
            if output_path.exists():
                output_path.unlink()
            try:
                success, error = asyncio.get_event_loop().run_until_complete(
                    _convert_asset(fixture_path, output_path, flags)
                )
            except Exception as exc:
                success = False
                error = f"exception:{type(exc).__name__}:{exc}"
            counts = inspect_usd_material_counts(output_path) if output_path.suffix.lower() in {".usd", ".usda", ".usdc"} else None
            records.append(
                build_attempt_record(
                    name=name,
                    input_path=fixture_path,
                    output_path=output_path,
                    context_flags=flags,
                    conversion_success=success,
                    error_message=error,
                    stage_counts=counts,
                )
            )
        if checkpoint_manifest_path is not None:
            write_smoke_manifest(
                checkpoint_manifest_path,
                build_smoke_manifest(fixture_path=fixture_path, attempts=records),
            )
        return records
    finally:
        app.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-root", type=Path, default=DEFAULT_ISAAC_ROOT)
    parser.add_argument("--fixture", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = args.fixture or discover_asset_converter_fixture(args.isaac_root)
    if fixture is None:
        attempts: list[dict[str, Any]] = []
    else:
        attempts = run_smoke(fixture, args.output_root, checkpoint_manifest_path=args.out)
    manifest = build_smoke_manifest(fixture_path=fixture, attempts=attempts)
    write_smoke_manifest(args.out, manifest)
    print(
        f"Wrote {args.out} attempts={manifest['summary']['attempt_count']} "
        f"ready_for_sample_baseline={manifest['summary']['ready_for_sample_baseline']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
