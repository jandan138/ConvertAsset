# ACL VLM Benchmark Selection

Checked: 2026-05-20.

## Recommendation

Use **GRScenes-100 + PIO-style VLM grounding** as the primary ACL experiment route. Use **InternNav / VL-LN** as the downstream navigation extension after the grounding pilot is working.

This route is the best fit because GRScenes-100 is already local in this project, is USD-native, contains MDL materials, and exposes object-level semantics that can be turned into language-grounding prompts. The PIO protocol gives us an ACL-shaped VLM evaluation target: ask a model to point to or identify the visual evidence needed for embodied reasoning, then compare original MDL renders against ConvertAsset no-MDL renders.

## Candidate Comparison

| Candidate | USD asset fit | VLM / language fit | Reproduction cost | Decision |
|---|---|---|---|---|
| GRScenes-100 + PIO-style protocol | Strong: local USD scenes with MDL materials | Strong if we generate referred-object and task-driven grounding prompts | Low: uses current dataset and ConvertAsset pipeline | Primary ACL experiment |
| InternNav / VL-LN | Strong via InternUtopia / Isaac Sim / GRScenes ecosystem | Strong: dialog-enabled navigation and language-conditioned goals | Medium: heavier simulator and navigation stack | Secondary downstream extension |
| BEHAVIOR-1K / OmniGibson | Strong Omniverse/Isaac Sim family | Strong household tasks and manipulation | Medium-high: larger install/runtime surface | Optional future extension |
| OpenEQA-style embodied QA | Weak for this repo unless we re-render our own assets | Strong VLM embodied QA framing | Medium | Not primary |
| ChaChaBench / OmniGibson video VLM | Indirect | VLM video reasoning | Medium | Not primary because the metric is motion/video, not material-grounded object recognition |

## Selected Experiment Framing

Research question:

> How do controlled USD material and texture transformations affect VLM grounding and language-conditioned embodied decisions in realistic indoor scenes?

Minimum pilot:

1. Select 5 home and 5 commercial GRScenes-100 scenes.
2. Convert each `layout.usd` with ConvertAsset no-MDL to create matched `layout.usd` / `layout_noMDL.usd` conditions.
3. Render matched camera views around semantic object prims.
4. Generate PIO-style prompts:
   - S1 referred-object localization, such as "Point to the wooden cabinet."
   - S2 task-driven grounding, such as "Where would the robot grasp to open the drawer?"
   - S3 navigation proxy, such as "Which object should the robot move toward to sit down?"
5. Run open VLMs that support point or coordinate outputs where available, with Qwen2.5-VL / Molmo-style models as first candidates.
6. Score original-vs-converted deltas with point-in-box or point-in-mask accuracy, answer consistency, and per-category failure analysis.

## Why This Is ACL-Shaped

The contribution becomes a controlled diagnostic benchmark for multimodal language grounding under asset material transformations. The claim is no longer only "USD conversion is faster." It becomes: "material simplification can be measured as a language-grounding distribution shift for embodied VLMs, and the failure modes are predictable by object/material/task category."

## External Sources

- GRScenes-100 dataset card: https://huggingface.co/datasets/InternRobotics/GRScenes
- InternNav repository: https://github.com/InternRobotics/InternNav
- InternNav VL-LN benchmark docs: https://internrobotics.github.io/user_guide/internnav/projects/benchmark.html
- PIO project page: https://research.nvidia.com/labs/cosmos-lab/pio/
- PIO dataset card: https://huggingface.co/datasets/pio-benchmark/PIO
- BEHAVIOR-1K overview: https://behavior.stanford.edu/
