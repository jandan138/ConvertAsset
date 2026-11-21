#!/usr/bin/env python3
"""Idempotent Colab orchestrator for CVIU v3 Stages 1-4 with incremental Google Drive checkpoint sync."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


EXP_DIR = Path(__file__).resolve().parent


def _repo_root() -> Path:
    for parent in EXP_DIR.parents:
        if (parent / ".git").exists() and (parent / "paper" / "shared" / "evidence").is_dir():
            return parent
    return EXP_DIR.parents[4]


def _gpu_vram_gb() -> tuple[int, float, str]:
    import torch

    if not torch.cuda.is_available():
        return 0, 0.0, "CPU"
    n = torch.cuda.device_count()
    tot = sum(torch.cuda.get_device_properties(i).total_memory for i in range(n)) / (1024.0 ** 3)
    name = torch.cuda.get_device_name(0)
    return n, tot, name


def _sync_to_drive(work_dir: Path, analysis_dir: Path, drive_out: Path) -> None:
    drive_out.mkdir(parents=True, exist_ok=True)
    # Mirror compact analysis JSON/CSV
    dst_analysis = drive_out / "analysis"
    dst_analysis.mkdir(parents=True, exist_ok=True)
    for f in analysis_dir.glob("*"):
        if f.is_file() and f.suffix in (".json", ".csv"):
            shutil.copy2(f, dst_analysis / f.name)

    # Mirror prediction JSONLs and metadata from v3 runs (small text files, not PNGs)
    runs_dir = work_dir / "runs"
    if runs_dir.is_dir():
        dst_runs = drive_out / "runs"
        dst_runs.mkdir(parents=True, exist_ok=True)
        for sub in runs_dir.iterdir():
            if sub.is_file() and sub.name.startswith("pilot_qualification_"):
                shutil.copy2(sub, dst_runs / sub.name)
            elif sub.is_dir():
                target_sub = dst_runs / sub.name
                target_sub.mkdir(parents=True, exist_ok=True)
                for item in sub.iterdir():
                    if item.is_file() and item.suffix in (".json", ".jsonl"):
                        shutil.copy2(item, target_sub / item.name)
    print(f"[drive-sync] mirrored compact artifacts -> {drive_out}", flush=True)


def _run_py(script_name: str, args: list[str], *, check: bool = True) -> int:
    cmd = [sys.executable, "-u", str(EXP_DIR / script_name), *args]
    print(f"[exec] {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {proc.returncode}")
    return proc.returncode


def main() -> int:
    root = _repo_root()
    raw_v1 = root / "paper/shared/evidence/raw/cviu_formal/v1"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path("/content/cviu_v3_work"))
    parser.add_argument("--assets-root", type=Path, default=Path("/cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu"))
    parser.add_argument("--analysis-dir", type=Path, default=root / "paper/shared/evidence/raw/cviu_v3")
    parser.add_argument(
        "--drive-out",
        type=Path,
        default=Path("/content/drive/MyDrive/UltraSync/ConvertAsset/remote_runs/cviu_v3_20261116"),
    )
    parser.add_argument("--stages", default="1,2,3,4", help="Comma-separated subset of 1,2,3,4")
    args = parser.parse_args()

    os.environ["CVIU_ASSETS_ROOT"] = str(args.assets_root)
    stages = {s.strip() for s in args.stages.split(",") if s.strip()}

    work_dir = args.work_dir.resolve()
    cf_dir = work_dir / "counterfactuals"
    runs_dir = work_dir / "runs"
    analysis_dir = args.analysis_dir.resolve()
    v1_runs_dir = args.assets_root.resolve() / "formal_model_runs_v1"

    n_gpus, vram_gb, gpu_name = _gpu_vram_gb()
    print(f"[env] GPUs={n_gpus} ({gpu_name}), total_vram={vram_gb:.2f} GiB", flush=True)

    # Restore previously backed up runs from Google Drive if starting in a fresh Colab runtime
    drive_runs = args.drive_out / "runs"
    if drive_runs.is_dir() and not runs_dir.exists():
        shutil.copytree(drive_runs, runs_dir, dirs_exist_ok=True)
        print(f"[resume] restored prior v3 runs from {drive_runs}", flush=True)

    # Stage 1: Synthesize 1,440 counterfactuals + extract 480 optical features + initial risk auditor
    if "1" in stages:
        print("=== STAGE 1: Counterfactuals, Optical Features & Initial Risk Gate ===", flush=True)
        cf_manifest = cf_dir / "counterfactual_manifest.json"
        if not cf_manifest.is_file():
            _run_py(
                "build_counterfactual_inputs.py",
                [
                    "--manifest", str(raw_v1 / "manifest.json"),
                    "--out-dir", str(cf_dir),
                    "--assets-root", str(args.assets_root),
                ],
            )
        feat_json = analysis_dir / "pair_optical_features.json"
        if not feat_json.is_file():
            _run_py(
                "optical_and_risk_features.py",
                [
                    "--manifest", str(raw_v1 / "manifest.json"),
                    "--scenes", str(raw_v1 / "scenes.json"),
                    "--reviews-dir", str(raw_v1 / "final_visual_reviews"),
                    "--out-dir", str(analysis_dir),
                    "--assets-root", str(args.assets_root),
                ],
            )
        _run_py(
            "analyze_v3_all.py",
            [
                "--features", str(feat_json),
                "--v1-runs-dir", str(v1_runs_dir),
                "--v3-runs-dir", str(runs_dir),
                "--out-dir", str(analysis_dir),
            ],
        )
        _sync_to_drive(work_dir, analysis_dir, args.drive_out)

    # Stage 2: Qwen3-VL-8B stochastic control (480) + 480-pair counterfactuals (1,440)
    if "2" in stages:
        print("=== STAGE 2: Qwen3-VL-8B Stochastic Control & 480-Pair Counterfactuals ===", flush=True)
        _run_py(
            "run_v3_vlm_suite.py",
            [
                "--task", "stochastic-control",
                "--model-key", "qwen3_vl_8b",
                "--num-draws", "5",
                "--temperature", "0.2",
                "--top-p", "0.95",
                "--max-new-tokens", "64",
                "--out", str(runs_dir / "stochastic_control_qwen3_vl_8b"),
                "--assets-root", str(args.assets_root),
            ],
        )
        _run_py(
            "run_v3_vlm_suite.py",
            [
                "--task", "counterfactual",
                "--model-key", "qwen3_vl_8b",
                "--manifest", str(cf_dir / "counterfactual_manifest.json"),
                "--max-new-tokens", "64",
                "--out", str(runs_dir / "counterfactual_qwen3_vl_8b"),
                "--assets-root", str(args.assets_root),
            ],
        )
        _run_py(
            "analyze_v3_all.py",
            [
                "--features", str(analysis_dir / "pair_optical_features.json"),
                "--v1-runs-dir", str(v1_runs_dir),
                "--v3-runs-dir", str(runs_dir),
                "--out-dir", str(analysis_dir),
            ],
        )
        _sync_to_drive(work_dir, analysis_dir, args.drive_out)

    # Stage 3: Qwen3-VL-2B scaling anchor (pilot + 960 formal + 96 control repeat)
    if "3" in stages:
        print("=== STAGE 3: Qwen3-VL-2B Scaling Completion ===", flush=True)
        _run_py(
            "run_v3_vlm_suite.py",
            [
                "--task", "pilot-qualify",
                "--model-key", "qwen3_vl_2b",
                "--out", str(runs_dir / "pilot_qwen3_vl_2b"),
                "--assets-root", str(args.assets_root),
            ],
        )
        _run_py(
            "run_v3_vlm_suite.py",
            [
                "--task", "formal-primary",
                "--model-key", "qwen3_vl_2b",
                "--repeat", "0",
                "--out", str(runs_dir / "formal_qwen3_vl_2b"),
                "--assets-root", str(args.assets_root),
            ],
        )
        _run_py(
            "run_v3_vlm_suite.py",
            [
                "--task", "control-repeat",
                "--model-key", "qwen3_vl_2b",
                "--repeat", "1",
                "--out", str(runs_dir / "control_repeat_qwen3_vl_2b"),
                "--assets-root", str(args.assets_root),
            ],
        )
        _run_py(
            "analyze_v3_all.py",
            [
                "--features", str(analysis_dir / "pair_optical_features.json"),
                "--v1-runs-dir", str(v1_runs_dir),
                "--v3-runs-dir", str(runs_dir),
                "--out-dir", str(analysis_dir),
            ],
        )
        _sync_to_drive(work_dir, analysis_dir, args.drive_out)

    # Stage 4: Cross-family generalization (InternVL3.5 + 3rd Western lineage gated on pilot)
    if "4" in stages:
        print("=== STAGE 4: Cross-Family Generalization ===", flush=True)
        if vram_gb >= 78.0:
            intern_candidates: tuple[str, ...] = ("internvl3_5_38b", "internvl3_5_14b", "internvl3_5_8b")
        elif vram_gb >= 30.0:
            intern_candidates = ("internvl3_5_14b", "internvl3_5_8b")
        else:
            intern_candidates = ("internvl3_5_8b",)

        intern_key: str | None = None
        for cand in intern_candidates:
            rc = _run_py(
                "run_v3_vlm_suite.py",
                [
                    "--task", "pilot-qualify",
                    "--model-key", cand,
                    "--out", str(runs_dir / f"pilot_{cand}"),
                    "--assets-root", str(args.assets_root),
                ],
                check=False,
            )
            qual_file = runs_dir / f"pilot_qualification_{cand}.json"
            if rc == 0 and qual_file.is_file() and json.loads(qual_file.read_text()).get("passed_90pct_gate"):
                intern_key = cand
                break
            print(f"[fallback] {cand} did not pass pilot/load on {vram_gb:.2f} GiB; trying next InternVL candidate", flush=True)
        if intern_key is None:
            raise RuntimeError(f"All InternVL candidates {intern_candidates} failed >=90% pilot gate or load.")

        _run_py(
            "run_v3_vlm_suite.py",
            [
                "--task", "formal-primary",
                "--model-key", intern_key,
                "--repeat", "0",
                "--out", str(runs_dir / f"formal_{intern_key}"),
                "--assets-root", str(args.assets_root),
            ],
        )
        _sync_to_drive(work_dir, analysis_dir, args.drive_out)

        # Lineage 3 (Western VLM): Molmo2-8B first (native transformers 5.x + 8B param-matched), then Pixtral/Molmo fallback
        western_candidates: tuple[str, ...] = (
            ("molmo2_8b", "pixtral_12b", "molmo_7b_o") if vram_gb >= 26.0 else ("molmo2_8b", "molmo_7b_o")
        )
        promoted_3rd: str | None = None
        for cand in western_candidates:
            rc = _run_py(
                "run_v3_vlm_suite.py",
                [
                    "--task", "pilot-qualify",
                    "--model-key", cand,
                    "--out", str(runs_dir / f"pilot_{cand}"),
                    "--assets-root", str(args.assets_root),
                ],
                check=False,
            )
            qual_file = runs_dir / f"pilot_qualification_{cand}.json"
            if rc == 0 and qual_file.is_file() and json.loads(qual_file.read_text()).get("passed_90pct_gate"):
                promoted_3rd = cand
                break
        if promoted_3rd is None:
            raise RuntimeError(f"All 3rd-family candidates {western_candidates} failed >=90% pilot gate.")

        _run_py(
            "run_v3_vlm_suite.py",
            [
                "--task", "formal-primary",
                "--model-key", promoted_3rd,
                "--repeat", "0",
                "--out", str(runs_dir / f"formal_{promoted_3rd}"),
                "--assets-root", str(args.assets_root),
            ],
        )
        _run_py(
            "analyze_v3_all.py",
            [
                "--features", str(analysis_dir / "pair_optical_features.json"),
                "--v1-runs-dir", str(v1_runs_dir),
                "--v3-runs-dir", str(runs_dir),
                "--out-dir", str(analysis_dir),
            ],
        )
        _sync_to_drive(work_dir, analysis_dir, args.drive_out)

    print("[done] Colab CVIU v3 campaign completed cleanly.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

