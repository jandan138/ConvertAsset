import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_sample_manifest.py"
)


def load_manifest_module():
    spec = importlib.util.spec_from_file_location("material_effect_sample_manifest", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_detect_material_effects_keeps_opaque_constant_out_of_opacity_group(tmp_path: Path) -> None:
    module = load_manifest_module()
    mdl_path = tmp_path / "opaque.mdl"
    mdl_path.write_text(
        """
mdl 1.6;
export material Opaque(*) = KooPbr::KooMtl(
    diffuse: color(0.1f, 0.2f, 0.3f),
    texmap_bump: state::normal(),
    opacity: 1.f,
    self_illumination: color(0.f, 0.f, 0.f));
""",
        encoding="utf-8",
    )

    effects = module.detect_material_effects([mdl_path])

    assert effects["normal_bump"]["present"] is True
    assert effects["opacity_transparency"]["present"] is False
    assert effects["emission"]["present"] is False


def test_detect_material_effects_finds_translucent_emissive_displacement_and_procedural(
    tmp_path: Path,
) -> None:
    module = load_manifest_module()
    mdl_path = tmp_path / "risk.mdl"
    mdl_path.write_text(
        """
mdl 1.6;
uniform texture_2d Normal_Tex = texture_2d("./Textures/normal.png", ::tex::gamma_linear);
float Opacity = 0.5;
float EmissiveIntensity = 2.0;
float3 WorldPositionOffset_mdl = float3(0.0, 0.0, 1.0);
float pattern = noise(float3(0.1, 0.2, 0.3));
export material Risky() = ::OmniUe4Translucent(
    normal: Normal_mdl,
    opacity: Opacity,
    emissive_color: EmissiveColor_mdl,
    displacement: WorldPositionOffset_mdl);
""",
        encoding="utf-8",
    )

    effects = module.detect_material_effects([mdl_path])

    assert effects["normal_bump"]["present"] is True
    assert effects["opacity_transparency"]["present"] is True
    assert effects["emission"]["present"] is True
    assert effects["displacement_height"]["present"] is True
    assert effects["procedural_texture"]["present"] is True


def test_build_effect_sample_manifest_links_stress_pairs_to_material_models(tmp_path: Path) -> None:
    module = load_manifest_module()
    source_root = tmp_path / "source"
    model_root = source_root / "models/object/others/cup/hash_a"
    material_root = source_root / "Materials"
    model_root.mkdir(parents=True)
    material_root.mkdir(parents=True)
    mdl_path = material_root / "cup.mdl"
    mdl_path.write_text(
        """
mdl 1.6;
uniform texture_2d Normal_Tex = texture_2d("./Textures/normal.png", ::tex::gamma_linear);
float Opacity = 0.5;
export material Cup() = ::OmniUe4Translucent(
    normal: Normal_mdl,
    opacity: Opacity);
""",
        encoding="utf-8",
    )

    target_prim = "/Root/Meshes/Furnitures/cup/model_hash_a_0"
    material_closure_plan = {
        "schema_version": 1,
        "status": "planned_material_dependency_closure",
        "models": [
            {
                "model_root": str(model_root),
                "root_asset": str(model_root / "instance.usd"),
                "targets": [
                    {
                        "source_scene_id": "scene_a_usd",
                        "object_instance_id": "cup/model_hash_a_0",
                        "target_prim_path": target_prim,
                        "object_category": "cup",
                    }
                ],
                "required_material_assets": [
                    {"source_path": str(mdl_path), "size_bytes": mdl_path.stat().st_size}
                ],
            }
        ],
    }
    stress_manifest = {
        "schema_version": 1,
        "summary": {"stress_pair_count": 1},
        "selected_pairs": [
            {
                "pair_id": "sample.zoom_001",
                "target_id": "sample",
                "source_scene_id": "scene_a_usd",
                "target_prim_path": target_prim,
                "target_category": "cup",
                "visual_review": {"verdict": "PASS"},
            }
        ],
    }

    manifest = module.build_effect_sample_manifest(
        material_closure_plan,
        stress_manifest,
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["status"] == "effect_sample_manifest_ready"
    assert manifest["summary"]["sample_count"] == 1
    assert manifest["summary"]["effect_counts"]["normal_bump"] == 1
    assert manifest["summary"]["effect_counts"]["opacity_transparency"] == 1
    assert "clearcoat" in manifest["summary"]["effect_gaps"]
    assert manifest["samples"][0]["pair_id"] == "sample.zoom_001"
    assert manifest["samples"][0]["material_model"]["target_prim_path"] == target_prim
    assert manifest["samples"][0]["effects"]["opacity_transparency"]["present"] is True
