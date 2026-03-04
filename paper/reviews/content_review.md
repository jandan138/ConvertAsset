# Content Review: MDL-to-UsdPreviewSurface Material Simplification Paper
## Reviewer: Simulated CVPR Workshop Reviewer

### 1. Summary (3 sentences)

This paper evaluates the visual and semantic impact of converting MDL materials to UsdPreviewSurface in NVIDIA Isaac Sim, measuring pixel-level quality (PSNR, SSIM, LPIPS), rendering performance, feature-level preservation (CLIP, DINOv2), and zero-shot object detection. The study finds that conversion preserves high visual fidelity for standard PBR assets while enabling broader toolchain interoperability, with degradation concentrated in assets using complex multi-layer MDL effects. The authors release ConvertAsset, an open-source pipeline automating the conversion, and provide practical guidelines for synthetic data practitioners.

### 2. Strengths (3-5 bullet points)

- **Well-structured multi-level evaluation framework.** The four-level evaluation (pixel, performance, feature, task) is methodologically sound and provides complementary perspectives. The choice to use both CLIP and DINOv2 as feature-level probes is well-motivated, and the paper provides a clear explanation (Sec. 5, Discussion) for why they yield different sensitivity levels.

- **Practical relevance.** The "within-simulation rendering gap" concept is a genuine blind spot in the synthetic data literature. Practitioners routinely convert materials for interoperability without quantifying the consequences, making this evaluation timely for the SynData4CV audience.

- **Honest reporting of null/weak results.** The paper does not overclaim the performance benefits (correctly noting near-identical FPS and memory) and transparently discusses the sparsity of the detection experiment. The limitations section (Sec. 6) acknowledges the narrow scope.

- **Reproducible methodology.** The release of the ConvertAsset toolkit and the clear description of the pipeline architecture (Sec. 3.1) make the work reproducible. The compositional-preservation design decision is technically sound for production USD workflows.

- **Internally consistent pixel-level analysis.** The per-scene breakdown correctly identifies chestofdrawers_0023 as the hardest case and provides a reasonable attribution (multi-layer MDL materials, procedural textures). The PSNR range of 23-44 dB across viewpoints is informative.

### 3. Weaknesses (3-5 bullet points)

- **Extremely narrow dataset scope.** Four assets from a single furniture category (chest-of-drawers) is insufficient to support the broad claims and "practical guidelines" offered. The paper acknowledges this but still presents guidelines as if they generalize. Materials involving transparency, subsurface scattering, emission, or highly specular metals are entirely unrepresented. The paper title and abstract promise a general evaluation but deliver a case study.

- **Data-text discrepancies in the detection experiment (critical).** The raw data shows **7** UsdPreviewSurface images with detections (not 5 as claimed in Table 4 and Sec. 4.4), and the mean confidence for version B is **0.513** (not 0.527 as reported). See detailed comments below. These errors undermine confidence in the reported results.

- **The detection experiment lacks statistical power and is poorly designed.** With only 6 total detections for MDL and 9 for UsdPreviewSurface (most images have zero detections), no meaningful statistical comparison can be made. The paper claims the conversion is "detection-neutral" based on this, which is not justified. The experiment design (zero-shot on single-object renders against COCO-trained YOLOv8) almost guarantees sparse results by construction, making the evaluation uninformative.

- **No statistical tests anywhere.** The paper reports mean +/- std throughout but never performs any statistical significance tests (e.g., paired t-tests, Wilcoxon signed-rank) to determine whether observed differences are statistically meaningful. With only 6 viewpoints per scene, the standard deviations may be unreliable estimates of population variability.

- **Viewpoint naming inconsistency.** The methodology section (Sec. 3.2) describes viewpoints as "front, back, left, right, top-front, and top-back," but the actual data files use "top_front_left" and "top_front_right." These are different viewing angles. This suggests either the paper text is wrong or the data was collected differently than described.

### 4. Detailed Section-by-Section Comments

#### Introduction

