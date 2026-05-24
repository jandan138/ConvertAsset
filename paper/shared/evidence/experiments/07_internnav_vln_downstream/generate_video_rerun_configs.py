#!/usr/bin/env python3
"""Generate selected-only InternNav video rerun datasets and configs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_minipair as prep  # noqa: E402


DEFAULT_OUTPUT_MANIFEST = (
    prep.PROJECT_ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/video_rerun_manifest.json"
)


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


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    episodes = payload.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError(f"dataset missing episodes list: {path}")
    return episodes


def _write_dataset(path: Path, episodes: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump({"episodes": episodes}, handle, ensure_ascii=True, sort_keys=True)


def _episode_path_key(episode: dict[str, Any]) -> str:
    return f"{episode['trajectory_id']}_{episode['episode_id']}"


def _install_file(source: Path, destination: Path, *, link_mode: str) -> str:
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        destination.unlink()
    if link_mode == "copy":
        shutil.copy2(source, destination)
    else:
        destination.symlink_to(source.resolve())
    return str(destination)


def _install_sidecars(sidecars: dict[str, str], destination_dir: Path) -> dict[str, str]:
    installed: dict[str, str] = {}
    destination_dir.mkdir(parents=True, exist_ok=True)
    for name, raw_target in sidecars.items():
        target = Path(raw_target)
        if not target.exists():
            raise FileNotFoundError(target)
        destination = destination_dir / name
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        destination.symlink_to(target.resolve())
        installed[name] = str(target)
    return installed


def _select_episodes(
    *,
    episodes: list[dict[str, Any]],
    selected_path_keys: list[str],
) -> list[dict[str, Any]]:
    episode_by_key = {_episode_path_key(episode): episode for episode in episodes}
    seen: set[str] = set()
    selected = []
    for path_key in selected_path_keys:
        if path_key in seen:
            raise ValueError(f"duplicate selected path_key: {path_key}")
        seen.add(path_key)
        episode = episode_by_key.get(path_key)
        if episode is None:
            raise KeyError(f"selected path_key not found in source dataset: {path_key}")
        selected.append(episode)
    return selected


def _write_eval_configs(work_root: Path, dataset_root: Path, split_name: str) -> dict[str, str]:
    config_dir = work_root / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_specs = {
        "original": {
            "task_name": prep._task_name(prep.ORIGINAL_CONDITION_LABEL, split_name),
            "scene_data_dir": work_root / "scene_data/original",
        },
        "modified": {
            "task_name": prep._task_name(prep.MODIFIED_CONDITION_LABEL, split_name),
            "scene_data_dir": work_root / "scene_data/converted",
        },
    }
    paths: dict[str, str] = {}
    for condition, spec in config_specs.items():
        task_name = str(spec["task_name"])
        path = config_dir / prep._config_filename(condition, task_name, split_name)
        path.write_text(
            prep._config_text(
                task_name=task_name,
                scene_data_dir=Path(spec["scene_data_dir"]),
                base_data_dir=dataset_root,
                split_name=split_name,
                vis_output=True,
            ),
            encoding="utf-8",
        )
        paths[condition] = str(path)
    return paths


def _wrapper_command(config_path: str) -> str:
    return prep._wrapper_command(config_path)


def _task_names(split_name: str) -> dict[str, str]:
    return {
        "original": prep._task_name(prep.ORIGINAL_CONDITION_LABEL, split_name),
        "modified": prep._task_name(prep.MODIFIED_CONDITION_LABEL, split_name),
    }


def generate_video_rerun_configs(
    *,
    prep_manifest_path: Path,
    video_case_manifest_path: Path,
    output_work_root: Path,
    output_manifest_path: Path,
    split_name: str,
    link_mode: str = "symlink",
) -> dict[str, Any]:
    if link_mode not in {"symlink", "copy"}:
        raise ValueError("link_mode must be 'symlink' or 'copy'")

    prep_manifest_path = prep_manifest_path.resolve()
    video_case_manifest_path = video_case_manifest_path.resolve()
    output_work_root = output_work_root.resolve()
    output_manifest_path = output_manifest_path.resolve()
    prep_manifest = _load_json(prep_manifest_path)
    video_case_manifest = _load_json(video_case_manifest_path)
    selected_cases = video_case_manifest.get("selected_cases", [])
    if not selected_cases:
        raise ValueError("video case manifest has no selected_cases")
    selected_path_keys = [str(case["path_key"]) for case in selected_cases]

    source_dataset_path = Path(prep_manifest["dataset"]["path"])
    selected_episodes = _select_episodes(
        episodes=_load_dataset(source_dataset_path),
        selected_path_keys=selected_path_keys,
    )

    dataset_root = output_work_root / f"datasets/grscene_sn_{prep._sanitize_id(split_name)}"
    dataset_path = dataset_root / split_name / f"{split_name}.json.gz"
    _write_dataset(dataset_path, selected_episodes)

    scene_record_by_id = {record["scene_id"]: record for record in prep_manifest.get("scene_records", [])}
    scene_records = []
    for scene_id in sorted({episode["scan"] for episode in selected_episodes}):
        source_record = scene_record_by_id.get(scene_id)
        if source_record is None:
            raise KeyError(f"selected scene missing from prep manifest scene_records: {scene_id}")
        original_dir = output_work_root / "scene_data/original" / scene_id
        modified_dir = output_work_root / "scene_data/converted" / scene_id
        original_fixed = _install_file(Path(source_record["original_fixed_usd"]), original_dir / "fixed.usd", link_mode=link_mode)
        original_docker = _install_file(
            Path(source_record["original_fixed_docker_usd"]),
            original_dir / "fixed_docker.usd",
            link_mode=link_mode,
        )
        modified_fixed = _install_file(Path(source_record["converted_fixed_usd"]), modified_dir / "fixed.usd", link_mode=link_mode)
        modified_docker = _install_file(
            Path(source_record["converted_fixed_docker_usd"]),
            modified_dir / "fixed_docker.usd",
            link_mode=link_mode,
        )
        scene_records.append(
            {
                "scene_id": scene_id,
                "source_scene_record": source_record,
                "original_fixed_usd": original_fixed,
                "original_fixed_docker_usd": original_docker,
                "modified_fixed_usd": modified_fixed,
                "modified_fixed_docker_usd": modified_docker,
                "original_dependency_sidecars": _install_sidecars(
                    source_record.get("original_dependency_sidecars", {}),
                    original_dir,
                ),
                "modified_dependency_sidecars": _install_sidecars(
                    source_record.get("converted_dependency_sidecars", {}),
                    modified_dir,
                ),
            }
        )

    eval_configs = _write_eval_configs(output_work_root, dataset_root, split_name)
    task_names = _task_names(split_name)
    expected_video_outputs = [
        {
            "path_key": path_key,
            "original_mp4": str(prep.INTERNNAV_ROOT / "logs" / task_names["original"] / "video" / path_key / f"{path_key}.mp4"),
            "modified_mp4": str(prep.INTERNNAV_ROOT / "logs" / task_names["modified"] / "video" / path_key / f"{path_key}.mp4"),
        }
        for path_key in selected_path_keys
    ]
    manifest = {
        "schema_version": 1,
        "claim_boundary": "video_rerun_input_preparation_only_not_video_evidence",
        "source_prep_manifest": {
            "path": str(prep_manifest_path),
            "hash_sha256": _sha256_file(prep_manifest_path),
        },
        "source_video_case_manifest": {
            "path": str(video_case_manifest_path),
            "hash_sha256": _sha256_file(video_case_manifest_path),
        },
        "work_root": str(output_work_root),
        "dataset": {
            "dataset_type": "grscene",
            "split": split_name,
            "path": str(dataset_path),
            "hash_sha256": _sha256_file(dataset_path),
            "episode_count": len(selected_episodes),
        },
        "scene_records": scene_records,
        "selected_cases": selected_cases,
        "internnav_eval_configs": eval_configs,
        "internnav_eval_commands": {
            "original": _wrapper_command(eval_configs["original"]),
            "modified": _wrapper_command(eval_configs["modified"]),
        },
        "expected_video_outputs": expected_video_outputs,
        "claim_gate": {
            "selected_episode_count": len(selected_episodes),
            "selected_scene_count": len(scene_records),
            "vis_output": True,
            "status": "ready_for_selected_video_rerun",
        },
    }
    _write_json(output_manifest_path, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prep-manifest", required=True, type=Path)
    parser.add_argument("--video-case-manifest", required=True, type=Path)
    parser.add_argument("--output-work-root", required=True, type=Path)
    parser.add_argument("--output-manifest", default=DEFAULT_OUTPUT_MANIFEST, type=Path)
    parser.add_argument("--split-name", required=True)
    parser.add_argument("--link-mode", choices=("symlink", "copy"), default="symlink")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = generate_video_rerun_configs(
        prep_manifest_path=args.prep_manifest,
        video_case_manifest_path=args.video_case_manifest,
        output_work_root=args.output_work_root,
        output_manifest_path=args.output_manifest,
        split_name=args.split_name,
        link_mode=args.link_mode,
    )
    print(
        json.dumps(
            {
                "selected_episode_count": manifest["dataset"]["episode_count"],
                "output": str(args.output_manifest),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
