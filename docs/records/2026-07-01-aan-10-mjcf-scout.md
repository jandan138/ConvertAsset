# 2026-07-01 AAN-10 MJCF Scout

## Summary

Implemented and retained `AAN-10-mjcf-scout`, a post-MVP research lane for MJCF /
AutoBio-style sources. The scout does not convert MJCF to USD and does not make an
asset package. It extracts source inventory and records semantic gaps so a future
MJCF source adapter can decide what is convertible, what needs a surrogate or manual
contract, and what must remain blocked.

The retained fixture is AutoBio-like MJCF, not an official AutoBio reproduction.

## Code Changes

- Added `convert_asset/asset_application_normalizer/mjcf_scout.py`.
  - Parses MJCF with the Python standard library XML parser.
  - Extracts body tree, geoms, joints, sites, mesh/texture/material assets, actuators,
    sensors, contacts, equality constraints, tendons, plugins, and task-like elements.
  - Outputs `aan10.mjcf_scout.v1` JSON.
  - Sets `overall_status` to `semantic_gap_report_only`.
  - Explicitly forbids claims that MJCF has been converted to USD or that AutoBio
    official reproduction is supported.
- Added regression coverage in `tests/test_asset_application_normalizer_pm_and_mjcf.py`.

## Retained Evidence

Evidence directory:

`docs/records/evidence/2026-07-01-aan-10-mjcf-scout/`

Artifacts:

- `sources/autobio_like_mjcf.xml`
- `mjcf_scout_manifest.json`

Inventory counts from the retained run:

| Field | Count |
|---|---:|
| bodies | 2 |
| geoms | 2 |
| joints | 1 |
| sites | 1 |
| meshes | 1 |
| textures | 1 |
| materials | 1 |
| actuators | 1 |
| sensors | 1 |
| contacts | 1 |
| equality | 1 |
| tendons | 1 |
| plugins | 1 |

Semantic gaps retained:

- `actuator`
- `sensor`
- `contact`
- `equality`
- `tendon`
- `plugin`
- `task_semantic`

## Verification

Commands run:

```bash
python -m pytest tests/test_asset_application_normalizer_pm_and_mjcf.py::test_mjcf_scout_extracts_inventory_and_semantic_gaps -q
python -m convert_asset.asset_application_normalizer.mjcf_scout docs/records/evidence/2026-07-01-aan-10-mjcf-scout/sources/autobio_like_mjcf.xml --out docs/records/evidence/2026-07-01-aan-10-mjcf-scout/mjcf_scout_manifest.json
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_asset_application_normalizer_pm_and_mjcf.py -q
python -m compileall convert_asset/asset_application_normalizer
git diff --check
```

Evidence audit:

```bash
python - <<'PY'
import json
from pathlib import Path
manifest = json.loads(Path("docs/records/evidence/2026-07-01-aan-10-mjcf-scout/mjcf_scout_manifest.json").read_text())
assert manifest["schema_version"] == "aan10.mjcf_scout.v1"
assert manifest["overall_status"] == "semantic_gap_report_only"
assert manifest["source"]["source_format"] == "mjcf"
assert "MJCF has been converted to USD." in manifest["claims_forbidden"]
assert "AutoBio official reproduction is supported." in manifest["claims_forbidden"]
PY
```

## Claim Boundary

AAN-10 pass means AAN has a first machine-readable MJCF semantic gap report. It does
not mean `normalize-asset` accepts MJCF, does not mean a USD package exists, and does
not mean MuJoCo or AutoBio semantics are supported by EBench.
