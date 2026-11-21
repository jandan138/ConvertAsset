#!/usr/bin/env python3
"""Serial model campaign with model-specific environments and persistent logs."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=["qwen3vl2b", "qwen3vl8b", "gemma4"])
    parser.add_argument("--config", type=Path, default=HERE / "models.json")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for model in args.models:
        command = [config["models"][model]["python"], str(HERE / "run_interventions.py"),
                   "--models", str(args.config.resolve()), "--model", model,
                   "--manifest", str(args.manifest.resolve()), "--out", str(args.out / model)]
        log = args.out / f"{model}.log"
        with log.open("x") as handle:
            result = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, cwd=ROOT)
        results.append({"model": model, "command": command, "return_code": result.returncode, "log": str(log)})
        (args.out / "campaign.json").write_text(json.dumps(results, indent=2) + "\n")
        print(f"{model}: rc={result.returncode}", flush=True)
    if any(r["return_code"] != 0 for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
