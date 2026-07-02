import json
import pytest
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

from convert_asset.cli import main
from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.negative_gate import build_negative_gate_summary
from convert_asset.asset_application_normalizer.pipeline import normalize_asset


ROOT = Path(__file__).resolve().parents[1]


def _base_args(
    source: Path,
    out_dir: Path,
    evidence_out: Path,
    *,
    asset_class: str = "auto",
) -> list[str]:
    return [
        "normalize-asset",
        str(source),
        "--out",
        str(out_dir),
        "--asset-id",
        "DryingBox",
        "--asset-class",
        asset_class,
        "--source-runtime",
        "isaac51",
        "--target-runtime",
        "isaac41",
        "--target-benchmark",
        "ebench-lift2",
        "--task-id",
        "Lift2.DryingBox",
        "--required-prim",
        "/World/DryingBox",
        "--gates",
        "static",
        "--evidence-out",
        str(evidence_out),
        "--dry-run",
    ]


def test_normalize_asset_dry_run_writes_manifest_without_package_contents(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DryingBox.usd"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "evidence" / "manifest.json"

    code = main(_base_args(source, out_dir, evidence_out))

    assert code == 0
    assert evidence_out.exists()
    assert not out_dir.exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "asset_application_normalizer.v1"
    assert manifest["milestone"] == "AAN-02-cli-skeleton"
    assert manifest["overall_status"] == "dry_run_incomplete"
    assert manifest["source"]["path"] == str(source)
    assert manifest["source"]["source_format"] == "usd"
    assert manifest["target"] == {
        "target_runtime_profile": "isaac41",
        "target_benchmark_profile": "ebench-lift2",
    }
    assert manifest["entrypoints"]["root_usd"] == "asset.usd"
    assert manifest["required_prim_paths"] == [
        {
            "name": "required_prim_0",
            "path": "/World/DryingBox",
            "role": "contract_required_prim",
            "required": True,
        }
    ]
    assert manifest["stage_gates"][0]["check_id"] == "AAN-02-cli-skeleton"
    assert manifest["material_runtime_closure"]["mirror_actions"] == []
    assert manifest["runtime_evidence"] == {}
    assert manifest["waivers"] == []
    assert manifest["blocked_reasons"] == []


def test_normalize_asset_rejects_non_usd_input_without_manifest(
    tmp_path: Path,
) -> None:
    source = tmp_path / "robot.urdf"
    source.write_text("<robot />\n", encoding="utf-8")
    evidence_out = tmp_path / "manifest.json"

    code = main(_base_args(source, tmp_path / "package", evidence_out))

    assert code == 2
    assert not evidence_out.exists()


def test_normalize_asset_rejects_unsupported_runtime_and_benchmark(
    tmp_path: Path,
) -> None:
    source = tmp_path / "asset.usd"
    source.write_text("#usda 1.0\n", encoding="utf-8")

    runtime_args = _base_args(source, tmp_path / "pkg_runtime", tmp_path / "runtime.json")
    runtime_args[runtime_args.index("isaac41")] = "isaac51"
    assert main(runtime_args) == 2
    assert not (tmp_path / "runtime.json").exists()

    benchmark_args = _base_args(source, tmp_path / "pkg_benchmark", tmp_path / "benchmark.json")
    benchmark_args[benchmark_args.index("ebench-lift2")] = "autobio"
    assert main(benchmark_args) == 2
    assert not (tmp_path / "benchmark.json").exists()


def test_normalize_asset_blocks_missing_local_dependency_without_package(
    tmp_path: Path,
) -> None:
    source = tmp_path / "asset.usda"
    source.write_text(
        "#usda 1.0\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" (\n"
        "        references = @missing_child.usda@\n"
        "    ) {}\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "blocked_manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 5
    assert evidence_out.exists()
    assert not out_dir.exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "blocked"
    assert manifest["milestone"] == "AAN-05-physics-static"
    gate_by_id = {gate["check_id"]: gate for gate in manifest["stage_gates"]}
    assert gate_by_id["AAN-04-material-closure"]["status"] == "not_run"
    assert gate_by_id["AAN-05-physics-static"]["status"] == "not_run"
    assert manifest["static_material_report"]["status"] == "not_run"
    assert manifest["static_usd_report"]["required_prims"][0] == {
        "path": "/World/DryingBox",
        "exists": True,
        "status": "pass",
    }
    missing_record = manifest["dependency_closure"]["missing"][0]
    assert missing_record["raw_asset_path"] == "missing_child.usda"
    assert missing_record["resolution"] == "blocked"
    assert missing_record["required_resolution"]
    assert manifest["dependency_closure"]["resolution_summary"]["blocked"] == 1
    assert manifest["blocked_reasons"][0]["blocker_id"] == "aan03_block_missing_dependency"


def test_normalize_asset_writes_package_local_usd_closure(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    (source_root / "parts").mkdir(parents=True)
    (source_root / "materials").mkdir()
    (source_root / "textures").mkdir()
    (source_root / "materials" / "surface.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (source_root / "textures" / "albedo.png").write_bytes(b"png")
    (source_root / "parts" / "part.usda").write_text(
        "#usda 1.0\n"
        "def Xform \"Part\" {\n"
        "    custom asset material = @../materials/surface.mdl@\n"
        "    custom asset texture = @../textures/albedo.png@\n"
        "}\n",
        encoding="utf-8",
    )
    source = source_root / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        "    subLayers = [@parts/part.usda@]\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" (\n"
        "        references = @parts/part.usda@\n"
        "    ) {}\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    assert (out_dir / "asset.usd").exists()
    assert (out_dir / "deps" / "usd" / "part.usda").exists()
    assert (out_dir / "deps" / "mdl" / "surface.mdl").exists()
    assert (out_dir / "deps" / "textures" / "albedo.png").exists()
    root_text = (out_dir / "asset.usd").read_text(encoding="utf-8")
    part_text = (out_dir / "deps" / "usd" / "part.usda").read_text(encoding="utf-8")
    assert "@deps/usd/part.usda@" in root_text
    assert "@../mdl/surface.mdl@" in part_text
    assert "@../textures/albedo.png@" in part_text
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-05-physics-static"
    assert manifest["overall_status"] == "pass"
    assert manifest["entrypoints"]["root_usd"] == "asset.usd"
    assert manifest["static_usd_report"]["root_layer"]["default_prim"] == "World"
    assert manifest["static_material_report"]["material_count"] == 0
    assert manifest["static_usd_report"]["required_prims"][0] == {
        "path": "/World/DryingBox",
        "exists": True,
        "status": "pass",
    }
    assert manifest["dependency_closure"]["missing"] == []
    assert manifest["dependency_closure"]["unauthorized_remote_uri"] == []
    local_files = {
        (record["kind"], record["package_path"])
        for record in manifest["dependency_closure"]["local_files"]
    }
    assert ("usd", "deps/usd/part.usda") in local_files
    assert ("mdl", "deps/mdl/surface.mdl") in local_files
    assert ("texture", "deps/textures/albedo.png") in local_files


def test_normalize_asset_writes_material_closure_for_packaged_mdl_and_texture(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    (source_root / "materials").mkdir(parents=True)
    (source_root / "textures").mkdir()
    (source_root / "materials" / "paint.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (source_root / "textures" / "alpha.png").write_bytes(b"alpha")
    source = source_root / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {}\n"
        "}\n"
        "def Scope \"Looks\" {\n"
        "    def Material \"Paint\" {\n"
        "        token outputs:mdl:surface.connect = </Looks/Paint/Shader.outputs:out>\n"
        "        def Shader \"Shader\" {\n"
        "            uniform token info:implementationSource = \"sourceAsset\"\n"
        "            asset info:mdl:sourceAsset = @materials/paint.mdl@\n"
        "            color3f inputs:diffuseColor = (0.2, 0.4, 0.6)\n"
        "            float inputs:roughness = 0.5\n"
        "            asset inputs:opacity_texture = @textures/alpha.png@\n"
        "            token outputs:out\n"
        "        }\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-05-physics-static"
    assert manifest["static_material_report"]["material_count"] == 1
    assert manifest["static_material_report"]["closure_mode_counts"]["local_mirror"] == 1
    record = manifest["material_closure"][0]
    assert record["material_prim"] == "/Looks/Paint"
    assert record["closure_mode"] == "local_mirror"
    assert record["source_assets_preserved"] is True
    assert record["source_mdl_assets"][0]["raw_asset_path"] == "materials/paint.mdl"
    assert record["source_mdl_assets"][0]["package_path"] == "deps/mdl/paint.mdl"
    assert len(record["source_mdl_assets"][0]["package_sha256"]) == 64
    assert record["texture_paths"][0]["raw_asset_path"] == "textures/alpha.png"
    assert record["texture_paths"][0]["package_path"] == "deps/textures/alpha.png"
    assert len(record["texture_paths"][0]["package_sha256"]) == 64
    assert record["extracted_channels"]["baseColor"]["source"] == "constant"
    assert record["transparency_strategy"] == "opacity_input"
    assert record["preview_surface_fallback"]["status"] == "not_generated"


def test_normalize_asset_blocks_unresolved_mdl_runtime_helper_before_physics(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    (source_root / "materials").mkdir(parents=True)
    (source_root / "materials" / "paint.mdl").write_text(
        "mdl 1.0;\nimport ad_3dsmax_materials::*;\n",
        encoding="utf-8",
    )
    source = source_root / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {}\n"
        "}\n"
        "def Scope \"Looks\" {\n"
        "    def Material \"Paint\" {\n"
        "        def Shader \"Shader\" {\n"
        "            uniform token info:implementationSource = \"sourceAsset\"\n"
        "            asset info:mdl:sourceAsset = @materials/paint.mdl@\n"
        "            token outputs:out\n"
        "        }\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "blocked"
    assert manifest["material_runtime_closure"]["status"] == "blocked"
    gate_by_id = {gate["check_id"]: gate for gate in manifest["stage_gates"]}
    assert gate_by_id["AAN-11-material-runtime-closure"]["status"] == "blocked"
    assert gate_by_id["AAN-05-physics-static"]["status"] == "not_run"


def test_normalize_asset_mirrors_mdl_runtime_helper_and_texture_from_source_context(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    (source_root / "materials" / "helpers").mkdir(parents=True)
    (source_root / "textures").mkdir()
    (source_root / "materials" / "helpers" / "paint.mdl").write_text(
        "mdl 1.0;\n",
        encoding="utf-8",
    )
    (source_root / "textures" / "albedo.png").write_bytes(b"png")
    root_text = (
        "mdl 1.0;\n"
        "import .::helpers::paint::*;\n"
        'export material m(texture_2d tex = texture_2d("../textures/albedo.png")) = material();\n'
    )
    (source_root / "materials" / "root.mdl").write_text(root_text, encoding="utf-8")
    source = source_root / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {}\n"
        "}\n"
        "def Scope \"Looks\" {\n"
        "    def Material \"Paint\" {\n"
        "        def Shader \"Shader\" {\n"
        "            uniform token info:implementationSource = \"sourceAsset\"\n"
        "            asset info:mdl:sourceAsset = @materials/root.mdl@\n"
        "            token outputs:out\n"
        "        }\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    assert (out_dir / "deps" / "mdl" / "helpers" / "paint.mdl").exists()
    assert (out_dir / "deps" / "textures" / "albedo.png").exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    runtime = manifest["material_runtime_closure"]
    assert runtime["status"] == "pass"
    assert runtime["root_mdl_assets"] == [
        "deps/mdl/helpers/paint.mdl",
        "deps/mdl/root.mdl",
    ]
    assert runtime["imported_mdl_modules"][0]["resolution"] == "mirrored"
    assert runtime["mdl_texture_assets"][0]["resolution"] == "mirrored"
    assert [action["action_id"] for action in runtime["mirror_actions"]] == [
        "aan11_mirror_helper_mdl",
        "aan11_mirror_mdl_texture",
    ]


def _authored_articulation_usda() -> str:
    return (
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def PhysicsScene \"PhysicsScene\" {}\n"
        "    def Xform \"DryingBox\" (\n"
        "        prepend apiSchemas = [\"PhysicsArticulationRootAPI\"]\n"
        "    ) {\n"
        "        def Mesh \"Body\" (\n"
        "            prepend apiSchemas = [\"PhysicsRigidBodyAPI\", \"PhysicsCollisionAPI\", \"PhysicsMassAPI\"]\n"
        "        ) {\n"
        "            bool physics:rigidBodyEnabled = 1\n"
        "            bool physics:collisionEnabled = 1\n"
        "            float physics:mass = 2\n"
        "            float3 physics:diagonalInertia = (0.1, 0.1, 0.1)\n"
        "            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]\n"
        "            int[] faceVertexCounts = [3]\n"
        "            int[] faceVertexIndices = [0, 1, 2]\n"
        "        }\n"
        "        def PhysicsRevoluteJoint \"DoorJoint\" {\n"
        "            uniform token physics:axis = \"Y\"\n"
        "            float physics:lowerLimit = 0\n"
        "            float physics:upperLimit = 90\n"
        "            bool physics:jointEnabled = 1\n"
        "        }\n"
        "    }\n"
        "}\n"
    )


def _authored_articulation_with_goal_usda() -> str:
    return (
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def PhysicsScene \"PhysicsScene\" {}\n"
        "    def Xform \"DryingBox\" (\n"
        "        prepend apiSchemas = [\"PhysicsArticulationRootAPI\"]\n"
        "    ) {\n"
        "        def Mesh \"Body\" (\n"
        "            prepend apiSchemas = [\"PhysicsRigidBodyAPI\", \"PhysicsCollisionAPI\", \"PhysicsMassAPI\"]\n"
        "        ) {\n"
        "            bool physics:rigidBodyEnabled = 1\n"
        "            bool physics:collisionEnabled = 1\n"
        "            float physics:mass = 2\n"
        "            float3 physics:diagonalInertia = (0.1, 0.1, 0.1)\n"
        "            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]\n"
        "            int[] faceVertexCounts = [3]\n"
        "            int[] faceVertexIndices = [0, 1, 2]\n"
        "        }\n"
        "        def Xform \"Goal\" {}\n"
        "        def PhysicsRevoluteJoint \"DoorJoint\" {\n"
        "            uniform token physics:axis = \"Y\"\n"
        "            float physics:lowerLimit = 0\n"
        "            float physics:upperLimit = 90\n"
        "            bool physics:jointEnabled = 1\n"
        "        }\n"
        "    }\n"
        "}\n"
    )


def test_normalize_asset_writes_physics_static_closure_for_authored_articulation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DryingBox.usda"
    source.write_text(_authored_articulation_usda(), encoding="utf-8")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out, asset_class="articulated")
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-05-physics-static"
    assert manifest["overall_status"] == "pass"
    assert manifest["stage_gates"][-1]["check_id"] == "AAN-05-physics-static"
    assert manifest["stage_gates"][-1]["status"] == "pass"
    assert manifest["physics_closure"]["summary"]["rigid_body_count"] == 1
    assert manifest["physics_closure"]["summary"]["collision_count"] == 1
    assert manifest["physics_closure"]["summary"]["mass_record_count"] == 1
    mass_record = manifest["physics_closure"]["mass_properties"][0]
    assert mass_record["mass"]["value_source"] == "authored"
    assert mass_record["inertia"]["value_source"] == "authored"
    assert manifest["articulation_closure"]["summary"]["articulation_root_count"] == 1
    assert manifest["articulation_closure"]["summary"]["joint_count"] == 1
    joint = manifest["articulation_closure"]["joints"][0]
    assert joint["joint_type"] == "PhysicsRevoluteJoint"
    assert joint["axis"]["value"] == "Y"
    assert joint["axis"]["value_source"] == "authored"
    assert joint["limits"]["lower"]["value"] == 0
    assert joint["limits"]["upper"]["value"] == 90
    assert manifest["runtime_evidence"]["status"] == "not_run"


def test_normalize_asset_generates_mass_inertia_for_rigid_prop_without_mass_api(
    tmp_path: Path,
) -> None:
    source = tmp_path / "Beaker.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Mesh \"Beaker\" (\n"
        "        prepend apiSchemas = [\"PhysicsRigidBodyAPI\", \"PhysicsCollisionAPI\"]\n"
        "    ) {\n"
        "        bool physics:rigidBodyEnabled = 1\n"
        "        bool physics:collisionEnabled = 1\n"
        "        point3f[] points = [(0, 0, 0), (4, 0, 0), (0, 3, 0), (0, 0, 5)]\n"
        "        int[] faceVertexCounts = [3, 3, 3, 3]\n"
        "        int[] faceVertexIndices = [0, 1, 2, 0, 1, 3, 0, 2, 3, 1, 2, 3]\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out, asset_class="rigid")
    args[args.index("DryingBox")] = "Beaker"
    args[args.index("Lift2.DryingBox")] = "AAN08.TransparentBeaker"
    args[args.index("/World/DryingBox")] = "/World/Beaker"
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    package_text = (out_dir / "asset.usd").read_text(encoding="utf-8")
    assert "PhysicsMassAPI" in package_text
    assert "physics:mass" in package_text
    assert "physics:diagonalInertia" in package_text
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "pass"
    assert manifest["physics_closure"]["summary"]["mass_record_count"] == 1
    assert manifest["physics_closure"]["summary"]["derived_mass_count"] == 1
    mass_record = manifest["physics_closure"]["mass_properties"][0]
    assert mass_record["prim_path"] == "/World/Beaker"
    assert mass_record["mass"]["value_source"] == "derived"
    assert mass_record["mass"]["status"] == "pass"
    assert mass_record["mass"]["value"] > 0
    assert mass_record["inertia"]["value_source"] == "derived"
    assert mass_record["inertia"]["status"] == "pass"
    assert all(value > 0 for value in mass_record["inertia"]["value"])
    assert mass_record["generation"]["method"] == "bbox_shell_density_template_v0"


def test_normalize_asset_generates_invalid_mass_inertia_for_articulated_bodies(
    tmp_path: Path,
) -> None:
    source = tmp_path / "MuffleFurnace.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"Furnace\" (\n"
        "        prepend apiSchemas = [\"PhysicsArticulationRootAPI\"]\n"
        "    ) {\n"
        "        def Mesh \"Door\" (\n"
        "            prepend apiSchemas = [\"PhysicsRigidBodyAPI\", \"PhysicsCollisionAPI\", \"PhysicsMassAPI\"]\n"
        "        ) {\n"
        "            bool physics:rigidBodyEnabled = 1\n"
        "            bool physics:collisionEnabled = 1\n"
        "            float physics:mass = 0\n"
        "            float3 physics:diagonalInertia = (0, 0, 0)\n"
        "            point3f[] points = [(0, 0, 0), (4, 0, 0), (0, 3, 0), (0, 0, 5)]\n"
        "            int[] faceVertexCounts = [3, 3, 3, 3]\n"
        "            int[] faceVertexIndices = [0, 1, 2, 0, 1, 3, 0, 2, 3, 1, 2, 3]\n"
        "        }\n"
        "        def PhysicsRevoluteJoint \"DoorJoint\" {\n"
        "            uniform token physics:axis = \"Z\"\n"
        "            float physics:lowerLimit = -90\n"
        "            float physics:upperLimit = 0\n"
        "        }\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out, asset_class="articulated")
    args[args.index("DryingBox")] = "MuffleFurnace"
    args[args.index("Lift2.DryingBox")] = "AAN08.MuffleFurnaceDoor"
    args[args.index("/World/DryingBox")] = "/World/Furnace"
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "pass"
    assert manifest["physics_closure"]["summary"]["derived_mass_count"] == 1
    assert manifest["physics_closure"]["summary"]["derived_inertia_count"] == 1
    mass_record = manifest["physics_closure"]["mass_properties"][0]
    assert mass_record["mass"]["value_source"] == "derived"
    assert mass_record["inertia"]["value_source"] == "derived"
    assert manifest["articulation_closure"]["joints"][0]["axis"]["value"] == "Z"


def test_normalize_asset_benchmark_gate_writes_ebench_task_contract(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DryingBox.usda"
    source.write_text(_authored_articulation_with_goal_usda(), encoding="utf-8")
    contract = {
        "task_config": {
            "task_id": "Lift2.DryingBox",
            "benchmark": "ebench-lift2",
            "asset_id": "DryingBox",
        },
        "required_prims": {
            "asset_root": "/World/DryingBox",
            "manipulated_body": "/World/DryingBox/Body",
            "collision_root": "/World/DryingBox/Body",
            "articulation_root": "/World/DryingBox",
            "spawn_anchor": "/World/DryingBox",
            "goal_target": "/World/DryingBox/Goal",
        },
        "evaluator": {
            "entrypoint": "ebench.evaluators.lift2:DryingBoxEvaluator",
            "metric": "door_open_success",
        },
    }
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out, asset_class="articulated")
    args.remove("--dry-run")
    args[args.index("static")] = "static,benchmark"
    args.extend(["--contract", str(contract_path)])

    code = main(args)

    assert code == 0
    assert (out_dir / "task" / "task_config.yaml").exists()
    assert (out_dir / "task" / "required_prims.yaml").exists()
    assert (out_dir / "task" / "evaluator.yaml").exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-07-benchmark-contract"
    assert manifest["stage_gates"][-1]["check_id"] == "AAN-07-benchmark-contract"
    assert manifest["stage_gates"][-1]["status"] == "pass"
    assert manifest["benchmark_contract"]["status"] == "pass"
    assert manifest["entrypoints"]["task_config"] == "task/task_config.yaml"
    assert manifest["entrypoints"]["required_prims"] == "task/required_prims.yaml"
    assert manifest["entrypoints"]["metric_evaluator"] == "task/evaluator.yaml"
    assert manifest["benchmark_contract"]["task_files"]["task_config"] == "task/task_config.yaml"
    assert "EBench task readiness is achieved." in manifest["claims_allowed"]
    assert "EBench task readiness is achieved." not in manifest["claims_forbidden"]


def test_normalize_asset_benchmark_gate_blocks_without_evaluator_entrypoint(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DryingBox.usda"
    source.write_text(_authored_articulation_with_goal_usda(), encoding="utf-8")
    contract = {
        "task_config": {
            "task_id": "Lift2.DryingBox",
            "benchmark": "ebench-lift2",
            "asset_id": "DryingBox",
        },
        "required_prims": {
            "asset_root": "/World/DryingBox",
            "manipulated_body": "/World/DryingBox/Body",
            "collision_root": "/World/DryingBox/Body",
            "articulation_root": "/World/DryingBox",
            "spawn_anchor": "/World/DryingBox",
            "goal_target": "/World/DryingBox/Goal",
        },
        "evaluator": {
            "metric": "door_open_success",
        },
    }
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out, asset_class="articulated")
    args.remove("--dry-run")
    args[args.index("static")] = "static,benchmark"
    args.extend(["--contract", str(contract_path)])

    code = main(args)

    assert code == 5
    assert not (out_dir / "task" / "evaluator.yaml").exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-07-benchmark-contract"
    assert manifest["overall_status"] == "blocked"
    assert manifest["stage_gates"][-1]["status"] == "blocked"
    assert manifest["benchmark_contract"]["status"] == "blocked"
    blocker_ids = {item["blocker_id"] for item in manifest["blocked_reasons"]}
    assert "aan07_block_missing_evaluator_entrypoint" in blocker_ids
    assert "EBench task readiness is achieved." in manifest["claims_forbidden"]


def test_normalize_asset_blocks_articulated_asset_without_articulation_facts(
    tmp_path: Path,
) -> None:
    source = tmp_path / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {}\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out, asset_class="articulated")
    args.remove("--dry-run")

    code = main(args)

    assert code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-05-physics-static"
    assert manifest["overall_status"] == "blocked"
    assert manifest["stage_gates"][-1]["check_id"] == "AAN-05-physics-static"
    assert manifest["stage_gates"][-1]["status"] == "blocked"
    assert manifest["physics_closure"]["summary"]["rigid_body_count"] == 0
    assert manifest["articulation_closure"]["summary"]["articulation_root_count"] == 0
    blocker_ids = {item["blocker_id"] for item in manifest["blocked_reasons"]}
    assert "aan05_block_missing_articulation" in blocker_ids


def test_normalize_asset_runtime_gate_records_smoke_evidence_when_requested(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from convert_asset.asset_application_normalizer import pipeline

    source = tmp_path / "DryingBox.usda"
    source.write_text(_authored_articulation_usda(), encoding="utf-8")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    def fake_runtime_smoke(*_args, **_kwargs):
        return SimpleNamespace(
            overall_status="pass",
            return_code=0,
            runtime_evidence={
                "status": "pass",
                "cold_load": {"status": "pass"},
                "render_readback": {
                    "status": "pass",
                    "mean_rgb": [10.0, 20.0, 30.0],
                    "non_background_ratio": 0.42,
                    "bbox_ratio": 0.25,
                    "sha256": "a" * 64,
                },
                "physics_step": {"status": "pass", "frames": 4},
                "reset": {"status": "pass"},
                "material_view_evidence": [
                    {
                        "view_id": "front",
                        "camera_pose": {"position": [1, 0, 1], "look_at": [0, 0, 0]},
                        "target_prim": "/World/DryingBox",
                        "render_hash": "b" * 64,
                        "mean_rgb": [11.0, 21.0, 31.0],
                        "foreground_rgb": [12.0, 22.0, 32.0],
                        "non_background_ratio": 0.44,
                        "bbox_ratio": 0.27,
                    },
                    {
                        "view_id": "orbit_3q",
                        "camera_pose": {"position": [1, 1, 1], "look_at": [0, 0, 0]},
                        "target_prim": "/World/DryingBox",
                        "render_hash": "c" * 64,
                        "mean_rgb": [13.0, 23.0, 33.0],
                        "foreground_rgb": [14.0, 24.0, 34.0],
                        "non_background_ratio": 0.45,
                        "bbox_ratio": 0.28,
                    },
                ],
            },
            stage_gate={
                "check_id": "AAN-06-runtime-smoke",
                "stage": "runtime_smoke",
                "status": "pass",
                "summary": "fake runtime smoke passed",
            },
            blocked_reasons=[],
        )

    monkeypatch.setattr(pipeline, "build_runtime_smoke", fake_runtime_smoke, raising=False)
    request = NormalizeAssetRequest(
        source_usd=source,
        out_dir=out_dir,
        asset_id="DryingBox",
        asset_class="articulated",
        source_runtime="isaac51",
        target_runtime="isaac41",
        target_benchmark="ebench-lift2",
        task_id="Lift2.DryingBox",
        required_prims=["/World/DryingBox"],
        gates=["static", "runtime"],
        evidence_out=evidence_out,
    )

    result = normalize_asset(request)

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-06-runtime-smoke"
    assert manifest["overall_status"] == "pass"
    assert manifest["stage_gates"][-1]["check_id"] == "AAN-06-runtime-smoke"
    assert manifest["runtime_evidence"]["render_readback"]["non_background_ratio"] == 0.42
    assert manifest["material_runtime_closure"]["view_evidence"] == [
        {
            "bbox_ratio": 0.27,
            "camera_pose": {"position": [1, 0, 1], "look_at": [0, 0, 0]},
            "foreground_rgb": [12.0, 22.0, 32.0],
            "mean_rgb": [11.0, 21.0, 31.0],
            "non_background_ratio": 0.44,
            "render_hash": "b" * 64,
            "target_prim": "/World/DryingBox",
            "view_id": "front",
        },
        {
            "bbox_ratio": 0.28,
            "camera_pose": {"position": [1, 1, 1], "look_at": [0, 0, 0]},
            "foreground_rgb": [14.0, 24.0, 34.0],
            "mean_rgb": [13.0, 23.0, 33.0],
            "non_background_ratio": 0.45,
            "render_hash": "c" * 64,
            "target_prim": "/World/DryingBox",
            "view_id": "orbit_3q",
        },
    ]


def test_normalize_asset_runtime_gate_blocks_material_compiler_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from convert_asset.asset_application_normalizer import pipeline

    source = tmp_path / "DryingBox.usda"
    source.write_text(_authored_articulation_usda(), encoding="utf-8")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    def fake_runtime_smoke(layout, *_args, **_kwargs):
        stderr_path = layout.root / "evidence" / "runtime_smoke" / "stderr.log"
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.write_text(
            "[Error] [rtx.mdltranslator] MDLC: could not find module .::ad_3dsmax_materials\n",
            encoding="utf-8",
        )
        return SimpleNamespace(
            overall_status="pass",
            return_code=0,
            runtime_evidence={
                "status": "pass",
                "cold_load": {"status": "pass"},
                "render_readback": {
                    "status": "pass",
                    "mean_rgb": [10.0, 20.0, 30.0],
                    "non_background_ratio": 0.42,
                    "bbox_ratio": 0.25,
                    "sha256": "a" * 64,
                },
                "physics_step": {"status": "pass", "frames": 4},
                "reset": {"status": "pass"},
                "stderr_path": "evidence/runtime_smoke/stderr.log",
            },
            stage_gate={
                "check_id": "AAN-06-runtime-smoke",
                "stage": "runtime_smoke",
                "status": "pass",
                "summary": "fake runtime smoke passed",
            },
            blocked_reasons=[],
        )

    monkeypatch.setattr(pipeline, "build_runtime_smoke", fake_runtime_smoke, raising=False)
    request = NormalizeAssetRequest(
        source_usd=source,
        out_dir=out_dir,
        asset_id="DryingBox",
        asset_class="articulated",
        source_runtime="isaac51",
        target_runtime="isaac41",
        target_benchmark="ebench-lift2",
        task_id="Lift2.DryingBox",
        required_prims=["/World/DryingBox"],
        gates=["static", "runtime"],
        evidence_out=evidence_out,
    )

    result = normalize_asset(request)

    assert result.return_code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-11-material-runtime-closure"
    assert manifest["overall_status"] == "blocked"
    assert manifest["material_runtime_closure"]["status"] == "blocked"
    assert manifest["material_runtime_closure"]["runtime_compiler"]["status"] == "blocked"
    assert manifest["material_runtime_closure"]["runtime_compiler"]["missing_modules"] == [
        "ad_3dsmax_materials"
    ]
    gate_by_id = {gate["check_id"]: gate for gate in manifest["stage_gates"]}
    assert gate_by_id["AAN-11-material-runtime-closure"]["status"] == "blocked"
    assert "Material runtime closure is complete." in manifest["claims_forbidden"]


def test_runtime_smoke_writes_worker_report_before_simulation_app_close(
    tmp_path: Path,
) -> None:
    from convert_asset.asset_application_normalizer.runtime_smoke import (
        _close_simulation_app_with_report,
    )

    class ExitingSimulationApp:
        def close(self) -> None:
            raise SystemExit(0)

    report = {"status": "pass", "cold_load": {"status": "pass"}}
    report_path = tmp_path / "report.json"

    with pytest.raises(SystemExit):
        _close_simulation_app_with_report(ExitingSimulationApp(), report_path, report)

    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_runtime_smoke_waits_for_camera_rgba_until_available() -> None:
    from convert_asset.asset_application_normalizer.runtime_smoke import _wait_for_camera_rgba

    frames = [None, None, "rgba-frame"]
    steps: list[bool] = []

    class FakeWorld:
        def step(self, *, render: bool) -> None:
            steps.append(render)

    def fake_camera_rgba(_camera):
        return frames.pop(0)

    rgba = _wait_for_camera_rgba(
        camera=object(),
        world=FakeWorld(),
        camera_rgba=fake_camera_rgba,
        max_attempts=4,
    )

    assert rgba == "rgba-frame"
    assert steps == [True, True]


def test_runtime_smoke_render_metrics_records_foreground_rgb(tmp_path: Path) -> None:
    import numpy as np

    from convert_asset.asset_application_normalizer.runtime_smoke import _render_metrics

    render_path = tmp_path / "render.png"
    render_path.write_bytes(b"png")
    rgb = np.array(
        [
            [[40, 40, 40], [100, 50, 50]],
            [[40, 40, 40], [80, 70, 60]],
        ],
        dtype=np.uint8,
    )

    metrics = _render_metrics(rgb, render_path, (40, 40, 40))

    assert metrics["foreground_rgb"] == [90.0, 60.0, 55.0]
    assert metrics["non_background_ratio"] == 0.5


def test_runtime_smoke_material_view_capture_uses_injected_render_helpers(
    tmp_path: Path,
) -> None:
    import numpy as np

    from convert_asset.asset_application_normalizer.runtime_smoke import (
        _capture_material_view_evidence,
    )

    class FakeWorld:
        def step(self, *, render: bool) -> None:
            assert render is True

    def fake_set_camera(*_args, **_kwargs) -> None:
        return None

    def fake_camera_rgba(_camera):
        return np.full((2, 2, 4), 255, dtype=np.uint8)

    def fake_rgba_to_rgb(_rgba, *, background_color):
        return np.array(
            [
                [[40, 40, 40], [100, 50, 50]],
                [[40, 40, 40], [80, 70, 60]],
            ],
            dtype=np.uint8,
        )

    def fake_save(path: Path, _rgb) -> bool:
        path.write_bytes(b"png")
        return True

    records = _capture_material_view_evidence(
        camera=object(),
        world=FakeWorld(),
        center=np.array([0.0, 0.0, 0.0]),
        distance=1.0,
        args=SimpleNamespace(material_view_dir=tmp_path, render_steps=1),
        target_prim_path="/World/DryingBox",
        bbox_source="authored",
        background_color=(40, 40, 40),
        set_camera_look_at=fake_set_camera,
        camera_rgba=fake_camera_rgba,
        rgba_to_rgb=fake_rgba_to_rgb,
        save_rgb_png=fake_save,
    )

    assert [record["view_id"] for record in records] == ["front", "orbit_3q", "side"]
    assert records[0]["foreground_rgb"] == [90.0, 60.0, 55.0]
    assert records[0]["target_prim"] == "/World/DryingBox"
    assert (tmp_path / "front.png").exists()


def test_normalize_asset_reports_native_preview_surface_material(tmp_path: Path) -> None:
    source = tmp_path / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {}\n"
        "}\n"
        "def Scope \"Looks\" {\n"
        "    def Material \"Preview\" {\n"
        "        token outputs:surface.connect = </Looks/Preview/Shader.outputs:surface>\n"
        "        def Shader \"Shader\" {\n"
        "            uniform token info:id = \"UsdPreviewSurface\"\n"
        "            color3f inputs:diffuseColor = (0.1, 0.2, 0.3)\n"
        "            token outputs:surface\n"
        "        }\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-05-physics-static"
    assert manifest["static_material_report"]["material_count"] == 1
    record = manifest["material_closure"][0]
    assert record["material_prim"] == "/Looks/Preview"
    assert record["closure_mode"] == "native_resolved"
    assert record["source_mdl_assets"] == []
    assert record["texture_paths"] == []
    assert record["source_assets_preserved"] is True
    assert record["extracted_channels"]["baseColor"]["source"] == "constant"
    assert record["extracted_channels"]["baseColor"]["value"] == [0.1, 0.2, 0.3]


def test_normalize_asset_links_material_assets_from_rewritten_child_layers(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    (source_root / "parts").mkdir(parents=True)
    (source_root / "materials").mkdir()
    (source_root / "materials" / "child.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (source_root / "parts" / "part.usda").write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"Asset\"\n"
        ")\n"
        "def Xform \"Asset\" {\n"
        "    def Scope \"Looks\" {\n"
        "        def Material \"Child\" {\n"
        "            token outputs:mdl:surface.connect = </Asset/Looks/Child/Shader.outputs:out>\n"
        "            def Shader \"Shader\" {\n"
        "                uniform token info:implementationSource = \"sourceAsset\"\n"
        "                asset info:mdl:sourceAsset = @../materials/child.mdl@\n"
        "                token outputs:out\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    source = source_root / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" (\n"
        "        references = @parts/part.usda@\n"
        "    ) {}\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    record = next(
        item
        for item in manifest["material_closure"]
        if item["material_prim"] == "/World/DryingBox/Looks/Child"
    )
    assert record["closure_mode"] == "local_mirror"
    assert record["source_mdl_assets"][0]["package_path"] == "deps/mdl/child.mdl"


def test_normalize_asset_mirrors_mdl_from_package_sidecar_root(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    scene_dir = source_root / "assets" / "scene_usds" / "lab"
    mirror_dir = source_root / "assets" / "miscs" / "mdl" / "labutopia" / "mdl"
    scene_dir.mkdir(parents=True)
    mirror_dir.mkdir(parents=True)
    (mirror_dir / "OmniPBR.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    source = scene_dir / "asset.usda"
    source.write_text(
        "#usda 1.0\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {\n"
        "        custom asset material = @OmniPBR.mdl@\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    assert (out_dir / "deps" / "mdl" / "OmniPBR.mdl").exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "pass"
    assert manifest["dependency_closure"]["missing"] == []
    local_files = {
        (record["kind"], record["raw_asset_path"], record["package_path"])
        for record in manifest["dependency_closure"]["local_files"]
    }
    assert ("mdl", "OmniPBR.mdl", "deps/mdl/OmniPBR.mdl") in local_files
    mirrored_records = [
        record
        for record in manifest["dependency_closure"]["resolution_records"]
        if record["raw_asset_path"] == "OmniPBR.mdl"
    ]
    assert mirrored_records[0]["resolution"] == "mirrored"
    assert mirrored_records[0]["package_path"] == "deps/mdl/OmniPBR.mdl"
    assert manifest["dependency_closure"]["resolution_summary"]["mirrored"] == 1


def test_normalize_asset_exports_binary_usd_dependency_with_rewritten_paths(
    tmp_path: Path,
) -> None:
    try:
        from pxr import Sdf  # type: ignore
    except Exception:
        return

    source_root = tmp_path / "source"
    (source_root / "parts").mkdir(parents=True)
    (source_root / "materials").mkdir()
    (source_root / "materials" / "surface.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    binary_dep = source_root / "parts" / "part.usd"
    child_layer = Sdf.Layer.CreateAnonymous("part.usda")
    child_layer.ImportFromString(
        "#usda 1.0\n"
        "def Xform \"Part\" {\n"
        "    custom asset material = @../materials/surface.mdl@\n"
        "}\n"
    )
    child_layer.Export(str(binary_dep))
    assert binary_dep.read_bytes().startswith(b"PXR-USDC")

    source = source_root / "DryingBox.usda"
    source.write_text(
        "#usda 1.0\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" (\n"
        "        references = @parts/part.usd@\n"
        "    ) {}\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    packaged_part = out_dir / "deps" / "usd" / "part.usd"
    assert packaged_part.exists()
    assert "@deps/usd/part.usd@" in (out_dir / "asset.usd").read_text(encoding="utf-8")
    assert "@../mdl/surface.mdl@" in packaged_part.read_text(encoding="utf-8")
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "pass"
    assert manifest["dependency_closure"]["unrewritable_layers"] == []
    local_files = {
        (record["kind"], record["package_path"])
        for record in manifest["dependency_closure"]["local_files"]
    }
    assert ("usd", "deps/usd/part.usd") in local_files
    assert ("mdl", "deps/mdl/surface.mdl") in local_files


def test_normalize_asset_blocks_unauthorized_remote_uri_without_package(
    tmp_path: Path,
) -> None:
    source = tmp_path / "asset.usda"
    source.write_text(
        "#usda 1.0\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" (\n"
        "        references = @omniverse://server/assets/part.usd@\n"
        "    ) {}\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "remote_manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 5
    assert evidence_out.exists()
    assert not out_dir.exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["milestone"] == "AAN-05-physics-static"
    assert manifest["overall_status"] == "blocked"
    gate_by_id = {gate["check_id"]: gate for gate in manifest["stage_gates"]}
    assert gate_by_id["AAN-04-material-closure"]["status"] == "not_run"
    assert gate_by_id["AAN-05-physics-static"]["status"] == "not_run"
    assert manifest["static_material_report"]["status"] == "not_run"
    assert manifest["static_usd_report"]["required_prims"][0] == {
        "path": "/World/DryingBox",
        "exists": True,
        "status": "pass",
    }
    remote_record = manifest["dependency_closure"]["unauthorized_remote_uri"][0]
    assert remote_record["raw_asset_path"] == "omniverse://server/assets/part.usd"
    assert remote_record["resolution"] == "blocked"
    assert remote_record["required_resolution"]
    assert manifest["dependency_closure"]["resolution_summary"]["blocked"] == 1
    assert manifest["blocked_reasons"][0]["blocker_id"] == "aan03_block_remote_uri"


def test_negative_gate_summary_accepts_blocked_manifest_with_failure_modes(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "remote_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "asset_application_normalizer.v1",
                "asset_id": "RemoteBlockedAsset",
                "task_id": "AAN09.RemoteUriBlocked",
                "overall_status": "blocked",
                "source": {"path": str(tmp_path / "remote_uri_block.usda")},
                "stage_gates": [
                    {"stage": "usd_closure", "status": "blocked"},
                    {"stage": "material_closure", "status": "not_run"},
                    {"stage": "physics_static", "status": "not_run"},
                    {"stage": "runtime_smoke", "status": "not_run"},
                    {"stage": "benchmark_contract", "status": "not_run"},
                ],
                "dependency_closure": {
                    "resolution_summary": {
                        "mirrored": 0,
                        "pruned": 0,
                        "waived": 0,
                        "blocked": 1,
                    }
                },
                "waivers": [],
                "blocked_reasons": [
                    {
                        "blocker_id": "aan03_block_remote_uri",
                        "severity": "blocking",
                        "summary": "USD dependency closure found unauthorized remote URI dependencies.",
                        "required_resolution": "Mirror the remote URI into the package or keep blocked.",
                    }
                ],
                "claims_allowed": [
                    "AAN-03 static USD closure inspected the source graph and wrote an evidence manifest."
                ],
                "claims_forbidden": [
                    "Material closure is complete.",
                    "Physics or articulation closure is complete.",
                    "Isaac runtime smoke passed.",
                    "EBench task readiness is achieved.",
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = build_negative_gate_summary([manifest_path])

    assert summary["status"] == "pass"
    assert summary["case_count"] == 1
    assert summary["status_counts"] == {"blocked": 1}
    assert summary["waiver_count"] == 0
    assert summary["failure_modes"]["aan03_block_remote_uri"]["count"] == 1
    assert summary["representative_artifacts"][0]["manifest"] == str(manifest_path)
    assert summary["representative_artifacts"][0]["stage_statuses"]["usd_closure"] == "blocked"
    assert summary["claim_boundary"]["not_run_treated_as_pass"] is False


def test_negative_gate_summary_rejects_false_ready_negative_manifest(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "false_ready.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "asset_application_normalizer.v1",
                "asset_id": "FalseReadyAsset",
                "task_id": "AAN09.FalseReady",
                "overall_status": "pass",
                "source": {"path": str(tmp_path / "false_ready.usda")},
                "stage_gates": [
                    {"stage": "usd_closure", "status": "pass"},
                    {"stage": "material_closure", "status": "pass"},
                ],
                "waivers": [],
                "blocked_reasons": [],
                "claims_allowed": ["EBench task readiness is achieved."],
                "claims_forbidden": [],
            }
        ),
        encoding="utf-8",
    )

    summary = build_negative_gate_summary([manifest_path])

    assert summary["status"] == "fail"
    assert summary["invalid_cases"][0]["reason"] == "negative manifest was not blocked or waived"
    assert summary["case_count"] == 1


def test_negative_gate_summary_requires_complete_waiver_fields(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "bad_waiver.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "asset_application_normalizer.v1",
                "asset_id": "WaivedAsset",
                "task_id": "AAN09.Waived",
                "overall_status": "ready_with_waivers",
                "source": {"path": str(tmp_path / "waived.usda")},
                "stage_gates": [{"stage": "material_closure", "status": "waived"}],
                "waivers": [
                    {
                        "waiver_id": "AAN09-WAIVE-001",
                        "owner": "asset-review",
                        "reason": "Non-semantic texture missing.",
                    }
                ],
                "blocked_reasons": [],
                "claims_allowed": [],
                "claims_forbidden": ["Full visual material parity is achieved."],
            }
        ),
        encoding="utf-8",
    )

    summary = build_negative_gate_summary([manifest_path])

    assert summary["status"] == "fail"
    assert summary["invalid_cases"][0]["reason"] == "waiver record is incomplete"
    assert summary["invalid_cases"][0]["missing_fields"] == ["claims_forbidden", "expires_or_review_by", "impact"]


def test_normalize_asset_inventories_variant_usd_dependency(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "open_part.usda").write_text(
        "#usda 1.0\n"
        "def Xform \"OpenPart\" {}\n",
        encoding="utf-8",
    )
    source = source_root / "asset.usda"
    source.write_text(
        "#usda 1.0\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {\n"
        "        variantSet \"state\" = {\n"
        "            \"open\" {\n"
        "                def Xform \"Door\" (\n"
        "                    references = @open_part.usda@\n"
        "                ) {}\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "variant_manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    assert (out_dir / "deps" / "usd" / "open_part.usda").exists()
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    variant_records = [
        record
        for record in manifest["dependency_closure"]["local_files"]
        if record["raw_asset_path"] == "open_part.usda"
    ]
    assert variant_records[0]["arc_kind"] == "variant_reference"


def test_normalize_asset_inventories_value_clip_dependencies(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "clip_1.usda").write_text(
        "#usda 1.0\n"
        "def Xform \"Clip\" {}\n",
        encoding="utf-8",
    )
    (source_root / "clip_manifest.usda").write_text(
        "#usda 1.0\n"
        "def Xform \"ClipManifest\" {}\n",
        encoding="utf-8",
    )
    source = source_root / "asset.usda"
    source.write_text(
        "#usda 1.0\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" (\n"
        "        clips = {\n"
        "            dictionary default = {\n"
        "                asset[] assetPaths = [@clip_1.usda@]\n"
        "                asset manifestAssetPath = @clip_manifest.usda@\n"
        "            }\n"
        "        }\n"
        "    ) {}\n"
        "}\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "clip_manifest.json"
    args = _base_args(source, out_dir, evidence_out)
    args.remove("--dry-run")

    code = main(args)

    assert code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    arc_by_raw = {
        record["raw_asset_path"]: record["arc_kind"]
        for record in manifest["dependency_closure"]["local_files"]
        if record["raw_asset_path"] in {"clip_1.usda", "clip_manifest.usda"}
    }
    assert arc_by_raw == {
        "clip_1.usda": "clip_asset",
        "clip_manifest.usda": "clip_manifest",
    }


def test_asset_application_normalizer_imports_do_not_load_runtime_modules() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import convert_asset.asset_application_normalizer; "
                "import convert_asset.cli; "
                "loaded = [name for name in sys.modules "
                "if name == 'pxr' or name == 'omni' or name == 'isaacsim' "
                "or name.startswith(('pxr.', 'omni.', 'isaacsim.'))]; "
                "print(loaded)"
            ),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert result.stdout.strip() == "[]"
