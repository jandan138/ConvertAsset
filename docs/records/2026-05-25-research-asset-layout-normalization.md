# 2026-05-25 Research Asset Layout Normalization

## Context

The external asset root `/cpfs/user/zhuzihou/assets` had accumulated mixed
ConvertAsset experiment outputs at the top level:

- official InternNav KuJiaLe workspaces;
- repeated GRScenes InternNav trial workspaces;
- InternNav runtime dependencies;
- GRScenes source assets and no-MDL scratch trees;
- deduplication and metadata archives.

This made it hard to tell which paths were canonical, which were historical
retry outputs, and where the next official InternNav val-unseen expansion should
write new data.

## Change

Created the canonical ConvertAsset research root:

```text
/cpfs/user/zhuzihou/assets/convertasset_research
```

Moved `26` existing ConvertAsset-related top-level directories below that root
and left compatibility symlinks at the old paths. The machine-readable mapping
is:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/asset_layout_manifest_20260525.json
```

Top-level examples after normalization:

| Legacy alias | Canonical target |
| --- | --- |
| `/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525` | `/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_sanity_20260525` |
| `/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525` | `/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_nomdl_pair_20260525` |
| `/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523` | `/cpfs/user/zhuzihou/assets/convertasset_research/runtime/internnav/internnav_vln_runtime_deps_20260523` |
| `/cpfs/user/zhuzihou/assets/zzh-grscenes` | `/cpfs/user/zhuzihou/assets/convertasset_research/datasets/grscenes/source/zzh-grscenes` |
| `/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521` | `/cpfs/user/zhuzihou/assets/convertasset_research/experiments/grscenes/nomdl_full/zzh-grscenes_nomdl_full_work_20260521` |
| `/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_*` | `/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/grscenes_trials/internnav_vln_downstream_work_*` |

No repository evidence was mass-rewritten. Historical records still show the
absolute paths that were used when the experiments ran. The symlink layer keeps
those paths valid while new work uses the canonical root.

## Policy

New large external artifacts should use the layout documented in
`docs/operations/research-asset-layout.md`.

For the active official InternNav val-unseen expansion, the next canonical
workspace is:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_val_unseen_20260525
```

Metric runs should remain video-free. Selected qualitative video reruns should
be created only after the aggregate original/noMDL metric evidence is complete.

## Verification

Commands run:

```bash
find /cpfs/user/zhuzihou/assets -maxdepth 1 -mindepth 1 -printf '%f\t%y\t%l\n' | sort
```

Result: the old ConvertAsset-related top-level entries are symlinks, and
`convertasset_research` is the real directory.

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
print({'mapping_count': len(data['mappings']), 'error_count': len(errors), 'errors': errors[:20]})
PY
```

Result:

```text
mapping_count = 26
error_count = 0
```

## Open Risks

Some old manifests and docs intentionally retain legacy absolute paths. That is
acceptable while aliases exist, but new evidence should cite the canonical root.
If the alias layer is ever removed, the historical manifests must be migrated or
their reproducibility boundary must be documented explicitly.
