#!/usr/bin/env python3
"""Check ACL OpenReview Responsible NLP checklist copy source."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EXPECTED_QUESTIONS = (
    "A1. Did you discuss the limitations of your work?",
    "A2. Did you discuss potential risks of your work?",
    "A3. Do the abstract and introduction summarize the paper's main claims?",
    "B1. Did you cite the creators of artifacts you used?",
    "B2. Did you discuss license or terms for use/distribution?",
    "B3. Did you discuss intended use and compatibility with original access conditions?",
    "B4. Did you check whether used data contains identifying or offensive content and protect/anonymize it?",
    "B5. Did you provide artifact documentation?",
    "B6. Did you report relevant statistics and splits?",
    "C1. Did you report model parameters, compute budget, and infrastructure?",
    "C2. Did you discuss experimental setup and hyperparameters?",
    "C3. Did you report descriptive statistics and clarify max/mean/single-run status?",
    "C4. Did you report packages/implementation/settings used?",
    "D. Did you use human annotators or human subjects?",
    "D1-D5.",
    "E. Did you use AI assistants in research, coding, or writing?",
    "E1. Did you include information about AI assistant use?",
)

REQUIRED_POLICY_URLS = (
    "https://aclrollingreview.org/static/responsibleNLPresearch.pdf",
    "https://aclrollingreview.org/responsibleNLPresearch/",
    "https://aclrollingreview.org/authorchecklist",
    "https://aclrollingreview.org/responsible-nlp-checklist-appendices",
)

REQUIRED_ANCHOR_MARKERS = (
    "| Abstract | page 1;",
    "| Introduction / main results | pages 1-3;",
    "| Limitations | page 9;",
    "| Ethical Considerations | page 9;",
    "| Selected material-effect Figure 3 | page 8;",
    "| Selected InternNav Figure 4 | page 9;",
    "| References | starts on page 9 |",
)

PLACEHOLDER_RE = re.compile(
    r"\b(?:TODO|TBD|FIXME|PLACEHOLDER|XXX)\b|Draft needed|\[.*?TODO.*?\]",
    re.IGNORECASE,
)
BARE_ANSWER_RE = re.compile(r"^(?:Yes|No|N/A)\.$", re.IGNORECASE)
VENUE_WRAPPER_RE = re.compile(
    r"\b(?:ACL-facing|main ACL claim|ACL protocol|ACL/ARR claim boundary|Any ACL submission)\b"
)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def checklist_path(paper_root: Path) -> Path:
    return paper_root / "venues" / "acl27" / "OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md"


def extract_question_blocks(text: str) -> dict[str, str]:
    lines = text.splitlines()
    headings: list[tuple[str, int, int]] = []
    line_index = 0
    while line_index < len(lines):
        line = lines[line_index].strip()
        if not line.startswith("**"):
            line_index += 1
            continue

        start = line_index
        parts = [line]
        while not parts[-1].endswith("**") and line_index + 1 < len(lines):
            line_index += 1
            parts.append(lines[line_index].strip())

        candidate = normalize_space(" ".join(parts))
        if candidate.startswith("**") and candidate.endswith("**"):
            question = normalize_space(candidate[2:-2])
            if re.match(r"^(?:[A-E]\d?|D1-D5)\.", question):
                headings.append((question, start, line_index))
        line_index += 1

    blocks: dict[str, str] = {}
    for index, (question, _start, end) in enumerate(headings):
        next_start = headings[index + 1][1] if index + 1 < len(headings) else len(lines)
        blocks[question] = "\n".join(lines[end + 1 : next_start]).strip()
    return blocks


def first_paragraph(block: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", block) if part.strip()]
    return normalize_space(paragraphs[0]) if paragraphs else ""


def find_placeholder_hits(text: str) -> list[str]:
    hits: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if PLACEHOLDER_RE.search(line):
            hits.append(f"line {line_no}: {line.strip()}")
    return hits


def find_venue_wrapper_hits(text: str) -> list[str]:
    hits: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if VENUE_WRAPPER_RE.search(line):
            hits.append(f"line {line_no}: {line.strip()}")
    return hits


def check_openreview_checklist(paper_root: Path) -> dict[str, object]:
    path = checklist_path(Path(paper_root))
    text = path.read_text(encoding="utf-8")
    question_blocks = extract_question_blocks(text)

    missing_questions = [
        question for question in EXPECTED_QUESTIONS if question not in question_blocks
    ]
    extra_questions = [
        question for question in question_blocks if question not in EXPECTED_QUESTIONS
    ]
    bare_answer_questions = [
        question
        for question, block in question_blocks.items()
        if BARE_ANSWER_RE.match(first_paragraph(block))
    ]
    empty_answer_questions = [
        question for question, block in question_blocks.items() if not block.strip()
    ]
    missing_policy_inputs = [url for url in REQUIRED_POLICY_URLS if url not in text]
    missing_anchor_markers = [
        marker for marker in REQUIRED_ANCHOR_MARKERS if marker not in text
    ]
    normalized_text = normalize_space(text.replace(">", " "))
    ai_disclosure_present = (
        "AI coding and writing assistants" in normalized_text
        and "assistants were not credited" in normalized_text
        and "as authors" in normalized_text
    )

    checks = {
        "all_expected_questions_present": not missing_questions,
        "no_extra_questions": not extra_questions,
        "answers_not_empty": not empty_answer_questions,
        "no_bare_yes_no_na_answers": not bare_answer_questions,
        "no_placeholder_text": not find_placeholder_hits(text),
        "no_internal_venue_wrapper_phrasing": not find_venue_wrapper_hits(text),
        "policy_inputs_present": not missing_policy_inputs,
        "current_pdf_anchors_present": not missing_anchor_markers,
        "ai_disclosure_present": ai_disclosure_present,
    }

    return {
        "ok": all(checks.values()),
        "path": str(path),
        "question_count": len(question_blocks),
        "expected_question_count": len(EXPECTED_QUESTIONS),
        "missing_questions": missing_questions,
        "extra_questions": extra_questions,
        "empty_answer_questions": empty_answer_questions,
        "bare_answer_questions": bare_answer_questions,
        "placeholder_hits": find_placeholder_hits(text),
        "venue_wrapper_hits": find_venue_wrapper_hits(text),
        "missing_policy_inputs": missing_policy_inputs,
        "missing_anchor_markers": missing_anchor_markers,
        "current_pdf_anchors_present": not missing_anchor_markers,
        "ai_disclosure_present": ai_disclosure_present,
        "checks": checks,
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

    report = check_openreview_checklist(args.paper_root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
