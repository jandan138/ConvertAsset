# Articulated Device Admission And Requalification

This producer-owned runbook defines the limited path for admitting or
requalifying one articulated USD device for Scenario Forge consumption.
ConvertAsset owns the USD, proxy, profile, and physics work. Scenario Forge only
validates and consumes the promoted package; it must not repair it.

This is not a generic automated repair system. A repair is allowed only when its
parent-local opinions, inputs, and expected readbacks are explicit and
declarative. Never infer a moving-parent transform or task frame heuristically.
Passing this runbook does not claim robot-policy success, generated-task success,
benchmark performance, or real-world physical parity.

## Required Stages

1. **Immutable source and fresh output.** Preserve the raw source and record its
   SHA-256. Build a new package from an immutable source or facade identity; do
   not mutate an earlier admitted package.
2. **Parent-local overlay repair with preserved scale.** Author any proxy repair
   under its actual moving parent, preserve the proxy's local scale, and retain
   the raw-to-facade provenance. Reopen the composed result and read back the
   parent, local transform, scale, bounds, and intended collision placement.
3. **Measured source-bound profile.** Produce an
   `aan.articulated_device_profile.v1` with measured authoritative frames,
   semantic joints, runtime units, reset states, limits, and required gates. For
   a USD `Cube`, `scale` is its full dimension: its local `+Z` face is
   `translation + scale / 2` on Z, not `translation + scale`.
4. **Isaac session-only qualification.** In the target Isaac session, verify
   load/render/step/reset, runtime DOF order, required contact and state gates,
   drive integrity, and commanded/observed travel within declared safety limits.
   Retain the passing runtime report and its package identity evidence.
5. **Finalizer and promotion.** Run the package finalizer with the fresh package,
   profile, and report. It writes the packaged profile/report, final manifest,
   and promotion receipt without changing USD, physics, drives, or colliders.
6. **Scenario Forge loader smoke.** Run
   `load_convert_asset_package_handoff(..., usage="articulated_object")` against
   the promoted package. A passing smoke validates the handoff only; it does not
   authorize consumer-side asset edits or a robot rollout claim.

## Profile/Report ABI

The runtime report `inputs.device_profile` must contain exactly
`schema_version`, `profile_sha256`, and `source_sha256`. They must match,
respectively, `aan.articulated_device_profile.v1`, the SHA-256 of the packaged
`articulation/device_profile.json`, and that packaged profile's source SHA-256
(which must match the manifest source). The ConvertAsset finalizer and Scenario
Forge loader reject any mismatch.

## Invalidation And Retention

A changed source, facade, profile, or runtime report invalidates the candidate:
create a fresh package and promotion. Keep failed reports and related evidence
under separate immutable run IDs. Do not hand-repair a partial promotion; rebuild
and promote a fresh package instead.

Use `scripts/finalize_articulated_package.py` only after the producer stages have
passed. The finalizer refuses replacement promotion artifacts by design. The
closeout evidence for the r7 centrifuge example is recorded in
[`../records/2026-07-29-articulated-package-finalizer.md`](../records/2026-07-29-articulated-package-finalizer.md).
