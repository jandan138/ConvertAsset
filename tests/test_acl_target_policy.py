import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SCRIPT = PAPER / "venues/acl27/scripts/check_target_policy.py"


def load_module():
    assert SCRIPT.exists(), "ACL target-policy checker is missing"
    spec = importlib.util.spec_from_file_location("acl_target_policy", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_target_policy_sources_are_candidate_ready() -> None:
    module = load_module()

    report = module.check_target_policy(PAPER)

    assert report["ok"] is True
    assert report["route_status"] == "acl_arr_candidate"
    assert report["annual_acl_final_ready"] is False
    assert report["eacl_arr_public_route"] is True
    assert report["missing_urls"] == []
    assert report["missing_required_markers"] == []
    assert report["forbidden_final_claim_hits"] == []


def test_annual_acl_final_claim_is_rejected(tmp_path: Path) -> None:
    module = load_module()
    venue_root = tmp_path / "venues/acl27"
    venue_root.mkdir(parents=True)
    source_audit = PAPER / "venues/acl27/TARGET_CALL_POLICY_AUDIT.md"
    source_lock = PAPER / "venues/acl27/TARGET_LOCK_OPENREVIEW_REHEARSAL.md"
    (venue_root / "TARGET_CALL_POLICY_AUDIT.md").write_text(
        source_audit.read_text(encoding="utf-8")
        + "\nThis packet is Annual ACL 2027 final-ready.\n",
        encoding="utf-8",
    )
    (venue_root / "TARGET_LOCK_OPENREVIEW_REHEARSAL.md").write_text(
        source_lock.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    report = module.check_target_policy(tmp_path)

    assert report["ok"] is False
    assert any("Annual ACL 2027 final-ready" in hit for hit in report["forbidden_final_claim_hits"])


def test_missing_eacl_deadline_marker_is_rejected(tmp_path: Path) -> None:
    module = load_module()
    venue_root = tmp_path / "venues/acl27"
    venue_root.mkdir(parents=True)
    for name in ("TARGET_CALL_POLICY_AUDIT.md", "TARGET_LOCK_OPENREVIEW_REHEARSAL.md"):
        text = (PAPER / "venues/acl27" / name).read_text(encoding="utf-8")
        text = text.replace("August 3, 2026", "DATE REMOVED")
        (venue_root / name).write_text(text, encoding="utf-8")

    report = module.check_target_policy(tmp_path)

    assert report["ok"] is False
    assert "August 3, 2026" in report["missing_required_markers"]


def test_missing_acl2027_branding_resolution_marker_is_rejected(
    tmp_path: Path,
) -> None:
    module = load_module()
    venue_root = tmp_path / "venues/acl27"
    venue_root.mkdir(parents=True)
    for name in ("TARGET_CALL_POLICY_AUDIT.md", "TARGET_LOCK_OPENREVIEW_REHEARSAL.md"):
        text = (PAPER / "venues/acl27" / name).read_text(encoding="utf-8")
        text = text.replace("2027 ACL Conference Branding", "BRANDING REMOVED")
        (venue_root / name).write_text(text, encoding="utf-8")

    report = module.check_target_policy(tmp_path)

    assert report["ok"] is False
    assert "2027 ACL Conference Branding" in report["missing_required_markers"]
