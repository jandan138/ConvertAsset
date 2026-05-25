import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_effect_candidates.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("material_effect_supplemental_candidates", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_supplemental_candidate_manifest_recommends_missing_effect_sources(tmp_path: Path) -> None:
    module = load_module()
    clearcoat_mdl = tmp_path / "clearcoat.mdl"
    clearcoat_mdl.write_text(
        "export material clear() = material(surface: material_surface(scattering: clearcoat));\n"
        "float clearcoat_weight = 1.0f;\n",
        encoding="utf-8",
    )
    procedural_mdl = tmp_path / "procedural.mdl"
    procedural_mdl.write_text(
        "export color color_checker(float2 uv) { return checker(uv, 0.5, 0.0).tint; }\n"
        "base::perlin_noise_texture(noise_levels: 4);\n",
        encoding="utf-8",
    )
    clearcoat_usd = tmp_path / "clearcoat.usda"
    procedural_usd = tmp_path / "procedural.usda"
    clearcoat_usd.write_text("#usda 1.0\n", encoding="utf-8")
    procedural_usd.write_text("#usda 1.0\n", encoding="utf-8")
    existing_effect_manifest = {
        "summary": {
            "effect_gaps": ["clearcoat", "procedural_texture"],
            "effect_counts": {
                "clearcoat": 0,
                "opacity_transparency": 3,
                "emission": 3,
                "procedural_texture": 0,
                "normal_bump": 3,
                "displacement_height": 3,
            },
        }
    }
    candidates = [
        {
            "candidate_id": "clearcoat_candidate",
            "source_rank": 10,
            "source_kind": "official_isaac_sim_material_library_test",
            "source_usd": str(clearcoat_usd),
            "mdl_paths": [str(clearcoat_mdl)],
            "wrapper_required": True,
        },
        {
            "candidate_id": "procedural_candidate",
            "source_rank": 20,
            "source_kind": "official_nvidia_mdl_sdk_example",
            "source_usd": str(procedural_usd),
            "mdl_paths": [str(procedural_mdl)],
            "wrapper_required": True,
        },
    ]

    manifest = module.build_supplemental_candidate_manifest(
        existing_effect_manifest,
        candidates,
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["summary"]["missing_effects"] == ["clearcoat", "procedural_texture"]
    assert manifest["summary"]["covered_missing_effects"] == ["clearcoat", "procedural_texture"]
    assert manifest["summary"]["remaining_missing_effects"] == []
    assert manifest["summary"]["ready_for_fixture_authoring"] is True
    assert manifest["summary"]["ready_for_baseline_conversion"] is False
    assert "supplemental_wrapper_scenes_not_authored" in manifest["summary"]["blockers"]
    assert {
        recommendation["effect"]: recommendation["candidate_id"]
        for recommendation in manifest["recommendations"]
    } == {
        "clearcoat": "clearcoat_candidate",
        "procedural_texture": "procedural_candidate",
    }
    clearcoat = manifest["candidates"][0]
    assert clearcoat["present_effects"] == ["clearcoat"]
    assert clearcoat["matching_missing_effects"] == ["clearcoat"]
    assert clearcoat["source_usd_exists"] is True
    assert clearcoat["mdl_files"][0]["exists"] is True
    assert len(clearcoat["mdl_files"][0]["hash_sha256"]) == 64


def test_build_supplemental_candidate_manifest_reports_uncovered_gap(tmp_path: Path) -> None:
    module = load_module()
    clearcoat_mdl = tmp_path / "clearcoat.mdl"
    clearcoat_mdl.write_text("float clearcoat_weight = 1.0f;\n", encoding="utf-8")
    clearcoat_usd = tmp_path / "clearcoat.usda"
    clearcoat_usd.write_text("#usda 1.0\n", encoding="utf-8")
    existing_effect_manifest = {
        "summary": {"effect_gaps": ["clearcoat", "procedural_texture"]}
    }

    manifest = module.build_supplemental_candidate_manifest(
        existing_effect_manifest,
        [
            {
                "candidate_id": "clearcoat_candidate",
                "source_rank": 10,
                "source_kind": "official_isaac_sim_material_library_test",
                "source_usd": str(clearcoat_usd),
                "mdl_paths": [str(clearcoat_mdl)],
                "wrapper_required": True,
            }
        ],
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["summary"]["covered_missing_effects"] == ["clearcoat"]
    assert manifest["summary"]["remaining_missing_effects"] == ["procedural_texture"]
    assert manifest["summary"]["ready_for_fixture_authoring"] is False
    assert "missing_effects_without_candidate_sources" in manifest["summary"]["blockers"]


def test_default_candidate_specs_prefer_official_local_sources() -> None:
    module = load_module()
    specs = module.default_candidate_specs()

    assert specs[0]["candidate_id"].startswith("isaac_material_library")
    assert specs[0]["source_rank"] < specs[1]["source_rank"]
    assert "omni.kit.material.library" in specs[0]["source_usd"]
    assert "omni.mdl.usd_converter" in specs[1]["source_usd"]
