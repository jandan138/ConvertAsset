#!/usr/bin/env python3
"""Stage a local ICLR candidate PDF and metadata after consistency checks."""
import hashlib
import csv
import json
import shutil
from pathlib import Path

VENUE = Path(__file__).resolve().parents[1]
PAPER = VENUE.parents[1]


def main():
    report = json.loads((VENUE / "build/check_report.json").read_text())
    pdf = VENUE / "build/main.pdf"
    if not report["artifact_checks_passed"] or hashlib.sha256(pdf.read_bytes()).hexdigest() != report["pdf_sha256"]:
        raise ValueError("Run make iclr27-check on the current PDF first")
    out = PAPER / "submissions/iclr27_candidate"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, out / "main.pdf")
    shutil.copyfile(VENUE / "OPENREVIEW_METADATA.md", out / "metadata.md")
    # This summary has no machine paths or checkpoint locations.
    source = PAPER / "shared/evidence/raw/iclr_model_behavior/analysis_v1/results.csv"
    with source.open() as f:
        table = list(csv.DictReader(f))
    with (out / "experiment_results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    inventory = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.name in {"main.pdf", "metadata.md", "experiment_results.csv"}}
    (out / "manifest.json").write_text(json.dumps({"files": inventory, "status": "local_candidate_not_uploaded"}, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()
