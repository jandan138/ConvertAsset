#!/usr/bin/env python3
"""Stage the anonymous ACL/ARR review packet from tracked paper artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PACKET_ID = "acl27_arr_candidate_20260526"
DEFAULT_RELATIVE_OUT_DIR = Path("submissions") / DEFAULT_PACKET_ID
OPENREVIEW_CHECKLIST_SOURCE = Path("venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md")
OPENREVIEW_CHECKLIST_STAGED = Path("openreview/RESPONSIBLE_NLP_CHECKLIST.md")
OPENREVIEW_METADATA_SOURCE = Path("venues/acl27/OPENREVIEW_METADATA_PACKET.md")
OPENREVIEW_METADATA_STAGED = Path("openreview/METADATA.md")
FORBIDDEN_TOKENS = (
    "/cpfs",
    "/home/",
    "/root/",
    "zhuzihou",
    "jandan138",
    "github.com/jandan138",
    "ConvertAsset.git",
)


def default_paper_root() -> Path:
    return Path(__file__).resolve().parents[3]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def packet_readme(packet_id: str, *, include_media: bool) -> str:
    media_status = (
        "Selected qualitative media is excluded from this candidate packet because "
        "InteriorAgent / KuJiaLe scene-derived media needs explicit author/legal "
        "approval before redistribution."
        if not include_media
        else "Selected qualitative media was explicitly requested for inclusion."
    )
    return f"""# ACL/ARR Candidate Supplemental Packet

Packet ID: `{packet_id}`

This candidate packet is intentionally minimal. It is for anonymous review
staging of the manuscript and claim-bound supplemental inventory, not for
redistributing source scenes, generated scratch assets, model checkpoints, or
runtime logs.

## Included

- `main.pdf`: anonymous manuscript PDF built from the ACL-facing wrapper.
- `openreview/RESPONSIBLE_NLP_CHECKLIST.md`: copy-ready source material for
  the ARR/OpenReview checklist fields.
- `openreview/METADATA.md`: copy-ready title, abstract, track, and keyword
  source material for the ARR/OpenReview metadata fields.
- `manifest.json`: upload inventory and claim boundary for this candidate
  packet.

## Excluded

- Raw source scenes.
- Full scratch no-MDL USD trees.
- InternNav raw frame directories, LMDBs, and logs.
- Local model checkpoints.
- Selected qualitative videos.

{media_status}

## Claim Boundary

