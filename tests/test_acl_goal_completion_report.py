import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/venues/acl27/scripts/report_goal_completion.py"


def load_module():
    assert SCRIPT.exists(), "ACL goal completion reporter is missing"
    spec = importlib.util.spec_from_file_location("acl_goal_completion", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_repo_reports_static_candidate_ready_but_not_complete() -> None:
    module = load_module()

    report = module.build_goal_completion_report(ROOT / "paper", repo_root=ROOT)

    assert report["ok"] is True
    assert report["status"] == "candidate_ready_human_blocked"
    assert report["repo_static_ready"] is True
    assert report["candidate_ready_for_human_gate"] is True
    assert report["final_goal_complete"] is False
    assert report["fresh_preupload_gate_required_for_completion"] is True
    assert report["final_blockers"]["repo_blockers"] == []
    assert "private_author_gate_missing" in report["final_blockers"][
        "human_blockers"
    ]
    assert "python paper/venues/acl27/scripts/init_author_gate.py" in report[
        "required_commands"
    ]
    assert "python paper/venues/acl27/scripts/run_preupload_gate.py" in report[
        "required_commands"
    ]
    assert "private filled list" not in str(report)

    requirements = {item["id"]: item for item in report["requirements"]}
    assert requirements["claim_boundaries"]["status"] == "satisfied"
    assert requirements["evidence_numbers"]["status"] == "satisfied"
    assert requirements["citation_inventory"]["status"] == "satisfied"
    assert requirements["openreview_copy_sources"]["status"] == "satisfied"
    assert requirements["target_policy"]["status"] == "satisfied"
    assert requirements["integrity_fingerprint"]["status"] == "satisfied"
    assert requirements["final_upload_clearance"]["status"] == "human_blocked"


def test_repo_requirement_failure_blocks_static_readiness(tmp_path: Path) -> None:
    module = load_module()

    report = module.build_goal_completion_report(
        tmp_path / "paper",
        repo_root=tmp_path,
        check_git=False,
        check_repo_evidence=False,
    )

    assert report["status"] == "repo_blocked"
    assert report["repo_static_ready"] is False
    assert report["candidate_ready_for_human_gate"] is False
    assert "claim_boundaries" in report["repo_requirement_failures"]
