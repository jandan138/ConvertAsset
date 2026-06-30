import json
import subprocess
import sys
from pathlib import Path

from convert_asset.cli import main


ROOT = Path(__file__).resolve().parents[1]


def _base_args(source: Path, out_dir: Path, evidence_out: Path) -> list[str]:
    return [
        "normalize-asset",
        str(source),
        "--out",
        str(out_dir),
        "--asset-id",
        "DryingBox",
        "--asset-class",
        "articulated",
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
    assert manifest["dependency_closure"]["missing"][0]["raw_asset_path"] == "missing_child.usda"
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
    assert manifest["milestone"] == "AAN-03-usd-closure"
    assert manifest["overall_status"] == "pass"
    assert manifest["entrypoints"]["root_usd"] == "asset.usd"
    assert manifest["static_usd_report"]["root_layer"]["default_prim"] == "World"
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
    assert manifest["milestone"] == "AAN-03-usd-closure"
    assert manifest["overall_status"] == "blocked"
    assert manifest["dependency_closure"]["unauthorized_remote_uri"][0]["raw_asset_path"] == (
        "omniverse://server/assets/part.usd"
    )
    assert manifest["blocked_reasons"][0]["blocker_id"] == "aan03_block_remote_uri"


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
