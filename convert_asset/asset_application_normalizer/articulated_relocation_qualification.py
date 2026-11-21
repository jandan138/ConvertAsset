"""Promotion policy for relocatable articulated appliance packages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ArticulatedPromotionDecision:
    status: str
    promoted_tier: str | None
    blocked_reasons: tuple[str, ...]


def resolve_promotion(
    *,
    requested_tier: str,
    portability_checks: Mapping[str, bool],
    full_function_checks: Mapping[str, bool],
    scoped_function_checks: Mapping[str, bool],
) -> ArticulatedPromotionDecision:
    """Resolve strict full/scoped promotion without portability waivers."""
    if requested_tier not in {"relocatable_full", "relocatable_task_scoped"}:
        raise ValueError("unsupported articulated promotion tier")
    failed_portability = sorted(
        name for name, passed in portability_checks.items() if not passed
    )
    if not portability_checks or failed_portability:
        reasons = failed_portability or ["portability_checks_missing"]
        return ArticulatedPromotionDecision(
            status="blocked",
            promoted_tier=None,
            blocked_reasons=tuple(f"portability:{name}" for name in reasons),
        )
    full_passed = bool(full_function_checks) and all(full_function_checks.values())
    scoped_passed = bool(scoped_function_checks) and all(
        scoped_function_checks.values()
    )
    if requested_tier == "relocatable_full" and full_passed:
        return ArticulatedPromotionDecision("pass", "relocatable_full", ())
    if scoped_passed:
        return ArticulatedPromotionDecision(
            "pass", "relocatable_task_scoped", ()
        )
    failures = sorted(
        name for name, passed in scoped_function_checks.items() if not passed
    ) or ["scoped_function_checks_missing"]
    return ArticulatedPromotionDecision(
        status="blocked",
        promoted_tier=None,
        blocked_reasons=tuple(f"function:{name}" for name in failures),
    )
