import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SCRIPT = PAPER / "venues/acl27/scripts/check_openreview_checklist.py"


def load_module():
    assert SCRIPT.exists(), "ACL OpenReview checklist checker is missing"
    spec = importlib.util.spec_from_file_location("acl_openreview_checklist", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_openreview_checklist_is_copy_ready_for_current_packet() -> None:
    module = load_module()

    report = module.check_openreview_checklist(PAPER)

    assert report["ok"] is True
    assert report["question_count"] == 17
    assert report["missing_questions"] == []
    assert report["placeholder_hits"] == []
    assert report["bare_answer_questions"] == []
    assert report["missing_policy_inputs"] == []
    assert report["ai_disclosure_present"] is True
    assert report["current_pdf_anchors_present"] is True


def test_bare_yes_no_answer_is_rejected(tmp_path: Path) -> None:
    module = load_module()
    venue_root = tmp_path / "venues/acl27"
    venue_root.mkdir(parents=True)
    source = PAPER / "venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md"
    text = source.read_text(encoding="utf-8")
    text = text.replace(
        "Yes. See `Limitations`, page 8. The section states that the evidence is\n"
        "narrow, separates the 15-pair clean pilot from the frozen 30-pair stress set,\n"
        "marks selected videos as qualitative only, limits the 99-episode InternNav\n"
        "evidence to three official KuJiaLe scenes, and forbids promotion to broad\n"
        "InteriorNav, R2R/MP3D, manipulation, or all-GRScenes robustness.",
        "Yes.",
        1,
    )
    (venue_root / "OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md").write_text(
        text,
        encoding="utf-8",
    )

    report = module.check_openreview_checklist(tmp_path)

    assert report["ok"] is False
    assert "A1. Did you discuss the limitations of your work?" in report[
        "bare_answer_questions"
    ]


def test_placeholder_text_is_rejected(tmp_path: Path) -> None:
    module = load_module()
    venue_root = tmp_path / "venues/acl27"
    venue_root.mkdir(parents=True)
    source = PAPER / "venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md"
    text = source.read_text(encoding="utf-8") + "\nTODO: fill official form.\n"
    (venue_root / "OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md").write_text(
        text,
        encoding="utf-8",
    )

    report = module.check_openreview_checklist(tmp_path)

    assert report["ok"] is False
    assert any("TODO" in hit for hit in report["placeholder_hits"])
