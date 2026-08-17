from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_gpu_pbd_fill_sweep_states.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("build_fill_sweep", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_staged_variants_are_monotonic_and_hit_authored_surface_targets() -> None:
    module = _module()
    baseline = [
        [x, y, 0.04 + layer * 0.01]
        for layer in range(10)
        for x, y in ((-0.004, -0.004), (0.004, -0.004), (-0.004, 0.004), (0.004, 0.004))
    ]
    cavity = {"floor_z_m": 0.01, "rim_z_m": 0.31}

    variants = module.build_variants(
        baseline_local_positions=baseline,
        cavity=cavity,
        baseline_fill_ratio=0.40,
        targets=(0.20, 0.40, 0.60, 0.80),
    )

    counts = [len(variants[target]) for target in (0.20, 0.40, 0.60, 0.80)]
    assert counts == sorted(counts)
    assert variants[0.40] == baseline
    for target, points in variants.items():
        assert abs(module.fill_ratio(points, cavity) - target) <= 0.01
        assert min(point[2] for point in points) >= cavity["floor_z_m"]


def test_particle_count_can_be_tuned_without_raising_authored_surface() -> None:
    module = _module()
    baseline = [[0.0, 0.0, 0.02 + index * 0.001] for index in range(100)]
    cavity = {"floor_z_m": 0.01, "rim_z_m": 0.31}

    variant = module.build_variants(
        baseline_local_positions=baseline,
        cavity=cavity,
        baseline_fill_ratio=0.40,
        targets=(0.89,),
        count_ratios={0.89: 0.915},
    )[0.89]

    assert len(variant) == round(100 * 0.915 / 0.40)
    assert abs(module.fill_ratio(variant, cavity) - 0.89) <= 0.01
