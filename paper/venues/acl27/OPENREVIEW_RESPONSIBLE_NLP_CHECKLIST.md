# OpenReview Responsible NLP Checklist Packet

Checked: 2026-05-28.

This packet turns `RESPONSIBLE_NLP_CHECKLIST_DRAFT.md` into copy-ready ARR /
OpenReview form material for the current anonymous review PDF. It is still a
submission aid, not the official form. Before upload, re-check the selected ARR
or ACL-family venue instructions and copy the final answers into OpenReview.

## Official Policy Inputs Checked

- ARR Responsible NLP Research checklist:
  https://aclrollingreview.org/static/responsibleNLPresearch.pdf
- ARR Responsible NLP checklist explainer:
  https://aclrollingreview.org/responsibleNLPresearch/
- ARR common submission problems:
  https://aclrollingreview.org/authorchecklist
- ARR checklist-as-appendix note:
  https://aclrollingreview.org/responsible-nlp-checklist-appendices

The practical rule for this packet is: do not answer with bare yes/no strings.
For yes answers, provide a paper section or justification; for no or N/A
answers, provide the reason.

## Current PDF Anchors

These anchors are from `paper/venues/acl27/build/main.pdf` built on
2026-05-28.

| Paper element | Current anchor |
| --- | --- |
| Title / anonymous header | page 1 |
| Abstract | page 1; `sections/abstract.tex` lines 1-21 |
| Introduction / main results | pages 1-3; `sections/intro.tex` lines 1-85 |
| Related Work / artifact citations | page 3; `sections/related.tex` lines 1-61 |
| Method / evaluation checks | pages 3-5; `sections/method.tex` lines 1-68 |
| Results / reported statistics | pages 4-8 including floats; `sections/results.tex` lines 1-137 |
| Discussion / evaluation scope | page 8; `sections/discussion.tex` lines 1-28 |
| Conclusion / scoped result | page 8; `sections/conclusion.tex` lines 1-14 |
| Limitations | page 9; `sections/limitations.tex` lines 1-36 |
| Ethical Considerations | page 9; `sections/ethical-considerations.tex` lines 1-19 |
| Selected material-effect Figure 3 | page 8; `sections/results.tex` lines 103-115 |
| Selected InternNav Figure 4 | page 9; `sections/limitations.tex` lines 28-36 |
| References | starts on page 9 |

## Copy-Ready Checklist Answers

### A. For Every Submission

**A1. Did you discuss the limitations of your work?**

Yes. See `Limitations`, page 9. The section states that the evidence is
narrow, separates the 15-pair clean pilot from the frozen 30-pair stress set,
marks selected rollout panels as qualitative only, limits the 99-episode
InternNav evidence to three official KuJiaLe scenes, and avoids extending it to
broad InternNav or InteriorAgent coverage, R2R/MP3D, manipulation, or all
GRScenes robustness.

**A2. Did you discuss potential risks of your work?**

Yes. See `Ethical Considerations`, page 9. The paper frames the work as
synthetic-asset and computational-evaluation research, then identifies indirect
risks: dataset bias, license constraints, unsafe deployment assumptions,
overstated downstream robustness, and material simplification changing
object-affordance, safety, texture, or grounding cues. The same section now
also discloses AI coding, writing, and image-generation assistant use and
states that the Figure 1 method-chain roadmap is schematic, not experimental
evidence.

**A3. Do the abstract and introduction summarize the paper's main claims?**

Yes. See the abstract on page 1 and `Introduction` on pages 1-3. The paper
frames MDL-to-UsdPreviewSurface conversion as a controlled perturbation for VLM
grounding and embodied-data reliability. It does not report broad embodied
robustness, official-scene speedup, or a population NVIDIA failure rate.

### B. Scientific Artifacts

**B1. Did you cite the creators of artifacts you used?**

Yes, with final author wording review before upload. `Related Work`, page 3,
cites GRUtopia/GRScenes, InternNav/DualVLN, Habitat, AI2-THOR, TDW, Isaac/Orbit
/ Isaac Lab, CLIP, DINOv2, Shikra, Ferret, and related synthetic-data systems.
`CITATION_PROVENANCE_AUDIT.md` tracks DOI/URL metadata for current manuscript
citations, and `MODEL_AND_ASSET_LICENSE_AUDIT.md` records checked public model
and dataset identifiers.

**B2. Did you discuss license or terms for use/distribution?**

Mostly yes; final author/legal review remains required before upload. `Ethical
Considerations`, page 9, requires asset provenance and license compatibility.
`ARTIFACT_PROVENANCE_DRAFT.md` and `MODEL_AND_ASSET_LICENSE_AUDIT.md` record the
checked terms: GRScenes metadata is CC BY-NC-SA 4.0; InternNav code is MIT;
InteriorAgent uses custom terms that prohibit redistributing data or modified
data; Qwen2.5-VL and the checked Unsloth Gemma4 metadata report Apache-2.0. The
submission packet must not redistribute raw source scenes, scratch USD trees,
local checkpoints, raw InternNav outputs, or optional selected scene-derived
media unless the relevant terms allow it.

**B3. Did you discuss intended use and compatibility with original access
conditions?**

