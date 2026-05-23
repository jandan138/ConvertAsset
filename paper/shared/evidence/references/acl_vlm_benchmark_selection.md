# ACL VLM Benchmark Selection

Checked: 2026-05-23.

## Recommendation

Use **GRScenes-100 + PIO-style VLM grounding** as the primary ACL experiment
route. Use **InternNav / VL-LN** as the downstream navigation extension: a
one-episode smoke run now works, but it must scale before it can carry broad
paper claims.

This route is the best fit because the original GRScenes-100 benchmark package is available locally, is USD-native, contains MDL materials, and exposes object-level semantics that can be turned into language-grounding prompts. The PIO protocol gives us an ACL-shaped VLM evaluation target: ask a model to point to or identify the visual evidence needed for embodied reasoning, then compare original MDL renders against ConvertAsset no-MDL renders.

Important asset-role correction: the original package under `/cpfs/user/zhuzihou/assets/zzh-grscenes` is the benchmark source for ACL/VLM claims. The restored `test0_transitive_apply_parallel/dataset` mirror is only an engineering validation dataset for ConvertAsset smoke tests and runner debugging.

Local inventory checked on 2026-05-20 found 69 home scenes and 30 commercial scenes. The benchmark episode files cover 30 home scenes: `mm_episodes.json` has 420 episodes and `sn_episodes.json` has 300 episodes over the same scene set. Commercial scenes currently have no local `mm_episodes.json` / `sn_episodes.json` coverage, so they should be reported as metadata-driven material stress tests unless a future episode source is added.

## Candidate Comparison

| Candidate | USD asset fit | VLM / language fit | Reproduction cost | Decision |
|---|---|---|---|---|
| GRScenes-100 + PIO-style protocol | Strong: original local USD benchmark package with MDL materials | Strong if we generate referred-object and task-driven grounding prompts | Low-medium: uses official GRScenes source plus local engineering mirror for smoke tests | Primary ACL experiment |
| InternNav / VL-LN | Strong via InternUtopia / Isaac Sim / GRScenes ecosystem | Strong: dialog-enabled navigation and language-conditioned goals | Medium: heavier simulator and navigation stack; one-episode smoke is reproducible, aggregate run still pending | Secondary downstream extension |
| BEHAVIOR-1K / OmniGibson | Strong Omniverse/Isaac Sim family | Strong household tasks and manipulation | Medium-high: larger install/runtime surface | Optional future extension |
| OpenEQA-style embodied QA | Weak for this repo unless we re-render our own assets | Strong VLM embodied QA framing | Medium | Not primary |
| ChaChaBench / OmniGibson video VLM | Indirect | VLM video reasoning | Medium | Not primary because the metric is motion/video, not material-grounded object recognition |

## Selected Experiment Framing

Research question:

> How do controlled USD material and texture transformations affect VLM grounding and language-conditioned embodied decisions in realistic indoor scenes?

Minimum pilot:

1. Select 5 episode-backed home scenes from the 30-scene `mm_episodes.json` / `sn_episodes.json` pool, plus 5 commercial scenes only for metadata-driven material stress tests.
2. Copy each selected benchmark scene into a scratch work tree, then run ConvertAsset no-MDL on the scratch copy to create matched original / converted conditions.
3. Render matched camera views around semantic object prims.
4. Generate PIO-style prompts:
   - S1 referred-object localization, such as "Point to the wooden cabinet."
   - S2 task-driven grounding, such as "Where would the robot grasp to open the drawer?"
   - S3 navigation proxy, such as "Which object should the robot move toward to sit down?"
5. Run open VLMs that support point or coordinate outputs where available, with Qwen2.5-VL / Molmo-style models as first candidates.
6. Score original-vs-converted deltas with point-in-box or point-in-mask accuracy, answer consistency, and per-category failure analysis.

The original condition should come from `start_result_raw.usd`, `start_result_navigation.usd`, or `start_result_interaction.usd`, depending on the task. Generated no-MDL derivatives must not be written into the benchmark source tree. PIO should be described as prompt and metric inspiration unless the experiment later imports the PIO dataset directly.

## Why This Is ACL-Shaped

The contribution becomes a controlled diagnostic benchmark for multimodal language grounding under asset material transformations. The claim is no longer only "USD conversion is faster." It becomes: "material simplification can be measured as a language-grounding distribution shift for embodied VLMs, and the failure modes are predictable by object/material/task category."

## External Sources

- GRScenes-100 dataset card: https://huggingface.co/datasets/InternRobotics/GRScenes
- InternNav repository: https://github.com/InternRobotics/InternNav
- InternNav VL-LN benchmark docs: https://internrobotics.github.io/user_guide/internnav/projects/benchmark.html
- PIO project page: https://research.nvidia.com/labs/cosmos-lab/pio/
- PIO dataset card: https://huggingface.co/datasets/pio-benchmark/PIO
- BEHAVIOR-1K overview: https://behavior.stanford.edu/
