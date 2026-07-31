from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from convert_asset.asset_application_normalizer.object_interaction_profile import (
    load_and_resolve_interaction_profile,
)
from convert_asset.asset_application_normalizer.stage_metrics import read_stage_metrics


def _source(path: Path) -> None:
    path.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "World"
{
    def Xform "Stirrer"
    {
        def Cube "Body"
        {
            double size = 0.2
        }
    }
}
""",
        encoding="utf-8",
    )


def test_v2_profile_allows_device_specific_required_frames(tmp_path: Path) -> None:
    from pxr import Usd

    source = tmp_path / "stirrer.usda"
    _source(source)
    metrics = read_stage_metrics(source)
    assert metrics is not None
    profile = tmp_path / "interaction.json"
    profile.write_text(
        json.dumps(
            {
                "schema_version": "aan.object_interaction_profile.v2",
                "profile_id": "stirrer-test-v2",
                "revision": "test",
                "source_binding": {
                    "sha256": sha256(source.read_bytes()).hexdigest(),
                    "stage_metrics": metrics,
                },
                "asset_entry_prim": "/World/Stirrer",
                "rigid_root": {
                    "motion_role": "kinematic",
                    "disable_descendant_rigid_bodies": True,
                    "remove_descendant_mass_api": True,
                },
                "colliders": [
                    {
                        "relative_path": "__aan_collision_proxy/body",
                        "mode": "author",
                        "purpose": ["support"],
                        "geometry": {
                            "type": "Cube",
                            "size": 1.0,
                            "scale_body_local_usd": [0.2, 0.2, 0.1],
                            "translation_body_local_usd": [0, 0, 0.05],
                            "rotation_body_local_wxyz": [1, 0, 0, 0],
                        },
                    }
                ],
                "required_named_frames": ["support", "work_surface_center"],
                "named_frames": {
                    "support": {
                        "translation_body_local_usd": [0, 0, 0],
                        "rotation_body_local_wxyz": [1, 0, 0, 0],
                    },
                    "work_surface_center": {
                        "translation_body_local_usd": [0, 0, 0.1],
                        "rotation_body_local_wxyz": [1, 0, 0, 0],
                    },
                },
                "open_top": {"required": False},
                "runtime_gates": {
                    "root_motion": {
                        "required": True,
                        "min_translation_m": 0.001,
                    },
                    "stable_support": {"required": True},
                    "gripper_collision": {"required": True},
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    stage = Usd.Stage.Open(str(source))
    assert stage
    result = load_and_resolve_interaction_profile(
        profile, source, stage, ["/World/Stirrer"]
    )

    assert result.status == "pass"
    assert result.resolved is not None
    assert sorted(result.resolved["named_frames"]) == [
        "support",
        "work_surface_center",
    ]
