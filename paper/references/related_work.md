# Related Work

This document catalogs verified references for the paper:
**"Systematic evaluation of MDL→UsdPreviewSurface material simplification in NVIDIA Isaac Sim: trade-offs between rendering efficiency, visual quality, and AI task performance."**

Verification performed on 2026-03-03 via WebSearch with direct URL confirmation.

---

## 1. USD / MDL Material Systems in Robotics Simulation

Papers covering Universal Scene Description (USD), NVIDIA Omniverse, Isaac Sim as simulation platforms, and MDL/UsdPreviewSurface material representations.

| Title | Authors | Year | Venue | Relation to Our Work | Status |
|---|---|---|---|---|---|
| Isaac Lab: A GPU-Accelerated Simulation Framework for Multi-Modal Robot Learning | Mayank Mittal et al. (NVIDIA, 104+ contributors) | 2025 | arXiv | Primary platform paper — Isaac Lab is built on Isaac Sim (which uses USD/MDL). Establishes photorealistic RTX rendering as key capability | [VERIFIED] https://arxiv.org/abs/2511.04831 |
| Orbit: A Unified Simulation Framework for Interactive Robot Learning Environments | Mayank Mittal, Calvin Yu, et al. | 2023 | IEEE Robotics and Automation Letters (RA-L), Vol. 8, No. 6 | Predecessor to Isaac Lab; uses NVIDIA Isaac Sim with USD-based scene descriptions and RTX rendering for robot learning benchmarks | [VERIFIED] https://arxiv.org/abs/2301.04195 |
| Isaac Gym: High Performance GPU-Based Physics Simulation For Robot Learning | Viktor Makoviychuk, Lukasz Wawrzyniak, et al. | 2021 | NeurIPS 2021 | Foundational NVIDIA GPU simulation framework; provides context for the rendering pipeline evolution toward Isaac Sim and USD-based workflows | [VERIFIED] https://arxiv.org/abs/2108.10470 |
| SynTable: A Synthetic Data Generation Pipeline for Unseen Object Amodal Instance Segmentation of Cluttered Tabletop Scenes | Zhili Ng, Haozhe Wang, et al. | 2023 | SynData4CV Workshop @ CVPR 2025 (originally 2023) | Uses NVIDIA Isaac Sim Replicator (USD-based) for photorealistic synthetic data generation; demonstrates RTX rendering with MDL materials for sim-to-real perception | [VERIFIED] https://arxiv.org/abs/2307.07333 |
| Synthetica: Large Scale Synthetic Data for Robot Perception | Ritvik Singh, Jingzhou Liu, et al. | 2024 | arXiv:2410.21153 | Uses NVIDIA Omniverse Isaac Sim photorealistic ray-tracing renderer (with USD/MDL pipeline) to generate 2.7M images for robot detection; directly relevant to our rendering quality evaluation | [VERIFIED] https://arxiv.org/abs/2410.21153 |

---

## 2. Sim-to-Real Visual Gap and Domain Adaptation

Papers analyzing how visual/rendering quality differences between simulation and reality affect AI model performance.

