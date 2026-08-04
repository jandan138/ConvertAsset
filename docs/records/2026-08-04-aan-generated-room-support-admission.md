# Generated-room support admission

Date: 2026-08-04

## Investigation

Seven-view review of the generated scientific backgrounds found decorative
bottle groups almost entirely outside their intended sink benches. The v1
ConvertAsset packages correctly preserved source geometry, but their admission
contract did not ask whether small objects had credible supports. A visual
static pass therefore could not exclude producer placement defects.

## Decision

`blender44` + `visual_static_environment` admission now requires
`--support-relations`. The input must be a producer
`room-support-relations-v1` sidecar, but producer results are not trusted as a
waiver. ConvertAsset independently:

1. resolves the sidecar-relative source USD and verifies its SHA-256;
2. opens the composed source stage;
3. checks retained/removed prim existence;
4. recomputes complete horizontal footprint containment with the declared
   margin and vertical contact tolerance;
5. verifies mounted-object overlap; and
6. emits an AAN-owned report and furniture-to-prop `support_closure`.

A missing, stale, unresolved, or geometrically false declaration blocks the
package. ConvertAsset never changes the room source, object pose, collider, or
physics to make this gate pass.

Workspace-zone requests may reference the AAN report with
`support_audit_report`. The profile loader requires a passing report bound to
the same raw source SHA and carries its support closure into every generated
zone profile.

## Code changes

- `convert_asset/asset_application_normalizer/support_audit.py`: independent
  composed-USD support audit.
- `model.py`, `cli.py`, `pipeline.py`, `evidence_manifest.py`: required CLI
  input, package gate, report evidence, and manifest fields.
- `convert_asset/workspace/profiles.py` and `zone_batch.py`: profile-level
  support closure.

## Verification

The focused regression suite covers passing support, stale hashes, forged edge
support, missing sidecars, Blender admission requirements, manifest/CLI
compatibility, and zone-profile closure propagation.

Known boundary: the gate validates static visual support geometry. It does not
claim dynamic stability, contact forces, robot reachability, task success, or
benchmark success.
