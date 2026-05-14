The paper is clear and useful, addressing a practical Isaac Sim material-conversion problem and evaluating tradeoffs of MDL-to-UsdPreviewSurface material simplification. However, the experiments are limited in scope.
Official Reviewby Reviewer o7vM29 Apr 2026, 12:09 (modified: 03 May 2026, 00:01)Program Chairs, Reviewer o7vM, AuthorsRevisions
Strength: The paper addresses a practical interoperability problem: MDL materials improve realism in Isaac Sim but have limited compatibility with standard 3D tools and web viewers, and the effects of simplifying them to UsdPreviewSurface have not been well studied. It therefore evaluates the trade-offs of this conversion. The conversion pipeline is clearly described. The evaluation is well-rounded, including PSNR, SSIM, LPIPS, load time, GPU memory, FPS, and CLIP/DINOv2 feature similarity. The results provide actionable guidance about when simplification is safe.
Review:
The paper is well-written and easy to follow. The method itself does not seem highly novel, since it mainly maps MDL materials to the existing, standard UsdPreviewSurface representation, but the empirical study of this within-simulation material gap is useful and was underexplored. The results are useful and provide practical recommendations for synthetic data practitioners working with Isaac Sim assets, although I am not fully convinced about the generality because the experimental scope is limited, as discussed below.

Pros
The paper addresses a practical interoperability problem: MDL materials improve realism in Isaac Sim but have limited compatibility with standard 3D tools and web viewers, and the effects of simplifying them to UsdPreviewSurface have not been well studied. It therefore evaluates the trade-offs of this conversion.
The conversion pipeline is clearly described.
The evaluation is well-rounded, including PSNR, SSIM, LPIPS, load time, GPU memory, FPS, and CLIP/DINOv2 feature similarity.
The results provide actionable guidance about when simplification is safe.
Cons
The empirical scope is limited: the main evaluation uses only four same-category furniture assets and 24 matched pairs. Additionally, as the authors also pointed out, broader material categories such as transparent or translucent, highly specular, and organic surfaces still require validation.
The large-scene startup result is interesting, but its generality is unclear because it's based on only one GRScenes commercial interior with three runs per version.
Weaknesses: The empirical scope is limited: the main evaluation uses only four same-category furniture assets and 24 matched pairs. Additionally, as the authors also pointed out, broader material categories such as transparent/translucent, highly specular, and organic surfaces still require validation. The large-scene startup result is interesting, but the generality is unclear because it's based on only one GRScenes commercial interior with three runs per version.
Rating: 6: Marginally above acceptance threshold
Summary: The paper is clear and useful, addressing a practical Isaac Sim material-conversion problem and evaluating the tradeoff of simplifying MDL materials, with a well-described pipeline and multi-level evaluation. However, the claims shall be framed more cautiously, because the experiments are limited in scope. Overall, I recommend marginal acceptance.
Confidence: 3: The reviewer is fairly confident that the evaluation is correct
Add:
Paper Decision
Decisionby Program Chairs28 Apr 2026, 09:31 (modified: 02 May 2026, 01:53)Program Chairs, AuthorsRevisions
Decision: Accept
Add:
Rebuttal by Authors
Rebuttalby Authors (Haolong Zheng, Zhou Zhang, Zihou Zhu, Mei Haitao)02 May 2026, 10:08Program Chairs, Authors
Rebuttal:
Dear SynData4CV Program Chairs,

Thank you very much for accepting our paper. We are grateful for the opportunity to present our work at the workshop.

I wanted to kindly ask whether any review feedback or comments will be made available for our submission. At the moment, I do not see written reviews on OpenReview. If there are any suggestions from the reviewers or program chairs, we would be very grateful to receive them, as we hope to further improve the paper before the final version.

Thank you very much~

Best regards, Zihou Zhu

Add:
Technically sound conversion toolkit for Isaac Sim interoperability undermined by extreme empirical scarcity (
) and lack of downstream task validation.
Official Reviewby Reviewer CiLc27 Apr 2026, 12:10 (modified: 03 May 2026, 00:01)Program Chairs, Reviewer CiLc, AuthorsRevisions
Strength: 1. **Practical Industry Utility:** The identification of a
 reduction in "scene-ready" time for large interior environments (
 s vs.
 s) is a valuable finding for large-scale synthetic data pipelines. It correctly identifies that material initialization and shader settling are major "cold-start" bottlenecks in simulation.

2. **Structural Integrity in Conversion:** The proposed three-stage toolkit is technically well-conceived, particularly the composition-preserving USD traversal. By rewriting asset paths in composition arcs rather than flattening the scene, the tool maintains the modularity required for professional digital twin workflows.

3. **Holistic Diagnostic Strategy:** Moving beyond simple pixel-level error to include perceptual (LPIPS) and semantic (CLIP, DINOv2) alignment demonstrates a sophisticated understanding of how material representation impacts different levels of an AI pipeline.
Review:
The submission investigates the "within-simulation rendering gap" created by simplifying Material Definition Language (MDL) assets into the more universal UsdPreviewSurface representation within NVIDIA Isaac Sim. This conversion is motivated by the need for interoperability with standard 3D tools and web viewers.

Technical Implementation and Originality
The authors propose an automated toolkit that discovers the USD dependency graph and remaps four primary MDL channels—base color, roughness, metallic, and normal—to the UsdPreviewSurface specification. While the implementation appears robust, the originality is moderate. NVIDIA already provides "MDL Distill and Bake" and "Asset Converter" extensions that perform similar optimizations. The paper fails to provide a head-to-head comparison with these existing industrial solutions, leaving the unique contribution of the proposed toolkit unclear.

