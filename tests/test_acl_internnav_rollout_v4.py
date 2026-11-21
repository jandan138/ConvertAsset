import importlib.util
from pathlib import Path
import sys

from PIL import Image
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "paper/shared/figures"
SCRIPT = FIG_DIR / "gen_acl_internnav_rollout_v4.py"
STEM = FIG_DIR / "fig_internnav_rollout_main_v4"


def load_module():
    sys.path.insert(0, str(FIG_DIR))
    spec = importlib.util.spec_from_file_location("gen_acl_internnav_rollout_v4", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v4_output_bundle_is_complete() -> None:
    for suffix in (".svg", ".pdf", ".png"):
        path = STEM.with_suffix(suffix)
        assert path.is_file(), path
        assert path.stat().st_size > 1000, path
    with Image.open(STEM.with_suffix(".png")) as image:
        assert image.size == (2160, 825)
    qa = __import__("json").loads(
        (FIG_DIR / "fig_internnav_rollout_main_v4.qa.json").read_text(encoding="utf-8")
    )
    assert qa["status"] == "pass"
    assert qa["findings"]["critical"] == []
    assert qa["findings"]["major"] == []


def test_v4_label_gutter_preflight_passes(tmp_path: Path) -> None:
    module = load_module()
    report = module.build(tmp_path)
    assert report["ok"] is True
    assert report["findings"] == []
    assert report["row_label_count"] == 3
    assert report["column_count"] == 4
    assert report["label_right_x"] < report["first_image_x"]
    assert report["declared_gap_pixels_at_300_dpi"] >= 24


def test_v4_svg_keeps_editable_labels_and_portable_paths() -> None:
    text = STEM.with_suffix(".svg").read_text(encoding="utf-8")
    assert "<text" in text
    assert "SR O/N 1/1" in text
    assert "SR O/N 1/0" in text
    assert "SR O/N 0/1" in text
    assert "/cpfs/" not in text
    assert "/root/" not in text


def test_v4_is_active_and_registered() -> None:
    results = (ROOT / "paper/venues/acl27/sections/results.tex").read_text(
        encoding="utf-8"
    )
    limitations = (ROOT / "paper/venues/acl27/sections/limitations.tex").read_text(
        encoding="utf-8"
    )
    assert "fig_internnav_rollout_main_v4.pdf" in results
    assert "fig_internnav_rollout_main_v3.pdf" not in results
    assert "O/N in the row labels denotes" in results
    assert "fig_internnav_rollout_main_v4.pdf" not in limitations

    registry = yaml.safe_load((FIG_DIR / "sources.yaml").read_text(encoding="utf-8"))
    entry = next(
        item for item in registry["figures"] if item["id"] == "fig_internnav_rollout_main_v4"
    )
    assert entry["generated_by"] == "paper/shared/figures/gen_acl_internnav_rollout_v4.py"
    assert {Path(path).suffix for path in entry["outputs"]} == {
        ".svg",
        ".pdf",
        ".png",
    }
