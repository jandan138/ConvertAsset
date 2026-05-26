import json

from scripts.fix_mdl_absolute_imports import process_roots, repair_text, should_process_mdl


def test_repair_text_rewrites_koopbr_imports():
    text = (
        "import ::state::normal;\n"
        "import ::KooPbr::KooMtl;\n"
        "import ::KooPbr_maps::KooPbr_bitmap;\n"
        "import ::tex::gamma_mode;\n"
    )

    repaired, replacements = repair_text(text)

    assert "import ::state::normal;" in repaired
    assert "using .::KooPbr import KooMtl;" in repaired
    assert "using .::KooPbr_maps import KooPbr_bitmap;" in repaired
    assert "import ::tex::gamma_mode;" in repaired
    assert "import ::KooPbr::KooMtl;" not in repaired
    assert "import ::KooPbr_maps::KooPbr_bitmap;" not in repaired
    assert replacements == 2


def test_repair_text_keeps_line_endings_and_is_idempotent():
    text = "using .::KooPbr import KooMtl;\r\n"

    repaired, replacements = repair_text(text)
    repaired_again, second_replacements = repair_text(repaired)

    assert repaired == text
    assert replacements == 0
    assert repaired_again == text
    assert second_replacements == 0


def test_should_process_only_generated_material_instances():
    assert should_process_mdl("MI_6576cd34ade22a0001b5739d.mdl")
    assert should_process_mdl("abcdef0123456789abcdef0123456789.mdl")
    assert not should_process_mdl("KooPbr.mdl")
    assert not should_process_mdl("KooPbr_maps.mdl")
    assert not should_process_mdl("Num12.mdl")
    assert not should_process_mdl("OmniUe4Base.mdl")


def test_process_roots_dry_run_reports_without_writing(tmp_path):
    mdl = tmp_path / "MI_test.mdl"
    original = "import ::KooPbr::KooMtl;\n"
    mdl.write_text(original, encoding="utf-8")
    report = tmp_path / "report.json"

    summary = process_roots([tmp_path], apply=False, follow_symlinks=False, report_path=report)

    assert summary["applied"] is False
    assert summary["candidate_files"] == 1
    assert summary["changed_files"] == 1
    assert summary["total_replacements"] == 1
    assert mdl.read_text(encoding="utf-8") == original
    written = json.loads(report.read_text(encoding="utf-8"))
    assert written["files"][0]["replacements"] == 1


def test_process_roots_apply_rewrites_and_skips_libraries(tmp_path):
    material = tmp_path / "MI_test.mdl"
    library = tmp_path / "KooPbr.mdl"
    material.write_text("import ::KooPbr_maps::KooPbr_bitmap;\n", encoding="utf-8")
    library.write_text("import ::KooPbr_maps::KooPbr_bitmap;\n", encoding="utf-8")

    summary = process_roots([tmp_path], apply=True, follow_symlinks=False, report_path=None)

    assert summary["applied"] is True
    assert summary["candidate_files"] == 1
    assert summary["changed_files"] == 1
    assert "using .::KooPbr_maps import KooPbr_bitmap;" in material.read_text(encoding="utf-8")
    assert library.read_text(encoding="utf-8") == "import ::KooPbr_maps::KooPbr_bitmap;\n"

