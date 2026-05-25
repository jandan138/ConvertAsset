# Research Asset Layout

This runbook defines where ConvertAsset paper experiments may place large
runtime assets outside git. It exists because the old flat `/cpfs/.../assets`
layout mixed source datasets, scratch runs, runtime dependencies, logs, and
archived retries in the same top-level directory.

## Canonical Root

Use this root for all new ConvertAsset research assets:

```text
/cpfs/user/zhuzihou/assets/convertasset_research
```

The layout under that root is:

| Path | Purpose |
| --- | --- |
| `datasets/` | Read-mostly external datasets or official source assets |
| `experiments/` | Generated experiment workspaces, scratch copies, configs, logs, and video reruns |
| `runtime/` | Downloaded wheels, model/runtime dependency caches, and compatibility shims |
| `dedup/` | Historical deduplication workspaces |
| `metadata/` | Archived metadata snapshots |
| `asset_layout_manifest_20260525.json` | Machine-readable mapping from legacy top-level paths to canonical paths |

New experiments must create a dated workspace below `experiments/<route>/`.
For the official InternNav val-unseen expansion, use:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_val_unseen_20260525
```

## Directory Contract

Use this contract when adding new files:

| Artifact | Put it here | Git status |
| --- | --- | --- |
| Official/source dataset copy | `datasets/<dataset>/source/` | outside git |
| Scratch noMDL scene copy | `experiments/<route>/<run>/..._nomdl/` | outside git |
| Isaac/InternNav configs generated for a run | `experiments/<route>/<run>/configs/` | outside git, unless generalized into a script |
| Runtime logs | `experiments/<route>/<run>/logs/` | outside git |
| LMDB/sample episodes | InternNav runtime output dir or `experiments/<route>/<run>/analysis/` | outside git |
| Small aggregate results | `paper/shared/evidence/raw/...` | in git |
| Per-episode JSONL/CSV summaries | `paper/shared/evidence/raw/...` | in git when small |
| Selected qualitative video rerun scratch | `experiments/<route>/<run>/video_reruns/` | outside git |
| Curated selected qualitative deliverables | `paper/shared/evidence/raw/.../official_selected_qualitative_videos/` | in git when compressed and QA-passed |
| Contact sheets / small figures | `paper/shared/figures/` | in git when paper-facing |
| Run records and claim gates | `docs/records/` | in git |

In short: heavy artifacts stay outside git, but every heavy artifact needs a
small manifest or dated record in git that says where it lives and what it
means.

## Legacy Alias Policy

The previous top-level paths are retained as symlinks for compatibility. Do not
write new canonical references to these paths in docs or manifests, but do not
delete them while historical evidence still cites absolute paths.

Examples:

```text
/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525
  -> /cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_sanity_20260525

/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523
  -> /cpfs/user/zhuzihou/assets/convertasset_research/runtime/internnav/internnav_vln_runtime_deps_20260523

/cpfs/user/zhuzihou/assets/zzh-grscenes
  -> /cpfs/user/zhuzihou/assets/convertasset_research/datasets/grscenes/source/zzh-grscenes
```

Historical repo evidence may still contain the legacy strings. Those files are
records of what was run at the time, so mass-rewriting them would reduce
forensic clarity. The symlink layer keeps them reproducible while future work
uses the canonical root.

## Writing Rules

- Put large generated outputs under `experiments/`, not directly under
  `/cpfs/user/zhuzihou/assets`.
- Do not create new top-level directories in `/cpfs/user/zhuzihou/assets` for
  ConvertAsset work. If a temporary top-level directory is unavoidable, migrate
  it under `convertasset_research` before treating the run as complete.
- Keep source datasets under `datasets/` and avoid in-place conversion.
- Keep no-MDL conversion inputs in explicit scratch workspaces.
- Keep official source scenes and noMDL scratch scenes separate.
- Keep metric runs video-free unless the current experiment explicitly requests
  a selected qualitative video rerun.
- Sync only bounded evidence into git: JSON, JSONL, CSV, YAML, QA reports,
  small figures, dated docs records, and curated compressed selected-video
  deliverables that have a manifest and QA report.
- Do not sync raw video frame directories, LMDBs, runtime logs, generated
  configs, scene assets, or scratch USD trees into git.
- When a new large workspace is created, record the canonical root in the
  relevant `docs/records/` note and paper evidence README.
- If a path is a compatibility symlink, prefer the canonical target in new docs
  and manifests.

## Completion Checklist

Before closing an experiment that writes external assets:

1. Confirm the heavy workspace is under `convertasset_research`.
2. Confirm no new ConvertAsset top-level directory remains under
   `/cpfs/user/zhuzihou/assets`.
3. Confirm source datasets were not modified in place.
4. Confirm scratch noMDL outputs live in scratch directories.
5. Confirm git only contains lightweight evidence and small paper figures.
6. Add or update a dated `docs/records/` entry.
7. Add or update the relevant `paper/shared/evidence/raw/.../README.md`.

## Verification

After moving or creating asset roots, run:

```bash
python - <<'PY'
import json, os
from pathlib import Path

manifest = Path('/cpfs/user/zhuzihou/assets/convertasset_research/asset_layout_manifest_20260525.json')
data = json.loads(manifest.read_text())
errors = []
for row in data['mappings']:
    legacy = Path(row['legacy_path'])
    canonical = Path(row['canonical_path'])
    if not legacy.is_symlink():
        errors.append((str(legacy), 'legacy_not_symlink'))
    if not legacy.exists():
        errors.append((str(legacy), 'legacy_missing'))
    if not canonical.exists():
        errors.append((str(canonical), 'canonical_missing'))
    if legacy.is_symlink() and Path(os.readlink(legacy)) != canonical:
        errors.append((str(legacy), 'target_mismatch'))
print({'mapping_count': len(data['mappings']), 'error_count': len(errors), 'errors': errors[:10]})
PY
```

Expected result: `error_count` is `0`.
