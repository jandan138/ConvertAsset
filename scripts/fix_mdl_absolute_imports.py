#!/usr/bin/env python3
"""Repair GRScenes generated MDL imports that break KooPbr module lookup."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


IMPORT_RE = re.compile(r"^(\s*)import\s+::(KooPbr|KooPbr_maps)::([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$")
HEX_MDL_RE = re.compile(r"^[0-9a-fA-F]{16,64}\.mdl$")


def should_process_mdl(name_or_path: str | Path) -> bool:
    """Return true for generated material-instance MDL files, not library MDLs."""

    name = Path(name_or_path).name
    if not name.endswith(".mdl"):
        return False
    if name in {"KooPbr.mdl", "KooPbr_maps.mdl"}:
        return False
    if name.startswith("Num") or name.startswith("OmniUe4"):
        return False
    return name.startswith("MI_") or bool(HEX_MDL_RE.fullmatch(name))


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    if line.endswith("\r"):
        return line[:-1], "\r"
    return line, ""


def repair_text(text: str) -> tuple[str, int]:
    """Rewrite KooPbr absolute imports to relative using-import statements."""

    out: list[str] = []
    replacements = 0
    for line in text.splitlines(keepends=True):
        body, ending = _split_line_ending(line)
        match = IMPORT_RE.fullmatch(body)
        if match is None:
            out.append(line)
            continue
        indent, module, symbol = match.groups()
        out.append(f"{indent}using .::{module} import {symbol};{ending}")
        replacements += 1
    return "".join(out), replacements


def _read_text_preserve_newlines(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write_text_atomic(path: Path, text: str) -> None:
    stat_result = path.stat()
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as fh:
        tmp_path = Path(fh.name)
        fh.write(text)
    os.chmod(tmp_path, stat_result.st_mode & 0o7777)
    tmp_path.replace(path)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _iter_mdl_files(root: Path, *, follow_symlinks: bool) -> Iterable[Path]:
    if root.is_file():
        if should_process_mdl(root):
            yield root
        return

    visited_dirs: set[tuple[int, int]] = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        if follow_symlinks:
            kept_dirnames = []
            for dirname in dirnames:
                candidate = Path(dirpath) / dirname
                try:
                    stat_result = candidate.stat()
                except OSError:
                    continue
                key = (stat_result.st_dev, stat_result.st_ino)
                if key in visited_dirs:
                    continue
                visited_dirs.add(key)
                kept_dirnames.append(dirname)
            dirnames[:] = kept_dirnames

        for filename in filenames:
            if should_process_mdl(filename):
                yield Path(dirpath) / filename


def _repair_file(path: Path, *, apply: bool) -> dict:
    before_bytes = path.read_bytes()
    before_text = before_bytes.decode("utf-8")
    after_text, replacements = repair_text(before_text)
    after_bytes = after_text.encode("utf-8")
    record = {
        "path": str(path),
        "replacements": replacements,
        "bytes_before": len(before_bytes),
        "bytes_after": len(after_bytes),
        "sha256_before": _sha256_bytes(before_bytes),
        "sha256_after": _sha256_bytes(after_bytes),
        "applied": bool(apply and replacements),
    }
    if apply and replacements:
        _write_text_atomic(path, after_text)
    return record


def process_roots(
    roots: Iterable[str | Path],
    *,
    apply: bool,
    follow_symlinks: bool,
    report_path: str | Path | None,
) -> dict:
    """Process roots and optionally write a JSON report."""

    root_paths = [Path(root) for root in roots]
    files: list[dict] = []
    errors: list[dict] = []
    candidate_files = 0
    seen_paths: set[str] = set()

    for root in root_paths:
        for path in _iter_mdl_files(root, follow_symlinks=follow_symlinks):
            resolved_key = str(path.resolve())
            if resolved_key in seen_paths:
                continue
            seen_paths.add(resolved_key)
            candidate_files += 1
            try:
                record = _repair_file(path, apply=apply)
            except Exception as exc:  # pragma: no cover - defensive report path
                errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
                continue
            if record["replacements"]:
                files.append(record)

    summary = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "applied": apply,
        "follow_symlinks": follow_symlinks,
        "roots": [str(path) for path in root_paths],
        "candidate_files": candidate_files,
        "changed_files": len(files),
        "total_replacements": sum(int(record["replacements"]) for record in files),
        "errors": errors,
        "files": files,
    }

    if report_path is not None:
        report = Path(report_path)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", help="MDL file or directory roots to scan")
    parser.add_argument("--apply", action="store_true", help="write repaired files; default is dry-run")
    parser.add_argument("--dry-run", action="store_true", help="explicit dry-run alias for the default")
    parser.add_argument("--follow-symlinks", action="store_true", help="follow directory symlinks while scanning")
    parser.add_argument("--report", type=Path, help="write JSON repair report")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.apply and args.dry_run:
        raise SystemExit("--apply and --dry-run cannot be used together")
    summary = process_roots(
        args.roots,
        apply=bool(args.apply),
        follow_symlinks=bool(args.follow_symlinks),
        report_path=args.report,
    )
    print(
        json.dumps(
            {
                "applied": summary["applied"],
                "candidate_files": summary["candidate_files"],
                "changed_files": summary["changed_files"],
                "total_replacements": summary["total_replacements"],
                "errors": len(summary["errors"]),
                "report": str(args.report) if args.report else None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

