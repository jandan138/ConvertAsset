# 29.77 mm magnetic stir-bar admission

## Investigation and choice

Scientific Workbench contains eight source stir-bar geometries. The 29.77 mm
variant was selected for the empty-beaker VR task because its 8.71 mm diameter
is nearly as grasp-visible as the previously admitted 34.62 mm variant while
its shorter length leaves more placement margin. The immutable source is
`magnetic_stir_bar_01_29_77mm.usda`.

## Package

`scripts/build_magnetic_stir_bar_29_77.py` creates a source-bound identity-entry
package at
`outputs/scientific_workbench_magnetic_stir_bar_29_77_20260824/package/`.
It preserves the source USD byte-for-byte inside `deps/usd/`, authors a
29.77 x 8.71 mm cylindrical gripper/support collider, and derives provisional
PTFE mass and inertia from the already admitted stir-bar family. These are
geometry-derived simulation values, not measured material parameters.

## Runtime qualification

`scripts/qualify_magnetic_stir_bar_29_77.py` performs an Isaac Sim 4.1 free-drop
probe. The bar moved 37.96 mm, settled at the support plane, had a final linear
speed below 0.003 mm/s, and passed the stable-support and root-motion gates.
The package manifest is `pass` with no blocked reasons.

## Claim boundary

The package qualifies source closure, collider/support behavior, and Isaac 4.1
free-drop stability. It does not qualify robot grasp or any downstream task.

## Verification

```text
python -m pytest -q tests/test_build_magnetic_stir_bar_29_77.py
# 2 passed

python -m ruff check scripts/build_magnetic_stir_bar_29_77.py \
  scripts/qualify_magnetic_stir_bar_29_77.py \
  tests/test_build_magnetic_stir_bar_29_77.py
# All checks passed
```
