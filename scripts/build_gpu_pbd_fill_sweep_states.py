#!/usr/bin/env python3
"""Derive deterministic staged particle seeds from one qualified loaded start.

These files are build inputs only.  Their authored q95 height is not a runtime
claim; each variant must subsequently pass the v2 dynamic-loaded-start cold
qualification against live Isaac Sim particle positions.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping


SOURCE_INITIAL_XYZ = (0.25, 0.0, 0.0)


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def fill_ratio(points: list[list[float]], cavity: dict[str, Any]) -> float:
    floor = float(cavity["floor_z_m"])
    rim = float(cavity["rim_z_m"])
    return (_quantile([float(point[2]) for point in points], 0.95) - floor) / (
        rim - floor
    )


def _shift_to_target(
    points: list[list[float]], *, target: float, cavity: dict[str, Any]
) -> list[list[float]]:
    floor = float(cavity["floor_z_m"])
    rim = float(cavity["rim_z_m"])
    target_surface = floor + target * (rim - floor)
    shift = target_surface - _quantile([point[2] for point in points], 0.95)
    shifted = [[point[0], point[1], point[2] + shift] for point in points]
    minimum = min(point[2] for point in shifted)
    if minimum < floor:
        correction = floor - minimum
        shifted = [[point[0], point[1], point[2] + correction] for point in shifted]
    return [[round(value, 7) for value in point] for point in shifted]


def build_variants(
    *,
    baseline_local_positions: list[list[float]],
    cavity: dict[str, Any],
    baseline_fill_ratio: float,
    targets: Iterable[float],
    count_ratios: Mapping[float, float] | None = None,
) -> dict[float, list[list[float]]]:
    if not baseline_local_positions:
        raise ValueError("baseline particle state is empty")
    baseline = [[float(value) for value in point] for point in baseline_local_positions]
    ordered = sorted(baseline, key=lambda point: (point[2], point[1], point[0]))
    count = len(baseline)
    variants: dict[float, list[list[float]]] = {}
    for target in targets:
        target = float(target)
        if target == baseline_fill_ratio:
            variants[target] = baseline
            continue
        count_ratio = (
            float(count_ratios[target])
            if count_ratios is not None and target in count_ratios
            else target
        )
        desired_count = max(1, round(count * count_ratio / baseline_fill_ratio))
        if desired_count < count:
            seed = ordered[:desired_count]
        else:
            seed = list(baseline)
            remaining = desired_count - count
            while remaining:
                take = min(remaining, count)
                upper = ordered[:take]
                highest = max(point[2] for point in seed)
                lowest = min(point[2] for point in upper)
                spacing = 0.00582
                shift = highest - lowest + spacing
                seed.extend(
                    [[point[0], point[1], point[2] + shift] for point in upper]
                )
                remaining -= take
        variants[target] = _shift_to_target(seed, target=target, cavity=cavity)
    return variants


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-state", required=True, type=Path)
    parser.add_argument("--fixture-profile", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--baseline-fill-ratio", type=float, default=0.40)
    parser.add_argument("--targets", default="0.20,0.40,0.60,0.80")
    parser.add_argument(
        "--count-ratios",
        help=(
            "Optional comma-separated effective fill ratios controlling particle "
            "counts independently from authored q95 target heights."
        ),
    )
    args = parser.parse_args()
    state = json.loads(args.baseline_state.read_text(encoding="utf-8"))
    profile = json.loads(args.fixture_profile.read_text(encoding="utf-8"))
    targets = tuple(float(value) for value in args.targets.split(","))
    count_ratios = None
    if args.count_ratios is not None:
        values = tuple(float(value) for value in args.count_ratios.split(","))
        if len(values) != len(targets):
            parser.error("--count-ratios must have the same length as --targets")
        count_ratios = dict(zip(targets, values, strict=True))
    variants = build_variants(
        baseline_local_positions=state["positions"],
        cavity=profile["source"]["cavity"],
        baseline_fill_ratio=args.baseline_fill_ratio,
        targets=targets,
        count_ratios=count_ratios,
    )
    args.out.mkdir(parents=True, exist_ok=False)
    records = []
    for target, local in variants.items():
        label = f"fill{round(target * 100):02d}"
        world = [
            [
                round(point[0] + SOURCE_INITIAL_XYZ[0], 7),
                round(point[1] + SOURCE_INITIAL_XYZ[1], 7),
                round(point[2] + SOURCE_INITIAL_XYZ[2], 7),
            ]
            for point in local
        ]
        path = args.out / f"{label}_pre_settled_seed.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "aan.gpu_pbd_settled_particle_state.v1",
                    "coordinate_space": "world",
                    "particle_count": len(world),
                    "positions": world,
                    "source_pose": {
                        "xyz_m": list(SOURCE_INITIAL_XYZ),
                        "wxyz": [1.0, 0.0, 0.0, 0.0],
                    },
                    "seed_only_not_runtime_qualified": True,
                    "target_settled_fill_ratio": target,
                    "authored_q95_fill_ratio": fill_ratio(local, profile["source"]["cavity"]),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        records.append(
            {
                "fill_level_id": label,
                "target_settled_fill_ratio": target,
                "particle_count": len(world),
                "path": path.name,
                "sha256": _sha(path),
            }
        )
    manifest = args.out / "fill_sweep_seed_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "aan.gpu_pbd_fill_sweep_seeds.v1",
                "baseline_state_sha256": _sha(args.baseline_state),
                "qualification_required": True,
                "variants": records,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
