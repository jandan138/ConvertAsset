#!/usr/bin/env python3
"""Find supplemental local candidates for missing material-effect bins."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
DEFAULT_EFFECT_MANIFEST = RAW_DIR / "effect_sample_manifest.json"
DEFAULT_OUTPUT = RAW_DIR / "supplemental_effect_candidate_manifest.json"
SCRIPT_DIR = Path(__file__).resolve().parent


def _load_effect_detector():
    module_path = SCRIPT_DIR / "build_effect_sample_manifest.py"
    spec = importlib.util.spec_from_file_location("material_effect_sample_manifest_for_supplemental", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load effect detector: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_EFFECT_DETECTOR = _load_effect_detector()
EFFECT_ORDER = list(_EFFECT_DETECTOR.EFFECT_ORDER)
detect_material_effects = _EFFECT_DETECTOR.detect_material_effects


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
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


def default_candidate_specs() -> list[dict[str, Any]]:
    """Return bounded local official/sample candidate specs in priority order."""

    material_library_root = Path("/isaac-sim/extscache/omni.kit.material.library-1.5.15+d02c707b/data/tests")
    mdl_converter_root = Path(
        "/isaac-sim/extscache/omni.mdl.usd_converter-1.0.24+d02c707b/"
        "omni/mdl/usd_converter/tests/data"
    )
    return [
        {
            "candidate_id": "isaac_material_library_omnipbr_clearcoat_opacity",
            "source_rank": 10,
            "source_kind": "official_isaac_sim_material_library_test",
            "source_usd": str(material_library_root / "usd/material_binding.usda"),
            "mdl_paths": [str(material_library_root / "mtl/OmniPBR_ClearCoat_Opacity.mdl")],
            "wrapper_required": True,
            "wrapper_reason": "USD defines clearcoat MDL materials, but the test cube is not bound to the clearcoat material.",
            "notes": "Use as source MDL/material library evidence; author a small bound wrapper before conversion/render claims.",
        },
        {
            "candidate_id": "nvidia_mdl_sdk_tutorials_checker_noise",
            "source_rank": 20,
            "source_kind": "official_nvidia_mdl_sdk_example",
            "source_usd": str(mdl_converter_root / "usd/tutorials.usda"),
            "mdl_paths": [str(mdl_converter_root / "mdl/nvidia/sdk_examples/tutorials.mdl")],
            "wrapper_required": True,
            "wrapper_reason": "USD exposes shader/material definitions from the tutorial module, but no renderable bound object is selected yet.",
            "notes": "Use the tutorial checker/noise MDL functions as procedural-texture source evidence; author a bound wrapper stage next.",
        },
    ]


def _missing_effects(existing_effect_manifest: dict[str, Any]) -> list[str]:
    summary = existing_effect_manifest.get("summary") or {}
    gaps = summary.get("effect_gaps")
    if gaps:
        return [effect for effect in EFFECT_ORDER if effect in set(gaps)]
    counts = summary.get("effect_counts") or {}
    return [effect for effect in EFFECT_ORDER if int(counts.get(effect, 0) or 0) == 0]


def _candidate_record(spec: dict[str, Any], missing_effects: list[str]) -> dict[str, Any]:
    source_usd = Path(str(spec.get("source_usd") or ""))
    mdl_paths = [Path(str(path)) for path in spec.get("mdl_paths") or []]
    effects = detect_material_effects(mdl_paths)
    present_effects = [effect for effect in EFFECT_ORDER if effects[effect]["present"]]
    matching_missing = [effect for effect in missing_effects if effect in present_effects]
    return {
        "candidate_id": str(spec.get("candidate_id")),
        "source_rank": int(spec.get("source_rank", 9999)),
        "source_kind": spec.get("source_kind"),
        "source_usd": str(source_usd),
        "source_usd_exists": source_usd.is_file(),
        "source_usd_hash_sha256": _sha256(source_usd),
        "wrapper_required": bool(spec.get("wrapper_required", True)),
        "wrapper_reason": spec.get("wrapper_reason"),
        "notes": spec.get("notes"),
        "present_effects": present_effects,
        "matching_missing_effects": matching_missing,
        "effects": effects,
        "mdl_files": [
            {
                "path": str(path),
                "name": path.name,
                "exists": path.is_file(),
                "hash_sha256": _sha256(path),
            }
            for path in mdl_paths
        ],
    }


def _recommendations(candidates: list[dict[str, Any]], missing_effects: list[str]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for effect in missing_effects:
        matches = [
            candidate
            for candidate in candidates
            if effect in candidate["matching_missing_effects"]
            and candidate["source_usd_exists"]
            and all(mdl["exists"] for mdl in candidate["mdl_files"])
        ]
        if not matches:
            continue
        best = sorted(matches, key=lambda candidate: (candidate["source_rank"], candidate["candidate_id"]))[0]
        recommendations.append(
            {
                "effect": effect,
                "candidate_id": best["candidate_id"],
                "source_kind": best["source_kind"],
                "source_usd": best["source_usd"],
                "wrapper_required": best["wrapper_required"],
            }
        )
    return recommendations


def build_supplemental_candidate_manifest(
    existing_effect_manifest: dict[str, Any],
    candidate_specs: list[dict[str, Any]],
    *,
    generated_at_utc: str | None = None,
    generator_git_commit: str | None = None,
) -> dict[str, Any]:
    missing = _missing_effects(existing_effect_manifest)
    candidates = [_candidate_record(spec, missing) for spec in sorted(candidate_specs, key=lambda item: int(item.get("source_rank", 9999)))]
    recommendations = _recommendations(candidates, missing)
    covered = [effect for effect in missing if any(rec["effect"] == effect for rec in recommendations)]
    remaining = [effect for effect in missing if effect not in set(covered)]
    wrapper_required = any(rec.get("wrapper_required") for rec in recommendations)

    blockers: list[str] = []
    if remaining:
        blockers.append("missing_effects_without_candidate_sources")
    if wrapper_required:
        blockers.append("supplemental_wrapper_scenes_not_authored")
    if recommendations:
        blockers.append("supplemental_baseline_conversions_not_run")

    return {
        "schema_version": 1,
        "status": "supplemental_effect_candidate_manifest",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_effect_candidates.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "generator_git_commit": generator_git_commit or _git_commit(),
        "effect_order": EFFECT_ORDER,
        "summary": {
            "missing_effects": missing,
            "candidate_count": len(candidates),
            "recommendation_count": len(recommendations),
            "covered_missing_effects": covered,
            "remaining_missing_effects": remaining,
            "ready_for_fixture_authoring": bool(missing) and not remaining,
            "ready_for_baseline_conversion": False,
            "blockers": blockers,
        },
        "recommendations": recommendations,
        "candidates": candidates,
        "claim_boundary": {
            "allowed": [
                "This manifest identifies local official/sample sources that can fill missing material-effect bins.",
                "It can guide wrapper-stage authoring for supplemental baseline runs.",
            ],
            "forbidden": [
                "Do not count these candidates as covered baseline samples until wrapper scenes are authored.",
                "Do not update effect-table sample counts until original/noMDL/NVIDIA condition records exist.",
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effect-manifest", type=Path, default=DEFAULT_EFFECT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    manifest = build_supplemental_candidate_manifest(
        _load_json(args.effect_manifest),
        default_candidate_specs(),
    )
    manifest["inputs"] = {
        "effect_manifest": {
            "path": str(args.effect_manifest),
            "hash_sha256": _sha256(args.effect_manifest),
        }
    }
    manifest["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} recommendations={manifest['summary']['recommendation_count']} "
        f"remaining={manifest['summary']['remaining_missing_effects']}"
    )
    return 0 if not manifest["summary"]["remaining_missing_effects"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
