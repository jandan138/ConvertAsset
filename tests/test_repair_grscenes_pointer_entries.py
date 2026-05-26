from pathlib import Path

from scripts.repair_grscenes_pointer_entries import repair_pointer_entries


def test_repair_pointer_entries_dry_run_reports_without_writing(tmp_path):
    target = tmp_path / "Materials"
    target.mkdir()
    model = tmp_path / "models" / "layout" / "asset"
    model.mkdir(parents=True)
    pointer = model / "Materials"
    pointer.write_text("../../../Materials", encoding="utf-8")

    summary = repair_pointer_entries(tmp_path, apply=False, report_path=None)

    assert summary["applied"] is False
    assert summary["candidate_files"] == 1
    assert summary["repaired_count"] == 0
    assert summary["planned_count"] == 1
    assert pointer.is_file()
    assert not pointer.is_symlink()


def test_repair_pointer_entries_apply_replaces_only_scratch_entry(tmp_path):
    target = tmp_path / "Materials"
    target.mkdir()
    model = tmp_path / "models" / "layout" / "asset"
    model.mkdir(parents=True)
    pointer = model / "Materials"
    source_hardlink = tmp_path / "source_pointer_copy"
    pointer.write_text("../../../Materials", encoding="utf-8")
    source_hardlink.hardlink_to(pointer)

    summary = repair_pointer_entries(tmp_path, apply=True, report_path=None)

    assert summary["applied"] is True
    assert summary["candidate_files"] == 1
    assert summary["repaired_count"] == 1
    assert pointer.is_symlink()
    assert pointer.readlink() == Path("../../../Materials")
    assert (pointer.parent / pointer.readlink()).resolve() == target.resolve()
    assert source_hardlink.is_file()
    assert not source_hardlink.is_symlink()
    assert source_hardlink.read_text(encoding="utf-8") == "../../../Materials"


def test_repair_pointer_entries_rejects_escape_target(tmp_path):
    model = tmp_path / "models" / "layout" / "asset"
    model.mkdir(parents=True)
    pointer = model / "Materials"
    pointer.write_text("../../../../../../outside", encoding="utf-8")

    summary = repair_pointer_entries(tmp_path, apply=True, report_path=None)

    assert summary["candidate_files"] == 1
    assert summary["repaired_count"] == 0
    assert summary["errors"]
    assert pointer.is_file()


def test_create_missing_materials_symlink_from_instance_reference(tmp_path):
    (tmp_path / "Materials").mkdir()
    model = tmp_path / "models" / "object" / "others" / "tray" / "abc"
    model.mkdir(parents=True)
    (model / "instance.usd").write_bytes(b'asset info:mdl:sourceAsset = @./Materials/Num123.mdl@')

    summary = repair_pointer_entries(
        tmp_path,
        apply=True,
        report_path=None,
        create_missing_materials=True,
    )

    pointer = model / "Materials"
    assert summary["missing_materials_candidates"] == 1
    assert summary["created_missing_materials_count"] == 1
    assert pointer.is_symlink()
    assert (pointer.parent / pointer.readlink()).resolve() == (tmp_path / "Materials").resolve()


def test_missing_materials_symlink_is_not_created_without_local_reference(tmp_path):
    (tmp_path / "Materials").mkdir()
    model = tmp_path / "models" / "object" / "others" / "tray" / "abc"
    model.mkdir(parents=True)
    (model / "instance.usd").write_bytes(b"no local material reference")

    summary = repair_pointer_entries(
        tmp_path,
        apply=True,
        report_path=None,
        create_missing_materials=True,
    )

    assert summary["missing_materials_candidates"] == 0
    assert not (model / "Materials").exists()


def test_all_instance_dirs_policy_creates_missing_materials_symlink(tmp_path):
    (tmp_path / "Materials").mkdir()
    model = tmp_path / "models" / "object" / "others" / "tray" / "abc"
    model.mkdir(parents=True)
    (model / "instance.usd").write_bytes(b"binary-usd-like-content")

    summary = repair_pointer_entries(
        tmp_path,
        apply=True,
        report_path=None,
        create_missing_materials=True,
        missing_materials_policy="all_instance_dirs",
    )

    pointer = model / "Materials"
    assert summary["missing_materials_candidates"] == 1
    assert summary["created_missing_materials_count"] == 1
    assert pointer.is_symlink()
    assert (pointer.parent / pointer.readlink()).resolve() == (tmp_path / "Materials").resolve()


def test_instance_paths_limit_missing_materials_scan(tmp_path):
    (tmp_path / "Materials").mkdir()
    selected = tmp_path / "models" / "object" / "tray" / "selected"
    ignored = tmp_path / "models" / "object" / "tray" / "ignored"
    selected.mkdir(parents=True)
    ignored.mkdir(parents=True)
    selected_instance = selected / "instance.usd"
    selected_instance.write_bytes(b"binary-usd-like-content")
    (ignored / "instance.usd").write_bytes(b"binary-usd-like-content")

    summary = repair_pointer_entries(
        tmp_path,
        apply=True,
        report_path=None,
        create_missing_materials=True,
        missing_materials_policy="all_instance_dirs",
        instance_paths=[selected_instance],
    )

    assert summary["missing_materials_candidates"] == 1
    assert (selected / "Materials").is_symlink()
    assert not (ignored / "Materials").exists()


def test_can_skip_existing_pointer_scan_for_instance_list_only_repair(tmp_path):
    (tmp_path / "Materials").mkdir()
    pointer_model = tmp_path / "models" / "layout" / "asset"
    pointer_model.mkdir(parents=True)
    pointer = pointer_model / "Materials"
    pointer.write_text("../../../Materials", encoding="utf-8")

    selected = tmp_path / "models" / "object" / "tray" / "selected"
    selected.mkdir(parents=True)
    selected_instance = selected / "instance.usd"
    selected_instance.write_bytes(b"binary-usd-like-content")

    summary = repair_pointer_entries(
        tmp_path,
        apply=True,
        report_path=None,
        create_missing_materials=True,
        missing_materials_policy="all_instance_dirs",
        instance_paths=[selected_instance],
        repair_existing_pointers=False,
    )

    assert summary["candidate_files"] == 0
    assert summary["repaired_count"] == 0
    assert pointer.is_file()
    assert (selected / "Materials").is_symlink()
