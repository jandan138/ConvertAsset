#!/usr/bin/env python3
"""Run the local ACL/ARR pre-upload gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


PACKET_ID = "acl27_arr_candidate_20260526"
EXPECTED_PACKET_FILES = (
    "main.pdf",
    "openreview/METADATA.md",
    "openreview/RESPONSIBLE_NLP_CHECKLIST.md",
    "supplemental/README.md",
    "supplemental/manifest.json",
)
PRIVATE_TOKENS = (
    "/cpfs",
    "/home/",
    "/root",
    "zhuzihou",
    "jandan138",
    "github.com/jandan138",
    "ConvertAsset.git",
)
ACK_TOKENS = (
    "Acknowledg",
    "thanks",
    "Acknowledgment",
)
LATEX_UNRESOLVED_PATTERNS = (
    "undefined citations",
    "undefined references",
    "Citation `",
    "Reference `",
    "No file main.bbl",
)
PDF_EXPECTED_TOTAL_PAGES = 9
PDF_MAX_MAIN_CONTENT_PAGES = 8
PDF_REQUIRED_PAGE_SIZE_LABEL = "A4"
PDF_REQUIRED_VERSION = "1.5"
PDF_REQUIRED_TEXT = (
    "Material Conversion as a Controlled Perturbation",
    "Anonymous ACL submission",
    "Figure 3:",
    "Limitations",
    "Figure 4:",
    "Ethical Considerations",
    "References",
)
PDF_ORDERED_SECTION_TEXT = (
    "Figure 4:",
    "Discussion",
    "Conclusion",
    "Limitations",
)
PDF_NONCOUNTED_FIRST_SECTION = "Limitations"
NONCOUNTED_SECTION_FILES = (
    "sections/limitations.tex",
    "sections/ethical-considerations.tex",
)
NONCOUNTED_FORBIDDEN_SOURCE_RE = re.compile(
    r"\\begin\{(?:figure|table)\*?\}|\\includegraphics|\\input\{tables/"
)
PDF_PRE_LIMITATION_FLOAT_ONLY_MARKER_SETS = (
    (
        "Table 5: Material-effect scope matrix",
        "Table 6: Official KuJiaLe / InteriorAgent scene",
    ),
)
PDF_PRE_LIMITATION_BODY_MARKERS = (
    "Discussion",
    "The contribution is a measurement protocol",
    "Conclusion",
    "This paper treats synthetic-scene material conversion",
)
PDF_EXPECTED_LAYOUT_MARKERS = {
    5: ("Figure 2:", "Table 2:", "Table 3:"),
    6: ("Table 4:", "Table 5:", "Figure 3:"),
    7: ("Table 6:", "Figure 4:", "Discussion", "Conclusion"),
    8: ("Limitations", "Ethical Considerations", "References"),
}


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def build_preupload_plan(repo_root: Path) -> list[dict[str, object]]:
    paper_root = repo_root / "paper"
    packet_root = paper_root / "submissions" / PACKET_ID
    return [
        {
            "id": "claim_boundaries",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/check_claim_boundaries.py",
            ],
        },
        {
            "id": "target_policy",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/check_target_policy.py",
            ],
        },
        {
            "id": "metadata_consistency",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/check_metadata_consistency.py",
            ],
        },
        {
            "id": "openreview_checklist",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/check_openreview_checklist.py",
            ],
        },
        {
            "id": "noncounted_source_scan",
            "function": "check_noncounted_section_sources",
            "path": paper_root / "venues" / "acl27",
        },
        {
            "id": "citation_inventory",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/check_citation_inventory.py",
            ],
        },
        {
            "id": "evidence_numbers",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/check_evidence_numbers.py",
            ],
        },
        {
            "id": "integrity_fingerprint",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/check_integrity_fingerprint.py",
            ],
        },
        {
            "id": "final_blocker_report",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/report_final_blockers.py",
            ],
        },
        {
            "id": "goal_completion_report",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/report_goal_completion.py",
            ],
        },
        {
            "id": "focused_pytest",
            "command": [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_acl_submission_staging.py",
                "tests/test_acl_paper_figures_v3.py",
                "tests/test_acl_method_chain_v4_pptx.py",
                "tests/test_acl_internnav_rollout_v4.py",
                "tests/test_paper_layout.py",
                "tests/test_acl_target_policy.py",
                "tests/test_acl_metadata_consistency.py",
                "tests/test_acl_openreview_checklist.py",
                "tests/test_acl_openreview_upload_runbook.py",
                "tests/test_acl_claim_boundaries.py",
                "tests/test_acl_citation_inventory.py",
                "tests/test_acl_integrity_fingerprint.py",
                "tests/test_acl_final_blockers.py",
                "tests/test_acl_evidence_numbers.py",
                "tests/test_acl_author_gate.py",
                "tests/test_acl_author_gate_init.py",
                "tests/test_acl_author_gate_prefill.py",
                "tests/test_acl_goal_completion_report.py",
                "tests/test_render_scene_evidence_figure.py",
                "tests/test_acl_preupload_gate.py",
            ],
        },
        {
            "id": "clean_acl_build",
            "command": ["make", "-C", "paper", "clean-acl27", "acl27"],
        },
        {
            "id": "latex_log_scan",
            "function": "check_latex_log",
            "path": paper_root / "venues" / "acl27" / "build" / "main.log",
        },
        {
            "id": "stage_packet",
            "command": [
                sys.executable,
                "paper/venues/acl27/scripts/stage_submission_packet.py",
                "--force",
            ],
        },
        {
            "id": "packet_inventory",
            "function": "check_packet_inventory",
            "path": packet_root,
        },
        {
            "id": "packet_checksum_sidecar",
            "function": "check_packet_checksum_sidecar",
            "path": packet_root,
        },
        {
            "id": "packet_private_scan",
            "function": "scan_private_tokens",
            "path": packet_root,
        },
        {
            "id": "packet_acknowledgment_scan",
            "function": "scan_acknowledgment_tokens",
            "path": packet_root,
        },
        {
            "id": "pdfinfo",
            "command": ["pdfinfo", str(packet_root / "main.pdf")],
        },
        {
            "id": "pdf_profile",
            "function": "check_pdf_profile",
            "path": packet_root / "main.pdf",
        },
        {
            "id": "pdftotext_sections",
            "function": "check_pdf_text",
            "path": packet_root / "main.pdf",
        },
    ]


def run_command(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(command), flush=True)
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
    )


def check_latex_log(log_path: Path) -> None:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    matches = [pattern for pattern in LATEX_UNRESOLVED_PATTERNS if pattern in text]
    if matches:
        raise ValueError(f"{log_path} contains unresolved LaTeX marker(s): {matches}")


def check_noncounted_section_sources(venue_root: Path) -> None:
    violations: list[str] = []
    for relative in NONCOUNTED_SECTION_FILES:
        path = venue_root / relative
        text = path.read_text(encoding="utf-8")
        if NONCOUNTED_FORBIDDEN_SOURCE_RE.search(text):
            violations.append(relative)
    if violations:
        raise ValueError(
            "non-counted Limitations/Ethical Considerations sections contain "
            f"figure or table source: {violations}"
        )


def check_packet_inventory(packet_root: Path) -> None:
    actual = sorted(
        str(path.relative_to(packet_root))
        for path in packet_root.rglob("*")
        if path.is_file()
    )
    expected = sorted(EXPECTED_PACKET_FILES)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    if missing or unexpected:
        raise ValueError(
            f"packet inventory mismatch: missing={missing}, unexpected={unexpected}"
        )


def packet_checksum_path(packet_root: Path) -> Path:
    return packet_root.with_name(packet_root.name + ".sha256")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_checksum_sidecar(checksum_path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        checksum_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", raw_line)
        if not match:
            raise ValueError(f"malformed checksum line {line_number}: {raw_line}")
        relative_path = Path(match.group(2))
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"unsafe checksum path on line {line_number}: {raw_line}")
        checksums[match.group(2)] = match.group(1)
    return checksums


def check_packet_checksum_sidecar(packet_root: Path) -> None:
    checksum_path = packet_checksum_path(packet_root)
    if not checksum_path.exists():
        raise ValueError(f"missing packet checksum sidecar: {checksum_path}")

    checksums = parse_checksum_sidecar(checksum_path)
    expected = sorted(EXPECTED_PACKET_FILES)
    actual = sorted(checksums)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    if missing or unexpected:
        raise ValueError(
            f"packet checksum inventory mismatch: missing={missing}, unexpected={unexpected}"
        )

    mismatches = []
    for relative_path in expected:
        digest = file_sha256(packet_root / relative_path)
        if digest != checksums[relative_path]:
            mismatches.append(relative_path)
    if mismatches:
        raise ValueError(f"packet checksum mismatch: {mismatches}")


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {
            ".json",
            ".md",
            ".txt",
            ".tex",
            ".bib",
        }:
            yield path


def scan_text_forbidden_tokens(
    root: Path, *, tokens: tuple[str, ...], label: str
) -> None:
    violations: list[str] = []
    for path in iter_text_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in tokens:
            if token in text:
                violations.append(f"{path}: {label} {token}")
    if violations:
        raise ValueError("; ".join(violations))


def parse_pdfinfo_output(output: str) -> dict[str, object]:
    profile: dict[str, object] = {}
    for line in output.splitlines():
        if line.startswith("Pages:"):
            profile["pages"] = int(line.split(":", 1)[1].strip())
        elif line.startswith("Page size:"):
            match = re.search(r"\(([^)]+)\)", line)
            profile["page_size_label"] = match.group(1) if match else ""
        elif line.startswith("PDF version:"):
            profile["pdf_version"] = line.split(":", 1)[1].strip()
    missing = [
        key
        for key in ("pages", "page_size_label", "pdf_version")
        if key not in profile
    ]
    if missing:
        raise ValueError(f"pdfinfo output is missing field(s): {missing}")
    return profile


def validate_pdf_profile(profile: dict[str, object]) -> None:
    pages = int(profile["pages"])
    page_size_label = str(profile["page_size_label"])
    pdf_version = str(profile["pdf_version"])

    if pages != PDF_EXPECTED_TOTAL_PAGES:
        raise ValueError(
            f"PDF page count {pages} does not match the reviewed layout "
            f"({PDF_EXPECTED_TOTAL_PAGES})"
        )
    if page_size_label != PDF_REQUIRED_PAGE_SIZE_LABEL:
        raise ValueError(
            f"PDF page size {page_size_label!r} is not "
            f"{PDF_REQUIRED_PAGE_SIZE_LABEL!r}"
        )
    if pdf_version != PDF_REQUIRED_VERSION:
        raise ValueError(
            f"PDF version {pdf_version!r} is not {PDF_REQUIRED_VERSION!r}"
        )


def check_pdf_profile(pdf_path: Path) -> None:
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    validate_pdf_profile(parse_pdfinfo_output(result.stdout))


def validate_pdf_text_markers(text: str) -> None:
    missing = [token for token in PDF_REQUIRED_TEXT if token not in text]
    if missing:
        raise ValueError(f"PDF text is missing required marker(s): {missing}")

    positions = [text.index(token) for token in PDF_ORDERED_SECTION_TEXT]
    if positions != sorted(positions):
        raise ValueError(
            "PDF section markers are out of order: "
            + " -> ".join(PDF_ORDERED_SECTION_TEXT)
        )

    validate_main_content_boundary(text)
    validate_no_float_only_prelimitations_page(text)


def validate_reviewed_layout_pages(text: str) -> None:
    pages = text.split("\f")
    while pages and not pages[-1].strip():
        pages.pop()
    if len(pages) != PDF_EXPECTED_TOTAL_PAGES:
        raise ValueError(
            f"PDF text has {len(pages)} pages; expected "
            f"{PDF_EXPECTED_TOTAL_PAGES} reviewed pages"
        )

    for page_number, markers in PDF_EXPECTED_LAYOUT_MARKERS.items():
        page = pages[page_number - 1]
        missing = [marker for marker in markers if marker not in page]
        if missing:
            raise ValueError(
                f"reviewed page {page_number} is missing marker(s): {missing}"
            )


def validate_main_content_boundary(text: str) -> None:
    pages = text.split("\f")
    marker_pages = [
        index
        for index, page in enumerate(pages, start=1)
        if PDF_NONCOUNTED_FIRST_SECTION in page
    ]
    if not marker_pages:
        raise ValueError(
            f"PDF text is missing {PDF_NONCOUNTED_FIRST_SECTION!r} for page budget"
        )

    first_noncounted_page = marker_pages[0]
    if first_noncounted_page > PDF_MAX_MAIN_CONTENT_PAGES + 1:
        raise ValueError(
            f"{PDF_NONCOUNTED_FIRST_SECTION} starts on page "
            f"{first_noncounted_page}, after the allowed main-content boundary "
            f"page {PDF_MAX_MAIN_CONTENT_PAGES + 1}"
        )

    for page_number in range(PDF_MAX_MAIN_CONTENT_PAGES + 1, first_noncounted_page):
        if pages[page_number - 1].strip():
            raise ValueError(
                f"main content spills onto page {page_number} before "
                f"{PDF_NONCOUNTED_FIRST_SECTION}"
            )

    prefix = pages[first_noncounted_page - 1].split(
        PDF_NONCOUNTED_FIRST_SECTION, 1
    )[0]
    if re.sub(r"[\s\d]+", "", prefix):
        if first_noncounted_page <= PDF_MAX_MAIN_CONTENT_PAGES:
            return
        raise ValueError(
            f"main content appears before {PDF_NONCOUNTED_FIRST_SECTION} "
            f"on page {first_noncounted_page}"
        )


def validate_no_float_only_prelimitations_page(text: str) -> None:
    pages = text.split("\f")
    marker_pages = [
        index
        for index, page in enumerate(pages, start=1)
        if PDF_NONCOUNTED_FIRST_SECTION in page
    ]
    if not marker_pages:
        return

    first_noncounted_page = marker_pages[0]
    if first_noncounted_page <= 1:
        return

    preceding_page = re.sub(r"\s+", " ", pages[first_noncounted_page - 2])
    has_body_text = any(marker in preceding_page for marker in PDF_PRE_LIMITATION_BODY_MARKERS)
    for marker_set in PDF_PRE_LIMITATION_FLOAT_ONLY_MARKER_SETS:
        if all(marker in preceding_page for marker in marker_set) and not has_body_text:
            raise ValueError(
                "float-only material table page appears before "
                f"{PDF_NONCOUNTED_FIRST_SECTION}"
            )


def check_pdf_text(pdf_path: Path) -> None:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    try:
        validate_pdf_text_markers(result.stdout)
        validate_reviewed_layout_pages(result.stdout)
    except ValueError as exc:
        raise ValueError(f"{pdf_path}: {exc}") from exc


def run_function_step(step: dict[str, object]) -> None:
    function = step["function"]
    path = Path(step["path"])
    if function == "check_latex_log":
        check_latex_log(path)
    elif function == "check_packet_inventory":
        check_packet_inventory(path)
    elif function == "check_packet_checksum_sidecar":
        check_packet_checksum_sidecar(path)
    elif function == "scan_private_tokens":
        scan_text_forbidden_tokens(path, tokens=PRIVATE_TOKENS, label="private token")
    elif function == "scan_acknowledgment_tokens":
        scan_text_forbidden_tokens(path, tokens=ACK_TOKENS, label="acknowledgment token")
    elif function == "check_pdf_profile":
        check_pdf_profile(path)
    elif function == "check_pdf_text":
        check_pdf_text(path)
    elif function == "check_noncounted_section_sources":
        check_noncounted_section_sources(path)
    else:
        raise ValueError(f"unknown function step: {function}")


def run_preupload_gate(repo_root: Path, *, dry_run: bool = False) -> dict[str, object]:
    plan = build_preupload_plan(repo_root)
    completed: list[str] = []
    if dry_run:
        return {"ok": True, "dry_run": True, "steps": plan, "completed": completed}

    for step in plan:
        print(f"== {step['id']} ==", flush=True)
        if "command" in step:
            run_command(step["command"], cwd=repo_root)
        else:
            run_function_step(step)
        completed.append(str(step["id"]))

    return {"ok": True, "dry_run": False, "steps": plan, "completed": completed}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_repo_root())
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_preupload_gate(args.repo_root.resolve(), dry_run=args.dry_run)
    print(json.dumps(report, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
