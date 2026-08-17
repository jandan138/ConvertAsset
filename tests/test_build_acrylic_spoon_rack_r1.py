from __future__ import annotations

import json
from pathlib import Path

from scripts.build_acrylic_spoon_rack_r1 import build


def test_build_is_source_bound_and_preserves_the_central_hole(tmp_path: Path) -> None:
    source = tmp_path / "acrylic_spoon_rack.usda"
    source.write_text(
        '#usda 1.0\n(defaultPrim = "root" metersPerUnit = 1 upAxis = "Z")\n'
        'def Xform "root" {}\n',
        encoding="utf-8",
    )

    result = build(source=source, out=tmp_path / "built")

    interaction = json.loads(result["interaction"].read_text(encoding="utf-8"))
    physics = json.loads(result["physics"].read_text(encoding="utf-8"))
    assert interaction["asset_entry_prim"] == "/World/AcrylicSpoonRack"
    assert interaction["rigid_root"]["motion_role"] == "kinematic"
    assert interaction["named_frames"]["middle_socket_04_aperture"][
        "translation_body_local_usd"
    ] == [0.0, 0.0, 0.13672]
    assert interaction["named_frames"]["socket_0_aperture"] == interaction[
        "named_frames"
    ]["middle_socket_04_aperture"]
    proxy_names = {item["relative_path"] for item in interaction["colliders"]}
    assert "__aan_collision_proxy/upper_front_rail" in proxy_names
    assert "__aan_collision_proxy/upper_rear_rail" in proxy_names
    assert "__aan_collision_proxy/upper_gap_04_left" in proxy_names
    assert "__aan_collision_proxy/upper_gap_04_right" in proxy_names
    assert "__aan_collision_proxy/socket_0_bottom" in proxy_names
    assert "__aan_collision_proxy/socket_0_wall_pos_x" in proxy_names
    assert not any(name.endswith("upper_solid_plate") for name in proxy_names)
    assert physics["scope_rules"][0]["body_rules"][0]["motion_role"] == "kinematic"
    assert physics["evidence"]["parameter_status"] == "provisional_geometry"
    assert source.read_text(encoding="utf-8").endswith('def Xform "root" {}\n')
