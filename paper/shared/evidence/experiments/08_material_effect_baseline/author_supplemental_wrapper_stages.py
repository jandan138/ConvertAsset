#!/usr/bin/env python3
"""Author small bound USD wrapper stages for missing material-effect candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
DEFAULT_CANDIDATE_MANIFEST = RAW_DIR / "supplemental_effect_candidate_manifest.json"
DEFAULT_FIXTURE_ROOT = RAW_DIR / "supplemental_fixtures"
DEFAULT_OUTPUT = RAW_DIR / "supplemental_wrapper_stage_manifest.json"
EXPECTED_EFFECTS = ["clearcoat", "procedural_texture"]


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


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate_by_id(candidate_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(candidate.get("candidate_id")): candidate
        for candidate in candidate_manifest.get("candidates", [])
        if candidate.get("candidate_id")
    }


def _first_mdl_path(candidate: dict[str, Any]) -> Path | None:
    mdl_files = candidate.get("mdl_files") or []
    for mdl_file in mdl_files:
        path = mdl_file.get("path")
        if path:
            return Path(str(path))
    return None


def _asset(path: Path) -> str:
    return str(path)


def _clearcoat_stage_text(mdl_path: Path) -> str:
    return f"""#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Y"
)

def Xform "World"
{{
    def DistantLight "KeyLight"
    {{
        float angle = 1
        float intensity = 4500
        double3 xformOp:rotateXYZ = (315, 0, 30)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }}

    def Camera "Camera"
    {{
        double focalLength = 35
        double2 clippingRange = (0.1, 1000)
        double3 xformOp:translate = (0, 1.2, 4.5)
        double3 xformOp:rotateXYZ = (-12, 0, 0)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
    }}

    def Scope "Looks"
    {{
        def Material "OmniPBR_ClearCoat_Opacity"
        {{
            token outputs:mdl:surface.connect = </World/Looks/OmniPBR_ClearCoat_Opacity/Shader.outputs:out>
            token outputs:mdl:displacement.connect = </World/Looks/OmniPBR_ClearCoat_Opacity/Shader.outputs:out>
            token outputs:mdl:volume.connect = </World/Looks/OmniPBR_ClearCoat_Opacity/Shader.outputs:out>

            def Shader "Shader"
            {{
                uniform token info:implementationSource = "sourceAsset"
                uniform asset info:mdl:sourceAsset = @{_asset(mdl_path)}@
                uniform token info:mdl:sourceAsset:subIdentifier = "OmniPBR_ClearCoat_Opacity"
                bool inputs:enable_clearcoat = 1
                color3f inputs:diffuse_tint = (0.16, 0.28, 0.55)
                float inputs:reflection_roughness_constant = 0.24
                float inputs:clearcoat_weight = 1
                float inputs:clearcoat_transparency = 1
                float inputs:clearcoat_reflection_roughness = 0.02
                color3f inputs:clearcoat_tint = (1, 1, 1)
                token outputs:out
            }}
        }}
    }}

    def Sphere "ClearcoatTarget" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {{
        float3[] extent = [(-1, -1, -1), (1, 1, 1)]
        rel material:binding = </World/Looks/OmniPBR_ClearCoat_Opacity>
        double radius = 1
        double3 xformOp:translate = (0, 0, 0)
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }}
}}
"""


def _procedural_texture_path(mdl_path: Path) -> Path | None:
    candidate = mdl_path.parent / "resources" / "example.png"
    return candidate if candidate.exists() else None


def _procedural_stage_text(mdl_path: Path) -> str:
    texture_path = _procedural_texture_path(mdl_path)
    texture_line = f"                asset inputs:tex = @{_asset(texture_path)}@\n" if texture_path else ""
    return f"""#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Y"
)

