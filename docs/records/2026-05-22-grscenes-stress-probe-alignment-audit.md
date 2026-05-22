# 2026-05-22 GRScenes stress probe alignment audit

## Result

The existing zoom stress VLM probes are aligned with the new stress manifest at the sample level:

- `gemma4_zoom_stress_predictions.jsonl`: 28 rows, exact `sample_id` order match with `stress_vlm_run_manifest.json`.
- `qwen25_zoom_stress_structured_predictions.jsonl`: 28 rows, exact `sample_id` order match with `stress_vlm_run_manifest.json`.
- Both runs use `structured_text` responses and `normalized_1000` coordinates.

## Boundary

These files remain pilot/protocol evidence. Their metadata was generated before the stress manifest existed and points to `retake_zoom_target_projection_qa_report.json`, not to `stress_vlm_run_manifest.json`.

Do not rename or copy the existing probe outputs to root `stress_predictions.jsonl`. The root file is reserved for a future manifest-backed run. The final stress benchmark gate also still requires at least 30 stress pairs, while the current manifest contains 14 pairs.

## Plain version

The old zoom model outputs are useful and line up with the new stress input set, but we should not pretend their provenance is newer than it is. Use them for pilot tables and protocol discussion; rerun from `stress_vlm_run_manifest.json` when creating canonical stress outputs.

## Audit command

```bash
python - <<'PY'
import json
from pathlib import Path

root = Path('paper/shared/evidence/raw/grscene_vlm_grounding')
manifest = json.loads((root / 'stress_vlm_run_manifest.json').read_text())
manifest_ids = [record['sample_id'] for record in manifest['scoring_records']]
for path in [
    root / 'zoom_stress_probes/gemma4_zoom_stress_predictions.jsonl',
    root / 'zoom_stress_probes/qwen25_zoom_stress_structured_predictions.jsonl',
]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    metadata = json.loads(path.with_suffix(path.suffix + '.metadata.json').read_text())
    print(path.name)
    print('rows', len(rows), 'exact_order_match', [row.get('sample_id') for row in rows] == manifest_ids)
    print('response_format', metadata.get('response_format'), 'coordinate_frame', metadata.get('coordinate_frame'))
    print('input_report', metadata.get('input_projection_report', {}).get('path'))
PY
```
