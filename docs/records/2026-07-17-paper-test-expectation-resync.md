# 2026-07-17 Paper Test Expectation Resync After ACL27 Consolidation

## Why this record exists

The full pytest suite had 5 failing tests, all in the paper evidence lane.
Root cause: the 2026-06-10 `chore(paper): consolidate acl27 submission
package` commit rewrote checked-in ACL27 LaTeX artifacts and two evidence
generators, but four test expectations and one generator were left at the
pre-consolidation wording. The checked-in submission artifacts are
authoritative; this change resyncs the stale sides.

## Changes

| File | Change |
|---|---|
| `paper/shared/tables/gen_vlm_pilot_tables.py` | Header `Note / boundary` -> `Note / scope`, matching the checked-in `tab_grscenes_vlm_pass_only_pilot.tex` (generator was not updated by the consolidation commit; the artifact was) |
| `tests/test_grscenes_vlm_stress_expanded30_tables.py` | Caption assertion -> `Frozen 30-pair GRScenes material-shift stress set` (matches generator, checked-in tex, and `venues/acl27/build/main.aux`) |
| `tests/test_internnav_rollout_figure.py` | Caption/limitations assertions updated to the consolidated wording: `trajectory overlays for orientation only`, `Quantitative stack-entry measurements remain tied to the 99-episode paired run`, `The rollout panel only orients readers.`, `Load/render measures stability only, not speedup`; negative assertions unchanged |
| `tests/test_reviewer_closure_package.py` | `paired bootstrap confidence intervals` -> `Paired bootstrap confidence intervals` (sentence-case caption) |
| `tests/test_official_scene_submission_closure.py` | `NVIDIA official-scene baseline is omitted` -> `NVIDIA official-scene row is omitted` |

No paper content, evidence, or claim boundary changed; this is a
wording-level resync of tests and one generator against the frozen
submission artifacts.

## Verification

- `python -m pytest tests/ -q` -> `660 passed, 4 skipped` (was 5 failed,
  655 passed, 4 skipped before this change)

## Open issues

None. If a future paper revision intentionally rewrites these captions,
update the generator, the checked-in tex, and the test expectation in the
same commit to avoid this drift pattern.
