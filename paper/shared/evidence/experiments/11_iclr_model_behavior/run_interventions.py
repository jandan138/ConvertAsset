#!/usr/bin/env python3
"""Run reproducible paired probes, loading one model once and flushing each response.

Launch with the selected model's configured Python; --validate-only is CPU-only.
Use a fresh --out per run. --model-path can replace machine-local default paths.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--models", type=Path, default=HERE / "models.json")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-path")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit-pairs", type=int)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.models.read_text())
    model = dict(config["models"][args.model])
    if args.model_path:
        model["path"] = args.model_path
    records = json.loads(args.manifest.read_text())["scoring_records"]
    if args.limit_pairs:
        selected = list(dict.fromkeys(r["pair_id"] for r in records))[:args.limit_pairs]
        records = [r for r in records if r["pair_id"] in selected]
    for r in records:
        if not Path(r["image"]["path"]).is_file():
            raise ValueError(f"Missing image: {r['sample_id']}")
    if args.out.exists():
        raise ValueError("Use a fresh output directory")
    if args.validate_only:
        print(f"Validated {len(records)} records for {args.model}")
        return
    args.out.mkdir(parents=True)
    legacy = HERE.parent / "06_grscenes_vlm_grounding/run_vlm_predictions.py"
    snapshot = args.out / "runner_snapshot.py"
    shutil.copyfile(legacy, snapshot)
    spec = importlib.util.spec_from_file_location("frozen_vlm_engine", snapshot)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    # Model load and generation use a fixed environment and seed.
    import random
    import torch
    random.seed(config["decoding"]["seed"])
    torch.manual_seed(config["decoding"]["seed"])
    kwargs = dict(model_path=model["path"], temperature=0.0,
                  max_new_tokens=config["decoding"]["max_new_tokens"], dtype="bfloat16")
    if model["backend"] == "local_hf_generic":
        engine = runner.LocalHFGenericEngine(**kwargs, model_class=model.get("model_class"), attn_implementation="sdpa")
    elif model["backend"] == "local_hf_qwen":
        engine = runner.LocalHFQwenEngine(**kwargs, attn_implementation="eager")
    elif model["backend"] == "local_internvl_chat":
        engine = runner.LocalInternVLChatEngine(**kwargs)
    elif model["backend"] == "local_molmo":
        engine = runner.LocalMolmoEngine(**kwargs)
    else:
        engine = runner.LocalGemma4Engine(**kwargs, attn_implementation="eager")
    groups = {}
    for r in records:
        groups.setdefault(r.get("experiment", "canonical_refresh"), []).append(r)
    for family, rows in groups.items():
        path = args.out / f"{args.model}_{family}_predictions.jsonl"
        begin = time.time()
        with path.open("x") as f:
            for index, r in enumerate(rows):
                if "query_category" in r:
                    category = r["query_category"]
                    query = (f"The robot must {runner.S2_INTERACTION_ACTIONS.get(category, 'interact with the ' + category)}. "
                             if family == "two_view_action" else f"Locate the {category}. ")
                    prompt = ("The image contains two indoor views side by side. " + query +
                              "Point to the named object in whichever view contains it. "
                              "Use normalized 0-1000 coordinates over the ENTIRE image: "
                              "(0,0) is top left and (1000,1000) is bottom right. "
                              "Return exactly one line: Point: x, y")
                else:
                    prompt = runner.build_prompt(r, coordinate_frame="normalized_1000", response_format="structured_text")
                text = engine.generate(runner.build_messages(r, prompt))
                parsed = runner.parse_prediction_text(text, response_format="structured_text")
                result = dict(r)
                result["image"] = dict(r["image"], hash_sha256=sha(r["image"]["path"]))
                result["prompt"] = {"type": family, "coordinate_frame": "normalized_1000", "response_format": "structured_text", "text": prompt}
                result["prediction"] = {**parsed, "raw_text": text, "backend": model["backend"]}
                result["model_checkpoint"] = model["path"]
                result["decoding"] = config["decoding"]
                f.write(json.dumps(result) + "\n")
                f.flush()
                if index % 20 == 0:
                    print(f"{family}: {index+1}/{len(rows)}", flush=True)
        meta = {"schema_version": 1, "backend": model["backend"], "model_checkpoint": model["path"],
                "coordinate_frame": "normalized_1000", "response_format": "structured_text", "prompt_type": family,
                "prediction_count": len(rows), "elapsed_s": time.time() - begin, "decoding": config["decoding"],
                "manifest_sha256": sha(args.manifest), "prediction_sha256": sha(path),
                "runner_sha256": sha(snapshot), "orchestrator_sha256": sha(__file__),
                "python": sys.executable, "torch": torch.__version__,
                "transformers": __import__("transformers").__version__, "model_config": model}
        path.with_suffix(".jsonl.metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print("Run complete", flush=True)


if __name__ == "__main__":
    main()
