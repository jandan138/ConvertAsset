#!/usr/bin/env python3
"""Package selected InternNav qualitative videos into the repo evidence tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos"
)
REGISTERED_FIGURE_OUTPUTS = [
    "paper/shared/figures/fig_internnav_rollout_0036_0066_main3.png",
    "paper/shared/figures/fig_internnav_rollout_0036_0066_selected6_supp.png",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _repo_path(path: Path) -> str:
    path = path.resolve()
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_file(source: Path, destination: Path) -> dict[str, Any]:
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "path": _repo_path(destination),
        "source_path": str(source.resolve()),
        "size_bytes": destination.stat().st_size,
        "hash_sha256": _sha256_file(destination),
    }


def _case_by_key(case_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = case_manifest.get("selected_cases", [])
    if not cases:
        raise ValueError("case manifest has no selected_cases")
    return {str(case["path_key"]): case for case in cases}


def _sample_frame_indices(frame_count: int) -> list[tuple[str, int]]:
    if frame_count <= 0:
        return []
    last = max(frame_count - 1, 0)
    return [("start", 0), ("mid", last // 2), ("end", last)]


def _read_frame(cap: cv2.VideoCapture, index: int) -> np.ndarray | None:
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    return frame


def _frame_luma_stats(frame: np.ndarray | None) -> dict[str, Any]:
    if frame is None:
        return {
            "read_ok": False,
            "min_luma": None,
            "max_luma": None,
            "mean_luma": None,
            "std_luma": None,
        }
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return {
        "read_ok": True,
        "min_luma": int(gray.min()),
        "max_luma": int(gray.max()),
        "mean_luma": round(float(gray.mean()), 3),
        "std_luma": round(float(gray.std()), 3),
    }


def _is_nonblank(sample_stats: list[dict[str, Any]]) -> bool:
    readable = [stats for stats in sample_stats if stats.get("read_ok")]
    if not readable:
        return False
    return any(
        float(stats["std_luma"]) > 2.0 and int(stats["max_luma"]) - int(stats["min_luma"]) > 10
        for stats in readable
    )


def _extract_stills(
    *,
    video_path: Path,
    still_dir: Path,
    group_id: str,
    path_key: str,
    condition: str,
    frame_count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    still_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    still_records: list[dict[str, Any]] = []
    manifest_records: list[dict[str, str]] = []
    for label, frame_index in _sample_frame_indices(frame_count):
        frame = _read_frame(cap, frame_index)
        if frame is None:
            still_records.append(
                {
                    "label": label,
                    "frame_index": frame_index,
                    "path": None,
                    "read_ok": False,
                }
            )
            continue
        destination = still_dir / f"{group_id}_{path_key}_{condition}_{label}_{frame_index:06d}.png"
        ok = cv2.imwrite(str(destination), frame)
        if not ok:
            raise RuntimeError(f"failed to write still: {destination}")
        copied = {
            "label": label,
            "frame_index": frame_index,
            "path": _repo_path(destination),
            "size_bytes": destination.stat().st_size,
            "hash_sha256": _sha256_file(destination),
            "read_ok": True,
        }
        still_records.append(copied)
        manifest_records.append({"label": label, "path": _repo_path(destination)})
    cap.release()
    return still_records, manifest_records


def _qa_video(
    *,
    source_video: Path,
    copied_video: Path,
    group_id: str,
    path_key: str,
    condition: str,
    case: dict[str, Any],
    still_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    copied = _copy_file(source_video, copied_video)
    cap = cv2.VideoCapture(str(copied_video))
    opened = bool(cap.isOpened())
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) if opened else 0
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0) if opened else 0.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) if opened else 0
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) if opened else 0
    sample_frames = []
    for label, frame_index in _sample_frame_indices(frame_count):
        frame = _read_frame(cap, frame_index)
        stats = _frame_luma_stats(frame)
        stats.update({"label": label, "frame_index": frame_index})
        sample_frames.append(stats)
    cap.release()

    nonblank = _is_nonblank(sample_frames)
    still_records, still_manifest_records = _extract_stills(
        video_path=copied_video,
        still_dir=still_dir,
        group_id=group_id,
        path_key=path_key,
        condition=condition,
        frame_count=frame_count,
    )
    qa_pass = (
        copied_video.exists()
        and copied_video.stat().st_size > 100_000
        and opened
        and frame_count > 0
        and nonblank
        and all(record.get("read_ok") for record in still_records)
    )
    record = {
        "group_id": group_id,
        "path_key": path_key,
        "condition": condition,
        "case_type": case.get("case_type"),
        "full_run_metrics": case.get("metrics", {}),
        "failure_reason": case.get("failure_reason", {}),
        "source_path": str(source_video.resolve()),
        "path": copied["path"],
        "size_bytes": copied["size_bytes"],
        "hash_sha256": copied["hash_sha256"],
        "opened": opened,
        "frame_count": frame_count,
        "fps_video": round(fps, 3),
        "duration_seconds_video": round(frame_count / fps, 3) if fps > 0 else None,
        "width": width,
        "height": height,
        "sample_frames": sample_frames,
        "nonblank_sample_check": nonblank,
        "still_records": still_records,
        "qa_pass": qa_pass,
    }
    return record, still_manifest_records


def _load_still(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    return image.resize(size, Image.Resampling.LANCZOS)


def _draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont) -> None:
    draw.text(xy, text, fill=(20, 20, 20), font=font)


def _make_contact_sheet(
    *,
    cases: list[dict[str, Any]],
    still_lookup: dict[tuple[str, str, str], Path],
    destination: Path,
    title: str,
) -> dict[str, Any]:
    cell_w, cell_h = 256, 128
    label_w = 170
    header_h = 58
    row_h = cell_h * 2 + 40
    cols = [("original", "start"), ("original", "mid"), ("original", "end"), ("nomdl", "start"), ("nomdl", "mid"), ("nomdl", "end")]
    width = label_w + cell_w * len(cols)
    height = header_h + row_h * len(cases)
    canvas = Image.new("RGB", (width, height), (246, 246, 242))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    _draw_text(draw, (12, 10), title, font)
    for index, (condition, label) in enumerate(cols):
        x = label_w + index * cell_w + 6
        _draw_text(draw, (x, 34), f"{condition} {label}", font)

    for row_index, case in enumerate(cases):
        path_key = str(case["path_key"])
        y0 = header_h + row_index * row_h
        draw.rectangle((0, y0, width, y0 + row_h), outline=(205, 205, 198))
        _draw_text(draw, (12, y0 + 12), path_key, font)
        _draw_text(draw, (12, y0 + 30), str(case.get("case_type", "")), font)
        for col_index, (condition, label) in enumerate(cols):
            x = label_w + col_index * cell_w
            y = y0 + 24
            still_path = still_lookup.get((path_key, condition, label))
            if still_path is None:
                draw.rectangle((x + 4, y, x + cell_w - 4, y + cell_h), fill=(230, 230, 230), outline=(180, 180, 180))
                _draw_text(draw, (x + 12, y + 52), "missing", font)
                continue
            image = _load_still(still_path, (cell_w - 8, cell_h))
            canvas.paste(image, (x + 4, y))
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination)
    return {
        "path": _repo_path(destination),
        "size_bytes": destination.stat().st_size,
        "hash_sha256": _sha256_file(destination),
        "case_count": len(cases),
    }


def package_group(
    *,
    group_id: str,
    case_manifest_path: Path,
    original_log_root: Path,
    nomdl_log_root: Path,
    output_root: Path,
    source_rerun_manifest: Path | None,
    original_result: Path | None,
    nomdl_result: Path | None,
    main_case_keys: list[str],
) -> dict[str, Any]:
    case_manifest = _load_json(case_manifest_path)
    cases_by_key = _case_by_key(case_manifest)
    selected_cases = [cases_by_key[key] for key in cases_by_key]

    copied_manifests = {
        "case_manifest": _copy_file(case_manifest_path, output_root / "manifests" / f"{group_id}_video_case_manifest.json"),
    }
    if source_rerun_manifest is not None:
        copied_manifests["rerun_manifest"] = _copy_file(
            source_rerun_manifest,
            output_root / "manifests" / f"{group_id}_video_rerun_manifest.json",
        )
    original_result = original_result or original_log_root / "result.json"
    nomdl_result = nomdl_result or nomdl_log_root / "result.json"
    copied_manifests["original_result"] = _copy_file(
        original_result,
        output_root / "manifests" / f"{group_id}_original_result.json",
    )
    copied_manifests["nomdl_result"] = _copy_file(
        nomdl_result,
        output_root / "manifests" / f"{group_id}_nomdl_result.json",
    )

    video_records = []
    still_records_by_video = []
    still_lookup: dict[tuple[str, str, str], Path] = {}
    for path_key, case in cases_by_key.items():
        for condition, log_root in (("original", original_log_root), ("nomdl", nomdl_log_root)):
            source_video = log_root / "video" / path_key / f"{path_key}.mp4"
            copied_video = output_root / "videos" / group_id / condition / f"{path_key}.mp4"
            record, still_manifest_records = _qa_video(
                source_video=source_video,
                copied_video=copied_video,
                group_id=group_id,
                path_key=path_key,
                condition=condition,
                case=case,
                still_dir=output_root / "stills" / group_id,
            )
            video_records.append(record)
            still_records_by_video.append(
                {
                    "group_id": group_id,
                    "path_key": path_key,
                    "condition": condition,
                    "stills": still_manifest_records,
                }
            )
            for item in still_manifest_records:
                still_lookup[(path_key, condition, item["label"])] = PROJECT_ROOT / item["path"]

    qa_summary = {
        "checks": [
            "exists",
            "size_bytes>100000",
            "opencv_opened",
            "frame_count>0",
            "sampled_luma_nonblank",
            "start_mid_end_stills_written",
        ],
        "video_count": len(video_records),
        "qa_pass_count": sum(1 for record in video_records if record["qa_pass"]),
        "all_videos_pass_basic_nonblank_check": all(record["qa_pass"] for record in video_records),
    }
    qa = {"qa_summary": qa_summary, "video_records": video_records}
    qa_path = output_root / "manifests" / f"{group_id}_video_basic_qa.json"
    _write_json(qa_path, qa)

    selected_sheet = _make_contact_sheet(
        cases=selected_cases,
        still_lookup=still_lookup,
        destination=output_root / "contact_sheets" / f"{group_id}_selected6_paired_contact_sheet.png",
        title=f"{group_id} selected qualitative rollouts",
    )
    main_cases = [cases_by_key[key] for key in main_case_keys if key in cases_by_key]
    if not main_cases:
        main_cases = selected_cases[: min(3, len(selected_cases))]
    main_sheet = _make_contact_sheet(
        cases=main_cases,
        still_lookup=still_lookup,
        destination=output_root / "contact_sheets" / f"{group_id}_main3_paired_contact_sheet.png",
        title=f"{group_id} main qualitative candidates",
    )

    manifest = {
        "schema_version": 1,
        "group_id": group_id,
        "claim_boundary": "selected_qualitative_rollout_media_only; full paired metrics remain authoritative",
        "source_roots": {
            "original_log_root": str(original_log_root.resolve()),
            "nomdl_log_root": str(nomdl_log_root.resolve()),
        },
        "copied_manifests": copied_manifests,
        "selected_path_keys": list(cases_by_key),
        "qa_summary": qa_summary,
        "qa": {
            "path": _repo_path(qa_path),
            "size_bytes": qa_path.stat().st_size,
            "hash_sha256": _sha256_file(qa_path),
        },
        "videos": [
            {
                "group_id": record["group_id"],
                "path_key": record["path_key"],
                "condition": record["condition"],
                "case_type": record["case_type"],
                "path": record["path"],
                "size_bytes": record["size_bytes"],
                "hash_sha256": record["hash_sha256"],
                "frame_count": record["frame_count"],
                "duration_seconds_video": record["duration_seconds_video"],
                "qa_pass": record["qa_pass"],
            }
            for record in video_records
        ],
        "stills": still_records_by_video,
        "contact_sheets": {
            "selected6": selected_sheet,
            "main3": main_sheet,
        },
    }
    manifest_path = output_root / "manifests" / f"{group_id}_video_asset_manifest.json"
    _write_json(manifest_path, manifest)
    return {
        "group_id": group_id,
        "manifest": _repo_path(manifest_path),
        "qa": _repo_path(qa_path),
        "video_count": len(video_records),
        "qa_pass_count": qa_summary["qa_pass_count"],
        "output_root": _repo_path(output_root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group-id", required=True)
    parser.add_argument("--case-manifest", type=Path, required=True)
    parser.add_argument("--original-log-root", type=Path, required=True)
    parser.add_argument("--nomdl-log-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--source-rerun-manifest", type=Path)
    parser.add_argument("--original-result", type=Path)
    parser.add_argument("--nomdl-result", type=Path)
    parser.add_argument("--main-case-key", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = package_group(
        group_id=args.group_id,
        case_manifest_path=args.case_manifest,
        original_log_root=args.original_log_root,
        nomdl_log_root=args.nomdl_log_root,
        output_root=args.output_root,
        source_rerun_manifest=args.source_rerun_manifest,
        original_result=args.original_result,
        nomdl_result=args.nomdl_result,
        main_case_keys=args.main_case_key,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
