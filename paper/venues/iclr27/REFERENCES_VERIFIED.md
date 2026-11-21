# ICLR reference audit — 2026-09-16

## Result

**18 cited sources, 16 citation commands, 21 distinct key/context pairs inspected.** The original 12 citations, two model-family attributions and four appendix metric references are covered. All 17 paper PDFs and the official Gemma4 model card were read at the relevant sections. No missing bibliography keys, duplicate active keys, or unsupported nearby attribution was identified by the advisory reading.

**Submission gate: REVIEW_REQUIRED, not PASS.** The raw official resolver reports one `FAIL` caused by malformed Crossref author metadata. After a narrowly evidenced name normalization and replay through its unchanged identity checks, the effective report has 10 machine identity passes and 8 unresolved resolver results. All 21 human support entries remain `NOT_CHECKED`; no author signature or human review has been invented. Raw audit and cache evidence are retained unchanged; the normalized cache and exact repair log are separate artifacts.

- [Effective JSON report](citation_audit/audit.json) and [Markdown report](citation_audit/audit.md)
- [Raw official FAIL report](citation_audit/raw-audit.json) and [evidenced normalization log](citation_audit/metadata-normalization.json)
- [Context-bound advisory readings](citation_audit/advisory-support.json)
- [Unconfirmed human ledger](citation_audit/human-support.json)
- [Explicit bibliography correction log](citation_audit/corrections.json)
- [Source hashes](citation_audit/source-hashes.json), [PDF retrieval log](citation_audit/source-downloads.json), [fallback retrieval log](citation_audit/fallback-downloads.json)
- [Complete active TeX traversal](citation_audit/traversal-inventory.json) and [citation-free table inventory](citation_audit/supplemental-tex-inventory.json)
- [Metric-source retrieval log](citation_audit/metric-source-downloads.json)

The active bibliography is [references.bib](references.bib). Shared/ACL bibliography files are unchanged. `iclr_references.bib` remains the historical source input and is no longer included by the active main TeX.

## Primary-source findings

“Inspected” below means AI-assisted primary-source inspection, not a human-attested support decision. Full claim-specific locators and original manuscript contexts are in the advisory JSON.

