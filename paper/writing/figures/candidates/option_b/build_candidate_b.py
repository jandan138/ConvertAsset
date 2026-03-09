#!/usr/bin/env python3
"""Build methodology figure candidate B from the AutoFigure final SVG."""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import cairosvg


ROOT = Path("/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset")
SRC_SVG = ROOT / "paper/writing/figures/final_run/final.svg"
OUT_DIR = ROOT / "paper/writing/figures/candidates/option_b"
STEM = "fig_method_pipeline_candidate_b"
OUT_SVG = OUT_DIR / f"{STEM}.svg"
OUT_PDF = OUT_DIR / f"{STEM}.pdf"
OUT_PNG = OUT_DIR / f"{STEM}.png"


OVERLAY_STYLE = textwrap.dedent(
    """
      <style>
        .cb-stage-title {
          font-family: Georgia, serif;
          font-size: 30px;
          font-weight: 700;
          fill: #132433;
          text-anchor: middle;
        }
        .cb-stage-subtitle {
          font-family: Arial, sans-serif;
          font-size: 13px;
          font-weight: 600;
          fill: #4d6474;
          text-anchor: middle;
        }
        .cb-chip {
          fill: #ffffff;
          fill-opacity: 0.94;
          stroke: #8fa1af;
          stroke-width: 1.1;
          rx: 9;
        }
        .cb-chip-text {
          font-family: Arial, sans-serif;
          font-size: 16px;
          font-weight: 600;
          fill: #22313b;
          text-anchor: middle;
          dominant-baseline: middle;
        }
        .cb-chip-text-small {
          font-family: Arial, sans-serif;
          font-size: 14px;
          font-weight: 600;
          fill: #22313b;
          text-anchor: middle;
          dominant-baseline: middle;
        }
        .cb-box {
          fill: #fdfdfd;
          stroke: #8fa1af;
          stroke-width: 1.2;
          rx: 11;
        }
        .cb-box-text {
          font-family: Arial, sans-serif;
          font-size: 17px;
          font-weight: 600;
          fill: #22313b;
          text-anchor: middle;
          dominant-baseline: middle;
        }
      </style>
    """
).strip()


OVERLAY_GROUP = textwrap.dedent(
    """
    <g id="candidate-b-curation">
      <!-- Title refresh -->
      <rect x="25" y="50" width="555" height="88" fill="#dae8fc" />
      <rect x="605" y="50" width="595" height="88" fill="#d5e8d4" />
      <rect x="1225" y="50" width="360" height="88" fill="#fff2cc" />

      <text x="302" y="86" class="cb-stage-title">Stage 1: USD Traversal</text>
      <text x="302" y="112" class="cb-stage-subtitle">Collect composition dependencies without flattening</text>

      <text x="902" y="86" class="cb-stage-title">Stage 2: Material Conversion</text>
      <text x="902" y="112" class="cb-stage-subtitle">Translate MDL to UsdPreviewSurface, then clean up</text>

      <text x="1405" y="86" class="cb-stage-title">Stage 3: Path Rewriting</text>
      <text x="1405" y="112" class="cb-stage-subtitle">Rewrite sibling outputs while preserving the USD hierarchy</text>

      <!-- Stage 1 dependency categories -->
      <rect x="338" y="125" width="138" height="34" class="cb-chip" />
      <text x="407" y="142" class="cb-chip-text-small">Sublayers</text>

      <rect x="338" y="169" width="138" height="34" class="cb-chip" />
      <text x="407" y="186" class="cb-chip-text-small">References</text>

      <rect x="338" y="213" width="138" height="34" class="cb-chip" />
      <text x="407" y="230" class="cb-chip-text-small">Payloads</text>

      <rect x="338" y="257" width="138" height="40" class="cb-chip" />
      <text x="407" y="274" class="cb-chip-text-small">Variant</text>
      <text x="407" y="290" class="cb-chip-text-small">selections</text>

      <rect x="338" y="305" width="138" height="34" class="cb-chip" />
      <text x="407" y="322" class="cb-chip-text-small">Value clips</text>

      <!-- Stage 1 cleanup wording -->
      <rect x="160" y="558" width="128" height="48" class="cb-chip" />
      <text x="224" y="576" class="cb-chip-text-small">Cycle</text>
      <text x="224" y="592" class="cb-chip-text-small">detection</text>

      <rect x="307" y="558" width="128" height="48" class="cb-chip" />
      <text x="371" y="576" class="cb-chip-text-small">Dedup-</text>
      <text x="371" y="592" class="cb-chip-text-small">lication</text>

      <!-- Stage 2 cleanup wording -->
      <rect x="1088" y="378" width="104" height="56" fill="#d5e8d4" />
      <rect x="1091" y="387" width="98" height="42" class="cb-chip" />
      <text x="1140" y="403" class="cb-chip-text-small">Converted</text>
      <text x="1140" y="419" class="cb-chip-text-small">files</text>

      <rect x="928" y="552" width="128" height="52" class="cb-chip" />
      <text x="992" y="571" class="cb-chip-text-small">Clean up MDL</text>
      <text x="992" y="589" class="cb-chip-text-small">outputs &amp; prims</text>

      <!-- Stage 3 semantic relabeling -->
      <rect x="1258" y="209" width="124" height="42" class="cb-chip" />
      <text x="1320" y="226" class="cb-chip-text-small">Composition</text>
      <text x="1320" y="242" class="cb-chip-text-small">arcs</text>

      <rect x="1228" y="404" width="184" height="60" fill="#fff2cc" />
      <rect x="1240" y="412" width="154" height="44" class="cb-chip" />
      <text x="1317" y="435" class="cb-chip-text-small">Rewrite</text>
      <text x="1317" y="451" class="cb-chip-text-small">composition arcs</text>

      <rect x="1238" y="462" width="174" height="92" fill="#fff2cc" />
      <rect x="1244" y="476" width="160" height="72" class="cb-box" />
      <text x="1324" y="499" class="cb-box-text">Target:</text>
      <text x="1324" y="522" class="cb-box-text">*_noMDL.usd</text>

      <rect x="1434" y="388" width="118" height="58" fill="#fff2cc" />
      <rect x="1438" y="392" width="112" height="48" class="cb-chip" />
      <text x="1494" y="409" class="cb-chip-text-small">Converted USD</text>
      <text x="1494" y="425" class="cb-chip-text-small">hierarchy</text>
    </g>
    """
).strip()


def build_svg() -> str:
    svg = SRC_SVG.read_text(encoding="utf-8")
    svg = re.sub(
        r'<svg width="1593" height="672" viewBox="0 0 1593 672"',
        '<svg width="1660" height="672" viewBox="0 0 1660 672"',
        svg,
        count=1,
    )
    svg = svg.replace("</defs>", f"{OVERLAY_STYLE}\n  </defs>", 1)
    svg = svg.replace(
        "</defs>\n\n  <!-- Background Stages -->",
        "</defs>\n\n  <rect x=\"0\" y=\"0\" width=\"1660\" height=\"672\" fill=\"#ffffff\" />\n\n  <!-- Background Stages -->",
        1,
    )
    svg = svg.replace("</svg>", f"{OVERLAY_GROUP}\n\n</svg>", 1)
    return svg


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg = build_svg()
    OUT_SVG.write_text(svg, encoding="utf-8")

    cairosvg.svg2pdf(url=str(OUT_SVG), write_to=str(OUT_PDF))
    cairosvg.svg2png(
        url=str(OUT_SVG),
        write_to=str(OUT_PNG),
        output_width=1660,
        output_height=672,
    )


if __name__ == "__main__":
    main()