- The four contributions are clearly stated. However, contribution (1) claiming "the first systematic quantification" is a strong novelty claim. While likely true given the niche topic, the word "systematic" is generous for a study of 4 objects from 1 category. Consider softening to "an initial systematic quantification" or "a multi-level quantification."
- The framing of the "within-simulation rendering gap" (paragraph 3) is the strongest conceptual contribution. This is well-articulated and genuinely useful for the community.
- The paper mentions "standard 3D tools and web-based viewers" (line 19-20) as motivation but never actually demonstrates or benchmarks the converted assets in these environments. This is a missed opportunity.

#### Related Work

- The related work is adequate but narrow. There is no discussion of:
  - Prior work on material LOD or material simplification in computer graphics (e.g., Wang et al. "Appearance-Preserving Simplification", Peers et al. on BRDF simplification).
  - The USD specification itself and UsdPreviewSurface's documented limitations relative to full PBR models.
  - Other simulation platforms (Habitat, AI2-THOR, ThreeDWorld) that use different material representations and face similar interoperability questions.
- FID is mentioned in Sec. 2.3 but never used in the experiments. Either justify why it was excluded or remove the mention.

#### Methodology

- **Viewpoint mismatch (critical).** Section 3.2 states: "front, back, left, right, top-front, and top-back." The raw data files contain viewpoints named "top_front_left" and "top_front_right." This is not merely a naming inconsistency -- "top-front" and "top-front-left" are different camera positions, and "top-back" vs "top-front-right" even more so. The text must be corrected to match the actual experimental setup.
- **Hardware error.** The paper states "NVIDIA GeForce RTX 4090 (48 GB VRAM)." The RTX 4090 has 24 GB VRAM, not 48 GB. The 48 GB variant is the RTX 6000 Ada Generation. This factual error should be corrected.
- The choice of YOLOv8n (nano) as the detection model is not motivated. Why not a larger model that might produce more detections? The nano variant is the weakest in the YOLOv8 family.
- The paper does not describe how PSNR/SSIM/LPIPS were computed (which library, which LPIPS backbone network -- VGG vs AlexNet). For reproducibility, these details matter.
- The paper maps only four MDL channels to UsdPreviewSurface: "base color, roughness, metallic, and normal." It should explicitly acknowledge what MDL features are dropped (e.g., subsurface scattering, clearcoat, anisotropy, emission, opacity, displacement) and how this constrains the generalizability of the findings.
- Resolution of 1024x1024 is reasonable but the paper should note whether anti-aliasing, sample count, or denoising settings were controlled between the two rendering conditions.

#### Results

- **Image quality (Sec. 4.1):** Numbers match the raw data well. The paper correctly identifies the 23.11 dB outlier for chestofdrawers_0023/right. However, the text claims "22 of 24 pairs exceeding 30 dB PSNR" while the data shows **23 of 24** (only chestofdrawers_0023/right at 23.11 dB is below 30). This is a minor but unnecessary error that should be corrected.
- **Performance (Sec. 4.2):** The performance numbers match the raw data. The paper's observation that the cold-start effect drives the MDL load time variance (first run at 1.33s) is well-identified. However, including the cold-start run in the mean is questionable for a fair comparison -- consider reporting with and without the first run. Only 3 runs per scene is low for benchmarking; 10+ would be more standard.
- **Feature similarity (Sec. 4.3):** The overall numbers match. Minor discrepancy: the paper's Table 3 reports DINOv2 std for chestofdrawers_0004 as 0.156, but the raw data yields 0.171. The paper reports overall DINOv2 std as 0.102, while the data gives 0.104 -- a minor rounding difference but the 0.156/0.171 gap is larger and should be checked.
- **Detection (Sec. 4.4, critical errors):**
  - **Table 4 claims 5/24 UsdPreviewSurface images have detections.** The raw JSON shows **7/24** images with at least one detection for version B (chestofdrawers_0004/top_front_right, chestofdrawers_0011/front, chestofdrawers_0011/top_front_left, chestofdrawers_0011/top_front_right, chestofdrawers_0023/top_front_left, chestofdrawers_0023/top_front_right, chestofdrawers_0029/top_front_right).
  - **Table 4 claims 9 total detections for UsdPreviewSurface.** The raw data confirms 9 individual detections across those 7 images (2+1+2+1+1+1+1=9), so the total detection count is correct but the image count is wrong.
  - **Mean confidence for version B: paper says 0.527, data yields 0.513** ((0.51+0.4334+0.7921+0.6325+0.2813+0.273+0.9001+0.4185+0.3731)/9 = 4.616/9 = 0.513). This is a notable error.
  - **The claim that "detections are concentrated in elevated viewpoints (top-front-left and top-front-right)"** is partially incorrect for version A: MDL detections occur at top_front_right (3 scenes) and front (1 scene: chestofdrawers_0011). For version B, detections occur at front (1), top_front_left (2), and top_front_right (4). The front-view detections contradict the stated pattern.

