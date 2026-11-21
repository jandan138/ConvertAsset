"""Contracts for multi_engine_deformable_bundle/v0.2 (MorphTwin-absorbed v0.5 spec)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Mapping

import numpy as np

from convert_asset.deformable_parity.contracts import (
    ALLOWED_ENGINES,
    DAMAGE_THRESHOLD_DEFAULT,
    DeformableIntegrityBudget,
    DeformableSourceSpec,
    EngineParityEntry,
    MultiEngineDeformableBundleManifest,
)


BUNDLE_SCHEMA_VERSION_V02 = "multi_engine_deformable_bundle/v0.2"
DEFAULT_JACOBIAN_COND_MAX = 25.0
DEFAULT_TRUST_REGION_DELTA_Q_MAX = float(math.log(4.0))
MIN_POISSON = -0.45
MAX_POISSON = 0.49


def bulk_shear_from_young_poisson(youngs_modulus_pa: float, poissons_ratio: float) -> tuple[float, float]:
    """Convert isotropic (E, nu) to 3D bulk modulus K and shear modulus G."""
    e = float(youngs_modulus_pa)
    nu = float(poissons_ratio)
    if e <= 0.0:
        raise ValueError(f"youngs_modulus_pa must be > 0, got {e}")
    if not (-0.99 < nu < 0.499):
        raise ValueError(f"poissons_ratio must lie in (-0.99, 0.499), got {nu}")
    kappa = e / (3.0 * (1.0 - 2.0 * nu))
    mu = e / (2.0 * (1.0 + nu))
    return float(kappa), float(mu)


def young_poisson_from_bulk_shear(bulk_modulus_pa: float, shear_modulus_pa: float) -> tuple[float, float]:
    """Convert 3D bulk modulus K and shear modulus G to isotropic (E, nu)."""
    k = float(bulk_modulus_pa)
    g = float(shear_modulus_pa)
    if k <= 0.0 or g <= 0.0:
        raise ValueError(f"bulk and shear moduli must be > 0, got K={k}, G={g}")
    e = (9.0 * k * g) / (3.0 * k + g)
    nu = (3.0 * k - 2.0 * g) / (2.0 * (3.0 * k + g))
    nu_clamped = float(np.clip(nu, MIN_POISSON, MAX_POISSON))
    return float(e), nu_clamped


@dataclass(frozen=True)
class MorphCalibrationRecord:
    """Offline 2x2 local energy-response calibration for one physics engine or sidecar."""

    control_names: tuple[str, str]
    u0: tuple[float, float]
    q0_log_kappa_mu: tuple[float, float]
    jacobian_A_2x2: tuple[tuple[float, float], tuple[float, float]]
    condition_number: float
    trust_region_delta_q_max: float = DEFAULT_TRUST_REGION_DELTA_Q_MAX

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
        """Map shared relative edit delta_q = [d_log_kappa, d_log_mu] to engine control offset du = A^-1 dq."""
        dq = np.asarray(delta_q, dtype=np.float64).reshape(2)
        if not np.all(np.isfinite(dq)):
            raise ValueError(f"Non-finite delta_q: {dq!r}")
        if clamp_to_trust_region:
            lim = float(self.trust_region_delta_q_max)
            dq = np.clip(dq, -lim, lim)
        a = self.jacobian_matrix()
        if abs(float(np.linalg.det(a))) <= 1e-12:
            raise ValueError("Singular calibration Jacobian A_2x2")
        du = np.linalg.solve(a, dq)
        return du, dq

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_names": list(self.control_names),
            "u0": [float(self.u0[0]), float(self.u0[1])],
            "q0_log_kappa_mu": [float(self.q0_log_kappa_mu[0]), float(self.q0_log_kappa_mu[1])],
            "jacobian_A_2x2": [
                [float(self.jacobian_A_2x2[0][0]), float(self.jacobian_A_2x2[0][1])],
                [float(self.jacobian_A_2x2[1][0]), float(self.jacobian_A_2x2[1][1])],
            ],
            "condition_number": float(self.condition_number),
            "trust_region_delta_q_max": float(self.trust_region_delta_q_max),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MorphCalibrationRecord:
        a_raw = data["jacobian_A_2x2"]
        u0_raw = data.get("u0", (0.0, 0.0))
        q0_raw = data["q0_log_kappa_mu"]
        cn = data["control_names"]
        return cls(
            control_names=(str(cn[0]), str(cn[1])),
            u0=(float(u0_raw[0]), float(u0_raw[1])),
            q0_log_kappa_mu=(float(q0_raw[0]), float(q0_raw[1])),
            jacobian_A_2x2=(
                (float(a_raw[0][0]), float(a_raw[0][1])),
                (float(a_raw[1][0]), float(a_raw[1][1])),
            ),
            condition_number=float(data["condition_number"]),
            trust_region_delta_q_max=float(
                data.get("trust_region_delta_q_max", DEFAULT_TRUST_REGION_DELTA_Q_MAX)
            ),
        )


@dataclass(frozen=True)
class VolumetricShearProbeSummary:
    """Decoupled volumetric (bulk/Poisson) and shear/bend probe verification receipt."""

    effective_bulk_pa: float
    effective_shear_pa: float
    effective_poisson: float
    verify_loss_volumetric: float
    verify_loss_shear: float
    volumetric_passed: bool
    shear_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VolumetricShearProbeSummary:
        return cls(
            effective_bulk_pa=float(data["effective_bulk_pa"]),
            effective_shear_pa=float(data["effective_shear_pa"]),
            effective_poisson=float(data["effective_poisson"]),
            verify_loss_volumetric=float(data["verify_loss_volumetric"]),
            verify_loss_shear=float(data["verify_loss_shear"]),
            volumetric_passed=bool(data["volumetric_passed"]),
            shear_passed=bool(data["shear_passed"]),
        )


@dataclass(frozen=True)
class FractureBudgetV02:
    """Volumetric/deviatoric split integrity & irreversible fracture thresholds."""

    fragility_tier: str
    strain_metric: str = "polar_volumetric_deviatoric"
    volumetric_onset_a: float = 0.12
    volumetric_failure_b: float = 0.35
    deviatoric_onset_a: float = 0.15
    deviatoric_failure_b: float = 0.45
    fracture_strain_threshold: float = 0.50
    damage_threshold: float = DAMAGE_THRESHOLD_DEFAULT
    max_normal_force_n: float = 4.5
    max_shear_force_n: float = 2.0

    def to_legacy_v01(self) -> DeformableIntegrityBudget:
        return DeformableIntegrityBudget(
            fragility_tier=self.fragility_tier,
            strain_metric=self.strain_metric,
            strain_onset_a=self.deviatoric_onset_a,
            strain_failure_b=self.deviatoric_failure_b,
            damage_threshold=self.damage_threshold,
            max_normal_force_n=self.max_normal_force_n,
            max_shear_force_n=self.max_shear_force_n,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FractureBudgetV02:
        return cls(
            fragility_tier=str(data.get("fragility_tier", "medium")),
            strain_metric=str(data.get("strain_metric", "polar_volumetric_deviatoric")),
            volumetric_onset_a=float(data.get("volumetric_onset_a", 0.12)),
            volumetric_failure_b=float(data.get("volumetric_failure_b", 0.35)),
            deviatoric_onset_a=float(data.get("deviatoric_onset_a", data.get("strain_onset_a", 0.15))),
            deviatoric_failure_b=float(data.get("deviatoric_failure_b", data.get("strain_failure_b", 0.45))),
            fracture_strain_threshold=float(data.get("fracture_strain_threshold", 0.50)),
            damage_threshold=float(data.get("damage_threshold", DAMAGE_THRESHOLD_DEFAULT)),
            max_normal_force_n=float(data.get("max_normal_force_n", 4.5)),
            max_shear_force_n=float(data.get("max_shear_force_n", 2.0)),
        )


@dataclass(frozen=True)
class EngineMorphEntryV02:
    """Per-engine parity + decoupled volumetric/shear calibration record in bundle/v0.2."""

    engine_id: str
    solver: str
    artifact_relpath: str
    effective_params: dict[str, Any]
    fit_loss_drop: float
    verify_loss_compression: float
    volumetric_shear_probe: VolumetricShearProbeSummary
    morph_calibration: MorphCalibrationRecord
    parity_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "solver": self.solver,
            "artifact_relpath": self.artifact_relpath,
            "effective_params": dict(self.effective_params),
            "fit_loss_drop": float(self.fit_loss_drop),
            "verify_loss_compression": float(self.verify_loss_compression),
            "volumetric_shear_probe": self.volumetric_shear_probe.to_dict(),
            "morph_calibration": self.morph_calibration.to_dict(),
            "parity_verified": bool(self.parity_verified),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EngineMorphEntryV02:
        return cls(
            engine_id=str(data["engine_id"]),
            solver=str(data["solver"]),
            artifact_relpath=str(data["artifact_relpath"]),
            effective_params=dict(data.get("effective_params", {})),
            fit_loss_drop=float(data["fit_loss_drop"]),
            verify_loss_compression=float(data["verify_loss_compression"]),
            volumetric_shear_probe=VolumetricShearProbeSummary.from_dict(data["volumetric_shear_probe"]),
            morph_calibration=MorphCalibrationRecord.from_dict(data["morph_calibration"]),
            parity_verified=bool(data["parity_verified"]),
        )


@dataclass(frozen=True)
class MultiEngineDeformableBundleV02:
    """v0.2 multi-engine deformable bundle supporting MorphTwin decoupled calibration & sidecars."""

    asset_id: str
    source: DeformableSourceSpec
    reference_material: dict[str, float]
    integrity_budget: FractureBudgetV02
    engines: dict[str, EngineMorphEntryV02]
    optional_sidecars: dict[str, dict[str, Any]] = field(default_factory=dict)
    video_provenance: dict[str, Any] | None = None
    sha256_index: dict[str, str] = field(default_factory=dict)
    schema_version: str = BUNDLE_SCHEMA_VERSION_V02

    def __post_init__(self) -> None:
        unknown = set(self.engines.keys()) - set(ALLOWED_ENGINES)
        if unknown:
            raise ValueError(f"Unsupported engine keys in bundle/v0.2: {sorted(unknown)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "asset_id": self.asset_id,
            "source": self.source.to_dict(),
            "reference_material": {k: float(v) for k, v in self.reference_material.items()},
            "integrity_budget": self.integrity_budget.to_dict(),
            "engines": {k: v.to_dict() for k, v in self.engines.items()},
            "optional_sidecars": dict(self.optional_sidecars),
            "video_provenance": dict(self.video_provenance) if self.video_provenance is not None else None,
            "sha256_index": dict(self.sha256_index),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MultiEngineDeformableBundleV02:
        return cls(
            asset_id=str(data["asset_id"]),
            source=DeformableSourceSpec.from_dict(data["source"]),
            reference_material={str(k): float(v) for k, v in data["reference_material"].items()},
            integrity_budget=FractureBudgetV02.from_dict(data["integrity_budget"]),
            engines={
                str(k): EngineMorphEntryV02.from_dict(v)
                for k, v in dict(data["engines"]).items()
            },
            optional_sidecars=dict(data.get("optional_sidecars", {})),
            video_provenance=(
                dict(data["video_provenance"]) if data.get("video_provenance") is not None else None
            ),
            sha256_index={str(k): str(v) for k, v in dict(data.get("sha256_index", {})).items()},
            schema_version=str(data.get("schema_version", BUNDLE_SCHEMA_VERSION_V02)),
        )

    @classmethod
    def upgrade_from_v01(cls, legacy: MultiEngineDeformableBundleManifest) -> MultiEngineDeformableBundleV02:
        """Upgrade a legacy v0.1 bundle into v0.2 with analytical default Jacobians."""
        kappa, mu = bulk_shear_from_young_poisson(
            legacy.source.youngs_modulus_pa,
            legacy.source.poissons_ratio,
        )
        sx, sy, sz = legacy.source.dimensions_xyz_m
        ref_vol = sx * sy * sz
        q0 = (math.log(kappa), math.log(mu))
        nu = float(legacy.source.poissons_ratio)
        # Analytic sensitivity of [log K, log G] wrt [log E, nu]
        # d log K / d log E = 1, d log K / d nu = 2 / (1 - 2*nu)
        # d log G / d log E = 1, d log G / d nu = -1 / (1 + nu)
        a_mat = np.array(
            [
                [1.0, 2.0 / max(1.0 - 2.0 * nu, 0.05)],
                [1.0, -1.0 / (1.0 + nu)],
            ],
            dtype=np.float64,
        )
        cond = float(np.linalg.cond(a_mat))
        upgraded_engines: dict[str, EngineMorphEntryV02] = {}
        for eng_id, entry in legacy.engines.items():
            assert isinstance(entry, EngineParityEntry)
            cal = MorphCalibrationRecord(
                control_names=("log_E", "nu"),
                u0=(math.log(legacy.source.youngs_modulus_pa), nu),
                q0_log_kappa_mu=q0,
                jacobian_A_2x2=(
                    (float(a_mat[0, 0]), float(a_mat[0, 1])),
                    (float(a_mat[1, 0]), float(a_mat[1, 1])),
                ),
                condition_number=cond,
            )
            vs = VolumetricShearProbeSummary(
                effective_bulk_pa=kappa,
                effective_shear_pa=mu,
                effective_poisson=nu,
                verify_loss_volumetric=entry.verify_loss_compression,
                verify_loss_shear=entry.verify_loss_compression,
                volumetric_passed=entry.independent_passed,
                shear_passed=entry.independent_passed,
            )
            upgraded_engines[eng_id] = EngineMorphEntryV02(
                engine_id=eng_id,
                solver=entry.solver,
                artifact_relpath=entry.artifact_relpath,
                effective_params=dict(entry.effective_params),
                fit_loss_drop=entry.fit_loss_drop,
                verify_loss_compression=entry.verify_loss_compression,
                volumetric_shear_probe=vs,
                morph_calibration=cal,
                parity_verified=entry.parity_verified,
            )
        budget = FractureBudgetV02(
            fragility_tier=legacy.integrity_budget.fragility_tier,
            strain_metric="polar_volumetric_deviatoric",
            volumetric_onset_a=legacy.integrity_budget.strain_onset_a * 0.85,
            volumetric_failure_b=legacy.integrity_budget.strain_failure_b * 0.85,
            deviatoric_onset_a=legacy.integrity_budget.strain_onset_a,
            deviatoric_failure_b=legacy.integrity_budget.strain_failure_b,
            fracture_strain_threshold=legacy.integrity_budget.strain_failure_b * 1.1,
            damage_threshold=legacy.integrity_budget.damage_threshold,
            max_normal_force_n=legacy.integrity_budget.max_normal_force_n,
            max_shear_force_n=legacy.integrity_budget.max_shear_force_n,
        )
        return cls(
            asset_id=legacy.asset_id,
            source=legacy.source,
            reference_material={
                "youngs_modulus_pa": float(legacy.source.youngs_modulus_pa),
                "poissons_ratio": nu,
                "bulk_modulus_pa": kappa,
                "shear_modulus_pa": mu,
                "reference_volume_m3": ref_vol,
            },
            integrity_budget=budget,
            engines=upgraded_engines,
            optional_sidecars={},
            video_provenance=None,
            sha256_index=dict(legacy.sha256_index),
        )

