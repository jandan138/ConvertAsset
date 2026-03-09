# 2026-03-09 Remove Detection Experiment

## Context

The compiled PDF was ~8.5 pages of content (10 total), exceeding the SynData4CV 8-page limit (excluding references). The detection experiment (Section 4.4) was the weakest result with near-zero statistical power (4/24 vs 7/24 images, 6 vs 9 total detections), so it was removed to fit the page limit.

## What Was Removed

- **results.tex**: Entire `\subsection{Zero-Shot Detection}` (Section 4.4), including Table 5 (`tab:detection`) and all surrounding analysis (~45 lines)
- **methodology.tex**: `\paragraph{Detection Proxy.}` (~10 lines describing YOLOv8n setup)
- **discussion.tex**: `\paragraph{Interpreting sparse detection results.}` (~11 lines)
- **references.bib**: `Jocher2023YOLO` bib entry (no longer cited)

## What Was Updated

- **main.tex** (abstract): "four dimensions" → "three dimensions"; removed detection confidence mention; added DINOv2 score (0.872) alongside CLIP
- **introduction.tex**: "four contributions" → "three contributions"; merged items 1+2 into single contribution
- **results.tex**: Opening paragraph "four complementary dimensions" → "three"
- **discussion.tex**: "four evaluation dimensions" → "three"; removed "and no systematic change in detection behavior"
- **conclusion.tex**: "four complementary dimensions" → "three"; removed detection results paragraph; kept detection as future work item
- **methodology.tex**: "Feature extraction and detection inference" → "Feature extraction"

## What Was Preserved

- Detection remains mentioned as **future work** in conclusion.tex: "measuring the impact on downstream AI task performance (e.g., object detection, segmentation)"
- Related work references to detection in broader context (Singh2025Synthetica, Hodan2019Photorealistic) remain untouched

## Verification

- Full 3-pass pdflatex + bibtex compilation: clean, 0 warnings
- PDF: 10 pages total (8 content + 2 references) — within limit
- No dangling `\ref` or `\cite` references
- All remaining "detect" mentions verified as contextually appropriate (cycle-detection in code, related work, future work)
