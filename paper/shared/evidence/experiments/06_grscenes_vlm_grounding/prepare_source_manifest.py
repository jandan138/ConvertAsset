#!/usr/bin/env python3
"""Prepare the non-render source manifest for the GRScenes VLM pilot.

This script is intentionally pure Python. It does not open USD stages, run
Isaac Sim, copy scenes, or generate no-MDL files. Its job is to lock down the
source dataset, scene selection, scratch locations, and provenance fields before
rendering or VLM inference starts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_SOURCE_ROOT = Path("/cpfs/user/zhuzihou/assets/zzh-grscenes")
DEFAULT_SCRATCH_ROOT = Path("/cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520")
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "paper"
    / "shared"
    / "evidence"
    / "raw"
    / "grscene_vlm_grounding"
    / "source_manifest.json"
)
PROTOCOL_PATH = PROJECT_ROOT / "paper" / "shared" / "evidence" / "experiments" / "06_grscenes_vlm_grounding" / "protocol.yaml"
DATASET_URL = "https://huggingface.co/datasets/InternRobotics/GRScenes"
DATASET_LICENSE = "CC BY-NC-SA 4.0"
EPISODE_FILES = ("mm_episodes.json", "sn_episodes.json")
SCENE_USD_CANDIDATES = (
    "start_result_raw.usd",
    "start_result_navigation.usd",
    "start_result_interaction.usd",
)
REQUIRED_SCENE_FILES = SCENE_USD_CANDIDATES + ("metadata.json", "interactive_obj_list.json")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _parse_object_instance_id(object_instance_id: str) -> dict[str, Any]:
    category, sep, model_instance = object_instance_id.partition("/")
    if not sep or not model_instance.startswith("model_"):
        return {"object_category": category or None, "model_hash": None, "instance_index": None}
    model_tail = model_instance.removeprefix("model_")
    model_hash, index_sep, index_text = model_tail.rpartition("_")
    if not index_sep:
        return {"object_category": category, "model_hash": model_tail, "instance_index": None}
    try:
        instance_index: int | None = int(index_text)
    except ValueError:
        instance_index = None
    return {"object_category": category, "model_hash": model_hash, "instance_index": instance_index}


def _metadata_model_paths(scene_dir: Path, object_category: str | None, model_hash: str | None) -> list[str]:
    if not object_category or not model_hash:
        return []
    metadata = _load_json(scene_dir / "metadata.json")
    models = metadata.get("models", []) if isinstance(metadata, dict) else []
    matches = []
    category_token = f"/{object_category}/"
    hash_token = f"/{model_hash}/"
    for model_path in models:
        model_path_text = str(model_path)
        normalized = f"/{model_path_text.strip('/')}/"
        if category_token in normalized and hash_token in normalized:
            matches.append(model_path_text)
    return sorted(matches)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
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


def _count_episode_records(object_map: dict[str, Any]) -> int:
    count = 0
    for records in object_map.values():
        count += len(records) if isinstance(records, list) else 1
    return count


def _load_episode_counts(source_root: Path) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    benchmark_root = source_root / "benchmark"
    for episode_file in EPISODE_FILES:
        data = _load_json(benchmark_root / episode_file)
        for split_map in data.values():
            for scene_id, object_map in split_map.items():
                counts.setdefault(scene_id, {})[episode_file] = _count_episode_records(object_map)
    return counts


def _flatten_episode_records(source_root: Path) -> dict[str, list[dict[str, Any]]]:
    records_by_scene: dict[str, list[dict[str, Any]]] = {}
    benchmark_root = source_root / "benchmark"
    for episode_file in EPISODE_FILES:
        episode_path = benchmark_root / episode_file
        episode_file_hash = _sha256_file(episode_path)
        data = _load_json(episode_path)
        for split, scene_map in data.items():
            for scene_id, object_map in scene_map.items():
                for object_instance_id, records in object_map.items():
                    episode_list = records if isinstance(records, list) else [records]
                    for episode_index, episode in enumerate(episode_list):
                        pointer = (
                            f"/{_json_pointer_token(str(split))}"
                            f"/{_json_pointer_token(str(scene_id))}"
                            f"/{_json_pointer_token(str(object_instance_id))}"
                            f"/{episode_index}"
                        )
                        episode_hash = _sha256_json(episode)
                        stable_input = f"{episode_file}|{split}|{scene_id}|{object_instance_id}|{episode_index}|{episode_hash}"
                        parsed_object = _parse_object_instance_id(object_instance_id)
                        records_by_scene.setdefault(scene_id, []).append(
                            {
                                "stable_episode_id": _sha256_bytes(stable_input.encode("utf-8"))[:24],
                                "episode_family": episode_file.removesuffix("_episodes.json"),
                                "episode_file": episode_file,
                                "episode_file_hash_sha256": episode_file_hash,
                                "episode_split": split,
                                "source_scene_id": scene_id,
                                "object_instance_id": object_instance_id,
                                **parsed_object,
                                "episode_index": episode_index,
                                "episode_json_pointer": pointer,
                                "episode_hash_sha256": episode_hash,
                                "instruction": episode.get("instruction"),
                                "condition": episode.get("condition"),
                                "prompt": episode.get("prompt"),
                                "candidate_instance_ids": episode.get("candidates", []),
                                "mapping_status": "pending_metadata_to_prim",
                                "mapping_method": None,
                                "mapping_confidence": None,
                                "target_prim_path": None,
                                "candidate_prim_paths": [],
                                "world_bbox": None,
                                "image_bbox": None,
                            }
                        )
    for scene_records in records_by_scene.values():
        scene_records.sort(key=lambda item: (item["episode_file"], item["episode_split"], item["object_instance_id"], item["episode_index"]))
    return records_by_scene


def _scene_dirs(source_root: Path, split: str) -> dict[str, Path]:
    scenes_dir = source_root / "scenes" / "GRScenes-100" / split / "scenes"
    if not scenes_dir.exists():
        raise FileNotFoundError(scenes_dir)
    return {path.name: path for path in sorted(scenes_dir.glob("*_usd")) if path.is_dir()}


def _validate_scene_dir(scene_dir: Path) -> None:
    missing = [name for name in REQUIRED_SCENE_FILES if not (scene_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"{scene_dir}: missing required files: {', '.join(missing)}")


def _converted_usd_path(source_usd_name: str, scratch_scene_root: Path) -> Path:
    source_usd = Path(source_usd_name)
    return scratch_scene_root / f"{source_usd.stem}_noMDL{source_usd.suffix}"


def _scratch_scene_root(scratch_root: Path, scene_split: str, scene_id: str) -> Path:
    return scratch_root / "scenes" / "GRScenes-100" / scene_split / "scenes" / scene_id


def _scene_entry(
    *,
    source_root: Path,
    scratch_root: Path,
    scene_id: str,
    scene_split: str,
    scene_dir: Path,
    source_usd_name: str,
    pilot_role: str,
    episode_counts: dict[str, int],
) -> dict[str, Any]:
    _validate_scene_dir(scene_dir)
    scratch_scene_root = _scratch_scene_root(scratch_root, scene_split, scene_id)
    source_usd = scene_dir / source_usd_name
    converted_usd = _converted_usd_path(source_usd_name, scratch_scene_root)
    episode_sources = [name for name in EPISODE_FILES if name in episode_counts]
    paper_claim_eligible = pilot_role == "episode_backed_home" and set(episode_sources) == set(EPISODE_FILES)
    conversion_command = f"./scripts/isaac_python.sh ./main.py no-mdl {scratch_scene_root / source_usd_name}"

    return {
        "dataset_role": "benchmark_source_dataset",
        "source_dataset_root": str(source_root),
        "source_scene_id": scene_id,
        "source_scene_split": scene_split,
        "scene_dir": str(scene_dir),
        "source_usd": str(source_usd),
        "source_usd_hash_sha256": _sha256_file(source_usd),
        "source_usd_size_bytes": source_usd.stat().st_size,
        "source_usd_mtime_ns": source_usd.stat().st_mtime_ns,
        "source_usd_variant": source_usd_name,
        "scratch_scene_root": str(scratch_scene_root),
        "converted_usd": str(converted_usd),
        "conversion_command": conversion_command,
        "material_conditions": ["original", "converted"],
        "pilot_role": pilot_role,
        "paper_claim_eligible": paper_claim_eligible,
        "episode_sources": episode_sources,
        "episode_counts": {name: episode_counts[name] for name in episode_sources},
        "metadata_json": str(scene_dir / "metadata.json"),
        "metadata_hash_sha256": _sha256_file(scene_dir / "metadata.json"),
        "interactive_obj_list_json": str(scene_dir / "interactive_obj_list.json"),
        "interactive_obj_list_hash_sha256": _sha256_file(scene_dir / "interactive_obj_list.json"),
        "filesystem_notes": {
            "materials_pointer_file": str(scene_dir / "Materials"),
            "models_pointer_file": str(scene_dir / "models"),
        },
    }


def build_source_manifest(
    *,
    source_root: Path,
    scratch_root: Path,
    episode_home_scenes: int,
    metadata_commercial_scenes: int,
    targets_per_scene: int,
    source_usd_name: str = "start_result_raw.usd",
) -> dict[str, Any]:
    source_root = source_root.resolve()
    scratch_root = scratch_root.resolve()
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if source_usd_name not in SCENE_USD_CANDIDATES:
        raise ValueError(f"source_usd_name must be one of {', '.join(SCENE_USD_CANDIDATES)}")

    home_dirs = _scene_dirs(source_root, "home_scenes")
    commercial_dirs = _scene_dirs(source_root, "commercial_scenes")
    episode_counts = _load_episode_counts(source_root)
    episode_records_by_scene = _flatten_episode_records(source_root)

    episode_backed_home_ids = sorted(
        scene_id for scene_id, counts in episode_counts.items() if scene_id in home_dirs and set(counts) == set(EPISODE_FILES)
    )
    selected_home_ids = episode_backed_home_ids[: max(0, episode_home_scenes)]
    selected_commercial_ids = sorted(commercial_dirs)[: max(0, metadata_commercial_scenes)]

    scenes: list[dict[str, Any]] = []
    for scene_id in selected_home_ids:
        scenes.append(
            _scene_entry(
                source_root=source_root,
                scratch_root=scratch_root,
                scene_id=scene_id,
                scene_split="home_scenes",
                scene_dir=home_dirs[scene_id],
                source_usd_name=source_usd_name,
                pilot_role="episode_backed_home",
                episode_counts=episode_counts[scene_id],
            )
        )
    for scene_id in selected_commercial_ids:
        scenes.append(
            _scene_entry(
                source_root=source_root,
                scratch_root=scratch_root,
                scene_id=scene_id,
                scene_split="commercial_scenes",
                scene_dir=commercial_dirs[scene_id],
                source_usd_name=source_usd_name,
                pilot_role="metadata_driven_commercial_stress",
                episode_counts={},
            )
        )

    episode_records: list[dict[str, Any]] = []
    excluded_episode_records: list[dict[str, Any]] = []
    for scene_id in selected_home_ids:
        selected_for_scene = 0
        for record in episode_records_by_scene.get(scene_id, []):
            metadata_paths = _metadata_model_paths(
                home_dirs[scene_id],
                record.get("object_category"),
                record.get("model_hash"),
            )
            enriched_record = {
                **record,
                "dataset_role": "benchmark_source_dataset",
                "source_dataset_root": str(source_root),
                "source_scene_split": "home_scenes",
                "pilot_role": "episode_backed_home",
                "paper_claim_eligible": True,
                "metadata_model_paths": metadata_paths,
                "metadata_match_count": len(metadata_paths),
            }
            if len(metadata_paths) != 1:
                excluded_episode_records.append(
                    {
                        **enriched_record,
                        "paper_claim_eligible": False,
                        "exclusion_reason": "metadata_model_path_match_count_not_one",
                    }
                )
                continue
            if selected_for_scene >= max(0, targets_per_scene):
                continue
            episode_records.append(
                enriched_record
            )
            selected_for_scene += 1

    return {
        "schema_version": 1,
        "status": "planned_source_manifest",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_source_manifest.py",
        "generator_git_commit": _git_commit(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "protocol_path": str(PROTOCOL_PATH),
        "protocol_hash_sha256": _sha256_file(PROTOCOL_PATH) if PROTOCOL_PATH.exists() else "missing",
        "dataset_roles": {
            "benchmark_source_dataset": {
                "local_root": str(source_root),
                "name": "GRScenes-100",
                "url": DATASET_URL,
                "license": DATASET_LICENSE,
                "mutation_policy": "never_in_place",
            },
            "intervention_outputs": {
                "scratch_root": str(scratch_root),
                "retention_policy": "generated_outputs_may_be_deleted_and_regenerated",
            },
        },
        "selection": {
            "source_usd_variant": source_usd_name,
            "episode_home_scenes": len(selected_home_ids),
            "metadata_commercial_scenes": len(selected_commercial_ids),
            "targets_per_scene": targets_per_scene,
            "episode_backed_home_pool": len(episode_backed_home_ids),
            "home_scene_pool": len(home_dirs),
            "commercial_scene_pool": len(commercial_dirs),
            "selection_policy": "deterministic_sorted_scene_ids_then_deterministic_sorted_episode_records",
        },
        "paper_claim_gate": {
            "episode_backed_results_require_paper_claim_eligible_true": True,
            "commercial_stress_results_are_not_episode_backed": True,
            "source_root_required": str(source_root),
        },
        "scenes": scenes,
        "episode_records": episode_records,
        "excluded_episode_records": excluded_episode_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--scratch-root", type=Path, default=DEFAULT_SCRATCH_ROOT)
    parser.add_argument("--episode-home-scenes", type=int, default=5)
    parser.add_argument("--metadata-commercial-scenes", type=int, default=5)
    parser.add_argument("--targets-per-scene", type=int, default=8)
    parser.add_argument("--source-usd", choices=SCENE_USD_CANDIDATES, default="start_result_raw.usd")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    manifest = build_source_manifest(
        source_root=args.source_root,
        scratch_root=args.scratch_root,
        episode_home_scenes=args.episode_home_scenes,
        metadata_commercial_scenes=args.metadata_commercial_scenes,
        targets_per_scene=args.targets_per_scene,
        source_usd_name=args.source_usd,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} with {len(manifest['scenes'])} scenes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