#### Discussion

- The practical recommendations (numbered list, Sec. 5) are useful but insufficiently evidence-based given the narrow dataset. For example:
  - Guideline 3 proposes a "go/no-go threshold" of CLIP cosine similarity 0.85, but no experiment validates this threshold. Where does 0.85 come from? The lowest per-pair CLIP similarity in the data is ~0.808 (chestofdrawers_0029/front), so the threshold appears to be below the worst observed case, making it vacuous for this dataset.
  - Guideline 4 proposes a DINOv2 threshold of 0.80. Three data points fall below this (chestofdrawers_0004/back at 0.615, right at 0.595, and left at 0.738), yet the paper does not discuss these failures in the context of the proposed threshold.
- The t-SNE visualization (Fig. 4) is a nice addition but t-SNE is non-parametric and the specific layout depends on hyperparameters (perplexity, learning rate). Were these reported? With only 48 points, t-SNE may not be meaningful.
- The claim "the within-simulation gap introduced by material simplification is negligible compared to the sim-to-real gap" is stated without evidence, since no real-world images are included in the evaluation. This is speculation, not a finding.

#### Conclusion

- The conclusion accurately summarizes the findings and limitations. The future work directions are appropriate.
- The repeated summary of all numbers (PSNR 35.52, SSIM 0.990, etc.) is redundant with the abstract and results sections but acceptable for a workshop paper.

### 5. Questions for Authors

1. **Detection data discrepancy:** Can you reconcile the claim of "5/24 UsdPreviewSurface images with detections" and "mean confidence 0.527" with the raw JSON data, which shows 7/24 images and mean confidence 0.513? Were some detections filtered by a confidence threshold not described in the paper?

2. **Viewpoint naming:** The methodology describes "top-front and top-back" viewpoints, but the data uses "top_front_left and top_front_right." Which is correct? Were the viewpoints mis-described in the text?

3. **GPU specification:** Is the GPU actually an RTX 4090 (24 GB) or an RTX 6000 Ada (48 GB)? The stated 48 GB does not match the RTX 4090 specification.

4. **Threshold justification:** What evidence supports the CLIP 0.85 and DINOv2 0.80 thresholds recommended in the practical guidelines? Have you validated these on any held-out data or downstream tasks?

5. **Why only chest-of-drawers?** Given that the Isaac Sim asset library contains diverse object categories, what prevented inclusion of at least 2-3 additional categories (e.g., chairs with fabric, kitchen appliances with metal/glass, or robotic parts)?

6. **PSNR count:** The paper states "22 of 24 pairs exceeding 30 dB PSNR" but the data shows 23/24. Can you verify?

### 6. Missing Experiments or Analyses

1. **Diverse object categories.** The most significant omission. At minimum, the evaluation should include 2-3 object categories beyond furniture, especially categories with challenging materials: transparent/translucent objects (glass, plastic), highly specular metals, textured fabrics, and objects with emission or subsurface scattering.

2. **Downstream task with fine-tuned models.** The zero-shot detection experiment is acknowledged as weak. A much more informative experiment would train a detector on MDL-rendered images and test on UsdPreviewSurface images (and vice versa), directly measuring whether the material change degrades training signal quality.

3. **Statistical significance tests.** Paired t-tests or Wilcoxon signed-rank tests for the image quality and feature similarity metrics would strengthen all claims. With n=24 paired observations, these tests have reasonable power.

4. **FID or distributional metrics.** The paper mentions FID in related work but never computes it. Even with only 24 images per version, reporting FID (or KID, which is better for small samples) would complement the per-pair metrics.