Use this packet for the ACL/ARR review draft only. The manuscript may describe
bounded GRScenes VLM grounding evidence, scoped official KuJiaLe InternNav
sanity evidence, and selected NVIDIA material-effect diagnostics. It must not
claim broad embodied benchmark completion, official-scene speedup, NVIDIA
official-scene performance comparison, population-level NVIDIA failure rates, or
procedural texture preservation success.
"""


def build_manifest(packet_id: str, *, include_media: bool) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "packet_id": packet_id,
        "generated_at_utc": utc_timestamp(),
        "include_media": include_media,
        "claim_boundary": "selected_media_excluded_by_default_pending_explicit_media_approval"
        if not include_media
        else "selected_media_included_after_explicit_license_and_anonymization_review",
        "files": [
            {
                "path": "main.pdf",
                "role": "anonymous_review_manuscript",
            },
            {
                "path": str(OPENREVIEW_CHECKLIST_STAGED),
                "role": "openreview_responsible_nlp_form_source",
            },
            {
                "path": str(OPENREVIEW_METADATA_STAGED),
                "role": "openreview_metadata_form_source",
            },
            {
                "path": "supplemental/README.md",
                "role": "human_readable_upload_boundary",
            },
            {
                "path": "supplemental/manifest.json",
                "role": "machine_readable_upload_inventory",
            },
        ],
        "excluded_materials": [
            "raw source scenes",
            "full scratch no-MDL USD trees",
            "InternNav raw frames",
            "InternNav LMDBs",
            "InternNav raw logs",
            "local model checkpoints",
            "selected qualitative videos",
        ],
        "remaining_gates": [
            "final selected venue policy lock",
            "final author confirmation of compute/runtime details",
            "optional selected-media redistribution legal review",
            "final OpenReview Responsible NLP checklist field completion",
        ],
    }


def assert_text_sanitized(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    leaked = [token for token in FORBIDDEN_TOKENS if token in text]
    if leaked:
        raise ValueError(f"{path} contains forbidden token(s): {', '.join(leaked)}")


def packet_checksum_path(out_dir: Path) -> Path:
    return out_dir.with_name(out_dir.name + ".sha256")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksum_sidecar(out_dir: Path, manifest: dict[str, Any]) -> Path:
    lines = []
    for item in sorted(manifest["files"], key=lambda record: record["path"]):
        relative_path = Path(item["path"])
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"Refusing unsafe packet path in manifest: {item['path']}")
        staged_path = out_dir / relative_path
        lines.append(f"{file_sha256(staged_path)}  {item['path']}")

    checksum_path = packet_checksum_path(out_dir)
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert_text_sanitized(checksum_path)
    return checksum_path


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists():
        if not force:
            raise FileExistsError(f"Refusing to overwrite existing packet directory: {out_dir}")
        shutil.rmtree(out_dir)
    (out_dir / "supplemental").mkdir(parents=True)
    (out_dir / OPENREVIEW_CHECKLIST_STAGED.parent).mkdir(parents=True)


def stage_submission_packet(
    *,
    paper_root: Path,
    out_dir: Path,
    packet_id: str = DEFAULT_PACKET_ID,
    include_media: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    if include_media:
        raise ValueError(
            "Selected media staging is intentionally disabled until license, "
            "terms-of-use, legal approval, and anonymization review are complete."
        )

    paper_root = Path(paper_root)
    out_dir = Path(out_dir)
    source_pdf = paper_root / "venues/acl27/build/main.pdf"
    checklist_source = paper_root / OPENREVIEW_CHECKLIST_SOURCE
    metadata_source = paper_root / OPENREVIEW_METADATA_SOURCE
    if not source_pdf.exists():
        raise FileNotFoundError(f"Missing ACL PDF; build it first: {source_pdf}")
    if not checklist_source.exists():
        raise FileNotFoundError(f"Missing OpenReview checklist packet: {checklist_source}")
    if not metadata_source.exists():
        raise FileNotFoundError(f"Missing OpenReview metadata packet: {metadata_source}")

    prepare_output_dir(out_dir, force=force)
    shutil.copy2(source_pdf, out_dir / "main.pdf")
    checklist_staged = out_dir / OPENREVIEW_CHECKLIST_STAGED
    shutil.copy2(checklist_source, checklist_staged)
    metadata_staged = out_dir / OPENREVIEW_METADATA_STAGED
    shutil.copy2(metadata_source, metadata_staged)

    readme_path = out_dir / "supplemental/README.md"
    readme_path.write_text(packet_readme(packet_id, include_media=include_media), encoding="utf-8")

    manifest = build_manifest(packet_id, include_media=include_media)
    manifest_path = out_dir / "supplemental/manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    assert_text_sanitized(readme_path)
    assert_text_sanitized(checklist_staged)
    assert_text_sanitized(metadata_staged)
    assert_text_sanitized(manifest_path)
    write_checksum_sidecar(out_dir, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paper-root",
        type=Path,
        default=default_paper_root(),
        help="Paper root containing venues/acl27/build/main.pdf.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=default_paper_root() / DEFAULT_RELATIVE_OUT_DIR,
        help="Destination staging directory.",
    )
    parser.add_argument("--packet-id", default=DEFAULT_PACKET_ID)
    parser.add_argument(
        "--include-media",
        action="store_true",
        help="Reserved for a future reviewed media packet; currently refused.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = stage_submission_packet(
        paper_root=args.paper_root,
        out_dir=args.out_dir,
        packet_id=args.packet_id,
        include_media=args.include_media,
        force=args.force,
    )
    print(
        json.dumps(
            {
                "out_dir": str(args.out_dir),
                "packet_id": manifest["packet_id"],
                "checksum_path": str(packet_checksum_path(args.out_dir)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
