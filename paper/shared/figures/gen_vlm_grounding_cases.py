#!/usr/bin/env python3
"""Generate qualitative VLM grounding case panels from checked-in predictions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw


FIG_DIR = Path(__file__).resolve().parent
PAPER_SHARED = FIG_DIR.parent
RAW = PAPER_SHARED / "evidence" / "raw" / "grscene_vlm_grounding"
OUT_STEM = FIG_DIR / "fig_vlm_grounding_cases"
OUT_PNG = OUT_STEM.with_suffix(".png")
OUT_PDF = OUT_STEM.with_suffix(".pdf")

CELL_W = 260
CELL_H = 205
MARGIN = 24
GAP_X = 14
GAP_Y = 24
TITLE_H = 34
STATUS_H = 46
HEADER_H = 22
CASE_COLUMNS = 2
CASE_GAP_X = 28
POINT_RADIUS = 7
POINT_HALO_RADIUS = 10

BOX_COLOR = (0, 160, 120)
POINT_COLOR = (210, 40, 40)
MISS_COLOR = (160, 80, 30)
TEXT_COLOR = (25, 25, 25)
MUTED = (90, 90, 90)
MAX_ANSWER_CHARS = 15


class CaseEntry(NamedTuple):
    version: str
    image_path: Path
    width: int
    height: int
    bbox_xyxy: list[float]
    point_xy: tuple[float, float] | None
    answer: str | None
    answer_match: bool | None
    score_hit: bool | None


class GroundingCase(NamedTuple):
    title: str
    split: str
    model: str
    pair_id: str
    target_category: str
    point_frame: str
    score_metric: str
    entries: dict[str, CaseEntry]


CASE_SPECS = [
    {
        "title": "Clean preservation success",
        "split": "clean",
        "model": "Gemma4",
        "pair_id": "21dde4a14ca93f539a47.retake_008",
        "predictions": RAW / "clean_pool_probes" / "gemma4_clean_pool_pass15_predictions.jsonl",
        "score_summary": RAW / "clean_pool_probes" / "gemma4_clean_pool_pass15_score_summary.json",
        "point_frame": "normalized_1000",
        "score_metric": "point_in_bbox_normalized_1000",
    },
    {
        "title": "Clean coordinate disagreement",
        "split": "clean",
        "model": "Qwen2.5-VL",
        "pair_id": "c27086f557d316584264.view_001",
        "predictions": RAW / "clean_pool_probes" / "qwen25_clean_pool_pass15_structured_predictions.jsonl",
        "score_summary": RAW / "clean_pool_probes" / "qwen25_clean_pool_pass15_structured_score_summary.json",
        "point_frame": "raw_pixel",
        "score_metric": "point_in_bbox",
    },
    {
        "title": "Expanded stress success",
        "split": "stress",
        "model": "Gemma4",
        "pair_id": "47aa36277a54f6ca90cc.zoom_018",
        "predictions": RAW / "stress_predictions.jsonl",
        "score_summary": RAW / "stress_score_summary.json",
        "point_frame": "normalized_1000",
        "score_metric": "point_in_bbox_normalized_1000",
    },
    {
        "title": "Expanded stress disagreement",
        "split": "stress",
        "model": "Qwen2.5-VL",
        "pair_id": "c8ee4b66274b05d242c2.zoom_017",
        "predictions": RAW / "stress_expanded30_probes" / "qwen25_stress_expanded30_structured_predictions.jsonl",
        "score_summary": RAW / "stress_expanded30_probes" / "qwen25_stress_expanded30_structured_score_summary.json",
        "point_frame": "raw_pixel",
        "score_metric": "point_in_bbox",
    },
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_score_records(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {record["sample_id"]: record for record in data.get("records", [])}


def point_to_pixel(
    point: list[float] | tuple[float, float] | None,
    *,
    width: int,
    height: int,
    frame: str,
) -> tuple[float, float] | None:
    if point is None:
        return None
    x = float(point[0])
    y = float(point[1])
    if frame == "raw_pixel":
        return (x, y)
    if frame == "normalized_1000":
        return (x / 1000.0 * width, y / 1000.0 * height)
    raise ValueError(f"Unsupported point frame: {frame}")


def _load_entry(row: dict, score: dict | None, *, point_frame: str, score_metric: str) -> CaseEntry:
    image = row["image"]
    prediction = row.get("prediction") or {}
    target = row["target"]
    point = point_to_pixel(
        prediction.get("point_xy"),
        width=int(image["width"]),
        height=int(image["height"]),
        frame=point_frame,
    )
    return CaseEntry(
        version=row["version"],
        image_path=Path(image["path"]),
        width=int(image["width"]),
        height=int(image["height"]),
        bbox_xyxy=[float(v) for v in target["bbox_xyxy"]],
        point_xy=point,
        answer=prediction.get("answer"),
        answer_match=None if score is None else score.get("answer_match"),
        score_hit=None if score is None else score.get(score_metric),
    )


def load_case(spec: dict) -> GroundingCase:
    rows = [row for row in read_jsonl(Path(spec["predictions"])) if row.get("pair_id") == spec["pair_id"]]
    scores = load_score_records(Path(spec["score_summary"]))
    by_version = {row["version"]: row for row in rows}
    if set(by_version) != {"original", "converted"}:
        raise ValueError(f"Expected original and converted rows for {spec['pair_id']}")

    entries = {
        version: _load_entry(
            by_version[version],
            _require_score(scores, by_version[version]["sample_id"], spec["score_metric"]),
            point_frame=spec["point_frame"],
            score_metric=spec["score_metric"],
        )
        for version in ("original", "converted")
    }
    target_category = by_version["original"]["target"]["category"]
    return GroundingCase(
        title=spec["title"],
        split=spec["split"],
        model=spec["model"],
        pair_id=spec["pair_id"],
        target_category=target_category,
        point_frame=spec["point_frame"],
        score_metric=spec["score_metric"],
        entries=entries,
    )


def _require_score(scores: dict[str, dict], sample_id: str, score_metric: str) -> dict:
    score = scores.get(sample_id)
    if score is None:
        raise ValueError(f"Missing score record for selected sample: {sample_id}")
    if score_metric not in score:
        raise ValueError(f"Missing score metric {score_metric} for selected sample: {sample_id}")
    return score


def build_cases(specs: list[dict] | None = None) -> list[GroundingCase]:
    return [load_case(spec) for spec in (specs or CASE_SPECS)]


def _status(value: bool | None, *, positive: str, negative: str) -> str:
    if value is True:
        return positive
    if value is False:
        return negative
    return "n/a"


def _short_answer(answer: str | None) -> str:
    if not answer:
        return "none"
    if len(answer) <= MAX_ANSWER_CHARS:
        return answer
    return answer[:MAX_ANSWER_CHARS].rstrip() + "..."


def status_line(entry: CaseEntry) -> str:
    point_status = _status(entry.score_hit, positive="pt hit", negative="pt miss")
    answer_status = _status(entry.answer_match, positive="ans hit", negative="ans miss")
    return f"{entry.version}: {point_status}, {answer_status}"


def answer_line(entry: CaseEntry) -> str:
    return f"ans={_short_answer(entry.answer)}"


def case_title(case: GroundingCase) -> str:
    point_label = "norm1000" if case.point_frame == "normalized_1000" else "raw"
    return f"{case.title} | {case.model} | target={case.target_category} | {point_label}"


def _fit_image(path: Path) -> tuple[Image.Image, float, int, int]:
    img = Image.open(path).convert("RGB")
    scale = min(CELL_W / img.width, CELL_H / img.height)
    new_w = max(1, round(img.width * scale))
    new_h = max(1, round(img.height * scale))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (CELL_W, CELL_H), "white")
    x0 = (CELL_W - new_w) // 2
    y0 = (CELL_H - new_h) // 2
    canvas.paste(resized, (x0, y0))
    return canvas, scale, x0, y0


def _draw_entry(draw: ImageDraw.ImageDraw, canvas: Image.Image, entry: CaseEntry, x: int, y: int) -> None:
    img, scale, ox, oy = _fit_image(entry.image_path)
    canvas.paste(img, (x, y))
    x1, y1, x2, y2 = entry.bbox_xyxy
    box = (
        x + ox + x1 * scale,
        y + oy + y1 * scale,
        x + ox + x2 * scale,
        y + oy + y2 * scale,
    )
    draw.rectangle(box, outline=BOX_COLOR, width=3)
    if entry.point_xy is not None:
        px, py = entry.point_xy
        cx = x + ox + px * scale
        cy = y + oy + py * scale
        color = POINT_COLOR if entry.score_hit is True else MISS_COLOR
        halo = POINT_HALO_RADIUS
        r = POINT_RADIUS
        draw.ellipse((cx - halo, cy - halo, cx + halo, cy + halo), fill="white", outline=(20, 20, 20), width=1)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color, outline=(20, 20, 20), width=1)
        draw.line((cx - halo, cy, cx + halo, cy), fill="white", width=2)
        draw.line((cx, cy - halo, cx, cy + halo), fill="white", width=2)
    draw.rectangle((x, y, x + CELL_W, y + CELL_H), outline=(170, 170, 170), width=1)


def _case_block_width() -> int:
    return CELL_W * 2 + GAP_X


def _case_block_height() -> int:
    return TITLE_H + CELL_H + STATUS_H


def _draw_case(canvas: Image.Image, draw: ImageDraw.ImageDraw, case: GroundingCase, index: int) -> None:
    grid_row = index // CASE_COLUMNS
    grid_col = index % CASE_COLUMNS
    block_w = _case_block_width()
    y = MARGIN + HEADER_H + grid_row * (_case_block_height() + GAP_Y)
    left_x = MARGIN + grid_col * (block_w + CASE_GAP_X)
    right_x = left_x + CELL_W + GAP_X
    draw.text((left_x, y + 8), case_title(case), fill=TEXT_COLOR)

    image_y = y + TITLE_H
    _draw_entry(draw, canvas, case.entries["original"], left_x, image_y)
    _draw_entry(draw, canvas, case.entries["converted"], right_x, image_y)

    for x, version in ((left_x, "original"), (right_x, "converted")):
        entry = case.entries[version]
        draw.text((x + 4, image_y + CELL_H + 5), status_line(entry), fill=TEXT_COLOR)
        draw.text((x + 4, image_y + CELL_H + 20), answer_line(entry), fill=TEXT_COLOR)


def render_figure(cases: list[GroundingCase], *, out_png: Path = OUT_PNG, out_pdf: Path = OUT_PDF) -> None:
    row_count = (len(cases) + CASE_COLUMNS - 1) // CASE_COLUMNS
    width = MARGIN * 2 + CASE_COLUMNS * _case_block_width() + (CASE_COLUMNS - 1) * CASE_GAP_X
    height = MARGIN * 2 + HEADER_H + row_count * _case_block_height() + (row_count - 1) * GAP_Y
    canvas = Image.new("RGB", (width, height), (248, 248, 248))
    draw = ImageDraw.Draw(canvas)
    for col in range(CASE_COLUMNS):
        block_x = MARGIN + col * (_case_block_width() + CASE_GAP_X)
        draw.text((block_x + 82, MARGIN), "Original MDL render", fill=TEXT_COLOR)
        draw.text((block_x + CELL_W + GAP_X + 58, MARGIN), "Converted no-MDL render", fill=TEXT_COLOR)
    for index, case in enumerate(cases):
        _draw_case(canvas, draw, case, index)
    canvas.save(out_png)
    canvas.save(out_pdf, "PDF", resolution=300.0)


def main() -> None:
    cases = build_cases()
    render_figure(cases)
    print(OUT_PNG)
    print(OUT_PDF)


if __name__ == "__main__":
    main()
