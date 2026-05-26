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


def complete_private_rows(module, overrides: dict[str, str] | None = None) -> list[str]:
    values = {
        field: "confirmed"
        for field in module.REQUIRED_FIELDS
    }
    values.update(
        {
            "Selected route": "EACL 2027 via ARR",
            "OpenReview profile complete for each author": "all profiles complete",
            "Reviewer-registration commitment": "confirmed by all authors",
            "All authors notified of reviewer-duty sanctions": "notified and confirmed",
            "Author contribution / authorship approval": "approved by all authors",
            "Dual submission status": "no concurrent archival submission",
            "Title approved": "approved",
            "Abstract approved and under current venue limit": "approved under limit",
            "Primary ARR area approved": "approved",
            "Secondary area / keywords approved": "approved",
            "Responsible NLP checklist copied into OpenReview": "copied into OpenReview",
            "Runtime / compute wording approved": "approved",
            "AI-assistance wording approved": "approved",
            "Model and asset license wording approved": "approved",
            "Optional media decision": "excluded by default",
            "Undefined citation/reference scan": "pass: no unresolved citations",
            "Local path / username / private-link scan": "pass: no leaks",
            "Acknowledgment scan": "pass: no acknowledgments",
            "Limitations / Ethical Considerations / References text scan": "pass: ordered",
            "Final decision: upload / do not upload": "upload",
        }
    )
    if overrides:
        values.update(overrides)
    rows = ["| Field | Fill in local copy |", "| --- | --- |"]
    rows.extend(f"| {field} | {values[field]} |" for field in module.REQUIRED_FIELDS)
    return rows


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
    rows = complete_private_rows(
        module,
        {"Final author list and order": "private filled list"},
    )
    worksheet.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = module.check_author_gate(paper_root, check_git=False)

    assert report["ok"] is True
    assert report["checked_fields"] == module.REQUIRED_FIELDS
    assert "private filled list" not in str(report)


def test_negative_human_decisions_block_private_author_gate(
    tmp_path: Path,
) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    worksheet.parent.mkdir(parents=True)
    rows = complete_private_rows(
        module,
        {
            "OpenReview profile complete for each author": "private blocked value",
            "Final decision: upload / do not upload": "do not upload",
        },
    )
    worksheet.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = module.check_author_gate(paper_root, check_git=False)

    assert report["ok"] is False
    assert report["invalid_fields"] == [
        "OpenReview profile complete for each author",
        "Final decision: upload / do not upload",
    ]
    assert "private blocked value" not in str(report)


def test_failed_final_scans_block_private_author_gate(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    worksheet.parent.mkdir(parents=True)
    rows = complete_private_rows(
        module,
        {
            "Undefined citation/reference scan": "failed: private unresolved ref",
            "Local path / username / private-link scan": "failed: private leak",
            "Acknowledgment scan": "failed: private acknowledgment",
        },
    )
    worksheet.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = module.check_author_gate(paper_root, check_git=False)

    assert report["ok"] is False
    assert report["invalid_fields"] == [
        "Undefined citation/reference scan",
        "Local path / username / private-link scan",
        "Acknowledgment scan",
    ]
    assert "private unresolved ref" not in str(report)
    assert "private leak" not in str(report)
