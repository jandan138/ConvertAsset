# ICLR 2027 Submission 23337 — official reviews (user-supplied transcript)

- Paper: **Same Scene, Different Decisions: Material Sensitivity in Embodied Models**
- Author shown in supplied submission metadata: Zihou Zhu, Shanghai Artificial Intelligence Laboratory.
- Source: the complete three-review text pasted by the user in this conversation; archived 2026-11-14.
- This is a transcription of supplied text, not a fresh OpenReview export. No forum URL or final decision was supplied or independently verified. “Clear rejection” below is a reviewer rating, not the conference decision.
- Review fields, dates, ratings, questions, reference list, spelling and wording are preserved. Web UI controls and repeated display headings outside review fields are omitted. Markdown headings/code fences are archival formatting.
- Reviewer statements (including paper descriptions and reference metadata) are not independently verified facts. In particular, the third review's statement about unchanged object colors must not be adopted as the experimental specification.
- Working responses and completion evidence belong in the [CVIU revision tracker](../../cviu/REVIEW_RESPONSE_TRACKER.md), not in the review text below.

## Reviewer zAz6

Official Review of Submission23337 by Reviewer zAz6

Official Reviewby Reviewer zAz605 Nov 2026, 05:55 (modified: 06 Nov 2026, 20:24)EveryoneRevisions

```text
Paper Summary:
The paper studies if changing the material representation of a 3d scene affects the decision of an embodied model while keeping the scene geometry fixed.

The authors investigate this through visual grounding experiments with several VLMs and closed-loop navigation experiments.

The main finding is that the overall aggregate performance can hide substantial changes in individual decisions. The grounding experiment further examine how output formats, object position, and changes to target affect the presentation.

Presentation: 1: Difficult to follow despite careful reading.
Informativeness: 2: I learned something interesting or useful.
Soundness: 1: I have significant concerns about the paper’s soundness that do not appear easy to address.
Critical Strengths:
this is an interesting probelm with strong prctical releveance. Different environments may have the same geometric structure but different materials. The consistency of embodied models across these enviorment is essential to the success the of the task,

some good eveluation provide usefull information beyond average accuracy, the controlled grounding experiments also attempt to separate different sources of variation.

Critical Weaknesses:
The biggest concern for this paper is that it primarily just observes changes in model decisions without proposing any solution to address the material sensitivity for embodied model or providing a deeper explanation of what causes these sensitivities. The main finding that individual predictions can change despite similar aggregate performance is somewhat expected. While this observation is interesting, there are limited methodological or theoretical insights. In my opinion, the novelty and significance of the contribution fall well below the bar for an ICLR-level conference.

The paper is also very difficult to follow, with several unconnected experiments and insufficient explanation of how the contributions relate to the central RQ of this paper. for example, sections 4 and 5 switch between material sensitivity, coordinate readout, and output format without clearly explaining how they relate. The connection between the grounding experiments and the downstream navigation results is also not well established.

Grounding experiments use only four source pairs, and navigation experiments lack repeated runs under identical conditions; there is no strong stats evidence to distinguish material sensitivity from runtime variability.

Questions For Authors:
The grounding experiments only use four pairs. Would the findings still hold with more objects and scenes? What caused such a small scale of experiments?

How much of the reported outcome change could simply come from randomness in the navigation process?

Flag For Ethics Review: No
Rating: 1: Clear rejection
Confidence: 2: I have broad familiarity with this field but little or no direct research experience on this topic.
```

## Reviewer GRGE

Official Review of Submission23337 by Reviewer GRGE

Official Reviewby Reviewer GRGE22 Oct 2026, 02:35 (modified: 06 Nov 2026, 20:24)EveryoneRevisions