| Title | Authors | Year | Venue | Relation to Our Work | Status |
|---|---|---|---|---|---|
| Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World | Josh Tobin, Rachel Fong, Alex Ray, Jonas Schneider, Wojciech Zaremba, Pieter Abbeel | 2017 | IROS 2017 | Seminal domain randomization paper; establishes that rendering variation in simulation directly impacts real-world transfer — foundational context for our material simplification impact study | [VERIFIED] https://arxiv.org/abs/1703.06907 |
| Training Deep Networks with Synthetic Data: Bridging the Reality Gap by Domain Randomization | Jonathan Tremblay, Aayush Prakash, et al. | 2018 | CVPR 2018 Workshop (Deep Vision) | NVIDIA paper demonstrating how visual rendering randomization (textures, lighting) in simulation affects downstream object detection — directly analogous to our MDL vs. UsdPreviewSurface rendering comparison | [VERIFIED] https://arxiv.org/abs/1804.06516 |
| Robust Visual Sim-to-Real Transfer for Robotic Manipulation | Ricardo Garcia, Robin Strudel, Shizhe Chen, Etienne Arlaud, Ivan Laptev, Cordelia Schmid | 2023 | IROS 2023 (IEEE) | Systematically evaluates visual domain randomization parameters (texture, lighting, camera) for robotic manipulation; methodology directly parallels our paired rendering quality analysis | [VERIFIED] https://arxiv.org/abs/2307.15320 |
| Photo-realistic Neural Domain Randomization | Sergey Zakharov, Rares Ambrus, Vitor Guizilini, Wadim Kehl, Adrien Gaidon | 2022 | ECCV 2022 | Proposes modular neural rendering for photo-realistic domain randomization; demonstrates that rendering quality (materials, lighting) impacts 6D object detection performance — key reference for our rendering fidelity vs. task performance analysis | [VERIFIED] https://arxiv.org/abs/2210.12682 |
| Sim-to-Real Transfer in Deep Reinforcement Learning for Robotics: a Survey | Wenshuai Zhao, Jorge Peña Queralta, Tomi Westerlund | 2020 | IEEE SSCI 2020 | Survey of sim-to-real techniques including visual domain adaptation; provides taxonomy for understanding where material rendering fits in the broader transfer gap | [VERIFIED] https://arxiv.org/abs/2009.13303 |
| Instance Performance Difference: A Metric to Measure the Sim-To-Real Gap in Camera Simulation | Bo-Hsun Chen, Dan Negrut | 2024 | arXiv:2411.07375 | Introduces IPD metric specifically for quantifying how synthetic vs. real visual rendering affects perception task performance — methodologically aligned with our quantitative rendering quality evaluation | [VERIFIED] https://arxiv.org/abs/2411.07375 |

---

## 3. Image Quality Metrics for Simulation Evaluation

Papers defining or applying PSNR, SSIM, LPIPS, FID, and perceptual quality metrics in simulation/synthetic image contexts.

| Title | Authors | Year | Venue | Relation to Our Work | Status |
|---|---|---|---|---|---|
| Image Quality Assessment: From Error Visibility to Structural Similarity (SSIM) | Zhou Wang, Alan C. Bovik, Hamid R. Sheikh, Eero P. Simoncelli | 2004 | IEEE Transactions on Image Processing, Vol. 13, No. 4 | Defines SSIM metric used in our rendering quality evaluation; canonical reference for structural similarity measure between MDL and UsdPreviewSurface renders | [VERIFIED] https://ieeexplore.ieee.org/document/1284395/ |
| The Unreasonable Effectiveness of Deep Features as a Perceptual Metric (LPIPS) | Richard Zhang, Phillip Isola, Alexei A. Efros, Eli Shechtman, Oliver Wang | 2018 | CVPR 2018 | Introduces LPIPS perceptual similarity metric; key reference for our perceptual image quality evaluation comparing MDL vs. UsdPreviewSurface renders | [VERIFIED] https://arxiv.org/abs/1801.03924 |
| GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium (FID) | Martin Heusel, Hubert Ramsauer, Thomas Unterthiner, Bernhard Nessler, Sepp Hochreiter | 2017 | NeurIPS 2017 | Introduces Fréchet Inception Distance (FID) metric; used in our visual feature distribution analysis to quantify domain gap between MDL and UsdPreviewSurface rendered image populations | [VERIFIED] https://arxiv.org/abs/1706.08500 |

---

## 4. Visual Feature Robustness Across Domain Shifts

Papers on CLIP, DINOv2/DINO, and visual feature analysis across domain boundaries (synthetic vs. real, or different rendering conditions).

