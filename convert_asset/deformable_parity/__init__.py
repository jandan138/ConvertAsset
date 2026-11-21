"""Four-engine deformable asset parity compiler and verification contracts (M1)."""

from __future__ import annotations

from .compiler import compile_multi_engine_deformable_bundle
from .contracts import (
    BUNDLE_SCHEMA_VERSION,
    CALIBRATION_LOSS_MAX,
    DAMAGE_THRESHOLD_DEFAULT,
    VERIFICATION_LOSS_MAX,
    DeformableIntegrityBudget,
    DeformableSourceSpec,
    EngineParityEntry,
    MultiEngineDeformableBundleManifest,
    ProbeResponseSummary,
    compute_probe_discrepancy_loss,
    edge_stretch_strain,
    evaluate_integrity_readout,
    naive_rfws_strain_from_F,
    polar_stretch_strain_from_F,
)
from .rfws_intake import (
    build_grid_cloth_mesh,
    build_pilot_flexible_wiping_cloth_spec,
    build_pilot_fragile_chocopie_tofu_spec,
    build_subdivided_box_mesh,
    load_rfws_asset_record,
)
from .tet_utils import (
    build_arched_cloth_points,
    build_voxel_tet_mesh,
    compute_tet_deformation_gradients,
    vertical_span_m,
)

__all__ = [
    "BUNDLE_SCHEMA_VERSION",
    "CALIBRATION_LOSS_MAX",
    "DAMAGE_THRESHOLD_DEFAULT",
    "VERIFICATION_LOSS_MAX",
    "DeformableIntegrityBudget",
    "DeformableSourceSpec",
    "EngineParityEntry",
    "MultiEngineDeformableBundleManifest",
    "ProbeResponseSummary",
    "build_arched_cloth_points",
    "build_grid_cloth_mesh",
    "build_pilot_flexible_wiping_cloth_spec",
    "build_pilot_fragile_chocopie_tofu_spec",
    "build_subdivided_box_mesh",
    "build_voxel_tet_mesh",
    "compile_multi_engine_deformable_bundle",
    "compute_probe_discrepancy_loss",
    "compute_tet_deformation_gradients",
    "edge_stretch_strain",
    "evaluate_integrity_readout",
    "load_rfws_asset_record",
    "naive_rfws_strain_from_F",
    "polar_stretch_strain_from_F",
    "vertical_span_m",
]
