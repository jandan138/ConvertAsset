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


def test_normalize_asset_non_dry_run_is_blocked_without_writing_package(
    tmp_path: Path,
) -> None:
    source = tmp_path / "asset.usd"
    source.write_text("#usda 1.0\n", encoding="utf-8")
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
    assert manifest["blocked_reasons"][0]["blocker_id"] == "aan02_block_non_dry_run_not_implemented"


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
