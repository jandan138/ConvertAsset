"""Video-to-Deformable Real-to-Sim intake contracts, synthetic CI proxy, and remote GPU worker (M2)."""

from .contracts import (
    VIDEO_OBSERVATION_SCHEMA_VERSION,
    MorphTwinInversionReceipt,
    VideoObservationManifest,
    import_morphtwin_export,
)
from .remote_worker import RemoteVideoIntakeConfig, build_colab_worker_command
from .synthetic_proxy import SyntheticVideoProxyProvider, invert_deformable_from_observation

__all__ = [
    "VIDEO_OBSERVATION_SCHEMA_VERSION",
    "MorphTwinInversionReceipt",
    "RemoteVideoIntakeConfig",
    "SyntheticVideoProxyProvider",
    "VideoObservationManifest",
    "build_colab_worker_command",
    "import_morphtwin_export",
    "invert_deformable_from_observation",
]

