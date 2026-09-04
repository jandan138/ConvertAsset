# Traditional titration assets r1

The producer archive `traditional_titration_v1_v1.1.zip` is admitted as three
separate packages under `outputs/traditional_titration_assets_r1_20260904/`:

- `packages/burette`: the independent 25 mL burette and its 0–90 degree
  stopcock;
- `packages/stand`: the independent source stand;
- `packages/station`: a fixed-base station assembly with an identity
  `/World/TitrationStation/Instance` layout.

The independent assets preserve the producer geometry. The station assembly
uses the same parts but extends the stand-only rod and clamp to place the
burette over a separate magnetic stirrer. The source 40 mm stopcock handle is
not enlarged and no oversized invisible grasp collider is added. The authored
rest pose and fixed-joint anchors use the same `(0.22, 0, 0.515) m` burette
mount, so the unopened USD and the simulated pose agree.

The station owns a relocatable OmniGraph state machine. It reads the physical
`stopcock_joint` and exposes flow, remaining volume, dispensed volume, ordered
OPEN/FINE/DRIP visits, endpoint hold, overshoot, reset, and task-success state.
It lowers the internal burette column and updates a consumer-bound receiver
shader. It never renders a falling stream or droplet and does not claim true
chemistry.

Three Isaac Sim 4.5 cold starts passed both the 15.0 mL success route and the
overshoot-failure route. Each run also verifies one DOF, fixed-base stability,
reset, the liquid-column change, and the receiver color transition. The
promotion receipt does not claim robot-policy or benchmark success.
