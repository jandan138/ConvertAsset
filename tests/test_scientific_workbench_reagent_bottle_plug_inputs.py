from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts/build_scientific_workbench_reagent_bottle_plug_inputs.py"
ARCHIVE = (
    ROOT.parent
    / "scenario-forge/external_artifacts/incoming/manual_glassware_v1.tar.gz"
)
SIMREADY_MEMBER = "manual_glassware_v1/simready/reagent_bottle_plug_45_40.usdc"
SIMREADY_SHA256 = "ea6f4b5f13f7f55c6c8bb53073f9afde8e6a6f1131afffffda462d1e8b3ce612"
SOURCE_MEMBER = "manual_glassware_v1/source_usd/reagent_bottle_plug_45_40_source.usdc"
SOURCE_SHA256 = "7d419bc7669a49991b56de09607188b694ff1cf0b5a7fac12e4955989c577f1c"


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "reagent_bottle_plug_inputs", BUILDER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plug_inputs_preserve_the_matched_simready_source(tmp_path: Path) -> None:
    builder = _load_builder()
    results = builder.build_inputs(archive=ARCHIVE, out=tmp_path)
    paths = results["reagent_bottle_plug_45_40"]
    assert set(paths) == {
        "source",
        "source_dependency",
        "interaction",
        "physics",
        "provenance",
    }

    with tarfile.open(ARCHIVE, "r:gz") as bundle:
        simready = bundle.extractfile(SIMREADY_MEMBER)
        source = bundle.extractfile(SOURCE_MEMBER)
        assert simready is not None
        assert source is not None
        assert paths["source"].read_bytes() == simready.read()
        assert paths["source_dependency"].read_bytes() == source.read()

    assert builder._sha(paths["source"]) == SIMREADY_SHA256
    assert builder._sha(paths["source_dependency"]) == SOURCE_SHA256
    assert paths["source_dependency"].parent.name == "source_usd"

    provenance = json.loads(paths["provenance"].read_text(encoding="utf-8"))
    assert provenance["archive_member"] == SIMREADY_MEMBER
    assert provenance["source_dependency_member"] == SOURCE_MEMBER
    assert provenance["source_modified"] is False
    assert provenance["visual_material_policy"] == "preserve_original_simready"
    assert provenance["matched_vessel"] == "reagent_bottle_90x55"

    interaction = json.loads(paths["interaction"].read_text(encoding="utf-8"))
    assert interaction["schema_version"] == "aan.object_interaction_profile.v2"
    assert interaction["asset_entry_prim"] == "/ObjectRoot"
    assert interaction["open_top"]["required"] is False
    assert interaction["required_named_frames"] == [
        "support",
        "joint_tip",
        "joint_seat",
        "grasp",
    ]
    assert [item["relative_path"] for item in interaction["colliders"]] == [
        "Model/COL_ReagentBottlePlug_Stem/COL_ReagentBottlePlug_Stem_Mesh",
        "Model/COL_ReagentBottlePlug_Cap/Cylinder_001",
    ]
    assert all(item["mode"] == "preserve" for item in interaction["colliders"])
    assert interaction["source_binding"]["sha256"] == SIMREADY_SHA256
    assert interaction["named_frames"]["joint_seat"]["translation_body_local_usd"] == [
        0.0,
        0.0,
        0.04,
    ]

    physics = json.loads(paths["physics"].read_text(encoding="utf-8"))
    mass = physics["scope_rules"][0]["body_rules"][0]["mass_properties"]
    assert mass["mass_kg"] == 0.085
    assert physics["source_binding"]["sha256"] == SIMREADY_SHA256
