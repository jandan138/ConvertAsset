# Task 09 r14 Dual Knob and 60-degree Door

The r14 materialized OVEN 125 adds a second physical knob at local position
`(-0.22, -0.34, 0.724)`, between the mains rocker and display bezel. It copies
the admitted rotor, press carrier, colliders, masses, and two-joint mechanism.
The knobs remain mechanically independent while the embedded controller maps
both to the same temperature, page, timer, and heating state. Press thresholds
are adjusted by the oven root uniform scale.

The door angular-drive damping changed from 18 to 9. The rigid-body angular
damping remains 0.8. The revolute upper limit changed from 180 degrees to 60
degrees; the lower limit remains zero.

Isaac Sim 4.1 qualification passed:

- primary knob at scale 1.0;
- auxiliary knob at scales 0.85, 1.0, and 1.15;
- physical rotation changing the setpoint;
- physical press starting heating;
- controller graph execution and source immutability;
- force-driven door opening into the 58–62 degree band, 60-degree dwell, and
  closing to within 3 degrees.

The producer's unrelated power-page and timer checks are not inherited as r14
claims. Promotion is deliberately task-scoped. Robot-policy and benchmark
success remain false.

GUI locations:

- door resistance: `/World/obj_oven/Joints/DoorHinge` → Physics → Drive →
  Angular → Damping (`9.0`);
- maximum opening: the same prim → Physics → Revolute Joint → Upper Limit
  (`60.0`).
