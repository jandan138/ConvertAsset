import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/tables/gen_vlm_pilot_tables.py"


def load_table_module():
    spec = importlib.util.spec_from_file_location("gen_vlm_pilot_tables", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_rows_extracts_pass_only_vlm_metrics() -> None:
    module = load_table_module()

    rows = module.build_rows()

    by_id = {row["row_id"]: row for row in rows}
    assert by_id["gemma4_pass_only"]["answer_rows"] == "8/8"
    assert by_id["gemma4_pass_only"]["point_rows_original"] == "4/4"
    assert by_id["gemma4_pass_only"]["point_rows_converted"] == "4/4"
    assert by_id["gemma4_pass_only"]["answer_original"] == "4/4"
    assert by_id["gemma4_pass_only"]["answer_converted"] == "4/4"
    assert by_id["gemma4_pass_only"]["raw_point_original"] == "0/4"
    assert by_id["gemma4_pass_only"]["norm1000_point_converted"] == "3/4"
    assert by_id["gemma4_pass_only"]["pair_note"] == "Norm-1000: 3/4 same hit status; 3/4 both-hit; mean point delta 27.05 px"

    assert by_id["qwen25_json"]["response_format"] == "json"
    assert by_id["qwen25_json"]["answer_rows"] == "0/8"
    assert by_id["qwen25_json"]["answer_original"] == "--"
    assert by_id["qwen25_json"]["raw_point_converted"] == "--"
    assert by_id["qwen25_json"]["claim_boundary"] == "response_format_diagnostic_not_performance"
    assert "addCriterion" in by_id["qwen25_json"]["pair_note"]

    assert by_id["qwen25_structured"]["answer_rows"] == "8/8"
    assert by_id["qwen25_structured"]["point_rows_original"] == "3/4"
    assert by_id["qwen25_structured"]["point_rows_converted"] == "4/4"
    assert by_id["qwen25_structured"]["answer_original"] == "3/4"
    assert by_id["qwen25_structured"]["answer_converted"] == "3/4"
    assert by_id["qwen25_structured"]["raw_point_original"] == "2/3"
    assert by_id["qwen25_structured"]["raw_point_converted"] == "2/4"
    assert by_id["qwen25_structured"]["norm1000_point_original"] == "0/3"
    assert "0/3 both-hit" in by_id["qwen25_structured"]["pair_note"]


def test_write_outputs_creates_csv_and_latex(tmp_path: Path) -> None:
    module = load_table_module()
    csv_path = tmp_path / "pilot.csv"
    tex_path = tmp_path / "pilot.tex"

    module.write_outputs(csv_path=csv_path, tex_path=tex_path)

    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    assert [row["row_id"] for row in rows] == ["gemma4_pass_only", "qwen25_json", "qwen25_structured"]
    tex = tex_path.read_text(encoding="utf-8")
    assert "\\caption{PASS-only GRScenes VLM grounding pilot" in tex
    assert "Pilot only; not final benchmark performance" in tex
    assert "Qwen2.5-VL structured" in tex
    assert "Answer rows" in tex
    assert "Parsed" not in tex
    assert "Norm pair agree" not in tex
    assert "Coordinate semantics unresolved" in tex


def test_checked_in_outputs_match_generator(tmp_path: Path) -> None:
    module = load_table_module()
    csv_path = tmp_path / "pilot.csv"
    tex_path = tmp_path / "pilot.tex"

    module.write_outputs(csv_path=csv_path, tex_path=tex_path)

    assert module.DEFAULT_CSV.read_text(encoding="utf-8") == csv_path.read_text(encoding="utf-8")
    assert module.DEFAULT_TEX.read_text(encoding="utf-8") == tex_path.read_text(encoding="utf-8")
