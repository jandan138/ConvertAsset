"""Contracts for multi_engine_deformable_bundle/v0.3 (HermiteTwin-absorbed v0.8 thin-shell spec)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import math
from typing import Any, Mapping

import numpy as np

from convert_asset.deformable_parity.contracts import ALLOWED_ENGINES
from convert_asset.deformable_v05.contracts_v05 import DEFAULT_JACOBIAN_COND_MAX


BUNDLE_SCHEMA_VERSION_V03 = "multi_engine_deformable_bundle/v0.3"
DEFAULT_SHELL_TRUST_REGION_DQ = float(math.log(4.0))


class EvidenceTierV08(str, Enum):
    """Honest evidence grading tiers for thin-shell digital twin pipelines."""

    FAST_CHECK_CPU_PREVIEW = "FAST_CHECK_CPU_PREVIEW"
    NATIVE_SIM_A_B = "NATIVE_SIM_A_B"
    MULTI_ENGINE_PARITY_VERIFIED = "MULTI_ENGINE_PARITY_VERIFIED"
    STUDIO_CYCLES_AGX_NATIVE_VERIFIED = "STUDIO_CYCLES_AGX_NATIVE_VERIFIED"
    REAL_VIDEO_TWIN = "REAL_VIDEO_TWIN"


@dataclass(frozen=True)
class HermiteShellSpec:
    """Declarative specification for a C1 bicubic Hermite Kirchhoff-Love shell + dense contact."""

    asset_id: str
    structural_family: str
    nx: int
    ny: int
    length_u_m: float
    length_v_m: float
    thickness_m: float
    area_density_kg_m2: float
    youngs_modulus_pa: float
    poissons_ratio: float
    bending_stiffness_scale: float = 1.0
    membrane_stiffness_scale: float = 1.0
    rayleigh_mass_damp: float = 0.8
    rayleigh_stiff_damp: float = 0.008
    contact_nu: int = 24
    contact_nv: int = 24
    capture_radius_m: float = 0.018
    clamp_stiffness_n_m: float = 3800.0
    coulomb_friction_mu: float = 0.85
    release_clearance_m: float = 0.012

    def __post_init__(self) -> None:
        if self.structural_family not in ("cloth_sheet", "shell", "garment"):
            raise ValueError(f"Unsupported thin-shell family {self.structural_family!r}")
        if self.nx < 1 or self.ny < 1:
            raise ValueError(f"Grid elements (nx, ny) must be >= 1, got {(self.nx, self.ny)}")
        if self.length_u_m <= 0.0 or self.length_v_m <= 0.0 or self.thickness_m <= 0.0:
            raise ValueError("Shell dimensions and thickness must be positive")
        if self.youngs_modulus_pa <= 0.0 or not (-0.5 < self.poissons_ratio < 0.499):
            raise ValueError("Invalid (youngs_modulus_pa, poissons_ratio)")

    @property
    def membrane_rigidity(self) -> float:
        """Plane-stress membrane stiffness E*h/(1-nu^2) scaled by membrane_stiffness_scale."""
        return float(
            self.membrane_stiffness_scale
            * self.youngs_modulus_pa
            * self.thickness_m
            / (1.0 - self.poissons_ratio ** 2)
        )

    @property
    def bending_rigidity(self) -> float:
        """Kirchhoff-Love flexural rigidity D = E*h^3/(12*(1-nu^2)) scaled by bending_stiffness_scale."""
        return float(
            self.bending_stiffness_scale
            * self.youngs_modulus_pa
            * (self.thickness_m ** 3)
            / (12.0 * (1.0 - self.poissons_ratio ** 2))
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HermiteShellSpec:
        return cls(
            asset_id=str(data["asset_id"]),
            structural_family=str(data["structural_family"]),
            nx=int(data["nx"]),
            ny=int(data["ny"]),
            length_u_m=float(data["length_u_m"]),
            length_v_m=float(data["length_v_m"]),
            thickness_m=float(data["thickness_m"]),
            area_density_kg_m2=float(data["area_density_kg_m2"]),
            youngs_modulus_pa=float(data["youngs_modulus_pa"]),
            poissons_ratio=float(data["poissons_ratio"]),
            bending_stiffness_scale=float(data.get("bending_stiffness_scale", 1.0)),
            membrane_stiffness_scale=float(data.get("membrane_stiffness_scale", 1.0)),
            rayleigh_mass_damp=float(data.get("rayleigh_mass_damp", 0.8)),
            rayleigh_stiff_damp=float(data.get("rayleigh_stiff_damp", 0.008)),
            contact_nu=int(data.get("contact_nu", 24)),
            contact_nv=int(data.get("contact_nv", 24)),
            capture_radius_m=float(data.get("capture_radius_m", 0.018)),
            clamp_stiffness_n_m=float(data.get("clamp_stiffness_n_m", 3800.0)),
            coulomb_friction_mu=float(data.get("coulomb_friction_mu", 0.85)),
            release_clearance_m=float(data.get("release_clearance_m", 0.012)),
        )


@dataclass(frozen=True)
class ThinShellCalibrationRecord:
    """Offline 2x2 local membrane/bending sensitivity calibration & identified contact tuple."""

    control_names: tuple[str, str]
    u0: tuple[float, float]
    q0_log_mem_bend: tuple[float, float]
    jacobian_A_2x2: tuple[tuple[float, float], tuple[float, float]]
    condition_number: float
    identified_contact_params: dict[str, float] = field(default_factory=dict)
    trust_region_delta_q_max: float = DEFAULT_SHELL_TRUST_REGION_DQ

    def jacobian_matrix(self) -> np.ndarray:
        return np.asarray(self.jacobian_A_2x2, dtype=np.float64)

    def is_well_conditioned(self, max_cond: float = DEFAULT_JACOBIAN_COND_MAX) -> bool:
        a = self.jacobian_matrix()
        det = float(np.linalg.det(a))
        return bool(np.all(np.isfinite(a)) and abs(det) > 1e-9 and self.condition_number <= max_cond)

    def solve_control_delta(
        self,
        delta_q: tuple[float, float] | np.ndarray,
        *,
        clamp_to_trust_region: bool = True,
    ) -> tuple[np.ndarray, np.ndarray]:
        dq = np.asarray(delta_q, dtype=np.float64).reshape(2)
        if not np.all(np.isfinite(dq)):
            raise ValueError(f"Non-finite delta_q: {dq!r}")
        if clamp_to_trust_region:
            lim = float(self.trust_region_delta_q_max)
            dq = np.clip(dq, -lim, lim)
        a = self.jacobian_matrix()
        if abs(float(np.linalg.det(a))) <= 1e-12:
            raise ValueError("Singular thin-shell calibration Jacobian A_2x2")
        du = np.linalg.solve(a, dq)
        return du, dq

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_names": list(self.control_names),
            "u0": [float(self.u0[0]), float(self.u0[1])],
            "q0_log_mem_bend": [float(self.q0_log_mem_bend[0]), float(self.q0_log_mem_bend[1])],
            "jacobian_A_2x2": [
                [float(self.jacobian_A_2x2[0][0]), float(self.jacobian_A_2x2[0][1])],
                [float(self.jacobian_A_2x2[1][0]), float(self.jacobian_A_2x2[1][1])],
            ],
            "condition_number": float(self.condition_number),
            "identified_contact_params": {str(k): float(v) for k, v in self.identified_contact_params.items()},
            "trust_region_delta_q_max": float(self.trust_region_delta_q_max),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ThinShellCalibrationRecord:
        cn = data["control_names"]
        u0_raw = data["u0"]
        q0_raw = data["q0_log_mem_bend"]
        a_raw = data["jacobian_A_2x2"]
        return cls(
            control_names=(str(cn[0]), str(cn[1])),
            u0=(float(u0_raw[0]), float(u0_raw[1])),
            q0_log_mem_bend=(float(q0_raw[0]), float(q0_raw[1])),
            jacobian_A_2x2=(
                (float(a_raw[0][0]), float(a_raw[0][1])),
                (float(a_raw[1][0]), float(a_raw[1][1])),
            ),
            condition_number=float(data["condition_number"]),
            identified_contact_params={
                str(k): float(v) for k, v in dict(data.get("identified_contact_params", {})).items()
            },
            trust_region_delta_q_max=float(
                data.get("trust_region_delta_q_max", DEFAULT_SHELL_TRUST_REGION_DQ)
            ),
        )


@dataclass(frozen=True)
class ThinShellBundleManifestV03:
    """v0.3 multi-engine thin-shell bundle manifest supporting HermiteTwin + 4 engines + 3DGS."""

    asset_id: str
    hermite_spec: HermiteShellSpec
    calibration_record: ThinShellCalibrationRecord
    engine_overlays: dict[str, dict[str, Any]]
    gs_binding_relpath: str
    evidence_tier: str = EvidenceTierV08.FAST_CHECK_CPU_PREVIEW.value
    source_sha256: str = ""
    schema_version: str = BUNDLE_SCHEMA_VERSION_V03

    def __post_init__(self) -> None:
        unknown = set(self.engine_overlays.keys()) - set(ALLOWED_ENGINES)
        if unknown:
            raise ValueError(f"Unsupported engine keys in bundle/v0.3: {sorted(unknown)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "asset_id": self.asset_id,
            "hermite_spec": self.hermite_spec.to_dict(),
            "calibration_record": self.calibration_record.to_dict(),
            "engine_overlays": {str(k): dict(v) for k, v in self.engine_overlays.items()},
            "gs_binding_relpath": self.gs_binding_relpath,
            "evidence_tier": self.evidence_tier,
            "source_sha256": self.source_sha256,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ThinShellBundleManifestV03:
        return cls(
            asset_id=str(data["asset_id"]),
            hermite_spec=HermiteShellSpec.from_dict(data["hermite_spec"]),
            calibration_record=ThinShellCalibrationRecord.from_dict(data["calibration_record"]),
            engine_overlays={str(k): dict(v) for k, v in dict(data["engine_overlays"]).items()},
            gs_binding_relpath=str(data["gs_binding_relpath"]),
            evidence_tier=str(data.get("evidence_tier", EvidenceTierV08.FAST_CHECK_CPU_PREVIEW.value)),
            source_sha256=str(data.get("source_sha256", "")),
            schema_version=str(data.get("schema_version", BUNDLE_SCHEMA_VERSION_V03)),
        )
