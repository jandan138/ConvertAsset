#!/usr/bin/env python3
"""Check that the final integrity audit still matches current ACL sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCHEMA_VERSION = 1
DEFAULT_FINGERPRINT_RELPATH = (
    "venues/acl27/FINAL_INTEGRITY_SOURCE_FINGERPRINT.json"
)
DEFAULT_SOURCE_PATTERNS = (
    "venues/acl27/main.tex",
    "venues/acl27/sections/*.tex",
    "shared/sections/appendix.tex",
    "shared/tables/*.tex",
    "shared/references.bib",
    "venues/acl27/OPENREVIEW_METADATA_PACKET.md",
    "venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md",
    "venues/acl27/TARGET_CALL_POLICY_AUDIT.md",
    "venues/acl27/TARGET_LOCK_OPENREVIEW_REHEARSAL.md",
    "shared/evidence/references/verification_report.md",
    "shared/evidence/raw/image_quality.csv",
    "shared/evidence/raw/feature_similarity.csv",
    "shared/tables/grscenes_vlm_clean_pool_pass15.csv",
    "shared/tables/grscenes_vlm_stress_expanded30.csv",
    "shared/tables/reviewer_closure_paired_ci.csv",
    "shared/tables/material_effect_risk_matrix.csv",
    "shared/tables/official_scene_performance_summary.csv",
    "shared/tables/vlm_coordinate_baselines.csv",
    "shared/evidence/raw/internnav_vln_downstream/"
    "official_val_unseen_99/paired_99_summary.json",
    "shared/evidence/raw/official_scene_submission_closure/"
    "official_scene_submission_closure_summary.json",
)


def default_paper_root() -> Path:
    return Path(__file__).resolve().parents[3]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_relpath(path: str | Path) -> str:
    relpath = Path(path)
    if relpath.is_absolute() or ".." in relpath.parts:
        raise ValueError(f"unsafe source path: {path}")
    return relpath.as_posix()


def default_source_relpaths(paper_root: Path) -> tuple[str, ...]:
    relpaths: set[str] = set()
    for pattern in DEFAULT_SOURCE_PATTERNS:
        matches = sorted(paper_root.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"integrity source pattern matched no files: {pattern}")
        for path in matches:
            if path.is_file():
                relpaths.add(path.relative_to(paper_root).as_posix())
    return tuple(sorted(relpaths))


def iter_source_paths(
    paper_root: Path, *, source_relpaths: tuple[str, ...] | None = None
):
    relpaths = source_relpaths or default_source_relpaths(paper_root)
    for relpath in sorted(normalize_relpath(path) for path in relpaths):
        path = paper_root / relpath
        if not path.is_file():
            raise FileNotFoundError(f"missing integrity source file: {relpath}")
        yield path


def build_fingerprint(
    paper_root: Path, *, source_relpaths: tuple[str, ...] | None = None
) -> dict[str, object]:
    paper_root = paper_root.resolve()
    sources = []
    for path in iter_source_paths(paper_root, source_relpaths=source_relpaths):
        sources.append(
            {
                "path": path.relative_to(paper_root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "purpose": (
            "Guards the ACL final-integrity delta audit against stale "
            "manuscript, bibliography, policy, and evidence sources."
        ),
        "source_root": "paper",
        "source_count": len(sources),
        "sources": sources,
    }


def write_fingerprint(fingerprint: dict[str, object], fingerprint_path: Path) -> None:
    fingerprint_path.parent.mkdir(parents=True, exist_ok=True)
    fingerprint_path.write_text(
        json.dumps(fingerprint, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_fingerprint(fingerprint_path: Path) -> dict[str, object]:
    if not fingerprint_path.is_file():
        raise FileNotFoundError(f"missing integrity fingerprint: {fingerprint_path}")
    return json.loads(fingerprint_path.read_text(encoding="utf-8"))


def summarize_mismatch(
    recorded: dict[str, object], current: dict[str, object]
) -> dict[str, list[str]]:
    recorded_sources = {
        str(item["path"]): item for item in recorded.get("sources", [])
    }
    current_sources = {str(item["path"]): item for item in current.get("sources", [])}
    recorded_paths = set(recorded_sources)
    current_paths = set(current_sources)
    changed = sorted(
        path
        for path in recorded_paths & current_paths
        if recorded_sources[path] != current_sources[path]
    )
    return {
        "missing": sorted(recorded_paths - current_paths),
        "unexpected": sorted(current_paths - recorded_paths),
        "changed": changed,
    }


def check_fingerprint(
    paper_root: Path,
    *,
    fingerprint_path: Path | None = None,
    source_relpaths: tuple[str, ...] | None = None,
) -> dict[str, object]:
    fingerprint_path = fingerprint_path or paper_root / DEFAULT_FINGERPRINT_RELPATH
    recorded = load_fingerprint(fingerprint_path)
    current = build_fingerprint(paper_root, source_relpaths=source_relpaths)
    if recorded != current:
        mismatch = summarize_mismatch(recorded, current)
        raise ValueError(f"integrity fingerprint mismatch: {mismatch}")
    return {"ok": True, "source_count": current["source_count"], "fingerprint": current}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-root", type=Path, default=default_paper_root())
    parser.add_argument(
        "--fingerprint-path",
        type=Path,
        default=None,
        help="Defaults to venues/acl27/FINAL_INTEGRITY_SOURCE_FINGERPRINT.json.",
    )
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paper_root = args.paper_root.resolve()
    fingerprint_path = args.fingerprint_path or paper_root / DEFAULT_FINGERPRINT_RELPATH
    if args.write:
        fingerprint = build_fingerprint(paper_root)
        write_fingerprint(fingerprint, fingerprint_path)
        report = {
            "ok": True,
            "wrote": str(fingerprint_path),
            "source_count": fingerprint["source_count"],
        }
    else:
        report = check_fingerprint(paper_root, fingerprint_path=fingerprint_path)
        report = {
            "ok": True,
            "checked": str(fingerprint_path),
            "source_count": report["source_count"],
        }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
