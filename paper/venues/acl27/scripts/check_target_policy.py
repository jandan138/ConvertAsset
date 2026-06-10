#!/usr/bin/env python3
"""Check ACL/ARR target-policy notes for candidate-safe route wording."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


POLICY_FILES = (
    "TARGET_CALL_POLICY_AUDIT.md",
    "TARGET_LOCK_OPENREVIEW_REHEARSAL.md",
)

REQUIRED_URLS = (
    "https://aclrollingreview.org/dates",
    "https://aclrollingreview.org/authors",
    "https://aclrollingreview.org/authorchecklist",
    "https://acl-org.github.io/ACLPUB/formatting.html",
    "https://acl-org.github.io/ACLPUB/review-version.html",
    "https://www.aclweb.org/adminwiki/index.php/ACL_Resolutions",
    "https://2027.eacl.org/",
    "https://2027.eacl.org/calls/papers/",
)

REQUIRED_MARKERS = (
    "Checked: 2026-05-30.",
    "EACL 2027",
    "August 3, 2026",
    "October 11, 2026",
    "comprehensive CFP",
    "detailed timetable",
    "Annual ACL 2027",
    "2027 ACL Conference Branding",
    "No public official Annual ACL 2027 CFP",
    "not an Annual-ACL-final packet",
    "OpenReview",
    "reviewer-registration",
)

FORBIDDEN_FINAL_CLAIM_RE = re.compile(
    r"Annual ACL 2027\s+(?:final[- ]ready|ready|locked|selected|submission[- ]ready)",
    re.IGNORECASE,
)


def policy_root(paper_root: Path) -> Path:
    return paper_root / "venues" / "acl27"


def read_policy_text(paper_root: Path) -> tuple[str, dict[str, str], list[str]]:
    root = policy_root(paper_root)
    texts: dict[str, str] = {}
    missing_files: list[str] = []
    for filename in POLICY_FILES:
        path = root / filename
        if path.is_file():
            texts[filename] = path.read_text(encoding="utf-8")
        else:
            missing_files.append(filename)
            texts[filename] = ""
    return "\n".join(texts.values()), texts, missing_files


def find_forbidden_final_claims(text: str) -> list[str]:
    hits: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if FORBIDDEN_FINAL_CLAIM_RE.search(line):
            hits.append(f"line {line_no}: {line.strip()}")
    return hits


def check_target_policy(paper_root: Path) -> dict[str, object]:
    paper_root = Path(paper_root)
    combined_text, _texts, missing_files = read_policy_text(paper_root)
    missing_urls = [url for url in REQUIRED_URLS if url not in combined_text]
    missing_required_markers = [
        marker for marker in REQUIRED_MARKERS if marker not in combined_text
    ]
    forbidden_final_claim_hits = find_forbidden_final_claims(combined_text)

    annual_acl_final_ready = bool(forbidden_final_claim_hits)
    eacl_arr_public_route = (
        "EACL 2027" in combined_text
        and "August 3, 2026" in combined_text
        and "October 11, 2026" in combined_text
    )
    route_status = (
        "annual_acl_final"
        if annual_acl_final_ready
        else "acl_arr_candidate"
        if eacl_arr_public_route
        else "route_policy_incomplete"
    )
    checks = {
        "policy_files_present": not missing_files,
        "required_urls_present": not missing_urls,
        "required_markers_present": not missing_required_markers,
        "no_forbidden_annual_acl_final_claim": not forbidden_final_claim_hits,
        "eacl_arr_public_route": eacl_arr_public_route,
        "annual_acl_not_final_ready": not annual_acl_final_ready,
    }

    return {
        "ok": all(checks.values()),
        "route_status": route_status,
        "annual_acl_final_ready": annual_acl_final_ready,
        "eacl_arr_public_route": eacl_arr_public_route,
        "missing_files": missing_files,
        "missing_urls": missing_urls,
        "missing_required_markers": missing_required_markers,
        "forbidden_final_claim_hits": forbidden_final_claim_hits,
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

    report = check_target_policy(args.paper_root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
