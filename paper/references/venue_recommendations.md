# Venue Recommendations

Paper topic: **"Systematic evaluation of MDL→UsdPreviewSurface material simplification in NVIDIA Isaac Sim: trade-offs between rendering efficiency, visual quality, and AI task performance."**

Research performed on 2026-03-03.

## Hard Constraints Applied
- NO: ICRA, IROS, RA-L, CoRL, RSS, IJRR (prefer/require real hardware experiments)
- NO: IEEE Access
- YES: Pure simulation/computational papers
- YES: Computer vision venues
- YES: Simulation-specific venues

---

## Recommended Venues (Ranked by Fit)

| Venue | Type | Page Limit | Sim-Only OK? | Fit Score | Key Reason | Next Deadline |
|---|---|---|---|---|---|---|
| ECCV 2026 | Top CV Conference | 14 pages (LNCS) | Yes | **High** | Top CV venue; simulation + rendering papers routinely accepted; Sep 2026 conference gives time | March 5, 2026 (PASSED — next cycle ~2028) |
| CVPR 2026 | Top CV Conference | 8 pages | Yes | **High** | Largest CV conference; simulation quality papers accepted; but deadline Nov 2025 already passed | Nov 13, 2025 (PASSED — next cycle Nov 2026) |
| ICCV 2025 | Top CV Conference | 8 pages | Yes | **High** | Biennial top CV conference; rendering quality + perception evaluation squarely on topic | March 7, 2025 (PASSED — next cycle ~2027) |
| ICML 2026 | Top ML Conference | 8 pages | Yes | **Medium-High** | Strong fit if framed as representation learning / domain shift analysis; RL policy transfer experiment fits | Jan 28, 2026 (PASSED — next ICML cycle Jan 2027) |
| SIGGRAPH 2026 | Premier Graphics Conference | No max (journal track) / 7p (dual track) | Yes | **Medium-High** | Rendering/material conversion is core SIGGRAPH territory; technical evaluation of material fidelity directly fits | Jan 22, 2026 (PASSED — next cycle Jan 2027) |
| IEEE TVCG | Journal (continuous) | ~10 pages + refs | Yes | **Medium-High** | Relevant for rendering fidelity/quality evaluation work; accepts visualization and computer graphics papers; no conference deadline pressure | Rolling (submit anytime) |
| ICLR 2026 | Top ML Conference | 8 pages | Yes | **Medium** | Good fit for RL policy transfer + representation learning framing; but rendering focus may be peripheral to core ICLR topics | Sep 24, 2025 (PASSED — next cycle Sep 2026) |

**Note on deadlines:** As of March 2026, CVPR 2026, ECCV 2026 main track, ICML 2026, and ICLR 2026 submission deadlines have already passed. The most immediately actionable venues are: (1) IEEE TVCG (rolling), (2) a workshop track at CVPR/ECCV/ICCV, or (3) preparation for the next cycle of these conferences.

---

## Detailed Analysis

### ECCV 2026
- **Why it fits**: ECCV is one of the "big three" CV conferences (CVPR/ICCV/ECCV). It regularly accepts papers on synthetic data quality evaluation, rendering fidelity studies, and domain gap analysis. The paper's CLIP/DINOv2 embedding analysis, PSNR/SSIM/LPIPS metrics, and FID distribution analysis are all standard ECCV methodology. Simulation-only papers are routine at ECCV.
- **Fit for contributions**: Image quality metrics (contrib 2), visual feature analysis (contrib 3), downstream detection/segmentation (contrib 4) are all strong ECCV topics.
- **Potential concern**: The RL policy transfer contribution (contrib 5) may need to be de-emphasized or clearly framed as a perception evaluation rather than a robotics policy paper, since ECCV reviewers will primarily evaluate the computer vision angle.
- **Submission format**: OpenReview, 14 pages LNCS format, double-blind
- **Conference**: September 8-13, 2026, Malmö, Sweden
- **Source**: https://eccv.ecva.net/Conferences/2026/Dates

---

### CVPR 2026
- **Why it fits**: CVPR is the world's largest and most prestigious CV conference. Synthetic data quality, sim-to-real visual analysis, and rendering evaluation papers are well-represented. The paired rendering pipeline contribution and quantitative PSNR/SSIM/LPIPS study are standard CVPR empirical methodology.
- **Fit for contributions**: All 5 core contributions are relevant to CVPR. The framing as "when is material simplification safe for vision AI?" creates a clear, impactful narrative for CVPR reviewers.
- **Potential concern**: CVPR is highly competitive (~25% acceptance rate recently). The paper's novelty must be clearly distinguished from existing sim-to-real domain gap work.
- **Submission format**: OpenReview, 8 pages + unlimited references, double-blind
- **Conference**: June 3-7, 2026, Denver Convention Center
- **Next deadline**: ~November 2026 (for CVPR 2027)
- **Source**: https://cvpr.thecvf.com/Conferences/2026/Dates

---

### SIGGRAPH 2026 (Technical Papers)
- **Why it fits**: SIGGRAPH is the premier venue for rendering, materials, and visual computing. The paper's core subject — MDL vs. UsdPreviewSurface material rendering quality, trade-offs in visual fidelity — is directly within SIGGRAPH's scope. The material conversion pipeline analysis and rendering efficiency comparison would be highly relevant to the rendering/simulation community.
- **Fit for contributions**: Contributions 1 (paired rendering pipeline) and 2 (image quality metrics) are ideal SIGGRAPH topics. Contributions 3-5 (AI analysis) may be secondary in SIGGRAPH context, but provide practical impact.
- **Potential concern**: SIGGRAPH technical papers are highly competitive and the AI/robotics downstream evaluation may not be the strongest fit. The paper should be framed primarily around the rendering quality analysis if targeting SIGGRAPH.
- **Submission format**: Dual-track: 7 pages capped (dual-track) or no limit (journal track → ACM TOG). Published in ACM Transactions on Graphics.
- **Next deadline**: ~January 2027 (for SIGGRAPH 2027)
- **Source**: https://s2026.siggraph.org/program/technical-papers/

