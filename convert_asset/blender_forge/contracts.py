"""Contracts, Blender 4.4+ strict discovery, and geometry/physics hygiene reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Mapping


MIN_BLENDER_VERSION: tuple[int, int, int] = (4, 4, 0)
BLENDER_FORGE_SCHEMA_VERSION = "blender-simready-forge/v1.0"
_VERSION_RE = re.compile(r"Blender\s+(\d+)\.(\d+)\.(\d+)")


class BlenderVersionError(RuntimeError):
    """Raised when Blender is missing or older than the mandatory 4.4.0 baseline."""


@dataclass(frozen=True)
class BlenderRuntimeInfo:
    executable: str
    version: tuple[int, int, int]
    version_string: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "executable": self.executable,
            "version": list(self.version),
            "version_string": self.version_string,
        }


def _probe_blender_version(exe: Path) -> BlenderRuntimeInfo | None:
    if not exe.is_file():
        return None
    try:
        proc = subprocess.run(
            [str(exe), "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        return None
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    m = _VERSION_RE.search(text)
    if not m:
        return None
    ver = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return BlenderRuntimeInfo(
        executable=exe.resolve().as_posix(),
        version=ver,
        version_string=f"{ver[0]}.{ver[1]}.{ver[2]}",
    )


def resolve_blender44_bin(explicit: str | Path | None = None) -> BlenderRuntimeInfo:
    """Resolve a Blender >= 4.4.0 executable; reject < 4.4 with an actionable error."""
    if explicit is not None:
        p_exp = Path(explicit)
        info = _probe_blender_version(p_exp)
        if info is None:
            raise BlenderVersionError(f"Explicit Blender binary is invalid or missing: {p_exp}")
        if info.version < MIN_BLENDER_VERSION:
            raise BlenderVersionError(
                f"Explicit Blender binary {info.executable} is version {info.version_string}; "
                "Blender >= 4.4.0 is strictly required (AgX + 4.4 BSDF/USD APIs)."
            )
        return info

    candidates: list[Path] = []
    env_bin = os.environ.get("BLENDER_BIN")
    if env_bin:
        candidates.append(Path(env_bin))

    # Preferred portable & standard 4.4+ locations on Windows and Linux
    known_globs = [
        Path(r"G:\my_program\blender-4.4.3-windows-x64\blender.exe"),
        Path(r"G:\my_program"),
        Path(r"C:\Program Files\Blender Foundation"),
        Path("/opt"),
        Path("/usr/local"),
    ]
    for item in known_globs:
        if item.is_file():
            candidates.append(item)
        elif item.is_dir():
            for child in sorted(item.glob("blender-4.*"), reverse=True):
                for rel in ("blender.exe", "blender"):
                    p = child / rel
                    if p.is_file():
                        candidates.append(p)
            for child in sorted(item.glob("Blender 4.*"), reverse=True):
                p = child / "blender.exe"
                if p.is_file():
                    candidates.append(p)

    which_bin = shutil.which("blender")
    if which_bin:
        candidates.append(Path(which_bin))

    seen: set[str] = set()
    older_found: list[BlenderRuntimeInfo] = []
    for cand in candidates:
        key = str(cand).lower()
        if key in seen:
            continue
        seen.add(key)
        info = _probe_blender_version(cand)
        if info is None:
            continue
        if info.version >= MIN_BLENDER_VERSION:
            return info
        older_found.append(info)

    if older_found:
        found_str = ", ".join(f"{o.executable} ({o.version_string})" for o in older_found)
        raise BlenderVersionError(
            f"Blender >= 4.4.0 is required (AgX + 4.4 BSDF/USD APIs). Found only older versions: {found_str}."
        )
    raise BlenderVersionError(
        "No Blender >= 4.4.0 installation found. Set BLENDER_BIN or install Blender 4.4.3 portable."
    )


@dataclass(frozen=True)
class AssetForgeSpec:
    """Unified declarative specification for Blender 4.4+ -> OpenUSD SimReady asset forging."""

    asset_id: str
    family: str  # "articulated_cad" | "deformable_sculpted" | "room_environment"
    template: str  # "precision_benchtop_incubator" | "artisan_butter_croissant"
    dimensions_xyz_m: tuple[float, float, float]
    dimension_tolerance_m: float = 0.001
    mass_kg: float = 4.2
    cycles_device: str = "CPU"  # "CPU" (safe default) | "OPTIX" | "CUDA"
    cycles_samples: int = 36
    render_resolution: tuple[int, int] = (640, 480)
    deformable_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": BLENDER_FORGE_SCHEMA_VERSION,
            "asset_id": self.asset_id,
            "family": self.family,
            "template": self.template,
            "dimensions_xyz_m": [float(v) for v in self.dimensions_xyz_m],
            "dimension_tolerance_m": float(self.dimension_tolerance_m),
            "mass_kg": float(self.mass_kg),
            "cycles_device": self.cycles_device,
            "cycles_samples": int(self.cycles_samples),
            "render_resolution": [int(self.render_resolution[0]), int(self.render_resolution[1])],
            "deformable_params": dict(self.deformable_params),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AssetForgeSpec:
        dims = tuple(float(v) for v in data["dimensions_xyz_m"])
        res = tuple(int(v) for v in data.get("render_resolution", (640, 480)))
        return cls(
            asset_id=str(data["asset_id"]),
            family=str(data["family"]),
            template=str(data["template"]),
            dimensions_xyz_m=(dims[0], dims[1], dims[2]),
            dimension_tolerance_m=float(data.get("dimension_tolerance_m", 0.001)),
            mass_kg=float(data.get("mass_kg", 4.2)),
            cycles_device=str(data.get("cycles_device", "CPU")),
            cycles_samples=int(data.get("cycles_samples", 36)),
            render_resolution=(res[0], res[1]),
            deformable_params=dict(data.get("deformable_params", {})),
        )


@dataclass(frozen=True)
class ForgeHygieneReport:
    """Automated geometry, physics separation, dimension tolerance, and Cycles AgX visual QA gate."""

    asset_id: str
    family: str
    blender_version: str
    measured_dimensions_xyz_m: tuple[float, float, float]
    max_dimension_error_m: float
    dimension_gate_passed: bool
    non_manifold_edge_count: int
    manifold_gate_passed: bool
    uv_present: bool
    visual_collision_separated: bool
    total_visual_triangles: int
    total_collision_or_proxy_triangles: int
    studio_views_ok: bool
    studio_view_stats: dict[str, dict[str, float]]
    overall_passed: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

