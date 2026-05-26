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


def complete_private_rows(module, overrides: dict[str, str] | None = None) -> list[str]:
    values = {
        field: "confirmed"
        for field in module.author_gate_module().REQUIRED_FIELDS
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
    rows.extend(
        f"| {field} | {values[field]} |"
        for field in module.author_gate_module().REQUIRED_FIELDS
    )
    return rows


def test_current_repo_reports_human_blockers_without_private_values() -> None:
    module = load_module()

    report = module.build_final_blocker_report(ROOT / "paper", repo_root=ROOT)

    assert report["ok"] is True
    assert report["upload_ready"] is False
    assert report["status"] == "human_blocked"
    assert "private_author_gate_missing" in report["human_blockers"]
    assert "official_openreview_form_copy_pending" in report["human_blockers"]
    assert "target_route_author_confirmation_pending" in report["human_blockers"]
    assert "python paper/venues/acl27/scripts/init_author_gate.py" in report[
        "required_commands"
    ]
    assert "python paper/venues/acl27/scripts/check_author_gate.py" in report[
        "required_commands"
    ]
    assert "OPENREVIEW_AUTHOR_GATE_FILLED.local.md" in report["next_actions"][0]
    assert "init_author_gate.py" in report["next_actions"][0]
    assert "private filled list" not in str(report)


def test_current_repo_reports_structured_human_handoff_details() -> None:
    module = load_module()

    report = module.build_final_blocker_report(ROOT / "paper", repo_root=ROOT)

    details = report["human_blocker_details"]
    assert set(report["human_blockers"]) == set(details)
    assert "Selected route" in details[
        "target_route_author_confirmation_pending"
    ]["worksheet_fields"]
    assert "OPENREVIEW_METADATA_PACKET.md" in details[
        "official_openreview_form_copy_pending"
    ]["copy_sources"]
    assert "Runtime / compute wording approved" in details[
        "author_runtime_ai_media_approval_pending"
    ]["worksheet_fields"]
    assert "OPENREVIEW_AUTHOR_GATE_FILLED.local.md" in details[
        "private_author_gate_missing"
    ]["required_action"]
    assert "init_author_gate.py" in details[
        "private_author_gate_missing"
    ]["required_action"]
    assert "private filled list" not in str(report)


def test_completed_author_gate_removes_private_author_blocker(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    worksheet.parent.mkdir(parents=True)
    rows = complete_private_rows(
        module,
        {"Final author list and order": "private filled list"},
    )
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


def test_completed_author_gate_can_clear_all_human_blockers(
    tmp_path: Path,
) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    worksheet = paper_root / "venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md"
    worksheet.parent.mkdir(parents=True)
    rows = complete_private_rows(module)
    worksheet.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = module.build_final_blocker_report(
        paper_root,
        repo_root=tmp_path,
        check_git=False,
        check_repo_evidence=False,
    )

    assert report["upload_ready"] is True
    assert report["status"] == "upload_ready"
    assert report["human_blockers"] == []
    assert report["human_blocker_details"] == {}


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


def test_target_policy_gap_is_repo_blocker(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    venue_root = paper_root / "venues/acl27"
    venue_root.mkdir(parents=True)
    for name in (
        "OPENREVIEW_METADATA_PACKET.md",
        "OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md",
        "FINAL_SUBMISSION_PACKET_CHECKLIST.md",
        "TARGET_LOCK_OPENREVIEW_REHEARSAL.md",
    ):
        (venue_root / name).write_text("placeholder\n", encoding="utf-8")
    (venue_root / "TARGET_CALL_POLICY_AUDIT.md").write_text(
        "This packet is Annual ACL 2027 final-ready.\n",
        encoding="utf-8",
    )

    report = module.build_final_blocker_report(
        paper_root,
        repo_root=tmp_path,
        check_git=False,
        check_repo_evidence=True,
    )

    assert report["status"] == "repo_blocked"
    assert "target_policy_missing_or_unsafe" in report["repo_blockers"]
