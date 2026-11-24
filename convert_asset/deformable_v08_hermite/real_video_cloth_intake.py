"""Public real-video thin-shell (cloth/foam) intake manifest builder with SHA-256 provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path


@dataclass(frozen=True)
class ThinShellVideoObservationSpec:
    """Provenance-tracked multi-view/RGB-D video observation descriptor for thin-shell Real2Sim."""

    clip_id: str
    source_type: str  # real_external_video | continuum_reference_gt
    source_url: str
    camera_count: int
    total_frames: int
    train_split_frame: int
    fps: float
    sha256_manifest: dict[str, str]


def build_thin_shell_video_intake_manifest(
    *,
    clip_id: str,
    video_dir: str | Path,
    source_url: str,
    camera_count: int,
    total_frames: int,
    train_split_frame: int,
    fps: float = 24.0,
) -> ThinShellVideoObservationSpec:
    """Scan local real multi-view cloth video clip directory and lock SHA-256 file receipts."""
    root = Path(video_dir)
    if not root.exists():
        raise FileNotFoundError(f"Real thin-shell video clip directory not found: {root}")
    hashes: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h = sha256()
            with p.open("rb") as f:
                while chunk := f.read(1024 * 1024):
                    h.update(chunk)
            hashes[p.relative_to(root).as_posix()] = h.hexdigest()

    return ThinShellVideoObservationSpec(
        clip_id=clip_id,
        source_type="real_external_video" if hashes else "continuum_reference_gt",
        source_url=source_url,
        camera_count=int(camera_count),
        total_frames=int(total_frames),
        train_split_frame=int(train_split_frame),
        fps=float(fps),
        sha256_manifest=hashes,
    )


def write_thin_shell_video_intake_json(
    spec: ThinShellVideoObservationSpec,
    out_path: str | Path,
) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(spec), indent=2), encoding="utf-8")
    return p
