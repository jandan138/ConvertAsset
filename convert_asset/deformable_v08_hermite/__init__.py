"""HermiteTwin (arXiv:2611.27282) thin-shell digital twin & A/B comparison package (v0.8)."""

from __future__ import annotations

from .bicubic_hermite_shell import (
    HermiteShellMesh,
    HermiteShellSimulator,
    build_hermite_shell_mesh,
    evaluate_dense_surface,
)
from .contracts_v08 import (
    BUNDLE_SCHEMA_VERSION_V03,
    EvidenceTierV08,
    HermiteShellSpec,
    ThinShellBundleManifestV03,
    ThinShellCalibrationRecord,
)
from .four_engine_shell_compiler import (
    compile_thin_shell_bundle_v03,
)
from .hermite_gs_binding import (
    bind_gaussians_to_hermite_shell,
    render_hermite_3dgs_frame,
)
from .material_space_grasp import (
    MaterialSpaceContactModel,
    RigidObstacleBox,
)
from .real_video_cloth_intake import (
    ThinShellVideoObservationSpec,
    build_thin_shell_video_intake_manifest,
)
from .spring_mass_baseline import (
    SpringMassShellBaseline,
    SpringMassShellConfig,
)
from .sysid_cmaes_adjoint import (
    SysIDResult,
    run_two_stage_sysid,
)

__all__ = [
    "BUNDLE_SCHEMA_VERSION_V03",
    "EvidenceTierV08",
    "HermiteShellMesh",
    "HermiteShellSimulator",
    "HermiteShellSpec",
    "MaterialSpaceContactModel",
    "RigidObstacleBox",
    "SpringMassShellBaseline",
    "SpringMassShellConfig",
    "SysIDResult",
    "ThinShellBundleManifestV03",
    "ThinShellCalibrationRecord",
    "ThinShellVideoObservationSpec",
    "bind_gaussians_to_hermite_shell",
    "build_hermite_shell_mesh",
    "build_thin_shell_video_intake_manifest",
    "compile_thin_shell_bundle_v03",
    "evaluate_dense_surface",
    "render_hermite_3dgs_frame",
    "run_two_stage_sysid",
]