Visual Quality and the "Within-Simulation" Gap
Pixel-level fidelity is quantified using Peak Signal-to-Noise Ratio (PSNR), which is defined as:



where the Mean Squared Error (MSE) is calculated as:



The reported mean PSNR of
 dB and SSIM of
 indicate high alignment for standard PBR materials. However, the study identifies significant fidelity drops for complex materials (e.g., specular coatings), where PSNR falls to
 dB. This suggests the simplified model cannot capture the multi-layer effects enabled by the full MDL specification.

Feature-Level Alignment as a Proxy
The use of CLIP and DINOv2 feature similarity as a diagnostic for AI task performance is a compelling probe. The higher CLIP similarity (
) compared to DINOv2 (
) suggests that while high-level semantic categories are preserved, the fine-grained visual cues required for dense prediction tasks are more susceptible to simplification.

Pros
Addresses a legitimate interoperability bottleneck for synthetic data practitioners.
Composition-preserving traversal maintains asset modularity.
High-value insights into startup latency for large simulation environments.
Sophisticated use of foundation model feature-space alignment.
Cons
Empirical Inadequacy: An evaluation based on
 image pairs from only four furniture assets is insufficient for a CVPR-level benchmark.
Unsupported Claims: Despite "AI Task Performance" in the title, no actual tasks (e.g., object detection mAP) were evaluated.
Asset Bias: The evaluation is restricted to wood, metal, and fabric, ignoring challenging materials like glass or water where simplification typically fails.
Missing Baseline Comparison: No comparison against official NVIDIA conversion tools.
Weaknesses: The primary weakness is the paper's extreme lack of scale. A sample size of
 images is anecdotal and prevents the use of standard distributional metrics like Fréchet Inception Distance (FID), as the authors admit in Section 2.4. Furthermore, the study relies entirely on latent-space cosine similarity as a proxy for "AI Task Performance." Without an end-to-end experiment showing that a model trained on simplified data performs similarly to one trained on MDL data, the paper's central utility for the SynData4CV community remains speculative.
Rating: 4: Ok but not good enough - rejection
Summary: The paper provides a useful technical utility for Isaac Sim and demonstrates significant startup efficiency gains. However, as a scientific study, the execution is too limited for a CVPR-level workshop. The sample size is insufficient, the "AI Task Performance" claims are unverified by actual task results, and the asset diversity is too narrow to support generalized guidelines. I recommend rejection in its current form, though it could serve as a solid technical report if task evaluations are expanded.
Confidence: 4: The reviewer is confident but not absolutely certain that the evaluation is correct
Add:
Evaluating the Trade-offs of MDL-to-UsdPreviewSurface Material Simplification in NVIDIA Isaac Sim: Visual Quality, Feature Preservation, and AI Task Performance
Official Reviewby Reviewer cb7X22 Apr 2026, 12:56 (modified: 03 May 2026, 00:01)Program Chairs, Reviewer cb7X, AuthorsRevisions
Strength: 1. The writing is well-structured and easy to understand.
2. This paper conducts an interesting study of evaluating the trade-off between two types of material representation in NVIDIA Isaac Sim to compare their usage in simulation render accuracy.
3. The work propose a coarse guideline of when to use MDL and when to convert to UsdPreviewSurface for simulation.
Review:
This paper presents a well-structured study on an interesting and practical problem that has been largely overlooked in the simulation community: the simulation rendering gap introduced by material representation choices between MDL and UsdPreviewSurface in NVIDIA Isaac Sim.

The problem is clearly motivated and the proposed guidelines offer a useful starting point for synthetic data practitioners. However, the work has notable weaknesses that limit its impact. The evaluation methodology, while reasonable, is quite shallow and lacks the granularity needed to draw strong conclusions, relying entirely on standard pixel-level metrics (PSNR, SSIM, LPIPS) and semantic similarity scores (CLIP, DINOv2) without any fine-grained analysis of how specific MDL effects such as subsurface scattering, clearcoat layers, anisotropic reflectance, or procedural noise textures individually contribute to quality degradation after conversion, which would be far more informative for practitioners who need to understand exactly which material properties are at risk rather than just knowing that complex materials are harder to convert in general.

Furthermore, the practical utility of the proposed guidelines is limited. Recommending that practitioners manually validate complex materials using CLIP and DINOv2 similarity as diagnostic metrics still requires per-asset human inspection that does not scale well in large synthetic data pipelines, and a much more impactful contribution would have been an automatic conversion recommender that, given an MDL material definition, and predicts whether conversion is safe, which would make the pipeline genuinely practical at scale.

Weaknesses: 1. The overall evaluation is quite simple and straightforward, using PSNR, LPIPS, SSIM as pixel-level scores and DINO, CLIP as semantic scores, and offers no extra levels of vigorous evaluation with finer-granularity or on different aspects (for example the degradation for different MDL effects).
2. The proposed solution is also very trivial and provides no practical guidance. It would be much more easier if the authors can propose a automatic detector for whether it's recommended to convert one object into UsdPreviewSurface.
Rating: 4: Ok but not good enough - rejection
Summary: The paper tackles a meaningful and underexplored problem in simulation-based data generation, and the study is well-presented. However, the evaluation depth and practical contributions fall short of the standard for this workshop. Strengthening the per-effect analysis and moving toward an automated conversion recommendation system would significantly improve the impact and utility of this work. Ok but not good enough. Rejection.
Confidence: 3: The reviewer is fairly confident that the evaluation is correct
