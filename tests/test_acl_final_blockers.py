import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/venues/acl27/scripts/report_final_blockers.py"


def load_module():
    assert SCRIPT.exists(), "ACL final blocker reporter is missing"
    spec = importlib.util.spec_from_file_location("acl_final_blockers", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_repo_reports_human_blockers_without_private_values() -> None:
    module = load_module()

    report = module.build_final_blocker_report(ROOT / "paper", repo_root=ROOT)

    assert report["ok"] is True
    assert report["upload_ready"] is False
    assert report["status"] == "human_blocked"
    assert "private_author_gate_missing" in report["human_blockers"]
    assert "official_openreview_form_copy_pending" in report["human_blockers"]
    assert "target_route_author_confirmation_pending" in report["human_blockers"]
    assert "python paper/venues/acl27/scripts/check_author_gate.py" in report[
        "required_commands"
    ]
    assert "OPENREVIEW_AUTHOR_GATE_FILLED.local.md" in report["next_actions"][0]
    assert "private filled list" not in str(report)


def test_completed_author_gate_removes_private_author_blocker(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    worksheet.parent.mkdir(parents=True)
    rows = ["| Field | Fill in local copy |", "| --- | --- |"]
    for field in module.author_gate_module().REQUIRED_FIELDS:
        value = "filled"
        if field == "Final author list and order":
            value = "private filled list"
        rows.append(f"| {field} | {value} |")
    worksheet.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = module.build_final_blocker_report(
        paper_root,
        repo_root=tmp_path,
        check_git=False,
        check_repo_evidence=False,
    )

    assert "private_author_gate_missing" not in report["human_blockers"]
    assert "private_author_gate_incomplete" not in report["human_blockers"]
    assert "private filled list" not in str(report)


def test_repo_evidence_gap_is_repo_blocker(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    (paper_root / "venues/acl27").mkdir(parents=True)

    report = module.build_final_blocker_report(
        paper_root,
        repo_root=tmp_path,
        check_git=False,
        check_repo_evidence=True,
    )

    assert report["upload_ready"] is False
    assert report["status"] == "repo_blocked"
    assert "preupload_runner_missing" in report["repo_blockers"]
    assert "integrity_fingerprint_missing_or_stale" in report["repo_blockers"]


def test_openreview_checklist_gap_is_repo_blocker(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    venue_root = paper_root / "venues/acl27"
    venue_root.mkdir(parents=True)
    for name in (
        "OPENREVIEW_METADATA_PACKET.md",
        "FINAL_SUBMISSION_PACKET_CHECKLIST.md",
        "TARGET_LOCK_OPENREVIEW_REHEARSAL.md",
    ):
        (venue_root / name).write_text("placeholder\n", encoding="utf-8")
    (venue_root / "OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md").write_text(
        "TODO: incomplete checklist\n",
        encoding="utf-8",
    )

    report = module.build_final_blocker_report(
        paper_root,
        repo_root=tmp_path,
        check_git=False,
        check_repo_evidence=True,
    )

    assert report["status"] == "repo_blocked"
    assert "openreview_checklist_missing_or_incomplete" in report["repo_blockers"]
