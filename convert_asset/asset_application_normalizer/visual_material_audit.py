"""Evidence helpers for proving that a package revision is material-only."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "aan.visual_material_only_audit.v1"
_FORBIDDEN_TOKENS = (
    "physics:",
    "physx",
    "collision",
    "mass",
    "inertia",
    "xformOp:",
    "points",
    "faceVertex",
    "extent",
)


def audit_visual_material_only_package(
    package_dir: Path,
    *,
    expected_physics_profile: Path,
    expected_interaction_profile: Path,
) -> dict[str, Any]:
    """Return a machine-readable audit without mutating the package."""

    package_dir = package_dir.resolve()
    manifest_path = package_dir / "evidence/manifest.json"
    overlay_path = package_dir / "overlays/visual_material.usda"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    overlay = overlay_path.read_text(encoding="utf-8")
    physics = _identity_record(
        package_dir / "physics/profile.json", expected_physics_profile.resolve()
    )
    interaction = _identity_record(
        package_dir / "interaction/profile.json", expected_interaction_profile.resolve()
    )
    forbidden = [token for token in _FORBIDDEN_TOKENS if token.lower() in overlay.lower()]
    visual = manifest.get("visual_material_profile", {})
    runtime = manifest.get("runtime_evidence", {})
    checks = {
        "package_admission_passed": manifest.get("overall_status") == "pass"
        and not manifest.get("blocked_reasons"),
        "runtime_admission_passed": runtime.get("status") == "pass",
        "visual_profile_v2_applied": visual.get("status") == "pass"
        and visual.get("schema_version") == "aan.visual_material_profile.v2",
        "visual_overlay_has_no_geometry_or_physics_authoring": not forbidden,
        "physics_profile_byte_identical": physics["byte_identical"],
        "interaction_profile_byte_identical": interaction["byte_identical"],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if all(checks.values()) else "blocked",
        "package_id": manifest.get("package_id"),
        "asset_id": manifest.get("asset_id"),
        "source_usd_sha256": manifest.get("source", {}).get("sha256"),
        "checks": checks,
        "physics_profile": physics,
        "interaction_profile": interaction,
        "visual_overlay": {
            "path": "overlays/visual_material.usda",
            "sha256": _sha256(overlay_path),
            "binding_targets": visual.get("binding_targets", []),
            "mdl_inputs": visual.get("mdl_inputs", {}),
            "forbidden_authored_tokens": forbidden,
        },
        "claim_boundary": (
            "This audit proves byte identity of the declared physics and interaction "
            "profiles and absence of geometry/physics tokens in the visual override "
            "layer. It does not claim robot-policy or benchmark success."
        ),
    }


def _identity_record(actual: Path, expected: Path) -> dict[str, Any]:
    actual_sha = _sha256(actual)
    expected_sha = _sha256(expected)
    return {
        "package_path": str(actual),
        "expected_source_path": str(expected),
        "package_sha256": actual_sha,
        "expected_source_sha256": expected_sha,
        "byte_identical": actual_sha == expected_sha,
    }


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
