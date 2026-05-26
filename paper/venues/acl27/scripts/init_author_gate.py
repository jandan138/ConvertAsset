#!/usr/bin/env python3
"""Create the ignored private ACL/OpenReview author-gate worksheet."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


PRIVATE_WORKSHEET = Path("venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md")
TEMPLATE = Path("venues/acl27/OPENREVIEW_AUTHOR_GATE_WORKSHEET.md")


def default_paper_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def git_path_is_ignored(repo_root: Path, path: Path) -> bool:
    relative = path.relative_to(repo_root)
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(relative)],
        cwd=repo_root,
        check=False,
    )
    return result.returncode == 0


def init_author_gate(
    *,
    paper_root: Path,
    template_path: Path | None = None,
    repo_root: Path | None = None,
    check_git: bool = True,
) -> dict[str, object]:
    paper_root = Path(paper_root)
    repo_root = Path(repo_root) if repo_root is not None else paper_root.parent
    template_path = Path(template_path) if template_path is not None else paper_root / TEMPLATE
    worksheet_path = paper_root / PRIVATE_WORKSHEET

    if worksheet_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing private worksheet: {PRIVATE_WORKSHEET}")
    if not template_path.exists():
        raise FileNotFoundError(f"Missing author-gate template: {template_path}")

    worksheet_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, worksheet_path)

    git_ignored: bool | None = None
    if check_git:
        git_ignored = git_path_is_ignored(repo_root, worksheet_path)
        if not git_ignored:
            worksheet_path.unlink()
            raise RuntimeError(
                f"Created worksheet path is not git-ignored; removed: {PRIVATE_WORKSHEET}"
            )

    return {
        "ok": True,
        "created": True,
        "private_worksheet": str(PRIVATE_WORKSHEET),
        "template": str(TEMPLATE),
        "git_ignored": git_ignored,
        "message": "private author-gate worksheet initialized; fill it locally only",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
        default=default_repo_root(),
        help="Path to the repository root for git ignore checks.",
    )
    parser.add_argument(
        "--no-git-check",
        action="store_true",
        help="Skip git ignored checks. Intended for unit tests only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = init_author_gate(
        paper_root=args.paper_root,
        repo_root=args.repo_root,
        check_git=not args.no_git_check,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
