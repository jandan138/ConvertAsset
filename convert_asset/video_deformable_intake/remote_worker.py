"""Remote GPU worker entrypoint for real video -> MorphTwin inversion (Colab Pro+ / RTX 4090).

Strictly lazy-imports heavy vision stacks (`sam2`, `cotracker`, `trellis`, `gsplat`, `torch`)
so local Windows authoring and CI remain lightweight per dev/AGENTS.md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RemoteVideoIntakeConfig:
    """Configuration payload dispatched to Colab Pro+ A100/L4 or remote RTX 4090 worker."""

    video_dir: str
    output_dir: str
    asset_id: str
    category: str
    structural_family: str = "soft_solid"
    modality: str = "egocentric_stereo"
    sam2_checkpoint: str = "facebook/sam2.1-hiera-large"
    cotracker_checkpoint: str = "facebook/cotracker3"
    trellis_checkpoint: str = "microsoft/TRELLIS-image-large"
    fit_3dgs: bool = True
    device: str = "cuda:0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_colab_worker_command(
    config: RemoteVideoIntakeConfig,
    *,
    ultrasync_root: str = "/content/drive/MyDrive/UltraSync/ConvertAsset/remote_runs",
) -> str:
    """Emit a deterministic CLI invocation for Google Colab Pro+ / remote GPU execution."""
    return (
        "python -m convert_asset.video_deformable_intake.remote_worker "
        f"--video-dir {config.video_dir} "
        f"--output-dir {ultrasync_root}/{config.asset_id} "
        f"--asset-id {config.asset_id} "
        f"--category {config.category} "
        f"--structural-family {config.structural_family} "
        f"--modality {config.modality} "
        f"--device {config.device}"
    )


def check_remote_gpu_dependencies() -> dict[str, bool]:
    """Non-destructive probe reporting which optional heavy GPU vision stacks are installed."""
    availability: dict[str, bool] = {}
    for mod_name in ("torch", "sam2", "cotracker", "trellis", "gsplat"):
        try:
            __import__(mod_name)
            availability[mod_name] = True
        except Exception:
            availability[mod_name] = False
    return availability


def run_remote_video_intake(config: RemoteVideoIntakeConfig) -> Path:
    """Execute full real-video SAM2 + CoTracker3 + TRELLIS + carrier fit on a remote GPU host."""
    deps = check_remote_gpu_dependencies()
    missing = [k for k, ok in deps.items() if not ok and (k != "gsplat" or config.fit_3dgs)]
    if missing:
        raise RuntimeError(
            "Remote GPU video intake requires optional dependencies not installed in this lightweight host: "
            f"{missing}. Route execution to Colab Pro+ A100/L4 or remote RTX 4090 via UltraSync."
        )
    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raise NotImplementedError(
        "Bind local SAM2/CoTracker3/TRELLIS model checkpoints on the target GPU host before running."
    )

