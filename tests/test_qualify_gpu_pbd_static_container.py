from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/qualify_gpu_pbd_static_container.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("qualify_gpu_pbd_static", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_classifies_static_particles_against_measured_cavity() -> None:
    module = _module()
    positions = np.asarray([[0.0, 0.0, 0.02], [0.03, 0.0, 0.02], [0, 0, -0.1]])

    result = module.classify_positions(
        positions,
        np,
        module.ContainmentBounds(
            center_xy_m=(0.0, 0.0),
            radius_m=0.019185,
            floor_z_m=0.011705,
            rim_z_m=0.27824,
            support_z_m=0.0,
        ),
    )

    assert result == {
        "inside": 1,
        "outside": 2,
        "below_support": 1,
        "particle_count": 3,
    }


def test_classifies_translated_reference_beaker_in_world_coordinates() -> None:
    module = _module()
    positions = np.asarray(
        [
            [0.312, 0.092, 0.79],
            [0.40, 0.092, 0.79],
            [0.312, 0.092, 0.70],
        ]
    )

    result = module.classify_positions(
        positions,
        np,
        module.ContainmentBounds(
            center_xy_m=(0.312, 0.092),
            radius_m=0.05,
            floor_z_m=0.778,
            rim_z_m=0.864,
            support_z_m=0.772,
        ),
    )

    assert result == {
        "inside": 1,
        "outside": 2,
        "below_support": 1,
        "particle_count": 3,
    }


def test_gpu_error_blocks_otherwise_passing_observation() -> None:
    module = _module()
    result = module.finalize_checks(
        minimum_inside=540,
        maximum_below=0,
        particle_count=548,
        mean_rtx_fps=50.0,
        hard_runtime_errors=["Non-GPU-compatible convex mesh"],
    )

    assert result["gpu_cooking"] is False
    assert result["overall_status"] == "blocked"


def test_summarizes_particle_distribution() -> None:
    module = _module()
    positions = np.asarray([[0.0, 0.0, 0.01], [0.03, 0.04, 0.02]])

    result = module.summarize_positions(
        positions,
        np,
        module.ContainmentBounds(
            center_xy_m=(0.0, 0.0),
            radius_m=0.019185,
            floor_z_m=0.011705,
            rim_z_m=0.27824,
            support_z_m=0.0,
        ),
    )

    assert result["radial_max_m"] == 0.05
    assert result["z_range_m"] == [0.01, 0.02]
