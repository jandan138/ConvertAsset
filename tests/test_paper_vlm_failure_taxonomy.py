import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/tables/gen_vlm_failure_taxonomy.py"


def load_table_module():
    spec = importlib.util.spec_from_file_location("gen_vlm_failure_taxonomy", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_rows_extracts_selected_failure_cases() -> None:
    module = load_table_module()

    rows = module.build_rows()
    by_id = {row["row_id"]: row for row in rows}

    assert list(by_id) == [
        "clean_gemma_faucet_norm_flip",
        "clean_qwen_bottle_raw_flip",
        "clean_qwen_clock_answer_flip",
        "clean_qwen_faucet_parse_truncation",
        "zoom_qwen_picture_null_answer",
        "zoom_qwen_faucet_answer_truncation",
        "zoom_qwen_clock_counterexample",
    ]
    assert by_id["clean_qwen_bottle_raw_flip"]["point_metric"] == "raw_diagnostic"
    assert by_id["clean_qwen_bottle_raw_flip"]["original_status"] == "ans=hit; point=hit(raw)"
    assert by_id["clean_qwen_bottle_raw_flip"]["converted_status"] == "ans=hit; point=miss(raw)"
    assert "normalized-1000-requested" in by_id["clean_qwen_bottle_raw_flip"]["note"]
    assert by_id["clean_qwen_clock_answer_flip"]["original_status"] == "ans=miss; point=miss(raw)"
    assert by_id["clean_qwen_clock_answer_flip"]["converted_status"] == "ans=hit; point=miss(raw)"
    assert by_id["zoom_qwen_faucet_answer_truncation"]["converted_answer"] == "fauc"
    assert by_id["zoom_qwen_clock_counterexample"]["failure_type"] == "converted_raw_point_counterexample"


def test_write_outputs_creates_csv_and_latex(tmp_path: Path) -> None:
    module = load_table_module()
    csv_path = tmp_path / "failure_taxonomy.csv"
    tex_path = tmp_path / "failure_taxonomy.tex"

    module.write_outputs(csv_path=csv_path, tex_path=tex_path)

    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 7
    assert rows[0]["row_id"] == "clean_gemma_faucet_norm_flip"
    tex = tex_path.read_text(encoding="utf-8")
    assert "\\caption{Selected GRScenes VLM pilot failure taxonomy" in tex
    assert "\\label{tab:grscenes_vlm_failure_taxonomy}" in tex
    assert "clean\\_qwen\\_bottle\\_raw\\_flip" not in tex
    assert "raw point hit on original, miss on converted" in tex
    assert "raw-image scoring diagnostic over normalized-1000-requested outputs" in tex


def test_checked_in_outputs_match_generator(tmp_path: Path) -> None:
    module = load_table_module()
    csv_path = tmp_path / "failure_taxonomy.csv"
    tex_path = tmp_path / "failure_taxonomy.tex"

    module.write_outputs(csv_path=csv_path, tex_path=tex_path)

    assert module.DEFAULT_CSV.read_text(encoding="utf-8") == csv_path.read_text(encoding="utf-8")
    assert module.DEFAULT_TEX.read_text(encoding="utf-8") == tex_path.read_text(encoding="utf-8")
