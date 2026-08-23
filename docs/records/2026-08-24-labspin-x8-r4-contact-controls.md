# LABSPIN X8 r4 contact controls

## Investigation

The r3 package proved the embedded OPEN-to-lid transition only by commanding
the OPEN joint drive. Its added button link was constrained at the physical
button center, while its visual and collider children repeated that same
translation in link-local space. This double placement explained why the
earlier contact pusher did not operate the visible control.

## Design and changes

`scripts/build_labspin_x8_r4_behavior.py` copies r3 into a new package and
rebases the OPEN visual and collider to the dynamic link origin. The joint
anchor remains at the reviewed source button center. The source facade, rotor
socket geometry, lid limits, and existing START/STOP controls are unchanged.

The USD-embedded ScriptNode now exposes:

- lid states `closed`, `opening`, `open_hold`, `closing`, and `locked`;
- `device:lidState` and `device:powerState` on the articulation root;
- OPEN only while rotor speed is at most `0.1 rad/s`;
- STOP transitioning the observable power state to `off` and targeting zero
  rotor speed.

No external Python controller is needed by the consumed USD. The embedded
ScriptNode remains the explicit compatibility route because the Isaac 4.1
standard articulation-state graph returned empty arrays in the nested moving
articulation during r3 work.

## Runtime qualification

`scripts/qualify_labspin_x8_r4_behavior.py` uses kinematic rigid-body contact
pushers. It never writes OPEN, STOP, or lid joint state directly.

Isaac Sim 4.1 observations:

- OPEN contact travel: `2.5 mm`;
- rotor interlock probe speed: `7.996 rad/s` with lid remaining closed;
- stopped-rotor OPEN result: lid `-1.361 rad` (about 78 degrees);
- lid remains at `-1.361 rad` after OPEN release;
- STOP contact travel: `2.5 mm`, observable power state `off`.

The report is bound at
`outputs/labspin_x8_task11_r4_20260824/package/evidence/lid_behavior/report.json`.
The package manifest status is `pass` with no blocked reasons.

## Claim boundary

This qualifies physical contact actuation of OPEN and STOP, automatic opening,
open hold, and the rotor-open interlock. It does not qualify manual contact
closing/latching, a robot policy, or complete Task 11 success.

## Verification

```text
python -m pytest -q tests/test_build_labspin_x8_r4_behavior.py
# 2 passed

python -m ruff check scripts/build_labspin_x8_r4_behavior.py \
  scripts/qualify_labspin_x8_r4_behavior.py \
  tests/test_build_labspin_x8_r4_behavior.py
# All checks passed

./scripts/isaac41_python.sh scripts/qualify_labspin_x8_r4_behavior.py ...
# status: pass
```

## Open issue

Manual push-down closing and latch retention are authored as state-machine
transitions but remain outside the promoted runtime claims until a dedicated
contact qualification is added.
