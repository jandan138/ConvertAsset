# Submission Cover Letter — *Computer Vision and Image Understanding* (CVIU)

**Date:** November 19, 2026  
**To:** The Editors-in-Chief and Editorial Board, *Computer Vision and Image Understanding*  
**Manuscript Title:** *Geometric Fidelity Is Not Decision Fidelity: Bidirectional Optical Turnover and Pre-Deployment Risk Gating Under 3D Material Conversion*  
**Author:** Zihou Zhu (Sole & Corresponding Author, Shanghai Artificial Intelligence Laboratory, Shanghai, China)  
**Email:** `zhuzihou@pjlab.org.cn`  
**ORCID:** `0009-0003-7530-6776`

---

Dear Editors-in-Chief and Editorial Board of *Computer Vision and Image Understanding*,

I am pleased to submit my original research manuscript entitled **"Geometric Fidelity Is Not Decision Fidelity: Bidirectional Optical Turnover and Pre-Deployment Risk Gating Under 3D Material Conversion"** for consideration as a regular research article in *Computer Vision and Image Understanding* (CVIU).

Across embodied AI and robotics simulation pipelines, vendor-specific NVIDIA Material Definition Language (MDL) shaders within OpenUSD environments are routinely lowered into portable `UsdPreviewSurface` networks while keeping scene geometry, camera poses, and language instructions fixed. Although dataset-wide accuracy barely shifts after conversion (+0.42% on Qwen3-VL-32B, Molmo2-8B, and LLaVA-NeXT-Mistral-7B), this work reveals substantial bidirectional decision turnover (4.17% to 23.13%) across 30 indoor scenes (480 paired captures, 14,016 total VLM predictions spanning four independent open-weight model families). Through a four-level variance decomposition, 2,880 pixel-exact silhouette counterfactuals paired with CIE $L^*a^*b^*$ photometric controls, and 99 closed-loop navigation rollouts, the manuscript isolates an identical +3.54% non-photometric BSDF residual across distinct 8B architectures, shows that 85.7% of $\ge$7B regressions are specific to a single architecture, and introduces a lightweight zero-VLM pre-deployment risk gate reaching 0.743 held-out test AUROC (0.732 30-scene LOSO) where global RGB MAE fails (0.432).

**Relationship to Prior Workshop Paper (Originality Disclosure):**  
A preliminary workshop paper introducing the underlying conversion toolkit appeared in CVPR Workshops 2026 (SynData4CV): *"Evaluating the Trade-offs of MDL-to-UsdPreviewSurface Material Simplification in NVIDIA Isaac Sim: Visual Quality, Feature Preservation, and AI Task Performance"* (cited in Section 1 and Appendix A). That workshop study examined four individual furniture assets using low-level image similarity metrics (PSNR, SSIM, LPIPS), backbone feature cosines (CLIP, DINOv2), and simulator startup timing. **Over 85% of the present CVIU manuscript is completely new**, introducing the 30-scene geometry-locked grounding benchmark, four-family scaling and noise-floor experiments (14,016 predictions), 2,880 cross-family silhouette and photometric counterfactuals, family-calibrated zero-VLM risk gating, and a 99-episode closed-loop embodied navigation analysis.

I confirm that this extended journal manuscript is original, has not been published previously, and is not under consideration elsewhere, and that I have no competing financial interests or personal relationships that could have appeared to influence the reported work.

Thank you very much for considering this submission.

Sincerely,  

**Zihou Zhu** (Sole & Corresponding Author)  
Shanghai Artificial Intelligence Laboratory, Shanghai, China  
Email: `zhuzihou@pjlab.org.cn`  
ORCID: `0009-0003-7530-6776`
