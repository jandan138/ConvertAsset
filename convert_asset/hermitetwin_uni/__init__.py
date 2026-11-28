"""HermiteTwin-Uni: Unified C1-Hermite Continuous Mechanics for 1D Brazier-Cosserat Rods & 2D Thin Shells.

Phase 0/1 foundation targeting SIGGRAPH Asia 2027 (with CGF 2027 fallback):
- Unified 1D Cubic Hermite + Cosserat + Brazier hollow-tube mechanics (10 scalar DOFs/node)
- Manifestly SPD exact Brazier (1927) bending-ovalization inertia tensor
- NVIDIA Warp 1.19 CUDA kernels + exact Implicit Adjoint sensitivity solver
- Zero-copy Warp <-> PyTorch 2.11 bridge ready for anisotropic gsplat 3DGS coupling
"""

from .gsplat_c1_renderer import (
    CameraSpec,
    HermiteRodGaussianRenderer,
    HermiteShellGaussianRenderer,
    build_3olive_barb_gaussians,
    render_anisotropic_3dgs_torch,
    render_composite_3dgs_torch,
)
from .ipc_proxy_contact_warp import (
    BarbInterferenceResult,
    conservative_ccd_max_step_1d_barb,
    evaluate_rod_on_3olive_barb_contact,
    evaluate_rod_to_shell_ipc_contact,
    evaluate_two_rod_ipc_contact,
    ipc_barrier_val_grad_hess,
    mollified_coulomb_friction,
)
from .real_to_sim_sysid import (
    MultiViewTargetFrame,
    PixelSysIDResult,
    evaluate_multiview_pixel_loss_and_grad_q,
    run_two_stage_3dgs_adjoint_sysid,
)
from .real_video_bv_sysid import (
    RealHoseObservation,
    RealVideoSysIDReport,
    extract_bv17_real_hoses,
    run_bv17_real_video_sysid_and_zeroshot,
)
from .rod_brazier_warp import (
    BrazierRodSimulationResult,
    ImplicitAdjointResult,
    WarpBrazierRodSolver,
    analytical_brazier_critical_values,
)
from .shell_kl_warp import (
    HermiteShellMesh,
    ShellStepResult,
    WarpKirchhoffLoveShellSolver,
    build_hermite_shell_mesh,
)
from .ipctk_c1_contact import (
    IPCTKC1ContactSystem,
    RigidProxySpec,
    RodProxySpec,
    ShellProxySpec,
    build_rod_proxy_topology,
    build_shell_proxy_topology,
    eval_rod_proxy_vertices_and_jacobian,
)
from .sparse_solver_v2 import (
    SparseSceneStepResult,
    SparseUnifiedSceneSolver,
    solve_sparse_linear_warp_gpu,
    solve_sparse_spd_with_shift,
)
from .state_and_basis import (
    HermiteRodMesh,
    HermiteRodSpec,
    build_curved_rod_mesh_and_q0,
    build_straight_rod_mesh,
    evaluate_brazier_tube_surface,
    hermite_1d_basis,
)
from .unified_solver import (
    TwoRodCrossingResult,
    UnifiedRodShellSolver,
    UnifiedStepResult,
    solve_3olive_barb_interference_fit,
    solve_two_rod_crossing_pinch,
)

__all__ = [
    "BarbInterferenceResult",
    "BrazierRodSimulationResult",
    "HermiteRodMesh",
    "HermiteRodSpec",
    "HermiteShellMesh",
    "ImplicitAdjointResult",
    "ShellStepResult",
    "UnifiedRodShellSolver",
    "UnifiedStepResult",
    "WarpBrazierRodSolver",
    "WarpKirchhoffLoveShellSolver",
    "analytical_brazier_critical_values",
    "build_hermite_shell_mesh",
    "build_straight_rod_mesh",
    "conservative_ccd_max_step_1d_barb",
    "evaluate_brazier_tube_surface",
    "evaluate_rod_on_3olive_barb_contact",
    "evaluate_rod_to_shell_ipc_contact",
    "hermite_1d_basis",
    "ipc_barrier_val_grad_hess",
    "mollified_coulomb_friction",
    "solve_3olive_barb_interference_fit",
]

