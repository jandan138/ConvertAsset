from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/qualify_gpu_pbd_transfer.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("qualify_gpu_pbd_transfer", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_classifies_source_target_spill_and_below() -> None:
    module = _module()
    source_matrix = np.eye(4)
    source_matrix[3, :3] = [0.25, 0.0, 0.0]
    positions = np.asarray(
        [
            [0.25, 0.0, 0.02],
            [0.0, 0.0, 0.03],
            [0.2, 0.2, 0.02],
            [0.0, 0.0, -0.01],
        ]
    )

    result = module.classify_particles(
        positions,
        source_matrix=source_matrix,
        source_cavity={"radius_m": 0.019185, "floor_z_m": 0.011705, "rim_z_m": 0.27824},
        target_cavity={"radius_m": 0.03527, "floor_z_m": 0.003, "rim_z_m": 0.11509},
        np=np,
    )

    assert result == {
        "source": 1,
        "target": 1,
        "below_support": 1,
        "spill": 1,
        "particle_count": 4,
    }


def test_pose_for_pivot_keeps_local_rim_at_world_pivot() -> None:
    module = _module()
    position, orientation = module.pose_for_pivot(
        pivot_xyz=np.asarray([0.02, 0.0, 0.14]),
        rim_z_m=0.27824,
        angle_deg=-105.0,
        np=np,
    )
    matrix = module.source_matrix(position, orientation, np)
    rim_world = np.asarray([0.0, 0.0, 0.27824, 1.0]) @ matrix

    assert np.allclose(rim_world[:3], [0.02, 0.0, 0.14])


def test_spill_is_reported_but_not_a_blocking_gate() -> None:
    module = _module()
    checks = module.qualification_checks(
        static_source_ratio=1.0,
        maximum_below_support=0,
        final={"particle_count": 548, "target": 300, "below_support": 0, "spill": 248},
        hard_runtime_errors=[],
        mean_rtx_fps=60.0,
    )

    assert checks["target_reception"] is True
    assert "spill" not in checks
    assert all(checks.values())


def test_runtime_reader_prefers_live_points_over_rest_state() -> None:
    module = _module()

    class Attribute:
        def __init__(self, value: object) -> None:
            self.value = value

        def Get(self) -> object:
            return self.value

    class Prim:
        def GetAttribute(self, name: str) -> Attribute:
            value = [[1.0, 0.0, 0.0]] if name == "points" else [[9.0, 0.0, 0.0]]
            return Attribute(value)

    class Stage:
        def GetPrimAtPath(self, path: str) -> Prim:
            return Prim()

    assert module._read_positions(Stage(), np).tolist() == [[1.0, 0.0, 0.0]]
