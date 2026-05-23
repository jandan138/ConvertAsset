#!/usr/bin/env python3
"""Prepare a minimal GRScenes original-vs-noMDL VLN pair for InternNav.

This script is intentionally pure Python. It does not import pxr, launch Isaac
Sim, run InternNav, or copy large scene trees into the repository. It only
converts GRScenes SN episode metadata into InternNav's expected json.gz layout,
creates fixed.usd entry points under an external work root, and records the
external InternNav runtime metadata needed to reproduce real metrics.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_SOURCE_ROOT = Path("/cpfs/user/zhuzihou/assets/zzh-grscenes")
DEFAULT_NOMDL_ROOT = Path("/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521")
DEFAULT_WORK_ROOT = Path("/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523")
DEFAULT_REPO_MANIFEST = (
    PROJECT_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/prep_manifest.json"
)
RUN_EVAL_SCRIPT = PROJECT_ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py"
COLLECT_RESULTS_SCRIPT = PROJECT_ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/collect_results.py"
DEFAULT_RESULTS_SUMMARY = (
    PROJECT_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json"
)
RUNTIME_DEPS_ROOT = Path("/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523")
DEFAULT_SPLIT_NAME = "mini"
SOURCE_EPISODE_FILE = "sn_episodes.json"
ORIGINAL_NAV_USD = "start_result_navigation.usd"
CONVERTED_NAV_USD = "start_result_navigation_noMDL.usd"
SCENE_SPLITS = ("home_scenes", "commercial_scenes")
INTERNNAV_ROOT = Path("/cpfs/user/zhuzihou/dev/InternNav")
INTERNVLA_MODEL_PATH = "checkpoints/InternVLA-N1-DualVLN"
H1_ROBOT_USD_PATH = "data/Embodiments/vln-pe/h1/h1_internvla.usd"
CAMERA_PRIM_PATH = "torso_link/h1_1_25_down_30"
INTERNVLA_ATTN_FALLBACK = "sdpa"
NEXTDIT_CHECKPOINT_FFN_MULTIPLIER = 2 / 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(path),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "unknown"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _sanitize_id(value: str) -> str:
    chars = [ch if ch.isalnum() else "_" for ch in value]
    return "_".join("".join(chars).strip("_").split("_"))


def _scene_dir(root: Path, scene_split: str, scene_id: str) -> Path:
    return root / "scenes/GRScenes-100" / scene_split / "scenes" / scene_id


def _scene_split_for_scene(root: Path, scene_id: str) -> str | None:
    for scene_split in SCENE_SPLITS:
        if _scene_dir(root, scene_split, scene_id).exists():
            return scene_split
    return None


def _as_xyz(point: Any, *, default_z: float = 0.0) -> list[float]:
    if not isinstance(point, (list, tuple)) or len(point) < 2:
        raise ValueError(f"point must contain at least x/y coordinates: {point!r}")
    z = point[2] if len(point) >= 3 else default_z
    return [float(point[0]), float(point[1]), float(z)]


def _reference_path(record: dict[str, Any]) -> list[list[float]]:
    raw_path = record.get("path") or []
    path = [_as_xyz(point) for point in raw_path]
    if not path:
        path = [_as_xyz(record["start_point"])]
    target = _as_xyz(record.get("target_point", path[-1]))
    if path[-1][:2] != target[:2]:
        path.append(target)
    return path


def _start_rotation_from_path(path: list[list[float]]) -> list[float]:
    if len(path) < 2:
        return [1.0, 0.0, 0.0, 0.0]
    dx = path[1][0] - path[0][0]
    dy = path[1][1] - path[0][1]
    if dx == 0.0 and dy == 0.0:
        return [1.0, 0.0, 0.0, 0.0]
    yaw = math.atan2(dy, dx)
    return [round(math.cos(yaw / 2.0), 10), 0.0, 0.0, round(math.sin(yaw / 2.0), 10)]


def _instruction_text(record: dict[str, Any], object_instance_id: str) -> str:
    dialogue = record.get("dialogue")
    if isinstance(dialogue, list):
        for item in dialogue:
            if isinstance(item, dict) and item.get("role") == "human" and item.get("content"):
                return str(item["content"])
    for key in ("instruction", "prompt", "condition"):
        value = record.get(key)
        if value:
            return str(value)
    return f"Navigate to {object_instance_id.split('/', 1)[0]}."


def _iter_sn_records(source_root: Path) -> list[dict[str, Any]]:
    episode_path = source_root / "benchmark" / SOURCE_EPISODE_FILE
    data = _load_json(episode_path)
    records: list[dict[str, Any]] = []
    for split_name in ("test", "validate"):
        scene_map = data.get(split_name, {})
        for scene_id, object_map in scene_map.items():
            for object_instance_id, raw_records in object_map.items():
                episode_list = raw_records if isinstance(raw_records, list) else [raw_records]
                for index, episode in enumerate(episode_list):
                    records.append(
                        {
                            "source_split": split_name,
                            "scene_id": str(scene_id),
                            "object_instance_id": str(object_instance_id),
                            "episode_index": index,
                            "episode": episode,
                        }
                    )
    return records


def _build_internnav_episode(record: dict[str, Any], episode_id: int) -> dict[str, Any]:
    scene_id = record["scene_id"]
    object_instance_id = record["object_instance_id"]
    source_episode = record["episode"]
    path = _reference_path(source_episode)
    trajectory_id = f"{_sanitize_id(scene_id)}_{_sanitize_id(object_instance_id)}_{record['episode_index']}"
    return {
        "scan": scene_id,
        "trajectory_id": trajectory_id,
        "episode_id": episode_id,
        "start_position": _as_xyz(source_episode.get("start_point", path[0])),
        "start_rotation": _start_rotation_from_path(path),
        "reference_path": path,
        "instruction": {
            "instruction_text": _instruction_text(source_episode, object_instance_id),
            "instruction_tokens": [],
        },
        "info": {
            "geodesic_distance": float(source_episode.get("distance", 0.0)),
        },
        "source": {
            "episode_file": SOURCE_EPISODE_FILE,
            "episode_split": record["source_split"],
            "object_instance_id": object_instance_id,
            "episode_index": record["episode_index"],
            "candidates": source_episode.get("candidates", []),
            "target_point": source_episode.get("target_point"),
        },
    }


def _install_fixed_usd(source: Path, destination_dir: Path, *, link_mode: str) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    fixed_path = destination_dir / "fixed.usd"
    docker_path = destination_dir / "fixed_docker.usd"
    for destination in (fixed_path, docker_path):
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        if link_mode == "copy":
            shutil.copy2(source, destination)
        else:
            destination.symlink_to(source.resolve())
    return fixed_path


def _write_dataset(path: Path, episodes: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump({"episodes": episodes}, handle, ensure_ascii=True, sort_keys=True)


def _config_text(
    *,
    task_name: str,
    scene_data_dir: Path,
    base_data_dir: Path,
    split_name: str,
) -> str:
    return f'''# Auto-generated by ConvertAsset prepare_minipair.py.
from internnav.configs.agent import AgentCfg
from internnav.configs.evaluator import EnvCfg, EvalCfg, EvalDatasetCfg, SceneCfg, TaskCfg


eval_cfg = EvalCfg(
    agent=AgentCfg(
        server_port=8023,
        model_name="internvla_n1",
        ckpt_path="",
        model_settings={{
            "env_num": 1,
            "sim_num": 1,
            "model_path": "{INTERNVLA_MODEL_PATH}",
            "camera_intrinsic": [[585.0, 0.0, 320.0], [0.0, 585.0, 240.0], [0.0, 0.0, 1.0]],
            "width": 640,
            "height": 480,
            "hfov": 79,
            "resize_w": 384,
            "resize_h": 384,
            "max_new_tokens": 1024,
            "num_frames": 32,
            "num_history": 8,
            "num_future_steps": 4,
            "device": "cuda:0",
            "predict_step_nums": 32,
            "continuous_traj": True,
            "infer_mode": "partial_async",
            "vis_debug": False,
            "vis_debug_path": "./logs/{task_name}/vis_debug",
        }},
    ),
    env=EnvCfg(
        env_type="internutopia",
        env_settings={{
            "use_fabric": False,
            "headless": True,
        }},
    ),
    task=TaskCfg(
        task_name="{task_name}",
        task_settings={{
            "env_num": 1,
            "use_distributed": False,
            "proc_num": 1,
            "max_step": 1000,
        }},
        scene=SceneCfg(
            scene_type="grscene",
            scene_data_dir="{scene_data_dir}",
        ),
        robot_name="h1",
        robot_flash=True,
        flash_collision=False,
        robot_usd_path="{H1_ROBOT_USD_PATH}",
        camera_resolution=[640, 480],
        camera_prim_path="{CAMERA_PRIM_PATH}",
        one_step_stand_still=True,
    ),
    dataset=EvalDatasetCfg(
        dataset_type="grscene",
        dataset_settings={{
            "base_data_dir": "{base_data_dir}",
            "split_data_types": ["{split_name}"],
            "filter_same_trajectory": False,
            "filter_stairs": False,
        }},
    ),
    eval_type="vln_distributed",
    eval_settings={{
        "save_to_json": True,
        "vis_output": False,
        "use_agent_server": False,
    }},
)
'''


def _write_eval_configs(work_root: Path, dataset_root: Path, split_name: str) -> dict[str, str]:
    config_dir = work_root / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    configs = {
        "original": {
            "path": config_dir / "original_eval_cfg.py",
            "task_name": "convertasset_grscene_sn_original_mini",
            "scene_data_dir": work_root / "scene_data/original",
        },
        "converted": {
            "path": config_dir / "converted_eval_cfg.py",
            "task_name": "convertasset_grscene_sn_nomdl_mini",
            "scene_data_dir": work_root / "scene_data/converted",
        },
    }
    for cfg in configs.values():
        cfg["path"].write_text(
            _config_text(
                task_name=str(cfg["task_name"]),
                scene_data_dir=Path(cfg["scene_data_dir"]),
                base_data_dir=dataset_root,
                split_name=split_name,
            ),
            encoding="utf-8",
        )
    return {key: str(value["path"]) for key, value in configs.items()}


def _wrapper_command(config_path: str) -> str:
    return (
        f"cd {PROJECT_ROOT} && ./scripts/isaac_python.sh {RUN_EVAL_SCRIPT} "
        f"--config {config_path} "
        f"--internnav-root {INTERNNAV_ROOT} "
        f"--runtime-deps-root {RUNTIME_DEPS_ROOT}"
    )


def _internnav_runtime_metadata() -> dict[str, Any]:
    return {
        "wrapper_path": str(RUN_EVAL_SCRIPT),
        "internnav_root": str(INTERNNAV_ROOT),
        "runtime_deps_root": str(RUNTIME_DEPS_ROOT),
        "pythonpath_entries": [
            str(RUNTIME_DEPS_ROOT / "python_target"),
            str(RUNTIME_DEPS_ROOT / "internutopia_probe"),
            str(INTERNNAV_ROOT),
        ],
        "hf_home": str(RUNTIME_DEPS_ROOT / "hf_cache"),
        "hf_hub_disable_xet": "1",
        "attn_fallback": INTERNVLA_ATTN_FALLBACK,
        "nextdit_checkpoint_ffn_multiplier": NEXTDIT_CHECKPOINT_FFN_MULTIPLIER,
        "checkpoint_path": str(INTERNNAV_ROOT / INTERNVLA_MODEL_PATH),
        "h1_robot_usd_path": str(INTERNNAV_ROOT / H1_ROBOT_USD_PATH),
        "compatibility_patches": [
            "disable_transformers_sklearn_probe",
            "flash_attention_2_to_sdpa_when_flash_attn_missing",
            "pkg_resources_packaging_alias_for_longclip",
            "lumina_gradient_checkpointing_signature_compat",
            "nextdit_ffn_dim_multiplier_for_checkpoint_shape",
        ],
        "debug_video_outputs": {
            "vis_debug": False,
            "vis_output": False,
            "reason": "avoid imageio/ffmpeg dependency and large debug video output in the minimal paired smoke run",
        },
    }


def _scene_record(
    *,
    scene_id: str,
    source_root: Path,
    nomdl_root: Path,
    work_root: Path,
    link_mode: str,
) -> dict[str, Any]:
    source_split = _scene_split_for_scene(source_root, scene_id)
    nomdl_split = _scene_split_for_scene(nomdl_root, scene_id)
    if source_split is None:
        return {
            "scene_id": scene_id,
            "pair_status": "missing_original_scene_dir",
            "blocked_by": ["missing_original_scene_dir"],
        }

    original_usd = _scene_dir(source_root, source_split, scene_id) / ORIGINAL_NAV_USD
    converted_usd = _scene_dir(nomdl_root, nomdl_split or source_split, scene_id) / CONVERTED_NAV_USD
    blocked_by = []
    if not original_usd.exists():
        blocked_by.append("missing_original_navigation_usd")
    if not converted_usd.exists():
        blocked_by.append("missing_converted_navigation_usd")

    original_fixed = None
    converted_fixed = None
    if original_usd.exists():
        original_fixed = _install_fixed_usd(
            original_usd,
            work_root / "scene_data/original" / scene_id,
            link_mode=link_mode,
        )
    if converted_usd.exists():
        converted_fixed = _install_fixed_usd(
            converted_usd,
            work_root / "scene_data/converted" / scene_id,
            link_mode=link_mode,
        )

    return {
        "scene_id": scene_id,
        "source_scene_split": source_split,
        "nomdl_scene_split": nomdl_split,
        "pair_status": "ready" if not blocked_by else blocked_by[0],
        "blocked_by": blocked_by,
        "original_navigation_usd": str(original_usd),
        "converted_navigation_usd": str(converted_usd),
        "original_navigation_usd_exists": original_usd.exists(),
        "converted_navigation_usd_exists": converted_usd.exists(),
        "original_fixed_usd": str(original_fixed) if original_fixed else None,
        "converted_fixed_usd": str(converted_fixed) if converted_fixed else None,
        "original_fixed_docker_usd": str(original_fixed.with_name("fixed_docker.usd")) if original_fixed else None,
        "converted_fixed_docker_usd": str(converted_fixed.with_name("fixed_docker.usd")) if converted_fixed else None,
    }


def prepare_minipair(
    *,
    source_root: Path,
    nomdl_root: Path,
    work_root: Path,
    repo_manifest_path: Path,
    max_episodes: int,
    split_name: str = DEFAULT_SPLIT_NAME,
    link_mode: str = "symlink",
    scene_ids: list[str] | None = None,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    nomdl_root = nomdl_root.resolve()
    work_root = work_root.resolve()
    repo_manifest_path = repo_manifest_path.resolve()
    if _is_relative_to(work_root, source_root):
        raise ValueError("work_root must not be inside source_root")
    if max_episodes <= 0:
        raise ValueError("max_episodes must be positive")
    if link_mode not in {"symlink", "copy"}:
        raise ValueError("link_mode must be 'symlink' or 'copy'")

    requested_scene_ids = list(scene_ids or [])
    raw_records = _iter_sn_records(source_root)
    if requested_scene_ids:
        requested_scene_id_set = set(requested_scene_ids)
        raw_records = [record for record in raw_records if record["scene_id"] in requested_scene_id_set]
    raw_records = raw_records[:max_episodes]
    episodes = [_build_internnav_episode(record, episode_id) for episode_id, record in enumerate(raw_records)]
    dataset_root = work_root / "datasets/grscene_sn_mini"
    dataset_path = dataset_root / split_name / f"{split_name}.json.gz"
    _write_dataset(dataset_path, episodes)

    scene_ids = sorted({episode["scan"] for episode in episodes})
    scene_records = [
        _scene_record(
            scene_id=scene_id,
            source_root=source_root,
            nomdl_root=nomdl_root,
            work_root=work_root,
            link_mode=link_mode,
        )
        for scene_id in scene_ids
    ]
    eval_configs = _write_eval_configs(work_root, dataset_root, split_name)
    runtime_metadata = _internnav_runtime_metadata()
    blocked_by = sorted({reason for scene in scene_records for reason in scene.get("blocked_by", [])})
    can_run_paired_eval = bool(episodes) and not blocked_by
    manifest = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "claim_boundary": "input_preparation_only_not_sr_spl_evidence",
        "project_git_commit": _git_commit(PROJECT_ROOT),
        "internnav_git_commit": _git_commit(INTERNNAV_ROOT),
        "source": {
            "grscenes_root": str(source_root),
            "nomdl_work_root": str(nomdl_root),
            "source_episode_file": str(source_root / "benchmark" / SOURCE_EPISODE_FILE),
            "requested_scene_ids": requested_scene_ids,
            "selected_scene_ids": scene_ids,
        },
        "work_root": str(work_root),
        "dataset": {
            "dataset_type": "grscene",
            "split": split_name,
            "path": str(dataset_path),
            "hash_sha256": _sha256_file(dataset_path),
            "episode_count": len(episodes),
        },
        "scene_data": {
            "original": str(work_root / "scene_data/original"),
            "converted": str(work_root / "scene_data/converted"),
        },
        "scene_records": scene_records,
        "episode_records": [
            {
                "episode_id": episode["episode_id"],
                "trajectory_id": episode["trajectory_id"],
                "scan": episode["scan"],
                "instruction_text": episode["instruction"]["instruction_text"],
                "geodesic_distance": episode["info"]["geodesic_distance"],
                "source": episode["source"],
            }
            for episode in episodes
        ],
        "internnav_eval_configs": eval_configs,
        "internnav_runtime": runtime_metadata,
        "internnav_eval_commands": {
            "original": _wrapper_command(eval_configs["original"]),
            "converted": _wrapper_command(eval_configs["converted"]),
            "expected_result_jsons": [
                "logs/convertasset_grscene_sn_original_mini/result.json",
                "logs/convertasset_grscene_sn_nomdl_mini/result.json",
            ],
            "collect_results": (
                f"python {COLLECT_RESULTS_SCRIPT} "
                f"--prep-manifest {repo_manifest_path} "
                "--original-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_mini/result.json "
                "--converted-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json "
                f"--output {DEFAULT_RESULTS_SUMMARY}"
            ),
        },
        "expected_metrics": ["TL", "NE", "FR", "StR", "OS", "SR", "SPL", "Count"],
        "runtime_requirements": {
            "required_for_real_metrics": [
                "internutopia",
                "internutopia_extension",
                "Isaac Sim omni runtime",
                "lmdb",
                "msgpack_numpy",
                "torch",
                "InternVLA-N1 or alternate VLN model checkpoint",
                "H1 robot USD and policy assets",
            ],
            "not_required_for_this_preparation_step": ["pxr", "omni", "InternNav model import"],
        },
        "claim_gate": {
            "can_run_paired_eval": can_run_paired_eval,
            "blocked_by": blocked_by,
            "status": "ready_for_internnav_runtime" if can_run_paired_eval else "missing_pair_inputs",
        },
    }
    _write_json(repo_manifest_path, manifest)
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--nomdl-root", type=Path, default=DEFAULT_NOMDL_ROOT)
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT)
    parser.add_argument("--repo-manifest-path", type=Path, default=DEFAULT_REPO_MANIFEST)
    parser.add_argument("--max-episodes", type=int, default=1)
    parser.add_argument("--split-name", default=DEFAULT_SPLIT_NAME)
    parser.add_argument("--link-mode", choices=("symlink", "copy"), default="symlink")
    parser.add_argument(
        "--scene-id",
        action="append",
        dest="scene_ids",
        default=None,
        help="Restrict episode selection to this GRScenes scene id. May be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = prepare_minipair(
        source_root=args.source_root,
        nomdl_root=args.nomdl_root,
        work_root=args.work_root,
        repo_manifest_path=args.repo_manifest_path,
        max_episodes=args.max_episodes,
        split_name=args.split_name,
        link_mode=args.link_mode,
        scene_ids=args.scene_ids,
    )
    print(json.dumps(manifest["claim_gate"], ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
