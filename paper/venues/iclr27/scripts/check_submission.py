#!/usr/bin/env python3
"""Check ICLR artifact consistency and PDF structure, not defensive phrasing."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

VENUE = Path(__file__).resolve().parents[1]
ROOT = VENUE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    failures = []
    from appendix_render_sources import load_repaired_pairs
    try:
        repaired = load_repaired_pairs()
        spec = json.loads((VENUE / 'figures/supplement/figure-spec.json').read_text())
        for name, rows in (('appendix_grounding_diagnostics_01', repaired[:3]),
                           ('appendix_grounding_diagnostics_02', repaired[3:])):
            expected = {str(row[v].relative_to(ROOT)): sha(row[v])
                        for row in rows for v in ('original', 'converted')}
            actual = {a['source']: a['source_sha256'] for a in spec[name]['assets']}
            if actual != expected:
                failures.append(f'Appendix figure does not use approved repaired renders: {name}')
    except (OSError, ValueError, KeyError) as exc:
        failures.append(f'Appendix render validation: {exc}')
    template = json.loads((VENUE / "TEMPLATE_PROVENANCE.json").read_text())
    for path, expected in template["files"].items():
        if sha(VENUE / path) != expected:
            failures.append(f"Template modified: {path}")
    sources = json.loads((VENUE / "ASSET_PROVENANCE.json").read_text())
    if sha(ROOT / sources["results"]) != sources["results_sha256"]:
        failures.append("Analysis changed since asset generation")
    if sha(VENUE / "scripts/build_assets.py") != sources["generator_sha256"]:
        failures.append("Generator changed since asset generation")
    for path, expected in sources.get("generators", {}).items():
        if sha(VENUE / path) != expected:
            failures.append(f"Generator changed: {path}")
    for path, expected in sources.get("image_sources", {}).items():
        if sha(ROOT / path) != expected:
            failures.append(f"Figure source changed: {path}")
    for path, expected in sources["outputs"].items():
        if sha(VENUE / path) != expected:
            failures.append(f"Generated asset changed: {path}")
    title_match = re.search(r"\\title\{([^}]+)\}", (VENUE / "main.tex").read_text())
    title = " ".join(title_match.group(1).replace("\\\\", " ").split()) if title_match else ""
    metadata = (VENUE / "OPENREVIEW_METADATA.md").read_text()
    if not title or title not in metadata:
        failures.append("Manuscript and submission-copy titles differ")
    aux = (VENUE / "build/main.aux").read_text()
    for label, number in (("fig:system", 1), ("fig:overview", 2)):
        if f"\\newlabel{{{label}}}{{{{{number}}}" not in aux:
            failures.append(f"Expected retained figure numbering: {label} = {number}")
    match = re.search(r"\\newlabel\{page:main-end\}\{\{[^}]*\}\{(\d+)\}", aux)
    pages = int(match.group(1)) if match else None
    if pages is None or pages > 9:
        failures.append(f"Main-text end page must be <=9, got {pages}")
    log = (VENUE / "build/main.log").read_text(errors="replace")
    if re.search(r"undefined references|Citation .+ undefined|There were undefined|LaTeX Error", log):
        failures.append("LaTeX reference/citation/error diagnostics")
    text = subprocess.check_output(["pdftotext", "-layout", str(VENUE / "build/main.pdf"), "-"], text=True)
    for forbidden in ("/cpfs/", "/root/", "zhuzihou", "TODO", "[PLACEHOLDER]"):
        if forbidden in text:
            failures.append(f"PDF contains {forbidden}")
    compact = re.sub(r"\s+", "", text).lower()
    for required in ("ICLR 2027", "AI Use Statement", "Navigation", "References"):
        if re.sub(r"\s+", "", required).lower() not in compact:
            failures.append(f"Missing PDF section: {required}")
    results = json.loads((ROOT / sources["results"]).read_text())
    new = [r for r in results["runs"] if r["pool"] == "two_view_category"]
    if not new:
        failures.append("No completed new grounding experiment")
    if len(new) != 3:
        failures.append(f"Expected three complete clean-composition models, got {len(new)}")
    families = {"two_view_category", "two_view_action", "target_window", "context_window"}
    for model in {r["model"] for r in new}:
        completed = {r["pool"] for r in results["runs"] if r["model"] == model and r["pool"] in families}
        if completed != families:
            failures.append(f"Incomplete intervention matrix: {model}")
    for run in new:
        if any(run["inventory"].values()):
            failures.append(f"New experiment image mismatch: {run['id']}")
        if run["center_baseline"]["original"]["hit_n"] != 0:
            failures.append(f"Center baseline still solves two-view task: {run['id']}")
    report = {"artifact_checks_passed": not failures, "main_text_end_page": pages,
              "pdf_sha256": sha(VENUE / "build/main.pdf"), "failures": failures,
              "research_status": "candidate: fresh-scene scaling and matched-state navigation repeats remain in roadmap",
              "submission_status": "local_preparation_only"}
    (VENUE / "build/check_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
