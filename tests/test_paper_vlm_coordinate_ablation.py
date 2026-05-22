import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/tables/gen_vlm_coordinate_ablation.py"


def load_table_module():
    spec = importlib.util.spec_from_file_location("gen_vlm_coordinate_ablation", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_rows_extracts_raw_vs_normalized_metrics() -> None:
    module = load_table_module()

    rows = module.build_rows()
    by_id = {row["row_id"]: row for row in rows}

    assert list(by_id) == ["clean_gemma4", "clean_qwen25", "zoom_gemma4", "zoom_qwen25"]
    assert by_id["clean_gemma4"]["prompt_frame"] == "normalized_1000"
    assert by_id["clean_gemma4"]["raw_point"] == "0/15 / 0/15"
    assert by_id["clean_gemma4"]["norm1000_point"] == "8/15 / 6/15"
    assert by_id["clean_gemma4"]["norm1000_pair"] == "11/15 same; 5/15 both-hit"
    assert by_id["clean_qwen25"]["answer"] == "8/11 / 9/12"
    assert by_id["clean_qwen25"]["raw_point"] == "5/14 / 5/15"
    assert by_id["clean_qwen25"]["norm1000_point"] == "0/14 / 0/15"
    assert by_id["clean_qwen25"]["interpretation"] == "raw diagnostic scores higher; coordinate semantics unresolved"
    assert by_id["zoom_gemma4"]["norm1000_point"] == "11/14 / 13/14"
    assert by_id["zoom_qwen25"]["raw_pair"] == "8/13 same; 5/13 both-hit"
    assert by_id["zoom_qwen25"]["norm1000_pair"] == "9/13 same; 1/13 both-hit"


def test_write_outputs_creates_csv_and_latex(tmp_path: Path) -> None:
    module = load_table_module()
    csv_path = tmp_path / "coordinate_ablation.csv"
    tex_path = tmp_path / "coordinate_ablation.tex"

    module.write_outputs(csv_path=csv_path, tex_path=tex_path)

    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    assert [row["row_id"] for row in rows] == ["clean_gemma4", "clean_qwen25", "zoom_gemma4", "zoom_qwen25"]
    tex = tex_path.read_text(encoding="utf-8")
    assert "\\caption{Coordinate-frame ablation for GRScenes VLM pilot grounding" in tex
    assert "\\label{tab:grscenes_vlm_coordinate_ablation}" in tex
    assert "raw diagnostic scores higher" in tex
    assert "final benchmark metric" in tex


def test_checked_in_outputs_match_generator(tmp_path: Path) -> None:
    module = load_table_module()
    csv_path = tmp_path / "coordinate_ablation.csv"
    tex_path = tmp_path / "coordinate_ablation.tex"

    module.write_outputs(csv_path=csv_path, tex_path=tex_path)

    assert module.DEFAULT_CSV.read_text(encoding="utf-8") == csv_path.read_text(encoding="utf-8")
    assert module.DEFAULT_TEX.read_text(encoding="utf-8") == tex_path.read_text(encoding="utf-8")
