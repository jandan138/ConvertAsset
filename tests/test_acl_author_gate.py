import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/venues/acl27/scripts/check_author_gate.py"
TEMPLATE = ROOT / "paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_WORKSHEET.md"


def load_module():
    assert SCRIPT.exists(), "ACL author-gate checker is missing"
    spec = importlib.util.spec_from_file_location("acl_author_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_private_author_gate_is_not_ready(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    (paper_root / "venues/acl27").mkdir(parents=True)

    report = module.check_author_gate(paper_root, check_git=False)

    assert report["ok"] is False
    assert report["missing_private_worksheet"] is True
    assert "OPENREVIEW_AUTHOR_GATE_FILLED.local.md" in report["message"]


def test_todo_fields_block_private_author_gate(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    worksheet.parent.mkdir(parents=True)
    worksheet.write_text(
        "| Field | Fill in local copy |\n"
        "| --- | --- |\n"
        "| Selected route | TODO: EACL 2027 via ARR / Annual ACL 2027 later |\n"
        "| Final author list and order | Alice; Bob |\n",
        encoding="utf-8",
    )

    report = module.check_author_gate(paper_root, check_git=False)

    assert report["ok"] is False
    assert report["todo_fields"] == ["Selected route"]


def test_required_fields_cover_all_todo_rows_in_template() -> None:
    module = load_module()
    template_fields = set()
    for raw_line in TEMPLATE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in {"Field", "Gate"}:
            continue
        if cells[1].startswith("TODO"):
            template_fields.add(cells[0])

    assert sorted(template_fields - set(module.REQUIRED_FIELDS)) == []


def test_completed_private_author_gate_passes_without_leaking_values(
    tmp_path: Path,
) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    worksheet.parent.mkdir(parents=True)
    rows = ["| Field | Fill in local copy |", "| --- | --- |"]
    for field in module.REQUIRED_FIELDS:
        value = "filled"
        if field == "Final author list and order":
            value = "private filled list"
        rows.append(f"| {field} | {value} |")
    worksheet.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = module.check_author_gate(paper_root, check_git=False)

    assert report["ok"] is True
    assert report["checked_fields"] == module.REQUIRED_FIELDS
    assert "private filled list" not in str(report)
