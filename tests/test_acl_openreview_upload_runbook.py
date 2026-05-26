from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "paper/venues/acl27/OPENREVIEW_UPLOAD_RUNBOOK.md"


def test_openreview_upload_runbook_covers_final_handoff_surface() -> None:
    assert RUNBOOK.exists(), "final OpenReview upload runbook is missing"
    text = RUNBOOK.read_text(encoding="utf-8")

    required_markers = (
        "private_author_gate_missing",
        "private_author_gate_incomplete",
        "target_route_author_confirmation_pending",
        "official_openreview_form_copy_pending",
        "author_runtime_ai_media_approval_pending",
        "OPENREVIEW_AUTHOR_GATE_FILLED.local.md",
        "OPENREVIEW_METADATA_PACKET.md",
        "OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md",
        "python paper/venues/acl27/scripts/init_author_gate.py",
        "python paper/venues/acl27/scripts/prefill_author_gate.py --apply",
        "python paper/venues/acl27/scripts/prefill_author_gate.py --apply --overwrite",
        "python paper/venues/acl27/scripts/check_author_gate.py",
        "python paper/venues/acl27/scripts/run_preupload_gate.py",
        "Do not upload",
    )
    missing = [marker for marker in required_markers if marker not in text]

    assert missing == []