5. **Ablation on MDL material complexity.** The paper attributes degradation to "multi-layer MDL effects" but does not characterize which specific MDL features cause the largest quality drops (procedural textures vs. clearcoat vs. anisotropy vs. multi-layer stacking). An ablation enabling/disabling individual MDL features would be highly informative.

6. **Large-scale scene benchmarking.** The performance results are uninformative for single-object scenes (identical FPS and memory). Testing with scenes containing 50-100+ material instances would determine whether material simplification provides meaningful performance benefits at scale, which is the scenario practitioners actually care about.

7. **Real-world baseline images.** To contextualize the within-simulation gap, including even a small set of real photographs of similar furniture and computing the same metrics (CLIP/DINOv2 similarity) between {real, MDL-rendered, UsdPreviewSurface-rendered} would provide the missing comparison to the sim-to-real gap.

8. **Per-material-channel ablation.** The pipeline converts 4 channels (diffuse, roughness, metallic, normal). Which channels contribute most to the observed quality degradation? Ablating each channel individually would provide more actionable guidance.

### 7. Minor Issues

- **Table 3, chestofdrawers_0004 DINOv2 std:** Paper reports 0.156, data computes to 0.171. Check the computation.
- **Overall DINOv2 std:** Paper reports 0.102, data gives 0.104. Minor rounding but should be consistent.
- **Sec. 3.2, "six camera viewpoints: front, back, left, right, top-front, and top-back":** Should read "front, back, left, right, top-front-left, and top-front-right" to match the data.
- **Missing TODO:** Sec. 3.1 contains a LaTeX comment "% TODO: Add Figure 1 (pipeline architecture diagram) here once created." This figure is referenced nowhere in the text, but a pipeline diagram would significantly improve the methodology section.
- **No figure numbers for missing figures:** The paper references Fig. 1 (render pairs), Fig. 2 (image quality), Fig. 3 (feature similarity), and Fig. 4 (t-SNE). Verify that all figure files exist and are correctly generated. The PDF paths point to `../results/figures/` which is a relative path from the writing directory.
- **Ref [14] (Oquab2023DINOv2):** Listed as year 2024 in the bib entry for the TMLR publication, but the text cites it as DINOv2~\cite{Oquab2023DINOv2}. The citation key suggests 2023 (arxiv year). This is fine but could cause confusion.
- **Abstract and Conclusion both list all major numbers.** Consider trimming one to avoid redundancy and stay within page limits.
- **The performance table (Table 2) reports "mean +/- std over 4 scenes x 3 runs"** = 12 data points per version. Confirm whether the cold-start run (1.33s for chestofdrawers_0004 MDL run 1) should be excluded or flagged.
- **The term "detection-neutral" (Sec. 4.4)** is introduced without definition. Define what would constitute non-neutrality (e.g., a paired McNemar test showing significantly different detection rates).

### 8. Overall Recommendation

**Rating:** Weak Accept

**Confidence:** High

**Justification:** The paper addresses a genuine practical gap (the within-simulation rendering gap from material simplification) that is relevant to the SynData4CV workshop audience. The multi-level evaluation framework is well-designed and the pixel-level and feature-level analyses are competently executed. However, the paper has several issues that need correction before publication:

(1) **Data-text discrepancies in the detection results** (7 vs. 5 images, 0.513 vs. 0.527 mean confidence) are factual errors that must be fixed.
(2) **The viewpoint naming mismatch** between text and data suggests insufficient proofreading or a disconnect between the experiment and the writeup.
(3) **The GPU specification error** (48 GB vs. 24 GB for RTX 4090) is a factual mistake.
(4) **The extremely narrow scope** (4 objects, 1 category) limits the generalizability of all conclusions and the practical guidelines. The paper would benefit from at least acknowledging more explicitly that the guidelines are preliminary and category-specific.
(5) **The detection experiment is too weak** to support any conclusion, even the modest "detection-neutral" claim. It should be either substantially strengthened or repositioned as a preliminary pilot observation.

The paper is suitable for a workshop venue given the practical relevance, but the factual errors must be corrected and the scope limitations more prominently acknowledged. The conceptual contribution (within-simulation rendering gap) and the toolkit release add value beyond the experimental results alone.