```text
Paper Summary:
This paper appears to describe some focused tests of the ability of computer vision/AI systems to use verbal instructions (e.g., sentences) to make decisions about and navigate 3D rendered visual scenes across modest changes in material properties of the scenes. One prominent argument the paper makes is that overall decision performance may not be an ideal outcome measure, as a variety of specific stimuli result in different decision outcomes (e.g., some go from correct to incorrect with a change in material, while others change in the opposite direction). The paper seems to use relatively few pairs of rendered scenes for analyses and the justification for this choice is not made particularly clear. Details of the navigation experiments are poorly presented, so I cannot comment on this aspect of the work.

Presentation: 1: Difficult to follow despite careful reading.
Informativeness: 1: I learned little or nothing new from this paper.
Soundness: 2: I have minor or fixable concerns about the paper’s soundness.
Critical Strengths:
The paper appears to dedicate substantial effort to optimizing the pairs of scenes, though this results in a small number of tested scene pairs
Careful consideration of when model decisions change from correct/incorrect rather than overall changes in accuracy is an important focus that may enable new insights into the specific material property changes that are most impactful, which could guide design of computer vision systems supporting embodied agents
Critical Weaknesses:
The paper is very challenging to read and understand in its present form. Many of the acronyms are not defined, the rationale for the experiments is only briefly argued, and there is minimal discussion of how the static scene and navigation experiments are related
Navigation experiments in particular are not clearly described, and the data presented are not interpreted in a way that is useful for the broad audience expected for submissions to this venue
It appears that only a very, very narrow set of stimulus pairs is used throughout. Given that these pairs appear to be systematically and automatically generated, it’s unclear why only a small number are chosen. One would expect millions of pairwise comparisons rather than dozens. Though I highlight that characterizing changes to decisions (rather than changes to accuracy overall) is a strength, that strength is largely offset by the extremely narrow set of stimuli used without clear justification
There is no attempt to relate AI system performance in these tasks to human performance, and performance variability is only minimally addressed. Any real-world application of computer vision systems that need to be robust across small input changes would also need to be robust to noise, which is not examined or addressed here
The paper mentions that changes in material properties could result in changes in color, contrast, texture, etc – this seems likely to change the ‘salience’ of different locations in the image, which could itself impact performance of computer vision systems
Questions For Authors:
What is the potential role of differences in object salience on the results? Can this be experimentally determined (or ruled out)?
Why are only a small set of image pairs chosen?
My assessment could only be materially improved through substantial edits to the paper to improve its clarity and flow, clearer explanations of the experiments and results, and inclusion of reasonable justifications of design/experiment choices addressed in Weaknesses above.

Flag For Ethics Review: No
Rating: 1: Clear rejection
Confidence: 2: I have broad familiarity with this field but little or no direct research experience on this topic.
```

## Reviewer 51hM

Official Review of Submission23337 by Reviewer 51hM

Official Reviewby Reviewer 51hM14 Oct 2026, 15:56 (modified: 06 Nov 2026, 20:24)EveryoneRevisions

