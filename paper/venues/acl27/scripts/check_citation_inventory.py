#!/usr/bin/env python3
"""Check ACL citation inventory against BibTeX and web-trail evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


CITATION_RE = re.compile(r"\\cite\w*(?:\[[^\]]*\])*\{([^}]*)\}")
BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
IDENTIFIER_RE = re.compile(r"(?im)^\s*(doi|url)\s*=\s*\{?\s*([^},\n]+)")
ACL_WEBTRAIL_HEADING = "## 2026-05-26 ACL WRAPPER WEB-TRAIL ADDENDUM"


def default_paper_root() -> Path:
    return Path(__file__).resolve().parents[3]


def strip_latex_comments(text: str) -> str:
    return re.sub(r"(?m)%.*$", "", text)


def acl_manuscript_paths(paper_root: Path) -> list[Path]:
    venue_sections = sorted((paper_root / "venues" / "acl27" / "sections").glob("*.tex"))
    appendix = paper_root / "shared" / "sections" / "appendix.tex"
    paths = venue_sections[:]
    if appendix.exists():
        paths.append(appendix)
    return paths


def collect_cited_keys(paper_root: Path) -> list[str]:
    keys: list[str] = []
    for path in acl_manuscript_paths(paper_root):
        text = strip_latex_comments(path.read_text(encoding="utf-8"))
        for match in CITATION_RE.finditer(text):
            keys.extend(
                key.strip()
                for key in match.group(1).split(",")
                if key.strip()
            )
    return sorted(set(keys))


def parse_bib_entries(bib_path: Path) -> dict[str, str]:
    text = bib_path.read_text(encoding="utf-8")
    matches = list(BIB_ENTRY_RE.finditer(text))
    entries: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        entries[match.group(1).strip()] = text[start:end]
    return entries


def entry_has_identifier(entry_text: str) -> bool:
    for match in IDENTIFIER_RE.finditer(entry_text):
        if match.group(2).strip():
            return True
    return False


def extract_acl_webtrail_section(report_text: str) -> str:
    start = report_text.find(ACL_WEBTRAIL_HEADING)
    if start < 0:
        return ""
    next_heading = report_text.find("\n## ", start + len(ACL_WEBTRAIL_HEADING))
    if next_heading < 0:
        return report_text[start:]
    return report_text[start:next_heading]


def parse_verified_webtrail_keys(report_path: Path) -> list[str]:
    section = extract_acl_webtrail_section(report_path.read_text(encoding="utf-8"))
    keys: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        key_match = re.fullmatch(r"`([^`]+)`", cells[0])
        if not key_match:
            continue
        if cells[1] == "`VERIFIED`":
            keys.append(key_match.group(1))
    return sorted(set(keys))


def check_citation_inventory(paper_root: Path) -> dict[str, object]:
    paper_root = Path(paper_root)
    cited_keys = collect_cited_keys(paper_root)
    bib_entries = parse_bib_entries(paper_root / "shared" / "references.bib")
    webtrail_keys = parse_verified_webtrail_keys(
        paper_root / "shared" / "evidence" / "references" / "verification_report.md"
    )

    cited_set = set(cited_keys)
    bib_key_set = set(bib_entries)
    webtrail_set = set(webtrail_keys)

    missing_bib_keys = sorted(cited_set - bib_key_set)
    missing_identifier_keys = sorted(
        key
        for key in cited_keys
        if key in bib_entries and not entry_has_identifier(bib_entries[key])
    )
    missing_webtrail_keys = sorted(cited_set - webtrail_set)
    uncited_webtrail_keys = sorted(webtrail_set - cited_set)

    ok = (
        not missing_bib_keys
        and not missing_identifier_keys
        and not missing_webtrail_keys
        and not uncited_webtrail_keys
    )
    return {
        "ok": ok,
        "cited_keys": cited_keys,
        "cited_key_count": len(cited_keys),
        "webtrail_keys": webtrail_keys,
        "webtrail_key_count": len(webtrail_keys),
        "missing_bib_keys": missing_bib_keys,
        "missing_identifier_keys": missing_identifier_keys,
        "missing_webtrail_keys": missing_webtrail_keys,
        "uncited_webtrail_keys": uncited_webtrail_keys,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paper-root",
        type=Path,
        default=default_paper_root(),
        help="Path to the paper root directory.",
    )
    args = parser.parse_args(argv)

    report = check_citation_inventory(args.paper_root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
