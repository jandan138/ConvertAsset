import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/author_supplemental_wrapper_stages.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("material_effect_supplemental_wrappers", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate_manifest(tmp_path: Path) -> dict:
    clearcoat_mdl = tmp_path / "OmniPBR_ClearCoat_Opacity.mdl"
    clearcoat_mdl.write_text("export material OmniPBR_ClearCoat_Opacity() = material();\n", encoding="utf-8")
    procedural_mdl = tmp_path / "tutorials.mdl"
    procedural_mdl.write_text("export material example_df() = material();\n", encoding="utf-8")
    clearcoat_usd = tmp_path / "material_binding.usda"
    procedural_usd = tmp_path / "tutorials.usda"
    clearcoat_usd.write_text("#usda 1.0\n", encoding="utf-8")
    procedural_usd.write_text("#usda 1.0\n", encoding="utf-8")
    return {
        "schema_version": 1,
        "summary": {"missing_effects": ["clearcoat", "procedural_texture"]},
        "recommendations": [
            {
                "effect": "clearcoat",
                "candidate_id": "isaac_material_library_omnipbr_clearcoat_opacity",
                "source_kind": "official_isaac_sim_material_library_test",
                "source_usd": str(clearcoat_usd),
                "wrapper_required": True,
            },
            {
                "effect": "procedural_texture",
                "candidate_id": "nvidia_mdl_sdk_tutorials_checker_noise",
                "source_kind": "official_nvidia_mdl_sdk_example",
                "source_usd": str(procedural_usd),
                "wrapper_required": True,
            },
        ],
        "candidates": [
            {
                "candidate_id": "isaac_material_library_omnipbr_clearcoat_opacity",
                "source_usd": str(clearcoat_usd),
                "source_kind": "official_isaac_sim_material_library_test",
                "present_effects": ["clearcoat"],
                "matching_missing_effects": ["clearcoat"],
                "mdl_files": [{"path": str(clearcoat_mdl), "exists": True}],
            },
            {
                "candidate_id": "nvidia_mdl_sdk_tutorials_checker_noise",
                "source_usd": str(procedural_usd),
                "source_kind": "official_nvidia_mdl_sdk_example",
                "present_effects": ["procedural_texture"],
                "matching_missing_effects": ["procedural_texture"],
                "mdl_files": [{"path": str(procedural_mdl), "exists": True}],
            },
        ],
    }


def test_author_supplemental_wrappers_writes_bound_repo_stages(tmp_path: Path) -> None:
    module = load_module()
    output_root = tmp_path / "fixtures"

    manifest = module.author_supplemental_wrapper_manifest(
        candidate_manifest(tmp_path),
        output_root=output_root,
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["summary"]["wrapper_stage_count"] == 2
    assert manifest["summary"]["authored_wrapper_stage_count"] == 2
    assert manifest["summary"]["ready_for_baseline_conversion"] is True
    assert manifest["summary"]["blockers"] == ["supplemental_baseline_conversions_not_run"]
    assert [wrapper["effect"] for wrapper in manifest["wrappers"]] == [
        "clearcoat",
        "procedural_texture",
    ]

    clearcoat = manifest["wrappers"][0]
    clearcoat_text = Path(clearcoat["wrapper_stage"]).read_text(encoding="utf-8")
    assert clearcoat["material_path"] == "/World/Looks/OmniPBR_ClearCoat_Opacity"
    assert clearcoat["target_prim_path"] == "/World/ClearcoatTarget"
    assert 'prepend apiSchemas = ["MaterialBindingAPI"]' in clearcoat_text
    assert "rel material:binding = </World/Looks/OmniPBR_ClearCoat_Opacity>" in clearcoat_text
    assert "inputs:enable_clearcoat = 1" in clearcoat_text
    assert "double2 clippingRange = (0.1, 1000)" in clearcoat_text
    assert "subLayers" not in clearcoat_text
    assert len(clearcoat["hash_sha256"]) == 64

    procedural = manifest["wrappers"][1]
    procedural_text = Path(procedural["wrapper_stage"]).read_text(encoding="utf-8")
    assert procedural["material_path"] == "/World/Looks/ProceduralChecker"
    assert procedural["target_prim_path"] == "/World/ProceduralTarget"
    assert 'prepend apiSchemas = ["MaterialBindingAPI"]' in procedural_text
    assert "rel material:binding = </World/Looks/ProceduralChecker>" in procedural_text
    assert 'info:mdl:sourceAsset:subIdentifier = "example_df"' in procedural_text
    assert "inputs:checker_scale = 8" in procedural_text
    assert "double2 clippingRange = (0.1, 1000)" in procedural_text
    assert "subLayers" not in procedural_text


def test_author_supplemental_wrappers_records_blocker_for_missing_candidate(tmp_path: Path) -> None:
    module = load_module()
    data = candidate_manifest(tmp_path)
    data["recommendations"] = data["recommendations"][:1]
    data["candidates"] = data["candidates"][:1]

    manifest = module.author_supplemental_wrapper_manifest(
        data,
        output_root=tmp_path / "fixtures",
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["summary"]["wrapper_stage_count"] == 1
    assert manifest["summary"]["ready_for_baseline_conversion"] is False
    assert "supplemental_missing_recommended_wrapper_specs" in manifest["summary"]["blockers"]
    assert manifest["summary"]["missing_recommended_effects"] == ["procedural_texture"]


def test_cli_writes_manifest_and_stage_files(tmp_path: Path) -> None:
    module = load_module()
    candidate_path = tmp_path / "candidates.json"
    output_manifest = tmp_path / "wrapper_manifest.json"
    fixture_root = tmp_path / "fixture_root"
    candidate_path.write_text(json.dumps(candidate_manifest(tmp_path)), encoding="utf-8")

    exit_code = module.main(
        [
            "--candidate-manifest",
            str(candidate_path),
            "--fixture-root",
            str(fixture_root),
            "--out",
            str(output_manifest),
        ]
    )

    assert exit_code == 0
    written = json.loads(output_manifest.read_text(encoding="utf-8"))
    assert written["summary"]["ready_for_baseline_conversion"] is True
    assert all(Path(wrapper["wrapper_stage"]).is_file() for wrapper in written["wrappers"])
