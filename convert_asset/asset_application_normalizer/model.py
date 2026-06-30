"""Small stable IR for the AAN MVP CLI skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


SCHEMA_VERSION = "asset_application_normalizer.v1"
TOOL_VERSION = "convert_asset.asset_application_normalizer.v1"
MILESTONE_AAN02 = "AAN-02-cli-skeleton"
MILESTONE_AAN03 = "AAN-03-usd-closure"
MILESTONE_AAN04 = "AAN-04-material-closure"
MILESTONE_AAN05 = "AAN-05-physics-static"
MILESTONE_AAN06 = "AAN-06-runtime-smoke"

ALLOWED_SOURCE_RUNTIMES = {"isaac51"}
ALLOWED_TARGET_RUNTIMES = {"isaac41"}
ALLOWED_TARGET_BENCHMARKS = {"ebench-lift2"}
USD_EXTENSIONS = {".usd", ".usda", ".usdc"}


@dataclass(frozen=True)
class NormalizeAssetRequest:
    source_usd: Path
    out_dir: Path
    asset_id: str
    asset_class: str
    source_runtime: str
    target_runtime: str
    target_benchmark: str
    task_id: str
    contract: Path | None = None
    required_prims: list[str] = field(default_factory=list)
    material_policy: str = "native-or-mirror"
    allow_waiver: Path | None = None
    gates: list[str] = field(default_factory=lambda: ["static"])
    evidence_out: Path | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class NormalizeAssetResult:
    return_code: int
    manifest_path: Path | None
    overall_status: str
