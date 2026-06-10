import importlib.util
import hashlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/venues/acl27/scripts/run_preupload_gate.py"


def load_module():
    assert SCRIPT.exists(), "ACL pre-upload gate runner is missing"
    spec = importlib.util.spec_from_file_location("acl_preupload_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preupload_plan_orders_checks_before_staging() -> None:
    module = load_module()

    plan = module.build_preupload_plan(ROOT)
    step_ids = [step["id"] for step in plan]
    focused_pytest_step = next(step for step in plan if step["id"] == "focused_pytest")

    assert step_ids == [
        "claim_boundaries",
        "target_policy",
        "metadata_consistency",
        "openreview_checklist",
        "citation_inventory",
        "evidence_numbers",
        "integrity_fingerprint",
        "final_blocker_report",
        "goal_completion_report",
        "focused_pytest",
        "clean_acl_build",
        "latex_log_scan",
        "stage_packet",
        "packet_inventory",
        "packet_checksum_sidecar",
        "packet_private_scan",
        "packet_acknowledgment_scan",
        "pdfinfo",
        "pdf_profile",
        "pdftotext_sections",
    ]
    assert step_ids.index("claim_boundaries") < step_ids.index("stage_packet")
    assert step_ids.index("target_policy") < step_ids.index("stage_packet")
    assert step_ids.index("metadata_consistency") < step_ids.index("stage_packet")
    assert step_ids.index("openreview_checklist") < step_ids.index("stage_packet")
    assert step_ids.index("citation_inventory") < step_ids.index("stage_packet")
    assert step_ids.index("evidence_numbers") < step_ids.index("stage_packet")
    assert step_ids.index("integrity_fingerprint") < step_ids.index("stage_packet")
    assert step_ids.index("goal_completion_report") < step_ids.index("stage_packet")
    assert "tests/test_acl_citation_inventory.py" in focused_pytest_step["command"]
    assert "tests/test_acl_target_policy.py" in focused_pytest_step["command"]
    assert "tests/test_acl_integrity_fingerprint.py" in focused_pytest_step["command"]
    assert "tests/test_acl_final_blockers.py" in focused_pytest_step["command"]
    assert "tests/test_acl_openreview_checklist.py" in focused_pytest_step["command"]
    assert "tests/test_acl_author_gate.py" in focused_pytest_step["command"]
    assert "tests/test_acl_author_gate_init.py" in focused_pytest_step["command"]
    assert "tests/test_acl_openreview_upload_runbook.py" in focused_pytest_step[
        "command"
    ]
    assert "tests/test_acl_goal_completion_report.py" in focused_pytest_step[
        "command"
    ]
    assert "tests/test_acl_author_gate_prefill.py" in focused_pytest_step["command"]
    assert "tests/test_render_scene_evidence_figure.py" in focused_pytest_step[
        "command"
    ]


def test_packet_inventory_rejects_extra_files(tmp_path: Path) -> None:
    module = load_module()
    packet_root = tmp_path / "packet"
    for relative in module.EXPECTED_PACKET_FILES:
        path = packet_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")
    extra = packet_root / "extra.txt"
    extra.write_text("not allowed", encoding="utf-8")

    with pytest.raises(ValueError, match="unexpected"):
        module.check_packet_inventory(packet_root)


def test_packet_checksum_sidecar_must_match_expected_files(tmp_path: Path) -> None:
    module = load_module()
    packet_root = tmp_path / "packet"
    checksums = {}
    for relative in module.EXPECTED_PACKET_FILES:
        path = packet_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"content for {relative}", encoding="utf-8")
        checksums[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    checksum_path = packet_root.with_name(packet_root.name + ".sha256")
    checksum_path.write_text(
        "\n".join(f"{checksums[relative]}  {relative}" for relative in sorted(checksums))
        + "\n",
        encoding="utf-8",
    )

    module.check_packet_checksum_sidecar(packet_root)

    checksum_path.write_text(
        "\n".join(
            f"{'0' * 64 if relative == 'main.pdf' else checksums[relative]}  {relative}"
            for relative in sorted(checksums)
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="checksum mismatch"):
        module.check_packet_checksum_sidecar(packet_root)


def test_text_scan_detects_private_tokens(tmp_path: Path) -> None:
    module = load_module()
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    leaked = packet_root / "leak.md"
    leaked.write_text("local path /cpfs/user/example leaked", encoding="utf-8")

    with pytest.raises(ValueError, match="/cpfs"):
        module.scan_text_forbidden_tokens(
            packet_root,
            tokens=module.PRIVATE_TOKENS,
            label="private token",
        )


def test_pdf_profile_accepts_current_acl_candidate_shape() -> None:
    module = load_module()
    pdfinfo_output = """
Pages:           12
Page size:       595.276 x 841.89 pts (A4)
PDF version:     1.5
"""

    profile = module.parse_pdfinfo_output(pdfinfo_output)

    assert profile["pages"] == 12
    assert profile["page_size_label"] == "A4"
    module.validate_pdf_profile(profile)


def test_pdf_profile_rejects_unreviewed_page_growth() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="page count"):
        module.validate_pdf_profile(
            {
                "pages": module.PDF_MAX_TOTAL_PAGES + 1,
                "page_size_label": "A4",
                "pdf_version": "1.5",
            }
        )


def test_pdf_text_markers_must_preserve_section_order() -> None:
    module = load_module()
    out_of_order_text = "\n".join(
        [
            "Material Conversion as a Controlled Perturbation",
            "Anonymous ACL submission",
            "Figure 3:",
            "Limitations",
            "Ethical Considerations",
            "Figure 4:",
            "References",
        ]
    )

    with pytest.raises(ValueError, match="out of order"):
        module.validate_pdf_text_markers(out_of_order_text)


def test_pdf_text_markers_reject_main_content_spill_before_limitations() -> None:
    module = load_module()
    text = "\f".join(
        [
            "Material Conversion as a Controlled Perturbation\n"
            "Anonymous ACL submission\n"
            "Figure 3:"
        ]
        * 8
        + [
            "Conclusion text still running before Limitations\n"
            "Limitations\nFigure 4:\nEthical Considerations\nReferences"
        ]
    )

    with pytest.raises(ValueError, match="main content appears before Limitations"):
        module.validate_pdf_text_markers(text)


def test_pdf_text_markers_allow_conclusion_before_limitations_on_page_8() -> None:
    module = load_module()
    text = "\f".join(
        ["Material Conversion as a Controlled Perturbation\nFigure 3:"] * 7
        + [
            "Conclusion\n"
            "This paper treats synthetic-scene material conversion as a controlled perturbation.\n"
            "Limitations\n"
            "Figure 4: Selected qualitative InternNav rollout panel\n"
            "Ethical Considerations\n"
            "References\n"
            "Anonymous ACL submission"
        ]
    )

    module.validate_pdf_text_markers(text)


def test_pdf_text_markers_reject_internnav_figure_after_references() -> None:
    module = load_module()
    text = "\f".join(
        ["Material Conversion as a Controlled Perturbation\nFigure 3:"] * 8
        + [
            "595\n\nLimitations\nEthical Considerations\nReferences\n"
            "Figure 4:\n"
            "Anonymous ACL submission"
        ]
    )

    with pytest.raises(ValueError, match="out of order"):
        module.validate_pdf_text_markers(text)


def test_pdf_text_markers_require_internnav_figure_before_ethics_and_refs() -> None:
    module = load_module()
    text = "\f".join(
        ["Material Conversion as a Controlled Perturbation\nFigure 3:"] * 8
        + [
            "595\n\nLimitations\n"
            "Figure 4: Supplemental qualitative InternNav rollout panel\n"
            "Ethical Considerations\nReferences\n"
            "Anonymous ACL submission"
        ]
    )

    module.validate_pdf_text_markers(text)


def test_pdf_text_markers_allow_wide_internnav_figure_before_limitations() -> None:
    module = load_module()
    text = "\f".join(
        ["Material Conversion as a Controlled Perturbation\nFigure 3:"] * 8
        + [
            "Figure 4: Selected InternNav path panels. These selected official KuJiaLe examples\n"
            "show original/noMDL start and end frames with trajectory overlays.\n"
            "Limitations\n"
            "The evidence base is intentionally narrow.\n"
            "Ethical Considerations\n"
            "The work studies conversion of synthetic 3D assets.\n"
            "References\n"
            "Anonymous ACL submission"
        ]
    )

    module.validate_pdf_text_markers(text)


def test_pdf_text_markers_allow_wide_figure_and_two_column_refs_on_limitations_page() -> None:
    module = load_module()
    text = "\f".join(
        ["Material Conversion as a Controlled Perturbation\nFigure 3:"] * 8
        + [
            "Figure 4: Selected InternNav path panels. These selected official KuJiaLe examples\n"
            "show original/noMDL start and end frames with trajectory overlays.\n"
            "Limitations\n"
            "The evidence base is intentionally narrow.\n"
            "References\n"
            "Peter Anderson et al.\n"
            "Ethical Considerations\n"
            "The work studies conversion of synthetic 3D assets.\n"
            "Anonymous ACL submission"
        ]
    )

    module.validate_pdf_text_markers(text)


def test_pdf_text_markers_allow_two_column_references_extraction_before_figure() -> None:
    module = load_module()
    text = "\f".join(
        ["Material Conversion as a Controlled Perturbation\nFigure 3:"] * 7
        + [
            "Limitations\n"
            "The evidence base is intentionally narrow.\n"
        ]
        + [
            "References\n"
            "Peter Anderson et al.\n"
            "Figure 4: Selected qualitative InternNav rollout panel.\n"
            "Ethical Considerations\n"
            "The work studies conversion of synthetic 3D assets.\n"
            "Anonymous ACL submission"
        ]
    )

    module.validate_pdf_text_markers(text)


def test_pdf_text_markers_reject_float_only_material_page_before_limitations() -> None:
    module = load_module()
    text = "\f".join(
        [
            "Material Conversion as a Controlled Perturbation\n"
            "Anonymous ACL submission\n"
            "Figure 3:"
        ]
        * 7
        + [
            "Table 5: Material-effect scope matrix\n"
            "Table 6: Official KuJiaLe / InteriorAgent scene\n"
        ]
        + ["Limitations\nFigure 4:\nEthical Considerations\nReferences"]
    )

    with pytest.raises(ValueError, match="float-only material table page"):
        module.validate_pdf_text_markers(text)


def test_pdf_text_markers_reject_material_tables_before_early_limitations() -> None:
    module = load_module()
    text = "\f".join(
        [
            "Material Conversion as a Controlled Perturbation\n"
            "Anonymous ACL submission\n"
            "Figure 3:"
        ]
        * 7
        + [
            "Table 5: Material-effect scope matrix\n"
            "Table 6: Official KuJiaLe / InteriorAgent scene\n"
            "Limitations\nFigure 4:\nEthical Considerations\nReferences"
        ]
    )

    with pytest.raises(ValueError, match="main content appears before Limitations"):
        module.validate_pdf_text_markers(text)


def test_pdf_text_markers_allow_material_tables_when_discussion_shares_page() -> None:
    module = load_module()
    text = "\f".join(
        [
            "Material Conversion as a Controlled Perturbation\n"
            "Anonymous ACL submission\n"
            "Figure 3:"
        ]
        * 7
        + [
            "Table 5: Material-effect scope matrix\n"
            "Table 6: Official KuJiaLe / InteriorAgent scene\n"
            "Discussion\n"
            "The contribution is a measurement protocol, not a converter leaderboard.\n"
        ]
        + ["Limitations\nFigure 4:\nEthical Considerations\nReferences"]
    )

    module.validate_pdf_text_markers(text)


def test_acl_main_does_not_force_references_to_a_fresh_page_after_ethics() -> None:
    main_tex = (ROOT / "paper/venues/acl27/main.tex").read_text(encoding="utf-8")
    assert "\\input{./sections/ethical-considerations}\n\n\\bibliography{references}" in main_tex
