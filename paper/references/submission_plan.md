# Submission Plan: SynData4CV @ CVPR 2026

Paper: "Systematic evaluation of MDL→UsdPreviewSurface material simplification in NVIDIA Isaac Sim: trade-offs between rendering efficiency, visual quality, and AI task performance."

Research performed: 2026-03-03.

---

## 1. Target Workshop

**Name:** 3rd Workshop on Synthetic Data for Computer Vision (SynData4CV)
**At:** IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR 2026)
**Website:** https://syndata4cv.github.io/
**CVPR 2026 Workshop Listing:** https://cvpr.thecvf.com/Conferences/2026/Workshops
**Location:** Denver, CO, United States
**Date:** June 2026 (half-day workshop)

### Deadlines

| Milestone | Date |
|---|---|
| **Submission deadline** | **March 12, 2026** (9 days from today) |
| Acceptance notification | TBD (check workshop site) |
| Camera-ready deadline | TBD |

**CRITICAL:** Submission deadline is March 12, 2026. That leaves 9 days. A full-length paper requires immediate prioritization of experiments.

### Format

| Parameter | Requirement |
|---|---|
| Short paper length | 4 pages (excluding references) |
| Long paper length | 8 pages (excluding references) |
| Template | CVPR 2026 author template |
| Review type | Double-blind |
| Proceedings | NOT included in CVPR proceedings — no double-submission conflict |
| Submission platform | OpenReview (link TBD on workshop site) |

