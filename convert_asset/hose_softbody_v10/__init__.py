"""Route A (D6-DER) and Route B (PhysX 5 GPU FEM) hose soft-body builders & specs (v10 / v10.1)."""

from .adaptive_hollow_tet_mesh import (
    AdaptiveHollowTubeMesh,
    build_adaptive_hollow_tube_tet_mesh,
    build_coaxial_barb_hose_centerline,
    compute_cuff_hoop_and_pinch_strain,
)
from .cosserat_twist_skinning import build_cosserat_twist_stripe_tube, extract_twist_angles_from_link_frames
from .specs_v10 import (
    DEFAULT_CONDENSER_BARB_V10,
    SURGICAL_LATEX_V10_1_SPEC,
    BarbCuffMicroSpringSpec,
    CondenserBarbGeometryV10,
    D6DerRodSpec,
    HoseMaterialSpecV10,
    compile_d6_der_rod_spec,
)

__all__ = [
    "AdaptiveHollowTubeMesh",
    "BarbCuffMicroSpringSpec",
    "CondenserBarbGeometryV10",
    "D6DerRodSpec",
    "DEFAULT_CONDENSER_BARB_V10",
    "HoseMaterialSpecV10",
    "SURGICAL_LATEX_V10_1_SPEC",
    "build_adaptive_hollow_tube_tet_mesh",
    "build_coaxial_barb_hose_centerline",
    "build_cosserat_twist_stripe_tube",
    "compile_d6_der_rod_spec",
    "compute_cuff_hoop_and_pinch_strain",
    "extract_twist_angles_from_link_frames",
]
