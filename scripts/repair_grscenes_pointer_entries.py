#!/usr/bin/env python3
"""Replace GRScenes text pointer entries with scratch-local symlinks."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_ENTRY_NAMES = {"Materials", "models"}
MAX_POINTER_BYTES = 4096
LOCAL_MATERIAL_REF = b"./Materials/"
MISSING_MATERIALS_POLICIES = {"referenced", "all_instance_dirs"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _absolute_without_resolve(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _iter_pointer_candidates(root: Path, *, entry_names: set[str]) -> Iterable[Path]:
    if root.is_file() and root.name in entry_names:
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [dirname for dirname in dirnames if not (Path(dirpath) / dirname).is_symlink()]
        for filename in filenames:
            if filename in entry_names:
                yield Path(dirpath) / filename


def _read_pointer_text(path: Path) -> str:
    if path.stat().st_size > MAX_POINTER_BYTES:
        raise ValueError(f"pointer file too large: {path.stat().st_size}")
    data = path.read_bytes()
    if b"\x00" in data:
        raise ValueError("pointer file contains NUL bytes")
    text = data.decode("utf-8").strip()
    if not text:
        raise ValueError("pointer file is empty")
    target = Path(text)
    if target.is_absolute():
        raise ValueError(f"pointer target must be relative: {text}")
    return text


def _replace_with_symlink(path: Path, target_text: str) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp-symlink.{os.getpid()}")
    if tmp_path.exists() or tmp_path.is_symlink():
        tmp_path.unlink()
    os.symlink(target_text, tmp_path, target_is_directory=True)
    os.replace(tmp_path, path)


def _instance_references_local_materials(path: Path) -> bool:
    try:
        return LOCAL_MATERIAL_REF in path.read_bytes()
    except OSError:
        return False


def _material_entry_for_instance(root: Path, instance_path: Path, *, policy: str) -> Path | None:
    if not instance_path.is_absolute():
        instance_path = root / instance_path
    if instance_path.name != "instance.usd":
        raise ValueError(f"instance list entry must be named instance.usd: {instance_path}")
    if not _is_inside(_absolute_without_resolve(instance_path), _absolute_without_resolve(root)):
        raise ValueError(f"instance list entry escapes root: {instance_path}")
    directory = instance_path.parent
    material_entry = directory / "Materials"
    if material_entry.exists() or material_entry.is_symlink():
        return None
    if policy == "all_instance_dirs" or _instance_references_local_materials(instance_path):
        return material_entry
    return None


def _iter_missing_material_entries(
    root: Path,
    *,
    policy: str,
    instance_paths: Sequence[str | Path] | None = None,
) -> Iterable[Path]:
    if instance_paths is not None:
        for instance_path in instance_paths:
            material_entry = _material_entry_for_instance(root, Path(instance_path), policy=policy)
            if material_entry is not None:
                yield material_entry
        return

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [dirname for dirname in dirnames if not (Path(dirpath) / dirname).is_symlink()]
        if "instance.usd" not in filenames:
            continue
        directory = Path(dirpath)
        material_entry = directory / "Materials"
        if material_entry.exists() or material_entry.is_symlink():
            continue
        if policy == "all_instance_dirs":
            yield material_entry
            continue
        instance_path = directory / "instance.usd"
        if _instance_references_local_materials(instance_path):
            yield material_entry


def repair_pointer_entries(
    root: str | Path,
    *,
    apply: bool,
    report_path: str | Path | None,
    entry_names: set[str] | None = None,
    create_missing_materials: bool = False,
    missing_materials_policy: str = "referenced",
    instance_paths: Sequence[str | Path] | None = None,
    repair_existing_pointers: bool = True,
) -> dict:
    if missing_materials_policy not in MISSING_MATERIALS_POLICIES:
        raise ValueError(f"unknown missing Materials policy: {missing_materials_policy}")

    root_path = Path(root)
    root_resolved = root_path.resolve()
    names = set(entry_names or DEFAULT_ENTRY_NAMES)
    files: list[dict] = []
    errors: list[dict] = []
    candidate_files = 0
    planned_count = 0
    repaired_count = 0
    existing_count = 0
    missing_materials_candidates = 0
    created_missing_materials_count = 0
    planned_missing_materials_count = 0
    instance_list_count = len(instance_paths) if instance_paths is not None else None

    if repair_existing_pointers:
        for path in _iter_pointer_candidates(root_path, entry_names=names):
            candidate_files += 1
            try:
                if path.is_symlink():
                    existing_count += 1
                    files.append({"path": str(path), "status": "exists", "target": os.readlink(path)})
                    continue
                if not path.is_file():
                    raise ValueError("candidate is not a regular file or symlink")
                target_text = _read_pointer_text(path)
                target_resolved = (path.parent / target_text).resolve()
                if not _is_inside(target_resolved, root_resolved):
                    raise ValueError(f"pointer target escapes root: {target_text}")
                if not target_resolved.exists():
                    raise ValueError(f"pointer target does not exist: {target_text}")
                if not target_resolved.is_dir():
                    raise ValueError(f"pointer target is not a directory: {target_text}")
                record = {
                    "path": str(path),
                    "status": "planned" if not apply else "repaired",
                    "target": target_text,
                    "target_resolved": str(target_resolved),
                    "bytes_before": path.stat().st_size,
                }
                planned_count += 0 if apply else 1
                if apply:
                    _replace_with_symlink(path, target_text)
                    repaired_count += 1
                files.append(record)
            except Exception as exc:  # pragma: no cover - report defensive path
                errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})

    if create_missing_materials:
        shared_materials = root_path / "Materials"
        shared_materials_resolved = shared_materials.resolve()
        for path in _iter_missing_material_entries(
            root_path,
            policy=missing_materials_policy,
            instance_paths=instance_paths,
        ):
            missing_materials_candidates += 1
            try:
                if not shared_materials_resolved.exists() or not shared_materials_resolved.is_dir():
                    raise ValueError(f"shared Materials directory missing: {shared_materials}")
                target_text = os.path.relpath(shared_materials, start=path.parent)
                record = {
                    "path": str(path),
                    "status": "planned_missing" if not apply else "created_missing",
                    "target": target_text,
                    "target_resolved": str(shared_materials_resolved),
                    "kind": "missing_materials_entry",
                }
                if apply:
                    _replace_with_symlink(path, target_text)
                    created_missing_materials_count += 1
                else:
                    planned_missing_materials_count += 1
                files.append(record)
            except Exception as exc:  # pragma: no cover - report defensive path
                errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})

    summary = {
        "schema_version": 1,
        "generated_at_utc": _utc_now(),
        "applied": apply,
        "root": str(root_path),
        "entry_names": sorted(names),
        "repair_existing_pointers": repair_existing_pointers,
        "candidate_files": candidate_files,
        "planned_count": planned_count,
        "repaired_count": repaired_count,
        "existing_count": existing_count,
        "create_missing_materials": create_missing_materials,
        "missing_materials_policy": missing_materials_policy,
        "instance_list_count": instance_list_count,
        "missing_materials_candidates": missing_materials_candidates,
        "planned_missing_materials_count": planned_missing_materials_count,
        "created_missing_materials_count": created_missing_materials_count,
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
    parser.add_argument("root", type=Path)
    parser.add_argument("--apply", action="store_true", help="replace pointer files with symlinks")
    parser.add_argument("--dry-run", action="store_true", help="explicit dry-run alias for the default")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--entry-name", action="append", dest="entry_names", help="entry basename to repair")
    parser.add_argument(
        "--skip-existing-pointer-scan",
        action="store_true",
        help="skip scanning existing Materials/models pointer files; useful with --instance-list repairs",
    )
    parser.add_argument(
        "--create-missing-materials",
        action="store_true",
        help="create missing Materials symlinks beside instance.usd files that reference ./Materials/",
    )
    parser.add_argument(
        "--missing-materials-policy",
        choices=sorted(MISSING_MATERIALS_POLICIES),
        default="referenced",
        help=(
            "how to choose instance.usd directories for missing Materials symlinks; "
            "referenced scans readable USD bytes for ./Materials/, all_instance_dirs repairs every missing instance directory"
        ),
    )
    parser.add_argument(
        "--instance-list",
        type=Path,
        help="newline-delimited list of instance.usd paths to scan for missing Materials entries",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.apply and args.dry_run:
        raise SystemExit("--apply and --dry-run cannot be used together")
    instance_paths = None
    if args.instance_list is not None:
        instance_paths = [
            line.strip()
            for line in args.instance_list.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    summary = repair_pointer_entries(
        args.root,
        apply=bool(args.apply),
        report_path=args.report,
        entry_names=set(args.entry_names) if args.entry_names else None,
        create_missing_materials=bool(args.create_missing_materials),
        missing_materials_policy=args.missing_materials_policy,
        instance_paths=instance_paths,
        repair_existing_pointers=not args.skip_existing_pointer_scan,
    )
    print(
        json.dumps(
            {
                "applied": summary["applied"],
                "candidate_files": summary["candidate_files"],
                "planned_count": summary["planned_count"],
                "repaired_count": summary["repaired_count"],
                "existing_count": summary["existing_count"],
                "missing_materials_candidates": summary["missing_materials_candidates"],
                "created_missing_materials_count": summary["created_missing_materials_count"],
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