---

### IEEE Transactions on Visualization and Computer Graphics (TVCG)
- **Why it fits**: TVCG is a top IEEE journal with scope covering visualization and computer graphics. The paper's rendering quality evaluation, visual feature analysis, and simulation pipeline development all fall within this scope. TVCG accepts both rendering papers and applied machine learning evaluation papers. Impact factor 6.55 (2024).
- **Fit for contributions**: Contributions 1-3 (rendering pipeline, image quality metrics, visual feature analysis) align well. The downstream task evaluation and RL policy transfer provide practical grounding that TVCG reviewers appreciate.
- **Potential concern**: TVCG is broad; reviewers may come from visualization backgrounds rather than robotics simulation. The paper needs to emphasize the graphics/rendering angle. Review times can be long (6-12 months).
- **Submission format**: Rolling submission, ~10 pages content + references, no conference deadline
- **Acceptance rate**: ~20-25%
- **Source**: https://www.computer.org/csdl/journal/tg

---

### ICML 2026
- **Why it fits**: ICML is a top machine learning venue. The paper's framing around "when is simplification safe for AI task performance?" positions it as a representation learning / domain shift study. The RL policy transfer experiment (contribution 5) is strong ICML material. CLIP/DINOv2 embedding analysis and distribution shift (FID, t-SNE) are common ICML methodology.
- **Fit for contributions**: Contributions 3-5 (visual features, downstream tasks, RL transfer) are strong ICML topics. Contributions 1-2 (rendering pipeline, image quality) may seem more engineering-focused to ICML reviewers.
- **Potential concern**: The rendering/simulation-specific content is not ICML's core focus. The paper would need to be framed as a study of "how domain shift from material simplification affects learned representations," which is valid but may feel niche to ICML reviewers without a strong robotics or vision ML community there.
- **Submission format**: 8 pages main + unlimited references/appendix, double-blind
- **Conference**: July 6-11, 2026, Seoul, South Korea
- **Deadline passed**: Jan 28, 2026; next cycle: ~Jan 2027
- **Source**: https://icml.cc/Conferences/2026/Dates

---

### ICLR 2026
- **Why it fits**: ICLR focuses on representation learning. The paper can be framed as studying how material simplification affects visual representations (CLIP/DINOv2 embeddings), which is a representation learning question. The RL policy transfer experiment provides an important downstream validation.
- **Fit for contributions**: Contribution 3 (visual feature robustness analysis) and contribution 5 (RL policy transfer) are the strongest ICLR fits. The rendering engineering pipeline is less relevant.
- **Potential concern**: ICLR reviewers may view the rendering/simulation domain as too narrow, and the paper's primary contribution (USD material conversion evaluation) may not resonate as a core representation learning paper. The strongest angle would be: "we study feature space invariance to rendering simplification."
- **Submission format**: 8 pages main + unlimited references, double-blind, OpenReview
- **Conference**: April 23-27, 2026, Rio de Janeiro, Brazil
- **Deadline passed**: Sep 24, 2025; next cycle: ~Sep 2026
- **Source**: https://iclr.cc/Conferences/2026/Dates

---

## Immediate Actionable Options (as of March 2026)

### Option A: IEEE TVCG (Recommended for immediate submission)
- No deadline — can submit now
- Scope matches well for a rendering + visual quality evaluation paper
- Longer review timeline (~9-12 months) but guaranteed consideration

### Option B: ECCV 2026 Workshop (Time-sensitive)
- ECCV 2026 workshops are accepting proposals until ~February 27, 2026
- Relevant workshops: SynData4CV (Synthetic Data for Computer Vision), SimRobot-style workshops
- Workshop papers typically 4-8 pages; lower bar than main conference
- Could serve as a vehicle for quick publication while revising for CVPR/SIGGRAPH

### Option C: CVPR 2027 Main Conference (Plan ahead)
- Deadline will be approximately November 2026
- Use the next ~8 months to fully execute all 5 contributions and prepare a polished submission
- This is the highest-impact venue for the work

### Option D: SIGGRAPH Asia 2026 or Eurographics 2027
- SIGGRAPH Asia 2026 (likely Nov/Dec 2026) — material/rendering papers fit well
- Eurographics 2026: September 8-13, 2026 (paper deadline likely January 2026, probably passed)

---

## Venue Decision Recommendation

**Primary target: CVPR 2027** (November 2026 deadline)
- Highest impact for the topic
- Computer vision community is the most relevant audience
- Simulation-only papers with rigorous quantitative evaluation are well-received
- Plenty of time to complete all 5 contributions

**Backup/parallel target: IEEE TVCG** (rolling submission)
- Submit as soon as the manuscript is ready
- Complements CV venues by reaching the graphics/rendering community
- Can cite a preprint to establish priority while CVPR review is ongoing (check dual-submission policy)

**Workshop option: SynData4CV @ CVPR 2026 or similar** (if workshop CfP is still open)
- Quick publication to establish the work publicly
- Receive community feedback before the main conference submission
