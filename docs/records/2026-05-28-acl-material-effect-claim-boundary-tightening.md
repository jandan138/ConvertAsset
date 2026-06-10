# 2026-05-28 ACL Material-Effect Claim-Boundary Tightening

## Scope

This record documents a manuscript-only ACL revision that tightens the link
between ConvertAsset's PreviewSurface conversion method and the material-effect
baseline claims.

## Problem

The previous Method text described the converter as mapping MDL materials to
portable base-color, roughness, metallic, and normal PreviewSurface channels.
The Results section then discussed selected material-effect bins including
opacity/transparency, emission, normal/bump, and displacement/height.

That was technically scoped by the table captions and claim registry, but it
left an avoidable reviewer risk: a reader could infer that a static
material-effect gate proves the underlying MDL mechanism is faithfully
preserved.

## Change

Updated the ACL manuscript to state that:

- ConvertAsset is a core-channel PreviewSurface approximation, not a full MDL
  semantic compiler.
- clearcoat, procedural texture, displacement/height, opacity/transparency,
  emission, and related mechanisms are risk labels for audit, not promises of
  mechanism-level reproduction.
- material-effect static gates check condition availability, zero active MDL in
  converted outputs, and target renderability; they do not themselves certify
  material-effect fidelity.
- the covered-bin result remains a bounded selected comparison supported by
  static and qualitative evidence, not a universal visual-quality win.

Touched manuscript files:

```text
paper/venues/acl27/sections/method.tex
paper/venues/acl27/sections/results.tex
paper/venues/acl27/sections/discussion.tex
```

Added a guard test:

```text
tests/test_acl_claim_boundaries.py::test_acl_material_effect_static_gates_do_not_imply_effect_preservation
```

## Verification

The guard was first run before the manuscript edit and failed because the
required boundary wording was absent. After the manuscript edit, the following
checks passed:

```text
python -m pytest -q \
  tests/test_acl_claim_boundaries.py::test_acl_material_effect_static_gates_do_not_imply_effect_preservation \
  tests/test_acl_claim_boundaries.py::test_current_acl_manuscript_preserves_claim_boundaries
# 2 passed

python paper/venues/acl27/scripts/check_claim_boundaries.py
# ok: true

python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
# ok: true, source_count: 53

python -m pytest -q \
  tests/test_acl_claim_boundaries.py \
  tests/test_acl_integrity_fingerprint.py \
  tests/test_paper_layout.py::test_acl_method_avoids_narrow_column_monospace_evidence_path
# 13 passed

python paper/venues/acl27/scripts/run_preupload_gate.py
# ok: true, focused pytest: 84 passed, 11-page A4 PDF
```

The refreshed build and staged packet are byte-identical:

```text
sha256=4d12baaa865c4328009c64a8a3145562ceb71d520c9425e22cbec73b95616c98
size=3,073,080 bytes
pages=11
```

A 150-DPI local visual review of the rebuilt PDF found no page-level overlap,
blank page, detached Figure 3 caption, or reintroduced red-material/contact
sheet issue. The visual review contact sheet is:

```text
tmp/acl27_material_boundary_visual_20260528/contact_sheet.png
sha256=0c2d1c2a9893ba19deb076feef4bb559e4f64f0fb207775ffd9dfa380f5798ea
```
