"""v0.5 MorphTwin-absorbed deformable contracts, response carriers, and multi-engine morph compiler."""

from .contracts_v05 import (
    BUNDLE_SCHEMA_VERSION_V02,
    DEFAULT_JACOBIAN_COND_MAX,
    DEFAULT_TRUST_REGION_DELTA_Q_MAX,
    FractureBudgetV02,
    MorphCalibrationRecord,
    MultiEngineDeformableBundleV02,
    VolumetricShearProbeSummary,
    bulk_shear_from_young_poisson,
    young_poisson_from_bulk_shear,
)
from .morph_compiler import (
    apply_material_morph,
    compile_deformable_bundle_v02,
    transfer_material_response,
)
from .response_carriers import (
    RelaxableSpringGraph,
    build_relaxable_carrier_graph,
    calibrate_carrier_graph,
    evaluate_reduced_bulk_shear_energy,
    simulate_explicit_with_fracture,
)

__all__ = [
    "BUNDLE_SCHEMA_VERSION_V02",
    "DEFAULT_JACOBIAN_COND_MAX",
    "DEFAULT_TRUST_REGION_DELTA_Q_MAX",
    "FractureBudgetV02",
    "MorphCalibrationRecord",
    "MultiEngineDeformableBundleV02",
    "RelaxableSpringGraph",
    "VolumetricShearProbeSummary",
    "apply_material_morph",
    "build_relaxable_carrier_graph",
    "bulk_shear_from_young_poisson",
    "calibrate_carrier_graph",
    "compile_deformable_bundle_v02",
    "evaluate_reduced_bulk_shear_energy",
    "simulate_explicit_with_fracture",
    "transfer_material_response",
    "young_poisson_from_bulk_shear",
]

