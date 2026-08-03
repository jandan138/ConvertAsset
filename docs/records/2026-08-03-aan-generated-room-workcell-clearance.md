# Generated-room full-workcell clearance

Date: 2026-08-03

## Investigation

The existing `aan.workspace_zone_request.v1` audit always used the historical
2.345 x 2.645 m eBench table footprint.  The new Code-as-Room backgrounds
reserve a larger central opening for the table, Lift2 base, and circulation, so
auditing only the tabletop could admit a room that was visibly too tight for
the complete workcell.

## Decision and implementation

`profile-room-zones` now accepts the optional request-level field
`clearance_footprint_m: [width, depth]`.  The declared envelope is rotated by
the reviewed zone yaw before the existing geometry audit.  Requests without
the field keep the historical table footprint, so previous profiles are
unchanged.

This is an audit input, not a geometry repair: ConvertAsset does not scale the
room, move furniture, or add consumer-side masks.  A room that cannot contain
the declared envelope is returned as `not_applicable`.

Changed files:

- `convert_asset/workspace/zone_batch.py`
- `tests/test_workspace_zone_batch.py`
- `docs/operations/workspace-profiling.md`

## Verification

The new regression first failed against the hard-coded legacy footprint, then
passed after the request field was implemented.  The focused suite was run
with the managed EOS development interpreter:

```text
python -m pytest -q \
  tests/test_workspace_zone_batch.py \
  tests/test_workspace_profiles.py \
  tests/test_workspace_audit.py
```

Result: 9 passed.

## Claim boundary and follow-up

The change proves only source-bound geometric clearance for the declared
envelope.  It does not prove Isaac runtime admission, robot reachability,
collision-free motion, task success, or benchmark success.  Those remain
separate package and consumer gates.
