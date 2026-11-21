"""Behavior tests for the ICLR estimands (independent of model runtimes)."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/11_iclr_model_behavior/analyze.py"


def module():
    spec = importlib.util.spec_from_file_location("iclr_analysis", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def record(pair, version, point, frame="normalized_1000"):
    return {"sample_id": f"{pair}.{version}", "pair_id": pair, "version": version,
            "image": {"width": 600, "height": 450},
            "target": {"bbox_xyxy": [240, 180, 360, 270], "category": "cup"},
            "prompt": {"coordinate_frame": frame},
            "prediction": {"point_xy": point, "answer": "cup"}}


def test_end_to_end_denominator_is_all_queries():
    rows = [record(f"t{i}.v0", v, [500, 500] if (i == 0 or (v == "converted" and i == 1)) else None)
            for i in range(4) for v in ("original", "converted")]
    s = module().summarize(rows, "normalized_1000")
    assert s["original"]["success_rate"] == 0.25
    assert s["converted"]["success_rate"] == 0.5
    assert s["delta"] == 0.25
    assert s["original"]["conditional_hit_rate"] == 1.0
    assert s["paired_valid_n"] == 1


def test_coordinate_conversion_uses_real_image_units():
    m = module()
    assert m.point_pixels(record("t.v0", "original", [500, 500]), "normalized_1000") == (300, 225)
    assert m.point_pixels(record("t.v0", "original", [300, 225]), "pixel") == (300, 225)
    assert m.point_pixels(record("t.v0", "original", [50, 50]), "normalized_100") == (300, 225)
    s = m.summarize([record("t.v0", "original", [500, 500]),
                     record("t.v0", "converted", [600, 500])], "normalized_1000")
    assert s["displacement_mean_px"] == 60.0


def test_missing_points_and_out_of_frame_are_failures():
    m = module()
    s = m.summarize([record("t.v0", "original", None),
                     record("t.v0", "converted", [500, 3300])], "normalized_1000")
    assert s["original"]["success_rate"] == s["converted"]["success_rate"] == 0
    assert s["original"]["conditional_hit_rate"] is None
    assert s["converted"]["in_frame_n"] == 0
    assert m.point_pixels(record("t.v1", "original", [True, False]), "pixel") is None


def test_duplicate_or_incomplete_pairs_raise():
    m = module()
    row = record("t.v0", "original", [500, 500])
    with pytest.raises(ValueError):
        m.summarize([row, row], "normalized_1000")
    with pytest.raises(ValueError):
        m.summarize([row], "normalized_1000")


def test_view_set_changes_even_when_hit_counts_do_not():
    rows = [record("t.v0", "original", [500, 500]), record("t.v0", "converted", [0, 0]),
            record("t.v1", "original", [0, 0]), record("t.v1", "converted", [500, 500])]
    s = module().summarize(rows, "normalized_1000")
    assert s["view_sets_changed"] == 1
    assert s["delta"] == 0


def test_group_bootstrap_keeps_views_together():
    low, high = module().cluster_ci({"a": [1, 1], "b": [-1, -1]}, rounds=1000)
    assert (low, high) == (-1.0, 1.0)


def test_same_count_does_not_imply_same_pair_set():
    m = module()
    rows = [record("a.v0", "original", [500, 500]), record("b.v0", "converted", [500, 500])]
    with pytest.raises(ValueError):
        m.summarize(rows, "normalized_1000")


def intervention_module():
    script = SCRIPT.parent / "prepare_interventions.py"
    spec = importlib.util.spec_from_file_location("iclr_interventions", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_window_crossover_changes_only_requested_region():
    from PIL import Image
    m = intervention_module()
    original = Image.new("RGB", (10, 8), (10, 20, 30))
    converted = Image.new("RGB", (10, 8), (100, 110, 120))
    box = [2, 2, 6, 6]
    target = m.crossover(original, converted, box, "target")
    context = m.crossover(original, converted, box, "context")
    assert target.getpixel((3, 3)) == converted.getpixel((3, 3))
    assert target.getpixel((0, 0)) == original.getpixel((0, 0))
    assert context.getpixel((3, 3)) == original.getpixel((3, 3))
    assert context.getpixel((0, 0)) == converted.getpixel((0, 0))


def test_tiled_box_translation_and_gutter():
    from PIL import Image
    m = intervention_module()
    tile = Image.new("RGB", (600, 450), "white")
    image, box = m.tile_pair(tile, tile, [240, 180, 360, 270], side=1)
    assert image.size == (1216, 450)
    assert box == [856, 180, 976, 270]
    assert not (box[0] <= image.width / 2 <= box[2])
