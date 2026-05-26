import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFILL_SCRIPT = ROOT / "paper/venues/acl27/scripts/prefill_author_gate.py"
CHECK_SCRIPT = ROOT / "paper/venues/acl27/scripts/check_author_gate.py"


def load_prefill_module():
    assert PREFILL_SCRIPT.exists(), "ACL author-gate prefill helper is missing"
    spec = importlib.util.spec_from_file_location("acl_author_gate_prefill", PREFILL_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_check_module():
    assert CHECK_SCRIPT.exists(), "ACL author-gate checker is missing"
    spec = importlib.util.spec_from_file_location("acl_author_gate_check", CHECK_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_private_worksheet(
    check_module,
    worksheet: Path,
    overrides: dict[str, str] | None = None,
) -> None:
    values = {field: "TODO" for field in check_module.REQUIRED_FIELDS}
    if overrides:
        values.update(overrides)
    rows = ["| Field | Fill in local copy |", "| --- | --- |"]
    rows.extend(f"| {field} | {values[field]} |" for field in check_module.REQUIRED_FIELDS)
    worksheet.parent.mkdir(parents=True)
    worksheet.write_text("\n".join(rows) + "\n", encoding="utf-8")


def make_packet(paper_root: Path) -> Path:
    packet = paper_root / "submissions/acl27_arr_candidate_20260526"
    for relpath in (
        "main.pdf",
        "openreview/METADATA.md",
        "openreview/RESPONSIBLE_NLP_CHECKLIST.md",
        "supplemental/README.md",
        "supplemental/manifest.json",
    ):
        path = packet / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{relpath}\n", encoding="utf-8")
    return packet


PDFINFO_TEXT = """\
Pages:           12
Page size:       595.276 x 841.89 pts (A4)
File size:       306187 bytes
PDF version:     1.5
"""


def test_prefill_updates_only_repo_evidence_rows_without_private_values(
    tmp_path: Path,
) -> None:
    prefill = load_prefill_module()
    check = load_check_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    write_private_worksheet(
        check,
        worksheet,
        {"Final author list and order": "private filled list"},
    )
    make_packet(paper_root)

    values = prefill.build_safe_prefill_values(
        paper_root,
        pdfinfo_text=PDFINFO_TEXT,
        timestamp_utc="2026-05-26T18:07:24Z",
    )
    report = prefill.apply_prefill(worksheet, values)

    assert report["ok"] is True
    assert "private filled list" not in str(report)
    assert set(report["changed_fields"]) == {
        "Clean PDF build command and timestamp",
        "Final PDF page count / page size",
        "Undefined citation/reference scan",
        "Staging command and packet path",
        "Staged file list",
        "Local path / username / private-link scan",
        "Acknowledgment scan",
        "Limitations / Ethical Considerations / References text scan",
    }

    fields = check.parse_markdown_table_fields(worksheet.read_text(encoding="utf-8"))
    assert fields["Final author list and order"] == "private filled list"
    assert fields["Title approved"] == "TODO"
    assert fields["Optional media decision"] == "TODO"
    assert fields["Final decision: upload / do not upload"] == "TODO"
    assert "run_preupload_gate.py passed" in fields["Clean PDF build command and timestamp"]
    assert "12 pages" in fields["Final PDF page count / page size"]
    assert "openreview/METADATA.md" in fields["Staged file list"]
    assert fields["Local path / username / private-link scan"].startswith("pass:")


def test_prefill_keeps_author_gate_incomplete_for_human_fields(
    tmp_path: Path,
) -> None:
    prefill = load_prefill_module()
    check = load_check_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    write_private_worksheet(check, worksheet)
    make_packet(paper_root)

    values = prefill.build_safe_prefill_values(
        paper_root,
        pdfinfo_text=PDFINFO_TEXT,
        timestamp_utc="2026-05-26T18:07:24Z",
    )
    prefill.apply_prefill(worksheet, values)
    check_report = check.check_author_gate(
        paper_root,
        repo_root=tmp_path,
        check_git=False,
    )

    assert check_report["ok"] is False
    assert "Clean PDF build command and timestamp" not in check_report["todo_fields"]
    assert "Local path / username / private-link scan" not in check_report["todo_fields"]
    assert "Title approved" in check_report["todo_fields"]
    assert "Final author list and order" in check_report["todo_fields"]
    assert "Final decision: upload / do not upload" in check_report["todo_fields"]
