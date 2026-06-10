# First-Page ACL Fit Audit

Checked: 2026-05-30.

This audit records the first-page hardening pass requested by
`ACL_REVIEWER_RISK_AUDIT.md`. It covers the title, abstract, opening
introduction paragraphs, and contribution list in the current ACL/ARR wrapper.

## Verdict

Pass for the current candidate draft, with a final human read still required
before upload.

The first screen now presents the work as a VLM grounding and embodied-data
reliability paper under controlled material perturbation. It does not present
the paper primarily as a ConvertAsset tool paper, a broad embodied-navigation
benchmark, or an NVIDIA comparison paper.

The current post-gate 2026-05-30 recheck covers the v18 11-page candidate PDF:

```text
paper/venues/acl27/build/main.pdf
sha256=177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356
pages=11
bytes=4066770
created=Sat May 30 20:25:01 2026 CST
```

The rendered first two pages were checked locally with the paper-figure visual
rubric during the post-gate full-PDF review. Page 1 keeps the title,
anonymous header, abstract, and opening introduction readable without overlap
or clipping. Page 2 keeps Figure 1, caption, four-gate paragraph, and
contribution list readable; the contribution list now flows after Figure 1
without a manual Introduction `\newpage`. No new imagegen iteration is needed
because the accepted v18 schematic remains visually serviceable and preserves
the exact `Target: box` label.

## Edits Made

The 2026-05-30 recheck removed a manual `\newpage` before the contribution
list in `sections/intro.tex`; the rendered first two pages still pass. The
2026-05-27 edits below remain the active first-page hardening changes:

- Retitled the paper from `Material Perturbations in Synthetic Scenes for
  Vision-Language Grounding Evaluation` to `Material Conversion as a Controlled
  Perturbation for Vision-Language Grounding in Synthetic 3D Scenes`.
- Refreshed the abstract sentence that previously led with `ConvertAsset`.
  The abstract now describes a composition-preserving conversion path and keeps
  the tool implementation implicit until the method/body.
- Updated `OPENREVIEW_METADATA_PACKET.md` so the OpenReview title and abstract
  match the manuscript.

## Claim Boundary Check

The first page still supports only bounded claims:

- proxy similarity is a screening gate, not task preservation proof;
- GRScenes clean evidence is a 15-pair pilot;
- GRScenes stress evidence is a frozen 30-pair target-centered stress set;
- Gemma4/Qwen results are protocol findings, not broad model rankings;
- NVIDIA evidence is selected and material-effect scoped;
- InternNav evidence is a scoped 99-episode official sanity run, not broad
  embodied robustness.

## Verification Commands

```bash
python - <<'PY'
from pathlib import Path
import re
text = Path('paper/venues/acl27/sections/abstract.tex').read_text()
text = re.sub(r'\\begin\{abstract\}|\\end\{abstract\}', ' ', text)
text = re.sub(r'\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^}]*\})?', ' ', text)
text = text.replace('\\,', ' ')
words = re.findall(r"[A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)*", text)
print(len(words))
PY
make -C paper clean-acl27 && make -C paper acl27
pdftotext -f 1 -l 2 paper/venues/acl27/build/main.pdf - | sed -n '1,160p'
pdftoppm -png -r 150 -f 1 -l 2 paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_visual_20260530_full2/page
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
```

Current 2026-05-30 verification result:

- abstract count: 183 words by the repository's conservative plain-text
  tokenizer;
- current build PDF remains the 11-page A4 v18 candidate with SHA-256
  `177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356`;
- rendered page hashes:
  - page 1:
    `811e00d49062b29a37e823b0752332e92abd13a31fb6aa69ad37474dbd1be237`;
  - page 2:
    `980f7931c141e6ae389421da30d5196f2e96a6f28f9b1d06e3c9b1f2bab05874`;
- first-page `pdftotext` extraction shows the current title, anonymous ACL
  header, refreshed abstract, opening VLM-grounding framing, and Figure 1
  caption;
- `check_claim_boundaries.py` passes;
- `check_metadata_consistency.py` passes.
