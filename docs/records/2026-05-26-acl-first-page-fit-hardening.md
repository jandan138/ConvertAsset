# ACL First-Page Fit Hardening

Date: 2026-05-26.

## Summary

Hardened the ACL wrapper's first-page story after the reviewer-risk audit. The
title and abstract now make the VLM grounding / material-perturbation framing
more explicit and reduce tool-first wording.

## Files Updated

- `paper/venues/acl27/main.tex`
- `paper/venues/acl27/sections/abstract.tex`
- `paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md`
- `paper/venues/acl27/FIRST_PAGE_ACL_FIT_AUDIT.md`
- `paper/venues/acl27/SUBMISSION_READINESS_AUDIT.md`
- `paper/venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md`
- `paper/venues/acl27/STATUS.md`

## Decision

Use the title:

```text
Material Conversion as a Controlled Perturbation for Vision-Language Grounding in Synthetic 3D Scenes
```

The abstract keeps the same evidence numbers and claim boundary but replaces
the tool-first `ConvertAsset preserves...` sentence with a
composition-preserving conversion-path description.

## Verification

Verification performed:

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
python -m pytest -q tests/test_paper_layout.py tests/test_acl_submission_staging.py
python paper/venues/acl27/scripts/stage_submission_packet.py --force
rg -n "/cpfs|/home/|/root|zhuzihou|jandan138|github.com/jandan138|ConvertAsset.git" \
  paper/submissions/acl27_arr_candidate_20260526 || true
rg -n "Acknowledg|thanks|Acknowledgment" \
  paper/submissions/acl27_arr_candidate_20260526 || true
pdfinfo paper/submissions/acl27_arr_candidate_20260526/main.pdf
pdftotext paper/submissions/acl27_arr_candidate_20260526/main.pdf - | \
  rg -n "Material Conversion as a Controlled Perturbation|Anonymous ACL submission|Limitations|Ethical Considerations|References"
```

Results:

- abstract count: 189 words by the conservative tokenizer;
- `make -C paper clean-acl27 && make -C paper acl27`: pass, rebuilt
  `venues/acl27/build/main.pdf`;
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_submission_staging.py`:
  11 passed;
- final `main.log` unresolved citation/reference scan: no matches;
- staged packet regenerated with the safe five-file boundary;
- local path/private identifier scan: no matches;
- acknowledgment scan: no matches;
- `pdfinfo`: 11 pages, A4, PDF 1.5, 299433 bytes;
- `pdftotext`: found the new title, anonymous ACL header, `Limitations`,
  `Ethical Considerations`, and `References`.

## Remaining Work

This does not close the active ACL/ARR goal. The remaining gates are still
target-route lock, private author fields, official policy refresh, final
OpenReview form copy, and exact-packet anonymization scans.
