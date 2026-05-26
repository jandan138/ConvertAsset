# GRScenes MDL Import Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the GRScenes VLM evidence scratch asset set so original-condition MDL renders no longer fail on `KooPbr` / `KooPbr_maps` absolute imports.

**Architecture:** Add a repo-tracked, pure-Python repair utility that rewrites known GRScenes generated MDL import lines from absolute `import ::...;` form to relative `using .::... import ...;` form, with dry-run/apply modes and JSON reporting. Apply it to the ACL GRScenes no-MDL scratch asset root, then rerender or revalidate the Fig.1 source cases before treating the qualitative panel as final evidence.

**Tech Stack:** Python stdlib, pytest, existing Isaac render wrapper for final smoke.

---

### Task 1: Script Behavior Tests

**Files:**
- Create: `tests/test_fix_mdl_absolute_imports.py`
- Later create: `scripts/fix_mdl_absolute_imports.py`

- [x] **Step 1: Write failing tests**

Add tests that verify:

```python
from scripts.fix_mdl_absolute_imports import repair_text, should_process_mdl


def test_repair_text_rewrites_koopbr_imports():
    text = "import ::KooPbr::KooMtl;\\nimport ::KooPbr_maps::KooPbr_bitmap;\\n"
    repaired, replacements = repair_text(text)
    assert "using .::KooPbr import KooMtl;" in repaired
    assert "using .::KooPbr_maps import KooPbr_bitmap;" in repaired
    assert replacements == 2


def test_should_process_only_generated_material_instances():
    assert should_process_mdl("MI_6576cd34ade22a0001b5739d.mdl")
    assert should_process_mdl("abcdef0123456789abcdef0123456789.mdl")
    assert not should_process_mdl("KooPbr.mdl")
    assert not should_process_mdl("KooPbr_maps.mdl")
    assert not should_process_mdl("Num12.mdl")
    assert not should_process_mdl("OmniUe4Base.mdl")
```

- [x] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest -q tests/test_fix_mdl_absolute_imports.py -q
```

Expected: import failure because `scripts/fix_mdl_absolute_imports.py` does not exist yet.

### Task 2: Repair Utility

**Files:**
- Create: `scripts/fix_mdl_absolute_imports.py`

- [x] **Step 1: Implement minimal script**

Implement:

- `repair_text(text: str) -> tuple[str, int]`
- `should_process_mdl(name_or_path: str) -> bool`
- recursive `.mdl` discovery under one or more roots
- `--dry-run` default, `--apply` opt-in
- `--follow-symlinks` opt-in
- `--report PATH` JSON output
- atomic write via temp file + `Path.replace`

- [x] **Step 2: Run unit tests and verify GREEN**

Run:

```bash
python -m pytest -q tests/test_fix_mdl_absolute_imports.py -q
```

Expected: pass.

### Task 3: Dry-Run The ACL Scratch Asset Set

**Files:**
- External report output:
  `paper/shared/evidence/raw/grscene_vlm_grounding/mdl_import_fix_dryrun_20260526.json`

- [x] **Step 1: Run dry-run**

Run:

```bash
python scripts/fix_mdl_absolute_imports.py \
  /cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes \
  --follow-symlinks \
  --report paper/shared/evidence/raw/grscene_vlm_grounding/mdl_import_fix_dryrun_20260526.json
```

Expected: nonzero candidate files and replacements; `applied=false`.

- [x] **Step 2: Spot-check source-protection risk**

Run `stat` before/after on at least one known hardlinked source/scratch pair.
Because the script writes atomically, applying through the scratch path should
replace only the scratch directory entry and reduce the old hardlink count,
not mutate the original source file contents.

### Task 4: Apply Repair To Scratch Asset Set

**Files:**
- External assets under:
  `/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes`
- Report:
  `paper/shared/evidence/raw/grscene_vlm_grounding/mdl_import_fix_apply_20260526.json`

- [x] **Step 1: Apply**

Run the same command with `--apply`.

- [x] **Step 2: Verify import patterns**

Run targeted `rg` checks on the Fig.1 scene/material paths:

```bash
rg -n "import ::KooPbr|import ::KooPbr_maps" <scratch-root> -g "*.mdl"
rg -n "using \\.::KooPbr|using \\.::KooPbr_maps" <scratch-root> -g "*.mdl"
```

Expected: no generated material-instance files in the repaired scratch root
still use the old `import ::KooPbr` / `import ::KooPbr_maps` lines.

### Task 5: Rerender Fig.1 Source Cases

**Files:**
- Reuse the four existing report commands from:
  - `paper/shared/evidence/raw/grscene_vlm_grounding/retake_paired_render_reports/21dde4a14ca93f539a47.retake_008.json`
  - `paper/shared/evidence/raw/grscene_vlm_grounding/paired_render_smoke_report.json`
  - `paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/47aa36277a54f6ca90cc.zoom_018.json`
  - `paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/c8ee4b66274b05d242c2.zoom_017.json`

- [ ] **Step 1: Rerun paired render smoke reports**

Status on 2026-05-26: the first selected pair
`c27086f557d316584264.view_001` was rerun after the MDL import and pointer
repairs. The repaired original-condition stderr no longer showed the checked
MDL-resolution error terms, but the headless viewport capture timed out at
1800 seconds after opening the stage and binding the camera. A direct converted
capture probe for the same view succeeded in about 226 seconds; a direct
original capture probe timed out at 300 seconds. Do not mark this step complete
until a reliable original-condition capture path exists.

Run the existing `run_paired_render_smoke.py` commands for the four pair IDs,
writing replacement JSON reports and logs to the existing evidence locations.

- [ ] **Step 2: Verify MDL errors are gone**

Partial status: checked stderr for `c27086f557d316584264.view_001` contained no
`KooPbr`, `KooPbr_maps`, `could not find module`, or `Failed to create MDL shade
node`, but the render command did not complete, so this is not final evidence.

Parse the new reports and require each selected original render to have:

```text
KooPbr == 0
KooPbr_maps == 0
Failed to create MDL shade node == 0
```

### Task 6: Figure And Documentation Refresh

**Files:**
- Regenerate: `paper/shared/figures/fig_vlm_grounding_cases.png`
- Regenerate: `paper/shared/figures/fig_vlm_grounding_cases.pdf`
- Modify: `docs/records/2026-05-26-acl-fig1-red-material-root-cause.md`
- Possibly modify: `paper/venues/acl27/STATUS.md`
- Possibly modify: `paper/venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md`

- [ ] **Step 1: Rerun or revalidate VLM overlay provenance**

If rerendered images changed materially, rerun the selected VLM predictions or
replace Fig.1 with clean-log cases whose predictions already match the exact
render files.

- [ ] **Step 2: Regenerate the qualitative panel**

Run:

```bash
python paper/shared/figures/gen_vlm_grounding_cases.py
make -C paper acl27
```

- [ ] **Step 3: Visual QA**

Render the Fig.1 PDF page and verify no obvious red fallback material remains
in the original-condition panels.
