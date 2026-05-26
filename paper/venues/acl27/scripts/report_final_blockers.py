#!/usr/bin/env python3
"""Report remaining ACL/ARR final-upload blockers without leaking private data."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


REQUIRED_COMMANDS = (
    "python paper/venues/acl27/scripts/init_author_gate.py",
    "python paper/venues/acl27/scripts/prefill_author_gate.py --apply",
    "python paper/venues/acl27/scripts/check_author_gate.py",
    "python paper/venues/acl27/scripts/run_preupload_gate.py",
)
HUMAN_PENDING_UNTIL_AUTHOR_GATE_COMPLETE = (
    "target_route_author_confirmation_pending",
    "official_openreview_form_copy_pending",
    "author_runtime_ai_media_approval_pending",
)
MISSING_AUTHOR_GATE_NEXT_ACTION = (
    (
        "Run init_author_gate.py to create and then fill "
        "paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md."
    )
)
INCOMPLETE_AUTHOR_GATE_NEXT_ACTION = (
    "Run python paper/venues/acl27/scripts/prefill_author_gate.py --apply for "
    "repo-verifiable rows, then complete or correct "
    "paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md and run "
    "check_author_gate.py."
)
FINAL_ROUTE_NEXT_ACTION = (
    "Choose EACL 2027 via ARR now, or wait for Annual ACL 2027 official policy."
)
OPENREVIEW_COPY_NEXT_ACTION = (
    "Copy the final metadata/checklist text into the real OpenReview form."
)
FINAL_GATE_NEXT_ACTION = (
    "Run run_preupload_gate.py, then "
    "prefill_author_gate.py --apply --overwrite, then check_author_gate.py and "
    "report_final_blockers.py on the exact upload state."
)
HUMAN_BLOCKER_HANDOFFS = {
    "private_author_gate_missing": {
        "required_action": (
            "Run python paper/venues/acl27/scripts/init_author_gate.py to create "
            "the ignored private copy "
            "paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md."
        ),
        "worksheet_fields": [],
        "copy_sources": [
            "OPENREVIEW_AUTHOR_GATE_WORKSHEET.md",
            "OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md",
        ],
        "done_when": "check_author_gate.py passes on the ignored private copy.",
    },
    "private_author_gate_incomplete": {
        "required_action": (
            "Complete or correct the ignored private author-gate worksheet."
        ),
        "worksheet_fields": [],
        "copy_sources": [
            "OPENREVIEW_AUTHOR_GATE_WORKSHEET.md",
            "OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md",
        ],
        "done_when": (
            "check_author_gate.py reports ok=true without printing private values; "
            "use its missing_fields, todo_fields, and invalid_fields names."
        ),
    },
    "target_route_author_confirmation_pending": {
        "required_action": (
            "Choose the final ACL-family route and record the route/policy rows "
            "in the private worksheet."
        ),
        "worksheet_fields": [
            "Selected route",
            "Final policy refresh date",
            "Target deadline",
            "Commitment venue if ARR-reviewed",
        ],
        "copy_sources": [
            "TARGET_CALL_POLICY_AUDIT.md",
            "TARGET_LOCK_OPENREVIEW_REHEARSAL.md",
            "OPENREVIEW_METADATA_PACKET.md",
        ],
        "done_when": "route rows are positively filled and final decision is upload.",
    },
    "official_openreview_form_copy_pending": {
        "required_action": (
            "Copy final title, abstract, area, keywords, and Responsible NLP "
            "answers into the official OpenReview form."
        ),
        "worksheet_fields": [
            "Title approved",
            "Abstract approved and under current venue limit",
            "Primary ARR area approved",
            "Secondary area / keywords approved",
            "Responsible NLP checklist copied into OpenReview",
        ],
        "copy_sources": [
            "OPENREVIEW_METADATA_PACKET.md",
            "OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md",
        ],
        "done_when": (
            "OpenReview form-copy rows are positively approved/copied in the "
            "private worksheet."
        ),
    },
    "author_runtime_ai_media_approval_pending": {
        "required_action": (
            "Record final author, runtime, AI-assistance, license, media, scan, "
            "and upload decisions in the private worksheet."
        ),
        "worksheet_fields": [
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
            "Runtime / compute wording approved",
            "AI-assistance wording approved",
            "Model and asset license wording approved",
            "Optional media decision",
            "Undefined citation/reference scan",
            "Local path / username / private-link scan",
            "Acknowledgment scan",
            "Limitations / Ethical Considerations / References text scan",
            "Final decision: upload / do not upload",
        ],
        "copy_sources": [
            "COMPUTE_RUNTIME_SUMMARY_DRAFT.md",
            "MODEL_AND_ASSET_LICENSE_AUDIT.md",
            "ARTIFACT_PROVENANCE_DRAFT.md",
            "OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md",
            "FINAL_SUBMISSION_PACKET_CHECKLIST.md",
        ],
        "done_when": (
            "all listed private rows use positive approval/pass/upload semantics."
        ),
    },
}


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_paper_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_script_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def author_gate_module():
    script = Path(__file__).with_name("check_author_gate.py")
    return load_script_module(script, "acl_author_gate")


def integrity_fingerprint_module():
    script = Path(__file__).with_name("check_integrity_fingerprint.py")
    return load_script_module(script, "acl_integrity_fingerprint")


def openreview_checklist_module():
    script = Path(__file__).with_name("check_openreview_checklist.py")
    return load_script_module(script, "acl_openreview_checklist")


def target_policy_module():
    script = Path(__file__).with_name("check_target_policy.py")
    return load_script_module(script, "acl_target_policy")


def repo_evidence_blockers(paper_root: Path, repo_root: Path) -> list[str]:
    blockers: list[str] = []
    if not (repo_root / "paper/venues/acl27/scripts/run_preupload_gate.py").is_file():
        blockers.append("preupload_runner_missing")
    try:
        integrity_fingerprint_module().check_fingerprint(paper_root)
    except Exception:
        blockers.append("integrity_fingerprint_missing_or_stale")
    try:
        checklist_report = openreview_checklist_module().check_openreview_checklist(
            paper_root
        )
        if not checklist_report["ok"]:
            blockers.append("openreview_checklist_missing_or_incomplete")
    except Exception:
        blockers.append("openreview_checklist_missing_or_incomplete")
    try:
        target_policy_report = target_policy_module().check_target_policy(paper_root)
        if not target_policy_report["ok"]:
            blockers.append("target_policy_missing_or_unsafe")
    except Exception:
        blockers.append("target_policy_missing_or_unsafe")
    for relpath in (
        "venues/acl27/OPENREVIEW_METADATA_PACKET.md",
        "venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md",
        "venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md",
        "venues/acl27/TARGET_LOCK_OPENREVIEW_REHEARSAL.md",
    ):
        if not (paper_root / relpath).is_file():
            blockers.append(f"missing_{relpath}")
    return blockers


def author_gate_report(
    paper_root: Path, repo_root: Path, *, check_git: bool
) -> dict[str, object]:
    return author_gate_module().check_author_gate(
        paper_root,
        repo_root=repo_root,
        check_git=check_git,
    )


def author_gate_blockers_from_report(report: dict[str, object]) -> list[str]:
    if report["ok"]:
        return []
    if report["missing_private_worksheet"]:
        return ["private_author_gate_missing"]
    return ["private_author_gate_incomplete"]


def author_gate_blockers(
    paper_root: Path, repo_root: Path, *, check_git: bool
) -> list[str]:
    report = author_gate_report(
        paper_root,
        check_git=check_git,
        repo_root=repo_root,
    )
    return author_gate_blockers_from_report(report)


def safe_author_gate_status(report: dict[str, object]) -> dict[str, object]:
    """Return author-gate status metadata without private worksheet values."""
    missing_fields = list(report.get("missing_fields") or [])
    todo_fields = list(report.get("todo_fields") or [])
    invalid_fields = list(report.get("invalid_fields") or [])
    checked_fields = list(report.get("checked_fields") or [])
    return {
        "ok": bool(report.get("ok")),
        "private_worksheet": report.get("private_worksheet"),
        "missing_private_worksheet": bool(report.get("missing_private_worksheet")),
        "checked_field_count": len(checked_fields),
        "missing_fields": missing_fields,
        "missing_field_count": len(missing_fields),
        "todo_fields": todo_fields,
        "todo_field_count": len(todo_fields),
        "invalid_fields": invalid_fields,
        "invalid_field_count": len(invalid_fields),
        "git_ignored": report.get("git_ignored"),
        "git_tracked": report.get("git_tracked"),
        "message": report.get("message", ""),
        "prints_private_author_values": False,
    }


def human_blocker_details(human_blockers: list[str]) -> dict[str, object]:
    return {
        blocker: HUMAN_BLOCKER_HANDOFFS[blocker]
        for blocker in human_blockers
        if blocker in HUMAN_BLOCKER_HANDOFFS
    }


def next_actions_for(human_blockers: list[str]) -> list[str]:
    actions: list[str] = []
    if "private_author_gate_missing" in human_blockers:
        actions.append(MISSING_AUTHOR_GATE_NEXT_ACTION)
    elif "private_author_gate_incomplete" in human_blockers:
        actions.append(INCOMPLETE_AUTHOR_GATE_NEXT_ACTION)
    if "target_route_author_confirmation_pending" in human_blockers:
        actions.append(FINAL_ROUTE_NEXT_ACTION)
    if "official_openreview_form_copy_pending" in human_blockers:
        actions.append(OPENREVIEW_COPY_NEXT_ACTION)
    actions.append(FINAL_GATE_NEXT_ACTION)
    return actions


def build_final_blocker_report(
    paper_root: Path,
    *,
    repo_root: Path | None = None,
    check_git: bool = True,
    check_repo_evidence: bool = True,
) -> dict[str, object]:
    paper_root = Path(paper_root)
    repo_root = Path(repo_root) if repo_root is not None else paper_root.parent

    repo_blockers = (
        repo_evidence_blockers(paper_root, repo_root) if check_repo_evidence else []
    )
    private_author_gate_report = author_gate_report(
        paper_root,
        repo_root,
        check_git=check_git,
    )
    human_blockers = author_gate_blockers_from_report(private_author_gate_report)
    if human_blockers:
        human_blockers.extend(HUMAN_PENDING_UNTIL_AUTHOR_GATE_COMPLETE)
    human_blockers = sorted(set(human_blockers))

    upload_ready = not repo_blockers and not human_blockers
    if repo_blockers:
        status = "repo_blocked"
    elif human_blockers:
        status = "human_blocked"
    else:
        status = "upload_ready"

    return {
        "ok": True,
        "upload_ready": upload_ready,
        "status": status,
        "repo_blockers": repo_blockers,
        "human_blockers": human_blockers,
        "human_blocker_details": human_blocker_details(human_blockers),
        "private_author_gate_status": safe_author_gate_status(
            private_author_gate_report
        ),
        "required_commands": list(REQUIRED_COMMANDS),
        "next_actions": next_actions_for(human_blockers),
        "privacy": {
            "prints_private_author_values": False,
            "filled_author_worksheet_tracked": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-root", type=Path, default=default_paper_root())
    parser.add_argument("--repo-root", type=Path, default=default_repo_root())
    parser.add_argument(
        "--no-git-check",
        action="store_true",
        help="Skip private worksheet ignored/tracked checks.",
    )
    parser.add_argument(
        "--skip-repo-evidence",
        action="store_true",
        help="Skip quick repository evidence checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_final_blocker_report(
        args.paper_root.resolve(),
        repo_root=args.repo_root.resolve(),
        check_git=not args.no_git_check,
        check_repo_evidence=not args.skip_repo_evidence,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