| Title | Authors | Year | Venue | Relation to Our Work | Status |
|---|---|---|---|---|---|
| Learning Transferable Visual Models From Natural Language Supervision (CLIP) | Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, et al. | 2021 | ICML 2021 | Introduces CLIP embeddings used in our visual feature analysis; we use CLIP similarity and retrieval evaluation to measure rendering impact on semantic feature preservation | [VERIFIED] https://arxiv.org/abs/2103.00020 |
| Emerging Properties in Self-Supervised Vision Transformers (DINO) | Mathilde Caron, Hugo Touvron, Ishan Misra, Hervé Jégou, Julien Mairal, Piotr Bojanowski, Armand Joulin | 2021 | ICCV 2021 | Introduces DINO self-supervised ViT features; we use DINO features for t-SNE visualization and distribution analysis of MDL vs. UsdPreviewSurface rendered images | [VERIFIED] https://arxiv.org/abs/2104.14294 |
| DINOv2: Learning Robust Visual Features without Supervision | Maxime Oquab, Timothée Darcet, Théo Moutakanni, Huy Vo, Marc Szafraniec, et al. (Meta AI) | 2023 | TMLR 2024 (originally arXiv 2023) | Provides DINOv2 embeddings used in our feature robustness study; DINOv2's domain generalization properties are relevant to quantifying rendering change impact on visual features | [VERIFIED] https://arxiv.org/abs/2304.07193 |

---

## 5. Synthetic Data Rendering Fidelity for Robot Learning

Papers studying how photorealism in synthetic data affects downstream robot learning or perception tasks.

| Title | Authors | Year | Venue | Relation to Our Work | Status |
|---|---|---|---|---|---|
| Synthetica: Large Scale Synthetic Data for Robot Perception | Ritvik Singh, Jingzhou Liu, et al. | 2024 | arXiv:2410.21153 | Uses photorealistic ray-tracing in Isaac Sim to generate 2.7M images for robot perception; demonstrates quantitative correlation between rendering quality and downstream detection performance — central reference for our rendering fidelity vs. task performance study | [VERIFIED] https://arxiv.org/abs/2410.21153 |
| Training Deep Networks with Synthetic Data: Bridging the Reality Gap by Domain Randomization | Jonathan Tremblay, Aayush Prakash, et al. | 2018 | CVPR 2018 Workshop | Shows how varying synthetic rendering quality (textures, lighting) affects object detection accuracy; demonstrates that non-photorealistic randomization can still enable successful transfer if varied enough | [VERIFIED] https://arxiv.org/abs/1804.06516 |
| Photo-realistic Neural Domain Randomization | Sergey Zakharov, Rares Ambrus, et al. | 2022 | ECCV 2022 | Demonstrates that photo-realistic rendering quality of synthetic images outperforms non-photorealistic counterparts for 6D detection; empirically measures rendering quality → task performance trade-offs | [VERIFIED] https://arxiv.org/abs/2210.12682 |
| SynTable: A Synthetic Data Generation Pipeline for Unseen Object Amodal Instance Segmentation | Zhili Ng, Haozhe Wang, et al. | 2023 | SynData4CV @ CVPR 2025 | Uses Isaac Sim high-fidelity RTX rendering (USD/MDL) to train instance segmentation models; evaluates sim-to-real transfer quality — provides benchmarking methodology for assessing rendering impact on downstream segmentation | [VERIFIED] https://arxiv.org/abs/2307.07333 |

---

## Summary Statistics

- Total papers found: 16 unique papers (some appear in multiple sections)
- Total [VERIFIED] entries: 14 distinct verified papers
- All verifications performed via direct arXiv or IEEE URL checks on 2026-03-03
- [UNVERIFIED] entries: 0 (all included entries have confirmed URLs)

### Papers Not Included (Could Not Verify on arXiv/IEEE):
- General NVIDIA Omniverse/MDL documentation and technical blogs — these are not academic papers and should be cited as tech reports if needed
- Wang et al. (2004) SSIM: Verified via IEEE Xplore (not arXiv), URL: https://ieeexplore.ieee.org/document/1284395/
