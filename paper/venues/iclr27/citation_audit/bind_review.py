"""Bind advisory source readings and an unconfirmed human ledger to current TeX contexts.
Run the official audit first. Never upgrades machine or human decisions.
"""
from pathlib import Path
import json,hashlib,re
p=Path(__file__).resolve().parent
report=json.loads((p/'audit.json').read_text())
existing=p/'human-support.json'
if existing.exists():
    previous=json.loads(existing.read_text())
    records = [previous.get('defaults', {}), *previous.get('sources', {}).values(), *previous.get('entries', [])]
    if any(e.get('checked_by') or e.get('checked_at') or any(e.get(field, 'NOT_CHECKED') != 'NOT_CHECKED' for field in ('identity_status', 'support_status', 'retraction_status')) for e in records):
        raise SystemExit('Refusing to overwrite a reviewed ledger; preserve and merge attestations manually.')
notes={
'Wang2004Image':('Section III.A–C, PDF pp. 4–6 (journal pp. 603–605)', 'Defines SSIM from luminance, contrast and structure comparisons against a reference image. Supports attribution of structural image similarity; no evidence about this manuscript’s material intervention.'),
'Zhang2018Unreasonable':('Section 4, PDF pp. 5–6; Figure 3 p. 6', 'Defines perceptual distance between deep feature representations and evaluates agreement with human perceptual judgments. Supports LPIPS attribution; metric preprocessing and architecture remain local protocol choices.'),
'Radford2021Learning':('Section 2.2 and Figure 3, PDF p. 3; encoder details pp. 3–4', 'CLIP jointly trains image and text encoders with normalized embeddings and cosine-similarity logits. Supports the image encoder source; paired image-to-image cosine here is the manuscript’s own analysis, not a validated perceptual metric claimed by CLIP.'),
'Oquab2023DINOv2':('Abstract and Introduction, PDF pp. 1–2; Section 7, transfer evaluations', 'Develops self-supervised visual features and evaluates frozen feature transfer. Supports the DINOv2 encoder attribution; pairwise embedding cosine and thresholds are local analysis choices, not a material-fidelity guarantee.'),
'Tobin2017Domain':('Section III.A, PDF p. 3; experiments pp. 4–6','Randomizes textures, lighting, cameras and distractors in synthetic object-localization images; evaluates transfer to real images.'),
'Tremblay2018Training':('Section 3, PDF pp. 2–3; Section 4, pp. 3–7','Applies random appearance and scene parameters to synthetic detector training, then evaluates real KITTI detection. CVF landing page pagination differs from the PDF.'),
'Geirhos2019Texture':('Sections 2–3, PDF pp. 3–6; cue-conflict discussion p. 2','Human/CNN experiments with conflicting shape and texture identify different cue preferences. This is background motivation, not evidence about the evaluated VLMs.'),
'Chen2023Shikra':('Introduction PDF p. 2; Section 3 pp. 4–5','Represents spatial coordinates as numerical text and combines spatial referring, grounding and dialogue in one multimodal model.'),
'You2024Ferret':('Section 3 and Figure 3, conference PDF pp. 4–5; introduction pp. 1–2','Uses discrete coordinates and continuous regional features to combine referring and grounding with language-model generation.'),
'Deitke2024Molmo':('Section 3, PixMo-Points, PDF pp. 4–5 (proceedings pp. 94–95); model variants p. 3','PixMo collects human pointing annotations; the paper describes Molmo variants including Molmo-7B-D. Supports pointing-data and model-family attribution.'),
'Bai2025Qwen':('Section 2.1, PDF pp. 3–4; Grounding Data with Absolute Position Coordinates, p. 6','Dynamic-resolution vision encoding and absolute-coordinate box/point training support localization and resolution claims; identifies the Qwen2.5-VL family.'),
'Zhu2025InternVL':('Sections 2.2–2.4, PDF pp. 4–9; Table 1 p. 4','Describes native multimodal pretraining, post-training and test-time recipes. Table 1 identifies the 8B variant used in the manuscript.'),
'Zhao2021Calibrate':('Section 3, PDF p. 3, Figures 2–3; Section 4 pp. 4–5','Varies prompt examples, order and format in few-shot language tasks and observes accuracy variation. Supports prompt dependence as background, not material sensitivity.'),
'Anderson2018Vision':('Figure 2, PDF p. 2; Sections 3–4 pp. 3–4','Defines visually grounded navigation as a sequence of actions that changes observations while following language instructions.'),
'Wang2024GRUtopia':('Section 3.1, PDF pp. 4–5; Section 4 benchmark, pp. 6–8','Describes GRScenes interactive environments within GRUtopia and tasks in GRBench. Does not establish this manuscript’s data selection.'),
'Wei2026Ground':('Section 3 and Figure 2, arXiv PDF p. 3; Section 3.1 pp. 3–4','DualVLN connects VLM pixel-goal grounding and latent goals to a diffusion policy producing continuous trajectories. The cited connection between grounding and control is explicit.'),
'Bai2025Qwen3':('Introduction, PDF pp. 1–2; Section 2 p. 3','Identifies Qwen3-VL dense 2B and 8B variants and multimodal architecture. Paper attribution does not replace the local checkpoint/configuration record.'),
'Google2026Gemma4':('Official model card: Model Information / Description and model-size table','Google DeepMind identifies Gemma4 as a text/image-input family including E4B and instruction-tuned variants. The evaluated third-party quantization is specified separately by the experiment configuration.')}
urls={r['citation_key']:r['bib_metadata'].get('url','') for r in report['references']}
urls['You2024Ferret']='https://proceedings.iclr.cc/paper_files/paper/2024/hash/fd6613131889a4b656206c50a8bd7790-Abstract-Conference.html'
urls['Wei2026Ground']='https://arxiv.org/abs/2512.08186'
advisory=[];ledger=[]
for o in report['occurrences']:
 k=o['citation_key'];loc,summary=notes[k]
 advisory.append({**o,'source_url':urls[k],'source_locator':loc,'advisory_evidence_summary':summary,'advisory_result':'NO_CONTEXT_MISMATCH_IDENTIFIED','reviewer_kind':'AI_ASSISTANT_ADVISORY','checked_at':'2026-09-16','human_confirmation':False})
 ledger.append({'citation_key':k,'context_sha256':o['context_sha256'],'identity_status':'NOT_CHECKED','source_kind':'software' if k=='Google2026Gemma4' else 'paper','source_url':urls[k],'support_status':'NOT_CHECKED','source_locator':loc,'evidence_summary':'Advisory reading only; see advisory-support.json. Human reviewer must independently confirm.','checked_by':'','checked_at':'','retraction_status':'NOT_CHECKED'})
(p/'advisory-support.json').write_text(json.dumps({'schema_version':'citation-advisory-v1','tex_source_set_sha256':report['inputs']['manuscript_source_set_sha256'],'coverage':{'keys':len(report['cited_keys']),'key_context_pairs':len(advisory)},'entries':advisory},indent=2))
(p/'human-support.json').write_text(json.dumps({'schema_version':'citation-support-v1','entries':ledger},indent=2))
files=[]
for f in sorted((p/'sources').glob('*')):
 if f.is_file():files.append({'path':str(f.relative_to(p)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
(p/'source-hashes.json').write_text(json.dumps({'checked_at':'2026-09-16','files':files},indent=2))
print('Bound',len(advisory),'key-context pairs; human statuses remain NOT_CHECKED')
