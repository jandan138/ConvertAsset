# 2026-03-09 GRScenes Startup Benchmark

## Context

This change adds a supplemental large-scene startup benchmark to complement the
existing single-object performance benchmark in the paper.

The motivation was straightforward: the existing Table 2 benchmark measured
headless startup and steady-state rendering for four shallow single-object
furniture scenes, which did not reflect the much larger scene-open gap observed
in practice when loading full Isaac Sim environments.

To probe that user-facing startup regime, the benchmark uses the provided
GRScenes commercial interior:

- `start_result_interaction.usd`
- `start_result_interaction_noMDL.usd`

under:

- `/cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/GRScenes-test0/GRScenes100/commercial/MV4AFHQKTKJZ2AABAAAAADQ8_usd/`

## Research / Investigation

The benchmark design was chosen to answer a narrower but more relevant
question than the original microbenchmark:

- not "does noMDL improve steady-state FPS on a shallow asset instance?"
- but "how long does a large composed scene take to become fully warmed and
  ready to render in a fresh Isaac Sim process?"

Key observations from the raw runs:

- the pure `open_stage` segment is not the dominant cost in this scene
- the large gap appears during the first fixed post-open update window
- this means MDL overhead is expressed mainly through early-frame warmup and
  settling, not only through raw USD composition time

## Benchmark Implementation

New experiment script:

- `paper/experiments/02_perf_benchmark/run_grscene_startup.py`

New raw results:

- `paper/results/raw/perf_benchmark_grscene.csv`

The script runs in two modes:

- `batch`: orchestrates repeated fresh-process runs from the system Python
- `once`: runs inside Isaac Sim and measures a single scene load

Each trial:

1. launches a fresh headless Isaac Sim process
2. opens one of the two scene variants
3. measures:
   - `sim_init_s`
   - `open_ready_s`
   - `warmup_s`
   - `total_ready_s`
   - `gpu_memory_mb`
   - `script_wall_s`
4. writes one CSV row per run

The benchmark keeps the same 30-update post-open window used in the paper's
single-object benchmark so the two workloads remain comparable at the metric
definition level.

## Results Summary

Across 3 fresh-process runs per version:

- MDL `total_ready_s`: `52.02 ± 2.69`
- noMDL `total_ready_s`: `13.70 ± 1.01`
- relative reduction in time to a fully warmed ready-to-render state:
  `73.67%`
- multiplicative speedup in `total_ready_s`: `3.80x`
- MDL `gpu_memory_mb`: `5458.3 ± 125.9`
- noMDL `gpu_memory_mb`: `5259.0 ± 83.1`
- post-load GPU memory reduction: about `199 MB`

The decomposition is important:

- MDL `open_ready_s`: `1.12 ± 0.22`
- noMDL `open_ready_s`: `1.76 ± 0.08`
- MDL `warmup_s`: `50.90 ± 2.88`
- noMDL `warmup_s`: `11.94 ± 0.93`

So the performance gain does **not** come from a faster bare `open_stage`
segment. It comes from much faster post-open warmup in the noMDL scene.

## Paper Changes

The paper text was updated to reflect a workload-dependent performance story:

- `paper/writing/main.tex`
- `paper/writing/sections/methodology.tex`
- `paper/writing/sections/results.tex`
- `paper/writing/sections/discussion.tex`
- `paper/writing/sections/conclusion.tex`

Key narrative changes:

- the existing single-object benchmark remains in place as a shallow-scene
  steady-state benchmark
- a new supplemental GRScenes benchmark is added as a large-scene startup case
- a compact qualitative companion figure is added from representative GRScenes
  MDL/noMDL render pairs
- the qualitative figure is later tightened from 3 pairs to 2 stronger pairs
  (`orbit_01` and `orbit_03`) for better single-column readability
- the paper now states that performance effects are workload-dependent
- the large-scene result is described as a reduction in time to a fully warmed
  ready-to-render state, which is more precise than a blanket "startup faster"
  claim because `open_ready_s` alone does not improve
- the qualitative figure is explicitly framed as approximate-viewpoint support,
  not as a pixel-aligned fidelity comparison

## Validation

Commands used:

```bash
python paper/experiments/02_perf_benchmark/run_grscene_startup.py \
  --runs 3 \
  --output-csv paper/results/raw/perf_benchmark_grscene.csv
```

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Compilation succeeded and the updated paper PDF was regenerated.

## Residual Risks

- This supplemental benchmark uses exactly one large GRScenes scene, so it is a
  strong case study but not yet a broad survey of large-scene workloads.
- The measurements are headless; they are closer to automated pipeline startup
  than to manual GUI interaction.
- The benchmark reports post-load GPU memory, not true peak memory during the
  entire open and renderer-initialization sequence.
- Because `open_ready_s` and `total_ready_s` move in different directions, the
  paper should continue using the more precise phrase "fully warmed
  ready-to-render state" rather than a vague "startup time" label.
