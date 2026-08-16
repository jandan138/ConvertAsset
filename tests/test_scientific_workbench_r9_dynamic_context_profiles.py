import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    "amber_reagent_bottle": 2,
    "clear_reagent_bottle": 2,
    "pipette_carousel": 3,
    "pipette_tip_box": 1,
    "wash_bottle": 2,
    "graduated_cylinder_100ml": 2,
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_r9_dynamic_context_profiles_are_source_bound_and_narrow() -> None:
    for name, collider_count in ASSETS.items():
        context = _load(
            ROOT / "profiles" / "context" / f"scientific_workbench_r9_{name}.context.json"
        )
        physics = _load(
            ROOT / "profiles" / "physics" / f"scientific_workbench_r9_{name}.provisional.json"
        )

        assert context["schema_version"] == "aan.dynamic_context_profile.v1"
        assert physics["schema_version"] == "aan.physics_profile.v1"
        assert context["source_binding"] == physics["source_binding"]
        assert context["asset_entry_prim"] == "/ObjectRoot"
        assert context["rigid_root"]["motion_role"] == "dynamic"
        assert context["required_named_frames"] == ["support"]
        assert context["runtime_gates"] == {
            "root_motion": {"required": True, "min_translation_m": 0.01},
            "stable_support": {"required": True},
            "gripper_collision": {"required": False},
        }

        colliders = context["colliders"]
        assert len(colliders) == collider_count
        assert {item["mode"] for item in colliders} == {"author"}
        assert {item["geometry"]["type"] for item in colliders} <= {"Cube", "Cylinder"}
        assert all(item["relative_path"].startswith("__aan_collision_proxy/") for item in colliders)

        assert physics["evidence"]["parameter_status"] == "provisional_geometry"
        assert "not a physical measurement" in physics["evidence"]["claim_boundary"]
        body = physics["scope_rules"][0]["body_rules"][0]
        mass = body["mass_properties"]
        assert physics["scope_rules"][0]["scope_path"] == "/ObjectRoot"
        assert body["motion_role"] == "dynamic"
        assert mass["mode"] == "explicit"
        assert mass["quality_tier"] == "provisional_geometry"
        assert mass["mass_kg"] > 0
        assert all(value > 0 for value in mass["diagonal_inertia_kg_m2"])


def test_r9_runtime_packages_preserve_context_claim_boundary_when_present() -> None:
    package_root = (
        ROOT
        / "outputs"
        / "scientific_workbench_r9_dynamic_context_assets_20260816"
        / "packages"
    )
    if not package_root.exists():
        return

    for package_name in (
        "amber_reagent_bottle",
        "clear_reagent_bottle",
        "pipette_carousel",
        "pipette_tip_box",
        "wash_bottle",
        "library_graduated_cylinder_100ml",
    ):
        manifest = _load(package_root / package_name / "evidence" / "manifest.json")
        contract = manifest["dynamic_context_contract"]
        assert manifest["overall_status"] == "pass"
        assert manifest["blocked_reasons"] == []
        assert manifest["runtime_evidence"]["status"] == "pass"
        assert manifest["runtime_evidence"]["runtime_profile_gate"]["observed_kit_version"].startswith(
            "4.1."
        )
        assert contract["schema_version"] == "aan.dynamic_context_contract.v1"
        assert contract["status"] == "pass"
        assert contract["asset_entry_prim"] == "/ObjectRoot"
        assert "no grasp, manipulation, task, policy, or benchmark-readiness claim" in contract[
            "claim_boundary"
        ]
