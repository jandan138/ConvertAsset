#!/usr/bin/env python3
"""Report ACL/ARR goal-completion state without leaking private data."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections.abc import Callable
from pathlib import Path


REQUIREMENT_CHECKS = (
    (
        "claim_boundaries",
        "Unsupported broad-claim guard",
        (("check_claim_boundaries.py", "check_claim_boundaries"),),
    ),
    (
        "evidence_numbers",
        "Manuscript numbers match local evidence artifacts",
        (("check_evidence_numbers.py", "check_acl_evidence_numbers"),),
    ),
    (
        "citation_inventory",
        "Cited ACL keys have BibTeX and DOI/URL/web-trail coverage",
        (("check_citation_inventory.py", "check_citation_inventory"),),
    ),
    (
        "openreview_copy_sources",
        "OpenReview metadata and Responsible NLP copy sources are current",
        (
            ("check_metadata_consistency.py", "check_metadata_consistency"),
            ("check_openreview_checklist.py", "check_openreview_checklist"),
        ),
    ),
    (
        "target_policy",
        "ACL/ARR target policy remains candidate-safe",
        (("check_target_policy.py", "check_target_policy"),),
    ),
    (
        "integrity_fingerprint",
        "Final-integrity source fingerprint matches protected sources",
        (("check_integrity_fingerprint.py", "check_fingerprint"),),
    ),
)


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


def script_function(script_name: str, function_name: str) -> Callable[[Path], object]:
    script = Path(__file__).with_name(script_name)
    module_name = f"acl_goal_{Path(script_name).stem}"
    module = load_script_module(script, module_name)
    return getattr(module, function_name)


def summarize_checker_report(report: object) -> dict[str, object]:
    if not isinstance(report, dict):
        return {"ok": bool(report)}
    summary: dict[str, object] = {"ok": bool(report.get("ok"))}
    for key in (
        "route_status",
        "abstract_word_count",
        "cited_key_count",
        "source_count",
        "question_count",
    ):
        if key in report:
            summary[key] = report[key]
    return summary


def run_requirement(paper_root: Path, requirement: tuple[str, str, tuple[tuple[str, str], ...]]) -> dict[str, object]:
    requirement_id, label, checks = requirement
    checker_summaries: list[dict[str, object]] = []
    failures: list[str] = []
    for script_name, function_name in checks:
        checker_id = f"{Path(script_name).stem}.{function_name}"
        try:
            checker_report = script_function(script_name, function_name)(paper_root)
            summary = summarize_checker_report(checker_report)
            summary["checker"] = checker_id
            checker_summaries.append(summary)
            if not summary["ok"]:
                failures.append(checker_id)
        except Exception as exc:
            checker_summaries.append(
                {
                    "checker": checker_id,
                    "ok": False,
                    "error": exc.__class__.__name__,
                }
            )
            failures.append(checker_id)
    return {
        "id": requirement_id,
        "label": label,
        "status": "satisfied" if not failures else "repo_blocked",
        "checkers": checker_summaries,
    }


def final_blocker_module():
    script = Path(__file__).with_name("report_final_blockers.py")
    return load_script_module(script, "acl_goal_final_blockers")


def build_goal_completion_report(
    paper_root: Path,
    *,
    repo_root: Path | None = None,
    check_git: bool = True,
    check_repo_evidence: bool = True,
    preupload_gate_passed: bool = False,
) -> dict[str, object]:
    paper_root = Path(paper_root)
    repo_root = Path(repo_root) if repo_root is not None else paper_root.parent

    requirements = [
        run_requirement(paper_root, requirement)
        for requirement in REQUIREMENT_CHECKS
    ]
    final_blockers = final_blocker_module().build_final_blocker_report(
        paper_root,
        repo_root=repo_root,
        check_git=check_git,
        check_repo_evidence=check_repo_evidence,
    )

    final_clearance_status = (
        "satisfied"
        if final_blockers["upload_ready"]
        else "repo_blocked"
        if final_blockers["repo_blockers"]
        else "human_blocked"
    )
    requirements.append(
        {
            "id": "final_upload_clearance",
            "label": "Final blocker report has no repo or human blockers",
            "status": final_clearance_status,
            "checkers": [
                {
                    "checker": "report_final_blockers.build_final_blocker_report",
                    "ok": final_blockers["upload_ready"],
                    "status": final_blockers["status"],
                }
            ],
        }
    )

    repo_requirement_failures = [
        item["id"]
        for item in requirements
        if item["id"] != "final_upload_clearance"
        and item["status"] != "satisfied"
    ]
    repo_static_ready = (
        not repo_requirement_failures
        and not final_blockers["repo_blockers"]
    )
    candidate_ready_for_human_gate = (
        repo_static_ready
        and final_blockers["status"] in {"human_blocked", "upload_ready"}
    )
    final_goal_complete = (
        repo_static_ready
        and final_blockers["upload_ready"]
        and preupload_gate_passed
    )

    if not repo_static_ready or final_blockers["repo_blockers"]:
        status = "repo_blocked"
    elif final_goal_complete:
        status = "complete"
    elif final_blockers["upload_ready"]:
        status = "upload_ready_needs_fresh_preupload_gate"
    else:
        status = "candidate_ready_human_blocked"

    return {
        "ok": True,
        "status": status,
        "repo_static_ready": repo_static_ready,
        "candidate_ready_for_human_gate": candidate_ready_for_human_gate,
        "final_goal_complete": final_goal_complete,
        "fresh_preupload_gate_required_for_completion": not preupload_gate_passed,
        "repo_requirement_failures": repo_requirement_failures,
        "requirements": requirements,
        "final_blockers": {
            "status": final_blockers["status"],
            "repo_blockers": final_blockers["repo_blockers"],
            "human_blockers": final_blockers["human_blockers"],
            "human_blocker_details": final_blockers["human_blocker_details"],
        },
        "required_commands": final_blockers["required_commands"],
        "next_actions": final_blockers["next_actions"],
        "privacy": final_blockers["privacy"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-root", type=Path, default=default_paper_root())
    parser.add_argument("--repo-root", type=Path, default=default_repo_root())
    parser.add_argument(
        "--preupload-gate-passed",
        action="store_true",
        help=(
            "Only use immediately after run_preupload_gate.py passed on the "
            "same exact working tree."
        ),
    )
    args = parser.parse_args(argv)

    report = build_goal_completion_report(
        args.paper_root,
        repo_root=args.repo_root,
        preupload_gate_passed=args.preupload_gate_passed,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
