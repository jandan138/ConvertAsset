"""Pure-Python contracts for video-based deformable Real-to-Sim ingestion (M2)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from convert_asset.deformable_parity.contracts import DeformableSourceSpec
from convert_asset.deformable_v05.contracts_v05 import (
    FractureBudgetV02,
    MultiEngineDeformableBundleV02,
)
from convert_asset.deformable_v05.morph_compiler import compile_deformable_bundle_v02


VIDEO_OBSERVATION_SCHEMA_VERSION = "deformable_video_observation/v0.1"


@dataclass(frozen=True)
class VideoObservationManifest:
    """Normalized observation handoff between vision preprocessing and physics inversion."""

    observation_id: str
    asset_id: str
    category: str
    structural_family: str
    modality: str  # "egocentric_stereo" | "multi_rgbd" | "single_rgbd" | "synthetic_proxy"
    n_frames: int
    fps: float
    dimensions_xyz_m: tuple[float, float, float]
    mass_kg: float
    tracks_3d_relpath: str
    rest_mesh_relpath: str = ""
    rgb_dir_relpath: str = ""
    depth_dir_relpath: str = ""
    interaction_frames: tuple[int, int] = (0, 0)
    camera_intrinsics: dict[str, Any] = field(default_factory=dict)
    schema_version: str = VIDEO_OBSERVATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "observation_id": self.observation_id,
            "asset_id": self.asset_id,
            "category": self.category,
            "structural_family": self.structural_family,
            "modality": self.modality,
            "n_frames": int(self.n_frames),
            "fps": float(self.fps),
            "dimensions_xyz_m": [float(v) for v in self.dimensions_xyz_m],
            "mass_kg": float(self.mass_kg),
            "tracks_3d_relpath": self.tracks_3d_relpath,
            "rest_mesh_relpath": self.rest_mesh_relpath,
            "rgb_dir_relpath": self.rgb_dir_relpath,
            "depth_dir_relpath": self.depth_dir_relpath,
            "interaction_frames": [int(self.interaction_frames[0]), int(self.interaction_frames[1])],
            "camera_intrinsics": dict(self.camera_intrinsics),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VideoObservationManifest:
        dims = tuple(float(v) for v in data["dimensions_xyz_m"])
        ifr = data.get("interaction_frames", [0, 0])
        return cls(
            observation_id=str(data["observation_id"]),
            asset_id=str(data["asset_id"]),
            category=str(data["category"]),
            structural_family=str(data["structural_family"]),
            modality=str(data["modality"]),
            n_frames=int(data["n_frames"]),
            fps=float(data["fps"]),
            dimensions_xyz_m=(dims[0], dims[1], dims[2]),
            mass_kg=float(data["mass_kg"]),
            tracks_3d_relpath=str(data["tracks_3d_relpath"]),
            rest_mesh_relpath=str(data.get("rest_mesh_relpath", "")),
            rgb_dir_relpath=str(data.get("rgb_dir_relpath", "")),
            depth_dir_relpath=str(data.get("depth_dir_relpath", "")),
            interaction_frames=(int(ifr[0]), int(ifr[1])),
            camera_intrinsics=dict(data.get("camera_intrinsics", {})),
            schema_version=str(data.get("schema_version", VIDEO_OBSERVATION_SCHEMA_VERSION)),
        )


@dataclass(frozen=True)
class MorphTwinInversionReceipt:
    """Recovered physical parameters and holdout video fidelity metrics from inversion."""

    observation_id: str
    asset_id: str
    method: str  # "morphtwin_carrier_decoupled" | "central_force_baseline" | "external_import"
    recovered_youngs_modulus_pa: float
    recovered_poissons_ratio: float
    recovered_bulk_modulus_pa: float
    recovered_shear_modulus_pa: float
    contact_stiffness_n_m: float
    contact_friction_mu: float
    contact_restitution: float
    holdout_track_error_m: float
    holdout_chamfer_distance_m: float
    holdout_psnr_db: float | None = None
    holdout_lpips: float | None = None
    ground_truth_youngs_pa: float | None = None
    ground_truth_poisson: float | None = None
    youngs_relative_error: float | None = None
    poisson_abs_error: float | None = None
    provenance_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MorphTwinInversionReceipt:
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})


def import_morphtwin_export(
    export_dir: str | Path,
    out_bundle_dir: str | Path,
    *,
    budget: FractureBudgetV02 | None = None,
) -> tuple[MultiEngineDeformableBundleV02, Path]:
    """Import a pre-computed MorphTwin/PhysTwin export directory into a v0.2 four-engine bundle.

    Expects `observation_manifest.json` and `inversion_receipt.json` inside `export_dir`.
    """
    src_dir = Path(export_dir)
    obs_path = src_dir / "observation_manifest.json"
    rec_path = src_dir / "inversion_receipt.json"
    if not obs_path.exists() or not rec_path.exists():
        raise FileNotFoundError(
            f"Expected observation_manifest.json and inversion_receipt.json under {src_dir}"
        )

    obs = VideoObservationManifest.from_dict(json.loads(obs_path.read_text(encoding="utf-8")))
    rec = MorphTwinInversionReceipt.from_dict(json.loads(rec_path.read_text(encoding="utf-8")))
    sx, sy, sz = obs.dimensions_xyz_m
    vol = max(sx * sy * sz, 1e-9)
    src_sha = sha256(rec_path.read_bytes()).hexdigest()

    spec = DeformableSourceSpec(
        asset_id=obs.asset_id,
        category=obs.category,
        structural_family=obs.structural_family,
        dimensions_xyz_m=obs.dimensions_xyz_m,
        mass_kg=obs.mass_kg,
        density_kg_m3=obs.mass_kg / vol,
        youngs_modulus_pa=rec.recovered_youngs_modulus_pa,
        poissons_ratio=rec.recovered_poissons_ratio,
        fragility_tier="medium",
        source_dataset=f"video_real2sim_{obs.modality}",
        source_asset_sha256=src_sha,
    )
    video_prov = {
        "observation_manifest": obs.to_dict(),
        "inversion_receipt": rec.to_dict(),
        "source_export_dir": src_dir.as_posix(),
    }
    return compile_deformable_bundle_v02(
        spec,
        out_bundle_dir,
        budget=budget,
        include_morphtwin_sidecar=True,
        video_provenance=video_prov,
    )

