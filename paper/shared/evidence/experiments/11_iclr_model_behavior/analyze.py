#!/usr/bin/env python3
"""ICLR analysis: fixed-denominator paired outcomes, explicit coordinates, target clusters.

Historical raw predictions are inputs, never rewritten. Conditional hit rates are
reported separately from end-to-end success. Native-frame reinterpretation is
never selected using target annotations. All displacement fields are real pixels.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RAW = ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
OUT = ROOT / "paper/shared/evidence/raw/iclr_model_behavior/analysis_v1"
LABELS = {"gemma4": "Gemma4-E4B", "qwen25": "Qwen2.5-VL-7B", "qwen3vl2b": "Qwen3-VL-2B",
          "qwen3vl8b": "Qwen3-VL-8B", "internvl3_8b": "InternVL3-8B", "molmo7b": "Molmo-7B-D"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def pair_key(row):
    return row.get("pair_id") or row["sample_id"].rsplit(".", 1)[0]


def cluster_key(row):
    return row.get("cluster_id") or (row.get("target") or {}).get("target_id") or pair_key(row).split(".")[0]


def point_pixels(row, frame):
    value = (row.get("prediction") or {}).get("point_xy")
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    if any(isinstance(v, bool) for v in value):
        return None
    try:
        x, y = map(float, value)
        w, h = float(row["image"]["width"]), float(row["image"]["height"])
    except (KeyError, ValueError, TypeError):
        return None
    if not all(math.isfinite(v) for v in (x, y, w, h)) or min(w, h) <= 0:
        return None
    if frame == "pixel":
        return x, y
    if frame not in {"normalized_1000", "normalized_100"}:
        raise ValueError(f"Unknown frame: {frame}")
    scale = 1000 if frame == "normalized_1000" else 100
    return x * w / scale, y * h / scale


def hit(row, frame):
    point = point_pixels(row, frame)
    if point is None:
        return False
    x, y = point
    image = row["image"]
    if not (0 <= x < image["width"] and 0 <= y < image["height"]):
        return False
    box = row["target"]["bbox_xyxy"]
    return min(box[0], box[2]) <= x <= max(box[0], box[2]) and min(box[1], box[3]) <= y <= max(box[1], box[3])


def cluster_ci(groups, rounds=2000, seed=20260915):
    """Resample whole target clusters; retain all repeated views within each draw."""
    rng = random.Random(seed)
    clusters = list(groups.values())
    if not clusters:
        return None, None
    boot = []
    for _ in range(rounds):
        sample = [v for _ in clusters for v in clusters[rng.randrange(len(clusters))]]
        boot.append(statistics.mean(sample))
    boot.sort()
    return boot[int((rounds - 1) * .025)], boot[int((rounds - 1) * .975)]


def summarize(rows, frame):
    paired = defaultdict(dict)
    for row in rows:
        version = row["version"]
        if version not in {"original", "converted"}:
            raise ValueError(f"Unknown condition: {version}")
        key = pair_key(row)
        if version in paired[key]:
            raise ValueError(f"Duplicate pair/condition: {key}/{version}")
        paired[key][version] = row
    if not paired or any(set(sides) != {"original", "converted"} for sides in paired.values()):
        raise ValueError("Empty or incomplete pair set")
    result = {"n_pairs": len(paired), "frame": frame}
    for version in ("original", "converted"):
        selected = [s[version] for s in paired.values()]
        points = [point_pixels(r, frame) for r in selected]
        valid_n = sum(p is not None for p in points)
        hits = sum(hit(r, frame) for r in selected)
        result[version] = {
            "n": len(selected), "valid_point_n": valid_n, "hit_n": hits,
            "success_rate": hits / len(selected), "coverage": valid_n / len(selected),
            "conditional_hit_rate": hits / valid_n if valid_n else None,
            "in_frame_n": sum(p is not None and 0 <= p[0] < r["image"]["width"] and
                              0 <= p[1] < r["image"]["height"] for r, p in zip(selected, points)),
        }
    deltas, by_cluster, views, disps = [], defaultdict(list), defaultdict(lambda: defaultdict(set)), []
    paired_valid, transitions = 0, defaultdict(int)
    for key, sides in paired.items():
        o, c = sides["original"], sides["converted"]
        oh, ch = hit(o, frame), hit(c, frame)
        delta = int(ch) - int(oh)
        cluster = cluster_key(o)
        deltas.append(delta)
        by_cluster[cluster].append(delta)
        if oh:
            views[cluster]["original"].add(key)
        if ch:
            views[cluster]["converted"].add(key)
        # Include all-miss targets as well.
        views[cluster]
        transitions[f"{int(oh)}{int(ch)}"] += 1
        op, cp = point_pixels(o, frame), point_pixels(c, frame)
        if op is not None and cp is not None:
            paired_valid += 1
            disps.append(math.dist(op, cp))
    low, high = cluster_ci(by_cluster)
    result.update({
        "delta": statistics.mean(deltas), "ci95_target_cluster": [low, high],
        "n_targets": len(by_cluster), "paired_valid_n": paired_valid,
        "transitions": dict(transitions), "flip_n": transitions["01"] + transitions["10"],
        "both_hit_n": transitions["11"],
        "view_sets_changed": sum(v["original"] != v["converted"] for v in views.values()),
        "displacement_n": len(disps),
        "displacement_mean_px": statistics.mean(disps) if disps else None,
        "displacement_median_px": statistics.median(disps) if disps else None,
    })
    return result


def input_inventory(rows, cache):
    missing, mismatch, unstamped = [], [], []
    for row in rows:
        image = row["image"]
        path = image.get("path", "")
        if path not in cache:
            cache[path] = digest(path) if Path(path).is_file() else None
        if cache[path] is None:
            missing.append(row["sample_id"])
        elif not image.get("hash_sha256"):
            unstamped.append(row["sample_id"])
        elif image["hash_sha256"] != cache[path]:
            mismatch.append(row["sample_id"])
    return {"missing_images": missing, "changed_images": mismatch, "unstamped_images": unstamped}


def navigation_summary():
    folder = ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99"
    source = folder / "paired_99_summary.json"
    data = json.loads(source.read_text())
    changes = data["paired_outcomes"]["SR"]
    return {"source": str(source.relative_to(ROOT)), "source_sha256": digest(source),
            "n": data["episode_count"], "scenes": data["scene_ids"],
            "metrics": data["metrics"], "fail_to_success": changes["modified_better"],
            "success_to_fail": changes["original_better"], "unchanged": changes["tie"],
            "flips": changes["modified_better"] + changes["original_better"]}


def sampling_summary():
    output = []
    for prefix in ("qwen3vl8b", "qwen3vl2b", "gemma4"):
        paths = [RAW / f"sampling_variance_probes/{prefix}_t07_seed{s}_predictions.jsonl" for s in range(3)]
        seeds = [{r["sample_id"]: r for r in load_rows(p)} for p in paths]
        if any(set(s) != set(seeds[0]) for s in seeds):
            raise ValueError("Seed query IDs differ")
        spreads, unstable, complete = [], 0, 0
        for sid in seeds[0]:
            records = [s[sid] for s in seeds]
            points = [point_pixels(r, "normalized_1000") for r in records]
            unstable += len({hit(r, "normalized_1000") for r in records}) > 1
            if all(p is not None for p in points):
                complete += 1
                spreads.append(statistics.mean(math.dist(points[i], points[j]) for i,j in ((0,1),(0,2),(1,2))))
        output.append({"model": LABELS[prefix], "queries": len(seeds[0]), "seeds": 3, "complete_point_queries": complete,
                       "mean_pairwise_seed_distance_px": statistics.mean(spreads), "hit_instability": unstable / len(seeds[0]),
                       "sources": {str(p.relative_to(ROOT)): digest(p) for p in paths}})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--new-runs", type=Path, help="Additional run directory with predictions/metadata")
    args = parser.parse_args()
    stress_ids = {r["pair_id"] for r in json.loads((RAW / "stress_vlm_run_manifest_expanded30.json").read_text())["scoring_records"]}
    files = [RAW / "stress_predictions.jsonl"]
    for subdir in ("stress_expanded30_probes", "stress_extended80_probes", "clean_pool_probes"):
        files.extend(sorted((RAW / subdir).glob("*_predictions.jsonl")))
    if args.new_runs:
        files.extend(sorted(args.new_runs.rglob("*_predictions.jsonl")))
    runs, cache = [], {}
    for path in files:
        path = path.resolve()
        if not path.with_suffix(".jsonl.metadata.json").exists():
            # A flushed JSONL without its closing metadata is an in-flight run.
            continue
        rows = load_rows(path)
        meta = json.loads(path.with_suffix(".jsonl.metadata.json").read_text())
        frame = meta["coordinate_frame"]
        if "clean_pool" in str(path):
            pool = "clean15"
        elif "extended80" in str(path):
            pool = "extended80"
        elif path.is_relative_to(RAW):
            pool = "stress30"
        else:
            pool = rows[0].get("experiment", "new")
        tag = next((label for prefix, label in LABELS.items() if path.name.startswith(prefix)), "Gemma4-E4B")
        run = {"id": path.stem, "model": tag, "pool": pool, "frame": frame,
               "format": meta["response_format"], "prompt": meta.get("prompt_type", "s1_point"),
               "source": str(path.relative_to(ROOT)), "source_sha256": digest(path),
               "checkpoint": meta["model_checkpoint"], "metadata_sha256": digest(path.with_suffix(".jsonl.metadata.json")),
               "inventory": input_inventory(rows, cache), "score": summarize(rows, frame),
               "normalized1000_diagnostic": summarize(rows, "normalized_1000"),
               "subsets": {}}
        for view_type in ("zoom", "retake"):
            sub = [r for r in rows if f".{view_type}_" in r["sample_id"]]
            if sub:
                run["subsets"][view_type] = summarize(sub, frame)
        # Image-center baseline needs no model or target at inference time.
        centers = [dict(r, prediction={"point_xy": [r["image"]["width"] / 2, r["image"]["height"] / 2]}) for r in rows]
        run["center_baseline"] = summarize(centers, "pixel")
        if pool == "extended80":
            matching = [r for r in rows if pair_key(r) in stress_ids]
            if len(matching) == 60:
                run["current_stress30_slice"] = summarize(matching, frame)
                run["current_stress30_slice_note"] = "Exact ID subset of this 80-pair inference run; not new inference"
        runs.append(run)
    args.out.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "analysis_sha256": digest(__file__),
              "estimand": "paired end-to-end success; all queries in denominator; target-cluster bootstrap",
              "runs": runs, "navigation": navigation_summary(), "sampling": sampling_summary()}
    (args.out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    fields = ["id", "model", "pool", "frame", "format", "prompt", "n_pairs", "n_targets", "success_original",
              "success_converted", "delta", "coverage_original", "coverage_converted", "paired_valid_n",
              "ci_low", "ci_high", "median_displacement_px", "changed_images"]
    with (args.out / "results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for run in runs:
            s = run["score"]
            writer.writerow({**{k: run[k] for k in fields[:6]}, "n_pairs": s["n_pairs"], "n_targets": s["n_targets"],
                             "success_original": s["original"]["success_rate"], "success_converted": s["converted"]["success_rate"],
                             "delta": s["delta"], "coverage_original": s["original"]["coverage"],
                             "coverage_converted": s["converted"]["coverage"], "paired_valid_n": s["paired_valid_n"],
                             "ci_low": s["ci95_target_cluster"][0], "ci_high": s["ci95_target_cluster"][1],
                             "median_displacement_px": s["displacement_median_px"],
                             "changed_images": len(run["inventory"]["changed_images"])})
    print(json.dumps({"runs": len(runs), "out": str(args.out),
                      "changed_image_records": sum(len(r["inventory"]["changed_images"]) for r in runs)}, indent=2))


if __name__ == "__main__":
    main()
