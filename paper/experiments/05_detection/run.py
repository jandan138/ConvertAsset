#!/usr/bin/env python3
"""Experiment #4a: Zero-shot Detection Confidence using YOLOv8n.

No Isaac Sim needed. Uses rendered image pairs from Experiment #0.

Usage:
    pip install ultralytics
    python paper/experiments/05_detection/run.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RENDERS_DIR = PROJECT_ROOT / "paper" / "results" / "raw" / "renders"
OUTPUT_JSON = PROJECT_ROOT / "paper" / "results" / "raw" / "detection_results.json"

SCENE_IDS = [
    "chestofdrawers_0004",
    "chestofdrawers_0011",
    "chestofdrawers_0023",
    "chestofdrawers_0029",
]

ANGLES = ["front", "back", "left", "right", "top_front_left", "top_front_right"]


def main():
    from ultralytics import YOLO

    print("[Exp#4a] Loading YOLOv8n...")
    model = YOLO("yolov8n.pt")

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    results_data = {"metadata": {"model": "yolov8n", "scenes": SCENE_IDS, "angles": ANGLES}, "detections": []}

    for scene_id in SCENE_IDS:
        scene_dir = RENDERS_DIR / scene_id

        for version_label in ["A", "B"]:
            for angle in ANGLES:
                img_path = scene_dir / f"{version_label}_{angle}.png"
                if not img_path.exists():
                    print(f"[WARN] Missing: {img_path}")
                    continue

                # Run detection
                det_results = model(str(img_path), verbose=False)

                num_detections = 0
                confidences = []

                for r in det_results:
                    boxes = r.boxes
                    if boxes is not None and len(boxes) > 0:
                        confs = boxes.conf.cpu().numpy().tolist()
                        num_detections += len(confs)
                        confidences.extend(confs)

                entry = {
                    "scene_id": scene_id,
                    "version": version_label,
                    "angle": angle,
                    "num_detections": num_detections,
                    "mean_confidence": round(float(np.mean(confidences)), 6) if confidences else 0.0,
                    "max_confidence": round(float(np.max(confidences)), 6) if confidences else 0.0,
                    "all_confidences": [round(c, 4) for c in confidences],
                }
                results_data["detections"].append(entry)
                print(
                    f"  {scene_id}/{version_label}_{angle}: "
                    f"n={num_detections}, mean_conf={entry['mean_confidence']:.4f}, max_conf={entry['max_confidence']:.4f}"
                )

    with open(str(OUTPUT_JSON), "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"\n[Exp#4a] Wrote results to {OUTPUT_JSON}")

    # Summary
    detections = results_data["detections"]
    for ver in ["A", "B"]:
        ver_data = [d for d in detections if d["version"] == ver]
        n_dets = [d["num_detections"] for d in ver_data]
        mean_confs = [d["mean_confidence"] for d in ver_data if d["num_detections"] > 0]
        max_confs = [d["max_confidence"] for d in ver_data if d["num_detections"] > 0]
        print(f"  Version {ver}: avg_detections={np.mean(n_dets):.1f}, "
              f"avg_mean_conf={np.mean(mean_confs):.4f} +/- {np.std(mean_confs):.4f}, "
              f"avg_max_conf={np.mean(max_confs):.4f}" if mean_confs else
              f"  Version {ver}: avg_detections={np.mean(n_dets):.1f}, no confident detections")

    return 0


if __name__ == "__main__":
    sys.exit(main())
