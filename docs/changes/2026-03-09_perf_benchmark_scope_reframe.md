# 2026-03-09 Performance Benchmark Scope Reframe

## Context

This note records why Table 2 and the surrounding performance discussion were
rewritten to make a narrower, benchmark-scoped claim.

The trigger for the rewrite was a mismatch between what the current benchmark
actually measures and what the earlier paper wording implied. The existing
experiment is useful, but only for a specific workload:

- headless Isaac Sim execution
- four single-object furniture instance scenes
- load time measured as `open_stage` plus a fixed 30-update warm-up window
- three runs per scene and per version

That scope is materially narrower than interactive whole-scene startup in a
large composed Isaac Sim environment.

## Research / Investigation

The rewrite rationale was verified against the current paper text and benchmark
artifacts:

- `paper/experiments/02_perf_benchmark/run.py`
- `paper/results/raw/perf_benchmark.csv`
- `paper/writing/sections/methodology.tex`
- `paper/writing/sections/results.tex`
- `paper/writing/sections/discussion.tex`
- `paper/writing/sections/conclusion.tex`
- `paper/reviews/content_review.md`

Key observations:

- The raw CSV has only six columns:
  `scene_id`, `version`, `load_time_s`, `gpu_memory_mb`, `fps`, `run_id`.
- The benchmark script records exactly three runs per scene and labels run
  order through `run_id`, which is enough to separate first-pass cold-start
  behavior from subsequent warm runs.
- The script does not measure interactive stage readiness, peak memory during
  complex scene composition, or large-scene startup behavior.
- Review feedback had already flagged that the cold-start outlier
  (`chestofdrawers_0004`, MDL, run 1 at 1.33 s) dominates the variance and that
  the benchmark should be interpreted conservatively.

## Why Table 2 Needed Reframing

### 1. The current benchmark is not a whole-scene startup benchmark

The benchmark is a headless single-object benchmark, not a general scene-open
benchmark.

More specifically, it measures:

- `open_stage`
- a fixed 30-update post-open warm-up window
- post-load GPU memory
- steady-state FPS over a fixed frame window

It does **not** measure:

- interactive whole-scene startup on large composed Isaac Sim environments
- stage-readiness synchronization for complex referenced scenes
- startup behavior under many assets, many materials, or deep composition
- peak memory or latency across a materially diverse scene graph

The old phrasing risked reading as a claim about scene startup in general. The
new phrasing makes the measured scope explicit.

### 2. The current CSV supports cold-start vs warm-load separation, but not a "10x" claim

The existing raw data support a modest but important distinction:

- first-run cold-start load can differ noticeably between MDL and converted USD
- warm runs are effectively similar in this benchmark

This is because `run_id` allows the paper to separate:

- cold-start load: run 1 for each scene
- warm load: runs 2--3 for each scene

However, the data do **not** support a strong quantitative claim such as a
"10x" performance advantage, or any similar large-magnitude general efficiency
claim. Reasons include:

- only four scenes are included
- all scenes are shallow single-object furniture instances
- only three runs per scene are available
- the main load-time gap is driven by a first-run MDL initialization outlier,
  not by a stable per-scene throughput gap
- FPS and GPU memory are nearly identical once the benchmark is warm

The rewrite therefore moves away from broad or dramatic efficiency language and
toward a constrained statement that the benchmark reveals first-load behavior,
not a universal acceleration factor.

## Design Decision

The paper wording was reframed from a broad negative or universal statement
into a benchmark-scoped claim.

Old rhetorical risk:

- "no performance advantage"
- wording that readers could interpret as applying to conversion in general
- wording that could be read as ruling out gains in larger, more complex scenes

New intended claim:

- in the headless single-object benchmark used in this study, conversion does
  not show a clear steady-state FPS or GPU-memory advantage
- the observable difference is concentrated in first-load latency variability
- stronger claims about large-scene startup require a different benchmark

This wording is stricter scientifically because it distinguishes:

- what the current data actually establish
- what remains plausible but untested

## Paper Rewrite Guidance

The revised performance narrative should consistently do the following across
Table 2, Results, Discussion, and Conclusion:

- name the workload as a **headless single-object benchmark**
- explicitly separate **cold-start** and **warm-load** behavior
- avoid implying that the study benchmarked **whole-scene startup**
- avoid claims that conversion has **no performance advantage** in all settings
- replace broad claims with benchmark-scoped language tied to the measured
  workload

Recommended paper-level framing:

- The benchmark shows that under the tested single-object workload, steady-state
  FPS and GPU memory are similar between MDL and converted USD.
- The main measured difference is reduced first-load latency variability for
  the converted assets.
- Any claim about startup speedups in larger composed scenes requires a
  dedicated benchmark with explicit cache control, stage-readiness checks, and
  larger scene complexity.

## Code / Text Changes Documented

This note documents the already completed paper-facing rewrite in:

- `paper/writing/sections/methodology.tex`
- `paper/writing/sections/results.tex`
- `paper/writing/sections/discussion.tex`
- `paper/writing/sections/conclusion.tex`

The key text-level changes are:

- Table 2 caption now names the benchmark scope explicitly.
- Results text now distinguishes cold-start from warm-load behavior.
- Discussion now avoids presenting the study as evidence of a general
  rendering-efficiency result.
- Conclusion now states a benchmark-scoped takeaway instead of a general
  performance verdict.

## Validation

The validation commands that should accompany this rewrite are:

```bash
python - <<'PY'
import csv
from pathlib import Path
p = Path('paper/results/raw/perf_benchmark.csv')
with p.open() as f:
    rows = list(csv.DictReader(f))
print('rows', len(rows))
print('columns', rows[0].keys())
print('cold_rows', sum(1 for r in rows if r['run_id'] == '1'))
print('warm_rows', sum(1 for r in rows if r['run_id'] in {'2', '3'}))
PY
```

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

If a camera-ready pass is being prepared, run `pdflatex` enough times to
stabilize references after any text/table edits.

## Open Issues / Residual Risks

- The benchmark still has limited external validity because it covers only four
  single-object furniture scenes.
- Three runs per scene are enough for cold-vs-warm separation but not enough
  for strong quantitative efficiency claims.
- The benchmark currently logs post-load GPU memory, not true peak memory
  across scene-open and renderer initialization.
- Readers may still overgeneralize Table 2 unless the benchmark scope is
  repeated in the caption, results paragraph, and conclusion.
- A future large-scene benchmark should add explicit cache control, randomized
  version order, scene-readiness synchronization, and peak-memory logging.
