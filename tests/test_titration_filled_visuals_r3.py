from scripts.build_titration_filled_visuals_r3 import lower_profile, column_state, meniscus_mesh


def test_column_does_not_consume_precharge_or_move_bottom():
    full = column_state(25, 25)
    half = column_state(12.5, 25)
    assert abs(full['surface_z'] - 0.23) < 1e-9
    assert abs(half['surface_z'] - 0.07) < 1e-9
    assert full['bottom_z'] == half['bottom_z'] == -0.09
    assert column_state(0, 25)['visible'] is False
    assert lower_profile()[-1] == (-0.09, 0.005)
    assert lower_profile()[0][0] < -0.27


def test_meniscus_is_concave_and_thin():
    points, counts, indices = meniscus_mesh()
    assert points[0][2] < points[1][2]
    assert max(p[2] for p in points)-min(p[2] for p in points) <= 0.00031
    assert sum(counts) == len(indices)