| Citation key | Primary identity and content evidence | Relevant locator | Finding |
| --- | --- | --- | --- |
| Tobin2017Domain | [arXiv PDF](https://arxiv.org/pdf/1703.06907), [DOI](https://doi.org/10.1109/IROS.2017.8202133) | Section III.A, PDF p. 3 | Randomized simulated appearance and real-image transfer inspected. |
| Tremblay2018Training | [CVF proceedings](https://openaccess.thecvf.com/content_cvpr_2018_workshops/w14/html/Tremblay_Training_Deep_Networks_CVPR_2018_paper.html), [DOI](https://doi.org/10.1109/CVPRW.2018.00143) | Section 3, PDF pp. 2–3 | Domain randomization inspected. Publisher pagination discrepancy retained in notes below. |
| Geirhos2019Texture | [Original paper](https://arxiv.org/abs/1811.12231) | Sections 2–3, PDF pp. 3–6 | Human/CNN texture–shape cue conflicts inspected; does not attribute these experiments to VLMs. |
| Chen2023Shikra | [Original paper](https://arxiv.org/abs/2306.15195), [DataCite DOI record](https://api.datacite.org/dois/10.48550/arxiv.2306.15195) | Introduction p. 2; Section 3 pp. 4–5 | Coordinate-based referring and grounding inspected. DOI matches the title and authors. |
| You2024Ferret | [ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/fd6613131889a4b656206c50a8bd7790-Abstract-Conference.html), [conference PDF](https://proceedings.iclr.cc/paper_files/paper/2024/file/fd6613131889a4b656206c50a8bd7790-Paper-Conference.pdf) | Section 3, pp. 4–5 | Formal ICLR 2024 version and hybrid region representation inspected. |
| Deitke2024Molmo | [CVPR 2025 proceedings](https://openaccess.thecvf.com/content/CVPR2025/html/Deitke_Molmo_and_PixMo_Open_Weights_and_Open_Data_for_State-of-the-Art_CVPR_2025_paper.html) | PixMo-Points, PDF pp. 4–5; model variants p. 3 | Updated to formal 2025 proceedings, completed 50-author list. Pointing data and Molmo-7B-D inspected. |
| Bai2025Qwen | [Original paper](https://arxiv.org/abs/2502.13923) | Section 2.1 pp. 3–4; grounding data p. 6 | Dynamic resolution and absolute-coordinate localization inspected; completed 27-author list. |
| Zhu2025InternVL | [Original paper, v3](https://arxiv.org/abs/2504.10479v3) | Sections 2.2–2.4 pp. 4–9; Table 1 p. 4 | Training/test-time recipes and 8B variant inspected; completed the version-matched 51-author list. |
| Zhao2021Calibrate | [PMLR proceedings](https://proceedings.mlr.press/v139/zhao21c.html), [PDF](https://proceedings.mlr.press/v139/zhao21c/zhao21c.pdf) | Section 3 p. 3; Figures 2–3 | Prompt dependence inspected. Publisher author-name variant documented below. |
| Anderson2018Vision | [Original paper](https://arxiv.org/abs/1711.07280), [DOI](https://doi.org/10.1109/CVPR.2018.00387) | Figure 2 p. 2; Sections 3–4 pp. 3–4 | Language, sequential observations and navigation actions inspected. |
| Wang2024GRUtopia | [Original paper](https://arxiv.org/abs/2407.10943), [DataCite DOI record](https://api.datacite.org/dois/10.48550/arxiv.2407.10943) | Section 3.1 pp. 4–5; Section 4 pp. 6–8 | Interactive GRScenes and benchmark tasks inspected. DOI matches the title and authors. |
| Wei2026Ground | [Original paper](https://arxiv.org/abs/2512.08186), [indexed conference PDF](https://openreview.net/pdf/1a25efebc28583e7d38570ab67050516fcc20d8e.pdf) | Section 3 and Figure 2 p. 3 | DualVLN grounding/control connection inspected; title aligned to original PDF. OpenReview direct retrieval remains challenged. |
| Bai2025Qwen3 | [Original paper](https://arxiv.org/abs/2511.21631) | Introduction pp. 1–2; architecture p. 3 | Added attribution for the actual evaluated 2B/8B family; complete 64-author metadata. |
| Google2026Gemma4 | [Official Google model card](https://ai.google.dev/gemma/docs/core/model_card_4) | Description; model-size table | E4B multimodal and instruction-tuned family inspected. Local quantization is documented in the experiment setup, not asserted by this source. |

| Wang2004Image | [Author-hosted journal PDF](https://www.cns.nyu.edu/pub/lcv/wang03-reprint.pdf), [DOI](https://doi.org/10.1109/TIP.2003.819861) | Section III, PDF pp. 4–6 (journal pp. 603–605) | SSIM luminance, contrast and structural comparisons inspected; 2004 volume13(4), pp.600–612 and DOI match. |
| Zhang2018Unreasonable | [CVF proceedings](https://openaccess.thecvf.com/content_cvpr_2018/html/Zhang_The_Unreasonable_Effectiveness_CVPR_2018_paper.html), [DOI](https://doi.org/10.1109/CVPR.2018.00068) | Section 4, PDF pp. 5–6; Figure 3 p. 6 | Deep-feature perceptual distance inspected; CVPR2018 pp.586–595 and DOI match. |
| Radford2021Learning | [PMLR proceedings](https://proceedings.mlr.press/v139/radford21a.html) | Section 2.2 and Figure 3 p. 3; encoder details pp. 3–4 | CLIP normalized image/text representations inspected. The manuscript computes its own image-to-image cosine similarity; it does not attribute a material-fidelity guarantee to CLIP. |
| Oquab2023DINOv2 | [Author paper, v2](https://arxiv.org/abs/2304.07193v2), [TMLR forum](https://openreview.net/forum?id=a68SUt6zFt) | Introduction pp. 1–2; Section 7 transfer evaluation | DINOv2 frozen visual features inspected. PDF explicitly identifies TMLR January2024; stable key2023 is not the publication year. |

## Corrections and remaining distinctions

Applied changes are explicit in `corrections.json`: three complete author lists; Molmo publication metadata updated from arXiv 2024 to CVPR 2025; DualVLN's PDF title includes “Vision-and-Language”; two missing model-family references added. Citation keys remain stable. On September16, four existing shared entries were copied into the venue bibliography for the new metric paragraph; primary checks required no identity-field corrections. These changes identify the same works; no source was substituted to prop up a different claim.

Two publisher inconsistencies are **not silently normalized**:

- **Zhao:** the PMLR landing page/BibTeX uses “Zihao Zhao”; the PDF and author's page use “Tony Z. Zhao.” Retained the official PMLR export's form; the work and coauthors match.
- **Tremblay:** CVF landing page uses pp. 969–977; the PDF prints 1082–1090, and Crossref stores the malformed range 1082–10828. Retained the CVF citation pagination. Audit locators use PDF page numbers to avoid confusion.

The eight unresolved official resolver results are not evidence of seven nonexistent papers. Its short-title comparison includes the arXiv identifier prefix (Qwen reports), its primary-domain allowlist excludes Google/CVF, it queries arXiv DOIs via Crossref rather than DataCite (Shikra/GRUtopia), and OpenReview returns a browser challenge (Ferret/DualVLN/DINOv2). Direct DataCite records and retrieved original PDFs are retained as independent evidence. Ferret's formal PDF was obtained from the ICLR proceedings host. DualVLN's ICLR 2026 label is corroborated by the indexed official conference PDF, but direct access to that conference artifact remains unresolved; the author arXiv PDF supplies the content reading.

No withdrawal/retraction notice was observed in inspected primary records; this is a bounded signal check, not a human `CLEAR` attestation or proof that no notice exists elsewhere. DOI registrant metadata for every declared DOI was inspected, including DataCite records for arXiv-issued DOIs. The authoritative script's retraction flags alone are insufficient because several backends initialize these flags to false.

### SSIM metadata normalization

Crossref records the full name `Zhou Wang` in the first author's `family` field, with no `given` field. The correct BibTeX author and the journal PDF agree on Zhou Wang, but the raw checker compares `Zhou Wang` against the parsed surname `Wang` and emits `METADATA_MISMATCH`. Its raw `FAIL` report is preserved.

`normalize_metadata.py` applies one evidence-bound repair for the exact SSIM DOI and verified author string, requiring the pinned journal PDF hash and absent `given` field. It recomputes the match and identity through the official rules using captured responses; it never assigns a PASS state manually. Raw metadata/cache remain unchanged. Separate regression checks confirm that wrong author, wrong DOI, wrong title and wrong year still fail. The resulting `REVIEW_REQUIRED` does not claim human support. No correct bibliography author or DOI was altered to accommodate the checker.

## Reproduction and handoff

The official audit implementation is `/root/.codex/skills/citation-integrity-auditor/scripts/audit_citations.py`. The venue-local adapter invokes it unchanged except for TeX input resolution: venue working directory first, then child-relative fallback, with missing inputs treated as errors. This covers all nested appendix sections and generated tables; historical snapshots are not traversed. The report records both official-script and adapter hashes. Run from the repository root:

```bash
python paper/venues/iclr27/citation_audit/normalize_metadata.py
python paper/venues/iclr27/citation_audit/run_audit.py \
  --main-tex paper/venues/iclr27/main.tex \
  --bib paper/venues/iclr27/references.bib \
  --support-ledger paper/venues/iclr27/citation_audit/human-support.json \
  --cache paper/venues/iclr27/citation_audit/normalized-metadata-cache.json \
  --json-out paper/venues/iclr27/citation_audit/audit.json \
  --markdown-out paper/venues/iclr27/citation_audit/audit.md \
  --project-root . --offline --strict
```

The raw September16 refresh used `--refresh --timeout 8 --workers 8`. The final cached run exits **1, REVIEW_REQUIRED**, with no structural failures. `bind_review.py` generates advisory contexts and an empty-signature ledger; its guard refuses to overwrite reviewed fields in entries, defaults or source records, including retraction-only attestations. New or edited claims require a fresh advisory reading before rebinding. Full PDFs/text/HTML are local audit cache, not submission assets. Source hashes bind those exact downloaded bytes. Parent task handles the final PDF/BibTeX build and integrated `docs/records/` change record.

The remaining submission action is genuine author confirmation of source identity, nearby claim support and retraction status; this audit has completed the available machine/advisory work without claiming that confirmation occurred.
