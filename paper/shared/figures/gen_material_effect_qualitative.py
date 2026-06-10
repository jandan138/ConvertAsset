#!/usr/bin/env python3
"""Generate a material-effect baseline qualitative contact sheet."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "paper/shared/figures/fig_material_effect_baseline_qualitative.png"
SUPPLEMENTAL_OUTPUT = PROJECT_ROOT / "paper/shared/figures/fig_material_effect_supplemental_qualitative.png"
CONDITION_ORDER = [
    "original_MDL",
    "existing_noMDL",
    "nvidia_asset_converter_preview_or_bake",
]
CONDITION_LABELS = {
    "original_MDL": "Original MDL",
    "existing_noMDL": "ConvertAsset",
    "nvidia_asset_converter_preview_or_bake": "NVIDIA",
}
EFFECT_LABELS = {
    "opacity_transparency": "opacity/transparency",
    "emission": "emission",
    "normal_bump": "normal/bump",
    "displacement_height": "displacement/height",
    "clearcoat": "clearcoat",
    "procedural_texture": "procedural texture",
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


def _records_by_case(manifest: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for record in manifest.get("records", []):
        sample_id = str(record.get("sample_id") or "")
        condition = str(record.get("condition") or "")
        if sample_id and condition:
            out.setdefault(sample_id, {})[condition] = record
    return out


def _complete_cases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    by_case = _records_by_case(manifest)
    complete: list[dict[str, Any]] = []
    for case in manifest.get("selected_cases", []):
        sample_id = str(case.get("sample_id") or "")
        records = by_case.get(sample_id) or {}
        if all(
            condition in records
            and (records[condition].get("image") or {}).get("status") == "ready"
            and Path(str((records[condition].get("image") or {}).get("path"))).is_file()
            for condition in CONDITION_ORDER
        ):
            complete.append({**case, "records": records})
    return complete


def _fit_image(
    image: Image.Image,
    size: tuple[int, int],
    *,
    fit_mode: str = "cover",
) -> Image.Image:
    if fit_mode == "cover":
        return ImageOps.fit(
            image.convert("RGB"),
            size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

    fitted = image.convert("RGB")
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (245, 245, 245))
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ) if bold else (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    for path in paths:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, fill=(25, 25, 25)) -> None:
    draw.text(xy, text, font=font, fill=fill)


def _case_caption(case: dict[str, Any]) -> str:
    effects = ", ".join(EFFECT_LABELS.get(str(effect), str(effect)) for effect in case.get("covered_effects") or [])
    category = str(case.get("target_category") or "target")
    return f"{category.capitalize()}: {effects}"


def build_material_effect_contact_sheet(
    manifest: dict[str, Any],
    *,
    output_path: Path,
    cell_size: tuple[int, int] = (360, 120),
    fit_mode: str = "cover",
    margin: int = 12,
    gutter: int = 10,
    header_h: int = 42,
    caption_h: int = 0,
    label_font_size: int = 18,
    caption_font_size: int = 16,
) -> dict[str, Any]:
    complete = _complete_cases(manifest)
    blockers: list[str] = []
    if not complete:
        blockers.append("no_complete_qualitative_cases")
        return {
            "schema_version": 1,
            "status": "material_effect_qualitative_figure_report",
            "generated_at_utc": _utc_now(),
            "generated_by": "paper/shared/figures/gen_material_effect_qualitative.py",
            "output": {"path": str(output_path), "exists": False, "hash_sha256": None},
            "summary": {
                "selected_case_count": len(manifest.get("selected_cases", [])),
                "ready_case_count": 0,
                "figure_written": False,
                "blockers": blockers,
            },
        }

    row_h = header_h + cell_size[1] + caption_h
    width = margin * 2 + len(CONDITION_ORDER) * cell_size[0] + (len(CONDITION_ORDER) - 1) * gutter
    height = margin * 2 + len(complete) * row_h
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    label_font = _font(label_font_size, bold=True)
    caption_font = _font(caption_font_size)

    for row_idx, case in enumerate(complete):
        y0 = margin + row_idx * row_h
        _draw_text(draw, (margin, y0), _case_caption(case), caption_font)
        for col_idx, condition in enumerate(CONDITION_ORDER):
            x0 = margin + col_idx * (cell_size[0] + gutter)
            _draw_text(draw, (x0, y0 + 22), CONDITION_LABELS[condition], label_font)
            image_path = Path(str(case["records"][condition]["image"]["path"]))
            with Image.open(image_path) as image:
                fitted = _fit_image(image, cell_size, fit_mode=fit_mode)
            canvas.paste(fitted, (x0, y0 + header_h))
        if caption_h > 0:
            _draw_text(draw, (margin, y0 + header_h + cell_size[1] + 10), _case_caption(case), caption_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return {
        "schema_version": 1,
        "status": "material_effect_qualitative_figure_report",
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/figures/gen_material_effect_qualitative.py",
        "output": {
            "path": str(output_path),
            "exists": output_path.is_file(),
            "hash_sha256": _sha256_file(output_path) if output_path.is_file() else None,
            "bytes": output_path.stat().st_size if output_path.is_file() else 0,
        },
        "summary": {
            "selected_case_count": len(manifest.get("selected_cases", [])),
            "ready_case_count": len(complete),
            "figure_written": output_path.is_file(),
            "blockers": blockers,
            "layout": {
                "cell_size": list(cell_size),
                "fit_mode": fit_mode,
                "margin": margin,
                "gutter": gutter,
                "header_h": header_h,
                "caption_h": caption_h,
                "label_font_size": label_font_size,
                "condition_label_font_size": label_font_size,
                "caption_font_size": caption_font_size,
                "case_label_font_size": caption_font_size,
            },
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_OUTPUT.with_suffix(".report.json"))
    parser.add_argument("--cell-width", type=int, default=360)
    parser.add_argument("--cell-height", type=int, default=120)
    parser.add_argument("--fit-mode", choices=("cover", "contain"), default="cover")
    args = parser.parse_args(argv)

    report = build_material_effect_contact_sheet(
        _load_json(args.manifest),
        output_path=args.out,
        cell_size=(args.cell_width, args.cell_height),
        fit_mode=args.fit_mode,
    )
    report["inputs"] = {
        "manifest": {"path": str(args.manifest), "hash_sha256": _sha256_file(args.manifest)},
    }
    report["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_commit": _git_commit(),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.report} figure_written={report['summary']['figure_written']} "
        f"ready_cases={report['summary']['ready_case_count']}"
    )
    return 0 if report["summary"]["figure_written"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
