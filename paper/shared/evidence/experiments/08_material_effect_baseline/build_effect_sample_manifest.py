#!/usr/bin/env python3
"""Build a material-effect sample manifest for ConvertAsset vs NVIDIA baseline runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_ROOT = PROJECT_ROOT / "paper/shared/evidence/raw"
GRSCENES_RAW = RAW_ROOT / "grscene_vlm_grounding"
DEFAULT_MATERIAL_CLOSURE = GRSCENES_RAW / "material_dependency_closure_plan.json"
DEFAULT_STRESS_MANIFEST = GRSCENES_RAW / "stress_vlm_run_manifest_expanded30.json"
DEFAULT_OUTPUT = RAW_ROOT / "material_effect_baseline/effect_sample_manifest.json"

EFFECT_ORDER = [
    "clearcoat",
    "opacity_transparency",
    "emission",
    "procedural_texture",
    "normal_bump",
    "displacement_height",
]

EFFECT_LABELS = {
    "clearcoat": "clearcoat / coating",
    "opacity_transparency": "opacity / transparency / refraction",
    "emission": "emission / self illumination",
    "procedural_texture": "procedural texture",
    "normal_bump": "normal / bump",
    "displacement_height": "displacement / height",
}


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


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return ""


def _add_evidence(bucket: dict[str, Any], effect: str, evidence: str) -> None:
    entry = bucket[effect]
    entry["present"] = True
    if evidence not in entry["evidence"]:
        entry["evidence"].append(evidence)


def _float_literals(pattern: str, text: str) -> list[float]:
    values: list[float] = []
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        try:
            values.append(float(match.group(1)))
        except (TypeError, ValueError):
            continue
    return values


def _color_is_nonzero(match: re.Match[str]) -> bool:
    channels = match.groups()
    try:
        return any(float(channel) > 1e-4 for channel in channels)
    except ValueError:
        return False


def detect_material_effects(mdl_paths: list[Path]) -> dict[str, dict[str, Any]]:
    """Return stable material-effect labels from a bounded set of MDL files."""

    effects = {
        key: {"present": False, "label": EFFECT_LABELS[key], "evidence": []}
        for key in EFFECT_ORDER
    }
    for path in mdl_paths:
        text = _read_text(path)
        lowered = text.lower()
        name = path.name

        if re.search(r"\b(clearcoat|clear_coat|coat_roughness|coat_weight)\b", lowered):
            _add_evidence(effects, "clearcoat", f"{name}: clearcoat/coating token")

        opacity_values = _float_literals(r"\b(?:float\s+)?(?:texmap_)?opacity\b\s*[:=]\s*([0-9.]+)\s*f?", text)
        if any(value < 0.999 for value in opacity_values):
            _add_evidence(effects, "opacity_transparency", f"{name}: opacity below 1")
        if re.search(r"\b(omniue4translucent|transparent|transmission|refraction|switchrefraction)\b", lowered):
            _add_evidence(effects, "opacity_transparency", f"{name}: translucent/refraction token")
        if re.search(r"\bthin_walled\s*:\s*true\b", lowered):
            _add_evidence(effects, "opacity_transparency", f"{name}: thin_walled true")

        emissive_values = _float_literals(r"\bemissiveintensity\b\s*=\s*([0-9.]+)\s*f?", text)
        if any(value > 1e-4 for value in emissive_values):
            _add_evidence(effects, "emission", f"{name}: EmissiveIntensity > 0")
        if re.search(r"\b(emissive_color|emissive_tex|emission_tex)\b", lowered):
            _add_evidence(effects, "emission", f"{name}: emissive shader input")
        for match in re.finditer(
            r"\bself_illumination\s*:\s*color\s*\(\s*([0-9.]+)f?\s*,\s*([0-9.]+)f?\s*,\s*([0-9.]+)f?\s*\)",
            text,
            flags=re.IGNORECASE,
        ):
            if _color_is_nonzero(match):
                _add_evidence(effects, "emission", f"{name}: nonzero self_illumination")

        if re.search(r"\b(noise|cellular|checker|procedural|flow_noise|perlin)\s*\(", lowered):
            _add_evidence(effects, "procedural_texture", f"{name}: procedural function token")
        if re.search(r"\b(unpack_normal_map|sampler_normal|normal_tex|texmap_bump|bump|normal\s*:)\b", lowered):
            _add_evidence(effects, "normal_bump", f"{name}: normal/bump token")
        if re.search(r"\b(displacement|worldpositionoffset|height_tex|heightmap|polygonoffset)\b", lowered):
            _add_evidence(effects, "displacement_height", f"{name}: displacement/height token")

    return effects


def _mdl_paths_for_model(model: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for asset in model.get("required_material_assets", []):
        source_path = asset.get("source_path") or asset.get("src")
        if source_path and str(source_path).lower().endswith(".mdl"):
            paths.append(Path(source_path))
    return paths


def _models_by_target_prim(material_closure_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_target: dict[str, dict[str, Any]] = {}
    for model in material_closure_plan.get("models", []):
        mdl_paths = _mdl_paths_for_model(model)
        effects = detect_material_effects(mdl_paths)
        material_model = {
            "model_root": model.get("model_root"),
            "root_asset": model.get("root_asset"),
            "mdl_files": [
                {"path": str(path), "name": path.name, "hash_sha256": _sha256(path)}
                for path in mdl_paths
            ],
            "effects": effects,
        }
        for target in model.get("targets", []):
            target_prim_path = target.get("target_prim_path")
            if not target_prim_path:
                continue
            by_target[str(target_prim_path)] = {
                **material_model,
                "target_prim_path": str(target_prim_path),
                "object_instance_id": target.get("object_instance_id"),
                "object_category": target.get("object_category"),
                "source_scene_id": target.get("source_scene_id"),
            }
    return by_target


def build_effect_sample_manifest(
    material_closure_plan: dict[str, Any],
    stress_manifest: dict[str, Any],
    *,
    generated_at_utc: str | None = None,
    generator_git_commit: str | None = None,
) -> dict[str, Any]:
    models_by_target = _models_by_target_prim(material_closure_plan)
    samples: list[dict[str, Any]] = []
    missing_material_models: list[dict[str, str]] = []
    effect_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    for pair in stress_manifest.get("selected_pairs", []):
        target_prim_path = str(pair.get("target_prim_path") or "")
        material_model = models_by_target.get(target_prim_path)
        if not material_model:
            missing_material_models.append(
                {"pair_id": str(pair.get("pair_id")), "target_prim_path": target_prim_path}
            )
            continue
        effects = material_model["effects"]
        present_effects = [key for key in EFFECT_ORDER if effects[key]["present"]]
        for effect in present_effects:
            effect_counts[effect] += 1
        category = str(pair.get("target_category") or material_model.get("object_category") or "unknown")
        category_counts[category] += 1
        samples.append(
            {
                "sample_id": str(pair.get("pair_id")),
                "pair_id": str(pair.get("pair_id")),
                "source_scene_id": pair.get("source_scene_id") or material_model.get("source_scene_id"),
                "target_category": category,
                "target_id": pair.get("target_id"),
                "source": "grscenes_stress_expanded30",
                "visual_review": pair.get("visual_review"),
                "present_effects": present_effects,
                "effects": effects,
                "material_model": {
                    key: value
                    for key, value in material_model.items()
                    if key not in {"effects"}
                },
                "baseline_plan": {
                    "convertasset_condition": "existing_noMDL",
                    "nvidia_condition": "pending_asset_converter_preview_or_bake",
                    "original_condition": "original_MDL",
                },
            }
        )

    effect_gaps = [effect for effect in EFFECT_ORDER if effect_counts[effect] == 0]
    blockers = []
    if missing_material_models:
        blockers.append("selected_pairs_missing_material_model_link")
    if effect_gaps:
        blockers.append("effect_groups_need_official_sample_or_more_grscenes_assets")

    return {
        "schema_version": 1,
        "status": "effect_sample_manifest_ready",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_sample_manifest.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "generator_git_commit": generator_git_commit or _git_commit(),
        "objective": "Select representative material-effect samples for ConvertAsset vs NVIDIA baseline comparison.",
        "effect_order": EFFECT_ORDER,
        "summary": {
            "sample_count": len(samples),
            "missing_material_model_count": len(missing_material_models),
            "effect_counts": {effect: effect_counts[effect] for effect in EFFECT_ORDER},
            "effect_gaps": effect_gaps,
            "target_category_counts": dict(sorted(category_counts.items())),
            "ready_for_nvidia_baseline_smoke": bool(samples),
            "ready_for_full_claim": False,
            "blockers": blockers,
        },
        "samples": samples,
        "missing_material_models": missing_material_models,
        "claim_boundary": {
            "allowed": [
                "This manifest selects candidate samples for material-effect attribution.",
                "It can support baseline execution planning after NVIDIA conversion smoke succeeds.",
            ],
            "forbidden": [
                "Do not claim ConvertAsset is better than NVIDIA baseline from this manifest alone.",
                "Do not claim all requested effects are covered when effect_gaps is non-empty.",
            ],
        },
        "inputs": {
            "material_closure_status": material_closure_plan.get("status"),
            "stress_manifest_status": stress_manifest.get("status"),
            "stress_pair_count": (stress_manifest.get("summary") or {}).get("stress_pair_count"),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--material-closure", type=Path, default=DEFAULT_MATERIAL_CLOSURE)
    parser.add_argument("--stress-manifest", type=Path, default=DEFAULT_STRESS_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_effect_sample_manifest(
        _load_json(args.material_closure),
        _load_json(args.stress_manifest),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.out} samples={manifest['summary']['sample_count']} "
        f"effect_gaps={','.join(manifest['summary']['effect_gaps']) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
