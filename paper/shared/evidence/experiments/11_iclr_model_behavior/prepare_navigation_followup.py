#!/usr/bin/env python3
"""Prepare same-condition repeats and matched-state navigation probes.

Selection is hashed by scene/episode ID, independent of success transitions.
This prepares inputs only; it does not claim new rollouts were executed.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-scene", type=int, default=4)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--out", type=Path, default=ROOT / "paper/shared/evidence/raw/iclr_model_behavior/navigation_followup.json")
    args = parser.parse_args()
    source = ROOT / "paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/paired_episode_transitions.csv"
    rows = list(csv.DictReader(source.open()))
    cases = []
    for scene in sorted({r["scene_id"] for r in rows}):
        candidates = [r for r in rows if r["scene_id"] == scene]
        candidates.sort(key=lambda r: hashlib.sha256(f"20260915:{scene}:{r['path_key']}".encode()).hexdigest())
        for row in candidates[:args.per_scene]:
            cases.append({"scene_id": scene, "path_key": row["path_key"],
                          "conditions": ["original", "converted"], "repeat_seeds": list(range(args.repeats)),
                          "matched_state_probe": {"state": "identical episode start pose", "capture_camera": "agent RGB camera",
                              "measurements": ["target localization", "policy output", "first divergence state"]},
                          "status": "prepared_not_executed"})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"schema_version": 1, "status": "prepared_not_executed",
            "source": str(source.relative_to(ROOT)), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "selection": "smallest SHA-256 episode keys per scene, seed prefix 20260915; independent of outcome",
            "cases": cases, "planned_rollouts": len(cases)*2*args.repeats,
            "runtime_entry": "paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py",
            "required_before_execution": ["resolve official episode source and model checkpoint", "generate per-repeat configs and LMDBs",
                                          "match both conditions at identical camera/agent poses"]}, indent=2) + "\n")
    print(f"Prepared {len(cases)} paired episodes / {len(cases)*2*args.repeats} rollout jobs")


if __name__ == "__main__":
    main()
