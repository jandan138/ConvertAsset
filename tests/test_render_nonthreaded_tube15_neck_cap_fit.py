from pathlib import Path


def test_renderer_captures_old_and_new_with_same_camera_contract() -> None:
    source = (
        Path(__file__).parents[1]
        / "scripts/render_nonthreaded_tube15_neck_cap_fit.py"
    ).read_text()
    assert '(("old", args.old.resolve()), ("new", args.new.resolve()))' in source
    assert 'f"{label}.png"' in source
    assert "same_camera_parameters" in source
    assert "RayTracedLighting" in source
