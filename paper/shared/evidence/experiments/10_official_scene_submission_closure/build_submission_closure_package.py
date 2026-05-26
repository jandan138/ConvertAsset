#!/usr/bin/env python3
"""Build the official-scene submission-closure evidence package.

This script is intentionally pure Python. It audits already-synced official
InternNav evidence, selected qualitative video assets, and optional official
scene performance-run CSVs without importing Isaac Sim or pxr.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_ROOT = PROJECT_ROOT / "paper/shared/evidence/raw"
TABLE_ROOT = PROJECT_ROOT / "paper/shared/tables"
INTERNNAV_ROOT = RAW_ROOT / "internnav_vln_downstream"
OUTPUT_ROOT = RAW_ROOT / "official_scene_submission_closure"

DEFAULT_PER_SCENE_SUMMARY = INTERNNAV_ROOT / "official_val_unseen_99/per_scene_aggregate_summary.json"
DEFAULT_STATIC_GATE_0036_0066 = INTERNNAV_ROOT / "official_val_unseen_99/nomdl_static_gate_0036_0066.json"
DEFAULT_VIDEO_PACKAGE_INDEX = INTERNNAV_ROOT / "official_selected_qualitative_videos/package_index.json"
DEFAULT_PERFORMANCE_CSV = OUTPUT_ROOT / "official_scene_performance_runs.csv"

DEFAULT_SUMMARY_JSON = OUTPUT_ROOT / "official_scene_submission_closure_summary.json"
DEFAULT_PERFORMANCE_PLAN_JSON = OUTPUT_ROOT / "official_scene_performance_plan.json"
DEFAULT_VIDEO_SUMMARY_JSON = OUTPUT_ROOT / "official_scene_video_evidence_summary.json"
DEFAULT_CLAIM_AUDIT_JSON = OUTPUT_ROOT / "official_scene_claim_audit_checklist.json"
DEFAULT_STATUS_CSV = TABLE_ROOT / "official_scene_submission_closure_status.csv"
DEFAULT_STATUS_TEX = TABLE_ROOT / "tab_official_scene_submission_closure_status.tex"

DEFAULT_SCENE_PATHS = {
    "kujiale_0031": {
        "original_mdl": (
            "/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525/"
            "interiornav_data/scene_data/kujiale_0031/kujiale_0031.usda"
        ),
        "convertasset_nomdl": (
            "/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/"
            "scene_data_nomdl/kujiale_0031/kujiale_0031.usda"
        ),
    },
    "kujiale_0036": {
        "original_mdl": (
            "/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/"
            "official/internnav_official_val_unseen_20260525/interiornav_data/"
            "scene_data/kujiale_0036/kujiale_0036.usda"
        ),
        "convertasset_nomdl": (
            "/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/"
            "official/internnav_official_val_unseen_20260525/scene_data_nomdl/"
            "kujiale_0036/kujiale_0036.usda"
        ),
    },
    "kujiale_0066": {
        "original_mdl": (
            "/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/"
            "official/internnav_official_val_unseen_20260525/interiornav_data/"
            "scene_data/kujiale_0066/kujiale_0066.usda"
        ),
        "convertasset_nomdl": (
            "/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/"
            "official/internnav_official_val_unseen_20260525/scene_data_nomdl/"
            "kujiale_0066/kujiale_0066.usda"
        ),
    },
}

REQUIRED_PERFORMANCE_CONDITIONS = ("original_mdl", "convertasset_nomdl")


def load_json(path: Path, *, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    mu = sum(values) / len(values)
    return math.sqrt(sum((value - mu) ** 2 for value in values) / (len(values) - 1))


def bootstrap_mean_ci(values: list[float], *, rounds: int = 1000, seed: int = 20260526) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "ci95_low": None, "ci95_high": None}
    if len(set(values)) == 1:
        value = round(values[0], 4)
        return {"mean": value, "ci95_low": value, "ci95_high": value}
    rng = random.Random(seed)
    samples = []
    n = len(values)
    for _ in range(rounds):
        samples.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    samples.sort()
    low_index = int(0.025 * (rounds - 1))
    high_index = int(0.975 * (rounds - 1))
    return {
        "mean": round(sum(values) / len(values), 4),
        "ci95_low": round(samples[low_index], 4),
        "ci95_high": round(samples[high_index], 4),
    }


def _condition_record(status: str, *, path: str | None = None, reason: str | None = None, static_gate_pass: Any = None) -> dict[str, Any]:
    record: dict[str, Any] = {"status": status}
    if path:
        record["stage_path"] = path
        record["path_exists"] = Path(path).exists()
    if reason:
        record["reason"] = reason
    if static_gate_pass is not None:
        record["static_gate_pass"] = static_gate_pass
    return record


def _static_gate_by_scene(static_gate_0036_0066: dict[str, Any]) -> dict[str, bool]:
    by_scene: dict[str, bool] = {}
    for result in static_gate_0036_0066.get("results", []):
        scene_path = str(result.get("scene_usd", ""))
        for scene_id in ("kujiale_0031", "kujiale_0036", "kujiale_0066"):
            if scene_id in scene_path:
                by_scene[scene_id] = bool(result.get("static_gate_pass"))
    by_scene.setdefault("kujiale_0031", True)
    return by_scene


def build_scene_inventory(
    *,
    per_scene_summary: dict[str, Any],
    static_gate_0036_0066: dict[str, Any],
    path_overrides: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    path_map = {scene_id: dict(paths) for scene_id, paths in DEFAULT_SCENE_PATHS.items()}
    if path_overrides:
        for scene_id, overrides in path_overrides.items():
            path_map.setdefault(scene_id, {}).update(overrides)

    static_by_scene = _static_gate_by_scene(static_gate_0036_0066)
    per_scene = per_scene_summary.get("per_scene", {})
    scene_order = per_scene_summary.get("scene_order") or sorted(per_scene)

    inventory = []
    for scene_id in scene_order:
        paths = path_map.get(scene_id, {})
        episode_count = per_scene.get(scene_id, {}).get("episode_count")
        conditions = {
            "original_mdl": _condition_record("planned", path=paths.get("original_mdl")),
            "convertasset_nomdl": _condition_record(
                "planned",
                path=paths.get("convertasset_nomdl"),
                static_gate_pass=static_by_scene.get(scene_id),
            ),
            "nvidia_baseline": _condition_record(
                "not_available",
                reason="no_official_scene_nvidia_conversion_yet",
            ),
        }
        inventory.append(
            {
                "scene_id": scene_id,
                "episode_count": episode_count,
                "scene_family": "official_kujiale_interioragent",
                "conditions": conditions,
            }
        )
    return inventory


def build_video_evidence_summary(package_index: dict[str, Any]) -> dict[str, Any]:
    counts = package_index.get("file_counts_excluding_package_index", {})
    groups = package_index.get("groups", [])
    qa_pass_count = sum(int(group.get("qa_pass_count", 0)) for group in groups)
    video_count = sum(int(group.get("video_count", 0)) for group in groups)
    all_groups_nonblank = all(bool(group.get("all_videos_pass_basic_nonblank_check")) for group in groups) if groups else False
    complete = video_count > 0 and qa_pass_count == video_count and all_groups_nonblank
    return {
        "video_package_complete": complete,
        "group_count": len(groups),
        "group_ids": [group.get("group_id") for group in groups],
        "mp4_count": int(counts.get("mp4", 0)),
        "png_count": int(counts.get("png", 0)),
        "json_count": int(counts.get("json", 0)),
        "total_files": int(counts.get("total_files", 0)),
        "video_count": video_count,
        "qa_pass_count": qa_pass_count,
        "all_videos_pass_basic_nonblank_check": all_groups_nonblank,
        "size_bytes": package_index.get("size_bytes_excluding_package_index"),
        "claim_boundary": "selected_qualitative_only_full_metric_runs_authoritative",
    }


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _load_performance_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _metric_stats(values: list[float], *, ci_rounds: int, seed: int) -> dict[str, Any]:
    ci = bootstrap_mean_ci(values, rounds=ci_rounds, seed=seed)
    return {
        "mean": ci["mean"],
        "std": round(sample_std(values), 4) if values else None,
        "ci95_low": ci["ci95_low"],
        "ci95_high": ci["ci95_high"],
    }


def summarize_performance_rows(
    rows: list[dict[str, Any]],
    *,
    min_successful_runs: int = 3,
    planned_scene_count: int | None = None,
    ci_rounds: int = 1000,
) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    failures: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (str(row.get("scene_id", "")), str(row.get("condition", "")))
        if not key[0] or not key[1]:
            continue
        if row.get("status") == "success":
            grouped.setdefault(key, []).append(row)
        else:
            failures[key] = failures.get(key, 0) + 1

    keys = sorted(set(grouped) | set(failures))
    summary_rows = []
    for index, key in enumerate(keys):
        scene_id, condition = key
        success_rows = grouped.get(key, [])
        warmup_fps_values = []
        for row in success_rows:
            warmup_s = _float_or_none(row.get("warmup_s"))
            warmup_updates = _float_or_none(row.get("warmup_updates"))
            if warmup_s and warmup_updates:
                warmup_fps_values.append(warmup_updates / warmup_s)

        metric_values = {
            "open_ready_s": [_float_or_none(row.get("open_ready_s")) for row in success_rows],
            "warmup_s": [_float_or_none(row.get("warmup_s")) for row in success_rows],
            "total_ready_s": [_float_or_none(row.get("total_ready_s")) for row in success_rows],
            "gpu_memory_mb": [_float_or_none(row.get("gpu_memory_mb")) for row in success_rows],
            "warmup_fps": warmup_fps_values,
        }
        metric_values = {
            metric: [value for value in values if value is not None]
            for metric, values in metric_values.items()
        }

        output: dict[str, Any] = {
            "scene_id": scene_id,
            "condition": condition,
            "success_count": len(success_rows),
            "failure_count": failures.get(key, 0),
            "min_successful_runs_required": min_successful_runs,
            "complete_for_condition": len(success_rows) >= min_successful_runs,
        }
        for metric, values in metric_values.items():
            stats = _metric_stats(values, ci_rounds=ci_rounds, seed=20260526 + index)
            output[f"{metric}_mean"] = stats["mean"]
            output[f"{metric}_std"] = stats["std"]
            output[f"{metric}_ci95_low"] = stats["ci95_low"]
            output[f"{metric}_ci95_high"] = stats["ci95_high"]
        summary_rows.append(output)

    covered_required = {
        (row["scene_id"], row["condition"])
        for row in summary_rows
        if row["condition"] in REQUIRED_PERFORMANCE_CONDITIONS and row["complete_for_condition"]
    }
    scenes = {row["scene_id"] for row in summary_rows}
    required_count = (planned_scene_count or len(scenes)) * len(REQUIRED_PERFORMANCE_CONDITIONS)
    return {
        "schema_version": 1,
        "performance_complete": len(covered_required) >= required_count and required_count > 0,
        "min_successful_runs_required": min_successful_runs,
        "planned_scene_count": planned_scene_count,
        "required_condition_count": required_count,
        "complete_required_condition_count": len(covered_required),
        "rows": summary_rows,
    }


def build_claim_audit_checklist() -> dict[str, Any]:
    checks = [
        {
            "id": "official_scene_scope",
            "status": "pending_final_audit",
            "rule": "Say official KuJiaLe / InteriorAgent scenes, not broad GRScenes/R2R/MP3D benchmark.",
        },
        {
            "id": "performance_scope",
            "status": "pending_performance_runs",
            "rule": "Only claim multi-scene performance after official-scene repeated runs exist.",
        },
        {
            "id": "video_scope",
            "status": "ready_with_boundary",
            "rule": "Use selected videos as qualitative evidence only; full metric runs remain authoritative.",
        },
        {
            "id": "nvidia_scope",
            "status": "pending_or_not_available",
            "rule": "Do not imply an official-scene NVIDIA baseline unless those converted scenes are generated and benchmarked.",
        },
        {
            "id": "material_effect_scope",
            "status": "ready_with_boundary",
            "rule": "Keep clearcoat selected-failure and procedural-texture limitation language.",
        },
        {
            "id": "citation_provenance",
            "status": "pending_final_audit",
            "rule": "Verify official InternNav / InteriorAgent / KuJiaLe provenance and target venue citations.",
        },
    ]
    return {
        "schema_version": 1,
        "claim_audit_complete": False,
        "checks": checks,
        "claim_boundary": "audit_checklist_not_final_submission_approval",
    }


def build_completion_gates(
    *,
    scene_inventory: list[dict[str, Any]],
    performance_summary: dict[str, Any],
    video_summary: dict[str, Any],
    claim_audit: dict[str, Any],
) -> dict[str, Any]:
    official_scope_ready = len(scene_inventory) >= 3 and all(
        scene.get("conditions", {}).get(condition, {}).get("status") == "planned"
        for scene in scene_inventory
        for condition in REQUIRED_PERFORMANCE_CONDITIONS
    )
    gates = {
        "official_scene_scope": "ready" if official_scope_ready else "missing",
        "multi_run_performance_statistics": "ready" if performance_summary.get("performance_complete") else "missing",
        "selected_video_package": "ready" if video_summary.get("video_package_complete") else "missing",
        "final_claim_citation_audit": "ready" if claim_audit.get("claim_audit_complete") else "missing",
    }
    gates["submission_closure_complete"] = all(status == "ready" for status in gates.values())
    return gates


def build_status_rows(
    *,
    gates: dict[str, Any],
    performance_csv: Path,
    video_package_index: Path,
    claim_audit_path: Path,
) -> list[dict[str, str]]:
    evidence_by_requirement = {
        "official_scene_scope": repo_path(DEFAULT_PERFORMANCE_PLAN_JSON),
        "multi_run_performance_statistics": repo_path(performance_csv),
        "selected_video_package": repo_path(video_package_index),
        "final_claim_citation_audit": repo_path(claim_audit_path),
    }
    boundary_by_requirement = {
        "official_scene_scope": "official KuJiaLe / InteriorAgent only",
        "multi_run_performance_statistics": "requires repeated official-scene runs before paper claim",
        "selected_video_package": "selected qualitative only; full metric runs authoritative",
        "final_claim_citation_audit": "not complete until title/abstract/body/citations are checked",
    }
    return [
        {
            "requirement": requirement,
            "status": str(status),
            "evidence": evidence_by_requirement[requirement],
            "claim_boundary": boundary_by_requirement[requirement],
        }
        for requirement, status in gates.items()
        if requirement != "submission_closure_complete"
    ]


def _latex_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("#", "\\#")
    )


def write_status_table(csv_path: Path, tex_path: Path, rows: list[dict[str, Any]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["requirement", "status", "evidence", "claim_boundary"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    tex_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        "\\resizebox{\\linewidth}{!}{%",
        "\\begin{tabular}{llll}",
        "\\toprule",
        "Requirement & Status & Evidence & Claim boundary \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{_latex_escape(row['requirement'])} & {_latex_escape(row['status'])} & "
            f"{_latex_escape(row['evidence'])} & {_latex_escape(row['claim_boundary'])} \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}%",
            "}",
            "\\caption{Official-scene submission closure status. The package tracks the official KuJiaLe / InteriorAgent performance, video, and final claim-audit gates.}",
            "\\label{tab:official_scene_submission_closure_status}",
            "\\end{table}",
            "",
        ]
    )
    tex_path.write_text("\n".join(lines), encoding="utf-8")


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    per_scene_summary = load_json(Path(args.per_scene_summary))
    static_gate = load_json(Path(args.static_gate_0036_0066), default={"results": []})
    video_package_index = load_json(Path(args.video_package_index), default={})
    performance_csv = Path(args.performance_csv)

    scene_inventory = build_scene_inventory(
        per_scene_summary=per_scene_summary,
        static_gate_0036_0066=static_gate,
    )
    video_summary = build_video_evidence_summary(video_package_index)
    performance_rows = _load_performance_rows(performance_csv)
    performance_summary = summarize_performance_rows(
        performance_rows,
        min_successful_runs=args.min_successful_runs,
        planned_scene_count=len(scene_inventory),
    )
    claim_audit = build_claim_audit_checklist()
    gates = build_completion_gates(
        scene_inventory=scene_inventory,
        performance_summary=performance_summary,
        video_summary=video_summary,
        claim_audit=claim_audit,
    )
    status_rows = build_status_rows(
        gates=gates,
        performance_csv=performance_csv,
        video_package_index=Path(args.video_package_index),
        claim_audit_path=Path(args.claim_audit_json),
    )

    performance_plan = {
        "schema_version": 1,
        "scene_inventory": scene_inventory,
        "required_conditions": list(REQUIRED_PERFORMANCE_CONDITIONS),
        "optional_conditions": ["nvidia_baseline"],
        "runs_per_scene_condition": args.min_successful_runs,
        "performance_csv": repo_path(performance_csv),
        "nvidia_baseline_policy": "include only if official-scene NVIDIA conversions are generated and smoke-gated",
    }
    summary = {
        "schema_version": 1,
        "goal": "official_scene_submission_closure_package",
        "scene_inventory": scene_inventory,
        "performance_summary": performance_summary,
        "video_summary": video_summary,
        "claim_audit": claim_audit,
        "completion_gates": gates,
        "status_table": repo_path(Path(args.status_csv)),
        "status_tex": repo_path(Path(args.status_tex)),
    }

    write_json(Path(args.performance_plan_json), performance_plan)
    write_json(Path(args.video_summary_json), video_summary)
    write_json(Path(args.claim_audit_json), claim_audit)
    write_json(Path(args.summary_json), summary)
    write_status_table(Path(args.status_csv), Path(args.status_tex), status_rows)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-scene-summary", default=str(DEFAULT_PER_SCENE_SUMMARY))
    parser.add_argument("--static-gate-0036-0066", default=str(DEFAULT_STATIC_GATE_0036_0066))
    parser.add_argument("--video-package-index", default=str(DEFAULT_VIDEO_PACKAGE_INDEX))
    parser.add_argument("--performance-csv", default=str(DEFAULT_PERFORMANCE_CSV))
    parser.add_argument("--summary-json", default=str(DEFAULT_SUMMARY_JSON))
    parser.add_argument("--performance-plan-json", default=str(DEFAULT_PERFORMANCE_PLAN_JSON))
    parser.add_argument("--video-summary-json", default=str(DEFAULT_VIDEO_SUMMARY_JSON))
    parser.add_argument("--claim-audit-json", default=str(DEFAULT_CLAIM_AUDIT_JSON))
    parser.add_argument("--status-csv", default=str(DEFAULT_STATUS_CSV))
    parser.add_argument("--status-tex", default=str(DEFAULT_STATUS_TEX))
    parser.add_argument("--min-successful-runs", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    summary = build_package(parse_args())
    print(f"Wrote {repo_path(DEFAULT_SUMMARY_JSON)}")
    print(f"Submission closure complete: {summary['completion_gates']['submission_closure_complete']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