def Xform "World"
{{
    def DistantLight "KeyLight"
    {{
        float angle = 1
        float intensity = 4500
        double3 xformOp:rotateXYZ = (315, 0, -25)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }}

    def Camera "Camera"
    {{
        double focalLength = 35
        double2 clippingRange = (0.1, 1000)
        double3 xformOp:translate = (0, 1.4, 4.2)
        double3 xformOp:rotateXYZ = (-14, 0, 0)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
    }}

    def Scope "Looks"
    {{
        def Material "ProceduralChecker"
        {{
            token outputs:mdl:surface.connect = </World/Looks/ProceduralChecker/Shader.outputs:out>
            token outputs:mdl:displacement.connect = </World/Looks/ProceduralChecker/Shader.outputs:out>
            token outputs:mdl:volume.connect = </World/Looks/ProceduralChecker/Shader.outputs:out>

            def Shader "Shader"
            {{
                uniform token info:implementationSource = "sourceAsset"
                uniform asset info:mdl:sourceAsset = @{_asset(mdl_path)}@
                uniform token info:mdl:sourceAsset:subIdentifier = "example_df"
                int inputs:add_checker = 1
                float inputs:checker_scale = 8
                float inputs:roughness = 0.18
                float inputs:tex_coord_scale = 12
                color3f inputs:diffuse_tint = (1, 0.55, 0.28)
                color3f inputs:glossy_tint = (0.2, 0.45, 1)
{texture_line}                token outputs:out
            }}
        }}
    }}

    def Mesh "ProceduralTarget" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {{
        float3[] extent = [(-1.2, -0.02, -1.2), (1.2, 0.02, 1.2)]
        int[] faceVertexCounts = [4]
        int[] faceVertexIndices = [0, 1, 2, 3]
        point3f[] points = [(-1.2, 0, -1.2), (1.2, 0, -1.2), (1.2, 0, 1.2), (-1.2, 0, 1.2)]
        texCoord2f[] primvars:st = [(0, 0), (1, 0), (1, 1), (0, 1)] (
            interpolation = "faceVarying"
        )
        rel material:binding = </World/Looks/ProceduralChecker>
        double3 xformOp:rotateXYZ = (18, 0, 0)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }}
}}
"""


def _wrapper_spec(effect: str, candidate: dict[str, Any], output_root: Path) -> dict[str, Any] | None:
    mdl_path = _first_mdl_path(candidate)
    if mdl_path is None:
        return None
    if effect == "clearcoat":
        return {
            "wrapper_id": "supplemental_clearcoat_omnipbr",
            "filename": "supplemental_clearcoat_omnipbr.usda",
            "material_path": "/World/Looks/OmniPBR_ClearCoat_Opacity",
            "target_prim_path": "/World/ClearcoatTarget",
            "stage_text": _clearcoat_stage_text(mdl_path),
        }
    if effect == "procedural_texture":
        return {
            "wrapper_id": "supplemental_procedural_checker",
            "filename": "supplemental_procedural_checker.usda",
            "material_path": "/World/Looks/ProceduralChecker",
            "target_prim_path": "/World/ProceduralTarget",
            "stage_text": _procedural_stage_text(mdl_path),
        }
    return None


def _author_wrapper(
    recommendation: dict[str, Any],
    candidate: dict[str, Any],
    output_root: Path,
) -> dict[str, Any] | None:
    effect = str(recommendation.get("effect") or "")
    spec = _wrapper_spec(effect, candidate, output_root)
    if spec is None:
        return None

    output_root.mkdir(parents=True, exist_ok=True)
    wrapper_stage = output_root / str(spec["filename"])
    wrapper_stage.write_text(str(spec["stage_text"]), encoding="utf-8")
    mdl_files = candidate.get("mdl_files") or []

    return {
        "wrapper_id": spec["wrapper_id"],
        "candidate_id": recommendation.get("candidate_id"),
        "effect": effect,
        "source_kind": recommendation.get("source_kind"),
        "source_usd": recommendation.get("source_usd"),
        "source_mdl_files": [
            {
                "path": mdl_file.get("path"),
                "exists": Path(str(mdl_file.get("path"))).is_file() if mdl_file.get("path") else False,
                "hash_sha256": _sha256(Path(str(mdl_file.get("path")))) if mdl_file.get("path") else None,
            }
            for mdl_file in mdl_files
        ],
        "wrapper_stage": str(wrapper_stage),
        "wrapper_stage_exists": wrapper_stage.is_file(),
        "hash_sha256": _sha256(wrapper_stage),
        "material_path": spec["material_path"],
        "target_prim_path": spec["target_prim_path"],
        "wrapper_strategy": "standalone_bound_stage_with_absolute_official_mdl_source_asset",
        "ready_for_baseline_conversion": wrapper_stage.is_file(),
    }


def author_supplemental_wrapper_manifest(
    candidate_manifest: dict[str, Any],
    *,
    output_root: Path = DEFAULT_FIXTURE_ROOT,
    generated_at_utc: str | None = None,
    generator_git_commit: str | None = None,
) -> dict[str, Any]:
    candidates = _candidate_by_id(candidate_manifest)
    wrappers: list[dict[str, Any]] = []
    unsupported_recommendations: list[dict[str, str]] = []

    for recommendation in candidate_manifest.get("recommendations", []):
        candidate_id = str(recommendation.get("candidate_id") or "")
        candidate = candidates.get(candidate_id)
        if not candidate:
            unsupported_recommendations.append(
                {"candidate_id": candidate_id, "effect": str(recommendation.get("effect") or "")}
            )
            continue
        wrapper = _author_wrapper(recommendation, candidate, output_root)
        if wrapper:
            wrappers.append(wrapper)
        else:
            unsupported_recommendations.append(
                {"candidate_id": candidate_id, "effect": str(recommendation.get("effect") or "")}
            )

    authored_effects = {wrapper["effect"] for wrapper in wrappers if wrapper.get("wrapper_stage_exists")}
    required_effects = [
        effect
        for effect in (candidate_manifest.get("summary") or {}).get("missing_effects", EXPECTED_EFFECTS)
        if effect in EXPECTED_EFFECTS
    ]
    missing_recommended_effects = [effect for effect in required_effects if effect not in authored_effects]

    blockers: list[str] = []
    if missing_recommended_effects or unsupported_recommendations:
        blockers.append("supplemental_missing_recommended_wrapper_specs")
    if wrappers:
        blockers.append("supplemental_baseline_conversions_not_run")

    ready_for_baseline_conversion = bool(wrappers) and not missing_recommended_effects and not unsupported_recommendations

    return {
        "schema_version": 1,
        "status": "supplemental_wrapper_stage_manifest",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/author_supplemental_wrapper_stages.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "generator_git_commit": generator_git_commit or _git_commit(),
        "summary": {
            "wrapper_stage_count": len(wrappers),
            "authored_wrapper_stage_count": sum(1 for wrapper in wrappers if wrapper.get("wrapper_stage_exists")),
            "missing_recommended_effects": missing_recommended_effects,
            "unsupported_recommendation_count": len(unsupported_recommendations),
            "ready_for_baseline_conversion": ready_for_baseline_conversion,
            "blockers": blockers,
        },
        "wrappers": wrappers,
        "unsupported_recommendations": unsupported_recommendations,
        "claim_boundary": {
            "allowed": [
                "Repo-resident wrapper stages now bind the selected official/sample MDL sources to renderable targets.",
                "These wrapper stages can be used as inputs for supplemental original/noMDL/NVIDIA conversion runs.",
            ],
            "forbidden": [
                "Do not count these wrappers as completed baseline samples until conversion manifests exist.",
                "Do not claim visual quality for clearcoat/procedural bins until rendered evidence is reviewed.",
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-manifest", type=Path, default=DEFAULT_CANDIDATE_MANIFEST)
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURE_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    candidate_manifest = _load_json(args.candidate_manifest)
    manifest = author_supplemental_wrapper_manifest(
        candidate_manifest,
        output_root=args.fixture_root,
    )
    manifest["inputs"] = {
        "candidate_manifest": {
            "path": str(args.candidate_manifest),
            "hash_sha256": _sha256(args.candidate_manifest),
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
        f"Wrote {args.out} wrappers={manifest['summary']['wrapper_stage_count']} "
        f"ready_for_baseline_conversion={manifest['summary']['ready_for_baseline_conversion']}"
    )
    return 0 if manifest["summary"]["ready_for_baseline_conversion"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
