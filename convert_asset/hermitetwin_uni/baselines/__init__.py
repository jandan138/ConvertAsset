"""Academic hard baselines for SIGGRAPH Asia 2027 Tables 1, 2, 4, and 5.

1. High-density 3D Nonlinear Volumetric Tetrahedral FEM (Stable Neo-Hookean, Warp 1.19 CUDA) — Ground Truth
2. Classic Discrete Elastic Rods (DER, Bergou et al. 2008/2010) — Rigid-section 1D rod baseline
3. Official Linear C0 Codimensional IPC (C-IPC, Li et al. 2021 via ipctk 1.6.1) — Linear C0 shell/contact baseline
"""

from .cipc_linear_baseline import (
    C0DiscreteShellMesh,
    CIPCLinearShellBaseline,
    build_c0_rect_shell_mesh,
)
from .der_rod_baseline import (
    DERBaselineResult,
    DERRodMesh,
    DiscreteElasticRodBaseline,
    build_der_straight_rod,
)
from .fem3d_tet_warp import (
    HollowTetMesh3D,
    StableNeoHookeanTetSolver,
    TetFEMResult,
    build_multilayer_hollow_tube_tet_mesh,
)

__all__ = [
    "C0DiscreteShellMesh",
    "CIPCLinearShellBaseline",
    "DERBaselineResult",
    "DERRodMesh",
    "DiscreteElasticRodBaseline",
    "HollowTetMesh3D",
    "StableNeoHookeanTetSolver",
    "TetFEMResult",
    "build_c0_rect_shell_mesh",
    "build_der_straight_rod",
    "build_multilayer_hollow_tube_tet_mesh",
]

