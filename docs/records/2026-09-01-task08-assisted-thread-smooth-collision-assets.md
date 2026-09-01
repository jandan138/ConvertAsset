# Task 08 Assisted-thread Smooth Collision Assets

## Investigation

The Task 08 r12 tube and cap both used the complete visible mesh as an SDF
collider.  Earlier contact probes showed that the detailed teeth could descend
slightly under exact scripted alignment but did not qualify as a robust VR
thread interaction.  The r13 consumer requires one approximate operator turn,
not a physical fine-thread claim.

## Decision and implementation

`scripts/build_task08_assisted_thread_assets.py` creates source-bound wrappers
around the promoted r12 glass tube and red closed cap.  The copied source
packages and visible thread geometry remain byte-identical.  Each wrapper:

- disables collision on the detailed visible mesh;
- adds hidden primitive colliders under `__aan_collision_proxy`;
- uses a smooth tube body/neck and a twelve-segment cap shell;
- authors 0.2 mm contact offset and zero rest offset; and
- declares an effective assisted lead of 7.6 mm per turn without claiming
  physical thread contact.

Output:

`outputs/scientific_workbench_task08_assisted_thread_r1_20260901/`

The output remains `candidate_runtime_pending`; the coupled controller and
runtime interaction belong to Scenario Forge's simulator adapter package.

## r2 grasp profiles

The 2026-09-02 r2 package adds two source-bound hidden grasp proxies after
Lift2 evidence showed that the smooth cylindrical shell was not a repeatable
pickup surface:

- cap: an 18 x 18 x 14 mm high-friction pickup box; the shell starts disabled
  and Scenario Forge switches to the shell at `capture`;
- tube: an 18 mm cube centered at local Z 85 mm, retained throughout handling.

No visible mesh, mass profile, or fine-thread contact claim changed.

## Verification

- `python -m pytest -q tests/test_build_task08_assisted_thread_assets.py`
  — 2 passed.
- Source and copied `asset.usd` hashes are compared by the test.
- Scenario Forge subsequently consumed both wrappers in Isaac Sim 4.1 and
  completed three one-turn/hold/lift observations; that evidence does not
  promote these wrappers as true contact-thread assets.

## Boundaries

The packages do not claim robot policy success, benchmark success, calibrated
mass properties, or fine-thread force/torque fidelity.  They must be consumed
with an assisted-thread controller rather than advertised as standalone
physical screw joints.