```text
Paper Summary:
The authors tackle an interesting problem: How is visual perception reliant on the material properties of the object / scene of interest? Through paired interventions, where an original scene is altered by modifying only the materials and not the geometry, the authors show that the decisions made by VLMs for grounding (i.e., localizing objects) and navigation (reaching a specified image target) vary between the original and modified scenes. The tested models include Gemma4-E4B, Qwen2.5-VL-7B, Qwen3-VL-2B, Qwen3-VL-8B, InternVL3-8B and Molmo-7B-D. The results demonstrate modest variation in grounding performance and larger variation in navigation performance based on material interventions. The authors highlight the importance of paired interventions with decision-flip analysis, and the need to focus on material properties, not just geometry for embodied tasks.

Presentation: 1: Difficult to follow despite careful reading.
Informativeness: 1: I learned little or nothing new from this paper.
Soundness: 1: I have significant concerns about the paper’s soundness that do not appear easy to address.
Critical Strengths:
The paper focuses on an interesting problem: How does material property affect VLM visual perception, especially in the context of navigation tasks?
The intervention of varying material properties while keeping the rest of the scene fixed (including the object colors) is scientifically sound and useful.

Critical Weaknesses:
I have three key weaknesses for the paper.

1. Novelty
There is a large body of prior work that has studied the importance of appearance and material properties for visual perception in neural networks [1,2,3] and VLMs [4,5,6,7,8]. These have not been cited nor compared with. The motivation for this particular study and why the results are surprising / unexpected is therefore unclear. There's also relevance of adversarial perturbations [9,10] (e.g., are the material variations observed now a form of adversarial perturbation?).

[1] Geirhos, Robert, et al. "ImageNet-trained CNNs are biased towards texture; increasing shape bias improves accuracy and robustness." arXiv preprint arXiv:1811.12231 (2018). [2] Hendrycks, Dan, and Thomas Dietterich. "Benchmarking neural network robustness to common corruptions and perturbations." arXiv preprint arXiv:1903.12261 (2019). [3] Zhang, Chenshuang, et al. "Imagenet-d: Benchmarking neural network robustness on diffusion synthetic object." 2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR). IEEE, 2024. [4] Gavrikov, Paul, et al. "Can we talk models into seeing the world differently?." International Conference on Learning Representations. Vol. 2025. 2025. [5] Eppel, Sagi, Mor Bismut, and Alona Strugatski. "Shape and texture recognition in large vision-language models." Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 2026. [6] Wang, Jiabao, et al. "The Constant Eye: Benchmarking and Bridging Appearance Robustness in Autonomous Driving." arXiv preprint arXiv:2602.12563 (2026). [7] Burgert, Tom, et al. "ImageNet-trained CNNs are not biased towards texture: Revisiting feature reliance through controlled suppression." Advances in Neural Information Processing Systems 38 (2026): 60809-60830. [8] Sar, Ayan, et al. "VLM Reality Check: A Causal Counterfactual Benchmark for Diagnosing Cognitive Biases in Vision-Language Models." Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 2026. [9] Chaubey, Ashutosh, et al. "Universal adversarial perturbations: A survey." arXiv preprint arXiv:2005.08087 (2020). [10] Tong, Shengbang, et al. "Eyes wide shut? exploring the visual shortcomings of multimodal llms." 2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR). IEEE, 2024.

2. Poor experimental setup
The experimental setup has several critical flaws.

The number of samples is so low (99 for navigation --- L323, 16 queries per intervention for grounding --- Table 1) that the results can be noisy and unreliable.
The null-hypothesis of re-evaluating models on the original stimulus and measuring performance / flips is not performed clearly (Tables 1 and 2). This is hinted at in L311 for grounding, where the decoding variability on its own explains ~16.7% of the cases in Qwen3-VL-2B vary without any changes to the stimuli. Is the variability seen just generation / low-data regime noise?
Alternate hypotheses for the variability in model predictions are not evaluated. E.g., if the color were changed while holding the materials fixed, or if the background was changed while keeping the objects fixed, how much would the performance vary? This type of variability could be likely due to models being weak, which is likely here.
All models evaluated are small / relatively old - Gemma4-E4B, Qwen2.5-VL-7B, Qwen3-VL-2B, Qwen3-VL-8B, InternVL3-8B and Molmo-7B-D. Each of these models have much better alternatives from the recent year, and also have higher capacity variants. None of the closed-source SoTA models like Claude Opus, Gemini, and GPT 5-* are evaluated. Given the rapid progression in model capacities, the findings could just be outdated.
Overall, the results are quite inconclusive and I don't have any good takeaways at the end of the paper due to the above concerns.

3. Paper writing clarity is poor.
The abstract is poorly written, with no indication of the significance of the results (e.g., navigation results can flip even normally across trials without any interventions for the same model and scene).
The introduction does not motivate the problem at all (why is it important to solve?). What has been done so far in this problem space and what does this paper contribute that is new?
Figure 1 is hard to understand. How are the middle and right panels related to material change? The original vs. swapped / converted do not convey a material change. The scene itself seems to have changed.
The experimental findings are not clearly analyzed. Examples:
L212 - 237 --- what is the takeaway? 0 - 3 flips out of 16 across conditions. Why is this meaningful?
L308-312 --- how does decoding variability (and more generally, generation variability) impact the conclusions?

Questions For Authors:
Why is this work novel?
Are models particularly sensitive to material properties, or are they just sensitive to any visual changes? Is the null-hypothesis rejected?
How do newer and larger models compare? Are these limitations still existing in models? Are the findings outdated?
The paper writing in general is poor, but addressing the key clarity concerns would be helpful.
Flag For Ethics Review: No
Rating: 1: Clear rejection
Confidence: 3: I am familiar with this topic and its relevant literature.
```
