#!/usr/bin/env python3
"""Create controlled two-view readout probes from real paired renders.

These are explicitly image-composition experiments, not newly rendered scenes.
Each board has two different categories, both left/right permutations, and both
category queries. Full material conversion and rectangular target-window/context
crossovers share exact source pixels. Selection uses IDs/categories, not scores.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding/stress_vlm_run_manifest_expanded30.json"
DEFAULT = ROOT / "paper/shared/evidence/raw/iclr_model_behavior/interventions_v1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def crossover(original, converted, bbox, region):
    box = (max(0, math.floor(bbox[0])), max(0, math.floor(bbox[1])),
           min(original.width, math.ceil(bbox[2])), min(original.height, math.ceil(bbox[3])))
    if region == "target":
        result = original.copy()
        result.paste(converted.crop(box), box[:2])
    elif region == "context":
        result = converted.copy()
        result.paste(original.crop(box), box[:2])
    else:
        raise ValueError(region)
    return result


def tile_pair(target, distractor, bbox, side):
    if target.size != distractor.size:
        raise ValueError("Tile sizes must match")
    w, h = target.size
    canvas = Image.new("RGB", (2 * w + 16, h), (128, 128, 128))
    offset = side * (w + 16)
    canvas.paste(target, (offset, 0))
    canvas.paste(distractor, ((1 - side) * (w + 16), 0))
    x1, y1, x2, y2 = bbox
    return canvas, [x1 + offset, y1, x2 + offset, y2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT)
    parser.add_argument("--verified-cases", type=Path, help="Use exact IDs from a clean-render case manifest")
    args = parser.parse_args()
    if (args.out / "manifest.json").exists():
        raise SystemExit("Manifest exists; use a new output version")
    source = json.loads(args.source.read_text())
    pairs = {}
    for row in source["scoring_records"]:
        pairs.setdefault(row["pair_id"], {})[row["version"]] = row
    # One frozen view per target, chosen lexically before inference.
    selected = {}
    if args.verified_cases:
        cases = json.loads(args.verified_cases.read_text())["selected_cases"]
        for case in cases:
            key = case["pair_id"]
            if key not in pairs:
                raise ValueError(f"Unknown verified pair {key}")
            selected[key.split(".")[0]] = key
    else:
        for key in sorted(pairs):
            selected.setdefault(key.split(".")[0], key)
    keys = list(selected.values())
    boards = set()
    for index, key in enumerate(keys):
        category = pairs[key]["original"]["target"]["category"]
        other = next(k for k in keys[index + 1:] + keys[:index]
                     if pairs[k]["original"]["target"]["category"] != category)
        boards.add(tuple(sorted((key, other))))
    args.out.mkdir(parents=True, exist_ok=True)
    rows, images, sources = [], {}, {}
    for key in keys:
        for condition, row in pairs[key].items():
            path = Path(row["image"]["path"])
            with Image.open(path) as im:
                images[key, condition] = im.convert("RGB")
            sources[f"{key}.{condition}"] = {"path": str(path), "sha256": sha(path)}
    for board_index, board in enumerate(sorted(boards)):
        for query_index, target_key in enumerate(board):
            other = board[1 - query_index]
            base = pairs[target_key]["original"]
            bbox = base["target"]["bbox_xyxy"]
            for side in (0, 1):
                board_id = f"board{board_index:02d}.q{query_index}.side{side}"
                for family in ("two_view_category", "two_view_action", "target_window", "context_window"):
                    pair_id = f"{board_id}.{family}"
                    for version in ("original", "converted"):
                        target = images[target_key, version]
                        context = images[other, version]
                        if version == "converted" and family == "target_window":
                            target = crossover(images[target_key, "original"], target, bbox, "target")
                            context = images[other, "original"]
                        elif version == "converted" and family == "context_window":
                            target = crossover(images[target_key, "original"], target, bbox, "context")
                        canvas, translated = tile_pair(target, context, bbox, side)
                        path = args.out / "images" / f"{pair_id}.{version}.png"
                        path.parent.mkdir(exist_ok=True)
                        canvas.save(path)
                        row = copy.deepcopy(base)
                        row.update({"sample_id": f"{pair_id}.{version}", "pair_id": pair_id,
                                    "version": version, "experiment": family, "cluster_id": f"board{board_index:02d}",
                                    "target_id": target_key.split(".")[0], "board_source_pairs": list(board),
                                    "target_side": side, "query_category": base["target"]["category"],
                                    "distractor_category": pairs[other]["original"]["target"]["category"],
                                    "task": family, "prediction": None})
                        row["target"]["bbox_xyxy"] = translated
                        row["image"] = {"path": str(path.resolve()), "width": canvas.width,
                                        "height": canvas.height, "hash_sha256": sha(path)}
                        rows.append(row)
    manifest = {"schema_version": 1, "experiment": "two-view category/action and window crossover probes",
                "selection": "one lexical view per target, cyclic different-category pairing; both query/position permutations",
                "source_manifest": str(args.source.relative_to(ROOT)), "source_sha256": sha(args.source),
                "n_boards": len(boards), "n_source_targets": len(keys), "sources": sources,
                "verified_case_manifest": str(args.verified_cases) if args.verified_cases else None,
                "generator_sha256": sha(__file__), "scoring_records": rows}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ("n_boards", "n_source_targets")}, indent=2))
    print(f"Prepared {len(rows)} image queries")


if __name__ == "__main__":
    main()