**The paper will NOT appear in CVPR proceedings.** This means it can be submitted simultaneously or subsequently to IEEE TVCG or CVPR 2027 main conference without violating double-submission rules. (Always confirm with the specific venue's dual-submission policy before relying on this.)

---

## 2. Alternative Workshops at CVPR 2026

If SynData4CV is not suitable (e.g., scope mismatch or deadline missed), these CVPR 2026 workshops are alternatives, ranked by fit:

### Alternative 1: DataCV 2026 — The 5th DataCV Workshop and Challenge

**Website:** https://sites.google.com/view/datacv-2026-cvpr/
**Submission deadline:** March 10, 2026 (23:59 AoE) — EARLIER than SynData4CV
**Acceptance notification:** March 16, 2026
**Camera-ready:** April 10, 2026
**Location:** Denver, CO, USA (half-day)
**Fit:** Moderate-high. DataCV focuses on "data-centric challenges in computer vision." Our paper's contribution — a toolkit that transforms USD assets for training data generation and a quantitative evaluation of how that transformation affects downstream vision tasks — fits the data-centric framing. Framing angle: "How does asset conversion quality affect the data-centric pipeline?"
**Caveat:** DataCV has a strong emphasis on vision-language models (VLMs) and dataset-level analysis; the rendering/material conversion focus is slightly off-center.

### Alternative 2: Embodied AI Workshop (7th Annual) @ CVPR 2026

**Website:** https://embodied-ai.org/
**Duration:** Full day (larger audience)
**Fit:** Moderate. Our work on MDL→UsdPreviewSurface simplification in Isaac Sim is directly relevant to embodied AI researchers who use Isaac Sim for robot learning. The RL policy transfer experiment (Experiment #5 in the checklist) is the strongest hook for this workshop. Framing angle: "Practical toolkit for efficient simulation environments for embodied AI."
**Caveat:** No submission deadline was findable on their website; check https://embodied-ai.org/ directly. This workshop typically favors papers with real robot or full policy learning results.

### Alternative 3: Domain Generalization Workshop (DG-EBF 2nd Edition) @ CVPR 2026

**Website:** https://dg-ebf.github.io/2026/
**Submission platform:** Microsoft CMT
**Fit:** Moderate. Our paper's core question — does material rendering simplification cause a domain shift that affects AI performance? — is a domain generalization question. Experiments 3a/3b (CLIP/DINOv2 feature distribution shift, FID) and 4a/4b (detection/segmentation transfer) map directly to domain generalization methodology.
**Framing angle:** "Material simplification as an unexpected source of domain shift in simulation-based training data."
**Caveat:** No specific submission deadline found; verify on their website. Scope may primarily emphasize real-world domain shifts rather than simulation-internal rendering variations.

### Alternative 4 (Non-workshop): IEEE Transactions on Visualization and Computer Graphics (TVCG)

**Type:** Rolling journal submission (no deadline)
**Fit:** High for the rendering/materials angle. After the workshop, a journal version expanded with all 6 experiments would be appropriate for TVCG.
**Rationale:** Even if the workshop submission is submitted first (establishing timestamp), a substantially extended journal version can be submitted to TVCG. TVCG's scope (rendering, visual computing, simulation) aligns with contributions 1 and 2 (rendering pipeline and image quality metrics) especially well.

---

## 3. Paper Length and Structure Plan for SynData4CV 2026

### Recommendation: Long Paper (8 pages, excluding references)

The 8-page format is recommended over the 4-page short paper because:
- The paper has 5 distinct quantitative experimental contributions (Experiments #1–#5 from EXPERIMENT_CHECKLIST.md)
- Workshop attendees specifically expect to see systematic evaluation methodology
- The paired MDL vs. UsdPreviewSurface rendering pipeline is novel enough to merit full description
- Comparable accepted papers at SynData4CV 2024 were 8-page long papers (see comparable papers section below)

### Proposed Section Breakdown

| Section | Target Words | Notes |
|---|---|---|
| **Abstract** | 150 | Hit: toolkit, evaluation, efficiency/quality trade-off, three finding types |
| **1. Introduction** | 400 | Problem: MDL→UsdPreviewSurface conversion in Isaac Sim; why it matters for synthetic data pipelines; 3-sentence summary of findings |
| **2. Related Work** | 350 | Sim-to-real rendering gap (Tremblay 2018, Garcia 2023); image quality metrics (SSIM, LPIPS); visual features (CLIP, DINOv2); USD/Isaac Sim pipelines (Synthetica, SynTable) |
| **3. ConvertAsset Toolkit** | 450 | Architecture summary; MDL→UsdPreviewSurface conversion algorithm; GLB export pipeline; what ConvertAsset enables (batch conversion, deduplication, non-flattening composition) |
| **4. Experimental Setup** | 300 | Scene selection; paired rendering pipeline (A=MDL, B=UsdPreviewSurface); hardware; metrics defined |
| **5. Rendering Performance** | 200 | Exp #1: load time, GPU memory, FPS table. Key takeaway: X% speedup |
| **6. Visual Quality Evaluation** | 400 | Exp #2 (PSNR/SSIM/LPIPS) + Exp #3a/3b (CLIP/DINOv2 cosine similarity, FID). One figure: side-by-side render pairs. One figure: metric comparison bar chart |
| **7. Downstream AI Task Performance** | 450 | Exp #4a detection + #4b segmentation (mAP, mIoU transfer table). One figure: per-category detection impact |
| **8. Discussion and Guidelines** | 300 | When is simplification safe? When is fidelity critical? Practical decision guide for Isaac Sim users |
| **9. Conclusion** | 100 | 3 sentences. Restate toolkit, key trade-off finding, future work pointer (RL experiment) |
| **References** | uncapped | Target 20-25 citations; references excluded from page count |

**Total estimated body words: ~3,100** (dense CVPR format, 8 pages with 2 figures + 3 tables fits comfortably).

### Figure Budget (8-page paper: approximately 4-5 figures total)

| Figure | Content | Priority |
|---|---|---|
| Fig. 1 | Architecture diagram: MDL → ConvertAsset → UsdPreviewSurface/GLB pipeline | Essential |
| Fig. 2 | Side-by-side render pairs (3-4 scenes): MDL vs. UsdPreviewSurface close-ups showing material differences | Essential |
| Fig. 3 | Quantitative metrics bar chart: PSNR / SSIM / LPIPS per scene or per material type | Essential |
| Fig. 4 | t-SNE or UMAP visualization: CLIP/DINOv2 features for MDL vs. UsdPreviewSurface renders | Recommended |
| Fig. 5 | Detection/segmentation performance table or grouped bar chart (mAP, mIoU, per-category) | Recommended |

### Experiments: Essential vs. Optional

| Experiment | Status for 8-page submission |
|---|---|
| #0 Paired rendering pipeline | **Essential** — required for all other experiments |
| #1 Rendering performance (load time, FPS, GPU memory) | **Essential** — establishes the efficiency motivation |
| #2 Image quality (PSNR, SSIM, LPIPS) | **Essential** — core quantitative fidelity claim |
| #3a Paired feature similarity (CLIP/DINOv2 cosine) | **Essential** — establishes "AI sees similar features" |
| #3b Feature distribution (FID, Wasserstein) | **Recommended** — adds rigor, fits in 1 paragraph + table |
| #3c t-SNE/UMAP visualization | **Recommended** — strong visual for workshop audience |
| #4a Detection transfer (mAP) | **Essential** — flagship downstream task |
| #4b Segmentation transfer (mIoU) | **Recommended** — adds breadth |
| #4c CLIP zero-shot retrieval | **Optional** — nice-to-have if space allows, else defer to journal version |
| #5 RL policy transfer | **Optional / Future Work** — label as "ongoing" or "future work" in paper; RL experiment is time-consuming and not strictly necessary to prove the core claim |

For a 4-page short paper: include only Experiments #0, #1, #2, #3a, and #4a. Drop all others.

---

## 4. Key Framing Advice for a Synthetic Data Workshop Audience

### Audience Profile at SynData4CV

SynData4CV attracts researchers who:
- Generate synthetic training data at scale (datasets with thousands to millions of images)
- Care about the quality-cost trade-off in synthetic data pipelines
- Use simulation engines (Isaac Sim, Blender, Unreal, CARLA) as data factories
- Want practical tools that reduce friction in the sim-to-real pipeline

### What to Emphasize

**1. Practical toolkit framing (lead with this)**
Open with the problem that synthetic data practitioners actually face: "Isaac Sim's full MDL materials are photorealistic but slow and produce files incompatible with standard 3D tools and web viewers. ConvertAsset converts them automatically." The toolkit is the concrete deliverable. SynData4CV reviewers value tools that help the community generate better data.

**2. Quantitative trade-off characterization (the key contribution)**
Frame the paper around: "We are the first to systematically quantify what you lose in visual quality and AI task performance when you simplify MDL materials, and what you gain in speed." This is a community service paper. The SynData4CV 2024 best long paper (CinePile) and honorable mention (C-SLAM benchmark) were both dataset/pipeline papers with clear quantitative characterization — not method novelty papers.

**3. "Safe simplification" decision guide**
End with practical guidelines: under what conditions can practitioners safely use UsdPreviewSurface materials? This is actionable advice that the synthetic data community will cite and use.

**4. Connection to sim-to-real gap**
Connect to the broader sim-to-real domain gap: material simplification is an underexplored source of domain shift within the simulation pipeline itself. Most domain gap papers focus on real vs. synthetic; ours characterizes a within-simulation rendering gap.

**5. Isaac Sim / Omniverse ecosystem relevance**
Explicitly note that Isaac Sim is widely used at NVIDIA (Synthetica: 2.7M images, SynTable, Orbit/Isaac Lab). Any result about Isaac Sim's material pipeline is directly relevant to a large fraction of the synthetic robotics data community.

### What to De-emphasize

**RL policy transfer (Experiment #5):**
In a synthetic data workshop context, this is "future work" or an appendix item. The workshop audience cares primarily about the rendering quality and downstream vision task impacts. RL transfer is compelling but requires substantial experimental infrastructure that may not be complete by the deadline. Reserve a sentence in the conclusion: "We plan to evaluate RL policy transfer, where material rendering differences may constitute a subtle but persistent source of domain mismatch."

**GLB export pipeline details:**
The GLB export capability is important for practitioners but secondary to the evaluation contribution. Mention it in one paragraph in the toolkit section; do not dedicate a full section to it.

**C++ QEM mesh simplification backend:**
The mesh simplification component is orthogonal to the core material evaluation. Mention it briefly as part of the pipeline but do not allocate space to benchmarking it.

**Heavy USD/MDL technical background:**
The synthetic data community will have varying familiarity with USD/MDL. Keep the technical background concise — 3-4 sentences — and focus on why the MDL→UsdPreviewSurface gap matters for training data quality, not on the USD spec details.

### Positioning Statement (for Abstract/Introduction)

Recommended framing: "We present ConvertAsset, an open-source toolkit for converting NVIDIA Isaac Sim assets from MDL to UsdPreviewSurface materials, and conduct the first systematic study of how this conversion affects rendering efficiency, visual image quality, and downstream AI task performance. Across N scenes, we find that UsdPreviewSurface rendering achieves [X]% faster load times and [Y]% GPU memory reduction, while maintaining [PSNR/SSIM/LPIPS values] visual fidelity and [mAP delta] detection performance — establishing practical guidelines for when material simplification is safe for synthetic training data generation."

---

## 5. Timeline to March 12 Deadline

Today is March 3, 2026. The submission deadline is March 12, 2026. That is 9 days.

### Recommended 9-Day Sprint Plan

| Day | Date | Task | Priority |
|---|---|---|---|
| Day 1 | Mar 3 (today) | Run Experiment #0: set up paired rendering pipeline, render 10-20 scene pairs | Blocking — everything depends on this |
| Day 1-2 | Mar 3-4 | Run Experiment #1: measure load time, FPS, GPU memory for MDL vs. UsdPreviewSurface | Fast — use existing benchmarking script |
| Day 2 | Mar 4 | Run Experiment #2: compute PSNR/SSIM/LPIPS on rendered pairs | Fast — numpy/skimage computation |
| Day 2-3 | Mar 4-5 | Run Experiment #3a: extract CLIP + DINOv2 embeddings, compute cosine similarity | Moderate — needs GPU time |
| Day 3 | Mar 5 | Run Experiment #3b: compute FID | Fast once embeddings exist |
| Day 3-4 | Mar 5-6 | Run Experiment #4a: train + evaluate detection model (MDL train → UsdPreviewSurface test) | Slowest experiment — start early |
| Day 4 | Mar 6 | Generate all figures: render pairs (Fig. 2), metrics bar chart (Fig. 3), t-SNE (Fig. 4) | Can run in parallel with Exp #4a |
| Day 5-6 | Mar 7-8 | First full draft: Introduction, Toolkit section, Experimental Setup, all result sections | Paper writing sprint |
| Day 7 | Mar 9 | Internal review pass: check figures, tables, narrative flow | Reserve for revision |
| Day 8 | Mar 10 | Revise draft, finalize references, prepare author information for double-blind | Near-final |
| Day 9 | Mar 11 | Proofread, format check against CVPR template, submit on OpenReview | Buffer day before hard deadline |
| **Deadline** | **Mar 12** | **Submission due** | |

### Risk Mitigation

- **If Experiment #4a (detection) is not complete by Day 6:** Submit with Experiments #0, #1, #2, #3a, #3b as the core results. Omit detection results rather than submitting placeholder data. The quality + feature analysis alone is sufficient for an 8-page paper.
- **If the paper is shorter than 8 pages after writing:** Do not pad. A tight 6-page submission with strong results is better than a padded 8-page one.
- **If the OpenReview submission link is not live on the workshop website:** Email the workshop organizers at the contact listed on https://syndata4cv.github.io/ to confirm the submission portal. (CVPR 2026 contact listed: Jieyu Zhang.)

---

## 6. Comparable Accepted Workshop Papers (for Calibration)

These papers were accepted at SynData4CV CVPR 2024, the most recent prior edition. They illustrate the type and quality of work that gets accepted.

### Paper 1: "A Benchmark Synthetic Dataset for C-SLAM in Service Environments" (Honorable Mention)

**Authors:** Harin Park, Inha Lee, Minje Kim, Hyungyu Park, Kyungdon Joo
**Type:** Long paper (8 pages), evaluation/analysis paper
**Summary:** Introduces a multi-modal synthetic dataset for service-robot SLAM using NVIDIA Isaac Sim. Provides synchronized stereo RGB, depth, IMU, and ground-truth poses across three environments. Evaluated against contemporary C-SLAM methods.
**Why relevant to us:** Used NVIDIA Isaac Sim directly. Dataset + evaluation paper structure. Won honorable mention despite being an Isaac Sim tools/dataset paper. This validates that Isaac Sim evaluation papers are valued at this workshop.
**URL:** https://openreview.net/forum?id=p6igw3ldIc

### Paper 2: "DDOS: The Drone Depth and Obstacle Segmentation Dataset"

**Authors:** Benedikt Kolbeinsson, Krystian Mikolajczyk
**Type:** Long paper (8 pages), dataset + evaluation paper
**Summary:** Introduces a synthetic aerial dataset for drone navigation using simulated images. Proposes drone-specific evaluation metrics. Evaluates semantic segmentation and depth estimation.
**Why relevant to us:** Dataset evaluation paper with custom metrics. Demonstrates that "tool + evaluation" papers are a standard format at SynData4CV, not just pure method papers.
**URL:** https://openreview.net/forum?id=FZxofmVOwg

### Paper 3: "Paved2Paradise: Cost-Effective and Scalable LiDAR Simulation by Factoring the Real World"

**Authors:** Michael A. Alcorn, Noah Schwartz
**Type:** Long paper (8 pages), pipeline + evaluation paper
**Summary:** Presents a pipeline for generating synthetic LiDAR datasets. Demonstrates that models trained on their synthetic data perform comparably to real-data-trained models.
**Why relevant to us:** Efficient simulation pipeline paper with a "does synthetic match real?" evaluation — structurally identical to our "does simplified material match full MDL?" question. This paper was accepted in a very similar framing to ours.
**URL:** https://openreview.net/forum?id=D9sfy3NUbY

### Paper 4: "Is Synthetic Data all We Need? Benchmarking the Robustness of Models Trained with Synthetic Images"

**Authors:** Krishnakant Singh, Thanush Navaratnam, Jannik Holmer, Simone Schaub-Meyer, Stefan Roth
**Type:** Evaluation/analysis paper (11 pages, CVPR 2024 Workshops proceedings, SyntaGen workshop)
**Summary:** First systematic evaluation of synthetic image models across supervised, self-supervised, and multi-modal categories. Finds synthetic-only training leads to more adversarially fragile models.
**Why relevant to us:** Purely evaluation/analysis paper with no new method. Demonstrates that systematic quantitative benchmarking is publishable at synthetic data workshops. Our paper follows the same "first systematic evaluation of X" framing.
**URL:** https://openaccess.thecvf.com/content/CVPR2024W/SyntaGen/html/Singh_Is_Synthetic_Data_all_We_Need_Benchmarking_the_Robustness_of_CVPRW_2024_paper.html

### Paper 5: "SynTable: A Synthetic Data Generation Pipeline for Unseen Object Amodal Instance Segmentation of Cluttered Tabletop Scenes"

**Authors:** Zhili Ng, Haozhe Wang, Zhengshen Zhang, Francis E. H. Tay, Marcelo H Ang Jr
**Venue:** SynData4CV Workshop @ CVPR 2025
**Type:** Pipeline + evaluation paper
**Summary:** Python-based dataset generator using NVIDIA Isaac Sim Replicator (USD-based RTX rendering with MDL materials). Auto-generates segmentation masks, depth maps, bounding boxes, material properties. Demonstrates improved performance on OSD-Amodal when training with synthetic data.
**Why relevant to us:** Directly uses Isaac Sim's USD/MDL pipeline. Demonstrates that an Isaac Sim synthetic data pipeline paper with downstream perception evaluation is exactly what the SynData4CV workshop accepts. This is the most directly comparable paper to ours.
**URL (arXiv):** https://arxiv.org/abs/2307.07333
**URL (OpenReview):** https://openreview.net/forum?id=L7xL80JclK

---

## Summary Decision

| Decision | Recommendation |
|---|---|
| Primary target | SynData4CV @ CVPR 2026 |
| Paper format | Long paper, 8 pages (excluding references) |
| Submission deadline | March 12, 2026 |
| Essential experiments for submission | #0 (rendering pairs), #1 (performance), #2 (quality), #3a (features), #4a (detection) |
| Optional / future work | #3b (FID), #3c (t-SNE), #4b (segmentation), #4c (retrieval), #5 (RL) |
| Framing | "First systematic quantification of material simplification trade-offs in Isaac Sim; practical toolkit + decision guidelines for synthetic data practitioners" |
| After workshop | Expand to full 8-experiment paper; target IEEE TVCG (rolling) or CVPR 2027 main conference (Nov 2026 deadline) |
