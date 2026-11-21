from scripts.build_spoon_physics_lane_geometry import (
    REGIONS,
    cell_spec,
    deform_point,
    region_weight,
)


def test_handle_scale_does_not_move_neck_or_head():
    assert region_weight(-0.2, "handle") == 1.0
    assert region_weight(0.0, "handle") < 0.05
    assert region_weight(0.2, "handle") == 0.0
    handle = deform_point([0.01, 0.0, -0.2], 2.0, "handle")
    neck = deform_point([0.01, 0.0, 0.0], 2.0, "handle")
    head = deform_point([0.01, 0.0, 0.2], 2.0, "handle")
    assert handle[0] == 0.02
    assert abs(neck[0] - 0.01) < 5e-4
    assert head == [0.01, 0.0, 0.2]


def test_neck_scale_leaves_handle_and_head():
    assert region_weight(-0.2, "neck") == 0.0
    assert region_weight(0.0, "neck") == 1.0
    assert region_weight(0.2, "neck") == 0.0
    handle = deform_point([0.01, 0.0, -0.2], 2.0, "neck")
    neck = deform_point([0.01, 0.0, 0.0], 2.0, "neck")
    head = deform_point([0.01, 0.0, 0.2], 2.0, "neck")
    assert handle == [0.01, 0.0, -0.2]
    assert neck[0] == 0.02
    assert head == [0.01, 0.0, 0.2]


def test_head_scale_leaves_handle_and_neck():
    assert region_weight(-0.2, "head") == 0.0
    assert region_weight(0.0, "head") == 0.0
    assert region_weight(0.2, "head") == 1.0
    handle = deform_point([0.01, 0.0, -0.2], 2.0, "head")
    neck = deform_point([0.01, 0.0, 0.0], 2.0, "head")
    head = deform_point([0.01, 0.0, 0.2], 2.0, "head")
    assert handle == [0.01, 0.0, -0.2]
    assert neck == [0.01, 0.0, 0.0]
    assert head[0] == 0.02


def test_handle_thick_scales_y_only():
    region, scale, axes = cell_spec("P2-handle-thick-2p00")
    assert (region, scale, axes) == ("handle", 2.0, "y")
    point = deform_point([0.01, 0.02, -0.2], scale, region, axes)
    assert point == [0.01, 0.04, -0.2]
    assert "P2-handle-thick-2p00" in REGIONS
