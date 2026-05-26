import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SCRIPT = PAPER / "venues/acl27/scripts/check_citation_inventory.py"


def load_module():
    assert SCRIPT.exists(), "ACL citation-inventory checker is missing"
    spec = importlib.util.spec_from_file_location("acl_citation_inventory", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_acl_citation_inventory_is_complete() -> None:
    module = load_module()

    report = module.check_citation_inventory(PAPER)

    assert report["ok"] is True
    assert report["cited_key_count"] == 20
    assert report["missing_bib_keys"] == []
    assert report["missing_identifier_keys"] == []
    assert report["missing_webtrail_keys"] == []
    assert report["uncited_webtrail_keys"] == []


def test_missing_bib_identifier_and_webtrail_are_detected(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    section_root = paper_root / "venues/acl27/sections"
    section_root.mkdir(parents=True)
    (paper_root / "shared/sections").mkdir(parents=True)
    (paper_root / "shared/evidence/references").mkdir(parents=True)
    (section_root / "intro.tex").write_text(
        r"Known source \citep{KnownKey}; missing source \cite{MissingKey}.",
        encoding="utf-8",
    )
    (paper_root / "shared/sections/appendix.tex").write_text("", encoding="utf-8")
    (paper_root / "shared/references.bib").write_text(
        "@article{KnownKey,\n"
        "  title = {Known Title},\n"
        "  author = {Example, Ada},\n"
        "  year = {2026}\n"
        "}\n",
        encoding="utf-8",
    )
    (paper_root / "shared/evidence/references/verification_report.md").write_text(
        "## 2026-05-26 ACL WRAPPER WEB-TRAIL ADDENDUM\n\n"
        "| Key | Verdict | Source checked | Confirmed fields / action |\n"
        "|---|---|---|---|\n"
        "| `ExtraKey` | `VERIFIED` | https://example.com | confirmed. |\n\n"
        "## 2026-05-22 ADDENDUM\n",
        encoding="utf-8",
    )

    report = module.check_citation_inventory(paper_root)

    assert report["ok"] is False
    assert report["missing_bib_keys"] == ["MissingKey"]
    assert report["missing_identifier_keys"] == ["KnownKey"]
    assert report["missing_webtrail_keys"] == ["KnownKey", "MissingKey"]
    assert report["uncited_webtrail_keys"] == ["ExtraKey"]


def test_comment_only_citations_are_ignored(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    section_root = paper_root / "venues/acl27/sections"
    section_root.mkdir(parents=True)
    (paper_root / "shared/sections").mkdir(parents=True)
    (paper_root / "shared/evidence/references").mkdir(parents=True)
    (section_root / "intro.tex").write_text(
        "% ignored \\cite{CommentOnly}\nReal citation \\cite{RealKey}.",
        encoding="utf-8",
    )
    (paper_root / "shared/sections/appendix.tex").write_text("", encoding="utf-8")
    (paper_root / "shared/references.bib").write_text(
        "@article{RealKey,\n"
        "  title = {Real Title},\n"
        "  author = {Example, Ada},\n"
        "  year = {2026},\n"
        "  url = {https://example.com/real}\n"
        "}\n",
        encoding="utf-8",
    )
    (paper_root / "shared/evidence/references/verification_report.md").write_text(
        "## 2026-05-26 ACL WRAPPER WEB-TRAIL ADDENDUM\n\n"
        "| Key | Verdict | Source checked | Confirmed fields / action |\n"
        "|---|---|---|---|\n"
        "| `RealKey` | `VERIFIED` | https://example.com/real | confirmed. |\n\n"
        "## 2026-05-22 ADDENDUM\n",
        encoding="utf-8",
    )

    report = module.check_citation_inventory(paper_root)

    assert report["ok"] is True
    assert report["cited_keys"] == ["RealKey"]
