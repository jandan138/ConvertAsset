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
MILESTONE_AAN07 = "AAN-07-benchmark-contract"
MILESTONE_AAN11 = "AAN-11-material-runtime-closure"

ALLOWED_SOURCE_RUNTIMES = {"isaac51"}
ALLOWED_TARGET_RUNTIMES = {"isaac41"}
ALLOWED_TARGET_BENCHMARKS = {"ebench-lift2", "scenario-forge"}
ALLOWED_ASSET_ROLES = {"dynamic", "visual_static"}
USD_EXTENSIONS = {".usd", ".usda", ".usdc"}


def validate_scope_prim_paths(scope_prims: list[str]) -> dict[str, object]:
    """Return a deterministic, fail-closed validation result for role scopes."""
    normalized = [str(path).rstrip("/") or "/" for path in scope_prims]
    errors: list[str] = []
    if not normalized:
        errors.append("at least one asset scope prim is required")
    if len(set(normalized)) != len(normalized):
        errors.append("asset scope prims must not contain duplicates")
    for path in normalized:
        if not path.startswith("/"):
            errors.append(f"asset scope prim must be an absolute USD path: {path}")
    for index, parent in enumerate(normalized):
        for child in normalized[index + 1 :]:
            if parent == child:
                continue
            if child.startswith(parent.rstrip("/") + "/") or parent.startswith(child.rstrip("/") + "/"):
                errors.append(f"asset scope prims must be disjoint: {parent}, {child}")
    return {
        "status": "pass" if not errors else "blocked",
        "scope_prims": normalized,
        "errors": errors,
    }


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
    asset_role: str = "dynamic"
    contract: Path | None = None
    required_prims: list[str] = field(default_factory=list)
    asset_scope_prims: list[str] = field(default_factory=list)
    material_policy: str = "native-or-mirror"
    allow_waiver: Path | None = None
    # Dynamic mass properties live in an explicit, source-bound profile rather
    # than in a consumer-side scene patch.  Keeping this optional preserves the
    # legacy EBench migration path, while Scenario Forge admissions require it.
    physics_profile: Path | None = None
    # Object topology, collision intent, and named interaction frames are a
    # separate versioned contract.  Physics profile v1 remains mass-only.
    interaction_profile: Path | None = None
    gates: list[str] = field(default_factory=lambda: ["static"])
    evidence_out: Path | None = None
    runtime_python: Path | None = None
    warning_baseline_log: Path | None = None
    warning_baseline_scope_prims: list[str] = field(default_factory=list)
    # Optional PhysX log captured after the package was instantiated by a
    # consumer (for example below a Scenario Forge room Xform).  Its paths are
    # interpreted only through the declared one-to-one binding below.
    runtime_physx_log: Path | None = None
    runtime_scope_bindings: list[dict[str, str]] = field(default_factory=list)
    expected_runtime_version: str = "4.1"
    runtime_timeout_seconds: int = 600
    dry_run: bool = False

    @property
    def effective_asset_scope_prims(self) -> list[str]:
        """Explicit role scope, falling back to the existing required-prim contract."""
        return self.asset_scope_prims or self.required_prims


@dataclass(frozen=True)
class NormalizeAssetResult:
    return_code: int
    manifest_path: Path | None
    overall_status: str
