"""Hose Softbody v1.0: Route A (PhysX D6-DER + Method-B Barb Sleeve) & Route B (Adaptive Hollow GPU FEM)."""

from .adaptive_hollow_tet_mesh import (
    AdaptiveHollowTubeMesh,
    build_adaptive_hollow_tube_tet_mesh,
    compute_cuff_hoop_and_pinch_strain,
)
from .cosserat_twist_skinning import (
    build_cosserat_twist_stripe_tube,
    extract_twist_angles_from_link_frames,
)
from .specs_v10 import (
    BarbCuffMicroSpringSpec,
    D6DerRodSpec,
    HoseMaterialSpecV10,
    compile_d6_der_rod_spec,
)

__all__ = [
    "AdaptiveHollowTubeMesh",
    "BarbCuffMicroSpringSpec",
    "D6DerRodSpec",
    "HoseMaterialSpecV10",
    "build_adaptive_hollow_tube_tet_mesh",
    "build_cosserat_twist_stripe_tube",
    "compile_d6_der_rod_spec",
    "compute_cuff_hoop_and_pinch_strain",
    "extract_twist_angles_from_link_frames",
]

