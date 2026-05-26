import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/venues/acl27/scripts/init_author_gate.py"
TEMPLATE = ROOT / "paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_WORKSHEET.md"
FILLING_GUIDE = ROOT / "paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md"
UPLOAD_RUNBOOK = ROOT / "paper/venues/acl27/OPENREVIEW_UPLOAD_RUNBOOK.md"


def load_module():
    assert SCRIPT.exists(), "ACL author-gate initializer is missing"
    spec = importlib.util.spec_from_file_location("acl_author_gate_init", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_init_author_gate_creates_private_copy_without_printing_values(
    tmp_path: Path,
) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"

    report = module.init_author_gate(
        paper_root=paper_root,
        template_path=TEMPLATE,
        check_git=False,
    )

    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    assert worksheet.exists()
    assert worksheet.read_text(encoding="utf-8") == TEMPLATE.read_text(
        encoding="utf-8"
    )
    assert report["created"] is True
    assert report["private_worksheet"] == (
        "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    )
    assert report["git_ignored"] is None
    assert "TODO: EACL" not in str(report)


def test_init_author_gate_refuses_to_overwrite_existing_private_copy(
    tmp_path: Path,
) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    worksheet.parent.mkdir(parents=True)
    worksheet.write_text("private local value\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        module.init_author_gate(
            paper_root=paper_root,
            template_path=TEMPLATE,
            check_git=False,
        )

    assert worksheet.read_text(encoding="utf-8") == "private local value\n"


def test_current_author_handoff_docs_prefer_initializer_over_manual_copy() -> None:
    for path in (TEMPLATE, FILLING_GUIDE, UPLOAD_RUNBOOK):
        text = path.read_text(encoding="utf-8")
        assert "python paper/venues/acl27/scripts/init_author_gate.py" in text
        assert "cp paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_WORKSHEET.md" not in text
