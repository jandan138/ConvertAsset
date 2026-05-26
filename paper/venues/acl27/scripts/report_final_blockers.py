#!/usr/bin/env python3
"""Report remaining ACL/ARR final-upload blockers without leaking private data."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


REQUIRED_COMMANDS = (
    "python paper/venues/acl27/scripts/check_author_gate.py",
    "python paper/venues/acl27/scripts/run_preupload_gate.py",
)
HUMAN_ALWAYS_PENDING = (
    "target_route_author_confirmation_pending",
    "official_openreview_form_copy_pending",
    "author_runtime_ai_media_approval_pending",
)
FINAL_NEXT_ACTIONS = (
    "Create and fill paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md.",
    "Choose EACL 2027 via ARR now, or wait for Annual ACL 2027 official policy.",
    "Copy the final metadata/checklist text into the real OpenReview form.",
    "Run check_author_gate.py and run_preupload_gate.py on the exact upload state.",
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


def author_gate_module():
    script = Path(__file__).with_name("check_author_gate.py")
    return load_script_module(script, "acl_author_gate")


def integrity_fingerprint_module():
    script = Path(__file__).with_name("check_integrity_fingerprint.py")
    return load_script_module(script, "acl_integrity_fingerprint")


def openreview_checklist_module():
    script = Path(__file__).with_name("check_openreview_checklist.py")
    return load_script_module(script, "acl_openreview_checklist")


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
    for relpath in (
        "venues/acl27/OPENREVIEW_METADATA_PACKET.md",
        "venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md",
        "venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md",
        "venues/acl27/TARGET_LOCK_OPENREVIEW_REHEARSAL.md",
    ):
        if not (paper_root / relpath).is_file():
            blockers.append(f"missing_{relpath}")
    return blockers


def author_gate_blockers(
    paper_root: Path, repo_root: Path, *, check_git: bool
) -> list[str]:
    report = author_gate_module().check_author_gate(
        paper_root,
        repo_root=repo_root,
        check_git=check_git,
    )
    if report["ok"]:
        return []
    if report["missing_private_worksheet"]:
        return ["private_author_gate_missing"]
    return ["private_author_gate_incomplete"]


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
    human_blockers = author_gate_blockers(
        paper_root,
        repo_root,
        check_git=check_git,
    )
    human_blockers.extend(HUMAN_ALWAYS_PENDING)
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
        "required_commands": list(REQUIRED_COMMANDS),
        "next_actions": list(FINAL_NEXT_ACTIONS),
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
