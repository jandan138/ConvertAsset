"""Core contracts, discrepancy loss, and rotation-invariant integrity readouts for M1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Mapping

import numpy as np


BUNDLE_SCHEMA_VERSION = "multi_engine_deformable_bundle/v0.1"
CALIBRATION_LOSS_MAX = 0.05
VERIFICATION_LOSS_MAX = 0.08
DAMAGE_THRESHOLD_DEFAULT = 0.25

ALLOWED_STRUCTURAL_FAMILIES: frozenset[str] = frozenset(
    {"soft_solid", "cloth_sheet", "shell", "garment", "bag", "rod_cable"}
)
ALLOWED_ENGINES: frozenset[str] = frozenset(
    {"genesis", "isaac_physx", "mujoco4", "newton18"}
)


def _to_plain(obj: Any) -> Any:
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {str(k): _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_plain(v) for v in obj]
    return obj


@dataclass(frozen=True)
class DeformableSourceSpec:
    """Normalized source specification for an RFW-S or procedural pilot deformable asset."""

    asset_id: str
    category: str
    structural_family: str
    dimensions_xyz_m: tuple[float, float, float]
    mass_kg: float
    density_kg_m3: float
    youngs_modulus_pa: float
    poissons_ratio: float
    yield_stress_pa: float | None = None
    plastic_strain_band: tuple[float, float] | None = None
    visual_mesh_relpath: str = ""
    proxy_mesh_relpath: str = ""
    mesh_topology: dict[str, Any] = field(default_factory=dict)
    fragility_tier: str = "medium"
    source_dataset: str = "self_authored_pilot"
    source_asset_sha256: str = ""

    def __post_init__(self) -> None:
        if self.structural_family not in ALLOWED_STRUCTURAL_FAMILIES:
            raise ValueError(
                f"Unsupported structural_family {self.structural_family!r}; "
                f"expected one of {sorted(ALLOWED_STRUCTURAL_FAMILIES)}"
            )
        if len(self.dimensions_xyz_m) != 3 or any(d <= 0.0 for d in self.dimensions_xyz_m):
            raise ValueError(f"Invalid dimensions_xyz_m: {self.dimensions_xyz_m!r}")
        if self.mass_kg <= 0.0 or self.density_kg_m3 <= 0.0:
            raise ValueError("mass_kg and density_kg_m3 must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "category": self.category,
            "structural_family": self.structural_family,
            "dimensions_xyz_m": list(self.dimensions_xyz_m),
            "mass_kg": self.mass_kg,
            "density_kg_m3": self.density_kg_m3,
            "youngs_modulus_pa": self.youngs_modulus_pa,
            "poissons_ratio": self.poissons_ratio,
            "yield_stress_pa": self.yield_stress_pa,
            "plastic_strain_band": (
                list(self.plastic_strain_band) if self.plastic_strain_band is not None else None
            ),
            "visual_mesh_relpath": self.visual_mesh_relpath,
            "proxy_mesh_relpath": self.proxy_mesh_relpath,
            "mesh_topology": dict(self.mesh_topology),
            "fragility_tier": self.fragility_tier,
            "source_dataset": self.source_dataset,
            "source_asset_sha256": self.source_asset_sha256,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DeformableSourceSpec:
        band_raw = data.get("plastic_strain_band")
        band = (float(band_raw[0]), float(band_raw[1])) if band_raw is not None else None
        dims = tuple(float(v) for v in data["dimensions_xyz_m"])
        return cls(
            asset_id=str(data["asset_id"]),
            category=str(data["category"]),
            structural_family=str(data["structural_family"]),
            dimensions_xyz_m=(dims[0], dims[1], dims[2]),
            mass_kg=float(data["mass_kg"]),
            density_kg_m3=float(data["density_kg_m3"]),
            youngs_modulus_pa=float(data["youngs_modulus_pa"]),
            poissons_ratio=float(data["poissons_ratio"]),
            yield_stress_pa=(
                float(data["yield_stress_pa"]) if data.get("yield_stress_pa") is not None else None
            ),
            plastic_strain_band=band,
            visual_mesh_relpath=str(data.get("visual_mesh_relpath", "")),
            proxy_mesh_relpath=str(data.get("proxy_mesh_relpath", "")),
            mesh_topology=dict(data.get("mesh_topology", {})),
            fragility_tier=str(data.get("fragility_tier", "medium")),
            source_dataset=str(data.get("source_dataset", "self_authored_pilot")),
            source_asset_sha256=str(data.get("source_asset_sha256", "")),
        )


@dataclass(frozen=True)
class ProbeResponseSummary:
    """Recorded physics behavior summary for one standardized deformable probe."""

    probe_name: str
    finite_fraction: float
    contact_fraction: float
    penetration_absent: bool
    settling_ratio: float
    steps_executed: int
    dt_s: float
    drop_deformation: float | None = None
    compression_deformation: float | None = None
    recovery_ratio: float | None = None
    polar_stretch_strain: float | None = None
    edge_stretch_strain: float | None = None
    naive_f_minus_i: float | None = None
    peak_normal_force_n: float = 0.0
    peak_shear_force_n: float = 0.0
    damage_score: float | None = None
    intact: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProbeResponseSummary:
        return cls(
            probe_name=str(data["probe_name"]),
            finite_fraction=float(data["finite_fraction"]),
            contact_fraction=float(data["contact_fraction"]),
            penetration_absent=bool(data["penetration_absent"]),
            settling_ratio=float(data["settling_ratio"]),
            steps_executed=int(data["steps_executed"]),
            dt_s=float(data["dt_s"]),
            drop_deformation=(
                float(data["drop_deformation"]) if data.get("drop_deformation") is not None else None
            ),
            compression_deformation=(
                float(data["compression_deformation"])
                if data.get("compression_deformation") is not None
                else None
            ),
            recovery_ratio=(
                float(data["recovery_ratio"]) if data.get("recovery_ratio") is not None else None
            ),
            polar_stretch_strain=(
                float(data["polar_stretch_strain"])
                if data.get("polar_stretch_strain") is not None
                else None
            ),
            edge_stretch_strain=(
                float(data["edge_stretch_strain"])
                if data.get("edge_stretch_strain") is not None
                else None
            ),
            naive_f_minus_i=(
                float(data["naive_f_minus_i"]) if data.get("naive_f_minus_i") is not None else None
            ),
            peak_normal_force_n=float(data.get("peak_normal_force_n", 0.0)),
            peak_shear_force_n=float(data.get("peak_shear_force_n", 0.0)),
            damage_score=(
                float(data["damage_score"]) if data.get("damage_score") is not None else None
            ),
            intact=bool(data["intact"]) if data.get("intact") is not None else None,
            extra=dict(data.get("extra", {})),
        )


@dataclass(frozen=True)
class DeformableIntegrityBudget:
    """Calibrated cross-engine integrity / fracture-proxy boundary."""

    fragility_tier: str
    strain_metric: str
    strain_onset_a: float
    strain_failure_b: float
    damage_threshold: float = DAMAGE_THRESHOLD_DEFAULT
    max_normal_force_n: float = 0.0
    max_shear_force_n: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DeformableIntegrityBudget:
        return cls(
            fragility_tier=str(data["fragility_tier"]),
            strain_metric=str(data["strain_metric"]),
            strain_onset_a=float(data["strain_onset_a"]),
            strain_failure_b=float(data["strain_failure_b"]),
            damage_threshold=float(data.get("damage_threshold", DAMAGE_THRESHOLD_DEFAULT)),
            max_normal_force_n=float(data.get("max_normal_force_n", 0.0)),
            max_shear_force_n=float(data.get("max_shear_force_n", 0.0)),
        )


@dataclass(frozen=True)
class EngineParityEntry:
    """Verification record for one physics engine inside a multi-engine deformable bundle."""

    engine_id: str
    solver: str
    artifact_relpath: str
    effective_params: dict[str, Any]
    fit_loss_drop: float
    verify_loss_compression: float
    cal_passed: bool
    independent_passed: bool
    parity_verified: bool
    drop_summary: ProbeResponseSummary
    compression_summary: ProbeResponseSummary
    gentle_grasp: ProbeResponseSummary | None = None
    crush_counterfactual: ProbeResponseSummary | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "solver": self.solver,
            "artifact_relpath": self.artifact_relpath,
            "effective_params": dict(self.effective_params),
            "fit_loss_drop": self.fit_loss_drop,
            "verify_loss_compression": self.verify_loss_compression,
            "cal_passed": self.cal_passed,
            "independent_passed": self.independent_passed,
            "parity_verified": self.parity_verified,
            "drop_summary": self.drop_summary.to_dict(),
            "compression_summary": self.compression_summary.to_dict(),
            "gentle_grasp": self.gentle_grasp.to_dict() if self.gentle_grasp is not None else None,
            "crush_counterfactual": (
                self.crush_counterfactual.to_dict()
                if self.crush_counterfactual is not None
                else None
            ),
        }


@dataclass(frozen=True)
class MultiEngineDeformableBundleManifest:
    """Top-level bundle manifest consumed by scenario-forge, trajectory-forge, and EOS."""

    asset_id: str
    source: DeformableSourceSpec
    integrity_budget: DeformableIntegrityBudget
    engines: dict[str, EngineParityEntry]
    sha256_index: dict[str, str] = field(default_factory=dict)
    schema_version: str = BUNDLE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "asset_id": self.asset_id,
            "source": self.source.to_dict(),
            "integrity_budget": self.integrity_budget.to_dict(),
            "engines": {k: v.to_dict() for k, v in self.engines.items()},
            "sha256_index": dict(self.sha256_index),
        }


def polar_stretch_strain_from_F(F_batch: np.ndarray) -> float:
    """Compute rotation-invariant right-stretch Frobenius strain Q_0.95(||U - I_3||_F).

    For deformation gradients F = R @ U via SVD (F = W @ S @ V^T => U = V @ S @ V^T),
    pure rigid rotations F = R in SO(3) yield U == I_3 and strain == 0.0.
    Supports either (N, 3, 3) or (T, N, 3, 3) arrays (taking max over T).
    """
    arr = np.asarray(F_batch, dtype=np.float64)
    if arr.ndim == 3:
        arr = arr[None, ...]
    if arr.ndim != 4 or arr.shape[-2:] != (3, 3):
        raise ValueError(f"Expected F shape (N, 3, 3) or (T, N, 3, 3), got {arr.shape}")

    eye = np.eye(3, dtype=np.float64)
    max_q95 = 0.0
    for t in range(arr.shape[0]):
        ft = arr[t]
        _, s, vt = np.linalg.svd(ft, full_matrices=True)
        # U = V @ diag(S) @ V^T = vt^T @ (S[:, :, None] * vt)
        u = np.einsum("nji,nj,njk->nik", vt, s, vt)
        diff = np.linalg.norm(u - eye[None, ...], ord="fro", axis=(-2, -1))
        q95 = float(np.percentile(diff, 95))
        if q95 > max_q95:
            max_q95 = q95
    return max_q95


def naive_rfws_strain_from_F(F_batch: np.ndarray) -> float:
    """Compute RFW-S Eq. (5) naive ||F - I_3||_F (sensitive to rigid rotation) for comparison."""
    arr = np.asarray(F_batch, dtype=np.float64)
    if arr.ndim == 3:
        arr = arr[None, ...]
    if arr.ndim != 4 or arr.shape[-2:] != (3, 3):
        raise ValueError(f"Expected F shape (N, 3, 3) or (T, N, 3, 3), got {arr.shape}")

    eye = np.eye(3, dtype=np.float64)
    max_q95 = 0.0
    for t in range(arr.shape[0]):
        diff = np.linalg.norm(arr[t] - eye[None, ...], ord="fro", axis=(-2, -1))
        q95 = float(np.percentile(diff, 95))
        if q95 > max_q95:
            max_q95 = q95
    return max_q95


def edge_stretch_strain(
    rest_points: np.ndarray,
    cur_points: np.ndarray,
    edges: np.ndarray,
) -> float:
    """Compute rotation-invariant edge-length stretch strain Q_0.95(|l - l_0| / l_0).

    Supports cur_points of shape (N, 3) or (T, N, 3).
    """
    rest = np.asarray(rest_points, dtype=np.float64)
    cur = np.asarray(cur_points, dtype=np.float64)
    ed = np.asarray(edges, dtype=np.int64)
    if cur.ndim == 2:
        cur = cur[None, ...]
    if ed.ndim != 2 or ed.shape[1] != 2 or len(ed) == 0:
        raise ValueError(f"Invalid edges shape: {ed.shape}")

    rest_len = np.linalg.norm(rest[ed[:, 0]] - rest[ed[:, 1]], axis=-1)
    denom = np.maximum(rest_len, 1e-6)

    max_q95 = 0.0
    for t in range(cur.shape[0]):
        cur_len = np.linalg.norm(cur[t, ed[:, 0]] - cur[t, ed[:, 1]], axis=-1)
        rel = np.abs(cur_len - rest_len) / denom
        q95 = float(np.percentile(rel, 95))
        if q95 > max_q95:
            max_q95 = q95
    return max_q95


def evaluate_integrity_readout(
    *,
    strain: float,
    strain_onset_a: float,
    strain_failure_b: float,
    peak_normal_force_n: float = 0.0,
    max_normal_force_n: float | None = None,
    peak_shear_force_n: float = 0.0,
    max_shear_force_n: float | None = None,
    damage_threshold: float = DAMAGE_THRESHOLD_DEFAULT,
) -> dict[str, Any]:
    """Evaluate normalized damage score D in [0, 1] and binary intact verdict (D < threshold)."""
    d_strain = min(
        1.0,
        max(0.0, (float(strain) - float(strain_onset_a)) / max(float(strain_failure_b) - float(strain_onset_a), 1e-6)),
    )

    d_force = 0.0
    if max_normal_force_n is not None and max_normal_force_n > 0.0:
        f_safe = 0.65 * float(max_normal_force_n)
        f_fail = 1.25 * float(max_normal_force_n)
        d_n = min(1.0, max(0.0, (float(peak_normal_force_n) - f_safe) / max(f_fail - f_safe, 1e-6)))
        d_force = max(d_force, d_n)
    if max_shear_force_n is not None and max_shear_force_n > 0.0:
        s_safe = 0.65 * float(max_shear_force_n)
        s_fail = 1.25 * float(max_shear_force_n)
        d_s = min(1.0, max(0.0, (float(peak_shear_force_n) - s_safe) / max(s_fail - s_safe, 1e-6)))
        d_force = max(d_force, d_s)

    damage_score = max(d_strain, d_force)
    return {
        "damage_strain": float(d_strain),
        "damage_force": float(d_force),
        "damage_score": float(damage_score),
        "intact": bool(damage_score < float(damage_threshold)),
        "damage_threshold": float(damage_threshold),
    }


def compute_probe_discrepancy_loss(
    candidate: ProbeResponseSummary,
    reference: ProbeResponseSummary,
    *,
    probe_kind: str,
) -> float:
    """Compute RFW-S Eq. (4) normalized clipped discrepancy loss L(c, r)."""
    terms: list[float] = []

    # Boolean checks
    bool_pairs = [
        (candidate.finite_fraction >= 1.0 - 1e-9, reference.finite_fraction >= 1.0 - 1e-9),
        (candidate.penetration_absent, reference.penetration_absent),
        (candidate.contact_fraction > 0.0, reference.contact_fraction > 0.0),
    ]
    for c_b, r_b in bool_pairs:
        terms.append(0.0 if bool(c_b) == bool(r_b) else 1.0)

    # Numeric checks per probe
    if probe_kind == "drop":
        num_pairs = [
            ("deform", candidate.drop_deformation, reference.drop_deformation),
            ("recov", candidate.recovery_ratio, reference.recovery_ratio),
        ]
    elif probe_kind == "compression_release":
        num_pairs = [
            ("deform", candidate.compression_deformation, reference.compression_deformation),
            ("recov", candidate.recovery_ratio, reference.recovery_ratio),
        ]
    else:
        raise ValueError(f"Unsupported probe_kind: {probe_kind!r}")

    for kind, c_val, r_val in num_pairs:
        if c_val is None or r_val is None:
            continue
        if not (math.isfinite(c_val) and math.isfinite(r_val)):
            terms.append(1.0)
            continue
        if kind == "recov":
            denom = max(abs(float(r_val)), 1.0 - abs(float(r_val)), 0.25)
        else:
            denom = max(abs(float(r_val)), 0.02)
        terms.append(min(1.0, abs(float(c_val) - float(r_val)) / denom))

    if not terms:
        return 1.0
    return float(sum(terms) / len(terms))

