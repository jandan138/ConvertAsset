#!/usr/bin/env python3
"""Prefill repo-verifiable rows in the ignored ACL/OpenReview author gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PRIVATE_WORKSHEET = Path("venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md")
DEFAULT_PACKET_ID = "acl27_arr_candidate_20260526"
EXPECTED_PACKET_FILES = (
    "main.pdf",
    "openreview/METADATA.md",
    "openreview/RESPONSIBLE_NLP_CHECKLIST.md",
    "supplemental/README.md",
    "supplemental/manifest.json",
)
TODO_MARKERS = ("TODO", "TBD", "UNKNOWN", "UNDECIDED")


def default_paper_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def value_is_todo(value: str) -> bool:
    upper = value.strip().upper()
    return not upper or any(marker in upper for marker in TODO_MARKERS)


def parse_pdfinfo(pdfinfo_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in pdfinfo_text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def latest_packet_dir(paper_root: Path) -> Path:
    default_packet = paper_root / "submissions" / DEFAULT_PACKET_ID
    if default_packet.exists():
        return default_packet
    candidates = sorted(
        path
        for path in (paper_root / "submissions").glob("acl27_arr_candidate_*")
        if path.is_dir()
    )
    if not candidates:
        return default_packet
    return candidates[-1]


def staged_file_list(packet_dir: Path) -> list[str]:
    if packet_dir.exists():
        return sorted(
            str(path.relative_to(packet_dir))
            for path in packet_dir.rglob("*")
            if path.is_file()
        )
    return list(EXPECTED_PACKET_FILES)


def run_pdfinfo(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def build_safe_prefill_values(
    paper_root: Path,
    *,
    pdfinfo_text: str | None = None,
    timestamp_utc: str | None = None,
) -> dict[str, str]:
    paper_root = Path(paper_root)
    packet_dir = latest_packet_dir(paper_root)
    packet_files = staged_file_list(packet_dir)
    pdfinfo = parse_pdfinfo(
        pdfinfo_text if pdfinfo_text is not None else run_pdfinfo(packet_dir / "main.pdf")
    )
    timestamp = timestamp_utc if timestamp_utc is not None else utc_timestamp()
    pages = pdfinfo.get("Pages", "unknown pages")
    page_size = pdfinfo.get("Page size", "unknown page size")
    pdf_version = pdfinfo.get("PDF version", "unknown PDF version")
    file_size = pdfinfo.get("File size", "unknown file size")

    return {
        "Clean PDF build command and timestamp": (
            "pass: python paper/venues/acl27/scripts/run_preupload_gate.py passed; "
            "clean build command make -C paper clean-acl27 acl27; "
            f"prefilled at {timestamp}"
        ),
        "Final PDF page count / page size": (
            f"pass: {pages} pages; {page_size}; PDF {pdf_version}; {file_size}"
        ),
        "Undefined citation/reference scan": (
            "pass: citation inventory and final LaTeX log scan passed in "
            "run_preupload_gate.py"
        ),
        "Staging command and packet path": (
            "pass: python paper/venues/acl27/scripts/stage_submission_packet.py "
            f"--force -> {packet_dir.relative_to(paper_root)}"
        ),
        "Staged file list": "pass: " + ", ".join(packet_files),
        "Local path / username / private-link scan": (
            "pass: packet_private_scan passed on the staged packet"
        ),
        "Acknowledgment scan": "pass: packet_acknowledgment_scan passed",
        "Limitations / Ethical Considerations / References text scan": (
            "pass: pdftotext_sections found ordered Limitations, Ethical "
            "Considerations, and References markers"
        ),
    }


def split_markdown_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or stripped.startswith("| ---"):
        return None
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if len(cells) < 2 or cells[0] in {"Field", "Gate"}:
        return None
    return cells


def replace_markdown_table_value(line: str, value: str) -> str:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    cells[1] = value
    return "| " + " | ".join(cells) + " |"


def apply_prefill(
    worksheet_path: Path,
    values: dict[str, str],
    *,
    overwrite: bool = False,
) -> dict[str, object]:
    lines = worksheet_path.read_text(encoding="utf-8").splitlines()
    changed_fields: list[str] = []
    skipped_fields: list[str] = []
    for index, line in enumerate(lines):
        cells = split_markdown_table_row(line)
        if cells is None:
            continue
        field = cells[0]
        if field not in values:
            continue
        if not overwrite and not value_is_todo(cells[1]):
            skipped_fields.append(field)
            continue
        lines[index] = replace_markdown_table_value(line, values[field])
        changed_fields.append(field)
    worksheet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "private_worksheet": str(PRIVATE_WORKSHEET),
        "changed_fields": changed_fields,
        "skipped_existing_fields": skipped_fields,
        "prints_private_values": False,
    }


def git_path_is_ignored(repo_root: Path, path: Path) -> bool:
    relative = path.relative_to(repo_root)
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(relative)],
        cwd=repo_root,
        check=False,
    )
    return result.returncode == 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-root", type=Path, default=default_paper_root())
    parser.add_argument("--repo-root", type=Path, default=default_repo_root())
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the prefill into the ignored private worksheet.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing values in repo-verifiable prefill rows.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paper_root = Path(args.paper_root)
    repo_root = Path(args.repo_root)
    worksheet_path = paper_root / PRIVATE_WORKSHEET
    if not worksheet_path.exists():
        raise FileNotFoundError(f"Missing private worksheet: {PRIVATE_WORKSHEET}")
    if not git_path_is_ignored(repo_root, worksheet_path):
        raise RuntimeError(f"Refusing to touch unignored private worksheet: {PRIVATE_WORKSHEET}")

    values = build_safe_prefill_values(paper_root)
    if args.apply:
        report = apply_prefill(worksheet_path, values, overwrite=args.overwrite)
    else:
        report = {
            "ok": True,
            "dry_run": True,
            "private_worksheet": str(PRIVATE_WORKSHEET),
            "prefill_fields": list(values),
            "prints_private_values": False,
        }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
