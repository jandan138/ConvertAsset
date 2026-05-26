# First-Page ACL Fit Audit

Checked: 2026-05-26.

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

## Edits Made

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
```

Current verification result:

- abstract count: 189 words by the repository's conservative plain-text
  tokenizer;
- clean ACL build succeeded and produced an 11-page A4 PDF;
- first-page `pdftotext` extraction shows the new title, anonymous ACL header,
  and refreshed abstract.
