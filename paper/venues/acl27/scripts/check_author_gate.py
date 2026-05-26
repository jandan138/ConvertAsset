#!/usr/bin/env python3
"""Check the private ACL/OpenReview author-gate worksheet."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PRIVATE_WORKSHEET = Path("venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md")
REQUIRED_FIELDS = [
    "Selected route",
    "Final policy refresh date",
    "Target deadline",
    "Commitment venue if ARR-reviewed",
    "Final author list and order",
    "Corresponding author / submitter",
    "OpenReview profile complete for each author",
    "Reviewer-registration commitment",
    "All authors notified of reviewer-duty sanctions",
    "Author contribution / authorship approval",
    "Dual submission status",
    "Prior ARR/OpenReview submission link",
    "Explanation of revisions needed",
    "Preprint status answer",
    "Public repository or project links",
    "Title approved",
    "Abstract approved and under current venue limit",
    "Primary ARR area approved",
    "Secondary area / keywords approved",
    "Responsible NLP checklist copied into OpenReview",
    "Runtime / compute wording approved",
    "AI-assistance wording approved",
    "Model and asset license wording approved",
    "Optional media decision",
    "Clean PDF build command and timestamp",
    "Final PDF page count / page size",
    "Undefined citation/reference scan",
    "Staging command and packet path",
    "Staged file list",
    "Local path / username / private-link scan",
    "Acknowledgment scan",
    "Limitations / Ethical Considerations / References text scan",
    "Final decision: upload / do not upload",
]
TODO_MARKERS = ("TODO", "TBD", "UNKNOWN", "UNDECIDED")
SEMANTIC_FIELD_RULES = {
    "OpenReview profile complete for each author": ("complete", "confirmed", "yes"),
    "Reviewer-registration commitment": ("confirmed", "yes"),
    "All authors notified of reviewer-duty sanctions": ("notified", "confirmed", "yes"),
    "Author contribution / authorship approval": ("approved", "confirmed", "yes"),
    "Dual submission status": (
        "no concurrent",
        "not under concurrent",
        "clear",
        "none",
    ),
    "Title approved": ("approved", "confirmed", "yes"),
    "Abstract approved and under current venue limit": (
        "approved",
        "confirmed",
        "under",
        "yes",
    ),
    "Primary ARR area approved": ("approved", "confirmed", "yes"),
    "Secondary area / keywords approved": ("approved", "confirmed", "yes"),
    "Responsible NLP checklist copied into OpenReview": (
        "copied",
        "complete",
        "confirmed",
        "yes",
    ),
    "Runtime / compute wording approved": ("approved", "confirmed", "yes"),
    "AI-assistance wording approved": ("approved", "confirmed", "yes"),
    "Model and asset license wording approved": ("approved", "confirmed", "yes"),
    "Optional media decision": ("excluded", "approved separate media", "approved"),
    "Undefined citation/reference scan": ("pass", "clean", "no unresolved"),
    "Local path / username / private-link scan": ("pass", "clean", "no leak"),
    "Acknowledgment scan": ("pass", "clean", "no acknowledgment"),
    "Limitations / Ethical Considerations / References text scan": (
        "pass",
        "clean",
        "ordered",
        "present",
    ),
}
FINAL_DECISION_FIELD = "Final decision: upload / do not upload"
NEGATIVE_SEMANTIC_MARKERS = (
    "do not upload",
    "not approved",
    "not confirmed",
    "not copied",
    "not complete",
    "missing",
    "failed",
    "fail:",
    "acknowledgment present",
)


def default_paper_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_markdown_table_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] == "Field":
            continue
        fields[cells[0]] = cells[1]
    return fields


def value_is_filled(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return False
    upper = normalized.upper()
    return not any(marker in upper for marker in TODO_MARKERS)


def value_matches_positive_rule(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.strip().lower()
    if any(marker in lowered for marker in NEGATIVE_SEMANTIC_MARKERS):
        return False
    return any(marker in lowered for marker in markers)


def find_invalid_semantic_fields(fields: dict[str, str]) -> list[str]:
    invalid_fields: list[str] = []
    for field, markers in SEMANTIC_FIELD_RULES.items():
        if field in fields and not value_matches_positive_rule(fields[field], markers):
            invalid_fields.append(field)
    if FINAL_DECISION_FIELD in fields:
        final_decision = fields[FINAL_DECISION_FIELD].strip().lower()
        if "upload" not in final_decision or "do not upload" in final_decision:
            invalid_fields.append(FINAL_DECISION_FIELD)
    return invalid_fields


def git_path_is_ignored(repo_root: Path, path: Path) -> bool:
    relative = path.relative_to(repo_root)
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(relative)],
        cwd=repo_root,
        check=False,
    )
    return result.returncode == 0


def git_path_is_tracked(repo_root: Path, path: Path) -> bool:
    relative = path.relative_to(repo_root)
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(relative)],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def check_author_gate(
    paper_root: Path,
    *,
    repo_root: Path | None = None,
    check_git: bool = True,
) -> dict[str, object]:
    paper_root = Path(paper_root)
    worksheet_path = paper_root / PRIVATE_WORKSHEET
    report: dict[str, object] = {
        "ok": False,
        "private_worksheet": str(PRIVATE_WORKSHEET),
        "missing_private_worksheet": False,
        "checked_fields": [],
        "missing_fields": [],
        "todo_fields": [],
        "invalid_fields": [],
        "git_ignored": None,
        "git_tracked": None,
        "message": "",
    }

    if not worksheet_path.exists():
        report["missing_private_worksheet"] = True
        report["message"] = f"missing private worksheet: {PRIVATE_WORKSHEET}"
        return report

    fields = parse_markdown_table_fields(worksheet_path.read_text(encoding="utf-8"))
    missing_fields = [field for field in REQUIRED_FIELDS if field not in fields]
    todo_fields = [
        field
        for field in REQUIRED_FIELDS
        if field in fields and not value_is_filled(fields[field])
    ]
    invalid_fields = find_invalid_semantic_fields(fields)
    report["checked_fields"] = REQUIRED_FIELDS
    report["missing_fields"] = missing_fields
    report["todo_fields"] = todo_fields
    report["invalid_fields"] = invalid_fields

    git_ignored = True
    git_tracked = False
    if check_git:
        if repo_root is None:
            repo_root = paper_root.parent
        repo_root = Path(repo_root)
        git_ignored = git_path_is_ignored(repo_root, worksheet_path)
        git_tracked = git_path_is_tracked(repo_root, worksheet_path)
        report["git_ignored"] = git_ignored
        report["git_tracked"] = git_tracked

    ok = (
        not missing_fields
        and not todo_fields
        and not invalid_fields
        and git_ignored
        and not git_tracked
    )
    report["ok"] = ok
    if ok:
        report["message"] = "private author gate worksheet is complete"
    else:
        report["message"] = "private author gate worksheet is incomplete"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paper-root",
        type=Path,
        default=default_paper_root(),
        help="Path to the paper root directory.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Path to the repository root for git ignore/tracked checks.",
    )
    parser.add_argument(
        "--no-git-check",
        action="store_true",
        help="Skip git ignored/tracked checks. Intended for unit tests only.",
    )
    args = parser.parse_args(argv)

    report = check_author_gate(
        args.paper_root,
        repo_root=args.repo_root,
        check_git=not args.no_git_check,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
