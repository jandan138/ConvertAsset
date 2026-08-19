from __future__ import annotations

from pathlib import Path

from scripts.record_analytical_balance_lichen_door_animation import (
    ANIMATION_OPEN_M,
    write_door_animation_timeline,
)


def test_door_animation_timeline_authors_sequential_open_close_samples(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    (package / "asset.usd").write_text(
        '#usda 1.0\n(\n    defaultPrim = "World"\n)\n\ndef Xform "World" {}\n',
        encoding="utf-8",
    )

    timeline = write_door_animation_timeline(
        package_asset=package / "asset.usd",
        out_usda=tmp_path / "demo_timeline.usda",
    )
    text = timeline.read_text(encoding="utf-8")

    assert "timeSamples" in text
    assert str(ANIMATION_OPEN_M) in text
    assert "Front_Sliding_Glass_Door" in text
    assert "Left_Sliding_Glass_Door" in text
    assert "Right_Sliding_Glass_Door" in text
    assert "Top_Sliding_Glass" in text
    assert "asset.usd" in text
    assert "Blue_Function_Key" not in text
