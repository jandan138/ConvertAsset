"""CLI adapter for the Asset Application Normalizer."""

from __future__ import annotations

import argparse
from pathlib import Path

from .model import NormalizeAssetRequest
from .pipeline import normalize_asset, parse_gates


def add_normalize_asset_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "normalize-asset",
        help="AAN MVP: write a dry-run asset package evidence manifest",
    )
    parser.add_argument("source_usd", help="Path to source USD file")
    parser.add_argument("--out", required=True, help="Target package directory")
    parser.add_argument("--asset-id", required=True, help="Stable asset id, e.g. DryingBox")
    parser.add_argument("--asset-class", default="auto", help="rigid, articulated, or auto")
    parser.add_argument(
        "--asset-role",
        default="dynamic",
        choices=("dynamic", "visual_static", "visual_static_environment"),
        help="Admission role; visual_static strips scoped physics from the owned package.",
    )
    parser.add_argument("--source-runtime", required=True, help="Source runtime lineage, MVP: isaac51")
    parser.add_argument("--target-runtime", required=True, help="Target runtime profile, MVP: isaac41")
    parser.add_argument("--target-benchmark", required=True, help="Target benchmark profile, MVP: ebench-lift2")
    parser.add_argument("--task-id", required=True, help="Target task id, e.g. Lift2.DryingBox")
    parser.add_argument("--contract", default=None, help="Task contract YAML/JSON path")
    parser.add_argument("--required-prim", action="append", default=[], help="Required prim path; may repeat")
    parser.add_argument(
        "--asset-scope-prim",
        action="append",
        default=[],
        help="Role-normalization scope; may repeat, defaults to --required-prim.",
    )
    parser.add_argument(
        "--material-policy",
        default="native-or-mirror",
        help="native-or-mirror, preview-fallback, waiver-ok, or block-on-gap",
    )
    parser.add_argument("--allow-waiver", default=None, help="Waiver policy YAML path")
    parser.add_argument(
        "--physics-profile",
        default=None,
        help=(
            "Source-bound AAN dynamic-physics profile JSON. Required for "
            "Scenario Forge dynamic admission."
        ),
    )
    parser.add_argument(
        "--interaction-profile",
        default=None,
        help=(
            "Source-bound AAN object-interaction profile JSON. It authors the "
            "package rigid root, colliders, and named frames before mass profile resolution."
        ),
    )
    parser.add_argument("--gates", default="static", help="Comma-separated gates, e.g. static,runtime")
    parser.add_argument("--evidence-out", default=None, help="Manifest output path")
    parser.add_argument(
        "--runtime-python",
        default=None,
        help="Explicit Isaac runtime Python executable for auditable runtime evidence.",
    )
    parser.add_argument(
        "--warning-baseline-log",
        default=None,
        help="Optional baseline PhysX log for scoped warning-diff evidence.",
    )
    parser.add_argument(
        "--warning-baseline-scope-prim",
        action="append",
        default=[],
        help="Baseline-log prim scope; defaults to the package role scope and may repeat.",
    )
    parser.add_argument(
        "--runtime-physx-log",
        default=None,
        help="Optional PhysX log from a consumer-instantiated runtime for the scoped warning gate.",
    )
    parser.add_argument(
        "--runtime-scope-binding",
        action="append",
        default=[],
        metavar="PACKAGE_SCOPE=RUNTIME_SCOPE",
        help=(
            "Exact package-to-instantiated runtime scope binding; may repeat. "
            "Non-identity mappings require --runtime-physx-log."
        ),
    )
    parser.add_argument(
        "--expected-runtime-version",
        default="4.1",
        help="Required Isaac/Kit major.minor for the runtime gate (default: 4.1).",
    )
    parser.add_argument(
        "--runtime-timeout-seconds",
        type=int,
        default=600,
        help="Bounded timeout for the isolated Isaac runtime worker (default: 600).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Write manifest only; do not write package contents")


def request_from_args(args: argparse.Namespace) -> NormalizeAssetRequest:
    return NormalizeAssetRequest(
        source_usd=Path(args.source_usd),
        out_dir=Path(args.out),
        asset_id=str(args.asset_id),
        asset_class=str(args.asset_class),
        asset_role=str(args.asset_role),
        source_runtime=str(args.source_runtime),
        target_runtime=str(args.target_runtime),
        target_benchmark=str(args.target_benchmark),
        task_id=str(args.task_id),
        contract=Path(args.contract) if args.contract else None,
        required_prims=list(args.required_prim or []),
        asset_scope_prims=list(args.asset_scope_prim or []),
        material_policy=str(args.material_policy),
        allow_waiver=Path(args.allow_waiver) if args.allow_waiver else None,
        physics_profile=Path(args.physics_profile) if args.physics_profile else None,
        interaction_profile=(
            Path(args.interaction_profile) if args.interaction_profile else None
        ),
        gates=parse_gates(str(args.gates) if args.gates else None),
        evidence_out=Path(args.evidence_out) if args.evidence_out else None,
        runtime_python=Path(args.runtime_python) if args.runtime_python else None,
        warning_baseline_log=Path(args.warning_baseline_log) if args.warning_baseline_log else None,
        warning_baseline_scope_prims=list(args.warning_baseline_scope_prim or []),
        runtime_physx_log=Path(args.runtime_physx_log) if args.runtime_physx_log else None,
        runtime_scope_bindings=_runtime_scope_bindings(args.runtime_scope_binding or []),
        expected_runtime_version=str(args.expected_runtime_version),
        runtime_timeout_seconds=int(args.runtime_timeout_seconds),
        dry_run=bool(args.dry_run),
    )


def _runtime_scope_bindings(raw_bindings: list[str]) -> list[dict[str, str]]:
    """Keep CLI syntax compact while deferring path validation to AAN gates."""
    bindings: list[dict[str, str]] = []
    for raw in raw_bindings:
        package_scope, separator, runtime_scope = str(raw).partition("=")
        if not separator:
            bindings.append({"package_scope": package_scope, "runtime_scope": ""})
            continue
        bindings.append(
            {
                "package_scope": package_scope.strip(),
                "runtime_scope": runtime_scope.strip(),
            }
        )
    return bindings


def run_from_args(args: argparse.Namespace) -> int:
    result = normalize_asset(request_from_args(args))
    return int(result.return_code)
