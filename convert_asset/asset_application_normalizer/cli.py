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
    parser.add_argument("--source-runtime", required=True, help="Source runtime lineage, MVP: isaac51")
    parser.add_argument("--target-runtime", required=True, help="Target runtime profile, MVP: isaac41")
    parser.add_argument("--target-benchmark", required=True, help="Target benchmark profile, MVP: ebench-lift2")
    parser.add_argument("--task-id", required=True, help="Target task id, e.g. Lift2.DryingBox")
    parser.add_argument("--contract", default=None, help="Task contract YAML/JSON path")
    parser.add_argument("--required-prim", action="append", default=[], help="Required prim path; may repeat")
    parser.add_argument(
        "--material-policy",
        default="native-or-mirror",
        help="native-or-mirror, preview-fallback, waiver-ok, or block-on-gap",
    )
    parser.add_argument("--allow-waiver", default=None, help="Waiver policy YAML path")
    parser.add_argument("--gates", default="static", help="Comma-separated gates, e.g. static,runtime")
    parser.add_argument("--evidence-out", default=None, help="Manifest output path")
    parser.add_argument("--dry-run", action="store_true", help="Write manifest only; do not write package contents")


def request_from_args(args: argparse.Namespace) -> NormalizeAssetRequest:
    return NormalizeAssetRequest(
        source_usd=Path(args.source_usd),
        out_dir=Path(args.out),
        asset_id=str(args.asset_id),
        asset_class=str(args.asset_class),
        source_runtime=str(args.source_runtime),
        target_runtime=str(args.target_runtime),
        target_benchmark=str(args.target_benchmark),
        task_id=str(args.task_id),
        contract=Path(args.contract) if args.contract else None,
        required_prims=list(args.required_prim or []),
        material_policy=str(args.material_policy),
        allow_waiver=Path(args.allow_waiver) if args.allow_waiver else None,
        gates=parse_gates(str(args.gates) if args.gates else None),
        evidence_out=Path(args.evidence_out) if args.evidence_out else None,
        dry_run=bool(args.dry_run),
    )


def run_from_args(args: argparse.Namespace) -> int:
    result = normalize_asset(request_from_args(args))
    return int(result.return_code)
