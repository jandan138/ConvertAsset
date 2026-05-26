#!/usr/bin/env python3
"""Check ACL OpenReview metadata against manuscript title and abstract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TITLE_RE = re.compile(r"\\title\{(?P<title>.*?)\}", re.DOTALL)
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)*")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def latex_to_plain_text(text: str) -> str:
    text = re.sub(r"(?m)%.*$", "", text)
    text = re.sub(r"\\(?:begin|end)\{abstract\}", " ", text)
    text = text.replace(r"\,", " ")
    text = re.sub(r"\\([#$%&_^{}])", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    return normalize_space(text)


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def extract_latex_title(main_tex: str) -> str:
    match = TITLE_RE.search(main_tex)
    if not match:
        raise ValueError("missing LaTeX title")
    return latex_to_plain_text(match.group("title"))


def extract_metadata_fenced_text(metadata_text: str, heading: str) -> str:
    heading_index = metadata_text.find(heading)
    if heading_index < 0:
        raise ValueError(f"missing metadata heading: {heading}")

    fence_index = metadata_text.find("```text", heading_index)
    if fence_index < 0:
        raise ValueError(f"missing text fence after metadata heading: {heading}")

    body_start = metadata_text.find("\n", fence_index)
    if body_start < 0:
        raise ValueError(f"malformed text fence after metadata heading: {heading}")
    body_start += 1

    body_end = metadata_text.find("```", body_start)
    if body_end < 0:
        raise ValueError(f"unterminated text fence after metadata heading: {heading}")

    return normalize_space(metadata_text[body_start:body_end])


def check_metadata_consistency(paper_root: Path) -> dict[str, object]:
    venue_root = paper_root / "venues" / "acl27"
    title = extract_latex_title((venue_root / "main.tex").read_text(encoding="utf-8"))
    source_abstract = latex_to_plain_text(
        (venue_root / "sections" / "abstract.tex").read_text(encoding="utf-8")
    )

    metadata_text = (venue_root / "OPENREVIEW_METADATA_PACKET.md").read_text(
        encoding="utf-8"
    )
    metadata_title = extract_metadata_fenced_text(
        metadata_text, "Plain-text metadata title:"
    )
    metadata_abstract = extract_metadata_fenced_text(metadata_text, "## Abstract")
    abstract_word_count = count_words(source_abstract)

    checks = {
        "title_matches_metadata": metadata_title == title,
        "abstract_matches_metadata": metadata_abstract == source_abstract,
        "abstract_under_200_words": abstract_word_count <= 200,
    }

    return {
        "title": title,
        "metadata_title": metadata_title,
        "source_abstract": source_abstract,
        "metadata_abstract": metadata_abstract,
        "abstract_word_count": abstract_word_count,
        "checks": checks,
        "ok": all(checks.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "--paper-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Path to the paper root directory.",
    )
    args = parser.parse_args(argv)

    report = check_metadata_consistency(args.paper_root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

