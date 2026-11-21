#!/usr/bin/env python3
"""Fresh RTX paired renders with a fixed off-axis camera, in a new output tree.

Run under Isaac Python (PXR for camera authoring; each capture gets its own
SimulationApp subprocess). Timeouts/errors remain explicit in report.json.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import signal
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding/stress_vlm_run_manifest_expanded30.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--limit-targets", type=int)
    parser.add_argument("--shift", type=float, default=0.18)
    args = parser.parse_args()
    from pxr import Usd, UsdGeom
    from PIL import Image
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out / "report.json").exists():
        raise ValueError("Fresh output required")
    data = json.loads(SOURCE.read_text())
    pairs = {}
    for r in data["scoring_records"]:
        pairs.setdefault(r["pair_id"], {})[r["version"]] = r
    selected = {}
    for key in sorted(pairs):
        selected.setdefault(key.split(".")[0], key)
    keys = list(selected.values())[:args.limit_targets]
    report = {"records": [], "selected_pairs": keys, "horizontal_shift_fraction": args.shift}
    completed = []
    for key in keys:
        pair_rows = []
        for version in ("original", "converted"):
            r = copy.deepcopy(pairs[key][version])
            original_stage = Path(r["image"]["path"]).parent / f"{version}_camera.usd"
            folder = args.out / key / version
            folder.mkdir(parents=True)
            stage_path = folder / "camera.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            stage.GetRootLayer().subLayerPaths = [str(original_stage)]
            camera = UsdGeom.Camera(stage.GetPrimAtPath("/World/GRScenesVLMTargetCamera"))
            if not camera:
                raise ValueError(f"Missing camera: {original_stage}")
            aperture = camera.GetHorizontalApertureAttr().Get()
            prior = camera.GetHorizontalApertureOffsetAttr().Get() or 0.0
            camera.CreateHorizontalApertureOffsetAttr().Set(prior + args.shift * aperture)
            stage.GetRootLayer().Save()
            del stage
            command = [str(ROOT / "scripts/isaac_python.sh"), str(ROOT / "scripts/render_with_viewport_capture.py"),
                       "--usd-path", str(stage_path), "--camera", "/World/GRScenesVLMTargetCamera",
                       "--output-dir", str(folder), "--prefix", "frame", "--ext", "png",
                       "--width", str(r["image"]["width"]), "--height", str(r["image"]["height"]),
                       "--start-frame", "0", "--end-frame", "0", "--wait-frames", "16", "--headless"]
            log_path = folder / "render.log"
            with log_path.open("w") as log:
                process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    code = process.wait(timeout=args.timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    code = "timeout"
            text = log_path.read_text(errors="replace")
            failures = {s: text.count(s) for s in ("Failed to create MDL", "MDL compiler error")}
            image_path = folder / "frame_0000.png"
            ok = code == 0 and image_path.is_file() and not any(failures.values())
            record = {"pair": key, "version": version, "command": command, "return_code": code,
                      "log": str(log_path), "material_error_terms": failures, "capture_ready": ok}
            report["records"].append(record)
            if ok:
                with Image.open(image_path) as im:
                    w, h = im.size
                # Changing film offset translates projections by -shift*width.
                dx = -args.shift * w
                box = r["target"]["bbox_xyxy"]
                r["target"]["bbox_xyxy"] = [box[0]+dx, box[1], box[2]+dx, box[3]]
                r["pair_id"] = f"{key}.offaxis"
                r["sample_id"] = f"{r['pair_id']}.{version}"
                r["cluster_id"] = key.split(".")[0]
                r["experiment"] = "offaxis_rtx"
                r["image"] = {"path": str(image_path), "width": w, "height": h,
                              "hash_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest()}
                r["render_log"] = str(log_path)
                r["prediction"] = None
                pair_rows.append(r)
            print(f"{key} {version}: {code}, ready={ok}", flush=True)
            (args.out / "report.json").write_text(json.dumps(report, indent=2))
        if len(pair_rows) == 2:
            completed.extend(pair_rows)
        (args.out / "manifest.json").write_text(json.dumps({"schema_version": 1,
                "source_manifest": str(SOURCE), "scoring_records": completed,
                "visual_review_status": "pending", "report": str(args.out / "report.json")}, indent=2))
    print(f"Complete: {len(completed)//2}/{len(keys)} pairs", flush=True)


if __name__ == "__main__":
    main()
