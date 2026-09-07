# Titration station r3: complete prefilled visual liquid

## Investigation and boundary

The promoted r2 station had only a liquid cylinder over the 25 mL scale. Its
bottom was local z=-0.09 m; the straight glass continued to -0.12 m, followed by
the valve neck, PTFE valve, outlet and cone. None of these lower portions had
visual liquid. Both column and meniscus were authored invisible until runtime.

r3 is a source-bound derivative of that exact package, not a source USD edit.
It changes visual liquid/materials and only the column cap compensation in
the controller. Existing paths, rigid bodies, joints, colliders and mass are
identical. No physics APIs are applied to the added liquid core.

## Implementation

- `scripts/build_titration_filled_visuals_r3.py` builds the candidate with local
  dependencies, a concave 0.3 mm cap, and a continuous lower liquid mesh.
- The original scale mapping remains 0.32 m for 25 mL, fixed at z=-0.09 m.
  Cylinder height excludes the cap depth; the cap follows the same surface.
- Lower charge is fixed visual prefill, not additional metered volume. At
  the end of the scale the upper column disappears but lower charge remains.
  Full tip drainage and falling drops are outside this implementation.
- The lower core fits the actual union of source tube/neck/valve/outlet/cone
  primitive envelopes. A submillimeter transition was tightened to avoid
  extending beyond the outlet/cone overlap. Static sampling checks 3,640
  surface points, all inside; this is sampled containment, not liquid physics.
- Liquid uses local OmniGlass: color (0.97,0.99,1), IOR 1.333, roughness 0.02,
  absorption depth 0.05 m, thin_walled=false, no cutout. Liquid shadows are
  disabled as a realtime visual approximation, matching receiver r1.3.
- `qualify_titration_filled_visuals_r3.py` tests the standalone device in fresh
  Isaac 4.5 processes with prescribed joint positions and a session-only
  target-container fixture flag. It does not claim robot interaction.
- `promote_titration_filled_visuals_r3.py` binds three passing reports to the
  exact asset SHA and publishes the manifest and promotion receipt.

## Validation and delivery

Output: `outputs/traditional_titration_assets_r3_filled_visuals_20260907/`.
Three final standalone cold starts passed: articulation initialization,
fixed-base stability, OPEN/FINE/DRIP/CLOSED success, overshoot rejection,
initial/mid/end-scale/reset liquid state, and persistent lower charge.
Physics signature and dependency closure checks passed. Focused pytest and
Ruff cover the new files; this checkout has no `make check` target.

Scenario Forge consumes the package in task r1.4 and performs scene-level
regression and camera review. Materials are deliberately near-clear, so the
thin liquid is less prominent than the old saturated blue cylinder.
No robot success, true chemistry, PBD or cross-version runtime claim is added.

Original r2 and unrelated paper worktree changes were left untouched.
