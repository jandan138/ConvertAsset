"""USD stage-unit and frame evidence for package-owned physics admission.

The functions in this module deliberately import :mod:`pxr` lazily.  AAN's
CLI and its JSON/profile validation remain usable outside an Isaac runtime,
while the actual USD admission always records the physical interpretation that
PhysX will receive.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any


METRIC_FIELDS = (
    "meters_per_unit",
    "kilograms_per_unit",
    "up_axis",
    "time_codes_per_second",
    "frames_per_second",
)


def stage_metrics(stage: Any) -> dict[str, Any]:
    """Return the physical/timing metadata PhysX needs to interpret a stage."""
    from pxr import UsdGeom, UsdPhysics  # type: ignore

    return {
        "meters_per_unit": float(UsdGeom.GetStageMetersPerUnit(stage)),
        "kilograms_per_unit": float(UsdPhysics.GetStageKilogramsPerUnit(stage)),
        "up_axis": str(UsdGeom.GetStageUpAxis(stage)),
        "time_codes_per_second": float(stage.GetTimeCodesPerSecond()),
        "frames_per_second": float(stage.GetFramesPerSecond()),
        "start_time_code": float(stage.GetStartTimeCode()),
        "end_time_code": float(stage.GetEndTimeCode()),
    }


def read_stage_metrics(path: Path) -> dict[str, Any] | None:
    """Open ``path`` and collect its metrics, returning ``None`` on failure."""
    try:
        from pxr import Usd  # type: ignore

        stage = Usd.Stage.Open(str(path))
        return stage_metrics(stage) if stage is not None else None
    except Exception:
        return None


def metrics_match(
    actual: dict[str, Any],
    expected: dict[str, Any],
    *,
    fields: tuple[str, ...] = METRIC_FIELDS,
) -> tuple[bool, list[dict[str, Any]]]:
    """Compare canonical metric records without silently accepting scale drift."""
    mismatches: list[dict[str, Any]] = []
    for field in fields:
        actual_value = actual.get(field)
        expected_value = expected.get(field)
        if field == "up_axis":
            matches = isinstance(actual_value, str) and actual_value == expected_value
        else:
            try:
                matches = math.isfinite(float(actual_value)) and math.isclose(
                    float(actual_value), float(expected_value), rel_tol=1.0e-9, abs_tol=1.0e-12
                )
            except (TypeError, ValueError):
                matches = False
        if not matches:
            mismatches.append(
                {"field": field, "source": expected_value, "package": actual_value}
            )
    return not mismatches, mismatches


def physical_frame_report(
    source_usd: Path,
    package_usd: Path,
    scope_prims: list[str],
) -> dict[str, Any]:
    """Prove that package entry metadata preserves the source physical frame.

    This is intentionally a gate rather than a best-effort note: the exact
    same numeric mass/inertia values describe a different real object when
    ``metersPerUnit`` or the up-axis changes beneath them.
    """
    try:
        from pxr import Usd, UsdGeom  # type: ignore

        source = Usd.Stage.Open(str(source_usd))
        package = Usd.Stage.Open(str(package_usd))
        if source is None or package is None:
            raise RuntimeError("could not open source or package stage")
        source_record = stage_metrics(source)
        package_record = stage_metrics(package)
        matches, mismatches = metrics_match(package_record, source_record)
        scopes: list[dict[str, Any]] = []
        for path in scope_prims:
            source_prim = source.GetPrimAtPath(path)
            package_prim = package.GetPrimAtPath(path)
            source_bound = _world_bound_si(source, source_prim)
            package_bound = _world_bound_si(package, package_prim)
            bound_matches = _bounds_match(source_bound, package_bound)
            scopes.append(
                {
                    "path": path,
                    "source_world_bound_m": source_bound,
                    "package_world_bound_m": package_bound,
                    "status": "pass" if bound_matches else "blocked",
                }
            )
        bad_scopes = [entry["path"] for entry in scopes if entry["status"] != "pass"]
        status = "pass" if matches and not bad_scopes else "blocked"
        return {
            "status": status,
            "source": source_record,
            "package": package_record,
            "metric_mismatches": mismatches,
            "scope_bounds": scopes,
            "blocked_scope_prims": bad_scopes,
            "policy": "source_and_package_stage_metrics_and_world_bounds_must_match",
        }
    except Exception as exc:
        return {
            "status": "blocked",
            "reason": str(exc),
            "source": read_stage_metrics(source_usd),
            "package": read_stage_metrics(package_usd),
            "metric_mismatches": [],
            "scope_bounds": [],
            "blocked_scope_prims": list(scope_prims),
            "policy": "source_and_package_stage_metrics_and_world_bounds_must_match",
        }


def _world_bound_si(stage: Any, prim: Any) -> dict[str, Any] | None:
    if not prim or not prim.IsValid():
        return None
    try:
        from pxr import Usd, UsdGeom  # type: ignore

        cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        aligned = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        minimum = aligned.GetMin()
        maximum = aligned.GetMax()
        scale = float(UsdGeom.GetStageMetersPerUnit(stage))
        values = [float(component) * scale for component in [*minimum, *maximum]]
        if not all(math.isfinite(value) for value in values):
            return None
        return {
            "min": [round(value, 10) for value in values[:3]],
            "max": [round(value, 10) for value in values[3:]],
        }
    except Exception:
        return None


def _bounds_match(source: dict[str, Any] | None, package: dict[str, Any] | None) -> bool:
    if source is None or package is None:
        return False
    try:
        source_values = [*source["min"], *source["max"]]
        package_values = [*package["min"], *package["max"]]
        return len(source_values) == len(package_values) and all(
            math.isclose(float(left), float(right), rel_tol=1.0e-7, abs_tol=1.0e-8)
            for left, right in zip(source_values, package_values)
        )
    except (KeyError, TypeError, ValueError):
        return False
