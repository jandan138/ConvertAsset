#!/usr/bin/env python3
"""Check ACL manuscript numbers against local evidence artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Mapping


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_decimal(value: float, digits: int) -> str:
    return f"{value:.{digits}f}"


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def row_by_id(rows: list[dict[str, str]], field: str, value: str) -> dict[str, str]:
    matches = [row for row in rows if row.get(field) == value]
    if len(matches) != 1:
        raise ValueError(f"expected one {field}={value!r}, found {len(matches)}")
    return matches[0]


def normalize_text(text: str) -> str:
    text = re.sub(r"(?m)%.*$", "", text)
    text = text.replace(r"\_", "_").replace(r"\,", " ")
    text = re.sub(r"\\cite\w*(?:\[[^\]]*\])*\{[^}]*\}", " ", text)
    text = re.sub(r"\\ref\{[^}]*\}", " ", text)
    text = re.sub(r"\\label\{[^}]*\}", " ", text)
    text = re.sub(r"\\input\{[^}]*\}", " ", text)
    text = re.sub(r"\\(?:begin|end)\{[^}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def load_acl_numeric_texts(paper_root: Path) -> dict[str, str]:
    venue_root = paper_root / "venues" / "acl27"
    paths = sorted((venue_root / "sections").glob("*.tex"))
    paths.append(paper_root / "shared" / "sections" / "appendix.tex")
    paths.append(venue_root / "OPENREVIEW_METADATA_PACKET.md")
    return {
        str(path.relative_to(paper_root)): normalize_text(
            path.read_text(encoding="utf-8")
        )
        for path in paths
    }


def build_evidence_snapshot(paper_root: Path) -> dict[str, object]:
    evidence_root = paper_root / "shared" / "evidence"
    raw_root = evidence_root / "raw"
    table_root = paper_root / "shared" / "tables"

    image_rows = read_csv_rows(raw_root / "image_quality.csv")
    feature_rows = read_csv_rows(raw_root / "feature_similarity.csv")
    stats = read_json(raw_root / "statistical_tests.json")
    assert isinstance(stats, dict)

    proxy = {
        "asset_count": len({row["scene_id"] for row in image_rows}),
        "render_pair_count": len(image_rows),
        "feature_pair_count": len(feature_rows),
        "psnr": fmt_decimal(float(stats["psnr_mean"]), 2),
        "ssim": fmt_decimal(float(stats["ssim_mean"]), 3),
        "lpips": fmt_decimal(float(stats["lpips_mean"]), 3),
        "clip": fmt_decimal(float(stats["clip_cosine_mean"]), 3),
        "dinov2": fmt_decimal(float(stats["dino_cosine_mean"]), 3),
    }

    clean_rows = read_csv_rows(table_root / "grscenes_vlm_clean_pool_pass15.csv")
    gemma_clean = row_by_id(clean_rows, "row_id", "gemma4_clean_pool_pass15")
    qwen_clean = row_by_id(
        clean_rows,
        "row_id",
        "qwen25_clean_pool_pass15_structured",
    )

    stress_rows = read_csv_rows(table_root / "grscenes_vlm_stress_expanded30.csv")
    gemma_stress = row_by_id(stress_rows, "row_id", "gemma4_expanded30")
    qwen_stress = row_by_id(stress_rows, "row_id", "qwen25_expanded30")

    internnav = read_json(
        raw_root
        / "internnav_vln_downstream"
        / "official_val_unseen_99"
        / "paired_99_summary.json"
    )
    assert isinstance(internnav, dict)
    metrics = internnav["metrics"]

    def paired_metric(metric: str) -> str:
        entry = metrics[metric]
        return (
            f"{float(entry['original_mean']):.4f}/"
            f"{float(entry['modified_mean']):.4f}"
        )

    performance_rows = read_csv_rows(table_root / "official_scene_performance_summary.csv")
    aggregate_rows = [row for row in performance_rows if row["row_type"] == "aggregate"]
    stability_summary = read_json(
        raw_root
        / "official_scene_submission_closure"
        / "official_scene_submission_closure_summary.json"
    )
    assert isinstance(stability_summary, dict)

    coord_rows = read_csv_rows(table_root / "vlm_coordinate_baselines.csv")
    image_center = row_by_id(coord_rows, "baseline_id", "image_center_pixel")
    bbox_pixel = row_by_id(coord_rows, "baseline_id", "bbox_center_pixel")
    bbox_norm = row_by_id(coord_rows, "baseline_id", "bbox_center_normalized_1000")

    return {
        "proxy": proxy,
        "clean_pool": {
            "pair_count": int(gemma_clean["pair_count"]),
            "gemma_answer_original": gemma_clean["answer_original"],
            "gemma_answer_converted": gemma_clean["answer_converted"],
            "gemma_norm_original": gemma_clean["norm1000_point_original"],
            "gemma_norm_converted": gemma_clean["norm1000_point_converted"],
            "qwen_answer_rows": qwen_clean["answer_rows"],
            "qwen_raw_original": qwen_clean["raw_point_original"],
            "qwen_raw_converted": qwen_clean["raw_point_converted"],
            "qwen_norm_original": qwen_clean["norm1000_point_original"],
            "qwen_norm_converted": qwen_clean["norm1000_point_converted"],
        },
        "stress": {
            "pair_count": int(gemma_stress["pair_count"]),
            "gemma_answer_original": gemma_stress["answer_original"],
            "gemma_answer_converted": gemma_stress["answer_converted"],
            "gemma_norm_original": gemma_stress["norm1000_point_original"],
            "gemma_norm_converted": gemma_stress["norm1000_point_converted"],
            "gemma_pair_agreement": gemma_stress["norm1000_pair_hit_agreement"],
            "qwen_raw_original": qwen_stress["raw_point_original"],
            "qwen_raw_converted": qwen_stress["raw_point_converted"],
            "qwen_norm_original": qwen_stress["norm1000_point_original"],
            "qwen_norm_converted": qwen_stress["norm1000_point_converted"],
        },
        "internnav": {
            "episode_count": int(internnav["episode_count"]),
            "official_scene_count": int(internnav["official_scene_count"]),
            "SR": paired_metric("SR"),
            "SPL": paired_metric("SPL"),
            "NE": paired_metric("NE"),
            "TL": paired_metric("TL"),
        },
        "official_scene_stability": {
            "success_total": sum(int(row["success_count"]) for row in aggregate_rows),
            "failure_total": sum(int(row["failure_count"]) for row in aggregate_rows),
            "aggregate_condition_count": len(aggregate_rows),
            "complete_required_condition_count": int(
                stability_summary["performance_summary"][
                    "complete_required_condition_count"
                ]
            ),
        },
        "coordinate_baselines": {
            "image_center_raw_original": image_center["raw_point_original"],
            "image_center_raw_converted": image_center["raw_point_converted"],
            "bbox_pixel_raw_original": bbox_pixel["raw_point_original"],
            "bbox_pixel_raw_converted": bbox_pixel["raw_point_converted"],
            "bbox_norm_norm_original": bbox_norm["norm1000_point_original"],
            "bbox_norm_norm_converted": bbox_norm["norm1000_point_converted"],
        },
        "source_consistency": {
            "recomputed_psnr": fmt_decimal(
                mean([float(row["psnr"]) for row in image_rows]),
                2,
            ),
            "recomputed_ssim": fmt_decimal(
                mean([float(row["ssim"]) for row in image_rows]),
                3,
            ),
            "recomputed_lpips": fmt_decimal(
                mean([float(row["lpips"]) for row in image_rows]),
                3,
            ),
            "recomputed_clip": fmt_decimal(
                mean([float(row["clip_cosine"]) for row in feature_rows]),
                3,
            ),
            "recomputed_dinov2": fmt_decimal(
                mean([float(row["dino_cosine"]) for row in feature_rows]),
                3,
            ),
        },
    }


def build_required_text_markers(snapshot: Mapping[str, object]) -> list[dict[str, object]]:
    proxy = snapshot["proxy"]
    clean = snapshot["clean_pool"]
    stress = snapshot["stress"]
    internnav = snapshot["internnav"]
    stability = snapshot["official_scene_stability"]
    coords = snapshot["coordinate_baselines"]

    return [
        {
            "claim_id": "proxy_scope",
            "markers": [
                "four single-object",
                f"{proxy['render_pair_count']} matched pairs",
            ],
        },
        {
            "claim_id": "proxy_psnr",
            "markers": [f"{proxy['psnr']} dB"],
        },
        {
            "claim_id": "proxy_visual_feature_metrics",
            "markers": [
                f"SSIM {proxy['ssim']}",
                f"LPIPS {proxy['lpips']}",
                f"CLIP {proxy['clip']}",
                f"DINOv2 {proxy['dinov2']}",
            ],
        },
        {
            "claim_id": "clean_pool_numbers",
            "markers": [
                f"{clean['pair_count']} source/noMDL pairs",
                f"point hits of {clean['gemma_norm_original']} original",
                f"{clean['gemma_norm_converted']} converted",
                f"{clean['qwen_answer_rows']} scorable answer rows",
                f"raw point hits of {clean['qwen_raw_original']}",
                f"{clean['qwen_raw_converted']}",
            ],
        },
        {
            "claim_id": "stress_gemma_numbers",
            "markers": [
                f"keeps all {stress['gemma_answer_original'].split('/')[0]} target labels",
                f"scores {stress['gemma_norm_original']} point hits",
                f"{stress['gemma_norm_converted']} on converted",
                f"{stress['gemma_pair_agreement'].split('/')[0]} pairs keep",
            ],
        },
        {
            "claim_id": "stress_qwen_numbers",
            "markers": [
                f"raw-pixel hits are {stress['qwen_raw_original']} original",
                f"{stress['qwen_raw_converted']} converted",
                f"normalized-1000 hits stay {stress['qwen_norm_original']} for both",
            ],
        },
        {
            "claim_id": "internnav_scope",
            "markers": [
                f"{internnav['episode_count']} paired",
                "three local scenes",
            ],
        },
        {
            "claim_id": "internnav_sr_spl_ne_tl",
            "markers": [
                f"SR {internnav['SR']}",
                f"SPL {internnav['SPL']}",
                f"NE {internnav['NE']}",
                f"TL {internnav['TL']}",
            ],
        },
        {
            "claim_id": "official_scene_stability",
            "markers": [
                f"{stability['success_total']} required paired runs",
                f"({stability['success_total']}/{stability['success_total']})",
            ],
        },
        {
            "claim_id": "coordinate_baselines",
            "markers": [
                f"score {coords['image_center_raw_original']} under raw point-in-box",
                "normalized-1000 bbox-center oracle",
            ],
        },
    ]


def find_source_consistency_violations(
    snapshot: Mapping[str, object]
) -> list[dict[str, str]]:
    proxy = snapshot["proxy"]
    recomputed = snapshot["source_consistency"]
    checks = {
        "psnr": "recomputed_psnr",
        "ssim": "recomputed_ssim",
        "lpips": "recomputed_lpips",
        "clip": "recomputed_clip",
        "dinov2": "recomputed_dinov2",
    }
    violations = []
    for field, recomputed_field in checks.items():
        if proxy[field] != recomputed[recomputed_field]:
            violations.append(
                {
                    "claim_id": f"source_{field}",
                    "expected": str(recomputed[recomputed_field]),
                    "observed": str(proxy[field]),
                }
            )
    return violations


def find_text_marker_violations(
    text_by_path: Mapping[str, str],
    required_markers: list[dict[str, object]],
) -> list[dict[str, str]]:
    combined = " ".join(normalize_text(text) for text in text_by_path.values()).lower()
    violations: list[dict[str, str]] = []
    for claim in required_markers:
        for marker in claim["markers"]:
            marker_text = str(marker).lower()
            if marker_text not in combined:
                violations.append(
                    {
                        "claim_id": str(claim["claim_id"]),
                        "missing_marker": str(marker),
                    }
                )
    return violations


def check_acl_evidence_numbers(paper_root: Path) -> dict[str, object]:
    snapshot = build_evidence_snapshot(paper_root)
    text_by_path = load_acl_numeric_texts(paper_root)
    required_markers = build_required_text_markers(snapshot)
    violations = [
        *find_source_consistency_violations(snapshot),
        *find_text_marker_violations(text_by_path, required_markers),
    ]
    return {
        "ok": not violations,
        "checked_files": sorted(text_by_path),
        "snapshot": snapshot,
        "required_markers": required_markers,
        "violations": violations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paper-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Path to the paper root directory.",
    )
    args = parser.parse_args(argv)

    report = check_acl_evidence_numbers(args.paper_root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
