#!/usr/bin/env python3
"""Check ACL manuscript text for unsupported broad claims."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple
from typing import Mapping


GUARDRAIL_RE = re.compile(
    r"\b("
    r"not|no|never|without|cannot|does\s+not|do\s+not|should\s+not|"
    r"rather\s+than|instead\s+of|only|scoped|selected|bounded|"
    r"limitation|limited|sanity|not\s+yet|not\s+available|not\s+generated|"
    r"excluded|qualitative|not\s+quantitative|do\s+not\s+report|overclaim(?:ing)?"
    r")\b",
    re.IGNORECASE,
)


class ClaimBoundaryRule(NamedTuple):
    rule_id: str
    description: str
    pattern: re.Pattern[str]


RULES = (
    ClaimBoundaryRule(
        "broad_embodied_robustness",
        "Broad embodied-navigation robustness must be negated or scoped.",
        re.compile(
            r"\b(broad\s+(?:embodied(?:-navigation)?|grscenes|downstream)[^.?!;]*"
            r"robust(?:ness)?|establish(?:es|ed)?\s+broad\s+"
            r"embodied(?:-navigation)?\s+robustness)\b",
            re.IGNORECASE,
        ),
    ),
    ClaimBoundaryRule(
        "broad_benchmark",
        "Broad benchmark claims must be negated or scoped.",
        re.compile(r"\bbroad[^.?!;]*benchmark\b", re.IGNORECASE),
    ),
    ClaimBoundaryRule(
        "all_scene_robustness",
        "All-scene, InternNav/InteriorAgent, R2R/MP3D, or manipulation robustness must be negated.",
        re.compile(
            r"\b(all[\s-]?(?:GRScenes|InteriorNav|InternNav|InteriorAgent)|"
            r"R2R/MP3D|MP3D|manipulation)\b",
            re.IGNORECASE,
        ),
    ),
    ClaimBoundaryRule(
        "official_scene_speedup",
        "Official-scene speedup claims are unsupported.",
        re.compile(
            r"\b(official-scene[^.?!;]*speedup|noMDL[^.?!;]*speedup|"
            r"always\s+faster|faster\s+than)\b",
            re.IGNORECASE,
        ),
    ),
    ClaimBoundaryRule(
        "nvidia_official_scene_performance",
        "NVIDIA official-scene performance comparison is not available.",
        re.compile(
            r"\bNVIDIA\s+official-scene[^.?!;]*(?:performance|baseline|comparison|row)\b",
            re.IGNORECASE,
        ),
    ),
    ClaimBoundaryRule(
        "population_failure_rate",
        "Selected NVIDIA cases cannot be a population failure rate.",
        re.compile(r"\bpopulation[^.?!;]*failure\s+rate\b", re.IGNORECASE),
    ),
    ClaimBoundaryRule(
        "procedural_texture_success",
        "Procedural texture preservation success is unsupported.",
        re.compile(
            r"\bprocedural\s+texture[^.?!;]*(?:preserv|success|successful)\b",
            re.IGNORECASE,
        ),
    ),
    ClaimBoundaryRule(
        "learned_classifier",
        "A learned automatic classifier claim is unsupported.",
        re.compile(
            r"\b(?:learned|automatic)[^.?!;]*(?:classifier|recommender)\b",
            re.IGNORECASE,
        ),
    ),
)


UNSAFE_FIGURES = (
    {
        "rule_id": "unsafe_vlm_grounding_qualitative_panel",
        "description": "The current VLM grounding qualitative panel is not final-upload safe.",
        "figure": "fig_vlm_grounding_cases",
        "pattern": re.compile(r"figures/fig_vlm_grounding_cases\.(?:pdf|png)", re.IGNORECASE),
    },
    {
        "rule_id": "unsafe_material_effect_qualitative_panel",
        "description": "The material-effect qualitative panel requires clean original-MDL provenance.",
        "figure": "fig_material_effect_baseline_qualitative",
        "pattern": re.compile(r"figures/fig_material_effect_baseline_qualitative\.png", re.IGNORECASE),
        "allow_when_material_effect_clean_provenance_ready": True,
    },
)


VENUE_WRAPPER_PHRASES = (
    ClaimBoundaryRule(
        "acl_facing",
        "Main-paper prose should not describe evidence as ACL-facing.",
        re.compile(r"\bACL-facing\b", re.IGNORECASE),
    ),
    ClaimBoundaryRule(
        "main_acl_claim",
        "Main-paper prose should not refer to an internal main ACL claim.",
        re.compile(r"\bmain\s+ACL\s+claim\b", re.IGNORECASE),
    ),
    ClaimBoundaryRule(
        "acl_protocol",
        "The abstract should describe the protocol without venue-wrapper wording.",
        re.compile(r"\b(?:claim-bounded\s+)?ACL\s+protocol\b", re.IGNORECASE),
    ),
    ClaimBoundaryRule(
        "any_acl_submission",
        "Ethics prose should be venue-neutral inside the manuscript.",
        re.compile(r"\bAny\s+ACL\s+submission\b", re.IGNORECASE),
    ),
    ClaimBoundaryRule(
        "acl_arr_claim_boundary",
        "Main-paper table captions should not expose ACL/ARR wrapper wording.",
        re.compile(r"\bACL/ARR\s+claim\s+boundary\b", re.IGNORECASE),
    ),
)


def strip_latex(text: str) -> str:
    text = re.sub(r"(?m)%.*$", "", text)
    text = text.replace(r"\_", "_").replace(r"\,", " ")
    text = re.sub(r"\\cite\w*(?:\[[^\]]*\])*\{[^}]*\}", " ", text)
    text = re.sub(r"\\ref\{[^}]*\}", " ", text)
    text = re.sub(r"\\label\{[^}]*\}", " ", text)
    text = re.sub(r"\\input\{[^}]*\}", " ", text)
    text = re.sub(r"\\(?:begin|end)\{[^}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def split_claim_windows(text: str) -> list[str]:
    plain = strip_latex(text)
    pieces = re.split(r"(?<=[.?!])\s+|\n+", plain)
    return [piece.strip() for piece in pieces if piece.strip()]


def is_guardrailed(window: str) -> bool:
    return bool(GUARDRAIL_RE.search(window))


def find_claim_boundary_violations(text_by_path: Mapping[str, str]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path, text in sorted(text_by_path.items()):
        for window in split_claim_windows(text):
            for rule in RULES:
                if rule.pattern.search(window) and not is_guardrailed(window):
                    violations.append(
                        {
                            "path": path,
                            "rule_id": rule.rule_id,
                            "description": rule.description,
                            "text": window,
                        }
                    )
    return violations


def find_unsafe_figure_violations(
    text_by_path: Mapping[str, str],
    *,
    material_effect_clean_provenance_ready: bool = False,
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path, text in sorted(text_by_path.items()):
        for figure in UNSAFE_FIGURES:
            if figure["pattern"].search(text):
                if (
                    figure.get("allow_when_material_effect_clean_provenance_ready")
                    and material_effect_clean_provenance_ready
                ):
                    continue
                violations.append(
                    {
                        "path": path,
                        "rule_id": str(figure["rule_id"]),
                        "description": str(figure["description"]),
                        "figure": str(figure["figure"]),
                    }
                )
    return violations


def material_effect_clean_provenance_ready(paper_root: Path) -> bool:
    project_root = paper_root.parent
    script = (
        project_root
        / "paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py"
    )
    manifest = project_root / "paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json"
    if not script.is_file() or not manifest.is_file():
        return False

    spec = importlib.util.spec_from_file_location("material_effect_clean_provenance", script)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.check_qualitative_clean_provenance(
        json.loads(manifest.read_text(encoding="utf-8"))
    )
    return bool(report.get("ok"))


def find_venue_wrapper_phrasing_violations(text_by_path: Mapping[str, str]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path, text in sorted(text_by_path.items()):
        for window in split_claim_windows(text):
            for rule in VENUE_WRAPPER_PHRASES:
                if rule.pattern.search(window):
                    violations.append(
                        {
                            "path": path,
                            "rule_id": rule.rule_id,
                            "description": rule.description,
                            "text": window,
                        }
                    )
    return violations


def extract_latex_captions(text: str) -> str:
    captions = re.findall(r"\\caption\{([^{}]*)\}", text, flags=re.DOTALL)
    return "\n".join(captions)


def load_acl_claim_texts(paper_root: Path) -> dict[str, str]:
    venue_root = paper_root / "venues" / "acl27"
    paths = sorted((venue_root / "sections").glob("*.tex"))
    paths.append(paper_root / "shared" / "sections" / "appendix.tex")
    paths.append(venue_root / "OPENREVIEW_METADATA_PACKET.md")
    text_by_path = {
        str(path.relative_to(paper_root)): path.read_text(encoding="utf-8")
        for path in paths
    }
    for table_path in sorted((paper_root / "shared" / "tables").glob("tab_*.tex")):
        captions = extract_latex_captions(table_path.read_text(encoding="utf-8"))
        if captions:
            text_by_path[f"{table_path.relative_to(paper_root)}#captions"] = captions
    return text_by_path


def check_claim_boundaries(paper_root: Path) -> dict[str, object]:
    text_by_path = load_acl_claim_texts(paper_root)
    clean_material_effect_panel_ready = material_effect_clean_provenance_ready(paper_root)
    violations = find_claim_boundary_violations(text_by_path)
    unsafe_figure_violations = find_unsafe_figure_violations(
        text_by_path,
        material_effect_clean_provenance_ready=clean_material_effect_panel_ready,
    )
    venue_wrapper_violations = find_venue_wrapper_phrasing_violations(text_by_path)
    return {
        "ok": not violations and not unsafe_figure_violations and not venue_wrapper_violations,
        "checked_files": sorted(text_by_path),
        "material_effect_clean_provenance_ready": clean_material_effect_panel_ready,
        "violations": violations,
        "unsafe_figure_violations": unsafe_figure_violations,
        "venue_wrapper_violations": venue_wrapper_violations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paper-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Path to the paper root directory.",
    )
    args = parser.parse_args(argv)

    report = check_claim_boundaries(args.paper_root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