Yes, with final license confirmation still required. `Method`, pages 3-5,
frames the work as research/evaluation of material-conversion reliability.
`Results`, `Discussion`, `Limitations`, and `Ethical Considerations` restrict
the interpretation to evaluation checks and do not report commercial deployment,
model training at scale, or unrestricted redistribution of source assets.

**B4. Did you check whether used data contains identifying or offensive content
and protect/anonymize it?**

N/A with justification. The current evidence uses synthetic 3D scenes, VLM
model outputs, and InternNav trajectory metrics, not human-subject text or
crowdworker annotations. The paper still flags synthetic-scene bias, license
risks, and misleading robustness statements in `Ethical Considerations`, page 9.
The staging packet is scanned to avoid local paths, usernames, private
repository URLs, and acknowledgments.

**B5. Did you provide artifact documentation?**

Yes, with final public packaging still pending. Artifact documentation lives in
the manuscript, `CLAIM_AUDIT.md`, `ARTIFACT_PROVENANCE_DRAFT.md`,
`COMPUTE_RUNTIME_SUMMARY_DRAFT.md`, experiment manifests, and evidence records
under `paper/shared/evidence/`. The safe local staging packet includes only the
anonymous PDF and form/supplemental metadata, not raw restricted assets.

**B6. Did you report relevant statistics and splits?**

Yes. `Results`, pages 4-8 including floats, reports the four-asset proxy metrics, the 15-pair
GRScenes clean pilot, the frozen 30-pair GRScenes stress set, material-effect
sample boundaries, 99 official KuJiaLe paired InternNav episodes across three
scenes, paired confidence intervals, and 18/18 official-scene load/render runs.

### C. Computational Experiments

**C1. Did you report model parameters, compute budget, and infrastructure?**

Mostly yes; final author confirmation is still required.
`COMPUTE_RUNTIME_SUMMARY_DRAFT.md` records the checked GPU host, Isaac Sim/USD
runtime, VLM environments, InternNav checkout, official-scene runtime evidence,
and public model IDs/revisions for the checked Gemma4 and Qwen2.5-VL runs.
Before upload, authors should confirm that the checked host/runtime matches the
submitted runs.

**C2. Did you discuss experimental setup and hyperparameters?**

Yes, with final appendix consolidation recommended. `Method`, pages 3-5, and
`Results`, pages 4-8 including floats, describe original/noMDL conditions, frozen render and
projection manifests, visual-QA split, normalized-1000 coordinate prompting,
raw-coordinate diagnostics, structured-text VLM output, selected material-effect
bins, official KuJiaLe episode splits, and selected-video qualitative status.
`COMPUTE_RUNTIME_SUMMARY_DRAFT.md` records decoding/runtime settings such as
`max_new_tokens=64` and the Qwen eager-attention diagnostic.

**C3. Did you report descriptive statistics and clarify max/mean/single-run
status?**

Yes. `Results`, pages 4-9 including floats, reports counts, paired means, paired confidence
intervals, and the official-scene 18/18 load/render closure. The paper
explicitly marks selected videos and selected material cases as qualitative or
diagnostic evidence rather than population-level estimates.

**C4. Did you report packages/implementation/settings used?**

Mostly yes; final OpenReview copy remains. `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`
records Isaac Sim, USD/PXR, Python, Torch, Transformers, Unsloth, Accelerate,
BitsAndBytes, Pillow, Qwen utility, InternNav, NVIDIA Asset Converter evidence,
and public VLM identifiers. Repository scripts and manifests document commands
and local output hashes, but local paths and checkpoints must stay out of the
upload packet.

### D. Human Annotators Or Subjects

**D. Did you use human annotators or human subjects?**

No. The current evidence package does not include human subjects, recruited
participants, crowdworker annotation, demographic characterization, or an IRB
study. Visual QA is an internal engineering audit of rendered synthetic images,
not a human-subject experiment.

**D1-D5.**

N/A. No participants were recruited, instructed, paid, or demographically
characterized.

### E. AI Assistants

**E. Did you use AI assistants in research, coding, or writing?**

Yes. AI coding, writing, and image-generation assistants were used for
implementation support, documentation organization, manuscript editing, audit
drafting, and a schematic method-chain figure. The schematic is labeled as a
roadmap and is not used as experimental evidence; the same scope is now
stated in the manuscript's `Ethical Considerations` section.

**E1. Did you include information about AI assistant use?**

Use this OpenReview/checklist wording for anonymous review:

> We used AI coding and writing assistants for implementation support,
> documentation organization, manuscript editing, audit drafting, and a
> schematic method-chain figure. All reported results, citations, experiments, generated
> text, and generated visual material were checked by the authors against
> repository evidence and cited sources; the assistants were not credited as
> authors.

If accepted, add any venue-required public checklist appendix or
acknowledgment/disclosure text according to the final ACL-family instructions.

## Remaining Human Gates

- Re-check the selected ARR or ACL-family checklist instructions immediately
  before submission.
- Replace draft section/page anchors if the PDF changes.
- Confirm the final target route, author list/order, OpenReview profiles,
  reviewer-registration commitment, dual-submission/resubmission status, and
  OpenReview preprint-status answer.
- Confirm final author/legal approval for any optional InteriorAgent / KuJiaLe
  scene-derived media beyond the manuscript PDF; the safe packet excludes it.
- Copy these answers into the official OpenReview form; this Markdown file is
  only a local staging aid.
